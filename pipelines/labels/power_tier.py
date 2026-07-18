# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Classify where each `power_mw` came from — ONE definition, three consumers.

    python -m pipelines.labels.power_tier <newsroom_calibration_dir> [--json]

WHY. `power_mw` feeds three things that must not treat all figures alike: the MW-tranche
estimator (training labels), L2 (MW per 1000 inhabitants — a SCORED indicator), and the future
MW-weighted index. Measured 2026-07-18, the classes are not comparable:

  * regulatory (EED registers) — the operator declares under legal obligation, the regulator
    publishes, and the declaration states its own basis (installed vs rated IT power);
  * open-common / aggregator / press — wrong by a factor of 2 to 13 against the operator's own
    figure (Atman Warsaw 57 vs 12.1 · DATASIX Vienna 3.0 vs 0.712 · Digital Realty DUS1 2.3 vs 23
    between two aggregators · CyrusOne AMS1 54 harvested vs 27 in the Dutch register).

WHY A PARSER AND NOT A FIELD. The scored record cannot carry this: `datacenter.schema.json` sets
`additionalProperties: false` on both the root and `identity`, and `power_mw` is a bare number.
Adding a structured `power_source` is a change to the PUBLIC schema contract — a methodology call
(A-16), not an implementation detail. Meanwhile the provenance is already recorded, just in prose:
the L2 source title carries e.g. "puissance 7.0 MW (DCWatch ODbL, export 7dd5b5e9)". This module
reads that, so nothing is mutated and no contract moves — and every consumer shares one definition
instead of re-inventing the regex. When the schema does gain the field, delete the parser, keep
the tiers.

Tiers are ordered: regulatory > open_common > press > unknown. `unknown` is never silently
promoted — an unattributed figure stays unattributed.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

TIERS = ("regulatory", "open_common", "press", "unknown")
_POWER_IN_L2 = re.compile(r"puissance\s+[\d.]+\s*MW\s*\(([^)]+)\)", re.I)
_OPEN_COMMON = re.compile(r"DCWatch|Hubblo", re.I)
_PRESS = re.compile(r"presse|press|CNDP|concertation|communiqu", re.I)


def classify(dc: dict, provenance: dict | None) -> dict:
    """Return {tier, confidence, source, basis, evidence} for this DC's power_mw."""
    out = {"dc_id": dc.get("id"), "power_mw": (dc.get("identity") or {}).get("power_mw"),
           "tier": "unknown", "confidence": "none", "source": None, "basis": None, "evidence": None}
    if out["power_mw"] is None:
        out["tier"] = None
        return out

    # 1) Regulatory: an EED register block in the provenance sidecar. It also states its own basis,
    #    which is the whole reason this tier is trustworthy.
    rvo = (provenance or {}).get("rvo_eed") or {}
    if rvo.get("it_power_mw") is not None:
        out.update(tier="regulatory", confidence="high", source=rvo.get("source") or "EED register",
                   basis=rvo.get("it_power_basis"), evidence=rvo.get("url"))
        return out

    # 2) Otherwise the attribution lives in the L2 source title (prose). Parse, never guess.
    l2 = next((i for i in dc.get("indicators", []) if i.get("id") == "L2"), None)
    title = ((l2 or {}).get("source") or {}).get("title") or ""
    m = _POWER_IN_L2.search(title)
    if not m:
        return out
    cited = m.group(1).strip()
    out["source"] = cited
    out["evidence"] = title[:200]
    if _OPEN_COMMON.search(cited):
        # An open common (ODbL) — real provenance, but the figure's basis is undeclared: it may be
        # IT load, grid feed or full-build. That ambiguity is what makes the class low-confidence.
        out.update(tier="open_common", confidence="low", basis="undeclared")
    elif _PRESS.search(cited):
        out.update(tier="press", confidence="low", basis="undeclared")
    return out


def census(calibration_dir: Path) -> list[dict]:
    rows = []
    for path in sorted(calibration_dir.glob("datacenters*/*.json")):
        if path.name.endswith((".provenance.json", ".draft.json")):
            continue
        dc = json.loads(path.read_text())
        sidecar = path.with_name(path.name.replace(".json", ".provenance.json"))
        prov = json.loads(sidecar.read_text()) if sidecar.exists() else None
        row = classify(dc, prov)
        if row["tier"] is not None:
            rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("calibration_dir", type=Path)
    ap.add_argument("--json", action="store_true", help="emit one JSON line per data centre")
    args = ap.parse_args(argv)
    rows = census(args.calibration_dir)
    if args.json:
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))
        return 0
    by_tier = Counter(r["tier"] for r in rows)
    print(f"power_mw present on {len(rows)} data centres")
    for tier in TIERS:
        n = by_tier.get(tier, 0)
        if n:
            print(f"  {tier:12} {n:>4}  ({n / len(rows) * 100:.0f}%)")
    scored = [r for r in rows if r["tier"] in ("open_common", "press", "unknown")]
    print(f"\n{len(scored)} of them are low-confidence or unattributed — L2 is a SCORED indicator, "
          f"so that is the audit surface.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
