# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Frozen analysis for the « note = indicateur avancé » pre-registration.

    python scripts/validation_precurseur.py <T0-snapshot.json> <outcomes.json>

THIS SCRIPT IS PART OF THE PREDICTION. It is committed AT THE TAG, with the
pre-registration, and run UNCHANGED at the T0+18-month deadline. Editing it after the
tag is a post-hoc degree of freedom — forbidden. (Pre-reg §6, refinement 3.)

Inputs:
  T0-snapshot.json : the immutable baseline (site grade + status + coords + operator
                     per site), frozen at T0. Exposure = site grade at T0.
  outcomes.json    : {site_id: {"contested": bool, "kind": ...}} — built by the veille
                     from events dated AFTER T0, joined to sites (coord<2km + operator).
                     Absent file → dry-run on the cohort only (power report, no outcome).

Metrics (frozen):
  - CO-PRIMARY A: Cochran-Armitage trend test across A→E (uses every stratum; robust to
    the thin A-B arm). Refinement 1.
  - CO-PRIMARY B: lift (relative risk) P(contested|D∪E)/P(contested|A∪B), with
    Haldane-Anscombe +0.5 continuity correction and a bootstrap 95% CI. Refinement 1.
  - Success (pre-specified): trend p<0.05 (one-sided, decreasing) AND lift≥2 with CI
    lower bound >1.
The result is published whatever it is (pre-reg §2). Ascertainment bias biases toward
the null (pre-reg §7), so a positive result is conservative.
"""

import json
import sys
from pathlib import Path

GRADE_ORDER = ["A", "B", "C", "D", "E"]
PIPELINE = {"announced", "permitting", "under_construction"}


def _cohort(snapshot):
    """Primary cohort: pipeline projects carrying a site grade at T0."""
    out = {}
    for rec in snapshot:
        gid = rec["id"]
        if gid.startswith(("zz-", "il-")):
            continue
        grade = rec.get("grade_site") or rec.get("grades", {}).get("site", {}).get("grade")
        if rec.get("project_status") in PIPELINE and grade in GRADE_ORDER:
            out[gid] = grade
    return out


def _cochran_armitage(by_grade):
    """Trend test on a 2xk table (contested yes/no across ordered grades A→E).
    Scores 0..4; returns (z, one-sided p for a DECREASING acceptability = increasing
    contestation from A to E). Pure stdlib (normal approx)."""
    from math import sqrt, erfc
    scores = {g: i for i, g in enumerate(GRADE_ORDER)}
    n_i = [by_grade[g][0] for g in GRADE_ORDER]
    x_i = [by_grade[g][1] for g in GRADE_ORDER]  # contested count
    N = sum(n_i)
    if N == 0:
        return None
    R = sum(x_i)
    t = [scores[g] for g in GRADE_ORDER]
    t_bar = sum(t[k] * n_i[k] for k in range(5)) / N
    num = sum((t[k] - t_bar) * x_i[k] for k in range(5))
    p_bar = R / N
    var = p_bar * (1 - p_bar) * sum(n_i[k] * (t[k] - t_bar) ** 2 for k in range(5))
    if var <= 0:
        return None
    z = num / sqrt(var)
    p_one_sided = 0.5 * erfc(z / sqrt(2))  # H1: trend increases with grade index (A→E)
    return {"z": round(z, 3), "p_one_sided_increasing": round(p_one_sided, 4)}


def _lift(by_grade):
    """Relative risk (D∪E vs A∪B) with Haldane-Anscombe +0.5 continuity correction."""
    hi_n = by_grade["A"][0] + by_grade["B"][0]
    hi_c = by_grade["A"][1] + by_grade["B"][1]
    lo_n = by_grade["D"][0] + by_grade["E"][0]
    lo_c = by_grade["D"][1] + by_grade["E"][1]
    p_hi = (hi_c + 0.5) / (hi_n + 1.0)
    p_lo = (lo_c + 0.5) / (lo_n + 1.0)
    return {"lift": round(p_lo / p_hi, 3), "exposed_DE": [lo_c, lo_n], "favorable_AB": [hi_c, hi_n],
            "note": "Haldane-Anscombe +0.5; bootstrap CI computed only when outcomes present"}


def main(argv):
    if not argv:
        print("usage: validation_precurseur.py <T0-snapshot.json> [outcomes.json]", file=sys.stderr)
        return 2
    raw = json.loads(Path(argv[0]).read_text())
    snapshot = raw["sites"] if isinstance(raw, dict) else raw  # snapshot carries metadata + sites[]
    cohort = _cohort(snapshot)
    from collections import Counter
    dist = Counter(cohort.values())
    print(f"cohort (pipeline, graded at T0): n={len(cohort)}  dist={dict(sorted(dist.items()))}", file=sys.stderr)
    print(f"  power arms — exposed D+E={dist['D']+dist['E']}  favorable A+B={dist['A']+dist['B']}", file=sys.stderr)

    if len(argv) < 2 or not Path(argv[1]).exists():
        print("  (no outcomes file — power dry-run only; no test run before the deadline)", file=sys.stderr)
        return 0

    outcomes = json.loads(Path(argv[1]).read_text())
    by_grade = {g: [0, 0] for g in GRADE_ORDER}  # [n, contested]
    for gid, grade in cohort.items():
        by_grade[grade][0] += 1
        if outcomes.get(gid, {}).get("contested"):
            by_grade[grade][1] += 1
    result = {
        "cohort_n": len(cohort),
        "by_grade": {g: {"n": by_grade[g][0], "contested": by_grade[g][1]} for g in GRADE_ORDER},
        "cochran_armitage": _cochran_armitage(by_grade),
        "lift": _lift(by_grade),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
