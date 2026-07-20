# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""home_showcase.json — who appears on the HOME, decided by rule (Franck 2026-07-20).

Putting one site on the front page is an editorial act. Left to chance it
targets somebody: the previous home demo required all 5 pillars graded — a
filter so tight that only 2 of 479 fiches passed, and the home ended up
showcasing the single hottest project in France by pure plumbing accident.
So the choice is a published RULE, computed by the engine, gated by tests:

  demo site = the most ORDINARY site of the corpus — the published site score
  closest to the corpus median. Never an extreme, neither showcase nor pillory.
  Excluded: sites not in service, fewer than MIN_PILLARS graded (the animation
  needs pillars to play), any site carrying a contestation, an operator
  response, or a watchlist entry nearby. Ties break on id → deterministic.

  wall = the corpus itself, in a deterministic grade-then-country round robin,
  so the marquee reads as Europe rather than as a shortlist. No exclusions
  here: showing 479 published fiches side by side singles out nobody.

Both lists are ordered CANDIDATES, not a final pick: satellite photos are
patched after scoring (media pipeline), so the site walks the list and takes
what has an image. Order is engine-owned; availability is infrastructure.
"""

from collections import Counter

SCHEMA_VERSION = "1.0"
MIN_PILLARS = 4          # the notation animation needs pillars to play
DEMO_CANDIDATES = 25     # enough headroom if the top ones lack a photo
WALL_CANDIDATES = 90     # the site keeps the first ~39 that carry an image
WATCH_NEAR_DEG = 0.05    # ~5 km — "a contested project next door"

_PIPELINE = ("announced", "permitting", "under_construction")


def _median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _graded_pillars(result: dict) -> int:
    return sum(1 for p in result.get("pillars", {}).values()
               if p.get("grade") not in (None, "insufficient_data"))


def _near_watchlist(dc: dict, watchlist: list[dict]) -> bool:
    coords = dc["identity"].get("coordinates") or {}
    lat, lon = coords.get("lat"), coords.get("lon")
    if lat is None or lon is None:
        return False
    for w in watchlist:
        wc = (w.get("identity") or w).get("coordinates") or {}
        wlat, wlon = wc.get("lat"), wc.get("lon")
        if wlat is None or wlon is None:
            continue
        if abs(wlat - lat) < WATCH_NEAR_DEG and abs(wlon - lon) < WATCH_NEAR_DEG:
            return True
    return False


def _is_neutral(dc: dict, result: dict, watchlist: list[dict]) -> bool:
    """Every exclusion is a reason we would NOT want this site in the window."""
    if dc["identity"].get("project_status") != "operational":
        return False
    if _graded_pillars(result) < MIN_PILLARS:
        return False
    if dc.get("contestation"):
        return False
    if (dc.get("publication") or {}).get("operator_response"):
        return False
    if _near_watchlist(dc, watchlist):
        return False
    return True


def build_showcase(datacenters: dict[str, dict], results: dict[str, dict],
                   watchlist: list[dict] | None = None) -> dict:
    watchlist = watchlist or []
    sites = [(dc_id, dc) for dc_id, dc in sorted(datacenters.items())
             if not dc_id.startswith("zz-")]
    scored = [(dc_id, dc, results[dc_id]) for dc_id, dc in sites
              if dc_id in results
              and isinstance(results[dc_id]["grades"]["site"].get("score"), (int, float))]

    median = round(_median([r["grades"]["site"]["score"] for _, _, r in scored]), 1) if scored else None

    # --- demo: the most ordinary site, exclusions first -------------------
    eligible = [(dc_id, dc, r) for dc_id, dc, r in scored if _is_neutral(dc, r, watchlist)]
    eligible.sort(key=lambda t: (abs(t[2]["grades"]["site"]["score"] - median), t[0]))
    demo = [{
        "id": dc_id,
        "score": r["grades"]["site"]["score"],
        "grade": r["grades"]["site"]["grade"],
        "delta_median": round(abs(r["grades"]["site"]["score"] - median), 2),
    } for dc_id, _, r in eligible[:DEMO_CANDIDATES]]

    # --- wall: grade-then-country round robin over the whole corpus -------
    # Round robin so the marquee alternates letters and countries instead of
    # opening on eight French C's — the eye must read "Europe", not "a list".
    buckets: dict[str, list[str]] = {}
    for dc_id, dc, r in scored:
        buckets.setdefault(r["grades"]["site"]["grade"], []).append(dc_id)
    for grade, ids in buckets.items():
        # inside a letter, alternate countries the same deterministic way
        by_country: dict[str, list[str]] = {}
        for dc_id in ids:
            by_country.setdefault(datacenters[dc_id]["identity"]["country"], []).append(dc_id)
        rotated: list[str] = []
        while any(by_country.values()):
            for country in sorted(by_country):
                if by_country[country]:
                    rotated.append(by_country[country].pop(0))
        buckets[grade] = rotated

    wall_ids: list[str] = []
    order = sorted(buckets)
    while any(buckets[g] for g in order) and len(wall_ids) < WALL_CANDIDATES:
        for grade in order:
            if buckets[grade]:
                wall_ids.append(buckets[grade].pop(0))
            if len(wall_ids) >= WALL_CANDIDATES:
                break

    statuses = Counter(dc["identity"].get("project_status") for _, dc in sites)
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "home_showcase",
        "rule": {
            "demo": "site score closest to the corpus median; excluded: not operational, "
                    f"fewer than {MIN_PILLARS} pillars graded, any contestation, an operator "
                    "response, a watchlist entry nearby; ties break on id",
            "wall": "whole corpus, grade-then-country round robin",
        },
        "median_site_score": median,
        "n_scored": len(scored),
        "n_eligible_demo": len(eligible),
        "n_pipeline": sum(statuses.get(s, 0) for s in _PIPELINE),
        "demo_candidates": demo,
        "wall_candidates": wall_ids,
    }
