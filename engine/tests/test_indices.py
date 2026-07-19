# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Country SITE index — the §4 gates of the 2026-07-18/19 brief:
A-25 reserve inside the aggregation, rule n°1 (no grade without its
documentation), n<5 floor, site_index labelling, history idempotence."""

import json

from engine.indices import build_indices, update_history

METHODOLOGY = {
    "version": "0.1.0-test",
    "grade_thresholds": [
        {"min": 80, "grade": "A"}, {"min": 65, "grade": "B"}, {"min": 50, "grade": "C"},
        {"min": 35, "grade": "D"}, {"min": 0, "grade": "E"},
    ],
}


def _dc(dc_id, country, status="operational", power=10.0, verified=False,
        accessed="2026-07-01"):
    return {
        "id": dc_id,
        "identity": {"country": country, "project_status": status, "power_mw": power},
        "indicators": [
            {"id": "E1", "status": "measured", "value": 1,
             "source": {"title": "t", "url": "u", "accessed": accessed},
             **({"verification_source": {"title": "audit", "url": "u"}} if verified else {})},
        ],
        "score_history": [],
    }


def _result(score, conf=0.6):
    return {"grades": {"site": {"grade": "?", "score": score,
                                "documentation": {"score": conf}}},
            "confidence": {"level": "medium", "score": conf}}


def _country(cc, scores, verified=False, confs=None):
    dcs, results = {}, {}
    for i, sc in enumerate(scores):
        did = f"{cc.lower()}-{i:02d}"
        dcs[did] = _dc(did, cc, verified=verified and i == 0)
        results[did] = _result(sc, (confs or [0.6] * len(scores))[i])
    return dcs, results


def test_gate_reserve_a25_inside_aggregation():
    # a fictional country at >= 80 WITHOUT verification MUST come out B + reserved
    dcs, results = _country("XX", [85, 90, 82, 88, 84])
    idx = build_indices(dcs, METHODOLOGY, results)
    e = idx["countries"]["XX"]
    assert e["grade"] == "B" and e["reserved_from"] == "A"
    assert e["score"] >= 80  # the real score is kept

    # with one third-party verification in the country, the A stands
    dcs2, results2 = _country("YY", [85, 90, 82, 88, 84], verified=True)
    e2 = build_indices(dcs2, METHODOLOGY, results2)["countries"]["YY"]
    assert e2["grade"] == "A" and e2["reserved_from"] is None


def test_rule1_grade_never_without_documentation():
    dcs, results = _country("FR", [60, 55, 58, 62, 57])
    e = build_indices(dcs, METHODOLOGY, results)["countries"]["FR"]
    assert "grade" in e and "documentation" in e
    assert e["documentation"]["band"] in ("solide", "moyenne", "faible")
    assert isinstance(e["documentation"]["median"], float)


def test_floor_n5_no_score_emitted():
    dcs, results = _country("BE", [60, 55])
    e = build_indices(dcs, METHODOLOGY, results)["countries"]["BE"]
    assert e == {"n": 2, "eligible": False}  # no score, no grade — nothing


def test_labels_say_site():
    idx = build_indices({}, METHODOLOGY, {})
    assert idx["kind"] == "site_index"
    assert "SITE" in idx["labels"]["title"]["fr"] and "SITE" in idx["labels"]["title"]["en"]


def test_announced_sites_enter_the_mean_and_denominators_emitted():
    dcs, results = _country("FR", [60, 55, 58, 62, 57])
    dcs["fr-ann"] = _dc("fr-ann", "FR", status="announced")
    results["fr-ann"] = _result(30)
    e = build_indices(dcs, METHODOLOGY, results)["countries"]["FR"]
    assert e["n"] == 6                       # the announced site IS in the mean
    assert e["n_operational"] == 5 and e["n_announced"] == 1


def test_mw_weighted_only_with_local_labels():
    dcs, results = _country("FR", [60, 55, 58, 62, 57])
    e = build_indices(dcs, METHODOLOGY, results)["countries"]["FR"]
    assert "mw_weighted" in e and e["mw_weighted"]["sensitivity_delta"] is None
    # a country whose sites disclose no MW gets no mw_weighted block
    dcs2, results2 = _country("SE", [60, 55, 58, 62, 57])
    for d in dcs2.values():
        d["identity"]["power_mw"] = None
    e2 = build_indices(dcs2, METHODOLOGY, results2)["countries"]["SE"]
    assert "mw_weighted" not in e2


def test_history_idempotent_and_event_driven(tmp_path):
    dcs, results = _country("FR", [60, 55, 58, 62, 57])
    idx = build_indices(dcs, METHODOLOGY, results)
    hp = tmp_path / "indices_history.json"

    h1 = update_history(idx, hp)
    hp.write_text(json.dumps(h1))
    assert len(h1) == 1 and h1[0]["event"] == "new_country"

    # same corpus again -> STRICTLY identical history (idempotence gate)
    h2 = update_history(idx, hp)
    assert h2 == h1

    # continuous drift WITHOUT a grade change -> still no event
    results2 = {k: _result(v["grades"]["site"]["score"] + 1.0)
                for k, v in results.items()}
    idx2 = build_indices(dcs, METHODOLOGY, results2)
    assert update_history(idx2, hp) == h1

    # a real grade change -> exactly one new event
    results3 = {k: _result(80.0) for k in results}
    idx3 = build_indices(dcs, METHODOLOGY, results3)
    h3 = update_history(idx3, hp)
    assert len(h3) == 2 and h3[-1]["event"] == "grade_change"


def test_zz_fixtures_never_indexed():
    dcs, results = _country("FR", [60, 55, 58, 62, 57])
    dcs["zz-x"] = _dc("zz-x", "FR")
    results["zz-x"] = _result(99)
    e = build_indices(dcs, METHODOLOGY, results)["countries"]["FR"]
    assert e["n"] == 5
