# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""JOB — audit géo « sur bâtiment » du corpus entier (reprise sur incident).

Reprend la MÉTHODE du prototype pipelines/geo_audit/probe.py (api.openstreetmap.org
map.json?bbox=, point-dans-polygone, pas Overpass, pas de centroïde) et l'industrialise
sur les ~1 430 fiches :
  - verdict par fiche : on_building / near_building (≤25 m) / off_building / no_building
  - distance en mètres à l'emprise la plus proche
  - id de l'objet OSM apparié (way/N) — traçabilité de la CONFIRMATION, pas de la provenance
  - dc_tagged : l'objet porte-t-il telecom=data_center / building=data_center (confirmation d'IDENTITÉ)

Sortie = sidecar dans le NEWSROOM PRIVÉ (jamais dans le build public) :
  calibration/geo-audit/on-building.json
Reprise obligatoire : checkpoint + écriture atomique. Relancer le job REPREND là où il
s'est arrêté (les fiches déjà jugées sont sautées ; les erreurs réseau sont réessayées).

Usage :
  python -m pipelines.geo_audit.audit            # tout le corpus, reprise auto
  python -m pipelines.geo_audit.audit --limit 5  # smoke test
  python -m pipelines.geo_audit.audit --retry-errors-only
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

OSM_MAP = "https://api.openstreetmap.org/api/0.6/map.json?bbox={w:.6f},{s:.6f},{e:.6f},{n:.6f}"
UA = "ScoreMyDataCenter/geo-audit (+https://scoremydatacenter.org)"
HALF_SPAN_DEG = 0.0009  # ~100 m en latitude ; corrigé en longitude par cos(lat)
POLITE_SLEEP = 1.2      # l'API principale d'OSM n'est pas un Overpass : on reste poli
ON_BUILDING_M = 25.0    # seuil d'échantillon (choix chef), pas une valeur calibrée
CHECKPOINT_EVERY = 10   # écriture atomique du sidecar toutes les N fiches
MAX_RETRIES = 3         # 429 / 5xx : quelques essais avec backoff, puis verdict "error"

NEWSROOM = Path(__file__).resolve().parents[3] / "smdc-newsroom"
OUT = NEWSROOM / "calibration" / "geo-audit" / "on-building.json"


def _ring(elements: list[dict]):
    """Emprises de bâtiments (avec leur id OSM) + drapeau data-center de la bbox."""
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in elements if e["type"] == "node"}
    polys: list[tuple[int, list[tuple[float, float]]]] = []
    dc_tagged = False
    for e in elements:
        if e["type"] != "way":
            continue
        tags = e.get("tags") or {}
        if tags.get("telecom") == "data_center" or tags.get("building") == "data_center":
            dc_tagged = True
        if "building" in tags or tags.get("telecom") == "data_center":
            pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if len(pts) >= 3:
                polys.append((e["id"], pts))
    return polys, dc_tagged


def inside(pt: tuple[float, float], poly: list[tuple[float, float]]) -> bool:
    """Ray casting. pt et poly en (lat, lon)."""
    y, x = pt
    hit = False
    for i in range(len(poly)):
        y1, x1 = poly[i]
        y2, x2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = math.pi / 180
    dlat, dlon = (b[0] - a[0]) * r, (b[1] - a[1]) * r
    h = math.sin(dlat / 2) ** 2 + math.cos(a[0] * r) * math.cos(b[0] * r) * math.sin(dlon / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def _fetch(lat: float, lon: float) -> list[dict]:
    dlon = HALF_SPAN_DEG / max(math.cos(math.radians(lat)), 0.2)
    url = OSM_MAP.format(w=lon - dlon, s=lat - HALF_SPAN_DEG, e=lon + dlon, n=lat + HALF_SPAN_DEG)
    last: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())["elements"]
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (429, 500, 502, 503, 504):
                time.sleep(POLITE_SLEEP * (attempt + 2))  # backoff poli
                continue
            raise
        except Exception as exc:  # noqa: BLE001 — réseau : on réessaie
            last = exc
            time.sleep(POLITE_SLEEP * (attempt + 2))
    raise last if last else RuntimeError("fetch failed")


