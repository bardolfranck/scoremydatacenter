# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Luxembourg — tier-1 draft collection from coordinates alone (national spec).

    python -m pipelines.spatial.lu --lat 49.783 --lon 6.083 \
        --name "..." --operator "..." --out <newsroom>/drafts/datacenters

The cheapest country yet: one keyless national endpoint family (features.geoportail.lu, OGC API
Features) serves W2, F2 and the national protected-area layers; Seveso is one INSPIRE GML
download in the pan-EU 3035 grid. No sub-national tier — the commune is the only unit.

Documented gaps (recon 2026-07-11): E1 has no keyless national feed (LU sits in the DE-LU
bidding zone, ENTSO-E is token-gated) → not_collected; E2/E3 have NO public Creos capacity or
queue data → missing; W1 drought status is press-release prose → not_collected; W3 abstraction
points carry no volumes → not_collected; L1 raw disposable income comes from the common Eurostat
NUTS2 brick (l1_raw in provenance, LU00 — LUSTAT commune salaries are not disposable income),
bands are a methodology decision → still not_collected as a scored indicator.
"""

import re

from . import eu
from .bands import l3_value
from .cache import cached_path
from .country import build_draft, run_cli
from .geo import laea3035, ogcapi_items
from .http import SourceUnavailable, get_json

FEATURES = "https://features.geoportail.lu"
PAG_COLLECTION = "698/28"          # Plan d'aménagement général (Zonage), all communes
WATER_BODIES_COLLECTION = "2090"   # Masses d'eau de surface 2021 (OWK_2021 → WISE LU<code>)
SEVESO_GML_URL = ("https://download.data.public.lu/resources/"
                  "seveso-iii-directive-seveso-installations/20260612-122729/"
                  "pf.productionfacility-seveso.gml")


def _source(title: str, url: str, accessed: str) -> dict:
    return {"title": title, "url": url, "accessed": accessed}


# --- identity backbone (ACT reverse geocoder) --------------------------------------------------

def fetch_commune(lat: float, lon: float) -> dict:
    try:
        data = get_json("https://apiv4.geoportail.lu/geocode/reverse", {"lat": lat, "lon": lon})
    except SourceUnavailable as exc:
        raise SourceUnavailable(f"backbone geocoder unreachable: {exc}") from exc
    results = data.get("results") or [data] if isinstance(data, dict) else data
    first = results[0] if isinstance(results, list) and results else {}
    addr = first.get("AddressDetails") or first
    name = (addr.get("commune") or first.get("commune")
            or (first.get("address") or {}).get("commune"))
    postal = addr.get("postal_code") or first.get("postal_code")
    return {"name": name, "postal_code": postal}


# --- W2 · water body (national layer → EEA WISE, code prefix 'LU') -----------------------------

def collect_w2(lat: float, lon: float, accessed: str) -> dict | None:
    try:
        feats = ogcapi_items(FEATURES, WATER_BODIES_COLLECTION, lat, lon, 300)
    except SourceUnavailable:
        return None
    if not feats:
        return None
    p = feats[0].get("properties", {})
    code, name = p.get("OWK_2021"), p.get("Name_2021")
    if not code:
        return None
    status, category = eu.wise_status_category(f"LU{code}", "LU")
    if category is None:
        return None
    return {
        "id": "W2", "status": "measured", "value": category,
        "source": _source(
            f"geoportail.lu masses d'eau 2021 (water body LU{code} '{name}' at point) + "
            f"EEA WISE WFD — ecological status class {status}/5",
            "https://discodata.eea.europa.eu/", accessed),
    }


# --- F2 · soil status (PAG national harmonized zoning; Corine cross-check) ---------------------

def _pag_to_category(categorie: str) -> str | None:
    """Harmonized PAG zoning category → methodology soil category (PROVISIONAL mapping)."""
    c = (categorie or "").upper()
    if c.startswith("ZAD"):                       # zone d'aménagement différé
        return "transitional"
    if c.startswith("AGR"):
        return "agricultural"
    if c.startswith(("FOR", "VERD", "PN", "PAYS")):
        return "natural_or_enaf"
    if c.startswith(("HAB", "MIX", "ECO", "SPEC", "SP", "GARE", "BEP", "REC", "AER")):
        return "artificialized"
    return None


def collect_f2(lat: float, lon: float, accessed: str) -> tuple[dict | None, dict]:
    primary, primary_src = None, None
    try:
        feats = ogcapi_items(FEATURES, PAG_COLLECTION, lat, lon, 40)
        if feats:
            cat = feats[0].get("properties", {}).get("categorie")
            primary = _pag_to_category(cat)
            primary_src = f"PAG zoning category '{cat}'"
    except SourceUnavailable:
        pass
    clc_code, clc_cat = eu.corine_at_point(lat, lon)
    crosscheck = {
        "primary": primary, "primary_source": primary_src,
        "land_cover": clc_cat, "clc_code": clc_code,
        "agree": (primary == clc_cat) if primary and clc_cat else None,
    }
    value = primary or clc_cat
    if value is None:
        return None, crosscheck
    if primary:
        title = (f"geoportail.lu PAG national zoning — {primary_src}; "
                 f"Corine cross-check: {clc_cat or 'unavailable'}")
        url = f"{FEATURES}/collections/698%2F28"
    else:
        title = (f"Corine Land Cover 2018 (EEA) — CLC code {clc_code} at point "
                 f"(EU-wide fallback; PAG silent at point, no cross-check)")
        url = eu.EEA_CORINE
    return {"id": "F2", "status": "measured", "value": value,
            "source": _source(title, url, accessed)}, crosscheck


# --- L3 · Seveso (INSPIRE GML download, EPSG:3035, tier not published) -------------------------

def _seveso_sites_km(lat: float, lon: float) -> list[dict] | None:
    """[{upper_tier: None, dist_km}] within 5 km from the cached national INSPIRE GML."""
    try:
        path = cached_path(SEVESO_GML_URL, "lu_seveso_inspire.gml")
    except SourceUnavailable:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    px, py = laea3035(lat, lon)
    sites = []
    for block in re.findall(r"<gml:pos(?:List)?[^>]*>([\d\.\s]+)<", text):
        nums = [float(v) for v in block.split()[:2]]
        if len(nums) < 2:
            continue
        # 3035 GML axis order is (northing, easting); accept either within the EU envelope
        for x, y in ((nums[1], nums[0]), (nums[0], nums[1])):
            if 3.9e6 < x < 4.3e6 and 2.8e6 < y < 3.1e6:  # Luxembourg envelope in EPSG:3035
                d = ((x - px) ** 2 + (y - py) ** 2) ** 0.5 / 1000
                if d <= 5.0:
                    sites.append({"upper_tier": None, "dist_km": round(d, 2)})
                break
    return sites


def collect_l3(lat: float, lon: float, accessed: str) -> dict | None:
    sites = _seveso_sites_km(lat, lon)
    if sites is None:
        return None
    value = l3_value(sites)
    if value is None:  # unknown-tier site inside 2 km — never guess a hazard class
        return None
    detail = (", ".join(f"site at {s['dist_km']} km" for s in sorted(sites, key=lambda s: s["dist_km"])[:3])
              or "no Seveso site within 5 km")
    return {"id": "L3", "status": "measured", "value": value,
            "source": _source(
                f"INSPIRE Seveso III installations (data.public.lu, GML 2026-06-12) — {detail}; "
                f"tier not published in the INSPIRE export (band safe: no site within 2 km)",
                "https://data.public.lu/fr/datasets/seveso-iii-directive-seveso-installations/",
                accessed)}


# --- the spec ----------------------------------------------------------------------------------

_GAPS = {
    "E2": "missing — Creos publishes no hosting-capacity map (no Caparéseau/Elia equivalent)",
    "E3": "missing — no public connection-queue data",
    "W3": "not_collected — geoportail.lu abstraction points (collection 567) carry no volumes",
    "L1": "not_collected — raw Eurostat NUTS2 disposable income in provenance (l1_eurostat, frozen "
          "skeleton baseline); LUSTAT salaries (DF_C1600) are not disposable income, and bands are "
          "a methodology decision anyway (same refusal as BE/NL)",
}

LU_SPEC = {
    "iso": "LU",
    "generator": "pipelines.spatial.lu v1",
    "summary": {
        "fr": "BROUILLON pré-rempli par le pipeline spatial LU — à vérifier avant tout usage.",
        "en": "DRAFT pre-filled by the LU spatial pipeline — verify before any use.",
    },
    "fetch_commune": fetch_commune,
    "identity_fields": lambda c: {"municipality": c.get("name") or "UNKNOWN — to fill"},
    "collectors": [
        (("W1",), lambda ctx, prov: [x] if (x := eu.collect_w1_aqueduct(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("E1",), lambda ctx, prov: [x] if (x := eu.collect_e1_energy_charts("LU", ctx["accessed"])) else []),
        # National masses d'eau layer first; EEA WISE universal resolver as fallback.
        (("W2",), lambda ctx, prov: [x] if (x := (collect_w2(ctx["lat"], ctx["lon"], ctx["accessed"])
                  or eu.collect_w2_universal(ctx["lat"], ctx["lon"], ctx["accessed"]))) else []),
        (("F1",), lambda ctx, prov: [x] if (x := eu.natura_rings(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F2",), lambda ctx, prov: _f2(ctx, prov)),
        (("L3",), lambda ctx, prov: [x] if (x := collect_l3(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
    ],
    "collectable_gaps": frozenset({"W3", "L1"}),
    "provenance_commune": lambda c: {
        "commune_name": c.get("name"),
        "postal_code": c.get("postal_code"),
    },
    "provenance_extra": lambda ctx, prov: {
        "known_gaps": _GAPS,
        "f2_crosscheck": prov.get("f2_crosscheck"),
    },
    "manual_still_required": ["F3", "L2", "T1", "T2", "E1", "W1", "W3", "L1(bands)"],
}


def _f2(ctx, prov):
    ind, crosscheck = collect_f2(ctx["lat"], ctx["lon"], ctx["accessed"])
    prov["f2_crosscheck"] = crosscheck
    return [ind] if ind else []


def collect(lat: float, lon: float, *, name: str, operator: str, power_mw: float | None,
            project_status: str, accessed: str) -> tuple[dict, dict, list[str]]:
    """Return (schema_valid_fragment, provenance_sidecar, skipped_indicator_ids)."""
    return build_draft(LU_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv: list[str] | None = None) -> int:
    return run_cli(LU_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
