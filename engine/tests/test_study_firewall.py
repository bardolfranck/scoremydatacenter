# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""A-19 firewall — the internal validation study cohort is never PUBLICLY graded.

The « note = indicateur avancé » validation needs an unbiased cohort: ALL detectable
EU pipeline projects (contested AND not), scored on their STRUCTURAL grade for the
study. Those study grades are an internal exposure variable. Publicly, the projects
stay « en veille » (A-19: watched, not graded) — so a study grade must NEVER reach a
SERVED artifact.

DESIGN (answer to the co-review): study fiches live in a SEPARATE analysis corpus
(private newsroom `validation/`), NEVER read by `build_prod_artifacts` — so by
construction they cannot enter the public build. This guard is the SAFETY NET
(defense in depth): if one is ever promoted into the served path by mistake, the
build breaks. No active scrub is needed (nothing enters the served build to blanch);
the physical separation is the primary firewall, this test is the tripwire.

Coverage — every grade-bearing surface the Israel scrub taught us to watch, caught by
a RECURSIVE scan of any key named `grade` / `grade_site` rather than an enumerated
list (so a new grade field is covered automatically):
  - dc/{id}.json      : grades.site.grade, grades.project_process.grade, every
                        pillars.*.grade
  - scores.json       : same, per study id (leaderboard)
  - map.geojson       : grade_site on the study feature
  - stats.json        : exemplars.*.grade_site (the vector that bit us on IL), and any
                        graded reference to a study id anywhere in the payload
A real A–E letter on a study id in any of these = A-19 breach → build broken. The
scrubbed sentinel « en_attente » (and `insufficient_data`) is fine — that is the
public « en veille » face. Empty manifest today → passes, armed.
"""

import json

from engine.core import DATA_DIR

SERVED = DATA_DIR.parent / "site" / "public" / "data"
REAL_GRADES = {"A", "B", "C", "D", "E"}
GRADE_KEYS = {"grade", "grade_site", "grade_project_process"}


def _study_ids():
    manifest = DATA_DIR / "validation_study_ids.json"
    if not manifest.exists():
        return set()
    return set(json.loads(manifest.read_text()).get("ids", []))


def _real_grades_in(obj):
    """Every real A–E letter carried by a grade-named field, anywhere in obj."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in GRADE_KEYS and isinstance(v, str) and v in REAL_GRADES:
                found.append((k, v))
            else:
                found += _real_grades_in(v)
    elif isinstance(obj, list):
        for v in obj:
            found += _real_grades_in(v)
    return found


def _records_for(study, container):
    """Yield (id, subtree) for every study id appearing anywhere in a served payload.
    Handles the {id: ...} dict rows (scores.json), geojson features, and stats.json
    exemplars/points — anything that is a dict carrying an `id` in the study set."""
    if isinstance(container, dict):
        if container.get("id") in study:
            yield container["id"], container
        # geojson features carry the id under properties
        props = container.get("properties")
        if isinstance(props, dict) and props.get("id") in study:
            yield props["id"], props
        for v in container.values():
            yield from _records_for(study, v)
    elif isinstance(container, list):
        for v in container:
            yield from _records_for(study, v)


def test_study_cohort_is_never_served_with_a_real_grade():
    study = _study_ids()
    if not study or not SERVED.exists():
        return  # inert: no cohort yet, or a bare clone

    leaks = []

    # (a) per-fiche served file — the richest surface (site, pp, every pillar)
    for dc_id in study:
        fiche = SERVED / "dc" / f"{dc_id}.json"
        if fiche.exists():
            for key, val in _real_grades_in(json.loads(fiche.read_text())):
                leaks.append(f"{dc_id}:dc.json:{key}={val}")

    # (b) consolidated artifacts — scan every study record wherever it appears
    for name in ("scores.json", "map.geojson", "stats.json"):
        path = SERVED / name
        if not path.exists():
            continue
        payload = json.loads(path.read_text())
        for dc_id, subtree in _records_for(study, payload):
            for key, val in _real_grades_in(subtree):
                leaks.append(f"{dc_id}:{name}:{key}={val}")

    assert not leaks, (
        "A-19 FIREWALL BREACH — internal study-cohort projects are SERVED with a real "
        f"grade (must be scrubbed « en_attente »): {sorted(set(leaks))[:12]}… A study "
        "grade is an internal exposure variable for the precursor validation; publishing "
        "it on an « en veille » project violates A-19. The study corpus must stay OUT of "
        "the served build (separate newsroom validation/), or the id leaves the manifest."
    )
