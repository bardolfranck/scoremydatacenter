# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""L'INDEX des dossiers d'urbanisme britanniques : point/bbox → dossiers → lien source.

Équivalent GB de `index.py` (France). Même chaîne (cadrage Franck 2026-10-02) :
REGISTRE (index) → LIEN DOC → DOCUMENTS RÉGLEMENTAIRES (contenu). Ce module ne fait que le
premier maillon : trouver le dossier de planning d'un data center, avec de quoi le raccrocher
au corpus (centroïde) et aller chercher ses documents.

Ce qui change vs la France, et qui explique le code :
  · La focale FR est la RÉGION (un schéma WFS DREAL par région). En GB, le gouvernement
    (MHCLG) a DÉJÀ normalisé les ~330 Local Planning Authorities en UN schéma national :
    `planning.data.gov.uk` (Open Government Licence, sans clé). Donc PAS de spec par LPA
    sur le registre — un seul client national. La variabilité par LPA ne touche QUE la
    récupération des PDF (portails IDOX, etc.), maillon suivant.
  · On interroge par GÉOMÉTRIE (bbox WGS84, `geometry_relation=intersects`) — mesuré : la
    requête par point seul rend 0 (les points tombent rarement dans un polygone de dossier),
    la bbox rend les dossiers. On raccroche donc par la position, pas par le nom.
  · COUVERTURE PARTIELLE MESURÉE (2026-10-02) : la plateforme nationale n'a onboardé qu'une
    fraction des LPA pour le jeu `planning-application` (~100 k dossiers, très concentrés).
    Un dossier absent n'est PAS une absence de projet → on le SIGNALE (fallback portail LPA
    / PINS pour les NSIP), on ne conclut jamais « pas de dossier ».

Le dénominateur commun mesuré = description + council + date de décision + référence + centroïde
+ lien. SIRET/opérateur (Companies House) = join SÉPARÉ, downstream (comme le pétitionnaire FR).
On LIE les documents, on ne les réhéberge pas (étude d'impact du pétitionnaire).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import urllib.parse
import urllib.request

from .index import Dossier  # même forme de sortie que la France → downstream partagé

API = "https://www.planning.data.gov.uk/entity.json"
ENTITY_URL = "https://www.planning.data.gov.uk/entity/{eid}"
UA = "ScoreMyDataCenter/1.0 (+https://scoremydatacenter.org)"
TIMEOUT = 120

# Un data center s'écrit de plusieurs façons dans les intitulés de planning. On cherche les
# RACINES, et on retire ce que « data » ramasse à tort (« data cabling », « metadata »…).
IS_A_DC = re.compile(r"data\s*cent(?:re|er)|datacent(?:re|er)|co-?location|colocation\s+facilit|"
                     r"hyperscale|server\s+farm|digital\s+infrastructure", re.I)
NOT_A_DC = re.compile(r"data\s+cabling|metadata|data\s+protection|biodata", re.I)

_COUNCIL_CACHE: dict[int, str] = {}


def _get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def council_name(org_entity: int | str | None) -> str:
    """organisation-entity (id) → nom de la LPA (council), caché. C'est la 'commune' GB."""
    if not org_entity:
        return ""
    oid = int(org_entity)
    if oid in _COUNCIL_CACHE:
        return _COUNCIL_CACHE[oid]
    try:
        req = urllib.request.Request(f"https://www.planning.data.gov.uk/entity/{oid}.json",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            name = json.loads(r.read().decode("utf-8", errors="replace")).get("name", "")
    except Exception:  # noqa: BLE001 — un nom de council manquant n'arrête pas la découverte
        name = ""
    _COUNCIL_CACHE[oid] = name
    return name


def _bbox_wkt(lat: float, lon: float, radius_m: int) -> str:
    """Petit carré WGS84 autour du point (WKT POLYGON, ordre lon lat)."""
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))
    w, e, s, n = lon - dlon, lon + dlon, lat - dlat, lat + dlat
    return f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"


