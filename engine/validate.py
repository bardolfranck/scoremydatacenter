"""Validation gates (phase 0 stub).

Phase 1 implements the real gates: JSON Schema validation, business rules
(mandatory sources, announced-vs-measured, contradictory-review state,
threshold traceability) and the transparency-floor property. Until then this
stub only checks the repository layout so `make build` exercises the full
chain on an empty dataset.
"""

import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main() -> int:
    for sub in ("datacenters", "methodology", "schema"):
        if not (DATA_DIR / sub).is_dir():
            print(f"validate: missing directory data/{sub}", file=sys.stderr)
            return 1
    files = sorted((DATA_DIR / "datacenters").glob("*.json"))
    print(f"validate: {len(files)} datacenter file(s) found — phase 0 scaffold, no gates active yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
