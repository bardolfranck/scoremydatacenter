# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Shared dedup util — vs-served (exclude/flag/None) + candidate-vs-candidate. Pins the fail-closed
rule agreed EU × codeur-API (2026-09-07)."""
from pipelines.veille import dedup


def _served(*rows):  # rows = (lon, lat, operator)
    return dedup.served_index([{"geometry": {"coordinates": [lon, lat]},
                                "properties": {"id": f"srv-{i}", "operator": op}}
                               for i, (lon, lat, op) in enumerate(rows)])


def test_exact_operator_excludes():
    idx = _served((8.49, 50.06, "Digital Realty"))
    assert dedup.match_served(50.061, 8.491, "Digital Realty", idx)[0] == "exclude"


def test_legal_suffix_descriptor_diff_still_excludes_via_first_brand():
    # Hetzner « Finland Oy » vs served « Hetzner Online » — differ on descriptor, share 1st brand.
    idx = _served((24.9, 60.3, "Hetzner Online"))
    assert dedup.match_served(60.301, 24.901, "Hetzner Finland Oy", idx)[0] == "exclude"


def test_non_first_overlap_flags_not_excludes():
    # « Global Realty » vs served « Digital Realty » share 'realty' (not 1st token) → FLAG, keep.
    idx = _served((2.35, 48.85, "Digital Realty"))
    assert dedup.match_served(48.851, 2.351, "Global Realty", idx)[0] == "flag"


def test_different_operator_same_cell_is_clean():
    idx = _served((2.35, 48.85, "NTT"))
    assert dedup.match_served(48.851, 2.351, "OVHcloud", idx) is None


def test_unknown_operator_never_hard_matches():
    idx = _served((2.35, 48.85, "NTT"))
    assert dedup.match_served(48.851, 2.351, "UNKNOWN — to fill", idx) is None


def test_internal_dedup_merges_close_same_operator_both_shapes():
    # top-level lat/lon (study_review shape)
    a = [{"id": "a", "operator": "DR", "lat": 50.0645, "lon": 8.4869},
         {"id": "b", "operator": "DR", "lat": 50.0650, "lon": 8.4875},   # ~70 m
         {"id": "c", "operator": "DR", "lat": 48.0, "lon": 2.0}]
    kept, merged = dedup.dedup_internal(a)
    assert [k["id"] for k in kept] == ["a", "c"] and merged == [("b", "a")]
    # nested coordinates{} (onboard shape)
    n = [{"id": "x", "operator": "DR", "coordinates": {"lat": 50.0645, "lon": 8.4869}},
         {"id": "y", "operator": "DR", "coordinates": {"lat": 50.0650, "lon": 8.4875}}]
    kept2, merged2 = dedup.dedup_internal(n)
    assert [k["id"] for k in kept2] == ["x"] and merged2 == [("y", "x")]


def test_dedup_vs_served_batch_clean_hard_soft():
    idx = _served((8.49, 50.06, "Digital Realty"), (2.35, 48.85, "NTT"))
    items = [
        {"id": "hard", "operator": "Digital Realty", "lat": 50.061, "lon": 8.491},   # exact → hard
        {"id": "soft", "operator": "Global Realty", "lat": 50.061, "lon": 8.491},     # cell DR + overlap 'realty' non-1er → soft
        {"id": "clean", "operator": "OVHcloud", "coordinates": {"lat": 43.6, "lon": 1.4}},  # nested shape, no cell
    ]
    clean, hard, soft = dedup.dedup_vs_served(items, idx)
    assert [i["id"] for i in hard] == ["hard"]
    assert [i["id"] for i in soft] == ["soft"]
    assert [i["id"] for i in clean] == ["clean"]
