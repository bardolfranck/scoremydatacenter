# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Weekly status proof → newsroom sidecar calibration/status-proof/status_check.json.

    make status-proof            # fetch PeeringDB, run the label model, write + commit the sidecar

The build (scripts/build_prod_artifacts.py) reads the sidecar and puts a `status_check` on each
operational fiche: « statut vérifié » (with its source) or « statut non vérifié ». This job never
edits a fiche, never changes a project_status, never touches a grade, never deploys.

Two signals are recorded but NOT published (no automatic public status flip — Franck's gate):
  - live_signal : a NON-operational fiche that PeeringDB shows running (possible stale « annoncé »);
  - demote      : an operational fiche the model is confident is not running.

Safety: if the verified count collapses versus the previous run (network hiccup, PeeringDB schema
change, join regression), the sidecar is NOT overwritten and the job fails loudly — a bad week must
never flip dozens of public « vérifié » to « non vérifié ».
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from engine.core import load_datacenters
from engine.score import _newsroom_calibration
from pipelines.status_proof import label_model, peeringdb

SIDECAR = Path("status-proof") / "status_check.json"
MAX_DROP = 0.30   # refuse to publish if verified falls by more than 30 % vs the previous run


def load_fiches(cal):
    dcs = load_datacenters(cal)
    out = []
    for dc_id, dc in sorted(dcs.items()):
        if dc_id.startswith(("zz-", "study-")):
            continue
        idn = dc["identity"]
        c = idn.get("coordinates") or {}
        if c.get("lat") is None or c.get("lon") is None:
            continue
        out.append({"id": dc_id, "name": idn.get("name") or "", "operator": idn.get("operator") or "",
                    "country": idn.get("country") or "", "status": idn.get("project_status"),
                    "lat": float(c["lat"]), "lon": float(c["lon"])})
    return out


def fired_lfs(match):
    fired = set()
    if match and match["kind"] == "BIND" and match["net_count"] > 0:
        fired.add("peeringdb_live")
    return fired


def build(fiches, facilities_by_country, today):
    result, counts = {}, {"verified": 0, "unverified": 0, "live_signal": 0, "demote": 0}
    for fi in fiches:
        match = peeringdb.join(fi, facilities_by_country.get(fi["country"], []))
        p, used = label_model.p_operational(fired_lfs(match))
        decision = label_model.decide(p)
        evidence = None
        if "peeringdb_live" in used:
            evidence = {"source": "PeeringDB", "url": match["url"], "facility": match["fac_name"],
                        "networks": match["net_count"]}
        if fi["status"] == "operational":
            verdict = "verified" if decision == "confirm_op" else "unverified"
            counts[verdict] += 1
            entry = {"verdict": verdict}
            if decision == "demote":
                entry["demote"] = True          # internal only, never auto-published
                counts["demote"] += 1
        else:
            if decision != "confirm_op":
                continue
            entry = {"verdict": "live_signal"}  # internal only: stale « annoncé » candidate
            counts["live_signal"] += 1
        entry["checked_at"] = today
        if p is not None:
            entry["p_operational"] = round(p, 3)
        if evidence:
            entry["evidence"] = evidence
        result[fi["id"]] = entry
    return result, counts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cal", type=Path, default=None, help="newsroom calibration dir")
    ap.add_argument("--force", action="store_true", help="publish even if verified collapsed")
    args = ap.parse_args(argv)
    cal = args.cal or _newsroom_calibration()

    fiches = load_fiches(cal)
    facilities = peeringdb.fetch_facilities()
    today = dt.date.today().isoformat()
    fiche_map, counts = build(fiches, facilities, today)

    out = cal / SIDECAR
    if out.is_file() and not args.force:
        prev = json.loads(out.read_text()).get("counts", {}).get("verified", 0)
        if prev and counts["verified"] < prev * (1 - MAX_DROP):
            print(f"status-proof: ABORT — verified {prev} → {counts['verified']} (>{int(MAX_DROP * 100)} % drop). "
                  "Sidecar kept unchanged; investigate (PeeringDB outage? join regression?) or rerun with --force.",
                  file=sys.stderr)
            return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "generated_at": today,
        "sources": ["PeeringDB"],
        "model": {"lf_precision": label_model.LF_PRECISION, "hi": label_model.HI, "lo": label_model.LO},
        "counts": counts,
        "fiches": fiche_map,
    }, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(f"status-proof: {len(fiches)} fiches · facilities {sum(map(len, facilities.values()))} "
          f"· {counts} → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
