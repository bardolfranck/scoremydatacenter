# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Great Britain — tier-1 draft collection from coordinates alone (v0).

    python -m pipelines.spatial.gb --lat 51.4139 --lon -0.7821 \
        --name "..." --operator "..." --out <newsroom>/drafts/datacenters

The Brexit finding, in data terms: the UK left the EU data commons, so the free EU-level bricks
partially fail here (probed 2026-07-12):
  * W2 — EEA WISE has ZERO GB water bodies for the 2022 WFD cycle (UK reports nationally now). Gap.
  * F1 — RECOVERED via Natural England/JNCC national layers (SAC England + UK SPA), the
    post-Brexit replacement for the EU-only EEA Natura. Scotland/Wales SAC = v1 gap.
  * F2 — Corine CLC2018 was produced while the UK was a member → it DOES cover GB. Works.
  * E1 — energy-charts rejects `gb`; instead GB has an excellent national feed: National Grid ESO
    carbonintensity.org.uk (keyless). Works — and GB's grid is comparatively clean (~106 gCO2/kWh,
    wind + gas), the opposite end from Poland.

So GB now = E1 (National Grid) + W1 (Aqueduct) + F1 (Natural England) + F2 (Corine) = 4/12. Unlike a fresh EU member, a deeper UK
adapter is a NATIONAL build (Environment Agency / SEPA / NRW catchment data for W2, JNCC for F1,
NGED/UKPN capacity, HSE COMAH for Seveso) — Brexit turned the free EU ride into national wiring,
like Germany's Länder but for a whole country. That is itself the strategic point.
"""

from . import eu
from .bands import F1_BEYOND_RINGS, F1_DISTANCE_RINGS
from .country import build_draft, run_cli
from .geo import arcgis_point_query
from .http import SourceUnavailable, get_json

# Natural England / JNCC Open Data (ArcGIS) — the national protected-areas layers that replace the
# Brexit-lost EEA Natura 2000. SAC polygons (England) + UK-wide SPAs; probed live 2026-07-12.
_NE = "https://services.arcgis.com/JJzESW51TqeY9uat/arcgis/rest/services"
_UK_PROTECTED = [(f"{_NE}/AnnexI_Polygons_NE_SAC_v2/FeatureServer", 0, "SAC (England)"),
                 (f"{_NE}/c20220316_UKSPAswithMarineComponents_WGS84/FeatureServer", 0, "SPA (UK)")]


def collect_f1_uk(lat: float, lon: float, accessed: str) -> dict | None:
    """F1 protected-area proximity via Natural England/JNCC (SAC + SPA) — recovers the indicator
    Brexit removed from the EEA Natura layer. England SAC + UK SPA; Scotland/Wales SAC = v1 gap."""
    reachable = False
    for radius, category in F1_DISTANCE_RINGS:
        for service, layer, _ in _UK_PROTECTED:
            try:
                feats = arcgis_point_query(service, layer, lat, lon, max(radius, 1), record_count=1)
            except SourceUnavailable:
                continue
            reachable = True
            if feats:
                return {"id": "F1", "status": "measured", "value": category,
                        "source": {"title": "Natural England / JNCC — SAC (England) + UK SPA "
                                            "protected-areas overlap by distance ring (post-Brexit "
                                            "national layers, EEA Natura is EU-only)",
                                   "url": "https://naturalengland-defra.opendata.arcgis.com/",
                                   "accessed": accessed}}
    if not reachable:
        return None
    return {"id": "F1", "status": "measured", "value": F1_BEYOND_RINGS,
            "source": {"title": "Natural England / JNCC — no SAC/SPA within 5 km (post-Brexit "
                               "national layers)",
                       "url": "https://naturalengland-defra.opendata.arcgis.com/", "accessed": accessed}}


def fetch_commune(lat: float, lon: float) -> dict:
    try:
        data = get_json("https://nominatim.openstreetmap.org/reverse",
                        {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10})
    except SourceUnavailable as exc:
        raise SourceUnavailable(f"backbone geocoder unreachable: {exc}") from exc
    addr = data.get("address", {})
    name = (addr.get("city") or addr.get("town") or addr.get("municipality")
            or addr.get("village") or addr.get("county"))
    return {"name": name, "county": addr.get("county"), "country_part": addr.get("ISO3166-2-lvl4")}


# --- E1 · GB grid carbon (National Grid ESO — carbonintensity.org.uk, national, keyless) --------

def collect_e1_gb(accessed: str) -> dict | None:
    """A 2-week mean of GB half-hourly carbon intensity (the API caps date ranges; a fortnight is
    a stable, representative window). National — GB has one balancing area."""
    end = accessed
    y, m, d = int(accessed[:4]), int(accessed[5:7]), int(accessed[8:10])
    start = f"{y:04d}-{m:02d}-01"  # ~2-4 weeks back within the same month floor; simple + range-safe
    try:
        data = get_json(f"https://api.carbonintensity.org.uk/intensity/{start}T00:00Z/{end}T00:00Z")
    except SourceUnavailable:
        return None
    vals = [row["intensity"]["actual"] for row in data.get("data", [])
            if row.get("intensity", {}).get("actual") is not None]
    if not vals:
        return None
    mean = round(sum(vals) / len(vals), 1)
    return {
        "id": "E1", "status": "measured", "value": mean,
        "source": {
            "title": f"National Grid ESO carbonintensity.org.uk — GB grid carbon intensity, "
                     f"mean {start}..{end} ({mean} gCO2/kWh, n={len(vals)} half-hourly)",
            "url": "https://carbonintensity.org.uk/", "accessed": accessed},
    }


_GAPS = {
    "W2": "not_collected — BREXIT: EEA WISE has no GB water bodies for the 2022 WFD cycle; the "
          "national source is Environment Agency / SEPA / NRW catchment data (v1)",
    "E2": "not_collected — grid capacity is per-DNO (NGED/UKPN/SSEN); no single national feed (v1)",
    "E3": "not_collected — no public national connection-queue feed wired",
    "W3": "not_collected — abstraction volumes not wired",
    "L1": "not_collected — BREXIT: the common Eurostat NUTS2 income brick has NO UK data (UK left "
          "EU regional statistics; find-nuts only resolves UK on pre-2021 vintages). ONS income "
          "per LAD is the national source (v1); bands are a methodology decision anyway",
    "L3": "not_collected — HSE COMAH (Seveso) establishments register not wired (v1)",
}

GB_SPEC = {
    "iso": "GB",
    "generator": "pipelines.spatial.gb v0 (national E1 + EU Corine; Brexit-limited)",
    "summary": {
        "fr": "BROUILLON GB v0 — post-Brexit : carbone réseau national (National Grid) + Corine. Natura/WISE tombés avec le Brexit. À vérifier.",
        "en": "GB DRAFT v0 — post-Brexit: national grid carbon (National Grid) + Corine. Natura/WISE lost to Brexit. Verify before use.",
    },
    "fetch_commune": fetch_commune,
    "identity_fields": lambda c: {
        "municipality": c.get("name") or "UNKNOWN — to fill",
        **({"admin_area": c["country_part"].removeprefix("GB-")} if c.get("country_part") else {}),
    },
    "collectors": [
        (("W1",), lambda ctx, prov: [x] if (x := eu.collect_w1_aqueduct(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("E1",), lambda ctx, prov: [x] if (x := collect_e1_gb(ctx["accessed"])) else []),
        (("F1",), lambda ctx, prov: [x] if (x := collect_f1_uk(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F2",), lambda ctx, prov: _f2(ctx, prov)),
    ],
    "collectable_gaps": frozenset({"W2", "E2", "E3", "W3", "L1", "L3"}),
    "provenance_commune": lambda c: {"county": c.get("county"), "country_part": c.get("country_part")},
    "provenance_extra": lambda ctx, prov: {"known_gaps": _GAPS, "f2_crosscheck": prov.get("f2_crosscheck")},
    "manual_still_required": ["F3", "L2", "T1", "T2", "W2", "E2", "E3", "W3", "L1", "L3"],
}


def _f2(ctx, prov):
    clc_code, clc_cat = eu.corine_at_point(ctx["lat"], ctx["lon"])
    prov["f2_crosscheck"] = {"primary": None, "primary_source": None,
                             "land_cover": clc_cat, "clc_code": clc_code, "agree": None,
                             "note": "Corine CLC2018 predates Brexit → still covers GB; no national zoning wired"}
    if clc_cat is None:
        return []
    return [{"id": "F2", "status": "measured", "value": clc_cat,
             "source": {"title": f"Corine Land Cover 2018 (EEA) — CLC code {clc_code} at point "
                                 f"(CLC2018 predates Brexit, covers GB; no national zoning in v0)",
                        "url": eu.EEA_CORINE, "accessed": ctx["accessed"]}}]


def collect(lat: float, lon: float, *, name: str, operator: str, power_mw: float | None,
            project_status: str, accessed: str) -> tuple[dict, dict, list[str]]:
    """Return (schema_valid_fragment, provenance_sidecar, skipped_indicator_ids)."""
    return build_draft(GB_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv: list[str] | None = None) -> int:
    return run_cli(GB_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
