# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Netherlands — tier-1 draft collection from coordinates alone (national spec).

    python -m pipelines.spatial.nl --lat 52.7774 --lon 5.0303 \
        --name "..." --operator "..." --out <newsroom>/drafts/datacenters

Remarkably centralized: one keyless backbone (PDOK Locatieserver — returns gemeente, province
AND waterschap in one call) and one keyless ArcGIS feed for the whole grid picture — the
Netbeheer Nederland capaciteitskaart merges every DSO plus TenneT, giving E2 (offtake capacity
class) and E3 (queue MW + congestion-resolution year) from a single source. This is the
Caparéseau slot, richer.

Documented gaps (recon 2026-07-11): E1 needs a key (NED.nl / ENTSO-E) → not_collected; W1
drought status (LCW) is prose → not_collected; W3 abstraction volumes are fragmented per
province/waterschap → not_collected; F2 legal zoning (ruimtelijke plannen API) is keyed → Corine
fallback; L1 exists cleanly at CBS StatLine (median disposable income per gemeente) but per
HOUSEHOLD, not per consumption unit → raw to provenance, NL bands pending (same refusal as BE).
"""

from . import eu
from .bands import e2_category, l3_value  # noqa: F401 (e2_category: FR/BE bands are MW-based — see _E2_AFNAME)
from .country import build_draft, run_cli
from .geo import arcgis_point_query, min_vertex_km, wfs_bbox_geojson
from .http import SourceUnavailable, get_json

LOCATIESERVER = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/reverse"
CAPACITEIT_DSO = ("https://services.arcgis.com/nSZVuSZjHpEZZbRo/arcgis/rest/services/"
                  "Capaciteitskaart_elektriciteitsnet_v2_afname/FeatureServer")
KRW_WMS = "https://service.pdok.nl/ihw/krw-oppervlaktewaterlichamen-geharmoniseerd/wms/v1_0"
SEVESO_WFS = ("https://service.pdok.nl/rws/faciliteiten-voor-productie-en-industrie/"
              "productie-installaties/wfs/v1_0")
CBS_ODATA = "https://opendata.cbs.nl/ODataApi/odata/86161NED/TypedDataSet"


def _source(title: str, url: str, accessed: str) -> dict:
    return {"title": title, "url": url, "accessed": accessed}


# --- identity backbone (PDOK Locatieserver) ----------------------------------------------------

def fetch_commune(lat: float, lon: float) -> dict:
    try:
        data = get_json(LOCATIESERVER, {"lat": lat, "lon": lon, "fl": "*", "rows": 1,
                                        "type": "gemeente"})
    except SourceUnavailable as exc:
        raise SourceUnavailable(f"backbone geocoder unreachable: {exc}") from exc
    docs = (data.get("response") or {}).get("docs") or []
    if not docs:
        raise SourceUnavailable("PDOK Locatieserver returned no gemeente (outside NL?)")
    d = docs[0]
    return {
        "name": d.get("gemeentenaam"),
        "gemeente_code": d.get("gemeentecode"),          # '1911' → StatLine 'GM1911'
        "province": d.get("provincienaam"),
        "waterschap": d.get("waterschapsnaam"),
    }


# --- E2 + E3 · grid capacity and congestion (Netbeheer Nederland capaciteitskaart) -------------

# The feed publishes an offtake-availability CLASS, not MW (afname 1..3 observed; legend:
# beschikbaar / beperkt / congestie-onderzoek-of-tekort). PROVISIONAL mapping onto the shared
# E2 bands; the raw class + queue figures ride in the source title for the reviewer.
_E2_AFNAME = {1: "adequate", 2: "constrained", 3: "saturated"}


def collect_grid(lat: float, lon: float, accessed: str) -> list[dict]:
    try:
        feats = arcgis_point_query(CAPACITEIT_DSO, 0, lat, lon, 1)
    except SourceUnavailable:
        return []
    if not feats:
        return []
    a = feats[0]["attributes"]
    afname = a.get("afname")
    area, dso = a.get("voedingsgebied_naam"), a.get("RNB")
    queue = a.get("wachtrij_afname")
    out = []
    e2 = _E2_AFNAME.get(int(afname)) if afname is not None else None
    if e2:
        out.append({
            "id": "E2", "status": "measured", "value": e2,
            "source": _source(
                f"Netbeheer Nederland capaciteitskaart (offtake) — {dso} area '{area}': "
                f"availability class {afname}/3 (1=available, 3=congested/shortage), "
                f"queue {queue}. Provisional class mapping",
                "https://capaciteitskaart.netbeheernederland.nl/", accessed),
        })
        # E3 from the same reading: congested class with a live queue = the congestion signal.
        e3 = {1: "low", 2: "moderate", 3: "high"}[int(afname)]
        if int(afname) == 3 and queue:
            e3 = "critical"
        out.append({
            "id": "E3", "status": "measured", "value": e3,
            "source": _source(
                f"Netbeheer Nederland capaciteitskaart (offtake) — {dso} area '{area}': "
                f"availability class {afname}/3, offtake queue {queue}. Provisional mapping "
                f"from class+queue (NL publishes congestion state, not a fill-rate %)",
                "https://capaciteitskaart.netbeheernederland.nl/", accessed),
        })
    return out


# --- W2 · water body (PDOK KRW WMS GetFeatureInfo → EEA WISE) ----------------------------------

def collect_w2(lat: float, lon: float, accessed: str) -> dict | None:
    # No WFS exists for the harmonized KRW layer; WMS GetFeatureInfo in JSON is the point probe.
    bbox = f"{lon-0.02},{lat-0.02},{lon+0.02},{lat+0.02}"
    try:
        data = get_json(KRW_WMS, {
            "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
            "LAYERS": "krw_oppervlaktewaterlichamen", "QUERY_LAYERS": "krw_oppervlaktewaterlichamen",
            "CRS": "CRS:84", "BBOX": bbox, "WIDTH": 101, "HEIGHT": 101, "I": 50, "J": 50,
            "INFO_FORMAT": "application/json", "FEATURE_COUNT": 5,
        })
    except SourceUnavailable:
        return None
    feats = data.get("features") or []
    if not feats:
        return None
    p = feats[0].get("properties", {})
    code = p.get("inspireIdLocalId") or p.get("owmident")
    name = p.get("naam") or p.get("owmnaam")
    if not code:
        return None
    status, category = eu.wise_status_category(code, "NL")
    if category is None:
        return None
    return {
        "id": "W2", "status": "measured", "value": category,
        "source": _source(
            f"PDOK KRW oppervlaktewaterlichamen (water body {code} '{name}' at point) + "
            f"EEA WISE WFD — ecological status class {status}/5",
            "https://discodata.eea.europa.eu/", accessed),
    }


# --- F2 · soil status (Corine only in v0 — ruimtelijke plannen API is keyed) -------------------

def collect_f2(lat: float, lon: float, accessed: str) -> tuple[dict | None, dict]:
    clc_code, clc_cat = eu.corine_at_point(lat, lon)
    crosscheck = {"primary": None, "primary_source": None,
                  "land_cover": clc_cat, "clc_code": clc_code, "agree": None,
                  "note": "legal zoning (ruimtelijke plannen API) is key-gated — v1 backlog"}
    if clc_cat is None:
        return None, crosscheck
    return {"id": "F2", "status": "measured", "value": clc_cat,
            "source": _source(
                f"Corine Land Cover 2018 (EEA) — CLC code {clc_code} at point (EU-wide "
                f"fallback; NL legal zoning API is key-gated, no cross-check)",
                eu.EEA_CORINE, accessed)}, crosscheck


# --- L3 · Seveso (PDOK INSPIRE production installations — tier not published) ------------------

def collect_l3(lat: float, lon: float, accessed: str) -> dict | None:
    try:
        feats = wfs_bbox_geojson(
            SEVESO_WFS, "productie-installaties:production_installation_point", lat, lon, 5000)
    except SourceUnavailable:
        return None
    sites = []
    for f in feats:
        geom = f.get("geometry")
        if not geom:
            continue
        d = min_vertex_km(lat, lon, geom.get("coordinates"))
        if d is not None and d <= 5.0:
            sites.append({"upper_tier": None, "dist_km": round(d, 2)})
    value = l3_value(sites)
    if value is None:  # unknown-tier site inside 2 km — never guess a hazard class
        return None
    detail = (", ".join(f"installation at {s['dist_km']} km"
                        for s in sorted(sites, key=lambda s: s["dist_km"])[:3])
              or "no Seveso installation within 5 km")
    return {"id": "L3", "status": "measured", "value": value,
            "source": _source(
                f"PDOK INSPIRE Seveso production installations — {detail}; tier not published "
                f"in the INSPIRE export (band safe: no installation within 2 km)",
                "https://service.pdok.nl/rws/faciliteiten-voor-productie-en-industrie/productie-installaties/wfs/v1_0",
                accessed)}


# --- L1 · income — RAW ONLY (provenance): CBS median is per household, not per UC --------------

def collect_l1_raw(gemeente_code: str | None) -> dict | None:
    if not gemeente_code:
        return None
    try:
        data = get_json(CBS_ODATA, {
            "$filter": f"RegioS eq 'GM{gemeente_code}' and Perioden eq '2024JJ00' "
                       f"and Populatie eq '1050010' and KenmerkenVanHuishoudens eq '1050010'",
            "$select": "RegioS,MediaanGestandaardiseerdInkomen_4,MediaanBesteedbaarInkomen_6",
        })
    except SourceUnavailable:
        return None
    rows = data.get("value") or []
    if not rows:
        return None
    r = rows[0]
    return {
        "median_disposable_income_household_keur": r.get("MediaanBesteedbaarInkomen_6"),
        "median_standardized_income_keur": r.get("MediaanGestandaardiseerdInkomen_4"),
        "definition": "CBS StatLine 86161NED, all private households, 2024 (k€/year)",
        "url": "https://opendata.cbs.nl/statline/#/CBS/nl/dataset/86161NED",
        "note": "raw value only — FR Filosofi bands are €/consumption-unit, NL bands pending "
                "methodology (the standardized median is the closest concept)",
    }


# --- the spec ----------------------------------------------------------------------------------

_GAPS = {
    "W1": "not_collected — LCW/droogtemonitor status is prose (v1: KNMI neerslagtekort proxy, "
          "keyed)",
    "W3": "not_collected — abstraction volumes fragmented per province/waterschap, no open feed",
    "L1": "not_collected — raw CBS value in provenance (l1_raw); per-household median ≠ FR "
          "€/consumption-unit bands, NL bands pending methodology",
}

NL_SPEC = {
    "iso": "NL",
    "generator": "pipelines.spatial.nl v1",
    "summary": {
        "fr": "BROUILLON pré-rempli par le pipeline spatial NL — à vérifier avant tout usage.",
        "en": "DRAFT pre-filled by the NL spatial pipeline — verify before any use.",
    },
    "fetch_commune": fetch_commune,
    "identity_fields": lambda c: {"municipality": c.get("name") or "UNKNOWN — to fill"},
    "collectors": [
        (("E1",), lambda ctx, prov: [x] if (x := eu.collect_e1_energy_charts("NL", ctx["accessed"])) else []),
        # National KRW WMS first; EEA WISE universal resolver as fallback (polder plots often miss).
        (("W2",), lambda ctx, prov: [x] if (x := (collect_w2(ctx["lat"], ctx["lon"], ctx["accessed"])
                  or eu.collect_w2_universal(ctx["lat"], ctx["lon"], ctx["accessed"]))) else []),
        (("F1",), lambda ctx, prov: [x] if (x := eu.natura_rings(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F2",), lambda ctx, prov: _f2(ctx, prov)),
        (("L3",), lambda ctx, prov: [x] if (x := collect_l3(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("E2", "E3"), lambda ctx, prov: collect_grid(ctx["lat"], ctx["lon"], ctx["accessed"])),
    ],
    "collectable_gaps": frozenset({"W1", "W3", "L1"}),
    "provenance_commune": lambda c: {
        "gemeente_code": c.get("gemeente_code"),
        "province": c.get("province"),
        "waterschap": c.get("waterschap"),
    },
    "provenance_extra": lambda ctx, prov: {
        "known_gaps": _GAPS,
        "l1_raw": collect_l1_raw(ctx["commune"].get("gemeente_code"))
                  or "unavailable (no gemeente code or StatLine unreachable)",
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
    return build_draft(NL_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv: list[str] | None = None) -> int:
    return run_cli(NL_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
