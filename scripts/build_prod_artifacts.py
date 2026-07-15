# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Rebuild the PRODUCTION site artifacts from the private newsroom calibration.

Two-repo hazard: `make score` reads the PUBLIC repo (only the zz- test fixtures) and
overwrites site/public/data with those 2 DCs — wiping the real corpus and the
watchlist from the served map. The production DCs (every `datacenters*` panel) and
the "En veille" watchlist live in the newsroom; this rebuilds the served artifacts
from there. Deterministic; no gate run (the calibration holds work-in-progress
drafts) — use `make score` / `make validate` for the public fixtures.

    make prod-artifacts                 # ../smdc-newsroom/calibration
    NEWSROOM_CAL=/path make prod-artifacts
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so `engine` imports when run as a file

from engine.artifacts import build_artifacts
from engine.core import ARTIFACTS_DIR, load_datacenters, load_methodology, load_watchlist

CAL = Path(os.environ.get("NEWSROOM_CAL", Path(__file__).resolve().parent.parent.parent / "smdc-newsroom" / "calibration"))


def main() -> int:
    if not (CAL / "datacenters").is_dir():
        raise SystemExit(f"newsroom calibration not found at {CAL} — clone smdc-newsroom or set NEWSROOM_CAL")
    dcs = load_datacenters(CAL)          # every datacenters* panel (FR, BE, …)
    dcs.update(load_datacenters())       # + the public zz- fixtures (tagged on site; carry the demo states)
    watchlist = load_watchlist(CAL)      # "En veille" 🗣️ layer
    results = build_artifacts(dcs, load_methodology(), out_dir=ARTIFACTS_DIR, watchlist=watchlist)
    de = sorted(i for i, r in results.items()
                if {r["grades"]["site"]["grade"], r["grades"]["project_process"]["grade"]} & {"D", "E"})
    print(f"prod-artifacts: {len(dcs)} DC + {len(watchlist)} watchlist entries → {ARTIFACTS_DIR}")
    print(f"prod-artifacts: exposure — {len(de)} DC(s) at D/E: " + (", ".join(de) if de else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
