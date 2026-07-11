# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""EU-level collectors — sources that already cover every member state.

The recon lesson (W2/WISE, then Natura and Corine): before stitching national platforms, go up
one level to the European aggregator. Anything here works for ANY country adapter out of the
box; a country module only overrides these when a national source is strictly richer (e.g.
Wallonia's own Natura layer carries site names the EEA layer lacks).
"""

from .bands import F1_BEYOND_RINGS, F1_DISTANCE_RINGS, WFD_STATUS_TO_CATEGORY, clc_to_category
from .geo import arcgis_identify, arcgis_point_query
from .http import SourceUnavailable

EEA_NATURA = ("https://bio.discomap.eea.europa.eu/arcgis/rest/services/"
              "ProtectedSites/Natura2000Sites/MapServer")
EEA_NATURA_COMBINED_LAYER = 2  # Habitats + Birds directives combined
EEA_CORINE = ("https://image.discomap.eea.europa.eu/arcgis/rest/services/"
              "Corine/CLC2018_WM/MapServer")


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


def wise_status_category(water_body_code: str, country: str) -> tuple[str | None, str | None]:
    """(raw_class, category) for a WFD water body code via the cached EEA WISE extract."""
    from .wise import load_wise_status
    try:
        status = load_wise_status(country).get(water_body_code)
    except SourceUnavailable:
        return None, None
    return status, WFD_STATUS_TO_CATEGORY.get(status)
