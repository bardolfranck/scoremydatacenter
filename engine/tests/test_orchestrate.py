# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the pipeline orchestrator (no network).

Pins the chaining (spatial → governance → contestation match → review), the single human gate
(nothing proceeds/publishes without it), and the promote contract (only `approve` is applied,
silence is never consent).
"""

import json

import pytest

from pipelines import orchestrate


@pytest.fixture
def stub_collectors(monkeypatch):
    monkeypatch.setattr(orchestrate, "spatial_collect",
                        lambda lat, lon, **k: ({"id": "zz-test", "indicators": []}, {"gen": "spatial"}, []))
    monkeypatch.setattr(orchestrate, "governance_collect",
                        lambda lat, lon, **k: {"proposed_t1_proxies": {"cndp_referral": True}})


def test_match_contestation_by_radius(tmp_path):
    fc = {"type": "FeatureCollection", "features": [
        {"geometry": {"type": "Point", "coordinates": [2.78, 48.58]},          # ~near
         "properties": {"source": "umap-fr", "kind": "opposition", "name": "Near", "country": "FR",
                        "sources": ["https://x"], "retrieved": "2026-07-08"}},
        {"geometry": {"type": "Point", "coordinates": [7.75, 48.58]},          # ~370 km east
         "properties": {"source": "umap-fr", "kind": "opposition", "name": "Far", "country": "FR",
                        "sources": ["https://x"], "retrieved": "2026-07-08"}},
    ]}
    path = tmp_path / "signal.geojson"
    path.write_text(json.dumps(fc))
    hits = orchestrate.match_contestation(48.58, 2.78, 25.0, path)
    assert [h["proposed"]["name"] for h in hits] == ["Near"]     # only the one within 25 km


def test_match_contestation_empty_without_signal():
    assert orchestrate.match_contestation(48.58, 2.78, 25.0, None) == []


def test_onboard_chains_and_gate_is_pending(stub_collectors):
    b = orchestrate.onboard(48.58, 2.78, name="X", operator="Op", power_mw=30,
                            project_status="announced", accessed="2026-07-08", signal_path=None)
    assert b["dc_id"] == "zz-test"
    assert b["fragment"]["id"] == "zz-test"                      # spatial ran
    assert b["governance"]["proposed_t1_proxies"]["cndp_referral"] is True  # voie A ran
    assert b["human_gate"] == "pending"                          # nothing proceeds without a human
    assert b["contestation_review"] == []                       # no signal path → no candidates


def test_promote_applies_only_approved(monkeypatch):
    monkeypatch.setattr(orchestrate, "archive_url", lambda url: "https://web.archive.org/web/x/" + url)
    items = [
        {"decision": "approve", "proposed": {"name": "A", "facts": [
            {"kind": "opposition", "label": {"fr": "l", "en": "l"}, "_label_status": "proposed_raw",
             "source": {"title": "t", "url": "https://a", "accessed": "d"}, "self_reported": False}]}},
        {"decision": "reject", "proposed": {"name": "B", "facts": []}},
        {"proposed": {"name": "C", "facts": []}},                # no decision → silence ≠ consent
    ]
    out = orchestrate.promote_contestation(items)
    assert [e["name"] for e in out] == ["A"]                     # only the approved one
    fact = out[0]["facts"][0]
    assert "_label_status" not in fact                          # internal flag stripped
    assert fact["source"]["archived_url"].endswith("https://a")  # archived_url added at promote (A-20)


def test_promote_into_dc_writes_the_last_mile(monkeypatch):
    monkeypatch.setattr(orchestrate, "archive_url", lambda url: None)   # keep it offline
    items = [
        {"decision": "approve", "proposed": {"name": "A", "facts": [
            {"kind": "opposition", "label": {"fr": "Opposition", "en": "Opposition"},
             "_label_status": "proposed_raw",
             "source": {"title": "t", "url": "https://a", "accessed": "d"}, "self_reported": False}]}},
        {"decision": "reject", "proposed": {"name": "B", "facts": [
            {"kind": "press", "label": {"fr": "x", "en": "x"},
             "source": {"title": "t", "url": "https://b", "accessed": "d"}}]}},
    ]
    dc = {"id": "zz-test", "indicators": []}
    out = orchestrate.promote_into_dc(dc, items)
    # only the approved entry's facts land in contestation[]; the rejected one does not
    assert len(out["contestation"]) == 1
    item = out["contestation"][0]
    assert item["kind"] == "opposition" and item["label"]["fr"] == "Opposition"
    assert set(item) == {"kind", "label", "source", "self_reported"}   # flattened to the DC shape
    assert "_label_status" not in item


def test_render_html_has_no_grade_and_marks_facts_only():
    html = orchestrate.render_review_html([
        {"proposed": {"name": "X", "country": "FR", "facts": [
            {"kind": "opposition", "label": {"fr": "Opposition"}, "source": {"url": "https://a"}}]},
         "flags": ["license_nc_umap"], "route": "agent", "decision": None}], "zz-test")
    low = html.lower()
    assert "aucune note" in low
    for forbidden in (">a<", ">b<", ">c<", ">d<", ">e<"):        # no bare grade letter as a cell
        assert forbidden not in low
    assert "grade" not in low and "score" not in low
