# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""PROTOTYPE — la coordonnée d'une fiche tombe-t-elle sur un bâtiment cartographié ?

Sondé sur 40 fiches tirées au hasard le 2026-09-28 : 21 points sur le bâtiment,
19 à côté (3 à 127 m, médiane ~17 m), AUCUN site sans bâtiment cartographié.
Avec un seuil à 25 m, 35/40 passent — soit ~1 250 fiches sur 1 430.

Ce prototype est là pour transmettre la MÉTHODE, pas pour être le job final
(pas de reprise sur incident, pas de sidecar, pas de registre de provenance) :
c'est le chantier d'agent-data-pipeline-FR. Deux points valent le détour.

1. **api.openstreetmap.org, pas Overpass.** Overpass est en panne depuis des jours
   et c'est lui qui a bloqué le calcul des distances aux habitations à 7 fiches sur
   1 430. L'endpoint `map.json?bbox=` est une infrastructure DIFFÉRENTE, il répond,
   et une bbox de ~180 m est une requête minuscule. C'est peut-être aussi la sortie
   de secours pour les habitations.
2. **Point-dans-polygone, pas distance au centroïde.** Un centroïde de bâtiment
   n'apprend rien sur un hangar de 200 m de côté. Ce qui compte est l'appartenance
   à l'emprise, puis la distance à l'emprise si le point tombe dehors.

Usage : python -m pipelines.geo_audit.probe [N]     (N fiches au hasard, défaut 40)
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
import urllib.request
from pathlib import Path

OSM_MAP = "https://api.openstreetmap.org/api/0.6/map.json?bbox={w:.6f},{s:.6f},{e:.6f},{n:.6f}"
UA = "ScoreMyDataCenter/geo-audit (+https://scoremydatacenter.org)"
HALF_SPAN_DEG = 0.0009  # ~100 m en latitude ; corrigé en longitude par cos(lat)
POLITE_SLEEP = 1.2  # l'API principale d'OSM n'est pas un Overpass : on reste poli
ON_BUILDING_M = 25.0  # seuil retenu : décalage de toit ou d'entrée, pas une erreur


def _ring(elements: list[dict]) -> tuple[list[list[tuple[float, float]]], bool]:
    """Emprises de bâtiments de la bbox, et « un objet porte-t-il un tag data center ? »."""
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in elements if e["type"] == "node"}
    polys: list[list[tuple[float, float]]] = []
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
                polys.append(pts)
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


def probe(lat: float, lon: float) -> dict:
    """Verdict pour un point : sur le bâtiment, à N mètres, ou rien de cartographié."""
    dlon = HALF_SPAN_DEG / max(math.cos(math.radians(lat)), 0.2)
    url = OSM_MAP.format(w=lon - dlon, s=lat - HALF_SPAN_DEG, e=lon + dlon, n=lat + HALF_SPAN_DEG)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        polys, dc_tagged = _ring(json.loads(resp.read())["elements"])

    if not polys:
        return {"verdict": "no_building", "distance_m": None, "dc_tagged": dc_tagged}
    if any(inside((lat, lon), p) for p in polys):
        return {"verdict": "on_building", "distance_m": 0.0, "dc_tagged": dc_tagged}
    d = min(min(metres((lat, lon), q) for q in p) for p in polys)
    return {
        "verdict": "near_building" if d <= ON_BUILDING_M else "off_building",
        "distance_m": round(d, 1),
        "dc_tagged": dc_tagged,
    }


def _corpus(newsroom: Path) -> list[tuple[str, str, float, float]]:
    out = []
    for p in sorted(newsroom.glob("calibration/datacenters*/*.json")):
        if p.name.endswith("provenance.json"):
            continue
        ident = (json.loads(p.read_text()).get("identity") or {})
        coords = ident.get("coordinates") or {}
        if coords.get("lat") is not None:
            out.append((p.stem, ident.get("name") or "?", coords["lat"], coords["lon"]))
    return out


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    newsroom = Path(__file__).resolve().parents[3] / "smdc-newsroom"
    sites = _corpus(newsroom)
    random.seed(42)  # échantillon reproductible : le même tirage que le sondage du 28/09
    tally: dict[str, int] = {}
    for sid, name, lat, lon in random.sample(sites, min(n, len(sites))):
        try:
            r = probe(lat, lon)
        except Exception as exc:  # une panne réseau n'est pas un verdict
            r = {"verdict": "error", "distance_m": None, "note": str(exc)[:60]}
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
        print(f"{sid:52} {name[:30]:32} {r['verdict']:14} {r.get('distance_m')}")
        time.sleep(POLITE_SLEEP)
    print("\n--- synthèse ---")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"{v:5}  {k}")


if __name__ == "__main__":
    main()
