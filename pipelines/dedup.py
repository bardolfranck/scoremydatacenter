"""Candidate de-duplication for the veille chantiers (voie A/B leads → existing corpus).

A discovery pipeline (CNDP saisine, GDELT announce, DCMag lead…) surfaces a *candidate*
project; before it becomes a new watchlist entry or a new panel, it must be checked against
what we already track — otherwise the same site enters twice under two spellings.

Two independent checks, because leads arrive with different evidence:

  * `near_existing(lat, lon, corpus, km)` — SPATIAL. For a geocoded candidate (geo.api.gouv
    gave it a point). The strong signal: two records within `km` are almost surely the same
    site regardless of how they are named.
  * `name_matches(municipality, operator, corpus)` — NOMINAL. For a press-only lead with no
    coordinates yet. The weak fallback: same commune AND same operator. Never commune alone —
    a big metro hosts many distinct sites.

Both are READ-ONLY and side-effect free: they return the matching corpus records (nearest /
best first) so the caller decides — merge, enrich, or list as new. They never mutate the
corpus and never assign a grade. Pure stdlib, reuses the canonical `haversine_m` so there is
one earth-radius in the codebase, not two.
"""

from __future__ import annotations

from pipelines.spatial.http import haversine_m

__all__ = ["coords_of", "haversine_km", "near_existing", "name_matches"]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres (thin wrapper over the canonical metre version)."""
    return haversine_m(lat1, lon1, lat2, lon2) / 1000.0


def coords_of(rec: dict) -> tuple[float, float] | None:
    """(lat, lon) of a record, tolerant of both shapes we store.

    Datacenter panels nest under `identity.coordinates`; watchlist entries and raw leads keep
    `coordinates` at top level. Missing or malformed → None (the record simply can't be matched
    spatially, which is not an error).
    """
    c = (rec.get("identity") or {}).get("coordinates") or rec.get("coordinates")
    if not isinstance(c, dict):
        return None
    lat, lon = c.get("lat"), c.get("lon")
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        return float(lat), float(lon)
    return None


def _identity_field(rec: dict, key: str) -> str:
    """Read `key` from either `identity.<key>` (panel) or top level (watchlist/lead)."""
    val = (rec.get("identity") or {}).get(key)
    if val is None:
        val = rec.get(key)
    return (val or "").strip().casefold()


def near_existing(lat: float, lon: float, corpus, km: float = 2.0) -> list[dict]:
    """Corpus records within `km` of (lat, lon), nearest first.

    Each returned item is the ORIGINAL record with an added `_distance_km` (rounded, read-only
    annotation for the caller's benefit) — a non-empty list means "probable duplicate(s), don't
    onboard blind". Records without usable coordinates are skipped, not matched.

    `km` default 2.0: tight enough that two hits are the same campus, loose enough to absorb the
    ~hundreds-of-metres scatter between a geocoded commune centroid and a precise site point.
    """
    hits = []
    for rec in corpus:
        pt = coords_of(rec)
        if pt is None:
            continue
        d = haversine_km(lat, lon, pt[0], pt[1])
        if d <= km:
            hits.append((d, rec))
    hits.sort(key=lambda t: t[0])
    return [{**rec, "_distance_km": round(d, 3)} for d, rec in hits]


def name_matches(municipality: str, operator: str, corpus) -> list[dict]:
    """Corpus records sharing BOTH commune and operator (case/space-insensitive).

    The fallback for a press-only lead with no coordinates. Requires both fields on both sides:
    a match on commune alone is not a duplicate (one town, many sites), and an empty operator or
    municipality on either side never matches (absence is not agreement).
    """
    m, o = (municipality or "").strip().casefold(), (operator or "").strip().casefold()
    if not m or not o:
        return []
    out = []
    for rec in corpus:
        if _identity_field(rec, "municipality") == m and _identity_field(rec, "operator") == o:
            out.append(rec)
    return out
