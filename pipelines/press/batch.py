# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Run the voie-A governance collector over a whole list of sites in one command.

    python -m pipelines.press.batch sites.csv --out ../smdc-newsroom/drafts/datacenters

Same input shape as the spatial batch (CSV header: name,operator,lat,lon[,...] or a JSON array).
One <id>.governance.json sidecar per row, keyed by id so re-runs refresh in place. A row that
fails is reported and skipped — it never aborts the batch. At the end a matrix shows, per site,
which deterministic proxies were filled — the at-a-glance governance-coverage view. Proposal only.
"""

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

from pipelines.spatial.http import SourceUnavailable
from .collect import collect, _DETERMINISTIC, _NEEDS_REVIEW


def _read_sites(path: Path) -> list[dict]:
    text = path.read_text()
    rows = json.loads(text) if path.suffix.lower() == ".json" else list(csv.DictReader(text.splitlines()))
    sites = []
    for i, r in enumerate(rows, 1):
        try:
            sites.append({
                "name": (r.get("name") or "").strip() or None,
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
            })
        except (KeyError, ValueError) as exc:
            print(f"  row {i}: skipped (bad input: {exc})", file=sys.stderr)
    return sites


def run(sites: list[dict], out_dir: Path, accessed: str, archive: bool = True) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for s in sites:
        try:
            sidecar = collect(s["lat"], s["lon"], name=s["name"], accessed=accessed, archive=archive)
        except SourceUnavailable as exc:
            print(f"  {s.get('name') or s['lat']},{s['lon']}: skipped ({exc})", file=sys.stderr)
            continue
        path = out_dir / f"{sidecar['draft_of']}.governance.json"
        path.write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n")
        results.append(sidecar)
        proposed = sidecar["proposed_t1_proxies"]
        filled = [k for k in _DETERMINISTIC if proposed.get(k) is not None]
        print(f"  {sidecar['draft_of']}: {filled}", file=sys.stderr)
    return results


def _coverage_report(results: list[dict]) -> str:
    lines = ["", "# Governance coverage (voie A — deterministic proxies)", "",
             "| Site | cndp_referral | legal_appeals_count | needs review |",
             "|------|---------------|---------------------|--------------|"]
    for r in results:
        p = r["proposed_t1_proxies"]
        cndp = "—" if p["cndp_referral"] is None else str(p["cndp_referral"])
        app = "—" if p["legal_appeals_count"] is None else str(p["legal_appeals_count"])
        lines.append(f"| {r['draft_of']} | {cndp} | {app} | {', '.join(_NEEDS_REVIEW)} |")
    lines.append("")
    lines.append("Deterministic only. The three judgment proxies + T2 are human/LLM review leads.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Batch voie-A governance sidecars from coordinates.")
    p.add_argument("sites", help="CSV (name,operator,lat,lon,...) or JSON array of sites.")
    p.add_argument("--out", default="../smdc-newsroom/drafts/datacenters")
    p.add_argument("--no-archive", action="store_true",
                   help="Skip web-archive snapshots (faster over a large corpus).")
    args = p.parse_args(argv)

    sites = _read_sites(Path(args.sites))
    if not sites:
        print("No valid sites to process.", file=sys.stderr)
        return 1
    out_dir = Path(args.out)
    results = run(sites, out_dir, date.today().isoformat(), archive=not args.no_archive)
    report = _coverage_report(results)
    (out_dir / "_governance_coverage.md").write_text(report + "\n")
    print(report, file=sys.stderr)
    print(f"\nWrote {len(results)} governance sidecar(s) → {out_dir}", file=sys.stderr)
    print("Proposal only — every sidecar is human-reviewed before it enters the circuit.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
