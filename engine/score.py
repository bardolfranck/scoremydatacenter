"""Score computation (phase 0 stub).

Phase 1 implements the real chain: normalization, prudent-declarative cap,
dual grade (site / project-process), two-cause confidence, letter grades and
the generated artifacts under site/public/data/. This stub keeps the build
chain runnable on an empty dataset.
"""

import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main() -> int:
    files = sorted((DATA_DIR / "datacenters").glob("*.json"))
    print(f"score: {len(files)} datacenter file(s) — no artifacts generated (phase 0 scaffold)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
