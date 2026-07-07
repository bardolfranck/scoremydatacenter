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
    assert "https://example.org/info" in r["sources"]  # source link pulled from description


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
