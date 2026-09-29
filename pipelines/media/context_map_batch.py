# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Industrialise the context map (annotated satellite photo) over a whole scope.

Wraps pipelines.media.context_map.render (rendering logic validated image-by-image with Franck —
NOT re-implemented here). This module adds the batch machinery, mirroring satellite.py:
  · DISPLAY GATE from calibration/geo-audit/on-building.json — only on_building / near_building
    (<=25 m) get a context map; off_building (>25 m) and no_building keep the raw vignette.
  · idempotent + resumable: an already-staged PNG is skipped (manifest + file check).
  · per-commune population cache lives in context_map (Nominatim is 1 req/s, banned on volume).
  · R2 upload OPTIONAL (--upload): ctx/{id}-{hmac8}.webp, same non-enumerable scheme as sat/ but a
    DISTINCT prefix — the raw sat/ vignette is kept untouched next to it (Franck 2026-09-28).
    Needs SMDC_MEDIA_SECRET + wrangler auth (deploy env); generation runs without them.

    uv run python -m pipelines.media.context_map_batch --scope non-fr            # generate only
    uv run python -m pipelines.media.context_map_batch --scope non-fr --upload   # + R2 (deploy env)
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from pipelines.media import context_map
from pipelines.media.satellite import REPO, BUCKET

NEWSROOM = REPO.parent / "smdc-newsroom"
GATE = NEWSROOM / "calibration" / "geo-audit" / "on-building.json"
CENTROID = NEWSROOM / "calibration" / "geo-audit" / "centroid-check.json"
SERVED_DC = REPO / "site" / "public" / "data" / "dc"
OUT_DIR = REPO / ".media-sat"
MANIFEST = OUT_DIR / "context-uploaded.txt"   # R2 keys confirmed uploaded
GATE_OK = {"on_building", "near_building"}
# Un PROJET non construit passe le gate quel que soit son verdict d'audit : le test
# sur-bâtiment ne dit rien de la qualité d'une coordonnée quand il n'y a pas encore de
# bâtiment à toucher. Ce qui garantit leur géo est plus fort — la règle 1 du PLAN
# pipeline-projets exige des coordonnées de niveau bâtiment à l'ingestion. Sans cette
# ouverture, on écarterait nos rendus les plus parlants : Sesterce Grand Est (600 MW,
# commune de 52 habitants), Google Étrechet, Prologis.
PROJECT_STATUSES = {"announced", "permitting", "under_construction"}


def ctx_key(dc_id: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), dc_id.encode(), hashlib.sha256).hexdigest()[:8]
    return f"ctx/{dc_id}-{digest}.webp"


def eligible(scope: str) -> tuple[list[str], dict]:
    """Return (ids to render, skip-report). scope 'non-fr' = everything except FR and IL (Franck)."""
    gate = json.loads(GATE.read_text())["fiches"]
    # Géo FABRIQUÉE (coordonnée = géocodage du nom de commune, classe Fouju) : ne JAMAIS rendre —
    # une photo aérienne annotée sur une coordonnée inventée désignerait le mauvais endroit. Ces
    # fiches retombent sur la vignette brute tant que la coordonnée n'est pas corrigée à la main.
    fabricated = set()
    if CENTROID.is_file():
        fabricated = {e["id"] for e in json.loads(CENTROID.read_text()).get("fabriquees_probables", [])}
    ids, skip = [], collections.Counter()
    for fid, v in gate.items():
        if fid in fabricated:
            skip["fabricated_geo"] += 1
            continue
        cc = fid.split("-", 1)[0]
        if scope == "non-fr" and cc in ("fr", "il"):
            continue
        if scope == "fr" and cc != "fr":
            continue
        served = SERVED_DC / f"{fid}.json"
        if not served.is_file():
            skip["no_served_dc_json"] += 1
            continue
        is_project = json.loads(served.read_text()).get("project_status") in PROJECT_STATUSES
        if v.get("verdict") not in GATE_OK and not is_project:
            skip[f"gate:{v.get('verdict')}"] += 1
            continue
        ids.append(fid)
    return ids, dict(skip)


