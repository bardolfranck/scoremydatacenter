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
import urllib.error
import urllib.parse
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

CAVEAT_SHORT = ("distances à vol d'oiseau depuis la coordonnée de référence · "
                "les anneaux sont des tampons de distance, non un zonage réglementaire")

CAVEAT_FULL = (
    "Les distances sont mesurées à vol d'oiseau depuis la coordonnée de référence du site. "
    "Les objets localisés — cours d'eau, postes électriques, bâtiments — proviennent "
    "d'OpenStreetMap, dont la complétude varie d'un territoire à l'autre : la mention "
    "« aucun dans 750 m » signale une absence de DONNÉE, pas nécessairement une absence "
    "d'objet. Les anneaux sont des tampons de distance, non un zonage réglementaire. "
    "L'état de la masse d'eau est rapporté à l'échelle de la masse d'eau au titre de la "
    "directive-cadre européenne, et non au point."
)

RESIDENTIAL = {"residential", "apartments", "house", "detached", "semidetached_house", "terrace", "dormitory"}


def fr_number(x: float) -> str:
    """1400.0 -> « 1 400 » ; 1.4 -> « 1,4 » — séparateur de milliers espace, virgule décimale."""
    if abs(x - round(x)) < 0.05:
        return f"{int(round(x)):,}".replace(",", " ")
    return f"{x:.1f}".replace(".", ",")


_POP_CACHE_PATH = OUT_DIR / "pop-cache.json"
_POP_CACHE: dict | None = None


def _pop_cache() -> dict:
    global _POP_CACHE
    if _POP_CACHE is None:
        try:
            _POP_CACHE = json.loads(_POP_CACHE_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            _POP_CACHE = {}
    return _POP_CACHE


def _pop_cache_key(served: dict) -> str:
    """Cache PAR COMMUNE (pas par fiche) : nos fiches se concentrent sur quelques agglomérations
    (Francfort en porte des dizaines) → divise les appels Nominatim (1 req/s, banni sur du volume).
    Clé = pays|commune ; repli sur une cellule de coord ~1 km si la commune manque."""
    cc = (served.get("country") or "").upper()
    muni = (served.get("municipality") or "").strip().lower()
    if muni:
        return f"{cc}|{muni}"
    return f"{cc}|cell:{round(served.get('_lat', 0), 2)},{round(served.get('_lon', 0), 2)}"


def commune_population(served: dict, ind: dict) -> tuple[int | None, str]:
    """Population de la commune — partout en Europe et dans le monde, sans clé.
    Cache disque PAR COMMUNE (voir _pop_cache_key) : une seule requête Nominatim par agglomération."""
    cache = _pop_cache()
    key = _pop_cache_key(served)
    if key in cache:
        c = cache[key]
        return (c[0], c[1]) if c else (None, "non récupérée")
    pop, source = _commune_population_uncached(served, ind)
    cache[key] = [pop, source] if pop else None
    try:
        _POP_CACHE_PATH.parent.mkdir(exist_ok=True)
        _POP_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False))
    except OSError:
        pass
    return pop, source


def _commune_population_uncached(served: dict, ind: dict) -> tuple[int | None, str]:
    """Population de la commune — partout en Europe et dans le monde, sans clé.

    Nominatim en géocodage inverse avec `extratags=1` rend la population de la commune,
    et à défaut son identifiant Wikidata d'où la propriété P1082 la donne. Vérifié sur
    Francfort 756 021, Amsterdam 881 933, Varsovie 1 863 845, Beringen 4 118, Tuusula
    42 521. En France, geo.api.gouv.fr reste prioritaire : c'est l'INSEE, déjà la source
    du pipeline spatial, et elle est plus à jour.

    Repli de dernier recours : L2 est la puissance pour 1 000 habitants, donc la population
    s'en déduit quand on a la puissance — approchée, donc arrondie à la centaine.
    """
    lat, lon = served["_lat"], served["_lon"]
    if served.get("country") == "FR":
        try:
            from pipelines.spatial import sources
            pop = sources.fetch_commune(lat, lon).get("population")
            if pop:
                return int(pop), "geo.api.gouv.fr (INSEE)"
        except Exception:
            pass
    try:
        pop, source = _nominatim_population(lat, lon)
        if pop:
            return pop, source
    except Exception:
        pass
    mw, l2 = served.get("power_mw"), ind.get("L2")
    if mw and l2:
        pop = mw / l2 * 1000
        return (round(pop) if pop < 1000 else round(pop / 100) * 100), "déduite de L2"
    return None, "non récupérée"


