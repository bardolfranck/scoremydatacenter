# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""The watchlist (A-19) publishes sourced facts, never a grade. A letter must be
structurally impossible — the schema forbids it and the gate turns any leak into a
named failure. These tests make that promise executable."""

import json

from engine.core import load_datacenters, load_methodology, load_watchlist
from engine.artifacts import build_artifacts
from engine.validate import _grade_leak, GRADE_LIKE_KEYS


def test_watchlist_geojson_has_no_grade(tmp_path):
    build_artifacts(load_datacenters(), load_methodology(), out_dir=tmp_path)
    geo = json.loads((tmp_path / "watchlist.geojson").read_text())
    assert geo["type"] == "FeatureCollection"
    assert geo["features"], "the fixture should yield at least one watchlist marker"
    for feat in geo["features"]:
        props = feat["properties"]
        assert not (GRADE_LIKE_KEYS & set(props)), "a watchlist marker must never carry a grade"
        for fact in props["facts"]:
            assert "source" in fact and "label" in fact  # facts are sourced
        assert _grade_leak(props) is None


def test_grade_leak_detector_catches_a_letter():
    clean = {"id": "x", "name": "n", "facts": [{"label": {"fr": "a", "en": "a"}}]}
    assert _grade_leak(clean) is None
    leaked = {"id": "x", "name": "n", "grade": "B"}
    assert _grade_leak(leaked) == "grade"
    nested = {"id": "x", "facts": [{"assessment": {"score": 42}}]}
    assert _grade_leak(nested) == "score"


def test_fixture_watchlist_is_sourced():
    # Every entry is justified by an entry-level source; facts MAY be empty
    # (a tracked flagship with no contestation yet — no fake fact is fabricated).
    for entry in load_watchlist():
        assert entry["source"]["url"], f"{entry['id']} must carry an entry-level source"
        for fact in entry.get("facts", []):
            assert fact["source"]["url"]


def test_watchlist_allows_empty_facts():
    ids = {e["id"]: e for e in load_watchlist()}
    flagship = ids.get("zz-watch-delta-flagship")
    assert flagship is not None and flagship["facts"] == [], "the empty-facts flagship case must validate"
