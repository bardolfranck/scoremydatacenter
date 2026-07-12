# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""EU-level collectors — sources that already cover every member state.

The recon lesson (W2/WISE, then Natura and Corine): before stitching national platforms, go up
one level to the European aggregator. Anything here works for ANY country adapter out of the
box; a country module only overrides these when a national source is strictly richer (e.g.
Wallonia's own Natura layer carries site names the EEA layer lacks).
"""

from .bands import (F1_BEYOND_RINGS, F1_DISTANCE_RINGS, WFD_STATUS_TO_CATEGORY,
                    aqueduct_bws_to_category, clc_to_category)
from .geo import arcgis_identify, arcgis_point_query
from .http import SourceUnavailable, get_json

EEA_NATURA = ("https://bio.discomap.eea.europa.eu/arcgis/rest/services/"
              "ProtectedSites/Natura2000Sites/MapServer")
AQUEDUCT = ("https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/"
            "aqueduct_water_risk/FeatureServer/1")  # layer 1 = Baseline Annual
EEA_NATURA_COMBINED_LAYER = 2  # Habitats + Birds directives combined
EEA_CORINE = ("https://image.discomap.eea.europa.eu/arcgis/rest/services/"
              "Corine/CLC2018_WM/MapServer")
EEA_WISE_SWB = ("https://water.discomap.eea.europa.eu/arcgis/rest/services/"
                "WISE_WFD/WFD2022_SurfaceWaterBody_WM/MapServer")
ENERGY_CHARTS_CO2 = "https://api.energy-charts.info/co2eq"


def _source(title: str, url: str, accessed: str) -> dict:
    return {"title": title, "url": url, "accessed": accessed}


def natura_rings(lat: float, lon: float, accessed: str, *,
                 service_url: str = EEA_NATURA, layer: int = EEA_NATURA_COMBINED_LAYER,
                 site_attr: tuple = ("SITECODE", "CODE_SITE"),
                 title: str = "EEA Natura2000Sites (Habitats+Birds combined) — overlap by distance ring",
                 url: str = EEA_NATURA) -> dict | None:
    """F1 by widening distance rings against any ArcGIS Natura layer (EEA default)."""
    reachable = False
    for radius, category in F1_DISTANCE_RINGS:
        try:
            feats = arcgis_point_query(service_url, layer, lat, lon, max(radius, 1))
        except SourceUnavailable:
            continue
        reachable = True
        if feats:
            codes = sorted({next((f["attributes"].get(a) for a in site_attr
                                  if f.get("attributes", {}).get(a)), None)
                            for f in feats} - {None})
            suffix = f" ({', '.join(codes[:4])})" if codes else ""
            return {"id": "F1", "status": "measured", "value": category,
                    "source": _source(title + suffix, url, accessed)}
    if not reachable:
        return None  # services unreachable — do not assert "distant"
    return {"id": "F1", "status": "measured", "value": F1_BEYOND_RINGS,
            "source": _source(title, url, accessed)}


def corine_at_point(lat: float, lon: float) -> tuple[str | None, str | None]:
    """(clc_code, soil_category) from Corine Land Cover 2018 at the point — EU wall-to-wall."""
    try:
        results = arcgis_identify(EEA_CORINE, lat, lon)
    except SourceUnavailable:
        return None, None
    code = results[0]["attributes"].get("Code_18") if results else None
    return code, clc_to_category(code)


def collect_w1_aqueduct(lat: float, lon: float, accessed: str) -> dict | None:
    """W1 baseline water stress for ANY point on Earth — WRI Aqueduct 4.0 (`bws_cat`/`bws_label`),
    the methodology's cited referential. ArcGIS point query, keyless, no dependency. A stable
    baseline (not volatile current-drought), which is what a durable site score wants."""
    try:
        feats = arcgis_point_query(AQUEDUCT.rsplit("/", 1)[0], int(AQUEDUCT.rsplit("/", 1)[1]),
                                   lat, lon, 1, record_count=1)
    except SourceUnavailable:
        return None
    if not feats:
        return None
    a = feats[0].get("attributes", {})
    cat, label = a.get("bws_cat"), a.get("bws_label")
    if cat is None:
        return None
    category = aqueduct_bws_to_category(int(cat))
    if category is None:
        return None
    return {
        "id": "W1", "status": "measured", "value": category,
        "source": _source(
            f"WRI Aqueduct 4.0 baseline water stress at point — '{label}' (bws_cat {cat}/4)",
            "https://www.wri.org/aqueduct", accessed),
    }


def wise_status_category(water_body_code: str, country: str) -> tuple[str | None, str | None]:
    """(raw_class, category) for a WFD water body code via the cached EEA WISE extract."""
    from .wise import load_wise_status
    try:
        status = load_wise_status(country).get(water_body_code)
    except SourceUnavailable:
        return None, None
    return status, WFD_STATUS_TO_CATEGORY.get(status)


# --- W2 · UNIVERSAL water-body resolver (EEA WISE spatial) — any EU point, no national WFS -----

_WISE_SWB_LAYERS = ((2, 1500), (4, 300), (3, 300), (5, 1500), (6, 3000))  # (layer, buffer m): river line first


def collect_w2_universal(lat: float, lon: float, accessed: str) -> dict | None:
    """W2 for ANY EU country: resolve the water-body code at the point off the EEA WISE spatial
    service, then join its ecological status from the cached WISE extract. Zero national wiring.

    This is a *nearest-within-buffer* resolver (rivers are lines), so a national point-in-polygon
    source, where one exists, stays preferable and takes precedence; this is the universal
    fallback that lifts every country lacking one. Returns None off any EU water body (e.g. a
    Dutch polder plot) — never fabricates.
    """
    code = name = country = None
    for layer, buf in _WISE_SWB_LAYERS:
        try:
            feats = arcgis_point_query(
                EEA_WISE_SWB, layer, lat, lon, buf,
                # outSR/outFields kept minimal; we only need the code + country to join WISE.
            )
        except SourceUnavailable:
            continue
        if feats:
            a = feats[0].get("attributes", {})
            code = a.get("euSurfaceWaterBodyCode")
            name = a.get("surfaceWaterBodyName")
            country = a.get("countryCode")
            if code and country:
                break
    if not code or not country:
        return None
    status, category = wise_status_category(code, country)
    if category is None:
        return None
    return {
        "id": "W2", "status": "measured", "value": category,
        "source": _source(
            f"EEA WISE spatial (WFD 2022) — nearest water body {code} '{name}' at point "
            f"+ WISE ecological status class {status}/5",
            "https://water.discomap.eea.europa.eu/", accessed),
    }


# --- E1 · UNIVERSAL grid carbon intensity (Fraunhofer energy-charts) — national, keyless -------

_e1_cache: dict[tuple[str, str], dict | None] = {}


def collect_e1_energy_charts(country: str, accessed: str) -> dict | None:
    """E1 for any EU country: 12-month mean CO2-equivalent grid intensity from energy-charts.info
    (Fraunhofer ISE, ENTSO-E-derived, keyless). Mean rather than snapshot — grids swing intraday.

    National grid intensity is identical for every DC in a country, so the year-long fetch (~35k
    quarter-hour points) is memoized per (country, window): one call per country per run, not one
    per site — which also stops the batch from rate-limiting itself.

    The national fallback for countries without a wired TSO source (DE, NL, LU…). FR (RTE) and BE
    (Elia) keep their authoritative national feeds. Note: LU has no own bidding zone (DE-LU) — its
    value carries the import caveat in the source title.
    """
    since = f"{int(accessed[:4]) - 1}{accessed[4:]}"
    key = (country.upper(), since)
    if key in _e1_cache:
        return _e1_cache[key]
    try:
        data = get_json(ENERGY_CHARTS_CO2, {"country": country.lower(), "start": since, "end": accessed})
    except SourceUnavailable:
        return None  # transient — not cached, so a later site retries
    vals = [v for v in (data.get("co2eq") or []) if v is not None]
    if not vals:
        return None
    mean = round(sum(vals) / len(vals), 1)
    zone = "DE-LU bidding zone; LU imports most of its electricity" if country.upper() == "LU" else country.upper()
    result = {
        "id": "E1", "status": "measured", "value": mean,
        "source": _source(
            f"Fraunhofer energy-charts.info — {country.upper()} grid CO2-equivalent intensity, "
            f"12-month mean {since}..{accessed} ({mean} gCO2/kWh, n={len(vals)}; zone {zone})",
            "https://api.energy-charts.info/", accessed),
    }
    _e1_cache[key] = result
    return result