def _centroid(wkt: str) -> tuple[float, float] | None:
    """Point indicatif = moyenne des sommets du WKT (lon lat). Sert à raccrocher au corpus,
    pas à servir une position — on ne reprojette ni ne fabrique rien."""
    nums = [float(x) for x in re.findall(r"-?\d+\.\d+", wkt or "")]
    if len(nums) < 2:
        return None
    lons, lats = nums[0::2], nums[1::2]
    return (sum(lats) / len(lats), sum(lons) / len(lons))


def _to_dossier(e: dict) -> Dossier:
    org = e.get("organisation-entity")
    d = Dossier(region=f"GB-{org}" if org else "GB")
    d.intitule = (e.get("description") or "").strip()
    d.commune = council_name(org)
    d.numero_avis = (e.get("reference") or "").strip()      # réf. de dossier LPA
    d.date_avis = (e.get("decision-date") or "").strip()
    d.date_reception = (e.get("start-date") or "").strip()
    d.statut = "decided" if e.get("decision-date") else "live"
    eid = e.get("entity")
    d.doc_url = ENTITY_URL.format(eid=eid) if eid else ""   # national; les PDF = portail LPA (downstream)
    d.centroid = _centroid(e.get("geometry") or e.get("point") or "")
    if not d.centroid:
        d.warnings.append("dossier sans géométrie — raccrochage au corpus par réf./council seulement")
    return d


def discover_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float,
                  *, dc_only: bool = True, limit: int = 500) -> list[Dossier]:
    """Dossiers de planning intersectant une bbox WGS84 (filtrage DC côté client)."""
    wkt = f"POLYGON(({min_lon} {min_lat},{max_lon} {min_lat},{max_lon} {max_lat}," \
          f"{min_lon} {max_lat},{min_lon} {min_lat}))"
    data = _get({"dataset": "planning-application", "geometry": wkt,
                 "geometry_relation": "intersects", "limit": limit})
    out = []
    for e in data.get("entities", []):
        intitule = e.get("description") or ""
        if dc_only and (NOT_A_DC.search(intitule) or not IS_A_DC.search(intitule)):
            continue
        out.append(_to_dossier(e))
    return out


def discover_near(lat: float, lon: float, *, radius_m: int = 300,
                  dc_only: bool = False, limit: int = 100) -> list[Dossier]:
    """Dossiers près d'un point (ex. une coord de notre corpus DC). dc_only=False par défaut :
    près d'un DC connu on veut SON dossier même si l'intitulé est laconique."""
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))
    found = discover_bbox(lon - dlon, lat - dlat, lon + dlon, lat + dlat,
                          dc_only=dc_only, limit=limit)
    if not found:
        # Couverture partielle : ne jamais conclure « pas de dossier ». On signale le fallback.
        stub = Dossier(region="GB")
        stub.warnings.append(
            f"aucun dossier sur planning.data.gov.uk dans {radius_m} m de ({lat:.5f},{lon:.5f}) — "
            "LPA probablement non onboardée : fallback = portail de la LPA (IDOX Public Access) "
            "ou Planning Inspectorate (NSIP/DCO) pour les gros projets")
        return [stub]
    return found