def _manifest() -> set[str]:
    return set(MANIFEST.read_text().split()) if MANIFEST.is_file() else set()


def _r2_put(key: str, path: Path) -> bool:
    p = subprocess.run(["npx", "wrangler", "r2", "object", "put", f"{BUCKET}/{key}",
                        "--file", str(path), "--content-type", "image/webp", "--remote"],
                       cwd=REPO / "site", capture_output=True, text=True)
    if p.returncode != 0:
        print(f"  R2 put failed {key}: {(p.stderr or p.stdout).strip().splitlines()[-1:]}", file=sys.stderr)
    return p.returncode == 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Batch context maps over a scope (gate-filtered).")
    ap.add_argument("--scope", default="non-fr", choices=["non-fr", "fr", "all"])
    ap.add_argument("--upload", action="store_true", help="upload PNGs to R2 (deploy env: SMDC_MEDIA_SECRET + wrangler)")
    ap.add_argument("--limit", type=int, default=0, help="cap the number rendered (pilot)")
    ap.add_argument("--force", action="store_true", help="re-render even if the PNG is staged")
    args = ap.parse_args(argv)

    ids, skip = eligible(args.scope)
    if args.limit:
        ids = ids[:args.limit]
    secret = os.environ.get("SMDC_MEDIA_SECRET") if args.upload else None
    if args.upload and not secret:
        print("context-batch: --upload needs SMDC_MEDIA_SECRET — aborting", file=sys.stderr)
        return 2
    uploaded = _manifest() if args.upload else set()

    done, errors, rendered = [], [], 0
    percountry = collections.Counter()
    for fid in ids:
        webp = OUT_DIR / f"context-{fid}.webp"
        if webp.is_file() and not args.force:
            done.append(fid)
        else:
            try:
                context_map.render(fid)
                rendered += 1
                done.append(fid)
                time.sleep(1)  # Esri/OSM politeness between fiches
            except Exception as exc:  # noqa: BLE001 — one bad fiche never aborts the batch
                errors.append((fid, str(exc)[:120]))
                print(f"  ERR {fid}: {str(exc)[:120]}", file=sys.stderr)
                continue
        percountry[fid.split("-", 1)[0].upper()] += 1
        if args.upload:
            key = ctx_key(fid, secret)
            if key in uploaded:
                continue
            if _r2_put(key, webp):
                with MANIFEST.open("a") as f:
                    f.write(key + "\n")

    # ---- report from stats sidecars
    anomalies = collections.Counter()
    empties = collections.Counter()
    for fid in done:
        sp = OUT_DIR / f"context-{fid}.stats.json"
        if not sp.is_file():
            continue
        s = json.loads(sp.read_text())
        if s.get("power_present") and s.get("power_voltage_missing"):
            anomalies["substation_without_voltage"] += 1
        if s.get("power_present"):
            anomalies["substation_present"] += 1
        if s.get("osm_fallback"):
            anomalies["osm_overpass_fallback"] += 1
        for k in ("power", "water", "dwelling", "site"):
            if not s.get(f"{k}_present"):
                empties[f"no_{k}"] += 1

    print("\n=== CONTEXT-MAP BATCH REPORT ===")
    print(f"scope={args.scope} | eligible={len(ids)} | rendered_now={rendered} | staged_total={len(done)} | errors={len(errors)}")
    print(f"skipped (not eligible): {skip}")
    print(f"per country (staged): {dict(sorted(percountry.items(), key=lambda x: -x[1]))}")
    print(f"annotations: {dict(anomalies)}")
    sub = anomalies.get("substation_present", 0)
    if sub:
        print(f"  ⚠ substation WITHOUT voltage: {anomalies.get('substation_without_voltage',0)}/{sub} "
              f"({100*anomalies.get('substation_without_voltage',0)//sub}%)")
    print(f"empty annotations: {dict(empties)}")
    if errors:
        print(f"first errors: {errors[:8]}")
    json.dump({"done": done, "errors": errors, "skip": skip,
               "percountry": dict(percountry), "anomalies": dict(anomalies), "empties": dict(empties)},
              open(OUT_DIR / "context-batch-report.json", "w"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
