# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Germany — tier-1 draft collection from coordinates alone (v0, EU-level only).

    python -m pipelines.spatial.de --lat 50.119 --lon 8.735 \
        --name "..." --operator "..." --out <newsroom>/drafts/datacenters

Germany is the real ×16: permitting, zoning, water and Seveso are all Länder-level (16 distinct
platforms). This v0 wires NO Land-specific source — it rides only EU-level collectors that work for every
country (eu.py): grid carbon from Fraunhofer energy-charts, WFD water-body status via the EEA
WISE spatial resolver + status join, Natura 2000 rings, Corine land cover, identity via
Nominatim. It puts German DCs on the map now AND proves the shared skeleton runs a brand-new
country with zero national code — the EU layer alone reaches E1+W2+F1+F2. Crucially E1 (~380
gCO2/kWh, coal-heavy grid) and the water-body status break the false-A that a land-cover-only
draft produced.

The rest are honest, documented gaps a Land adapter (Bayern, Hessen, NRW…) fills later, exactly
like Wallonia/Flanders did for BE:
  E2/E3 grid capacity/queue — no single national feed; per-TSO (50Hertz/Amprion/TenneT/TransnetBW)
  W1  drought — no national machine feed
  W3  withdrawals — per-Land
  L1  income — DESTATIS/Regionalatlas per Kreis (v1; bands are a methodology decision anyway)
  L3  Seveso — per-Land registers (no single national INSPIRE download located in recon)
