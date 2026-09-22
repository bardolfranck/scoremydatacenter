# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Distance au bâtiment d'habitation le plus proche (OpenStreetMap / Overpass).

    make habitations            # calcule le manquant, écrit le sidecar newsroom, commit

Un FAIT sourcé et daté, publié à côté de la note — il n'entre dans aucun indicateur, aucun pilier,
aucune lettre (même doctrine que la contestation). Deux niveaux de preuve, jamais mélangés :

  - `building` : un bâtiment tagué résidentiel (house, apartments, detached…) — le cas net ;
  - `landuse`  : seulement une zone `landuse=residential`, quand le bâti n'est pas encore tagué
                 (fréquent en rural). Moins précis : signalé comme tel, jamais présenté comme
                 une distance à une maison.

La distance est calculée jusqu'au CENTRE de l'objet OSM (`out center`) : elle est donc prudente
(légèrement surestimée pour un grand polygone), ce que le site doit dire — « environ X m ».
Aucune valeur n'est inventée : pas de réponse OSM → pas de champ.
"""

import json
import sys
import time

from pipelines.press.osm_projects import _fetch_overpass
from pipelines.veille.dedup import haversine_m

# Tags de bâti résidentiel: volontairement restrictif (un « yes » générique ne prouve pas qu'on
# habite dedans — une halle logistique est taguée building=yes).
RESIDENTIAL = ("residential|house|apartments|detached|semidetached_house|terrace|bungalow|farm|"
               "dormitory|static_caravan")
RADIUS_M = 2000          # au-delà, « pas de voisinage proche » dit déjà tout
LICENSE = "OpenStreetMap contributors, ODbL 1.0"


def query(lat, lon, radius=RADIUS_M):
    return (f"[out:json][timeout:120];("
            f'nwr["building"~"^({RESIDENTIAL})$"](around:{radius},{lat},{lon});'
            f'way["landuse"="residential"](around:{radius},{lat},{lon});'
            f");out center tags;")


def nearest(lat, lon, *, fetch=_fetch_overpass, radius=RADIUS_M):
    """(distance_m, kind) du plus proche élément résidentiel, ou (None, None) si OSM ne sait pas.

    Un vrai bâtiment l'emporte toujours sur une zone `landuse` moins précise, même plus proche."""
    data = fetch(query(lat, lon, radius))
    best = {"building": None, "landuse": None}
    for el in data.get("elements", []):
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        if c.get("lat") is None or c.get("lon") is None:
            continue
        kind = "landuse" if (el.get("tags") or {}).get("landuse") == "residential" else "building"
        m = haversine_m(lat, lon, c["lat"], c["lon"])
        if best[kind] is None or m < best[kind]:
            best[kind] = m
    for kind in ("building", "landuse"):
        if best[kind] is not None:
            return round(best[kind]), kind
    return None, None


def resolve(fiches, previous, today, *, fetch=_fetch_overpass, pause=2.0, recheck_days=365):
    """Calcule le manquant, réutilise l'existant (le bâti bouge lentement, Overpass est partagé).
    Une panne Overpass conserve la valeur précédente — elle n'efface jamais un fait déjà publié."""
    import datetime as dt
    out, failures = {}, 0
    for fi in fiches:
        prev = previous.get(fi["id"])
        if prev and prev.get("checked_at") and (
                dt.date.fromisoformat(today) - dt.date.fromisoformat(prev["checked_at"])).days < recheck_days:
            out[fi["id"]] = prev
            continue
        try:
            d, kind = nearest(fi["lat"], fi["lon"], fetch=fetch)
        except Exception as e:  # noqa: BLE001 — Overpass down/429: on gardera l'ancienne valeur
            failures += 1
            print(f"habitations: {fi['id']}: {e}", file=sys.stderr)
            if prev:
                out[fi["id"]] = prev
            continue
        if d is None:
            out[fi["id"]] = {"checked_at": today, "found": False}
        else:
            out[fi["id"]] = {"distance_m": d, "kind": kind, "checked_at": today, "found": True,
                             "source": "OpenStreetMap", "license": LICENSE, "radius_m": RADIUS_M}
        time.sleep(pause)   # Overpass est un service public partagé
    return out, failures