def probe(lat: float, lon: float) -> dict:
    """Verdict pour un point : sur le bâtiment, à N mètres, ou rien de cartographié."""
    polys, dc_tagged = _ring(_fetch(lat, lon))
    if not polys:
        return {"verdict": "no_building", "distance_m": None, "osm_object": None, "dc_tagged": dc_tagged}
    for oid, poly in polys:
        if inside((lat, lon), poly):
            return {"verdict": "on_building", "distance_m": 0.0,
                    "osm_object": f"way/{oid}", "dc_tagged": dc_tagged}
    best_oid, best_d = None, math.inf
    for oid, poly in polys:
        d = min(metres((lat, lon), q) for q in poly)
        if d < best_d:
            best_oid, best_d = oid, d
    return {
        "verdict": "near_building" if best_d <= ON_BUILDING_M else "off_building",
        "distance_m": round(best_d, 1),
        "osm_object": f"way/{best_oid}",
        "dc_tagged": dc_tagged,
    }


def _corpus() -> list[tuple[str, str, float, float]]:
    out = []
    for p in sorted(NEWSROOM.glob("calibration/datacenters*/*.json")):
        if p.name.endswith("provenance.json"):
            continue
        ident = (json.loads(p.read_text()).get("identity") or {})
        coords = ident.get("coordinates") or {}
        if coords.get("lat") is not None:
            out.append((p.stem, ident.get("name") or "?", coords["lat"], coords["lon"]))
    return out


def _load_state() -> dict:
    if OUT.exists():
        try:
            return json.loads(OUT.read_text())
        except json.JSONDecodeError:
            pass
    return {"meta": {}, "fiches": {}}


def _tally(fiches: dict) -> dict:
    t: dict[str, int] = {}
    for r in fiches.values():
        t[r["verdict"]] = t.get(r["verdict"], 0) + 1
    return t


def _save(state: dict) -> None:
    """Écriture atomique : temp + os.replace. Un crash ne laisse jamais un JSON tronqué."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fiches = state["fiches"]
    state["meta"] = {
        "generated_at": date.today().isoformat(),
        "method": "point-in-polygon vs OSM building footprints; api.openstreetmap.org map.json bbox ~180 m (PAS Overpass)",
        "threshold_near_m": ON_BUILDING_M,
        "source": "OpenStreetMap",
        "license": "OpenStreetMap contributors, ODbL 1.0",
        "note": "CONFIRMATION de position, PAS provenance de la coordonnée. Interne newsroom — jamais dans le build public.",
        "counts": {"fiches": len(fiches), **_tally(fiches)},
    }
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True))
    os.replace(tmp, OUT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="ne traiter que N fiches (smoke test)")
    ap.add_argument("--retry-errors-only", action="store_true", help="ne reprendre que les verdicts 'error'")
    args = ap.parse_args()

    state = _load_state()
    done = state["fiches"]
    sites = _corpus()

    todo = []
    for sid, name, lat, lon in sites:
        prev = done.get(sid)
        if prev is None or prev.get("verdict") == "error" or (args.retry_errors_only and prev.get("verdict") == "error"):
            if args.retry_errors_only and (prev is None or prev.get("verdict") != "error"):
                continue
            todo.append((sid, name, lat, lon))
    if args.limit:
        todo = todo[: args.limit]

    print(f"corpus {len(sites)} · déjà jugées {sum(1 for v in done.values() if v.get('verdict') != 'error')} · à traiter {len(todo)}", flush=True)
    for i, (sid, name, lat, lon) in enumerate(todo, 1):
        try:
            r = probe(lat, lon)
        except Exception as exc:  # noqa: BLE001
            r = {"verdict": "error", "distance_m": None, "osm_object": None, "dc_tagged": False, "note": str(exc)[:80]}
        r["checked_at"] = date.today().isoformat()
        done[sid] = r
        print(f"{i:4}/{len(todo)}  {sid:52} {r['verdict']:14} {r.get('distance_m')}", flush=True)
        if i % CHECKPOINT_EVERY == 0:
            _save(state)
        time.sleep(POLITE_SLEEP)

    _save(state)
    print("\n--- synthèse ---", flush=True)
    for k, v in sorted(_tally(done).items(), key=lambda kv: -kv[1]):
        print(f"{v:5}  {k}", flush=True)
    print(f"\nsidecar : {OUT}", flush=True)


if __name__ == "__main__":
    main()
