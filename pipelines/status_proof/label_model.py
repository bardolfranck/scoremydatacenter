# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Weak-supervision label model with calibrated abstention (R&D, topo-ml-statut.md).

Each signal is a noisy labeling function (LF) voting OP (running) or PROJ (not running),
weighted by its MEASURED precision. An LF below the reliability floor is silenced (it never
decides). P(operational) = sigmoid(weighted votes). Outside the confident band → ABSTAIN:
the fiche shows « statut non vérifié », automatically, with no human in the loop.

Measured precisions (v1 hand-verify, 2026-09-17): PeeringDB bind with net_count>0 = 25/25;
developer-class = 1/1 (too thin to decide alone); OSM lifecycle ≈ 0/88; DCWatch project 0/6.
A new signal (SIREN operator_type, coord_quality…) plugs in as one more LF with its measured
precision — never with a guessed one.
"""

import math

LF_PRECISION = {
    "peeringdb_live": 0.99,       # bind + net_count > 0 (25/25, shrunk off 1.0 for small N)
    "developer": 0.90,            # pure real-estate developer (1/1) — cannot decide alone
    "osm_lifecycle": 0.10,        # proximity noise on operating campuses — silenced
    "dcwatch_project": 0.15,      # campus-expansion confusions — silenced
}
LF_VOTE = {"peeringdb_live": "OP", "developer": "PROJ", "osm_lifecycle": "PROJ", "dcwatch_project": "PROJ"}
RELIABILITY_FLOOR = 0.70
LOGIT_SCALE = 2.5
HI, LO = 0.90, 0.10               # auto-decide only outside [LO, HI]


def weight(precision):
    return 0.0 if precision < RELIABILITY_FLOOR else (precision - 0.5) * 2.0


def p_operational(fired):
    """(P(operational), LFs used) from the set of fired LF names; (None, []) if none reliable."""
    s, used = 0.0, []
    for lf in sorted(fired):
        w = weight(LF_PRECISION[lf])
        if w == 0:
            continue
        s += (w if LF_VOTE[lf] == "OP" else -w) * LOGIT_SCALE
        used.append(lf)
    if not used:
        return None, []
    return 1 / (1 + math.exp(-s)), used


def decide(p):
    """confirm_op | demote | abstain."""
    if p is None:
        return "abstain"
    if p >= HI:
        return "confirm_op"
    if p <= LO:
        return "demote"
    return "abstain"
