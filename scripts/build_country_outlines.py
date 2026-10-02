# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Les contours de pays du comparateur, en chemins SVG légers — une seule fois, à froid.

    python scripts/build_country_outlines.py          # → site/src/data/outlines.json

Source : Natural Earth 1:50m (domaine public, aucune attribution exigée mais on la porte
quand même). On garde les coordonnées en LONGITUDE/LATITUDE : la carte les dessine dans le
même repère que les sites, donc le tracé et les points ne peuvent pas diverger.

Simplification Douglas-Peucker à ~2 km. Un contour de pays dans une vignette de 700 px n'a
pas besoin de la précision du littoral ; ce qu'il doit faire, c'est être reconnaissable.

Un anneau fermé a son premier point égal au dernier : Douglas-Peucker le réduit alors à un
segment. On le coupe donc au sommet le plus éloigné du premier avant de simplifier — sans
quoi chaque pays devient une ligne droite (constaté).
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import urllib.request

SOURCE = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
          "geojson/ne_50m_admin_0_countries.geojson")
OUT = pathlib.Path(__file__).resolve().parent.parent / "site" / "src" / "data" / "outlines.json"
PAYS = ["FR", "DE", "NL", "IT", "PL", "ES", "CH", "SE", "NO", "BE", "FI", "DK", "GB"]
TOLERANCE_DEG = 0.02          # ~2 km
MIN_POINTS = 40               # un anneau plus court qu'un timbre n'ajoute rien à la silhouette


def _dp(pts: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1e-9
    di, dm = 0, 0.0
    for i in range(1, len(pts) - 1):
        d = abs(dy * (pts[i][0] - a[0]) - dx * (pts[i][1] - a[1])) / n
        if d > dm:
            dm, di = d, i
    return _dp(pts[:di + 1], tol)[:-1] + _dp(pts[di:], tol) if dm > tol else [a, b]


def _ring(pts: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    a = pts[0]
    k = max(range(len(pts)), key=lambda i: (pts[i][0] - a[0]) ** 2 + (pts[i][1] - a[1]) ** 2)
    return _dp(pts[:k + 1], tol)[:-1] + _dp(pts[k:] + [a], tol)


def main() -> int:
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    raw = json.loads(src.read_text()) if src and src.is_file() else json.loads(
        urllib.request.urlopen(SOURCE, timeout=180).read())

    out: dict[str, dict] = {}
    for f in raw["features"]:
        p = f["properties"]
        iso = p.get("ISO_A2_EH") or p.get("ISO_A2")
        if iso not in PAYS:
            continue
        g = f["geometry"]
        rings = ([r[0] for r in g["coordinates"]] if g["type"] == "MultiPolygon"
                 else [g["coordinates"][0]])
        paths, lons, lats = [], [], []
        for r in rings:
            if len(r) < MIN_POINTS:
                continue
            pts = _ring([(float(x), float(y)) for x, y in r], TOLERANCE_DEG)
            if len(pts) < 4:
                continue
            paths.append("M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in pts) + " Z")
            lons += [x for x, _ in pts]
            lats += [y for _, y in pts]
        if not paths:
            continue
        # Les bornes servent au cadrage de la carte. Pour la France et l'Espagne, les
        # territoires lointains étireraient la vue jusqu'à l'illisible : on cadre sur
        # l'Europe continentale, les sites du corpus y étant tous.
        lo = [x for x in lons if -11 < x < 32]
        la = [y for y in lats if 34 < y < 72]
        out[iso] = {"path": " ".join(paths),
                    "bbox": [min(lo), min(la), max(lo), max(la)],
                    "points": sum(p.count("L") for p in paths)}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": "Natural Earth 1:50m (domaine public)",
                               "tolerance_deg": TOLERANCE_DEG, "pays": out}, ensure_ascii=False))
    total = sum(v["points"] for v in out.values())
    print(f"outlines: {len(out)} pays, {total} points, {OUT.stat().st_size // 1024} Ko → {OUT}")
    for k in PAYS:
        if k not in out:
            print(f"  MANQUANT : {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
