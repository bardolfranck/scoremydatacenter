# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the voie-B contestation-signal pipeline (no network).

Live feeds are exercised by hand (see RECON-contestation-signal.md). Here we pin the parsing of
each feed's real shape, the cross-feed dedupe, and the load-bearing A-21 contract: the output is
facts only — never a grade, letter, or confidence.
"""

import json

from pipelines.press import signal
from pipelines.press.collect_signal import harvest, _to_geojson, _dedupe_key


# --- feed parsing (fixtures mirror the real shapes probed live) ------------------------------

def test_umap_classifier_separates_opposition_project_inventory():
    opposition = [{"properties": {"name": "Opposition à X", "description": "d"}}]
    projects = [{"properties": {"name": "Data center - Y", "city": "Z", "postcode": "1",
                                "countrycode": "fr", "state": "s"}}]
    inventory = [{"properties": {"name": None, "operator": "OpCo", "telecom": "data_center"}}]
    assert signal._classify_umap_layer(opposition) == "opposition"
    assert signal._classify_umap_layer(projects) == "announced_project"
    assert signal._classify_umap_layer(inventory) == "inventory"      # OSM tags → skipped


def test_umap_fetch_normalizes_and_skips_inventory(monkeypatch):
    monkeypatch.setattr(signal, "_umap_layer_uuids", lambda accessed: ["opp", "inv"])
    layers = {
        "opp": {"features": [{"geometry": {"type": "Point", "coordinates": [2.78, 48.58]},
                              "properties": {"name": "Opposition à un projet",
                                             "description": "Collectifs. https://example.org/info"}}]},
        "inv": {"features": [{"geometry": {"type": "Point", "coordinates": [1.0, 2.0]},
                              "properties": {"operator": "OpCo", "telecom": "data_center"}}]},
    }
    monkeypatch.setattr(signal, "get_json",
                        lambda url: layers["opp"] if "opp" in url else layers["inv"])
    recs = signal.fetch_umap_layers("2026-07-07")
    assert len(recs) == 1                              # inventory layer skipped
    r = recs[0]
    assert r["kind"] == "opposition" and r["country"] == "FR"
    assert r["coordinates"] == {"lat": 48.58, "lon": 2.78}
    # The CITABLE source is the human press/collectif link from the description — the FIRST source,
    # never the raw datalayer GeoJSON feed (a local-official reader must land on a page, not JSON).
    assert r["sources"][0] == "https://example.org/info"
    assert not any("datalayer" in s for s in r["sources"])


def test_source_ranking_prefers_specific_press_article():
    # The default source must be the SPECIFIC press article, not a bare collectif homepage or an
    # aggregator — so the fiche never points a reader at a generic page.
    links = ["https://www.fne13.fr/",                                   # collectif homepage
             "https://linktr.ee/stopcampusia",                          # aggregator
             "https://www.laprovence.com/article/societe/12345/data-center-opposition"]  # press article
    ranked = signal._rank_source_links(links)
    assert ranked[0] == "https://www.laprovence.com/article/societe/12345/data-center-opposition"
    assert ranked[-1] in ("https://www.fne13.fr/", "https://linktr.ee/stopcampusia")


def test_umap_source_falls_back_to_map_page_not_the_json_feed(monkeypatch):
    # A feature with no link in its description → the human map page, never the datalayer endpoint.
    monkeypatch.setattr(signal, "_umap_layer_uuids", lambda accessed: ["opp"])
    monkeypatch.setattr(signal, "get_json", lambda url: {"features": [
        {"geometry": {"type": "Point", "coordinates": [2.0, 48.0]},
         "properties": {"name": "Opposition sans lien", "description": "pas d'url ici"}}]})
    r = signal.fetch_umap_layers("2026-07-07")[0]
    assert r["sources"] == [signal._UMAP_MAP]          # human map page, not the raw feed


def test_fights_keeps_only_opposition_rows_by_default(monkeypatch):
    rows = [
        {"project_name": "P1", "lat": 40.0, "lng": -80.0, "status": "active",
         "opposition_groups": ["Residents United"], "company": "C", "sources": ["https://s1"]},
        {"project_name": "P2", "lat": 41.0, "lng": -81.0, "opposition_groups": []},  # no groups → dropped
    ]
    monkeypatch.setattr(signal, "get_json", lambda url: rows)
    recs = signal.fetch_fights("2026-07-07")
    assert [r["name"] for r in recs] == ["P1"]
    assert recs[0]["opposition_groups"] == ["Residents United"]
    assert recs[0]["country"] == "US"
    # self-reported petition count is carried but explicitly flagged, never a score
    assert "petition_signatures_self_reported" in recs[0]["facts"]


def test_moratoria_filters_to_data_center_sector(monkeypatch):
    csv_text = ("jurisdiction,current_status,latitude,longitude,sectors,date_enacted_iso,legal_basis\n"
                'Townsville,Active,33.5,-86.8,"[""data_center""]",2026-03-03,ordinance\n'
                'Otherplace,Active,34.0,-87.0,"[""solar""]",2026-01-01,zoning\n')
    monkeypatch.setattr(signal, "get_text", lambda url: csv_text)
    recs = signal.fetch_moratoria("2026-07-07")
    assert [r["name"] for r in recs] == ["Townsville"]       # solar-only row filtered out
    assert recs[0]["kind"] == "moratorium"


def test_gdelt_degrades_to_empty_on_ratelimit_notice(monkeypatch):
    # A 429 returns a plain-text notice, not JSON — must degrade to [] not raise.
    monkeypatch.setattr(signal, "get_text", lambda url: "Please limit requests to one every 5 seconds")
    assert signal.fetch_gdelt("datacenter", "2026-07-07") == []


def test_gdelt_parses_artlist(monkeypatch):
    payload = json.dumps({"articles": [
        {"url": "https://news.test/a", "title": "Protest over datacenter", "domain": "news.test",
         "seendate": "20260622T200000Z", "language": "French", "sourcecountry": "France"}]})
    monkeypatch.setattr(signal, "get_text", lambda url: payload)
    recs = signal.fetch_gdelt("datacenter", "2026-07-07")
    assert recs[0]["kind"] == "article" and recs[0]["facts"]["domain"] == "news.test"


# --- per-country GDELT specs (the anti-clone factory of voie B) -------------------------------

def test_gdelt_country_prefixes_sourcecountry_dedupes_and_throttles(monkeypatch):
    seen_queries, slept = [], []

    def fake_raw(query, **kw):
        seen_queries.append(query)
        # both queries return the same url once → must be deduped across queries
        return {"articles": [{"url": "https://news.test/a", "title": "T",
                              "domain": "news.test", "sourcecountry": "Canada"}]}

    monkeypatch.setattr(signal, "_gdelt_fetch_raw", fake_raw)
    recs = signal.fetch_gdelt_country("ca", "2026-07-13", sleep=slept.append)
    assert len(recs) == 1                                     # url-deduped across queries
    assert len(seen_queries) == len(signal.GDELT_COUNTRY_SPECS["CA"]["queries"])
    assert all(q.startswith("sourcecountry:canada ") for q in seen_queries)
    assert slept == [signal._GDELT_THROTTLE_S]                # throttled BETWEEN queries only
    # the spec carries both Canadian spellings — EN "data centre" and FR "centre de données"
    joined = " ".join(seen_queries)
    assert "data centre" in joined and "centre de données" in joined


def test_gdelt_country_retries_a_slow_walked_query_then_succeeds(monkeypatch):
    # GDELT punishes bursts by slow-walking past the timeout (SourceUnavailable), not by a clean
    # 429 — the harvest must retry with backoff instead of silently losing the country.
    from pipelines.spatial.http import SourceUnavailable
    calls, slept = [], []

    def flaky_raw(query, **kw):
        calls.append(query)
        if len(calls) == 1:
            raise SourceUnavailable("timed out")
        return {"articles": [{"url": f"https://news.test/{len(calls)}", "title": "T",
                              "domain": "news.test", "sourcecountry": "Canada"}]}

    monkeypatch.setattr(signal, "_gdelt_fetch_raw", flaky_raw)
    recs = signal.fetch_gdelt_country("CA", "2026-07-13", sleep=slept.append)
    n_queries = len(signal.GDELT_COUNTRY_SPECS["CA"]["queries"])
    assert len(calls) == n_queries + 1                        # one retry, then every query ran
    assert len(recs) == n_queries                             # nothing lost to the slow-walk
    assert slept[0] > signal._GDELT_THROTTLE_S                # backoff harder than the base throttle


def test_gdelt_country_gives_up_loudly_never_raises(monkeypatch, capsys):
    from pipelines.spatial.http import SourceUnavailable

    def always_down(query, **kw):
        raise SourceUnavailable("timed out")

    monkeypatch.setattr(signal, "_gdelt_fetch_raw", always_down)
    recs = signal.fetch_gdelt_country("CA", "2026-07-13", sleep=lambda s: None, retries=2)
    assert recs == []                                         # degrades, never crashes the batch
    assert "gave up" in capsys.readouterr().err               # …but never silently


def test_gdelt_country_unknown_iso_is_empty_not_an_error():
    assert signal.fetch_gdelt_country("XX", "2026-07-13") == []


def test_harvest_countries_feed_press_detections_not_watchlist(monkeypatch):
    monkeypatch.setattr(signal, "fetch_umap_layers", lambda a: [])
    monkeypatch.setattr(signal, "fetch_fights", lambda a, **k: [])
    monkeypatch.setattr(signal, "fetch_moratoria", lambda a, **k: [])
    monkeypatch.setattr(signal, "fetch_gdelt_country", lambda iso, a, **k: [
        signal._record("gdelt", "https://news.test/ca", "l", "article",
                       name="Quinte West residents", country="Canada", retrieved=a)])
    watchlist, press, counts = harvest("2026-07-13", countries=("CA",))
    assert watchlist == []                                    # articles are triage leads,
    assert len(press) == 1                                    # never watchlist entries directly
    assert counts["gdelt-ca"] == 1


# --- dedupe + the no-grade contract ----------------------------------------------------------

def test_dedupe_merges_same_site_across_feeds():
    a = {"source": "umap-fr", "country": "FR", "coordinates": {"lat": 48.5831, "lon": 2.7822},
         "name": "X", "sources": ["u1"], "opposition_groups": None}
    b = {"source": "us-fights", "country": "FR", "coordinates": {"lat": 48.5832, "lon": 2.7823},
         "name": "X", "sources": ["u2"], "opposition_groups": ["G"]}
    assert _dedupe_key(a) == _dedupe_key(b)                  # coords round to the same key


def test_output_geojson_carries_no_grade(monkeypatch):
    monkeypatch.setattr(signal, "fetch_umap_layers", lambda a: [
        {"source": "umap-fr", "source_url": "u", "license": "l", "kind": "opposition",
         "name": "Opp", "country": "FR", "coordinates": {"lat": 48.5, "lon": 2.5},
         "status": None, "opposition_groups": ["G"], "facts": {}, "sources": ["u"], "retrieved": "d"}])
    monkeypatch.setattr(signal, "fetch_fights", lambda a, **k: [])
    monkeypatch.setattr(signal, "fetch_moratoria", lambda a, **k: [])
    watchlist, press, counts = harvest("2026-07-07")
    gj = _to_geojson(watchlist)
    blob = json.dumps(gj).lower()
    for forbidden in ("\"grade\"", "\"letter\"", "\"confidence\"", "\"score\""):
        assert forbidden not in blob
    assert gj["features"][0]["properties"]["watchlist_status"] == "en_veille"
    assert counts["_watchlist_after_dedupe"] == 1


# --- GDELT BigQuery bulk route (A-23) ------------------------------------------------

def test_gdelt_bq_reads_jsonl_export(tmp_path):
    from pipelines.press.signal import fetch_gdelt_bq
    export = tmp_path / "export.jsonl"
    export.write_text("\n".join([
        '{"url": "https://presse.example/fr/actu/opposition-au-data-center-de-testville", '
        '"domain": "presse.example", "seendate": "20260713120000", '
        '"locations": "1#Testville, France#FR#FR75#48.8#2.3#123", "themes": "PROTEST;ENV_GENERAL"}',
        '{"url": "https://zeitung.example/rechenzentrum-widerstand-in-teststadt", '
        '"domain": "zeitung.example", "seendate": "20260713110000", '
        '"locations": "1#Teststadt, Germany#GM##51.0#10.0#9", "themes": "PROTEST"}',
        'not json at all',
        '{"no_url": true}',
        # duplicate url must dedupe
        '{"url": "https://presse.example/fr/actu/opposition-au-data-center-de-testville", '
        '"domain": "presse.example", "seendate": "20260713130000", "locations": "", "themes": ""}',
    ]))
    records = fetch_gdelt_bq(str(export), "2026-07-14")
    assert len(records) == 2
    fr = records[0]
    assert fr["source"] == "gdelt-bq" and fr["kind"] == "article"
    assert fr["country"] == "FR"                       # FIPS FR -> ISO FR
    assert "opposition au data center" in fr["name"]   # slug title, triage aid
    assert fr["facts"]["title_is_slug"] is True
    de = records[1]
    assert de["country"] == "DE"                       # FIPS GM -> ISO DE
    # never a grade-like key anywhere (A-19/A-21)
    for r in records:
        assert not ({"grade", "score", "confidence"} & set(r))


def test_gdelt_bq_degrades_to_empty_on_missing_export(tmp_path):
    from pipelines.press.signal import fetch_gdelt_bq
    assert fetch_gdelt_bq(str(tmp_path / "absent.jsonl"), "2026-07-14") == []


def test_gdelt_bq_operator_axis(tmp_path):
    from pipelines.press.signal import fetch_gdelt_bq
    export = tmp_path / "orgs.jsonl"
    export.write_text(
        '{"url": "https://x.test/opposition-equinix-pa10", "domain": "x.test", '
        '"seendate": "20260713120000", "locations": "1#Paris#FR#FR75#48.8#2.3#1", '
        '"themes": "PROTEST", "organizations": "equinix,12;plaine commune,40;prefecture,80"}\n'
        '{"url": "https://y.test/rechenzentrum-widerstand", "domain": "y.test", '
        '"seendate": "20260713110000", "locations": "1#Berlin#GM##51#10#9", '
        '"themes": "PROTEST", "organizations": "stadtwerke,5"}\n'
    )
    recs = fetch_gdelt_bq(str(export), "2026-07-14")
    assert recs[0]["facts"]["operators"] == ["Equinix"]
    assert "equinix" in recs[0]["facts"]["organizations"]
    assert recs[1]["facts"]["operators"] == []          # no known operator -> honest empty
