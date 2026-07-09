# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Belgian tier-1 collectors — regional sources behind the national backbone.

Belgium's permitting and most geodata are REGIONAL (Wallonia / Flanders / Brussels). The good
news from the 2026-07-09 recon: Wallonia's geoservices.wallonie.be is a one-stop ArcGIS REST
serving five indicators with one query pattern; Flanders splits across Mercator/DOV; EU-level
services (EEA Natura 2000, Corine, WISE) fill most Flanders/Brussels gaps. Every collector
returns None rather than guessing — a gap is a provenance line, never a fabricated value.
"""

import json

from ..http import SourceUnavailable, get_json, haversine_m

_WALLONIA_ARCGIS = "https://geoservices.wallonie.be/arcgis/rest/services"
_EEA_NATURA = ("https://bio.discomap.eea.europa.eu/arcgis/rest/services/"
               "ProtectedSites/Natura2000Sites/MapServer")
_EEA_CORINE = ("https://image.discomap.eea.europa.eu/arcgis/rest/services/"
               "Corine/CLC2018_WM/MapServer")
_MERCATOR_WFS = "https://www.mercator.vlaanderen.be/raadpleegdienstenmercatorpubliek/wfs"


def _source(title: str, url: str, accessed: str) -> dict:
    return {"title": title, "url": url, "accessed": accessed}


def _arcgis_point_query(service_path: str, layer: int, lat: float, lon: float,
                        distance_m: int, *, geometry: bool = False) -> list[dict]:
    """Features of an ArcGIS layer within distance_m of the point (WGS84 in and out)."""
    params = {
        "f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
        "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
        "distance": distance_m, "units": "esriSRUnit_Meter",
        "outFields": "*", "returnGeometry": "true" if geometry else "false",
        "outSR": "4326", "resultRecordCount": 100,
    }
    data = get_json(f"{service_path}/{layer}/query", params)
    if "error" in data:
        raise SourceUnavailable(f"{service_path}/{layer}: {data['error']}")
    return data.get("features", [])


# --- identity backbone — commune + region routing ---------------------------------------------

_ISO_REGION = {"BE-WAL": "wallonia", "BE-VLG": "flanders", "BE-BRU": "brussels"}


def fetch_commune(lat: float, lon: float) -> dict:
    """{name, nis, region, province_iso} at the point.

    Nominatim reverse gives the commune name and the ISO 3166-2 region key (BE-WAL/VLG/BRU) that
    drives the adapter routing; the NIS code joins in from the cached official REFNIS
    nomenclature by normalized commune name (FR and NL names both indexed).
    """
    try:
        data = get_json("https://nominatim.openstreetmap.org/reverse",
                        {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10})
    except SourceUnavailable as exc:
        raise SourceUnavailable(f"backbone geocoder unreachable: {exc}") from exc
    addr = data.get("address", {})
    region = _ISO_REGION.get(addr.get("ISO3166-2-lvl4", ""), "unknown")
    province_iso = addr.get("ISO3166-2-lvl6")
    name = addr.get("town") or addr.get("city") or addr.get("municipality") or addr.get("village")
    nis = None
    if name:
        from .statbel import _normalize, load_refnis
        try:
            nis = load_refnis().get(_normalize(name))
        except SourceUnavailable:
            pass
    return {"name": name, "nis": nis, "region": region, "province_iso": province_iso}


# --- W2 · water body ecological status (SPW MESU code → EEA WISE status) ----------------------

def collect_w2(lat: float, lon: float, region: str, accessed: str) -> dict | None:
    """Wallonia only in v0: the Flanders surface-water-body code layer is still unlocated."""
    if region != "wallonia":
        return None
    from ..sources import _WISE_STATUS_TO_CATEGORY
    from ..wise import load_wise_status
    try:
        feats = _arcgis_point_query(f"{_WALLONIA_ARCGIS}/EAU/MESU/MapServer", 2, lat, lon, 1)
    except SourceUnavailable:
        return None
    if not feats:
        return None
    a = feats[0]["attributes"]
    code, name = a.get("EU_SWB_COD"), a.get("SWB_NAME")
    if not code:
        return None
    try:
        status = load_wise_status("BE").get(code)
    except SourceUnavailable:
        return None
    category = _WISE_STATUS_TO_CATEGORY.get(status)
    if category is None:
        return None
    return {
        "id": "W2",
        "status": "measured",
        "value": category,
        "source": _source(
            f"SPW geoservices EAU/MESU (water body {code} '{name}' at point) + EEA WISE WFD — "
            f"ecological status class {status}/5",
            "https://discodata.eea.europa.eu/",
            accessed),
    }


# --- F1 · protected areas by distance ring (SPW Natura 2000, EEA fallback) --------------------

def collect_f1(lat: float, lon: float, region: str, accessed: str) -> dict | None:
    if region == "wallonia":
        base, layer = f"{_WALLONIA_ARCGIS}/FAUNE_FLORE/NATURA2000/MapServer", 10
        title = "SPW geoservices FAUNE_FLORE/NATURA2000 — Natura 2000 overlap by distance ring"
        url = f"{base}"
    else:
        base, layer = _EEA_NATURA, 2  # combined Habitats + Birds layer
        title = "EEA Natura2000Sites (Habitats+Birds combined) — overlap by distance ring"
        url = _EEA_NATURA
    reachable = False
    for radius, category in ((1, "overlap"), (1000, "adjacent_under_1km"), (5000, "near_1_to_5km")):
        try:
            feats = _arcgis_point_query(base, layer, lat, lon, radius)
        except SourceUnavailable:
            continue
        reachable = True
        if feats:
            codes = sorted({f["attributes"].get("CODE_SITE") or f["attributes"].get("SITECODE")
                            for f in feats if f.get("attributes")})
            codes = [c for c in codes if c]
            return {
                "id": "F1", "status": "measured", "value": category,
                "source": _source(f"{title} ({', '.join(codes[:4])})", url, accessed),
            }
    if not reachable:
        return None  # services unreachable — do not assert "distant"
    return {"id": "F1", "status": "measured", "value": "distant_over_5km",
            "source": _source(title, url, accessed)}


# --- F2 · soil status (SPW plan de secteur; Corine fallback elsewhere) ------------------------

def _pds_to_category(description: str) -> str | None:
    """Walloon plan de secteur zone description → methodology soil category."""
    d = (description or "").lower()
    if "aménagement communal" in d:            # ZACC — to be opened by communal decision
        return "transitional"
    if any(k in d for k in ("économique", "industrielle", "habitat", "services publics",
                            "équipements communautaires", "extraction", "loisirs")):
        return "artificialized"
    if "agricole" in d:
        return "agricultural"
    if any(k in d for k in ("forestière", "naturelle", "espaces verts", "parc")):
        return "natural_or_enaf"
    return None


def collect_f2(lat: float, lon: float, region: str, accessed: str) -> tuple[dict | None, dict]:
    """Legal zoning first (Wallonia PDS), Corine Land Cover as fallback/cross-check."""
    from ..sources import _clc_to_category
    primary, primary_src, clc_cat, clc_code = None, None, None, None
    if region == "wallonia":
        try:
            feats = _arcgis_point_query(
                f"{_WALLONIA_ARCGIS}/AMENAGEMENT_TERRITOIRE/PDS/MapServer", 22, lat, lon, 1)
            if feats:
                desc = feats[0]["attributes"].get("DESCRIPTION")
                art = feats[0]["attributes"].get("ART_CODT")
                primary = _pds_to_category(desc)
                primary_src = f"plan de secteur '{desc}' ({art})"
        except SourceUnavailable:
            pass
    # Corine at point — fallback where zoning is silent, cross-check where it isn't
    try:
        identify = get_json(f"{_EEA_CORINE}/identify", {
            "f": "json",
            "geometry": json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryPoint", "sr": "4326", "tolerance": 1,
            "mapExtent": f"{lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}",
            "imageDisplay": "400,400,96", "returnGeometry": "false",
        })
        results = identify.get("results") or []
        clc_code = results[0]["attributes"].get("Code_18") if results else None
        clc_cat = _clc_to_category(clc_code)
    except SourceUnavailable:
        pass
    crosscheck = {
        "primary": primary, "primary_source": primary_src,
        "land_cover": clc_cat, "clc_code": clc_code,
        "agree": (primary == clc_cat) if primary and clc_cat else None,
    }
    value = primary or clc_cat
    if value is None:
        return None, crosscheck
    if primary:
        title = (f"SPW plan de secteur (AMENAGEMENT_TERRITOIRE/PDS) — {primary_src}; "
                 f"Corine cross-check: {clc_cat or 'unavailable'}")
        url = f"{_WALLONIA_ARCGIS}/AMENAGEMENT_TERRITOIRE/PDS/MapServer"
    else:
        title = (f"Corine Land Cover 2018 (EEA) — CLC code {clc_code} at point "
                 f"(EU-wide fallback; regional legal zoning not available, no cross-check)")
        url = _EEA_CORINE
    return {"id": "F2", "status": "measured", "value": value,
            "source": _source(title, url, accessed)}, crosscheck


# --- L3 · technological hazard / Seveso (SPW points; Mercator Flanders polygons) --------------

def _l3_value(sites: list[dict]) -> str:
    """sites = [{upper_tier: bool, dist_km: float}] within 5 km → methodology band."""
    if any(s["upper_tier"] and s["dist_km"] <= 2.0 for s in sites):
        return "seveso_high_within_2km"
    if sites:
        return "seveso_low_within_5km"
    return "none_within_5km"


def collect_l3(lat: float, lon: float, region: str, accessed: str) -> dict | None:
    sites, detail, url = [], [], None
    if region == "wallonia":
        url = f"{_WALLONIA_ARCGIS}/INDUSTRIES_SERVICES/SEVESO/MapServer"
        try:
            feats = _arcgis_point_query(url, 0, lat, lon, 5000, geometry=True)
        except SourceUnavailable:
            return None
        for f in feats:
            a, g = f["attributes"], f.get("geometry") or {}
            if "x" not in g:
                continue
            d = haversine_m(lat, lon, g["y"], g["x"]) / 1000
            upper = (a.get("SEUIL_DESC") or "").lower().startswith("seuil haut")
            sites.append({"upper_tier": upper, "dist_km": d})
            detail.append(f"{a.get('SOC_NOM')} ({a.get('SEUIL_DESC')}) at {round(d, 2)} km")
        title_src = "SPW geoservices INDUSTRIES_SERVICES/SEVESO"
    elif region == "flanders":
        url = _MERCATOR_WFS
        import math
        import urllib.parse
        import urllib.request
        dlat = 5000 / 111320.0
        dlon = 5000 / (111320.0 * math.cos(math.radians(lat)))
        bbox = f"{lat-dlat},{lon-dlon},{lat+dlat},{lon+dlon},urn:ogc:def:crs:EPSG::4326"
        params = {"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                  "typenames": "pf:pf_seveso_con", "outputFormat": "application/json",
                  "srsName": "EPSG:4326", "bbox": bbox, "count": "100"}
        try:
            data = get_json(f"{_MERCATOR_WFS}", params)
        except SourceUnavailable:
            return None
        for f in data.get("features", []):
            p, geom = f.get("properties", {}), f.get("geometry")
            if not geom:
                continue
            d = _min_vertex_km(lat, lon, geom.get("coordinates"))
            if d is None or d > 5.0:
                continue
            upper = (p.get("status") or "").lower().startswith("hoge")
            sites.append({"upper_tier": upper, "dist_km": d})
            detail.append(f"{p.get('bedrijf')} ({p.get('status')}) at {round(d, 2)} km")
        title_src = "Mercator Vlaanderen WFS pf_seveso_con"
    else:
        return None  # Brussels layer not probed yet (v1 backlog)
    value = _l3_value(sites)
    detail_sorted = ", ".join(sorted(detail)[:4]) if detail else "no Seveso site within 5 km"
    return {"id": "L3", "status": "measured", "value": value,
            "source": _source(f"{title_src} — {detail_sorted}", url, accessed)}


def _min_vertex_km(lat: float, lon: float, coords) -> float | None:
    """Min great-circle distance to any polygon vertex, tolerant of either axis order."""
    best = None

    def walk(c):
        nonlocal best
        if isinstance(c[0], (int, float)):
            for y, x in ((c[1], c[0]), (c[0], c[1])):  # try [lon,lat] and [lat,lon]
                if 49 < y < 52 and 2 < x < 7:
                    d = haversine_m(lat, lon, y, x) / 1000
                    if best is None or d < best:
                        best = d
        else:
            for sub in c:
                walk(sub)

    if coords:
        walk(coords)
    return best


# --- L1 · commune income — RAW ONLY (provenance), FR bands are not transposable ---------------

def collect_l1_raw(nis: str | None) -> dict | None:
    """Median net taxable income per declaration (Statbel Table D), commune aggregate.

    Returned for the PROVENANCE sidecar only — never as an L1 indicator value. The FR income
    bands are calibrated on Filosofi €/consumption-unit; Statbel's per-declaration median is a
    different quantity, and mapping it through FR cutoffs would hand a misleading 'strong_fit'
    to modest communes. BE bands are a methodology-lead decision (recon-voie-EU section 3).
    Aggregation = median of the commune's statistical-sector medians — the same technique the FR
    pipeline uses to back-fill Paris/Lyon/Marseille from arrondissements.
    """
    if not nis:
        return None
    import statistics
    from .statbel import load_sector_income
    try:
        sectors = load_sector_income()
    except SourceUnavailable:
        return None
    medians = sectors.get(nis)
    if not medians:
        return None
    return {
        "median_of_sector_medians_eur": round(statistics.median(medians), 2),
        "sectors_used": len(medians),
        "definition": "median net taxable income per declaration (fisc2023, Table D)",
        "url": "https://statbel.fgov.be/fr/themes/menages/revenus-fiscaux",
        "note": "raw value only — BE bands pending methodology calibration, FR bands refused",
    }
