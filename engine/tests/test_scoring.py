# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Numbers asserted here were computed BY HAND from the draft methodology —
they are an independent check of the engine, not a copy of its output."""

from engine.scoring import score_datacenter


def test_alpha_dual_grades(methodology, alpha):
    r = score_datacenter(alpha, methodology)
    site = r["grades"]["site"]
    # no editorial gloss: the letter and the one-decimal score, nothing else
    assert (site["grade"], site["score"]) == ("B", 79.5)
    assert "close_to" not in site
    pp = r["grades"]["project_process"]
    assert (pp["grade"], pp["score"], pp["coverage"]) == ("C", 62.3, 1.0)


def test_alpha_confidence_two_causes(methodology, alpha):
    c = score_datacenter(alpha, methodology)["confidence"]
    assert c["level"] == "high"
    assert c["causes"]["missing_data"] == 0.0
    assert c["causes"]["unverifiable_declarative"] == 0.098  # E4+W4+L4+L5 importance share


def test_beta_site_grade_on_rounded_score(methodology, beta):
    site = score_datacenter(beta, methodology)["grades"]["site"]
    # raw 34.95 rounds to the published 35.0 -> graded D: the published number
    # and the published letter can never contradict each other
    assert (site["grade"], site["score"]) == ("D", 35.0)


def test_beta_project_process_insufficient_data(methodology, beta):
    pp = score_datacenter(beta, methodology)["grades"]["project_process"]
    assert pp == {"grade": "insufficient_data", "coverage": 0.0}


def test_beta_confidence_missing_cause(methodology, beta):
    c = score_datacenter(beta, methodology)["confidence"]
    assert c["level"] == "medium"
    assert c["causes"]["missing_data"] == 0.289
    assert c["causes"]["unverifiable_declarative"] == 0.0


def test_insufficient_data_cascades_to_pillar_subscores(methodology, beta):
    pillars = score_datacenter(beta, methodology)["pillars"]
    # a pillar below the coverage floor is never given a punitive letter drawn from unknowns
    assert pillars["transparency_governance"] == {"grade": "insufficient_data", "coverage": 0.0}
    assert pillars["energy"]["grade"] == "E"  # known and bad is still graded (coverage 0.833)
    assert pillars["energy"]["coverage"] == 0.833
    assert pillars["local_impact"]["coverage"] == 0.4  # exactly at the floor: graded


def test_alpha_pillar_subscores(methodology, alpha):
    pillars = score_datacenter(alpha, methodology)["pillars"]
    assert pillars["land_biodiversity"]["grade"] == "A"
    assert pillars["land_biodiversity"]["score"] == 87.5
    assert set(pillars) == {"energy", "water", "land_biodiversity", "local_impact", "transparency_governance"}


def test_documentation_accompanies_every_grade(methodology, alpha):
    # Product rule n°1: a letter is never shown without its documentation chip.
    r = score_datacenter(alpha, methodology)
    for badge in ("site", "project_process"):
        doc = r["grades"][badge]["documentation"]
        assert doc["level"] in {"high", "medium", "low"}
        assert 1 <= doc["dots"] <= 4
        assert set(doc["label"]) == {"fr", "en"}
    for pillar, detail in r["pillars"].items():
        assert 1 <= detail["documentation"]["dots"] <= 4, pillar
        assert set(detail["documentation"]["label"]) == {"fr", "en"}


def test_no_documentation_without_a_grade(methodology, beta):
    # insufficient_data means no letter — and therefore no documentation chip either.
    r = score_datacenter(beta, methodology)
    assert r["grades"]["project_process"] == {"grade": "insufficient_data", "coverage": 0.0}
    assert "documentation" not in r["pillars"]["transparency_governance"]


def test_citable_quote_contrasts_when_a_pillar_is_worse(methodology, beta):
    # beta: site D; worst graded pillar is local_impact E (score 16.2, below energy/water E)
    # -> the generated headline names that contrast, tie-broken by the lowest score.
    q = score_datacenter(beta, methodology)["citable_quote"]
    # French guillemets carry non-breaking spaces (correct typography) -> normalize to compare.
    assert q["fr"].replace(chr(0xa0), " ") == "Noté D sur le site, mais E sur « Impact local »."
    assert q["en"] == "Rated D on site, but E on “Local impact”."


def test_citable_quote_is_factual_without_a_worse_pillar(methodology, alpha):
    # alpha: no graded pillar worse than site B -> no invented contrast, both notes stated.
    q = score_datacenter(alpha, methodology)["citable_quote"]
    assert q["fr"] == "Noté B sur le site, C en projet & processus."
    assert q["en"] == "Rated B on site, C on project & process."


def test_grade_boundary_is_inclusive(methodology, alpha):
    thresholds = {t["grade"]: t["min"] for t in methodology["grade_thresholds"]}
    assert thresholds["B"] == 65  # sanity: draft grid
    from engine.scoring import _grade
    assert _grade(65.0, methodology)["grade"] == "B"
    assert _grade(64.949, methodology)["grade"] == "C"  # rounds to 64.9
