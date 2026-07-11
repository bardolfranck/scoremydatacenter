# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Value→category mappings shared by EVERY country adapter — the canonical home.

A band is methodology semantics, not source access: the same available-MW cutoffs band a
Caparéseau poste (FR) and an Elia substation (BE), the same WFD classes band a Sandre or SPW
water body. Keeping them here is what guarantees cross-country comparability — a country module
may only diverge from these bands with an explicit, documented reason. All cutoffs are
PROVISIONAL: the methodology owns final calibration.
"""

# E2 · grid connection capacity — available MW at the nearest substation → category.
def e2_category(available_mw: float) -> str:
    if available_mw >= 100:
        return "ample"
    if available_mw >= 20:
        return "adequate"
    if available_mw >= 5:
        return "constrained"
    return "saturated"


# E3 · grid congestion — reserved-capacity fill rate (%) → category.
def e3_category(fill_pct: float) -> str:
    if fill_pct < 30:
        return "low"
    if fill_pct < 70:
        return "moderate"
    if fill_pct < 100:
        return "high"
    return "critical"


# W2 · WFD ecological status class (EEA WISE, '1'..'5') → category. EU-wide by construction.
WFD_STATUS_TO_CATEGORY = {
    "1": "very_good", "2": "good", "3": "moderate", "4": "poor", "5": "bad",
}


# F1 · protected-area proximity — the distance rings every country probes, nearest first.
F1_DISTANCE_RINGS = ((0, "overlap"), (1000, "adjacent_under_1km"), (5000, "near_1_to_5km"))
F1_BEYOND_RINGS = "distant_over_5km"


# F2 · soil status — Corine Land Cover code → category. EU-wide fallback and cross-check.
def clc_to_category(code: str | None) -> str | None:
    if not code:
        return None
    if code in ("133", "324"):   # construction sites / transitional woodland-shrub
        return "transitional"
    first = code[0]
    if first == "1":
        return "artificialized"
    if first == "2":
        return "agricultural"
    if first in ("3", "4", "5"):
        return "natural_or_enaf"
    return None


# L3 · Seveso proximity — sites = [{upper_tier: bool, dist_km: float}] within 5 km → category.
def l3_value(sites: list[dict]) -> str:
    if any(s["upper_tier"] and s["dist_km"] <= 2.0 for s in sites):
        return "seveso_high_within_2km"
    if sites:
        return "seveso_low_within_5km"
    return "none_within_5km"
