# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the watchlist-reviewer scaffold (no network).

Pins the mechanical reduction (rich harvester record → light published shape), the flags, and the
load-bearing contract: proposals only, never a grade, never auto-published.
"""

import json

from pipelines.press.review import reduce_entry, review_feature, build_queue, _HARD_FLAGS


def _feature(props, coords):
    return {"type": "Feature", "geometry": ({"type": "Point", "coordinates": coords} if coords else None),
            "properties": props}


def test_opposition_reduces_to_one_fact():
    e = reduce_entry({"source": "umap-fr", "kind": "opposition", "name": "Opposition à un projet",
                      "country": "FR", "sources": ["https://x.test/o"], "retrieved": "2026-07-08"},
                     [2.5, 48.6])
    assert e["coordinates"] == {"lat": 48.6, "lon": 2.5}
    assert len(e["facts"]) == 1 and e["facts"][0]["kind"] == "opposition"
    assert e["facts"][0]["label"]["fr"] == "Opposition à un projet"   # raw, to be neutralized
    assert e["facts"][0]["label"]["en"] is None                       # reviewer adds EN
    assert e["facts"][0]["_label_status"] == "proposed_raw"
    assert e["source"]["url"] == "https://x.test/o"


def test_announced_project_has_empty_facts():
    e = reduce_entry({"source": "umap-fr", "kind": "announced_project", "name": "Data center - Y",
                      "country": "FR", "status": "announced", "sources": ["https://x.test/p"],
                      "retrieved": "2026-07-08"}, [3.0, 50.3])
    assert e["facts"] == []                                            # bare project → no fake fact
    assert e["project_status"] == "announced"
    assert e["source"]["url"] == "https://x.test/p"                    # entry-level source justifies listing


def test_self_reported_petition_becomes_flagged_fact():
    e = reduce_entry({"source": "us-fights", "kind": "opposition", "name": "P",
                      "country": "US", "sources": ["https://x.test/f"], "retrieved": "2026-07-08",
                      "facts": {"petition_signatures_self_reported": 18000}}, [-86.0, 35.1])
    petition = [f for f in e["facts"] if f["kind"] == "petition"]
    assert petition and petition[0]["self_reported"] is True


def test_flags_out_of_country_and_nc_license():
    # A "FR" entry with US coords → geoloc_out_of_country (hard) → routed to human.
    item = review_feature(_feature(
        {"source": "umap-fr", "kind": "opposition", "name": "X", "country": "FR",
         "sources": ["https://x.test"], "retrieved": "2026-07-08"}, [-90.0, 40.0]))
    assert "geoloc_out_of_country" in item["flags"]
    assert "license_nc_umap" in item["flags"]
    assert item["route"] == "human"                                   # hard flag → person
    assert _HARD_FLAGS & set(item["flags"])


def test_clean_entry_routes_to_agent_for_label_work():
    item = review_feature(_feature(
        {"source": "us-moratorium", "kind": "moratorium", "name": "Townsville", "country": "US",
         "sources": ["https://x.test/m"], "retrieved": "2026-07-08"}, [-86.0, 35.1]))
    assert item["route"] == "agent"                                   # no hard flag; needs label + verify
    assert item["needs_label_work"] is True


def test_contract_never_publishes_and_never_grades():
    q = build_queue([_feature(
        {"source": "us-fights", "kind": "opposition", "name": "Z", "country": "US",
         "sources": ["https://x.test"], "retrieved": "2026-07-08"}, [-86.0, 35.1])])
    item = q[0]
    assert item["auto_published"] is False
    blob = json.dumps(q).lower()
    for forbidden in ('"grade"', '"letter"', '"score"', '"confidence"'):
        assert forbidden not in blob
