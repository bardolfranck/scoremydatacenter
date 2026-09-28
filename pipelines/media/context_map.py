# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""PROTOTYPE — carte de contexte : photo satellite ANNOTÉE, cuite côté serveur.

Arbitrage Franck (2026-09-28) : « c'est LE produit, le schéma sera toujours
suspecté de véridique ou pas, alors qu'une photo sat ne mente pas ». Donc pas de
carte cliente, pas de schéma : une image Esri réelle sur laquelle on grave les
faits mesurés.

Trois annotations normalisées, chacune portant le quoi / le combien / le
qualificatif, et chacune écrivant son absence quand la donnée manque :
  · le poste électrique le plus proche et sa tension ;
  · le cours d'eau NOMMÉ le plus proche et l'état de sa masse d'eau ;
  · l'emprise du site contre son voisinage.

Pourquoi cuire l'image plutôt que de l'assembler dans le navigateur : les
coordonnées servies sont **arrondies à ~1 km** (560 m d'écart constaté sur
Auxerre). Une carte cliente devrait donc recevoir la coordonnée fine, ce qu'on
refuse. En cuisant l'image, la précision reste dans le pipeline et le public ne
reçoit qu'une image plus un texte. C'est la même doctrine que la vignette
satellite existante, dont ce module réutilise la projection et les tuiles.

Zoom : z17 (~0,80 m/px à 48° de latitude) cadre 963 × 722 m, ce qui contient les
objets utiles jusqu'à ~350 m. z18 les ferait sortir du cadre.

    uv run python -m pipelines.media.context_map fr-virtua-networks