"""

import json

from . import eu
from .country import build_draft, run_cli
from .http import SourceUnavailable, get_json


# DESTATIS Regionalatlas AI1601 — disposable household income per capita per Kreis (EUR), national,
# keyless. Income lives in a Postgres table joined to the boundary geometry at query time via an
# ArcGIS dynamic-layer join (host = IT.NRW DMZ). Discovered in the deep-DE recon (RECON-de-deep.md).
_REGIONALATLAS = ("https://www.gis-idmz.nrw.de/arcgis/rest/services/stba/regionalatlas/"
                  "MapServer/identify")
_RA_INCOME_JOIN = json.dumps([{"id": 101, "source": {"type": "dataLayer", "dataSource": {
    "type": "joinTable",
    "leftTableSource": {"type": "dataLayer", "dataSource": {
        "type": "table", "workspaceId": "gdb",
        "dataSourceName": "regionalatlas.verwaltungsgrenzen_gesamt"}},
    "rightTableSource": {"type": "dataLayer", "dataSource": {
        "type": "table", "workspaceId": "gdb", "dataSourceName": "regionalatlas.ai016_1"}},
    "leftTableKey": "ags", "rightTableKey": "ags2", "joinType": "leftOuterJoin"}}}])


def collect_l1_raw(lat: float, lon: float) -> dict | None:
    """Disposable household income per capita (EUR) at the point's Kreis — RAW, for provenance only.

    German income bands are a methodology decision (the value is €/inhabitant disposable income, a
    different quantity from FR Filosofi's €/consumption-unit) — so this never becomes a scored L1,
    exactly like BE/NL. It enriches the provenance sidecar with a real German income figure.
    """
    try:
        data = get_json(_REGIONALATLAS, {
            "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "sr": "4326",
            "layers": "all", "tolerance": "1",
            "mapExtent": f"{lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05}",
            "imageDisplay": "600,600,96", "returnGeometry": "false", "f": "json",
            "dynamicLayers": _RA_INCOME_JOIN})
    except SourceUnavailable:
        return None
    for res in data.get("results", []):
        a = res.get("attributes", {})
        typ = next((v for k, v in a.items() if k.lower().endswith("typ")), None)
        inc = next((v for k, v in a.items() if k.lower().endswith("ai1601")), None)
        gen = next((v for k, v in a.items() if k.lower().endswith("gen")), None)
        if str(typ) in ("3", "5") and inc not in (None, "", " "):  # 3=Landkreis, 5=kreisfreie Stadt
            try:
                value = int(str(inc).strip())
            except ValueError:
                continue
            return {
                "disposable_income_per_capita_eur": value,
                "kreis": gen,
                "definition": "verfügbares Einkommen der privaten Haushalte je Einwohner (DESTATIS "
                              "Regionalatlas AI1601, VGRdL, ref. 2022)",
                "url": "https://regionalatlas.statistikportal.de/",
                "note": "raw value only — DE income bands are a methodology decision (per-inhabitant "
                        "disposable income ≠ FR €/consumption-unit), same refusal as BE/NL",
            }
    return None


def fetch_commune(lat: float, lon: float) -> dict:
    """{name, kreis, land} via Nominatim reverse (the only backbone wired in v0)."""
    try:
        data = get_json("https://nominatim.openstreetmap.org/reverse",
                        {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10})
    except SourceUnavailable as exc:
        raise SourceUnavailable(f"backbone geocoder unreachable: {exc}") from exc
    addr = data.get("address", {})
    name = (addr.get("city") or addr.get("town") or addr.get("municipality")
            or addr.get("village") or addr.get("county"))
    return {
        "name": name,
        "kreis": addr.get("county"),
        "land": addr.get("state"),
        "land_iso": addr.get("ISO3166-2-lvl4"),
    }


_GAPS = {
    "E2": "not_collected — no single national capacity feed; per-TSO (50Hertz/Amprion/"
          "TenneT DE/TransnetBW), a per-Land/TSO adapter (v1)",
    "E3": "not_collected — no public national connection-queue feed",
    "W1": "not_collected — no national drought machine feed",
    "W3": "not_collected — abstraction volumes are per-Land",
    "L1": "not_collected — raw income in provenance (l1_raw, DESTATIS Regionalatlas AI1601); DE "
          "bands are a methodology decision, same refusal as BE/NL",
    "L3": "not_collected — Seveso registers are per-Land; only Sachsen/Hamburg publish, neither a "
          "DC state (RECON-de-deep.md). No national register (EU eSPIRS is access-restricted)",
}

DE_SPEC = {
    "iso": "DE",
    "generator": "pipelines.spatial.de v0 (EU-level only)",
    "summary": {
        "fr": "BROUILLON DE v0 (socle EU seul : Natura 2000, Corine) — adaptateurs par Land à venir. À vérifier.",
        "en": "DE DRAFT v0 (EU-level only: Natura 2000, Corine) — per-Land adapters to come. Verify before use.",
    },
    "fetch_commune": fetch_commune,
    "identity_fields": lambda c: {
        "municipality": c.get("name") or "UNKNOWN — to fill",
        **({"admin_area": c["land_iso"].removeprefix("DE-")} if c.get("land_iso") else {}),
    },
    "collectors": [
        # E1 + W2 come from EU-level sources — no Land wiring (energy-charts, EEA WISE spatial).
        (("E1",), lambda ctx, prov: [x] if (x := eu.collect_e1_energy_charts("DE", ctx["accessed"])) else []),
        (("W2",), lambda ctx, prov: [x] if (x := eu.collect_w2_universal(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F1",), lambda ctx, prov: [x] if (x := eu.natura_rings(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F2",), lambda ctx, prov: _f2(ctx, prov)),
    ],
    # Everything unfetched here is collectable by a later Land adapter — never "verified absent".
    "collectable_gaps": frozenset({"E2", "E3", "W1", "W3", "L1", "L3"}),
    "provenance_commune": lambda c: {
        "kreis": c.get("kreis"),
        "land": c.get("land"),
    },
    "provenance_extra": lambda ctx, prov: {
        "known_gaps": _GAPS,
        "l1_raw": collect_l1_raw(ctx["lat"], ctx["lon"])
                  or "unavailable (Regionalatlas AI1601 unreachable or no Kreis at point)",
        "f2_crosscheck": prov.get("f2_crosscheck"),
    },
    "manual_still_required": ["F3", "L2", "T1", "T2", "E2", "E3", "W1", "W3", "L1", "L3"],
}


def _f2(ctx, prov):
    clc_code, clc_cat = eu.corine_at_point(ctx["lat"], ctx["lon"])
    prov["f2_crosscheck"] = {"primary": None, "primary_source": None,
                             "land_cover": clc_cat, "clc_code": clc_code, "agree": None,
                             "note": "no Land legal-zoning source wired in v0"}
    if clc_cat is None:
        return []
    return [{"id": "F2", "status": "measured", "value": clc_cat,
             "source": {"title": f"Corine Land Cover 2018 (EEA) — CLC code {clc_code} at point "
                                 f"(EU-wide; no Land zoning source in v0)",
                        "url": eu.EEA_CORINE, "accessed": ctx["accessed"]}}]


def collect(lat: float, lon: float, *, name: str, operator: str, power_mw: float | None,
            project_status: str, accessed: str) -> tuple[dict, dict, list[str]]:
    """Return (schema_valid_fragment, provenance_sidecar, skipped_indicator_ids)."""
    return build_draft(DE_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv: list[str] | None = None) -> int:
    return run_cli(DE_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
