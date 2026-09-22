# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Distance aux habitations → sidecar newsroom calibration/habitations/distance.json.

    make habitations                 # calcule le manquant et commit le sidecar

Le build (scripts/build_prod_artifacts.py) le lit et pose `nearest_dwelling` sur la fiche servie.
Ce job ne touche jamais une fiche du corpus, jamais un statut, jamais une note, et ne déploie pas.
"""

import argparse
import datetime as dt
import json
from pathlib import Path

from engine.core import load_datacenters
from engine.score import _newsroom_calibration
from pipelines.habitations import distance

SIDECAR = Path("habitations") / "distance.json"


def load_fiches(cal):
    out = []
    for dc_id, dc in sorted(load_datacenters(cal).items()):
        if dc_id.startswith(("zz-", "study-")):
            continue
        c = (dc["identity"].get("coordinates") or {})
        if c.get("lat") is None or c.get("lon") is None:
            continue
        out.append({"id": dc_id, "lat": float(c["lat"]), "lon": float(c["lon"])})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cal", type=Path, default=None)
    ap.add_argument("--limit", type=int, default=None, help="n'en calculer qu'un nombre (run par lots)")
    args = ap.parse_args(argv)
    cal = args.cal or _newsroom_calibration()

    out = cal / SIDECAR
    prev = json.loads(out.read_text()).get("fiches", {}) if out.is_file() else {}
    fiches = load_fiches(cal)
    todo = [f for f in fiches if f["id"] not in prev]
    if args.limit:
        fiches = [f for f in fiches if f["id"] in prev] + todo[:args.limit]

    today = dt.date.today().isoformat()
    rows, failures = distance.resolve(fiches, prev, today)
    found = [r["distance_m"] for r in rows.values() if r.get("found")]
    found.sort()
    stats = {"fiches": len(rows), "found": len(found), "no_result": len(rows) - len(found),
             "median_m": found[len(found) // 2] if found else None,
             "under_300m": sum(1 for d in found if d < 300)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "generated_at": today, "source": "OpenStreetMap (Overpass)", "license": distance.LICENSE,
        "method": ("distance au centre de l'objet OSM résidentiel le plus proche dans un rayon de "
                   f"{distance.RADIUS_M} m ; un bâtiment tagué résidentiel prime sur une zone "
                   "landuse=residential, moins précise"),
        "in_score": False, "counts": stats, "fetch_failures": failures, "fiches": rows,
    }, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(f"habitations: {stats} · échecs réseau {failures} · restant {max(0, len(todo) - (args.limit or len(todo)))} → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
