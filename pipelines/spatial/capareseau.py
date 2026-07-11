# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""E2 / E3 — grid connection capacity & congestion, from Caparéseau.

Caparéseau (RTE) publishes no documented API, but its Leaflet map is fed by a per-region JSON
of substations (poste sources) carrying WGS84 coordinates and the full S3REnR capacity block —
available hosting capacity (MW) and the reserved-capacity fill rate (%). We read that feed
directly: coordinates → nearest substation → E2 (available capacity) + E3 (congestion).

"No API" was never "no data". The map has to load its markers from somewhere; we load the same
file it does. The media UUID rotates, so we discover it from the region page each run instead of
hard-coding it. Category thresholds below are PROVISIONAL (methodology owns the final calibration);
the raw MW / % is kept in each source title so the mapping stays auditable.
"""

import json
import re

from .http import SourceUnavailable, get_json, get_text, haversine_m

BASE = "https://www.capareseau.fr"
_REGION_CACHE: dict[str, list[dict]] = {}


def _num(raw) -> float | None:
    """Parse Caparéseau's mixed number formatting ('100 %', '41.7', '1,6', '') → float or None."""
    if raw is None:
        return None
    s = str(raw).replace("%", "").replace(" ", " ").replace(",", ".").strip()
    s = s.split(" ")[0] if s else s
    try:
        return float(s)
    except ValueError:
        return None


def _region_postes(region_code: str) -> list[dict]:
    """The substation feed for one INSEE region code (poste dicts with X/Y/code/values)."""
    if region_code in _REGION_CACHE:
        return _REGION_CACHE[region_code]
    html = get_text(f"{BASE}/region/{region_code}")
    postes: list[dict] = []
    for uuid in dict.fromkeys(re.findall(r"/medias/([A-F0-9]{8}-[A-F0-9-]{20,})", html)):
        try:
            data = get_json(f"{BASE}/medias/{uuid}")
        except SourceUnavailable:
            continue
        if isinstance(data, list) and data and isinstance(data[0], dict) and \
                {"code", "X", "Y", "values"} <= set(data[0]):
            postes = data
            break
    _REGION_CACHE[region_code] = postes
    return postes


def _nearest(lat: float, lon: float, postes: list[dict],
             required_fields: tuple[str, ...] = ()) -> tuple[dict, float] | None:
    """Nearest substation. If required_fields is given, prefer the nearest one whose `values` has
    all of them populated (so E2 and E3 describe the *same* poste); fall back to nearest overall."""
    best, best_d = None, None
    fallback, fallback_d = None, None
    for p in postes:
        plon, plat = _num(p.get("X")), _num(p.get("Y"))
        if plon is None or plat is None:
            continue
        d = haversine_m(lat, lon, plat, plon)
        if fallback_d is None or d < fallback_d:
            fallback, fallback_d = p, d
        if required_fields:
            vals = p.get("values")
            if not isinstance(vals, dict) or any(_num(vals.get(f)) is None for f in required_fields):
                continue  # empty/absent values (some postes carry values: []) → not a candidate
        if best_d is None or d < best_d:
            best, best_d = p, d
    if best is not None:
        return best, best_d
    return (fallback, fallback_d) if fallback else None


from .bands import e2_category as _e2_category  # canonical home: bands.py


from .bands import e3_category as _e3_category  # canonical home: bands.py


def collect_grid_capacity(lat: float, lon: float, region_code: str | None, accessed: str) -> list[dict]:
    """Return [E2, E3] indicators for the substation nearest to the point (empty on any failure)."""
    if not region_code:
        return []
    try:
        postes = _region_postes(region_code)
    except SourceUnavailable:
        return []
    # Prefer the nearest poste that carries BOTH capacity fields, so E2 and E3 stay consistent.
    match = _nearest(lat, lon, postes, required_fields=("RTE_CDR", "INFO_TX"))
    if not match:
        return []
    poste, dist_m = match
    vals = poste.get("values")
    vals = vals if isinstance(vals, dict) else {}  # fallback poste may carry values: []
    name, code = poste.get("name", "?"), poste.get("code", "?")
    dist_km = round(dist_m / 1000, 1)
    updated = poste.get("updated", "")
    url = f"{BASE}/region/{region_code}?postCode={code}"

    indicators = []
    available = _num(vals.get("RTE_CDR"))
    if available is not None:
        indicators.append({
            "id": "E2", "status": "measured", "value": _e2_category(available),
            "source": {
                "title": f"Caparéseau (RTE S3REnR) — poste {name} at {dist_km} km: "
                         f"{available} MW available hosting capacity (updated {updated})",
                "url": url, "accessed": accessed,
            },
        })
    fill = _num(vals.get("INFO_TX"))
    if fill is not None:
        indicators.append({
            "id": "E3", "status": "measured", "value": _e3_category(fill),
            "source": {
                "title": f"Caparéseau (RTE S3REnR) — poste {name} at {dist_km} km: "
                         f"{fill}% reserved-capacity fill rate (updated {updated})",
                "url": url, "accessed": accessed,
            },
        })
    return indicators
