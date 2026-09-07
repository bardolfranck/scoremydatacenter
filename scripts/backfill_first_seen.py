# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Backfill `identity.first_seen` on newsroom DC fiches from GIT history (« first recorded » date).

    python scripts/backfill_first_seen.py --newsroom ../smdc-newsroom            # DRY-RUN (default)
    python scripts/backfill_first_seen.py --newsroom ../smdc-newsroom --apply    # WRITES the fiches

WHY: a « derniers projets SCORÉS » banner needs a per-fiche recency date; today NO date exists
(score_history is empty, identity has no vintage/first_seen). The HONEST, non-invented source is
the date the fiche was FIRST COMMITTED to the newsroom = when we first recorded that data center.
One `git log` pass maps each fiche → its first-commit date (no per-file git call).

Going forward, a fiche should carry identity.first_seen at creation; this backfills the existing
corpus. --apply mutates ~1400 fiches (a large corpus commit) → run ONLY on Franck's explicit go.
Files already carrying identity.first_seen are left untouched (idempotent).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REL = "calibration"  # scan calibration/datacenters* fiches


def first_commit_dates(newsroom: Path) -> dict:
    """{relpath: 'YYYY-MM-DD'} — the FIRST commit that introduced each file, in one git pass."""
    out = subprocess.run(
        ["git", "-C", str(newsroom), "log", "--reverse", "--date=short",
         "--format=commit %ad", "--name-only", "--", _REL],
        capture_output=True, text=True, check=True).stdout
    dates: dict = {}
    cur = None
    for line in out.splitlines():
        if line.startswith("commit "):
            cur = line[len("commit "):].strip()
        elif line.strip() and cur and line not in dates:
            dates[line.strip()] = cur   # first time a path appears = its creation date
    return dates


def backfill(newsroom: Path, *, apply: bool) -> dict:
    dates = first_commit_dates(newsroom)
    fiches = sorted(p for d in newsroom.glob(f"{_REL}/datacenters*") if d.is_dir()
                    for p in d.glob("*.json") if not p.name.endswith((".provenance.json",)))
    stats = {"total": len(fiches), "would_set": 0, "already": 0, "no_git_date": 0, "written": 0}
    samples = []
    for f in fiches:
        try:
            d = json.loads(f.read_text())
        except Exception:  # noqa: BLE001
            continue
        idn = d.get("identity", {})
        if idn.get("first_seen"):
            stats["already"] += 1
            continue
        rel = str(f.relative_to(newsroom))
        fs = dates.get(rel)
        if not fs:
            stats["no_git_date"] += 1
            continue
        stats["would_set"] += 1
        if len(samples) < 5:
            samples.append((d.get("id", f.stem), fs))
        if apply:
            idn["first_seen"] = fs
            d["identity"] = idn
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
            stats["written"] += 1
    return {"stats": stats, "samples": samples}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Backfill identity.first_seen from git history (dry-run default).")
    ap.add_argument("--newsroom", default="../smdc-newsroom", help="path to the private newsroom repo")
    ap.add_argument("--apply", action="store_true", help="WRITE first_seen into the fiches (large corpus mutation — Franck's go only)")
    args = ap.parse_args(argv)
    res = backfill(Path(args.newsroom), apply=args.apply)
    s = res["stats"]
    mode = "APPLY (fiches écrites)" if args.apply else "DRY-RUN (rien écrit)"
    print(f"backfill first_seen [{mode}] : {s['total']} fiches", file=sys.stderr)
    print(f"  à renseigner : {s['would_set']} · déjà : {s['already']} · sans date git : {s['no_git_date']} · écrites : {s['written']}", file=sys.stderr)
    print(f"  échantillon (id, first_seen) : {res['samples']}", file=sys.stderr)
    if not args.apply:
        print("  → --apply pour écrire (mutation ~corpus entier ; sur go Franck uniquement).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
