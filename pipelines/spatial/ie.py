# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Ireland — national spec. The Irish story IS the grid: Dublin's data-center connection moratorium.

    python -m pipelines.spatial.ie --lat 53.3136 --lon -6.4474 \
        --name "..." --operator "..." --out <newsroom>/drafts/datacenters

EU-level bricks fill W1/W2/F1/F2. The two national wins are the grid — exactly what makes Ireland
Ireland:
  * E1 — Fraunhofer energy-charts does NOT serve the Irish synchronous zone (HTTP 500), so we use
    EirGrid's own Smart Grid Dashboard CO2-intensity feed (ROI, keyless JSON).
  * E2/E3 — the decisional indicator. Since 2021 the CRU/EirGrid have constrained new data-center
    grid connections in the **Dublin region** (CRU/21/124 & successors) — a de-facto moratorium
    because the Greater Dublin grid is saturated. That is a real, sourced, zonal capacity signal:
    a DC in County Dublin faces a closed/critical connection queue; elsewhere in Ireland we hold no
    per-substation feed (honest not_collected). This is the moratorium, in the score.
"""

from datetime import date, timedelta

from . import eu
from .country import build_draft, run_cli
from .http import SourceUnavailable, get_json

_EIRGRID = "https://www.smartgriddashboard.com/DashboardService.svc/data"
# CRU/EirGrid Dublin-region data-center connection moratorium — the administrative counties of the
# Greater Dublin grid-constrained area (Nominatim returns "County Dublin" for all four at zoom 10).
_DUBLIN_COUNTIES = {"county dublin", "county fingal", "county south dublin",
                    "dún laoghaire–rathdown", "county dún laoghaire-rathdown"}


def fetch_commune(lat: float, lon: float) -> dict:
    try:
        data = get_json("https://nominatim.openstreetmap.org/reverse",
                        {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10})
    except SourceUnavailable as exc:
        raise SourceUnavailable(f"backbone geocoder unreachable: {exc}") from exc
    addr = data.get("address", {})
    name = (addr.get("city") or addr.get("town") or addr.get("municipality")
            or addr.get("suburb") or addr.get("county"))
    return {"name": name, "county": addr.get("county"), "county_iso": addr.get("ISO3166-2-lvl4")}


_e1_cache: dict[str, dict | None] = {}


def collect_e1_eirgrid(accessed: str) -> dict | None:
    """ROI grid CO2 intensity — mean of a recent ~7-day window from EirGrid's Smart Grid Dashboard
    (the API caps date ranges; a week is stable and keyless). National → memoized per run, both to
    avoid re-fetching for every Irish DC and to smooth the dashboard's intermittent 503s."""
    if accessed in _e1_cache:
        return _e1_cache[accessed]
    end = date.fromisoformat(accessed)
    start = end - timedelta(days=7)
    try:
        data = get_json(_EIRGRID, {"area": "co2intensity", "region": "ROI",
                                   "datefrom": f"{start} 00:00", "dateto": f"{end} 00:00"})
    except SourceUnavailable:
        return None  # transient — not cached, a later DC retries
    vals = [r.get("Value") for r in data.get("Rows", []) if r.get("Value") is not None]
    if not vals:
        return None
    mean = round(sum(vals) / len(vals), 1)
    result = {
        "id": "E1", "status": "measured", "value": mean,
        "source": {
            "title": f"EirGrid Smart Grid Dashboard — ROI grid CO2 intensity, mean {start}..{end} "
                     f"({mean} gCO2/kWh, n={len(vals)} half-hourly). energy-charts does not serve the Irish zone",
            "url": "https://www.smartgriddashboard.com/", "accessed": accessed},
    }
    _e1_cache[accessed] = result
    return result


def collect_grid_dublin_moratorium(county: str | None, accessed: str) -> list[dict]:
    """E2/E3 from the Dublin data-center connection moratorium. A DC in the Greater Dublin grid area
    faces a constrained/closed connection queue (CRU/EirGrid) — saturated capacity, critical queue.
    Outside the policy zone we hold no per-substation feed → not_collected (padded by the skeleton)."""
    if not county or county.strip().lower() not in _DUBLIN_COUNTIES:
        return []
    src = {
        "title": "CRU/EirGrid Dublin-region data-centre grid-connection moratorium (CRU/21/124 & "
                 "successors) — the Greater Dublin grid is constrained; new DC connections are "
                 "restricted/withheld. Zonal capacity signal from the published policy",
        "url": "https://www.cru.ie/publications/", "accessed": accessed}
    return [
        {"id": "E2", "status": "measured", "value": "saturated", "source": src},
        {"id": "E3", "status": "measured", "value": "critical", "source": src},
    ]


_GAPS = {
    "W3": "not_collected — abstraction volumes not wired",
    "L1": "not_collected — CSO income per county (v1; bands are a methodology decision anyway)",
    "L3": "not_collected — Seveso (COMAH) establishments register not wired (v1)",
}

IE_SPEC = {
    "iso": "IE",
    "generator": "pipelines.spatial.ie v1 (national grid: EirGrid + Dublin moratorium)",
    "summary": {
        "fr": "BROUILLON IE — le réseau EST l'histoire : carbone EirGrid + moratoire de raccordement de Dublin (E2/E3). À vérifier.",
        "en": "IE DRAFT — the grid IS the story: EirGrid carbon + Dublin connection moratorium (E2/E3). Verify before use.",
    },
    "fetch_commune": fetch_commune,
    "identity_fields": lambda c: {
        "municipality": c.get("name") or "UNKNOWN — to fill",
        **({"admin_area": c["county_iso"].split("-", 1)[1]} if c.get("county_iso") and "-" in c["county_iso"] else {}),
    },
    "collectors": [
        (("E1",), lambda ctx, prov: [x] if (x := collect_e1_eirgrid(ctx["accessed"])) else []),
        (("W1",), lambda ctx, prov: [x] if (x := eu.collect_w1_aqueduct(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("W2",), lambda ctx, prov: [x] if (x := eu.collect_w2_universal(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F1",), lambda ctx, prov: [x] if (x := eu.natura_rings(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F2",), lambda ctx, prov: _f2(ctx, prov)),
        (("E2", "E3"), lambda ctx, prov: collect_grid_dublin_moratorium(ctx["commune"].get("county"), ctx["accessed"])),
    ],
    "collectable_gaps": frozenset({"E2", "E3", "W3", "L1", "L3"}),
    "provenance_commune": lambda c: {"county": c.get("county")},
    "provenance_extra": lambda ctx, prov: {"known_gaps": _GAPS, "f2_crosscheck": prov.get("f2_crosscheck")},
    "manual_still_required": ["F3", "L2", "T1", "T2", "W3", "L1", "L3"],
}


def _f2(ctx, prov):
    clc_code, clc_cat = eu.corine_at_point(ctx["lat"], ctx["lon"])
    prov["f2_crosscheck"] = {"primary": None, "primary_source": None,
                             "land_cover": clc_cat, "clc_code": clc_code, "agree": None,
                             "note": "no national legal-zoning source wired"}
    if clc_cat is None:
        return []
    return [{"id": "F2", "status": "measured", "value": clc_cat,
             "source": {"title": f"Corine Land Cover 2018 (EEA) — CLC code {clc_code} at point",
                        "url": eu.EEA_CORINE, "accessed": ctx["accessed"]}}]


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    return build_draft(IE_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(IE_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
