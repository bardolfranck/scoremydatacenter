# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""SHARED spatial dedup — ONE source of truth for study_review (cohort) AND onboard (en-veille).

Pure, no I/O, trivially testable. Consolidates the two dedup passes that previously lived apart
(and drifted): vs the SERVED corpus, and candidate-vs-candidate. Design agreed EU × codeur-API
(2026-09-07); brand-token logic authored by codeur-API, placed here (pipelines/veille/ = EU domain).

Two shapes coexist — study_review snapshot items carry top-level lat/lon; onboard « en veille »
entries carry coordinates.{lat,lon} (watchlist schema). `_coords` reads both so one util serves both.

Rule (vs-served), fail-closed:
  EXCLUDE (auto-drop, certainly already public) = same 2 dp cell AND (exact operator after norm
    OR identical FIRST brand token) — the near-certain same site.
  FLAG (keep, mark for human review — voie rouge) = same cell + brand overlap that is NOT the
    first token (e.g. « Global Realty » vs « Digital Realty » share 'realty') — a dense-cluster
    coincidence, never auto-dropped and never auto-published.
  None = clean.
"""

import math
import re

_LEGAL = {"gmbh", "oy", "oyj", "ab", "ltd", "limited", "sa", "sas", "sarl", "bv", "ag", "plc",
          "llc", "inc", "srl", "spa", "as", "nv", "kg", "kgaa", "se", "corp", "co"}
_GENERIC = {"data", "center", "centre", "datacenter", "dc", "campus", "park", "cloud",
            "colocation", "colo"}
CELL_DP = 2  # served coords are 2 dp (~1.1 km) — dedup at the served resolution


def norm_op(op):
    toks = [t for t in re.split(r"[^a-z0-9]+", (op or "").lower()) if t and t not in _LEGAL]
    s = "".join(toks)
    return "" if not s or s.startswith("unknown") else s


def brand_tokens(op):
    return [t for t in re.split(r"[^a-z0-9]+", (op or "").lower())
            if t and t not in _LEGAL and t not in _GENERIC and len(t) >= 4]


def brand_overlap(a, b):
    return bool(set(brand_tokens(a)) & set(brand_tokens(b)))


def _first_brand(op):
    b = brand_tokens(op)
    return b[0] if b else None


def cell(lat, lon, dp=CELL_DP):
    try:
        return (round(float(lat), dp), round(float(lon), dp))
    except (TypeError, ValueError):
        return None


def _coords(item):
    """(lat, lon) from either top-level lat/lon or a nested coordinates{} — both shapes in use."""
    if item.get("lat") is not None and item.get("lon") is not None:
        return item["lat"], item["lon"]
    c = item.get("coordinates") or {}
    return c.get("lat"), c.get("lon")


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def served_index(features):
    """{cell: [(id, operator)]} from served map.geojson features (geometry.coordinates=[lon,lat])."""
    idx = {}
    for f in features or []:
        lon, lat = ((f.get("geometry") or {}).get("coordinates") or [None, None])[:2]
        c = cell(lat, lon)
        if c is None:
            continue
        p = f.get("properties") or {}
        idx.setdefault(c, []).append((p.get("id"), p.get("operator")))
    return idx


def index_from_entries(entries):
    """{cell: [(id, operator)]} from watchlist-shaped entries (coordinates.{lat,lon})."""
    idx = {}
    for e in entries or []:
        lat, lon = _coords(e)
        c = cell(lat, lon)
        if c is None:
            continue
        idx.setdefault(c, []).append((e.get("id"), e.get("operator")))
    return idx


def match_served(cand_lat, cand_lon, cand_op, idx):
    """('exclude', served_id) | ('flag', served_id) | None — see module rule."""
    served = idx.get(cell(cand_lat, cand_lon)) or []
    cf, cn = _first_brand(cand_op), norm_op(cand_op)
    flag = None
    for sid, sop in served:
        if cn and cn == norm_op(sop):
            return ("exclude", sid)                      # exact operator
        sf = _first_brand(sop)
        if cf and sf and cf == sf:
            return ("exclude", sid)                      # identical first brand token
        if flag is None and brand_overlap(cand_op, sop):
            flag = ("flag", sid)                         # non-first overlap → human review
    return flag


def dedup_internal(candidates, meters=250):
    """Candidate-vs-candidate: 2 OSM ways of one project (same operator, <= meters) → keep first.
    Returns (kept, merged) where merged = [(dropped_id, kept_id)]."""
    kept, merged = [], []
    for c in candidates:
        cn = norm_op(c.get("operator"))
        c_lat, c_lon = _coords(c)
        dup = None
        for k in kept:
            if not (cn and cn == norm_op(k.get("operator"))):
                continue
            k_lat, k_lon = _coords(k)
            try:
                if haversine_m(c_lat, c_lon, k_lat, k_lon) <= meters:
                    dup = k
                    break
            except (KeyError, TypeError):
                pass
        if dup:
            merged.append((c.get("id"), dup.get("id")))
        else:
            kept.append(c)
    return kept, merged
