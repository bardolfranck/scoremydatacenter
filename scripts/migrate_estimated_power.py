# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""One-shot corpus migration: the `estimated` documentation class (option 1c, 2026-07-27).

Audit 2026-07-27: 92 FR power fills in the newsroom ledger are kNN estimates
(poc-mw-estimator signature: >1-decimal MW + `population` feature) mislabeled
"DCWatch (Hubblo), ODbL" — our model output credited to DCWatch, served as a
fact in the ranking, and feeding L2 under that false attribution.

This migration (precedent: migrate_l2_prudence.py) makes the corpus tell the truth:

  ledger (calibration/_dcwatch_power.provenance.json)
    * the 92 estimated fills: attribution -> internal kNN model, `estimated: true`
      (legal effect: DCWatch's real ODbL footprint drops to the 121 true carries)
    * true carries with a null primary_source: filled with the export archive URL
      (the export IS the source; null was an unrecorded field)
    * 2 orphans (fr-campus-ia-fouju, fr-digital-realty-mrs4) gain ledger entries
      (announced figures with their own fiche sources — never DCWatch)

  DC files (calibration/datacenters*/)
    * the 92: identity.power_mw_status = "estimated"; L2 status -> "estimated";
      L2 source title names the estimator instead of DCWatch
    * the 121 + orphans: identity.power_mw_status = "announced" (a third-party /
      declarative figure — same class the 2026-07-19 L2-prudence memo assigned)

Grades must be byte-identical (the estimated cap equals the announced cap by
design); the caller verifies with a scores.json before/after grade diff.
`dcwatch_status` backfill for the 190 slim-export rows is DEFERRED (the seeds
CSV lacks the status column; next DCWatch release ingest carries it).

    uv run python scripts/migrate_estimated_power.py [--newsroom ../smdc-newsroom]
"""

import argparse
import json
from pathlib import Path

EXPORT_URL = ("https://gitlab.com/hubblo/datacenter-watch/-/archive/2026.04.09/"
              "datacenter-watch-2026.04.09.tar.gz")
ESTIMATE_ATTR = ("internal kNN estimate (poc-mw-estimator, commune-comparables model) — "
                 "NOT a DCWatch value; do not attribute to ODbL")
DCWATCH_TAG = "(DCWatch ODbL, export 7dd5b5e9)"
ESTIMATE_TAG = "(estimation interne kNN — poc-mw-estimator)"

ORPHANS = {
    "fr-campus-ia-fouju": {
        "power_mw": 1400.0,
        "attribution": "announced — dossier de concertation CNDP (cited on the fiche L2 source)",
        "primary_source": None,
        "primary_source_note": "CNDP concertation dossier; direct URL to backfill on the fiche pass",
    },
    "fr-digital-realty-mrs4": {
        "power_mw": 20.0,
        "attribution": "announced — corpus fiche source (operator/press figure)",
        "primary_source": None,
        "primary_source_note": "fiche corpus figure; direct URL to backfill on the fiche pass",
    },
}


def _decimals(x) -> int:
    s = repr(float(x))
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--newsroom", default=str(Path(__file__).resolve().parent.parent.parent
                                              / "smdc-newsroom"))
    args = ap.parse_args()
    news = Path(args.newsroom)
    ledger_path = news / "calibration/_dcwatch_power.provenance.json"
    ledger = json.loads(ledger_path.read_text())
    fills = ledger["fills"]

    dc_paths = {p.stem: p for panel in news.glob("calibration/datacenters*")
                for p in panel.glob("fr-*.json") if not p.name.endswith(".provenance.json")}

    stats = {"estimated_relabeled": 0, "carries_source_filled": 0, "dc_estimated_tagged": 0,
             "dc_announced_tagged": 0, "orphans_added": 0, "dc_missing_file": 0}

    for dc_id, fill in fills.items():
        is_estimate = _decimals(fill.get("power_mw", 0)) > 1
        if is_estimate:
            fill["attribution"] = ESTIMATE_ATTR
            fill["estimated"] = True
            fill["model"] = "poc-mw-estimator"
            stats["estimated_relabeled"] += 1
        elif not fill.get("primary_source"):
            fill["primary_source"] = EXPORT_URL
            stats["carries_source_filled"] += 1

        p = dc_paths.get(dc_id)
        if p is None:
            stats["dc_missing_file"] += 1
            continue
        dc = json.loads(p.read_text())
        dc["identity"]["power_mw_status"] = "estimated" if is_estimate else "announced"
        if is_estimate:
            for ind in dc.get("indicators", []):
                if ind.get("id") == "L2" and ind.get("status") in ("announced", "measured"):
                    ind["status"] = "estimated"
                    title = (ind.get("source") or {}).get("title") or ""
                    if DCWATCH_TAG in title:
                        ind["source"]["title"] = title.replace(DCWATCH_TAG, ESTIMATE_TAG)
            stats["dc_estimated_tagged"] += 1
        else:
            stats["dc_announced_tagged"] += 1
        p.write_text(json.dumps(dc, indent=2, ensure_ascii=False) + "\n")

    for dc_id, entry in ORPHANS.items():
        if dc_id in fills:
            continue
        fills[dc_id] = {**entry, "accessed": "2026-07-27"}
        stats["orphans_added"] += 1
        p = dc_paths.get(dc_id)
        if p is not None:
            dc = json.loads(p.read_text())
            dc["identity"]["power_mw_status"] = "announced"
            p.write_text(json.dumps(dc, indent=2, ensure_ascii=False) + "\n")

    ledger["note"] = (
        "power_mw provenance, two classes (migration 2026-07-27, option 1c): entries with "
        "`estimated: true` are INTERNAL kNN model outputs (poc-mw-estimator) — never attribute "
        "to DCWatch/ODbL; the rest are carried from the DCWatch common (ODbL, export 7dd5b5e9, "
        "release 2026.04.09) — attribution required on publication. dcwatch_status backfill for "
        "slim-export rows deferred to the next DCWatch release ingest."
    )
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