"""

from __future__ import annotations

import json
import math
import sys
import urllib.request
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from pipelines.media.satellite import REPO, fetch_tile, world_pixel

OSM_MAP = "https://api.openstreetmap.org/api/0.6/map.json?bbox={w:.6f},{s:.6f},{e:.6f},{n:.6f}"
UA = {"User-Agent": "ScoreMyDataCenter-context/1.0 (contact@scoremydatacenter.org)"}
NEWSROOM = REPO.parent / "smdc-newsroom"
FONT_PATH = REPO / "site" / "src" / "og" / "fonts" / "chivo-mono-400.ttf"
OUT_DIR = REPO / ".media-sat"

W, H, Z = 1200, 900, 17
RINGS_M = (100, 300)
INK = (255, 255, 255)
SHADE = (0, 0, 0)
WATER = (120, 190, 255)
POWER = (255, 190, 70)
DWELL = (255, 150, 120)
SITE = (255, 255, 255)

RESIDENTIAL = {"residential", "apartments", "house", "detached", "semidetached_house", "terrace", "dormitory"}


def metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = math.pi / 180
    dlat, dlon = (b[0] - a[0]) * r, (b[1] - a[1]) * r
    h = math.sin(dlat / 2) ** 2 + math.cos(a[0] * r) * math.cos(b[0] * r) * math.sin(dlon / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def osm_around(lat: float, lon: float, half_km: float = 0.75) -> dict:
    """Une seule requête bbox sur l'API principale d'OSM — PAS Overpass, qui est en panne."""
    dlat = half_km / 111.32
    dlon = dlat / max(math.cos(math.radians(lat)), 0.2)
    url = OSM_MAP.format(w=lon - dlon, s=lat - dlat, e=lon + dlon, n=lat + dlat)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as resp:
        return json.loads(resp.read())


def features(lat: float, lon: float, data: dict) -> dict:
    """Les objets utiles, avec leur géométrie RÉELLE — jamais de direction inventée."""
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in data["elements"] if e["type"] == "node"}
    here = (lat, lon)
    out: dict = {"site": None, "water": None, "power": None, "dwelling": None, "buildings": 0}

    for e in data["elements"]:
        tags = e.get("tags") or {}
        pts = [nodes[n] for n in e.get("nodes", []) if n in nodes] if e["type"] == "way" \
            else ([nodes[e["id"]]] if e["id"] in nodes else [])
        if not pts:
            continue
        d = min(metres(here, p) for p in pts)

        if "building" in tags:
            out["buildings"] += 1
            if out["site"] is None or d < out["site"]["d"]:
                out["site"] = {"d": d, "geom": pts, "tags": tags, "osm": f"way/{e['id']}"}
            if tags.get("building") in RESIDENTIAL and (out["dwelling"] is None or d < out["dwelling"]["d"]):
                out["dwelling"] = {"d": d, "geom": pts, "tags": tags}
        if tags.get("power") in ("substation", "transformer"):
            if out["power"] is None or d < out["power"]["d"]:
                out["power"] = {"d": d, "geom": pts, "tags": tags}
        if tags.get("waterway") in ("river", "canal") and tags.get("name"):
            if out["water"] is None or d < out["water"]["d"]:
                out["water"] = {"d": d, "geom": pts, "tags": tags}
    return out


def base_image(lat: float, lon: float) -> tuple[Image.Image, float]:
    """Tuiles Esri assemblées, fenêtre centrée sur le pixel monde EXACT du point."""
    cx, cy = world_pixel(lon, lat, Z)
    left, top = cx - W / 2, cy - H / 2
    tx0, ty0 = int(left // 256), int(top // 256)
    tx1, ty1 = int((left + W) // 256), int((top + H) // 256)
    canvas = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    with requests.Session() as s:
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                canvas.paste(fetch_tile(s, Z, tx, ty), ((tx - tx0) * 256, (ty - ty0) * 256))
    ox, oy = int(left - tx0 * 256), int(top - ty0 * 256)
    img = canvas.crop((ox, oy, ox + W, oy + H))
    mpp = 156_543.03392 * math.cos(math.radians(lat)) / (2 ** Z)
    return img, mpp


def projector(lat: float, lon: float):
    cx, cy = world_pixel(lon, lat, Z)
    def to_px(p: tuple[float, float]) -> tuple[float, float]:
        x, y = world_pixel(p[1], p[0], Z)
        return x - cx + W / 2, y - cy + H / 2
    return to_px


def label(img: Image.Image, draw: ImageDraw.ImageDraw, xy, num: str, text: str, font) -> None:
    """Étiquette lisible sur imagerie : texte clair sur bandeau sombre translucide."""
    x, y = xy
    pad = 9
    full = f"{num}  {text}"
    box = draw.textbbox((0, 0), full, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    plate = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), SHADE + (190,))
    img.paste(plate, (int(x), int(y)), plate)
    draw.text((x + pad, y + pad - box[1]), full, font=font, fill=INK)


def marker(draw: ImageDraw.ImageDraw, xy, num: str, colour, font) -> None:
    """Pastille numérotée : on POINTE l'objet, on ne le repeint pas.

    La photo montre déjà la rivière, le poste et les maisons. Redessiner par-dessus
    ajouterait une couche de nous entre le lecteur et la réalité — exactement ce que
    la photo est censée éviter. On se contente donc de désigner et de mesurer.

    Pas de cercle de zone autour d'une pastille non plus (Franck 2026-09-28) : les anneaux
    de distance délimitent DÉJÀ les zones. En ajouter un second, plus petit et sans échelle
    déclarée, inventerait une zone qui ne veut rien dire.
    """
    x, y = xy
    r = 15
    draw.ellipse([x - r, y - r, x + r, y + r], fill=SHADE + (205,), outline=colour + (255,), width=3)
    box = draw.textbbox((0, 0), num, font=font)
    draw.text((x - (box[2] - box[0]) / 2, y - (box[3] - box[1]) / 2 - box[1]), num, font=font, fill=colour)


def render(dc_id: str) -> Path:
    fiche = next(NEWSROOM.glob(f"calibration/datacenters*/{dc_id}.json"))
    ident = json.loads(fiche.read_text())["identity"]
    lat, lon = ident["coordinates"]["lat"], ident["coordinates"]["lon"]

    served = json.loads((REPO / "site/public/data/dc" / f"{dc_id}.json").read_text())
    ind = {i.get("id"): i.get("value") for i in served.get("indicators", [])}

    feat = features(lat, lon, osm_around(lat, lon))
    img, mpp = base_image(lat, lon)
    img = img.convert("RGB")
    to_px = projector(lat, lon)
    draw = ImageDraw.Draw(img, "RGBA")
    f_lab = ImageFont.truetype(str(FONT_PATH), 20)
    f_small = ImageFont.truetype(str(FONT_PATH), 16)
    cx, cy = W / 2, H / 2

    for ring in RINGS_M:
        r = ring / mpp
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK + (110,), width=2)
        draw.text((cx + r * 0.7071 + 4, cy - r * 0.7071 - 22), f"{ring} m", font=f_small, fill=INK + (200,))

    if feat["site"]:
        pts = [to_px(p) for p in feat["site"]["geom"]]
        if len(pts) > 2:
            draw.line(pts + [pts[0]], fill=SITE + (255,), width=4, joint="curve")

    draw.line([(cx - 14, cy), (cx + 14, cy)], fill=INK, width=2)
    draw.line([(cx, cy - 14), (cx, cy + 14)], fill=INK, width=2)

    def nearest_px(entry):
        best = min(entry["geom"], key=lambda p: metres((lat, lon), p))
        return to_px(best)

    bar_m = 200
    bx, by = 40, H - 86
    plate = Image.new("RGBA", (int(bar_m / mpp) + 24, 54), SHADE + (170,))
    img.paste(plate, (bx - 12, by - 34), plate)
    draw.line([(bx, by), (bx + bar_m / mpp, by)], fill=INK, width=3)
    for end in (bx, bx + bar_m / mpp):
        draw.line([(end, by - 8), (end, by + 8)], fill=INK, width=3)
    draw.text((bx, by - 30), f"{bar_m} m", font=f_lab, fill=INK)
    draw.line([(W - 60, 96), (W - 60, 44)], fill=INK, width=3)
    draw.polygon([(W - 60, 38), (W - 67, 54), (W - 53, 54)], fill=INK)
    draw.text((W - 72, 100), "nord", font=f_small, fill=INK)

    power_txt = "Poste électrique : aucun dans 750 m"
    if feat["power"]:
        volts = feat["power"]["tags"].get("voltage")
        kv = " / ".join(f"{int(v) // 1000} kV" if int(v) >= 1000 else f"{v} V" for v in volts.split(";")) \
            if volts and all(v.isdigit() for v in volts.split(";")) else "tension non renseignée"
        op = feat["power"]["tags"].get("operator") or "exploitant non renseigné"
        power_txt = f"Poste {op} — {kv} — {feat['power']['d']:.0f} m"

    w2 = {"poor": "masse d'eau en état médiocre", "bad": "masse d'eau en mauvais état",
          "moderate": "masse d'eau en état moyen", "good": "masse d'eau en bon état"}.get(
              ind.get("W2"), "état de la masse d'eau non renseigné")
    water_txt = "Cours d'eau nommé : aucun dans 750 m"
    if feat["water"]:
        water_txt = f"{feat['water']['tags']['name']} — {feat['water']['d']:.0f} m — {w2}"

    site_txt = "Emprise : aucun bâtiment cartographié"
    if feat["site"]:
        g = feat["site"]["geom"]
        lats, lons = [p[0] for p in g], [p[1] for p in g]
        wm = (max(lons) - min(lons)) * 111_320 * math.cos(math.radians(lat))
        hm = (max(lats) - min(lats)) * 111_320
        # Confirmation POSITIVE seulement. Écrire « non identifié comme data center » sur
        # l'image installait un doute sans rien apprendre au lecteur (Franck 2026-09-28) :
        # l'incertitude d'appariement appartient à la provenance de la fiche, pas au visuel.
        tagged = feat["site"]["tags"].get("building") == "data_center" or feat["site"]["tags"].get("telecom") == "data_center"
        site_txt = (f"Emprise du bâtiment — {wm:.0f} × {hm:.0f} m — à {feat['site']['d']:.0f} m du point"
                    + (" — identifié comme data center" if tagged else ""))
    dwell_txt = f"Zone des logements les plus proches — {feat['dwelling']['d']:.0f} m" if feat["dwelling"] \
        else "Logements : aucun dans 750 m"

    rows = [("1", site_txt, SITE, (cx, cy)),
            ("2", water_txt, WATER, nearest_px(feat["water"]) if feat["water"] else None),
            ("3", power_txt, POWER, nearest_px(feat["power"]) if feat["power"] else None),
            ("4", f"{dwell_txt} · {feat['buildings']} bâtiments dans 750 m", DWELL,
             nearest_px(feat["dwelling"]) if feat["dwelling"] else None)]
    y = 36
    for num, text, colour, anchor in rows:
        label(img, draw, (36, y), num, text, f_lab)
        y += 46
        if anchor and num != "1":
            ax, ay = anchor
            marker(draw, (min(max(ax, 56), W - 56), min(max(ay, 56), H - 110)),
                   num, colour, f_lab)
    marker(draw, (cx, cy + 46), "1", SITE, f_lab)

    foot = [f"scoremydatacenter.org · {served['name']} · {served.get('municipality')} · "
            f"note {served['grades']['site']['grade']} · relevé du {served.get('vintage') or '2026'}",
            "imagerie Esri, Maxar, Earthstar Geographics · objets OpenStreetMap (ODbL) · "
            "état des eaux : directive-cadre européenne"]
    f_foot = ImageFont.truetype(str(FONT_PATH), 14)
    strip = Image.new("RGBA", (W, 48), SHADE + (210,))
    img.paste(strip, (0, H - 48), strip)
    d2 = ImageDraw.Draw(img)
    for i, line in enumerate(foot):
        d2.text((12, H - 42 + i * 19), line, font=f_foot, fill=INK)

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"context-{dc_id}.png"
    img.save(out)
    return out


if __name__ == "__main__":
    print(render(sys.argv[1] if len(sys.argv) > 1 else "fr-virtua-networks"))
