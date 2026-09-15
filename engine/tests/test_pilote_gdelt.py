"""Precursor-validation GDELT pilot — pure-logic tests (no network). Pins the query construction,
the ratio floor, and the load-bearing NOTE-BLIND invariant (no grade anywhere)."""
import json

import scripts.pilote_gdelt_precurseur as P


def test_queries_total_and_contestation():
    total, contest = P._queries({"operator": "Google", "commune": "Étrechet"})
    assert total == '"Google" "Étrechet" ("data center" OR datacenter OR "centre de données" OR Rechenzentrum)'
    assert contest.startswith(total)                 # contestation = TOTAL + terms
    assert "opposition OR recours" in contest and "bezwaar" in contest


def _fake_fetch(total_n, contest_n):
    def fetch(q, start, **k):
        n = total_n if q.endswith(P.DC_CONTEXT) else contest_n
        return {"articles": [{"title": f"t{i}", "url": f"http://x/{i}", "domain": "x.fr",
                              "seendate": "20250101T000000Z"} for i in range(n)]}
    return fetch


def test_ratio_and_floor(monkeypatch):
    monkeypatch.setattr(P, "_fetch", _fake_fetch(8, 3))
    out = P.run("20230101000000", sleep=lambda s: None)
    assert out["sites"][0]["ratio"] == 0.375         # 3/8, total >= floor
    monkeypatch.setattr(P, "_fetch", _fake_fetch(4, 2))
    out = P.run("20230101000000", sleep=lambda s: None)
    assert out["sites"][0]["ratio"] == "NA(<5)"      # total < floor → NA, never a misleading ratio


def test_note_blind_no_grade_anywhere(monkeypatch):
    monkeypatch.setattr(P, "_fetch", _fake_fetch(6, 2))
    out = P.run("20230101000000", sleep=lambda s: None)
    assert out["note_blind"] is True and len(out["sites"]) == 15
    blob = json.dumps(out).lower()
    for banned in ('"grade"', '"score"', '"grade_site"', '"letter"', '"provisional_band"'):
        assert banned not in blob                     # the pilot never reads/writes a grade
    assert {s["group"] for s in out["sites"]} == {"positive", "background"}   # discrimination read
