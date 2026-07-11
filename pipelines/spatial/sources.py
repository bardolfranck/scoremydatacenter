# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Tier-1 collectors — one clean public source per indicator (v1 perimeter: E1, W1, F1, F2, L3).

Each collector maps an API answer onto the methodology's exact unit/categories and returns a
schema-shaped indicator dict ``{id, status, value, source}`` — or ``None`` when the source could
not be reached (the caller then leaves the indicator for manual collection; it never fabricates).
No collector returns a score, a note, or free text. See RECON.md for why these five and not others.
"""

from .http import SourceUnavailable, circle_geojson, get_json, get_text, haversine_m
from .cache import cached_path

# --- backbone -------------------------------------------------------------------------------

GEO_API = "https://geo.api.gouv.fr/communes"


def fetch_commune(lat: float, lon: float) -> dict:
    """Coords → administrative context (raises SourceUnavailable if the backbone is down)."""
    fields = "nom,code,population,surface,codeDepartement,codeRegion,codesPostaux"
    data = get_json(GEO_API, {"lat": lat, "lon": lon, "fields": fields, "format": "json"})
    if not data:
        raise SourceUnavailable("geo.api.gouv.fr returned no commune for the point (outside FR?)")
    return data[0]


def _source(title: str, url: str, accessed: str) -> dict:
    return {"title": title, "url": url, "accessed": accessed}


# --- E1 · grid carbon intensity (RTE eCO2mix, national) -------------------------------------

def collect_e1(accessed: str) -> dict | None:
    url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records"
    params = {"where": "taux_co2 IS NOT NULL", "order_by": "date_heure DESC", "limit": 1,
              "select": "date_heure,taux_co2"}
    try:
        rec = get_json(url, params)["results"][0]
    except (SourceUnavailable, KeyError, IndexError):
        return None
    return {
        "id": "E1",
        "status": "measured",
        "value": float(rec["taux_co2"]),
        # National grid intensity: France's electricity mix is managed nationally by RTE.
        "source": _source(
            f"RTE eCO2mix — national CO2 intensity {rec['date_heure']} ({rec['taux_co2']} gCO2/kWh)",
            "https://www.rte-france.com/eco2mix/les-emissions-de-co2-par-kwh-produit-en-france",
            accessed),
    }


# --- W1 · local water stress (VigiEau / Propluvia) ------------------------------------------

_VIGIEAU_TO_CATEGORY = {
    "vigilance": "moderate",
    "alerte": "high",
    "alerte_renforcee": "high",
    "crise": "zre_or_crisis",
}
_VIGIEAU_RANK = {"vigilance": 1, "alerte": 2, "alerte_renforcee": 3, "crise": 4}


def collect_w1(lat: float, lon: float, accessed: str) -> dict | None:
    url = "https://api.vigieau.beta.gouv.fr/api/zones"
    try:
        zones = get_json(url, {"lat": lat, "lon": lon, "profil": "particulier"})
    except SourceUnavailable:
        return None
    if not isinstance(zones, list):
        return None
    if not zones:  # no active restriction zone at this point
        value, arrete_url = "no_stress", None
    else:
        worst = max(zones, key=lambda z: _VIGIEAU_RANK.get(z.get("niveauGravite"), 0))
        value = _VIGIEAU_TO_CATEGORY.get(worst.get("niveauGravite"), "no_stress")
        arrete_url = (worst.get("arrete") or {}).get("cheminFichier")
    return {
        "id": "W1",
        "status": "measured",
        "value": value,
        "source": _source(
            f"VigiEau — drought-restriction status at point (accessed {accessed})",
            arrete_url or "https://vigieau.gouv.fr/",
            accessed),
    }


# --- F1 · protected-area overlap / distance (API Carto IGN — INPN) --------------------------

_NATURE_LAYERS = {
    "natura-habitat": "Natura 2000 (habitats)",
    "natura-oiseaux": "Natura 2000 (oiseaux)",
    "znieff1": "ZNIEFF type 1",
    "znieff2": "ZNIEFF type 2",
}


def collect_f1(lat: float, lon: float, accessed: str) -> dict | None:
    import json as _json
    point = _json.dumps({"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]})
    reachable = False
    # Tier by widening buffer; short-circuit on the first ring that intersects any layer.
    for radius, category in ((0, "overlap"), (1000, "adjacent_under_1km"), (5000, "near_1_to_5km")):
        geom = point if radius == 0 else circle_geojson(lat, lon, radius)
        for layer in _NATURE_LAYERS:
            url = f"https://apicarto.ign.fr/api/nature/{layer}"
            try:
                hit = (get_json(url, {"geom": geom}).get("totalFeatures") or 0) > 0
            except SourceUnavailable:
                continue
            reachable = True
            if hit:
                return _f1_result(category, accessed)
    if not reachable:
        return None  # API Carto unreachable — do not assert "distant"
    return _f1_result("distant_over_5km", accessed)


def _f1_result(value: str, accessed: str) -> dict:
    return {
        "id": "F1",
        "status": "measured",
        "value": value,
        "source": _source(
            "INPN / IGN API Carto — Natura 2000 & ZNIEFF overlap by distance ring",
            "https://apicarto.ign.fr/api/doc/nature",
            accessed),
    }


# --- F2 · soil status (API Carto IGN — PLU zoning, RPG fallback) ----------------------------

def _zone_to_category(typezone: str) -> str | None:
    t = (typezone or "").upper()
    if t.startswith("AU"):
        return "transitional"
    if t.startswith("U"):
        return "artificialized"
    if t.startswith("A"):
        return "agricultural"
    if t.startswith("N"):
        return "natural_or_enaf"
    return None


def collect_f2(lat: float, lon: float, accessed: str) -> dict | None:
    import json as _json
    geom = _json.dumps({"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]})
    primary, primary_src = None, None
    # 1) PLU zoning (most direct soil-vocation signal — legal vocation).
    try:
        feats = get_json("https://apicarto.ign.fr/api/gpu/zone-urba", {"geom": geom}).get("features") or []
    except SourceUnavailable:
        feats = None
    if feats:
        props = feats[0]["properties"]
        cat = _zone_to_category(props.get("typezone") or props.get("libelle"))
        if cat:
            primary = cat
            primary_src = _source(
                f"IGN API Carto GPU — PLU zoning '{props.get('libelle') or props.get('typezone')}'",
                "https://apicarto.ign.fr/api/doc/gpu", accessed)
    # 2) RPG registered agricultural parcel.
    if primary is None:
        try:
            rpg = get_json("https://apicarto.ign.fr/api/rpg/v2", {"geom": geom, "annee": 2022}).get("features") or []
        except SourceUnavailable:
            rpg = None
        if rpg:
            primary, primary_src = "agricultural", _source(
                "IGN API Carto RPG — point falls on a registered agricultural parcel (2022)",
                "https://apicarto.ign.fr/api/doc/rpg", accessed)

    # 3) Corine Land Cover — wall-to-wall observed land cover: the no-gap fallback AND the
    #    independent cross-check (observed cover vs. legal zoning).
    clc_code = _clc_at_point(lat, lon)
    clc_cat = _clc_to_category(clc_code)

    crosscheck = None
    if primary is not None and clc_cat is not None:
        crosscheck = {"primary": primary, "primary_source": "PLU/RPG",
                      "land_cover": clc_cat, "clc_code": clc_code,
                      "agree": primary == clc_cat}

    if primary is not None:
        return {"id": "F2", "status": "measured", "value": primary, "source": primary_src}, crosscheck
    if clc_cat is not None:  # fallback where PLU+RPG are silent
        return {
            "id": "F2", "status": "measured", "value": clc_cat,
            "source": _source(
                f"IGN Corine Land Cover 2018 — class {clc_code} (observed land cover fallback)",
                "https://data.geopf.fr/wfs/ows", accessed),
        }, None
    return None, None


def _clc_at_point(lat: float, lon: float) -> str | None:
    """Corine Land Cover 2018 class code (code_18) of the polygon containing the point."""
    params = {
        "SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
        "TYPENAMES": "LANDCOVER.CLC18_FR:clc18_fr", "SRSNAME": "CRS:84",
        "COUNT": 1, "OUTPUTFORMAT": "application/json",
        # Point coordinates are given in EPSG:4326 (lon lat) via the EWKT SRID prefix, so the
        # filter reprojects instead of reading them as the layer's native Lambert-93.
        "CQL_FILTER": f"INTERSECTS(geom, SRID=4326;POINT({lon} {lat}))",
    }
    try:
        feats = get_json("https://data.geopf.fr/wfs/ows", params).get("features") or []
    except SourceUnavailable:
        return None
    return feats[0]["properties"].get("code_18") if feats else None


from .bands import clc_to_category as _clc_to_category  # canonical home: bands.py


# --- L1 · municipality socio-economic profile (INSEE Filosofi, cached) ----------------------

# Commune median disposable income (Filosofi), open CSV on data.gouv (INSEE source).
_FILOSOFI_URL = ("https://static.data.gouv.fr/resources/revenu-des-francais-a-la-commune/"
                 "20251210-134014/revenu-des-francais-a-la-commune-1765372688826.csv")
_FILOSOFI_CODE_COL = "Code géographique"
_FILOSOFI_MEDIAN_COL = "[DISP] Médiane (€)"
_filosofi_index: dict[str, float] | None = None


def _load_filosofi() -> dict[str, float]:
    global _filosofi_index
    if _filosofi_index is not None:
        return _filosofi_index
    import csv
    path = cached_path(_FILOSOFI_URL, "filosofi_communes.csv")
    index: dict[str, float] = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            code = (row.get(_FILOSOFI_CODE_COL) or "").strip()
            raw = (row.get(_FILOSOFI_MEDIAN_COL) or "").replace(" ", "").replace(" ", "").strip()
            try:
                index[code] = float(raw)
            except ValueError:
                continue
    # Paris/Lyon/Marseille: Filosofi keys these by municipal arrondissement (75101…), but the
    # geocoder returns the commune head (75056). Back-fill each head with the median of its
    # arrondissements so a point in central Paris still resolves.
    import statistics
    for head, prefix in (("75056", "751"), ("69123", "6938"), ("13055", "132")):
        arr = [v for code, v in index.items() if code.startswith(prefix) and code != head]
        if arr and head not in index:
            index[head] = statistics.median(arr)
    _filosofi_index = index
    return index


def _l1_category(median_income: float) -> str:
    # PROVISIONAL bands on commune quartiles (Q1 ~21.3k€, Q3 ~24.7k€); methodology owns calibration.
    # Ethics: a poorer municipality is 'sensitive' (cannot improve the score), never 'strong_fit'.
    if median_income < 21000:
        return "sensitive"
    if median_income <= 25000:
        return "neutral"
    return "strong_fit"


def collect_l1(commune_insee: str, accessed: str) -> dict | None:
    try:
        median = _load_filosofi().get(commune_insee)
    except SourceUnavailable:
        return None
    if median is None:
        return None
    return {
        "id": "L1",
        "status": "measured",
        "value": _l1_category(median),
        "source": _source(
            f"INSEE Filosofi (via data.gouv) — commune {commune_insee}: "
            f"median disposable income {median:.0f} €/consumption unit",
            "https://www.data.gouv.fr/datasets/revenu-des-francais-a-la-commune/",
            accessed),
    }


# --- W3 · basin withdrawal pressure (Hub'Eau BNPE) ------------------------------------------

def _w3_category(volume_mm3: float) -> str:
    # PROVISIONAL thresholds on commune annual withdrawal (Mm3/yr); methodology owns calibration.
    if volume_mm3 < 0.5:
        return "low"
    if volume_mm3 < 5:
        return "moderate"
    if volume_mm3 < 50:
        return "high"
    return "very_high"


def collect_w3(commune_insee: str, accessed: str) -> dict | None:
    url = "https://hubeau.eaufrance.fr/api/v1/prelevements/chroniques"
    try:
        data = get_json(url, {"code_commune_insee": commune_insee, "size": 200}).get("data") or []
    except SourceUnavailable:
        return None
    years = [r["annee"] for r in data if r.get("annee")]
    if not years:
        return None
    latest = max(years)
    total_m3 = sum(r["volume"] for r in data if r.get("annee") == latest and r.get("volume"))
    volume_mm3 = round(total_m3 / 1e6, 3)
    return {
        "id": "W3",
        "status": "measured",
        "value": _w3_category(volume_mm3),
        "source": _source(
            f"Hub'Eau BNPE — commune {commune_insee}: {volume_mm3} Mm3 withdrawn in {latest} "
            f"(all uses, provisional pressure band)",
            "https://hubeau.eaufrance.fr/page/api-prelevements-eau",
            accessed),
    }


# --- W2 water-body identification (Sandre WFS) — code only, status join is the next collector ---

def resolve_water_body(lat: float, lon: float) -> dict | None:
    """Return {code, name} of the DCE water body at the point.

    Uses Sandre's 2022 reporting layer (VRAP2022) so the code matches the WISE 2022 status table
    used by collect_w2 — the 2013 delineation (VEDL) has coarser, non-aligned codes.
    """
    import html
    import re
    url = ("https://services.sandre.eaufrance.fr/geo/sandre?SERVICE=WFS&VERSION=1.1.0"
           "&REQUEST=GetFeature&TYPENAME=sa:MasseDEauRiviere_VRAP2022_FXX"
           f"&SRSNAME=urn:ogc:def:crs:EPSG::4326&MAXFEATURES=1"
           f"&BBOX={lat-0.03},{lon-0.03},{lat+0.03},{lon+0.03},urn:ogc:def:crs:EPSG::4326")
    try:
        gml = get_text(url)
    except SourceUnavailable:
        return None
    code = re.search(r"<sa:CdEuMasseDEau>([^<]+)</", gml)
    name = re.search(r"<sa:NomMasseDEau>([^<]+)</", gml)
    if not code:
        return None
    return {"code": code.group(1), "name": html.unescape(name.group(1)) if name else None}


# --- W2 · water body ecological status (Sandre WFS + EEA WISE, cached) -----------------------

from .bands import WFD_STATUS_TO_CATEGORY as _WISE_STATUS_TO_CATEGORY  # canonical home: bands.py


def collect_w2(lat: float, lon: float, accessed: str) -> dict | None:
    from .wise import load_wise_status
    wb = resolve_water_body(lat, lon)
    if not wb:
        return None
    try:
        status = load_wise_status().get(wb["code"])
    except SourceUnavailable:
        return None
    category = _WISE_STATUS_TO_CATEGORY.get(status)
    if category is None:  # code absent or status 'Unknown' — don't fabricate
        return None
    return {
        "id": "W2",
        "status": "measured",
        "value": category,
        "source": _source(
            f"EEA WISE (WFD 2022) — water body {wb['code']} '{wb['name']}': "
            f"ecological status class {status}/5",
            "https://discodata.eea.europa.eu/",
            accessed),
    }


# --- L3 · technological hazard / Seveso (Géorisques) ----------------------------------------

def collect_l3(lat: float, lon: float, accessed: str) -> dict | None:
    url = "https://www.georisques.gouv.fr/api/v1/installations_classees"
    try:
        data = get_json(url, {"latlon": f"{lon},{lat}", "rayon": 5000, "page": 1, "page_size": 100})
    except SourceUnavailable:
        return None
    sites = data.get("data") or []
    high_within_2km = False
    seveso_within_5km = False
    for s in sites:
        statut = (s.get("statutSeveso") or "")
        if "Seveso" not in statut:
            continue
        slat, slon = s.get("latitude"), s.get("longitude")
        if slat is None or slon is None:
            continue
        dist = haversine_m(lat, lon, slat, slon)
        if dist <= 5000:
            seveso_within_5km = True
        if "haut" in statut.lower() and dist <= 2000:
            high_within_2km = True
    if high_within_2km:
        value = "seveso_high_within_2km"
    elif seveso_within_5km:
        value = "seveso_low_within_5km"
    else:
        value = "none_within_5km"
    return {
        "id": "L3",
        "status": "measured",
        "value": value,
        "source": _source(
            "Géorisques — classified installations (Seveso status) within 5 km",
            "https://www.georisques.gouv.fr/",
            accessed),
    }
