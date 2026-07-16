# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""stats.json contract (T0 « Les chiffres du parc », cadrage §4.10):
published values only, exclusions counted apart, wired-country rule,
n-minimum gate, deterministic output."""

import json

from engine.stats import STATS_MIN_N, build_stats

METHODOLOGY = {
    "version": "0.1.0-test",
    "indicators": [
        {"id": "E2", "mvp": True}, {"id": "W1", "mvp": True}, {"id": "E4", "mvp": True},
        {"id": "XX", "mvp": False},
    ],
}


def _dc(dc_id, country, e2=("measured", "saturated"), w1=("measured", "high"),
        e4=("not_collected", None), status="operational", power=10.0, admin=None,
        accessed="2026-07-01"):
    return {
        "id": dc_id,
        "identity": {
            "name": dc_id, "country": country, "admin_area": admin,
            "project_status": status, "power_mw": power,
            "municipality": "x", "operator": "x", "summary": {},
            "coordinates": {"lat": 0, "lon": 0},
        },
        "indicators": [
            {"id": "E2", "status": e2[0], "value": e2[1],
             "source": {"title": "t", "url": "u", "accessed": accessed}},
            {"id": "W1", "status": w1[0], "value": w1[1]},
            {"id": "E4", "status": e4[0], "value": e4[1]},
        ],
        "publication": {"status": "published"},
        "score_history": [],
    }


def _corpus(n_fr=STATS_MIN_N + 2):
    dcs = {}
    for i in range(n_fr):
        # half saturated, half adequate; W1: one zre, rest no_stress
        e2 = ("measured", "saturated" if i % 2 == 0 else "adequate")
        w1 = ("measured", "zre_or_crisis" if i == 0 else "no_stress")
        dcs[f"fr-{i:02d}"] = _dc(f"fr-{i:02d}", "FR", e2=e2, w1=w1, admin="77")
    return dcs


def test_share_counts_and_exclusions_apart():
    dcs = _corpus()
    dcs["fr-miss"] = _dc("fr-miss", "FR", e2=("missing", None), admin="91")
    stats = build_stats(dcs, METHODOLOGY)
    s = stats["perimeters"]["FR"]["stats"]["grid_saturated"]
    # the missing site is OUT of the denominator AND counted apart
    assert s["n"] == STATS_MIN_N + 2
    assert s["excluded"] == {"missing": 1}
    assert s["num"] == (STATS_MIN_N + 2 + 1) // 2
    assert s["countries"] == ["FR"]


def test_unwired_country_never_aggregated():
    dcs = _corpus()
    # DE exists in the corpus but its E2 campaign never ran there
    dcs["de-0"] = _dc("de-0", "DE", e2=("not_collected", None))
    stats = build_stats(dcs, METHODOLOGY)
    s = stats["perimeters"]["europe"]["stats"]["grid_saturated"]
    assert "DE" not in s["countries"]
    assert s["countries_excluded"] == ["DE"]
    # and the DE site is not silently swallowed into the denominator
    assert s["n"] == STATS_MIN_N + 2


def test_gate_below_min_n():
    dcs = {f"be-{i}": _dc(f"be-{i}", "BE") for i in range(STATS_MIN_N - 1)}
    stats = build_stats(dcs, METHODOLOGY)
    peri = stats["perimeters"]["BE"]
    assert "grid_saturated" not in peri["stats"]
    assert peri["gated"]["grid_saturated"] == STATS_MIN_N - 1


def test_publish_rate_keeps_silence_in_denominator():
    dcs = _corpus()
    dcs["fr-pue"] = _dc("fr-pue", "FR", e4=("announced", "1.2"), admin="75")
    stats = build_stats(dcs, METHODOLOGY)
    s = stats["perimeters"]["FR"]["stats"]["pue_published"]
    # denominator = every site of the wired country; silence counted apart
    assert s["n"] == STATS_MIN_N + 3
    assert s["num"] == 1
    assert s["excluded"]["not_collected"] == STATS_MIN_N + 2


def test_pipeline_discloses_the_undisclosed():
    dcs = _corpus()
    dcs["fr-p1"] = _dc("fr-p1", "FR", status="announced", power=100.0, admin="59")
    dcs["fr-p2"] = _dc("fr-p2", "FR", status="permitting", power=None, admin="59")
    stats = build_stats(dcs, METHODOLOGY)
    p = stats["perimeters"]["FR"]["stats"]["pipeline"]
    assert p["projects"] == 2
    assert p["mw_announced"] == 100
    assert p["mw_disclosed_n"] == 1 and p["mw_undisclosed_n"] == 1


def test_regions_group_by_and_zz_fixtures_ignored():
    dcs = _corpus()
    dcs["zz-fixture"] = _dc("zz-fixture", "FR", admin="77")
    stats = build_stats(dcs, METHODOLOGY)
    fr = stats["perimeters"]["FR"]
    assert fr["n_sites"] == STATS_MIN_N + 2  # zz- fixture never counted
    assert "ile-de-france" in fr["regions"]
    assert fr["regions"]["ile-de-france"]["n_sites"] == STATS_MIN_N + 2


def test_watchlist_scoped_to_perimeter_countries():
    dcs = _corpus()
    watchlist = [
        {"id": "w1", "country": "FR", "facts": [{"kind": "opposition"}]},
        {"id": "w2", "country": "FR", "facts": [{"kind": "moratorium"}, {"kind": "opposition"}]},
        {"id": "w3", "country": "US", "facts": [{"kind": "opposition"}]},
    ]
    stats = build_stats(dcs, METHODOLOGY, watchlist)
    o = stats["perimeters"]["FR"]["stats"]["oppositions"]
    assert o["entries"] == 2  # the US entry never leaks into a European perimeter
    assert o["kinds"] == {"moratorium": 1, "opposition": 1}


def test_deterministic_and_dated():
    dcs = _corpus()
    a = json.dumps(build_stats(dcs, METHODOLOGY), sort_keys=True)
    b = json.dumps(build_stats(dcs, METHODOLOGY), sort_keys=True)
    assert a == b
    stats = build_stats(dcs, METHODOLOGY)
    assert stats["corpus_date"] == "2026-07-01"
    assert stats["methodology_version"] == "0.1.0-test"
    assert stats["min_n"] == STATS_MIN_N


def test_exemplars_mechanical_and_optional():
    dcs = _corpus()
    # without results: absent (grades unknown)
    assert "exemplars" not in build_stats(dcs, METHODOLOGY)["perimeters"]["FR"]
    results = {k: {"grades": {"site": {"grade": "C"}},
                   "confidence": {"level": "medium", "score": 0.5 + i / 100}}
               for i, k in enumerate(sorted(dcs))}
    stats = build_stats(dcs, METHODOLOGY, None, results)
    ex = stats["perimeters"]["FR"]["exemplars"]
    assert set(ex) == {"representative", "constrained", "documented"}
    # documented = highest confidence score (last id by construction)
    assert ex["documented"]["id"] == sorted(dcs)[-1]
    # constrained = max frictions, deterministic tie-break by id
    fr = [d for d in sorted(dcs)]
    assert ex["constrained"]["frictions"] >= 1


def test_map_points_flag_and_rounding():
    dcs = _corpus()
    stats = build_stats(dcs, METHODOLOGY)
    pts = stats["perimeters"]["FR"]["points"]
    assert len(pts) == len(dcs)
    assert all(len(p) == 3 and p[2] in (0, 1) for p in pts)
