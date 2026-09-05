# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""A-19 firewall — the internal validation study cohort is never PUBLICLY graded.

The « note = indicateur avancé » validation needs an unbiased cohort: ALL detectable
EU pipeline projects (contested AND not), scored on their STRUCTURAL grade for the
study. But many of those projects are, publicly, « en veille » (A-19: watched, not
graded). Their study grade is an internal exposure variable — it must NEVER leak into
what we SERVE, or we would be publishing a grade on an « en veille » project.

This guard makes the firewall a build invariant, not a promise (same spirit as the
Israel scrub and the non-circularity guard). It reads the study-cohort manifest
(`data/validation_study_ids.json`) and asserts: any manifest id that appears in the
served artifacts carries the scrubbed sentinel grade « en_attente », NEVER a real A–E
letter. Empty manifest today → passes trivially, armed the day the cohort is built:
the first study grade that leaks into a served file breaks the build LOUDLY.

Runs against the SERVED artifacts (site/public/data) when present — that is exactly
what ships. Absent (a fresh clone with only zz- fixtures) → the guard is inert.
"""

import json
from pathlib import Path

from engine.core import DATA_DIR

SERVED = DATA_DIR.parent / "site" / "public" / "data"
SENTINEL = "en_attente"
REAL_GRADES = {"A", "B", "C", "D", "E"}


def _study_ids():
    manifest = DATA_DIR / "validation_study_ids.json"
    if not manifest.exists():
        return set()
    return set(json.loads(manifest.read_text()).get("ids", []))


def _served_grade(dc_id):
    """The site grade this id is SERVED with, or None if not served."""
    fiche = SERVED / "dc" / f"{dc_id}.json"
    if fiche.exists():
        g = json.loads(fiche.read_text()).get("grades", {}).get("site", {})
        return g.get("grade")
    return None


def test_study_cohort_is_never_served_with_a_real_grade():
    study = _study_ids()
    if not study or not SERVED.exists():
        return  # inert: no cohort yet, or a bare clone
    leaks = []
    # (a) per-fiche served grade
    for dc_id in study:
        g = _served_grade(dc_id)
        if g in REAL_GRADES:
            leaks.append(f"{dc_id}:dc.json={g}")
    # (b) scores.json / map.geojson leaderboard + map layers
    scores = SERVED / "scores.json"
    if scores.exists():
        data = json.loads(scores.read_text())
        rows = data if isinstance(data, list) else []
        for x in rows:
            if x.get("id") in study and x.get("grades", {}).get("site", {}).get("grade") in REAL_GRADES:
                leaks.append(f"{x['id']}:scores.json")
    geo = SERVED / "map.geojson"
    if geo.exists():
        for f in json.loads(geo.read_text()).get("features", []):
            p = f.get("properties", {})
            if p.get("id") in study and p.get("grade_site") in REAL_GRADES:
                leaks.append(f"{p['id']}:map.geojson")
    assert not leaks, (
        "A-19 FIREWALL BREACH — internal study-cohort projects are SERVED with a real "
        f"grade (must be « {SENTINEL} »): {leaks[:10]}… A study grade is an internal "
        "exposure variable for the precursor validation; publishing it on an « en veille » "
        "project violates A-19. Scrub it, or remove the id from the study manifest."
    )
