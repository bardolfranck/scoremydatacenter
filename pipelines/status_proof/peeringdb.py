# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""PeeringDB facility ↔ fiche join (public API, no key).

A facility where networks interconnect (net_count > 0) is running. The join is the risk:
a campus hosts several buildings (SBG-1 operating, SBG-7 a project), so a BIND needs all
three of coordinates ≤ 150 m, a shared brand token AND matching building suffixes. Anything
else is not a bind — it is never resolved by a human, it simply proves nothing.
"""

import json
import re
import sys
import time
import urllib.request

from pipelines.veille.dedup import brand_tokens, haversine_m

API = "https://www.peeringdb.com/api/fac"
UA = "smdc-status-proof/1.0 (scoremydatacenter.org)"
FIELDS = "id,name,name_long,aka,latitude,longitude,net_count,ix_count,campus_id,org_name,city,country"
MAX_DIST_M = 150


def suffix(s):
    """Building identifiers (« SBG-7 », « PA7 », « TH2 ») — the campus discriminant."""
    return set(re.findall(r"[a-z]*\d+[a-z]*", (s or "").lower()))


def fetch_facilities(retries=4):
    """Every PeeringDB facility with coordinates, grouped by country — ONE request (the anonymous
    API rate-limits per-country loops). Raises on persistent failure: a silent empty result would
    publicly turn every verified fiche into « non vérifié »."""
    url = f"{API}?fields={FIELDS}"
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r).get("data", [])
            by_country = {}
            for f in data:
                if f.get("latitude") is None or f.get("longitude") is None:
                    continue
                by_country.setdefault(f.get("country") or "", []).append(f)
            return by_country
        except Exception as e:  # noqa: BLE001 — network/HTTP/JSON, retried then raised
            last = e
            print(f"peeringdb: attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"peeringdb: unreachable after {retries} attempts: {last}")


def join(fiche, facilities):
    """Nearest facility within MAX_DIST_M, classified BIND | NAME_MISMATCH | SUFFIX_MISMATCH.
    Returns None when no facility is close enough."""
    fi_suf = suffix(fiche["name"])
    fi_brand = set(brand_tokens(fiche.get("operator"))) | set(brand_tokens(fiche["name"]))
    best = None
    for fa in facilities:
        d = haversine_m(fiche["lat"], fiche["lon"], float(fa["latitude"]), float(fa["longitude"]))
        if d > MAX_DIST_M or (best is not None and d >= best["dist_m"]):
            continue
        fa_brand = (set(brand_tokens(fa.get("name"))) | set(brand_tokens(fa.get("name_long")))
                    | set(brand_tokens(fa.get("aka"))))
        fa_suf = suffix(fa.get("name")) | suffix(fa.get("name_long"))
        best = {
            "fac": fa,
            "dist_m": d,
            "name_ok": bool(fi_brand & fa_brand),
            "suffix_ok": (not fi_suf and not fa_suf) or bool(fi_suf & fa_suf),
        }
    if best is None:
        return None
    fa = best["fac"]
    kind = ("BIND" if best["name_ok"] and best["suffix_ok"]
            else "NAME_MISMATCH" if not best["name_ok"] else "SUFFIX_MISMATCH")
    return {
        "kind": kind,
        "fac_id": fa["id"],
        "fac_name": fa.get("name"),
        "dist_m": round(best["dist_m"]),
        "net_count": fa.get("net_count") or 0,
        "ix_count": fa.get("ix_count") or 0,
        "url": f"https://www.peeringdb.com/fac/{fa['id']}",
    }
