# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Migrate L2 to prudent status where its power figure is non-regulatory (memo 2026-07-19).

    python scripts/migrate_l2_prudence.py <corpus_datacenters_dir> [--apply]

An aggregator/press/operator MW is an unverified third-party claim: L2 built on it moves
`measured` -> `announced` (declarative cap + confidence penalty — existing engine semantics,
no new machinery). Regulatory-tier power (EED register) keeps `measured`. Unattributed prose
('unknown') is flipped too when a power figure is present in the canonical prose — an
unattributed figure cannot claim `measured` — but fictional/no-power entries are untouched.
Dry-run by default; --apply writes in place. Gate 9 enforces this invariant from now on.
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pipelines.labels.power_tier import classify, _POWER_IN_L2  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus_dir", type=Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    flipped, kept_regulatory, untouched = [], [], 0
    for path in sorted(args.corpus_dir.glob("*.json")):
        dc = json.loads(path.read_text())
        sidecar = path.with_name(path.name.replace(".json", ".provenance.json"))
        prov = json.loads(sidecar.read_text()) if sidecar.exists() else None
        l2 = next((e for e in dc.get("indicators", []) if e.get("id") == "L2"), None)
        if not l2 or l2.get("status") != "measured":
            untouched += 1
            continue
        tier = classify(dc, prov)["tier"]
        title = ((l2.get("source") or {}).get("title")) or ""
        has_power_prose = bool(_POWER_IN_L2.search(title))
        if tier == "regulatory":
            kept_regulatory.append(dc.get("id"))
        elif tier in ("operator", "open_common", "press") or (tier == "unknown" and has_power_prose):
            l2["status"] = "announced"
            flipped.append((dc.get("id"), tier))
            if args.apply:
                path.write_text(json.dumps(dc, ensure_ascii=False, indent=2))
        else:
            untouched += 1  # no power prose at all (e.g. fictional census) — Gate 9 is lenient here

    mode = "APPLIED" if args.apply else "dry-run"
    print(f"[{mode}] L2 measured->announced: {len(flipped)} | kept measured (regulatory): "
          f"{len(kept_regulatory)} | untouched: {untouched}", file=sys.stderr)
    for dcid, tier in flipped[:10]:
        print(f"  {dcid}  ({tier})", file=sys.stderr)
    if len(flipped) > 10:
        print(f"  … +{len(flipped) - 10}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
