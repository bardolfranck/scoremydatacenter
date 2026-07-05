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


def test_grade_boundary_is_inclusive(methodology, alpha):
    thresholds = {t["grade"]: t["min"] for t in methodology["grade_thresholds"]}
    assert thresholds["B"] == 65  # sanity: draft grid
    from engine.scoring import _grade
    assert _grade(65.0, methodology)["grade"] == "B"
    assert _grade(64.949, methodology)["grade"] == "C"  # rounds to 64.9
