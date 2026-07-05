import pytest

from engine.core import GateError
from engine.normalize import normalized_score


def _definition(methodology, indicator_id):
    return next(i for i in methodology["indicators"] if i["id"] == indicator_id)


def _entry(indicator_id, value, status="measured"):
    return {"id": indicator_id, "value": value, "status": status,
            "source": {"title": "t", "url": "https://example.org", "accessed": "2026-07-01"}}


def test_thresholds_boundaries_inclusive(methodology, parameters):
    e1 = _definition(methodology, "E1")  # <=50:100, <=150:60, <=400:30, above:0
    for value, expected in [(50, 100), (50.1, 60), (150, 60), (400, 30), (401, 0)]:
        assert normalized_score(e1, _entry("E1", value), parameters) == expected


def test_bounded_linear_higher_is_better_with_clamp(methodology, parameters):
    l4 = _definition(methodology, "L4")  # 0..50 jobs per 100 MW
    entry = _entry("L4", 25, status="announced")
    capped = normalized_score(l4, entry, parameters)
    assert capped == 50  # 50/100 linear, below the declarative cap
    entry_high = _entry("L4", 999, status="announced")
    assert normalized_score(l4, entry_high, parameters) == parameters["declarative_score_cap"]  # clamp then cap


def test_categorical_lookup_and_rejection(methodology, parameters):
    w1 = _definition(methodology, "W1")
    assert normalized_score(w1, _entry("W1", "zre_or_crisis"), parameters) == 0
    with pytest.raises(GateError):
        normalized_score(w1, _entry("W1", "not_a_category"), parameters)


def test_proxy_rubric_alpha_case(methodology, parameters, alpha):
    t1_def = _definition(methodology, "T1")
    t1 = next(e for e in alpha["indicators"] if e["id"] == "T1")
    # inquiry(25) + AE with reservations(15) + no CNDP(5) + 0 appeals(20) + council favorable(15)
    assert normalized_score(t1_def, t1, parameters) == 80


def test_declarative_cap_applies_to_announced_only(methodology, parameters):
    e4 = _definition(methodology, "E4")  # PUE 1.18 normalizes to 100
    announced = _entry("E4", 1.18, status="announced")
    assert normalized_score(e4, announced, parameters) == parameters["declarative_score_cap"]
    measured = _entry("E4", 1.18, status="measured")
    measured["verification_source"] = measured["source"]
    assert normalized_score(e4, measured, parameters) == 100  # ex-post verified: uncapped


def test_missing_returns_none(methodology, parameters):
    e4 = _definition(methodology, "E4")
    assert normalized_score(e4, {"id": "E4", "status": "missing"}, parameters) is None
