# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Phase-1 en-veille onboarding — the load-bearing invariants (no network).

An announced project reaches the PUBLIC lane ONLY as « en veille »: a sourced fact, NO grade
(A-19, structurally impossible in the watchlist schema). The named-operator gate, the pipeline-
status gate, and the served/watchlist dedup are pinned here so a regression can't leak a graded
or low-quality fiche to the public surface.
"""
import json

from pipelines.veille import onboard


_GEO = lambda lat, lon: {"country": "FR" if lat < 49 else "DE", "municipality": "Ville"}  # noqa: E731


def _rows():
    return [
        {"name": "Equinix PA12", "operator": "Equinix", "lat": 48.90, "lon": 2.30,
         "project_status": "under_construction", "source_url": "https://www.openstreetmap.org/way/111"},
        {"name": "unnamed", "operator": "UNKNOWN — to fill", "lat": 50.0, "lon": 8.6,
         "project_status": "announced", "source_url": "https://www.openstreetmap.org/way/222"},
        {"name": "Old DC", "operator": "Colt", "lat": 45.0, "lon": 9.0,
         "project_status": "operational", "source_url": "https://www.openstreetmap.org/way/333"},
        {"name": "Vantage X", "operator": "Vantage", "lat": 51.0, "lon": 7.0,
         "project_status": "announced", "source_url": "https://www.openstreetmap.org/way/444"},
    ]


def _no_served(monkeypatch):
    monkeypatch.setattr(onboard, "_served_index", lambda: {})
    monkeypatch.setattr(onboard, "_watchlist_index", lambda: {})


def test_gates_named_and_pipeline_only(monkeypatch):
    _no_served(monkeypatch)
    cand, rep = onboard.build_candidates(_rows(), today="2026-09-07", geocode=_GEO)
    assert rep["candidates"] == 2                       # Equinix + Vantage
    assert rep["dropped"]["unnamed"] == 1               # UNKNOWN operator dropped
    assert rep["dropped"]["status"] == 1                # operational dropped (pipeline only)
    ids = {c["id"] for c in cand}
    assert ids == {"fr-equinix-ville-111", "de-vantage-ville-444"}


def test_entries_carry_no_grade_and_validate(monkeypatch):
    _no_served(monkeypatch)
    cand, _ = onboard.build_candidates(_rows(), today="2026-09-07", geocode=_GEO)
    assert onboard._validate(cand) == []               # schema-valid en-veille
    for c in cand:
        assert c["facts"] == []                         # bare announced project, no fabricated fact
        assert "grade" not in json.dumps(c).lower()     # A-19: a grade is impossible here
        assert set(c["source"]) == {"title", "url", "accessed"}


def test_dedup_against_served_drops_public_site(monkeypatch):
    # Equinix at the same 2 dp cell as a served Equinix → already public → not re-listed.
    monkeypatch.setattr(onboard, "_served_index", lambda: {(48.90, 2.30): [("srv-eq", "Equinix")]})
    monkeypatch.setattr(onboard, "_watchlist_index", lambda: {})
    cand, rep = onboard.build_candidates(_rows(), today="2026-09-07", geocode=_GEO)
    assert rep["dropped"]["served_dup"] == 1
    assert {c["operator"] for c in cand} == {"Vantage"}   # Equinix deduped out


def test_dedup_against_existing_watchlist(monkeypatch):
    monkeypatch.setattr(onboard, "_served_index", lambda: {})
    monkeypatch.setattr(onboard, "_watchlist_index", lambda: {(51.0, 7.0): [("w1", "Vantage")]})
    cand, rep = onboard.build_candidates(_rows(), today="2026-09-07", geocode=_GEO)
    assert rep["dropped"]["watchlist_dup"] == 1
    assert {c["operator"] for c in cand} == {"Equinix"}


def test_review_markdown_lists_all_and_no_grade():
    from pipelines.veille import onboard
    cand = [{"name": "X", "operator": "Op", "country": "FR", "project_status": "announced",
             "municipality": "Ville", "source": {"url": "https://www.openstreetmap.org/way/1"}, "facts": []}]
    md = onboard.review_markdown(cand)
    assert "X — Ville" in md and "| FR |" in md and "grade" not in md.lower()
    assert md.count("openstreetmap.org") == 1   # one row per candidate


def test_internal_dedup_merges_two_osm_ways_of_one_project(monkeypatch):
    # DR Hattersheim 484/485 shape: 2 candidates, same operator, ~75 m apart → one project.
    monkeypatch.setattr(onboard, "_served_index", lambda: {})
    monkeypatch.setattr(onboard, "_watchlist_index", lambda: {})
    rows = [
        {"name": "DR a", "operator": "Digital Realty", "lat": 50.0644712, "lon": 8.4869027,
         "project_status": "under_construction", "source_url": "https://www.openstreetmap.org/way/484"},
        {"name": "DR b", "operator": "Digital Realty", "lat": 50.065011, "lon": 8.4875253,
         "project_status": "under_construction", "source_url": "https://www.openstreetmap.org/way/485"},
        {"name": "Far", "operator": "Digital Realty", "lat": 48.0, "lon": 2.0,
         "project_status": "announced", "source_url": "https://www.openstreetmap.org/way/999"},
    ]
    cand, rep = onboard.build_candidates(rows, today="2026-09-07", geocode=_GEO)
    assert rep["dropped"]["internal_merged"] == 1       # the 75 m pair collapses to one
    assert rep["candidates"] == 2                        # merged pair + the far one


def test_lane_classification_contested_vs_auto(monkeypatch):
    monkeypatch.setattr(onboard, "_served_index", lambda: {})
    monkeypatch.setattr(onboard, "_watchlist_index", lambda: {})
    # Vantage cell is a CONTESTED watchlist site → its candidate must route to manual_gate.
    monkeypatch.setattr(onboard, "_contested_index", lambda: {(51.0, 7.0): [("w1", "Vantage")]})
    cand, rep = onboard.build_candidates(_rows(), today="2026-09-07", geocode=_GEO)
    assert rep["auto_publish_enabled"] is True                # activé 2026-09-07 (go direct Franck via orchestrateur)
    assert rep["lanes"]["manual_gate"] == ["de-vantage-ville-444"]   # contested → Franck's eye
    assert rep["lanes"]["auto_eligible"] == ["fr-equinix-ville-111"] # clean → auto-eligible (label only)
    # the entries themselves stay schema-clean (no lane field stored)
    assert onboard._validate(cand) == []
    assert all("lane" not in c for c in cand)


def test_deposit_auto_eligible_writes_only_auto_and_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(onboard, "AUTO_PUBLISH_ENABLED", True)
    cand = [
        {"id": "fr-a", "name": "A", "operator": "Equinix", "country": "FR",
         "coordinates": {"lat": 48.8, "lon": 2.3}, "project_status": "announced",
         "source": {"title": "OSM", "url": "https://www.openstreetmap.org/way/1", "accessed": "2026-09-07"}, "facts": []},
        {"id": "fr-b", "name": "B", "operator": "Vantage", "country": "FR",
         "coordinates": {"lat": 49.0, "lon": 2.0}, "project_status": "announced",
         "source": {"title": "OSM", "url": "https://www.openstreetmap.org/way/2", "accessed": "2026-09-07"}, "facts": []},
    ]
    lanes = {"auto_eligible": ["fr-a"], "manual_gate": ["fr-b"]}   # fr-b contested → NEVER auto
    out = tmp_path / "eu-projects-auto.json"
    import json
    n = onboard.deposit_auto_eligible(cand, lanes, out)
    written = json.loads(out.read_text())
    assert n == 1 and [e["id"] for e in written] == ["fr-a"]        # only auto_eligible, not fr-b
    assert "grade" not in json.dumps(written).lower()               # A-19: en-veille, no grade
    onboard.deposit_auto_eligible(cand, lanes, out)                 # re-run (daily cron) → no dup
    assert [e["id"] for e in json.loads(out.read_text())] == ["fr-a"]


def test_deposit_noop_when_flag_off(tmp_path, monkeypatch):
    monkeypatch.setattr(onboard, "AUTO_PUBLISH_ENABLED", False)
    out = tmp_path / "x.json"
    n = onboard.deposit_auto_eligible([{"id": "z", "coordinates": {"lat": 1, "lon": 1}}],
                                      {"auto_eligible": ["z"]}, out)
    assert n == 0 and not out.exists()                              # fail-closed: nothing written
