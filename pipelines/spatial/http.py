# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Tiny HTTP + geometry helpers. Stdlib only — the parsers stay dependency-free
so an outside contributor can run them with a bare Python 3.12."""

import json
import math
import urllib.parse
import urllib.request

USER_AGENT = "ScoreMyDataCenter-pipeline/0.1 (+https://scoremydatacenter.org)"
TIMEOUT = 25


class SourceUnavailable(Exception):
    """A source did not answer usably. The collector degrades to 'missing', never crashes."""


def get_text(url: str, params: dict | None = None) -> str:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8", "ignore")
    except Exception as exc:
        raise SourceUnavailable(f"{url}: {exc}") from exc


def get_json(url: str, params: dict | None = None) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # network, HTTP, decode — all degrade the same way
        raise SourceUnavailable(f"{url}: {exc}") from exc


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def circle_geojson(lat: float, lon: float, radius_m: float, segments: int = 32) -> str:
    """A regular polygon approximating a circle, as a GeoJSON string for API Carto `geom`.

    Longitude degrees shrink with latitude; radius is applied in metres on both axes.
    """
    coords = []
    lat_m = 111320.0  # metres per degree of latitude
    lon_m = 111320.0 * math.cos(math.radians(lat))
    for i in range(segments + 1):
        theta = 2 * math.pi * i / segments
        dlat = (radius_m * math.cos(theta)) / lat_m
        dlon = (radius_m * math.sin(theta)) / lon_m
        coords.append([round(lon + dlon, 6), round(lat + dlat, 6)])
    return json.dumps({"type": "Polygon", "coordinates": [coords]})
