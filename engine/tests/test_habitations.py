# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Distance aux habitations : un bâtiment prime sur une zone, rien n'est inventé, une panne
Overpass ne détruit pas un fait déjà publié."""

from pipelines.habitations import distance


def el(lat, lon, tags):
    return {"lat": lat, "lon": lon, "tags": tags}


def fetch_with(elements):
    return lambda q: {"elements": list(elements)}


def test_building_beats_a_closer_landuse():
    # la zone est plus proche, mais moins précise : le bâtiment tagué résidentiel doit gagner
    f = fetch_with([el(48.8000, 2.3000, {"landuse": "residential"}),
                    el(48.8020, 2.3000, {"building": "house"})])
    d, kind = distance.nearest(48.8000, 2.3010, fetch=f)
    assert kind == "building" and d > 0


def test_landuse_only_is_flagged_not_hidden():
    f = fetch_with([el(48.8000, 2.3000, {"landuse": "residential"})])
    d, kind = distance.nearest(48.8000, 2.3010, fetch=f)
    assert kind == "landuse" and isinstance(d, int)


def test_no_osm_answer_invents_nothing():
    d, kind = distance.nearest(48.8, 2.3, fetch=fetch_with([]))
    assert (d, kind) == (None, None)


def test_resolve_marks_not_found_and_reuses_recent():
    fiches = [{"id": "a", "lat": 48.8, "lon": 2.3}, {"id": "b", "lat": 48.9, "lon": 2.4}]
    prev = {"b": {"distance_m": 120, "kind": "building", "checked_at": "2026-09-01", "found": True}}
    rows, failures = distance.resolve(fiches, prev, "2026-09-21", fetch=fetch_with([]), pause=0)
    assert rows["a"] == {"checked_at": "2026-09-21", "found": False}   # pas de valeur inventée
    assert rows["b"] == prev["b"] and failures == 0                    # récent : non re-interrogé


def test_overpass_outage_keeps_the_previous_fact():
    def boom(q):
        raise RuntimeError("overpass down")
    prev = {"a": {"distance_m": 90, "kind": "building", "checked_at": "2025-01-01", "found": True}}
    rows, failures = distance.resolve([{"id": "a", "lat": 48.8, "lon": 2.3}], prev, "2026-09-21",
                                      fetch=boom, pause=0)
    assert rows["a"] == prev["a"] and failures == 1
