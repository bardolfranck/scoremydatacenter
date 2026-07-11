# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Belgian national quirks — only what the shared skeleton cannot know.

Belgium's permitting and most geodata are REGIONAL (Wallonia / Flanders / Brussels): the
backbone resolves the region (Nominatim ISO 3166-2) and each collector routes to the regional
source, falling back to the EU-level collectors (eu.py) where the region has no probed layer
yet. Access plumbing lives in geo.py, band semantics in bands.py — nothing here duplicates
them. Every collector returns None rather than guessing.
"""

from .. import eu
from ..bands import l3_value as _l3_value  # canonical home: bands.py (kept for tests)
from ..geo import arcgis_point_query, min_vertex_km as _min_vertex_km, wfs_bbox_geojson
from ..http import SourceUnavailable, get_json, haversine_m

WALLONIA_ARCGIS = "https://geoservices.wallonie.be/arcgis/rest/services"
MERCATOR_WFS = "https://www.mercator.vlaanderen.be/raadpleegdienstenmercatorpubliek/wfs"


def _source(title: str, url: str, accessed: str) -> dict:
    return {"title": title, "url": url, "accessed": accessed}


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
    try:
        feats = arcgis_point_query(f"{WALLONIA_ARCGIS}/EAU/MESU/MapServer", 2, lat, lon, 1)
    except SourceUnavailable:
        return None
    if not feats:
        return None
    a = feats[0]["attributes"]
    code, name = a.get("EU_SWB_COD"), a.get("SWB_NAME")
    if not code:
        return None
    status, category = eu.wise_status_category(code, "BE")
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
        return eu.natura_rings(
            lat, lon, accessed,
            service_url=f"{WALLONIA_ARCGIS}/FAUNE_FLORE/NATURA2000/MapServer", layer=10,
            title="SPW geoservices FAUNE_FLORE/NATURA2000 — Natura 2000 overlap by distance ring",
            url=f"{WALLONIA_ARCGIS}/FAUNE_FLORE/NATURA2000/MapServer")
    return eu.natura_rings(lat, lon, accessed)  # EEA EU-wide combined layer


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
    primary, primary_src = None, None
    if region == "wallonia":
        try:
            feats = arcgis_point_query(
                f"{WALLONIA_ARCGIS}/AMENAGEMENT_TERRITOIRE/PDS/MapServer", 22, lat, lon, 1)
            if feats:
                desc = feats[0]["attributes"].get("DESCRIPTION")
                art = feats[0]["attributes"].get("ART_CODT")
                primary = _pds_to_category(desc)
                primary_src = f"plan de secteur '{desc}' ({art})"
        except SourceUnavailable:
            pass
    clc_code, clc_cat = eu.corine_at_point(lat, lon)
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
        url = f"{WALLONIA_ARCGIS}/AMENAGEMENT_TERRITOIRE/PDS/MapServer"
    else:
        title = (f"Corine Land Cover 2018 (EEA) — CLC code {clc_code} at point "
                 f"(EU-wide fallback; regional legal zoning not available, no cross-check)")
        url = eu.EEA_CORINE
    return {"id": "F2", "status": "measured", "value": value,
            "source": _source(title, url, accessed)}, crosscheck


# --- L3 · technological hazard / Seveso (SPW points; Mercator Flanders polygons) --------------

def collect_l3(lat: float, lon: float, region: str, accessed: str) -> dict | None:
    sites, detail = [], []
    if region == "wallonia":
        url = f"{WALLONIA_ARCGIS}/INDUSTRIES_SERVICES/SEVESO/MapServer"
        try:
            feats = arcgis_point_query(url, 0, lat, lon, 5000, geometry=True)
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
        url = MERCATOR_WFS
        try:
            feats = wfs_bbox_geojson(MERCATOR_WFS, "pf:pf_seveso_con", lat, lon, 5000)
        except SourceUnavailable:
            return None
        for f in feats:
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