def _nominatim_population(lat: float, lon: float) -> tuple[int | None, str]:
    query = urllib.parse.urlencode({"lat": lat, "lon": lon, "format": "jsonv2",
                                    "extratags": 1, "zoom": 10})
    url = f"https://nominatim.openstreetmap.org/reverse?{query}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as resp:
        extra = (json.loads(resp.read()).get("extratags") or {})
    if str(extra.get("population", "")).isdigit():
        return int(extra["population"]), "OpenStreetMap (Nominatim)"
    qid = extra.get("wikidata")
    if not qid:
        return None, ""
    wd = f"https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={qid}&property=P1082&format=json"
    with urllib.request.urlopen(urllib.request.Request(wd, headers=UA), timeout=30) as resp:
        claims = json.loads(resp.read()).get("claims", {}).get("P1082", [])
    if claims:
        amount = claims[-1]["mainsnak"]["datavalue"]["value"]["amount"]
        return int(float(amount)), f"Wikidata {qid}"
    return None, ""


def scale_line(served: dict, ind: dict) -> str | None:
    """« 1 400 MW déclarés — commune de 650 habitants ».

    Par défaut sur TOUTES les fiches (arbitrage Franck 2026-09-28) : le rapport entre la
    puissance et la taille de la commune intéresse autant un site urbain qu'un greenfield.

    Quand la puissance manque — le cas de beaucoup de projets — la ligne ne disparaît PAS :
    le nombre d'habitants reste une information utile, et l'ignorance de la puissance est
    elle-même un fait à publier. On écrit alors « puissance déclarée inconnue ».

    Le qualificatif suit power_mw_status : « déclarés » quand l'exploitant l'annonce,
    « estimés » quand nous l'avons reconstituée. Ne jamais écrire « déclarés » sur une
    estimation maison : ce serait lui attribuer un chiffre qui est le nôtre.
    """
    mw = served.get("power_mw")
    pop, _ = commune_population(served, ind)
    if mw:
        # 39 fiches du corpus portent une puissance sans statut : on nomme le trou plutôt
        # que d'écrire un chiffre nu, qui se lirait comme une donnée vérifiée.
        qualifier = {"announced": "déclarés", "declared": "déclarés",
                     "estimated": "estimés"}.get(served.get("power_mw_status"), "source non consignée")
        head = (f"{fr_number(mw)} MW {qualifier}" if qualifier.endswith("és")
                else f"{fr_number(mw)} MW, {qualifier}")
    else:
        head = "Puissance déclarée inconnue"
    if pop:
        return f"{head} — commune de {fr_number(pop)} habitants"
    return head if mw else None


def metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = math.pi / 180
    dlat, dlon = (b[0] - a[0]) * r, (b[1] - a[1]) * r
    h = math.sin(dlat / 2) ** 2 + math.cos(a[0] * r) * math.cos(b[0] * r) * math.sin(dlon / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


_OSM_FALLBACK_USED = False  # set per call; render() records it in the stats sidecar

_OVERPASS = "https://overpass-api.de/api/interpreter"


def _overpass_around(w: float, s: float, e: float, n: float) -> dict:
    """FALLBACK for dense bboxes only. OSM /map returns 400 above ~50 000 nodes (cities); a FILTERED
    Overpass query (buildings + substations/transformers + named rivers/canals) stays well under the
    cap. Same bbox → same 750 m radius → annotation text UNCHANGED. Returns the /map element shape
    (ways with node refs + tags, nodes with lat/lon) so features() is untouched."""
    bbox = f"{s:.6f},{w:.6f},{n:.6f},{e:.6f}"
    # `out geom` (not `>;out body`) — inline way geometry, no node-recurse: far lighter, avoids the
    # 504 that the recurse triggers on dense city bboxes. We then rebuild the /map element shape
    # (way.nodes refs + node lat/lon) so features() is untouched.
    q = (f'[out:json][timeout:120];'
         f'(way["building"]({bbox});node["building"]({bbox});'
         f'way["power"~"substation|transformer"]({bbox});node["power"~"substation|transformer"]({bbox});'
         f'way["waterway"~"river|canal"]["name"]({bbox}););out tags geom;')
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(_OVERPASS, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = json.loads(resp.read())
    # Normalise to the OSM /map shape: nodes carry (id,lat,lon); ways carry nodes=[ids]+tags.
    elements, nid = [], -1
    for el in raw.get("elements", []):
        if el["type"] == "node":
            elements.append({"type": "node", "id": el["id"], "lat": el["lat"], "lon": el["lon"],
                             "tags": el.get("tags", {})})
        elif el["type"] == "way":
            refs = []
            for pt in el.get("geometry") or []:
                if pt is None:
                    continue
                elements.append({"type": "node", "id": nid, "lat": pt["lat"], "lon": pt["lon"]})
                refs.append(nid); nid -= 1
            elements.append({"type": "way", "id": el["id"], "nodes": refs, "tags": el.get("tags", {})})
    return {"elements": elements}


def osm_around(lat: float, lon: float, half_km: float = 0.75) -> dict:
    """Objets dans un rayon de 750 m. OSM /map d'abord (a encaissé 1430 fiches sans erreur, pas de
    politique de volume) ; sur HTTP 400 (bbox trop dense, plafond 50k nœuds) SEULEMENT → repli
    Overpass filtré, même rayon. Repli compté (stats) — au-delà de ~10 %, à re-signaler."""
    global _OSM_FALLBACK_USED
    _OSM_FALLBACK_USED = False
    dlat = half_km / 111.32
    dlon = dlat / max(math.cos(math.radians(lat)), 0.2)
    w, s, e, n = lon - dlon, lat - dlat, lon + dlon, lat + dlat
    url = OSM_MAP.format(w=w, s=s, e=e, n=n)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            raise
        _OSM_FALLBACK_USED = True
        return _overpass_around(w, s, e, n)


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

    served["_lat"], served["_lon"] = lat, lon
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

    if feat["site"] and not (
            served.get("project_status") in ("announced", "permitting", "under_construction")
            and not (feat["site"]["tags"].get("building") == "data_center"
                     or feat["site"]["tags"].get("telecom") == "data_center")):
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
    nplate = Image.new("RGBA", (74, 96), SHADE + (170,))
    img.paste(nplate, (W - 97, 28), nplate)
    draw.line([(W - 60, 96), (W - 60, 50)], fill=INK, width=3)
    draw.polygon([(W - 60, 42), (W - 68, 60), (W - 52, 60)], fill=INK)
    draw.text((W - 76, 100), "nord", font=f_small, fill=INK)

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

    # Sur une fiche PROJET, ne JAMAIS cerner un bâtiment qui n'est pas tagué data center :
    # le site n'est pas construit, donc le « bâtiment le plus proche » est celui de
    # quelqu'un d'autre — une ferme voisine cernée et légendée « emprise » ferait croire
    # que le data center est déjà là, et le ferait croire sur le bien d'un tiers.
    is_project = served.get("project_status") in ("announced", "permitting", "under_construction")
    site_tagged = bool(feat["site"]) and (
        feat["site"]["tags"].get("building") == "data_center"
        or feat["site"]["tags"].get("telecom") == "data_center")
    if is_project and not site_tagged:
        feat["site"] = None

    site_txt = "Projet — aucune emprise bâtie à ce jour" if is_project else "Emprise : aucun bâtiment cartographié"
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
    scale = scale_line(served, ind)
    if scale:
        rows.append(("5", scale, INK, None))
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
            "état des eaux : directive-cadre européenne",
            CAVEAT_SHORT]
    f_foot = ImageFont.truetype(str(FONT_PATH), 14)
    strip = Image.new("RGBA", (W, 67), SHADE + (210,))
    img.paste(strip, (0, H - 67), strip)
    d2 = ImageDraw.Draw(img)
    for i, line in enumerate(foot):
        d2.text((12, H - 61 + i * 19), line, font=f_foot, fill=INK)

    # WEBP comme la vignette satellite, PAS PNG : sur de l'imagerie aérienne, un PNG
    # 1200 × 900 pèse ~1,9 Mo contre ~210 Ko en WebP qualité 82 — neuf fois plus lourd pour
    # une image destinée à s'afficher sur CHAQUE fiche. À l'échelle du corpus c'est 2,3 Go
    # au lieu de 260 Mo, et un temps de chargement qui rendrait la carte inutilisable.
    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"context-{dc_id}.webp"
    img.save(out, "WEBP", quality=82)
    # Stats sidecar (additif — n'altère pas l'image) : signaux pour le rapport d'industrialisation
    # (poste sans tension, annotations vides), sans re-fetch OSM côté wrapper.
    pv = feat["power"]["tags"].get("voltage") if feat["power"] else None
    pv_ok = bool(pv) and all(v.isdigit() for v in pv.split(";")) if pv else False
    try:
        (OUT_DIR / f"context-{dc_id}.stats.json").write_text(json.dumps({
            "power_present": bool(feat["power"]),
            "power_voltage_missing": bool(feat["power"]) and not pv_ok,
            "water_present": bool(feat["water"]),
            "dwelling_present": bool(feat["dwelling"]),
            "site_present": bool(feat["site"]),
            "buildings_750m": feat["buildings"],
            "osm_fallback": _OSM_FALLBACK_USED,
        }, ensure_ascii=False))
    except OSError:
        pass
    return out


if __name__ == "__main__":
    print(render(sys.argv[1] if len(sys.argv) > 1 else "fr-virtua-networks"))
