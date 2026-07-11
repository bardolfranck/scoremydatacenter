# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Generic geodata access — ArcGIS REST and OGC WFS point/bbox queries, stdlib only.

Most European public geodata sits behind one of two server families: Esri ArcGIS REST
(geoservices.wallonie.be, EEA discomap…) or OGC WFS (Mercator Vlaanderen, PDOK…). These helpers
are the country-agnostic access layer; a country module contributes endpoints and attribute
names, never its own HTTP plumbing.
"""

import json
import math

from .http import SourceUnavailable, get_json, haversine_m


def arcgis_point_query(service_url: str, layer: int, lat: float, lon: float,
                       distance_m: int, *, geometry: bool = False,
                       record_count: int = 100) -> list[dict]:
    """Features of an ArcGIS layer within distance_m of the point (WGS84 in and out)."""
    params = {
        "f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
        "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
        "distance": distance_m, "units": "esriSRUnit_Meter",
        "outFields": "*", "returnGeometry": "true" if geometry else "false",
        "outSR": "4326", "resultRecordCount": record_count,
    }
    data = get_json(f"{service_url}/{layer}/query", params)
    if "error" in data:
        raise SourceUnavailable(f"{service_url}/{layer}: {data['error']}")
    return data.get("features", [])


def arcgis_identify(service_url: str, lat: float, lon: float) -> list[dict]:
    """Raster/vector identify at a point (used for wall-to-wall layers like Corine)."""
    data = get_json(f"{service_url}/identify", {
        "f": "json",
        "geometry": json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}),
        "geometryType": "esriGeometryPoint", "sr": "4326", "tolerance": 1,
        "mapExtent": f"{lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}",
        "imageDisplay": "400,400,96", "returnGeometry": "false",
    })
    if "error" in data:
        raise SourceUnavailable(f"{service_url}/identify: {data['error']}")
    return data.get("results", [])


def wfs_bbox_geojson(wfs_url: str, typename: str, lat: float, lon: float,
                     radius_m: float, *, count: int = 100) -> list[dict]:
    """GeoJSON features of a WFS 2.0 layer within a radius_m box around the point."""
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
    bbox = f"{lat-dlat},{lon-dlon},{lat+dlat},{lon+dlon},urn:ogc:def:crs:EPSG::4326"
    data = get_json(wfs_url, {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typenames": typename, "outputFormat": "application/json",
        "srsName": "EPSG:4326", "bbox": bbox, "count": str(count),
    })
    return data.get("features", [])


def ogcapi_items(base_url: str, collection: str, lat: float, lon: float,
                 radius_m: float, *, limit: int = 20) -> list[dict]:
    """GeoJSON features of an OGC API Features collection within a radius_m box (pygeoapi…).

    Collection ids may contain a slash (geoportail.lu) — percent-encoded here.
    """
    import urllib.parse
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
    coll = urllib.parse.quote(collection, safe="")
    data = get_json(f"{base_url}/collections/{coll}/items", {
        "bbox": f"{lon-dlon},{lat-dlat},{lon+dlon},{lat+dlat}",
        "f": "json", "limit": str(limit),
    })
    return data.get("features", [])


def laea3035(lat: float, lon: float) -> tuple[float, float]:
    """WGS84/ETRS89 → EPSG:3035 (ETRS89-LAEA), the pan-EU INSPIRE grid. Metres out.

    Lets any collector measure distances against an INSPIRE download (GML in 3035) by
    projecting the query point forward — no inverse transform, no dependency.
    """
    a = 6378137.0
    e2 = 0.00669438002290
    e = math.sqrt(e2)
    lat0, lon0 = math.radians(52.0), math.radians(10.0)
    x0, y0 = 4321000.0, 3210000.0

    def q(phi):
        s = math.sin(phi)
        return (1 - e2) * (s / (1 - e2 * s * s) - (1 / (2 * e)) * math.log((1 - e * s) / (1 + e * s)))

    qp, q0, q1 = q(math.pi / 2), q(lat0), q(math.radians(lat))
    b0, b = math.asin(q0 / qp), math.asin(q1 / qp)
    rq = a * math.sqrt(qp / 2)
    lam = math.radians(lon) - lon0
    big_b = rq * math.sqrt(2 / (1 + math.sin(b0) * math.sin(b) + math.cos(b0) * math.cos(b) * math.cos(lam)))
    x = x0 + big_b * math.cos(b) * math.sin(lam)
    y = y0 + big_b * (math.cos(b0) * math.sin(b) - math.sin(b0) * math.cos(b) * math.cos(lam))
    return x, y


def min_vertex_km(lat: float, lon: float, coords,
                  lat_range: tuple = (35.0, 72.0), lon_range: tuple = (-25.0, 45.0)) -> float | None:
    """Min great-circle distance to any geometry vertex, tolerant of either axis order.

    Some WFS servers emit [lon, lat], others [lat, lon]; we test both interpretations against a
    plausibility window (default: Europe) and keep the nearest plausible one.
    """
    best = None

    def walk(c):
        nonlocal best
        if isinstance(c[0], (int, float)):
            for y, x in ((c[1], c[0]), (c[0], c[1])):
                if lat_range[0] < y < lat_range[1] and lon_range[0] < x < lon_range[1]:
                    d = haversine_m(lat, lon, y, x) / 1000
                    if best is None or d < best:
                        best = d
        else:
            for sub in c:
                walk(sub)

    if coords:
        walk(coords)
    return best
