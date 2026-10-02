# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""E6 — raccordabilité à un réseau de chaleur urbain (SITE, base, public_fact).

Join par coordonnée sur France Chaleur Urbaine (data.gouv, Licence Ouverte v2 / lov2) :
  · reseaux_de_chaleur.geojson — 1 033 réseaux, traces MultiLineString, Lambert 93 (EPSG:2154) ;
  · pdp.geojson — 219 Périmètres de Développement Prioritaire (obligation de raccordement).

Distance point→SEGMENT (pas au sommet), + test point-dans-PDP, + drapeau « réseau classé ».
Valeur catégorielle (poids figés R&D 2026-09-30, méthodo câblée par agent-codeur-site) :
  · raccordable  (100) — distance ≤ 300 m, OU dans un PDP, OU réseau le plus proche ≤1 km CLASSÉ ;
  · proche       (50)  — distance ≤ 1 000 m ;
  · eloigne      (0)   — au-delà.

Directionnalité (décision R&D) : E6 mesure la RACCORDABILITÉ pure (le DC exporte sa chaleur
fatale VERS le réseau). Le contenu CO2 / taux EnR&R du réseau NE module PAS E6 (un réseau fossile
bénéficie le plus d'une injection bas-carbone → l'inverser serait à l'envers). Qualité-réseau =
piste séparée. FR uniquement (FCU est FR-only) ; le monde attend la décision indice-pays.

Données FCU non commitées (~80 Mo) : HORS des deux dépôts (même convention que ~/.smdc/),
pointées par $SMDC_FCU_DIR ou --fcu. Rejouable depuis zéro :

    mkdir -p ~/.smdc/fcu && cd ~/.smdc/fcu
    curl -fsSLO https://static.data.gouv.fr/resources/traces-des-reseaux-de-chaleur-et-de-froid/20260914-103127/opendata-fcu.zip
    unzip -o opendata-fcu.zip reseaux_de_chaleur.geojson pdp.geojson
    export SMDC_FCU_DIR=~/.smdc/fcu

Les DEUX fichiers requis (les seuls lus ici), au format GeoJSON EPSG:2154 (Lambert 93) :
  · reseaux_de_chaleur.geojson  — 1033 réseaux, MultiLineString, prop « reseaux classes » ;
  · pdp.geojson                 — 219 Périmètres de Développement Prioritaire, MultiPolygon.
La page du jeu (versions plus récentes) : FCU_URL. Figer la version datée ci-dessus = provenance
reproductible ; pour rafraîchir, prendre la dernière archive de FCU_URL et re-vérifier le CRS.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

# Lambert 93 (IGN ALG0003), WGS84 ≈ GRS80
_N = 0.7256077650
_C = 11754255.426
_XS = 700000.0
_YS = 12655612.050
_LON0 = 3.0 * math.pi / 180
_E = 0.08181919104

RACCORDABLE_M = 300.0
PROCHE_M = 1000.0
FCU_URL = "https://www.data.gouv.fr/datasets/traces-des-reseaux-de-chaleur-et-de-froid"


def to_l93(lat: float, lon: float) -> tuple[float, float]:
    lat, lon = math.radians(lat), math.radians(lon)
    s = math.sin(lat)
    L = math.log(math.tan(math.pi / 4 + lat / 2) * ((1 - _E * s) / (1 + _E * s)) ** (_E / 2))
    R = _C * math.exp(-_N * L)
    g = _N * (lon - _LON0)
    return _XS + R * math.sin(g), _YS - R * math.cos(g)


def _seg_d2(px, py, ax, ay, bx, by) -> float:
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return (px - ax) ** 2 + (py - ay) ** 2
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    cx, cy = ax + t * dx, ay + t * dy
    return (px - cx) ** 2 + (py - cy) ** 2


def load_fcu(fcu_dir: Path) -> dict:
    """Charge et indexe les réseaux (bbox + segments + classé) et les PDP (bbox + rings)."""
    rc = json.loads((fcu_dir / "reseaux_de_chaleur.geojson").read_text())
    nets = []
    for f in rc["features"]:
        pts = []
        for line in f["geometry"]["coordinates"]:
            pts.extend((x, y) for x, y in line)
        if len(pts) < 2:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        classe = bool((f.get("properties") or {}).get("reseaux classes"))
        nets.append((min(xs), min(ys), max(xs), max(ys), pts, classe))
    pdp = json.loads((fcu_dir / "pdp.geojson").read_text())
    polys = []
    for f in pdp["features"]:
        g = f["geometry"]
        parts = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings, allpts = [], []
        for poly in parts:
            for ring in poly:
                r = [(x, y) for x, y in ring]
                rings.append(r)
                allpts.extend(r)
        if allpts:
            xs = [p[0] for p in allpts]
            ys = [p[1] for p in allpts]
            polys.append((min(xs), min(ys), max(xs), max(ys), rings))
    return {"nets": nets, "polys": polys}


def _nearest(px, py, nets) -> tuple[float, bool]:
    best, best_classe = 9e18, False
    for minx, miny, maxx, maxy, pts, classe in nets:
        if px < minx - 1500 or px > maxx + 1500 or py < miny - 1500 or py > maxy + 1500:
            continue
        for i in range(len(pts) - 1):
            d = _seg_d2(px, py, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            if d < best:
                best, best_classe = d, classe
    return best ** 0.5, best_classe


def _in_pdp(px, py, polys) -> bool:
    for minx, miny, maxx, maxy, rings in polys:
        if px < minx or px > maxx or py < miny or py > maxy:
            continue
        inside = False
        for r in rings:
            for i in range(len(r)):
                x1, y1 = r[i]
                x2, y2 = r[(i + 1) % len(r)]
                if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                    inside = not inside
        if inside:
            return True
    return False


def e6_at(lat: float, lon: float, fcu: dict, accessed: str) -> dict:
    """Indicateur E6 pour un point FR. Renvoie le dict indicateur (status/value/source)."""
    px, py = to_l93(lat, lon)
    dist_m, classe = _nearest(px, py, fcu["nets"])
    in_pdp = _in_pdp(px, py, fcu["polys"])
    # Option A (R&D 2026-09-30) : raccordable=100 repose sur une PREUVE géométrique — proximité
    # physique (≤300 m) OU polygone d'obligation réel (PDP). Le drapeau « réseau classé » N'entre
    # PAS : il crée une obligation dans un PÉRIMÈTRE de classement dont on n'a pas la géométrie ;
    # l'approximer (≤1 km) sur-revendiquerait le score max sur preuve mince. Flag conservé en
    # provenance — le jour où on a la géométrie du périmètre, on le traitera comme un PDP.
    if dist_m <= RACCORDABLE_M or in_pdp:
        cat = "raccordable"
    elif dist_m <= PROCHE_M:
        cat = "proche"
    else:
        cat = "eloigne"
    trig = ("≤300 m" if dist_m <= RACCORDABLE_M else
            "dans un PDP" if in_pdp else
            "≤1000 m" if dist_m <= PROCHE_M else ">1000 m")
    # Au-delà du pré-filtre bbox (~1,5 km), la distance exacte n'est pas calculée : la catégorie
    # est de toute façon « eloigne ». On l'écrit honnêtement plutôt qu'une sentinelle.
    dist_txt = f"{dist_m:.0f} m" if dist_m < 100000 else "aucun réseau dans ~1,5 km"
    title = (f"France Chaleur Urbaine (data.gouv, lov2) — réseau de chaleur le plus proche : "
             f"{dist_txt} (point→segment, Lambert 93) ; dans un PDP : {'oui' if in_pdp else 'non'} ; "
             f"réseau classé : {'oui' if classe else 'non'} → {cat} ({trig})")
    return {"id": "E6", "status": "measured", "value": cat,
            "source": {"title": title, "url": FCU_URL, "accessed": accessed,
                       "license": "Licence Ouverte v2.0 (etalab)"}}


def fcu_dir_from_env(cli: str | None = None) -> Path:
    d = cli or os.environ.get("SMDC_FCU_DIR")
    if not d:
        raise SystemExit("Données FCU requises : --fcu <dir> ou $SMDC_FCU_DIR (voir " + FCU_URL + ")")
    return Path(d)
