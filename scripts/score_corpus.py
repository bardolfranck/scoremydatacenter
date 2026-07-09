# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Score a calibration corpus from a directory of DC source files (reproducible weight iteration).

    python scripts/score_corpus.py <corpus_datacenters_dir> [<out_dir>]

The corpus lives OUTSIDE the public repo (nominative drafts → private newsroom, A-11); the engine
scores from those pinned sources so that between two runs **only the methodology weights change**,
never the facts. Loads the active methodology from the repo, scores every `*.json` in the corpus dir
(skipping any that fail, with a message — never aborts the batch), writes the artifacts, and prints
the grade distribution. Default out_dir is `site/public/data` (git-ignored).

This is a dev/calibration entry point, not part of the public build: `make score` still scores the
published `data/datacenters/`. Use this to re-score the calibration corpus after a weight change.
"""

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.core import load_methodology            # noqa: E402
from engine.scoring import score_datacenter          # noqa: E402
from engine.artifacts import build_artifacts         # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: score_corpus.py <corpus_datacenters_dir> [<out_dir>]", file=sys.stderr)
        return 2
    corpus = Path(argv[0])
    out = Path(argv[1]) if len(argv) > 1 else REPO / "site" / "public" / "data"
    methodology = load_methodology()

    good, skipped = {}, []
    for p in sorted(corpus.glob("*.json")):
        try:
            dc = json.loads(p.read_text())
            score_datacenter(dc, methodology)         # validate it scores before the batch build
            good[dc["id"]] = dc
        except Exception as exc:
            skipped.append(f"{p.name}: {exc}")

    build_artifacts(good, methodology, out_dir=out, watchlist=[])

    site = Counter(score_datacenter(dc, methodology)["grades"]["site"]["grade"] for dc in good.values())
    pp = Counter(score_datacenter(dc, methodology)["grades"]["project_process"]["grade"] for dc in good.values())
    print(f"corpus: {len(good)} scored → {out}  (methodology {methodology['version']})", file=sys.stderr)
    print(f"  site grade         : {dict(sorted(site.items()))}", file=sys.stderr)
    print(f"  project & process  : {dict(sorted(pp.items()))}", file=sys.stderr)
    if skipped:
        print(f"  skipped {len(skipped)}: {skipped}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
