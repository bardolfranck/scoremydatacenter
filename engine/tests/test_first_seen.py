# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Phase-1: scored fiches carry identity.first_seen in the served projection (map + dc + scores),
for a « derniers scorés » banner. A DATE (first recorded), never a grade date. Free-floor field
(SEAU_A_KEYS) — Seau A contract change, signed off with codeur-API."""
import json
import tempfile
from pathlib import Path

from engine.artifacts import build_artifacts
from engine.core import load_datacenters, load_methodology


def test_first_seen_projects_from_identity():
    dcs = load_datacenters()
    assert dcs, "need the zz- fixtures"
    a_id = sorted(dcs)[0]
    dcs[a_id]["identity"]["first_seen"] = "2026-07-14"   # inject on one fixture (in-memory)
    with tempfile.TemporaryDirectory() as d:
        build_artifacts(dcs, load_methodology(), out_dir=Path(d))
        mp = json.loads((Path(d) / "map.geojson").read_text())
        dcj = json.loads((Path(d) / "dc" / f"{a_id}.json").read_text())
    feat = next(f for f in mp["features"] if f["properties"]["id"] == a_id)
    assert feat["properties"]["first_seen"] == "2026-07-14"
    assert dcj["first_seen"] == "2026-07-14"
    # still no sellable field alongside it
    assert "pillars" not in feat["properties"] and "power_mw" not in feat["properties"]
