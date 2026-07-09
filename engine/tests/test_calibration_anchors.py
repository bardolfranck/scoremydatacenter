# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Retrospective calibration ANCHORS (iter-1) — the two known-outcome poles the
grid must be calibrated toward, encoded as tracked targets rather than as
already-met assertions.

Unlike gate 6 (`test_retrospective.py`, which pins the *published* corpus and must
stay green), these two anchors are nominative calibration cases whose live sources
are pinned in the private newsroom corpus (A-11). Here they carry ONLY the public
indicator vectors (no operator identity, no URLs) so the target can live in public CI.

Both targets are currently UNMET — they are `xfail(strict=True)`:
  * a passing anchor flips CI red (XPASS) the day calibration reaches it, forcing
    this marker to be removed and the target promoted to a hard assertion;
  * meanwhile CI stays green and the calibration debt is explicit, not silent.

Findings that make each target fail today (iter-1, 32-DC corpus):
  * E-anchor SITE=E is unreachable: the base/site thresholds collapse the whole
    corpus onto {B, C} — even a ~1400 MW farmland hyperscaler on water-stressed,
    grid-saturated land scores C. The site thresholds need recalibration to express E.
  * A-anchor PROJECT_PROCESS∈{A,B} is unreachable retrospectively: an operational
    DC's governance dossier is a sourcing desert (only 2/5 T1 proxies sourceable),
    so the transparency pillar stays below the coverage floor → insufficient_data.
    F5 (heat recovery, now MVP) alone cannot lift it. An A on project/process has to
    be earned by a *published* operator that discloses its project commitments, not
    reconstructed after the fact.
"""

import json
from pathlib import Path

import pytest

from engine.scoring import score_datacenter

ANCHORS = json.loads((Path(__file__).parent / "calibration_anchors.json").read_text())["anchors"]


def _dc(anchor: dict) -> dict:
    return {"id": anchor["id"], "indicators": anchor["indicators"]}


# MET at iter-2 (2026-07-09): base thresholds recalibrated (F2 agricultural→0 & weight
# swap with F1, E1 de-weighted intra-FR, W1 high tightened, L2 computed) — the anchor is
# now a hard assertion: any regression that makes E inexpressible again fails CI.
def test_e_anchor_site_is_E(methodology):
    a = ANCHORS["e_anchor_farmland_hyperscaler"]
    result = score_datacenter(_dc(a), methodology)
    assert result["grades"]["site"]["grade"] in a["target"]["site"]


@pytest.mark.xfail(strict=True, reason="retrospective governance unsourceable — project_process stays insufficient_data")
def test_a_anchor_project_process_is_AB(methodology):
    a = ANCHORS["a_anchor_heat_recovery"]
    result = score_datacenter(_dc(a), methodology)
    assert result["grades"]["project_process"]["grade"] in a["target"]["project_process"]