# --- LE VIVIER : documents RÉGLEMENTAIRES d'un dossier d'implantation DC (le « pas de côté ») ---
# Chaque dossier de planning majeur/EIA DOIT porter ces pièces. C'est la veine de données par
# projet — bien plus large que nos 5 indicateurs spatiaux. Déclaratif : document → ce qu'il
# quantifie → indicateurs/features SMDC qu'il alimente. Sert de SPEC CIBLE à l'extraction
# (maillon suivant), et de carte de couverture. Discipline (cf FR) : chaque fait extrait porte
# sa PHRASE + son N° DE PAGE ; on LIE le PDF ; pas d'OCR (on signale un doc sans couche texte).
REQUIRED_DOCUMENTS = {
    # — socle national (tout dossier) —
    "application_form":        {"mandatory": "all",   "yields": ["use_class", "floorspace_m2", "applicant", "agent"], "feeds": []},
    "location_site_plan":      {"mandatory": "all",   "yields": ["address", "red_line_boundary", "site_area_ha"], "feeds": ["F2_emprise"]},
    # — obligatoire pour tout MAJEUR (un DC l'est) —
    "design_access_statement": {"mandatory": "major", "yields": ["building_footprint", "height_m", "layout", "access"], "feeds": ["cathedrale_visuel"]},
    "biodiversity_gain_plan":  {"mandatory": "major", "yields": ["bng_units", "habitat_baseline", "net_gain_pct"], "feeds": ["F1_biodiversite"]},
    "drainage_suds_strategy":  {"mandatory": "major", "yields": ["impermeable_area", "runoff_rate", "suds"], "feeds": ["F2_sol", "W_eau"]},
    # — suite technique standard d'un DC (local list / EIA) : LE cœur du vivier —
    "environmental_statement": {"mandatory": "eia",   "yields": ["ALL_below_consolidated", "nts"], "feeds": ["*"]},
    "energy_sustainability":   {"mandatory": "local", "yields": ["it_power_mw", "site_power_mva", "pue", "annual_gwh", "renewable_ppa", "carbon_tco2"], "feeds": ["E1_carbone", "E2_E3_reseau"]},
    "grid_connection_utilities": {"mandatory": "local", "yields": ["connection_kv", "substation", "dno", "capacity_mva"], "feeds": ["E2_capacite", "E3_congestion"]},
    "noise_acoustic_assessment": {"mandatory": "local", "yields": ["generator_noise_db", "chiller_db", "emergence_db", "nearest_dwelling_m"], "feeds": ["bruit", "habitations_distance"]},
    "air_quality_assessment":  {"mandatory": "local", "yields": ["generator_count", "generator_mw", "fuel_type", "fuel_tank_m3", "stack_height_m"], "feeds": ["groupes_electrogenes", "cuves_fioul"]},
    "flood_risk_assessment":   {"mandatory": "local", "yields": ["flood_zone", "fra_level"], "feeds": ["W_alea"]},
    "water_foul_drainage":     {"mandatory": "local", "yields": ["water_demand_m3_yr", "cooling_type", "potable_vs_recycled"], "feeds": ["W3_volumes", "refroidissement"]},
    "heat_network_statement":  {"mandatory": "local", "yields": ["waste_heat_recovery", "heat_offtake_contract"], "feeds": ["E6_chaleur_fatale"]},
    "transport_assessment":    {"mandatory": "local", "yields": ["construction_hgv", "operational_trips", "travel_plan"], "feeds": ["nuisance_trafic"]},
    "lvia_landscape_visual":   {"mandatory": "local", "yields": ["visual_receptors", "massing", "screening"], "feeds": ["cathedrale_visuel"]},
    "ecology_appraisal":       {"mandatory": "local", "yields": ["designated_sites", "protected_species"], "feeds": ["F1_natura"]},
    "heritage_archaeology":    {"mandatory": "local", "yields": ["listed_buildings", "conservation_area"], "feeds": ["F_patrimoine"]},
    "ground_contamination":    {"mandatory": "local", "yields": ["prev_use", "contamination", "remediation"], "feeds": ["F2_sol"]},
    "lighting_assessment":     {"mandatory": "local", "yields": ["lux_spill", "obtrusive_light"], "feeds": ["nuisance_lumiere"]},
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Découverte GB : dossiers planning near point/bbox (planning.data.gov.uk).")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--radius", type=int, default=300, help="rayon en mètres (défaut 300)")
    ap.add_argument("--bbox", help="min_lon,min_lat,max_lon,max_lat")
    ap.add_argument("--all", action="store_true", help="ne pas filtrer sur 'data centre'")
    ap.add_argument("--docs", action="store_true", help="imprimer le vivier (documents réglementaires)")
    args = ap.parse_args(argv)

    if args.docs:
        print(json.dumps(REQUIRED_DOCUMENTS, ensure_ascii=False, indent=2))
        return 0
    if args.bbox:
        mn_lon, mn_lat, mx_lon, mx_lat = (float(x) for x in args.bbox.split(","))
        res = discover_bbox(mn_lon, mn_lat, mx_lon, mx_lat, dc_only=not args.all)
    elif args.lat is not None and args.lon is not None:
        res = discover_near(args.lat, args.lon, radius_m=args.radius, dc_only=not args.all)
    else:
        ap.error("fournir --lat/--lon, --bbox, ou --docs")
    print(json.dumps([d.as_dict() for d in res], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
