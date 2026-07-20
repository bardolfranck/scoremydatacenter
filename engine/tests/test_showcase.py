# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""home_showcase gates — the home must not target anybody (Franck 2026-07-20).

The rule these tests defend: the site shown on the front page is the most
ORDINARY one (closest to the corpus median), and every "hot" signal is an
exclusion. The bug this guards against is real: the previous home demo
required all 5 pillars, only 2 fiches of 479 passed, and the front page
ended up on the single most contested project in France."""

from engine.showcase import build_showcase


def _dc(dc_id, country="FR", status="operational", contestation=None,
        operator_response=None, lat=48.0, lon=2.0):
    return {
        "id": dc_id,
        "identity": {"name": dc_id, "country": country, "project_status": status,
                     "coordinates": {"lat": lat, "lon": lon}},
        "indicators": [],
        "publication": {"operator_response": operator_response} if operator_response else {},
        "contestation": contestation,
        "score_history": [],
    }


def _result(score, grade="C", n_pillars=4):
    pillars = {f"p{i}": {"grade": grade} for i in range(n_pillars)}
    pillars.update({f"p{i}": {"grade": "insufficient_data"} for i in range(n_pillars, 5)})
    return {"grades": {"site": {"grade": grade, "score": score}}, "pillars": pillars}


def _corpus(scores, **kw):
    dcs, results = {}, {}
    for i, s in enumerate(scores):
        did = f"fr-{i:02d}"
        dcs[did] = _dc(did, **kw)
        results[did] = _result(s)
    return dcs, results


def test_demo_is_the_median_site_never_an_extreme():
    dcs, results = _corpus([10.0, 30.0, 60.0, 85.0, 95.0])
    out = build_showcase(dcs, results)
    assert out["median_site_score"] == 60.0
    top = out["demo_candidates"][0]
    assert top["score"] == 60.0 and top["delta_median"] == 0
    # the extremes must never lead the ranking
    assert out["demo_candidates"][-1]["score"] in (10.0, 95.0)


def test_hot_signals_are_excluded():
    dcs, results = _corpus([60.0, 60.0, 60.0, 60.0])
    dcs["fr-00"]["contestation"] = [{"kind": "opposition"}]
    dcs["fr-01"]["publication"] = {"operator_response": {"text": "…"}}
    dcs["fr-02"]["identity"]["project_status"] = "announced"
    ids = [c["id"] for c in build_showcase(dcs, results)["demo_candidates"]]
    assert ids == ["fr-03"], f"a hot/unbuilt site slipped into the home: {ids}"


def test_watchlist_neighbour_excluded():
    dcs, results = _corpus([60.0, 60.0])
    watch = [{"identity": {"coordinates": {"lat": 48.001, "lon": 2.001}}}]
    dcs["fr-01"]["identity"]["coordinates"] = {"lat": 44.0, "lon": 1.0}
    ids = [c["id"] for c in build_showcase(dcs, results, watch)["demo_candidates"]]
    assert ids == ["fr-01"], "a site next to a contested project reached the home"


def test_pillar_floor_is_four_not_five():
    # the regression that put the hottest FR project on the home: a 5-pillar
    # requirement leaves ~2 eligible fiches in the whole corpus.
    dcs, results = _corpus([60.0, 60.0])
    results["fr-00"] = _result(60.0, n_pillars=3)
    results["fr-01"] = _result(60.0, n_pillars=4)
    ids = [c["id"] for c in build_showcase(dcs, results)["demo_candidates"]]
    assert ids == ["fr-01"]


def test_deterministic_and_tie_broken_on_id():
    dcs, results = _corpus([60.0] * 4)
    a = build_showcase(dcs, results)
    b = build_showcase(dcs, results)
    assert a == b                                   # byte-identical between builds
    assert [c["id"] for c in a["demo_candidates"]] == ["fr-00", "fr-01", "fr-02", "fr-03"]


def test_wall_alternates_grades_and_countries():
    dcs, results = {}, {}
    for i, (grade, country) in enumerate([("A", "FR"), ("A", "NL"), ("B", "FR"),
                                          ("B", "NL"), ("C", "FR"), ("C", "NL")]):
        did = f"{country.lower()}-{i}"
        dcs[did] = _dc(did, country=country)
        results[did] = _result(60.0, grade=grade)
    wall = build_showcase(dcs, results)["wall_candidates"]
    assert len(wall) == 6
    grades = [results[i]["grades"]["site"]["grade"] for i in wall[:3]]
    assert grades == ["A", "B", "C"], f"the wall opens on a block of one letter: {grades}"
    assert dcs[wall[0]]["identity"]["country"] != dcs[wall[3]]["identity"]["country"]


def test_zz_fixtures_never_on_the_home():
    dcs, results = _corpus([60.0, 60.0])
    dcs["zz-fixture"] = _dc("zz-fixture")
    results["zz-fixture"] = _result(60.0)
    out = build_showcase(dcs, results)
    assert all(not c["id"].startswith("zz-") for c in out["demo_candidates"])
    assert all(not i.startswith("zz-") for i in out["wall_candidates"])
