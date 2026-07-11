# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Run a country's spatial collector over a whole list of sites in one command.

    python -m pipelines.spatial.batch sites.csv --country NL --out ../smdc-newsroom/drafts/datacenters

--country selects the adapter from the registry (FR default for back-compat); every country runs
through the SAME batch code — one way to run, no per-country batch script. Input is a CSV (header:
name,operator,lat,lon[,power_mw,project_status]) or a JSON array of the same fields. One draft +
provenance pair is written per row, filenames keyed by id so re-runs refresh in place (idempotent).
A row that fails (bad coords, source down) is reported and skipped — it never aborts the batch. At
the end a coverage matrix shows, per indicator, how many sites the pipeline could fill.

Still a proposal, not a publication: everything lands as drafts for human review (see collect.py).
"""

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

from .http import SourceUnavailable
from .country import build_draft
from .registry import get_spec

# Indicators the spatial pipeline targets today (order = report columns).
_TRACKED = ["E1", "E2", "E3", "W1", "W2", "W3", "F1", "F2", "L1", "L3"]


def _read_sites(path: Path) -> list[dict]:
    text = path.read_text()
    if path.suffix.lower() == ".json":
        rows = json.loads(text)
    else:
        rows = list(csv.DictReader(text.splitlines()))
    sites = []
    for i, r in enumerate(rows, 1):
        try:
            sites.append({
                "name": (r.get("name") or "").strip() or f"site-{i}",
                "operator": (r.get("operator") or "UNKNOWN — to fill").strip(),
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "power_mw": float(r["power_mw"]) if r.get("power_mw") not in (None, "") else None,
                "project_status": (r.get("project_status") or "announced").strip(),
            })
        except (KeyError, ValueError) as exc:
            print(f"  row {i}: skipped (bad input: {exc})", file=sys.stderr)
    return sites


def run(sites: list[dict], out_dir: Path, accessed: str, spec: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results, coverage = [], {ind: 0 for ind in _TRACKED}
    for s in sites:
        try:
            fragment, provenance, _ = build_draft(
                spec, s["lat"], s["lon"], name=s["name"], operator=s["operator"],
                power_mw=s["power_mw"], project_status=s["project_status"], accessed=accessed)
        except SourceUnavailable as exc:
            print(f"  {s['name']}: FAILED ({exc})", file=sys.stderr)
            results.append({"name": s["name"], "ok": False})
            continue
        dc_id = fragment["id"]
        (out_dir / f"{dc_id}.draft.json").write_text(
            json.dumps(fragment, indent=2, ensure_ascii=False) + "\n")
        (out_dir / f"{dc_id}.provenance.json").write_text(
            json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
        filled = provenance["indicators_filled"]
        for ind in filled:
            if ind in coverage:
                coverage[ind] += 1
        results.append({"name": s["name"], "id": dc_id, "ok": True, "filled": filled,
                        "water_body": provenance.get("water_body_for_w2")})
        print(f"  {dc_id}: {len(filled)}/{len(_TRACKED)} filled", file=sys.stderr)
    return {"results": results, "coverage": coverage, "n": len(sites)}


def _print_report(report: dict) -> None:
    n = report["n"]
    ok = sum(1 for r in report["results"] if r["ok"])
    print(f"\n=== Batch coverage — {ok}/{n} sites collected ===")
    print("indicator  filled/sites   %")
    for ind in _TRACKED:
        c = report["coverage"][ind]
        pct = round(100 * c / n) if n else 0
        bar = "█" * (pct // 10)
        print(f"  {ind:8} {c:3}/{n:<3}      {pct:3}%  {bar}")
    print("\nDrafts are proposals — human review required before any enters the circuit.")


def _write_report(report: dict, out_dir: Path, accessed: str) -> Path:
    """Persist the coverage report next to the drafts (Markdown, human-readable)."""
    n = report["n"]
    ok = sum(1 for r in report["results"] if r["ok"])
    lines = [f"# Batch coverage — {accessed}", "",
             f"{ok}/{n} sites collected. Drafts are proposals — human review required.", "",
             "| indicator | filled | % |", "|---|---|---|"]
    for ind in _TRACKED:
        c = report["coverage"][ind]
        pct = round(100 * c / n) if n else 0
        lines.append(f"| {ind} | {c}/{n} | {pct}% |")
    lines += ["", "## Per site", "", "| id | filled | missing |", "|---|---|---|"]
    for r in report["results"]:
        if r["ok"]:
            missing = [i for i in _TRACKED if i not in r["filled"]]
            lines.append(f"| {r['id']} | {len(r['filled'])}/{len(_TRACKED)} | "
                         f"{', '.join(missing) or '—'} |")
        else:
            lines.append(f"| {r['name']} | FAILED | — |")
    path = out_dir / "_coverage.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Batch spatial collection over a list of sites.")
    p.add_argument("input", help="CSV (name,operator,lat,lon[,power_mw,project_status]) or JSON array")
    p.add_argument("--out", required=True, help="Output directory (smdc-newsroom/drafts/datacenters)")
    p.add_argument("--country", default="FR", help="ISO 3166-1 alpha-2 adapter (default FR)")
    args = p.parse_args(argv)

    try:
        spec = get_spec(args.country)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    sites = _read_sites(Path(args.input))
    if not sites:
        print("No valid sites in input.", file=sys.stderr)
        return 1
    accessed = date.today().isoformat()
    out_dir = Path(args.out)
    report = run(sites, out_dir, accessed, spec)
    _print_report(report)
    path = _write_report(report, out_dir, accessed)
    print(f"Coverage report written to {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
