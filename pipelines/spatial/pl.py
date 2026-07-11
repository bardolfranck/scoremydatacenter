# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Poland — tier-1 draft collection from coordinates alone (v0, EU-level only).

    python -m pipelines.spatial.pl --lat 52.2930 --lon 20.9216 \
        --name "..." --operator "..." --out <newsroom>/drafts/datacenters

Same posture as DE v0: no national source wired, only the EU-level collectors that work for every
member state (eu.py) — grid carbon from Fraunhofer energy-charts, WFD water-body status via the
EEA WISE spatial resolver + status join, Natura 2000 rings, Corine land cover, identity via
Nominatim. Reaches E1+W2+F1+F2 with zero Polish code.

Why Poland is worth posing on this thin adapter: the editorial angle is ENERGY, and E1 carries it
for free. The Polish grid is the dirtiest in Europe (~650 gCO2/kWh, coal) while Warsaw is the
fastest-growing EU hub after FLAP-D — the AI buildout landing on Europe's dirtiest grid. E1 alone
scores it, no national wiring needed.

The rest are honest gaps a national adapter would fill later (grid capacity via PSE, drought,
income via GUS, Seveso register) — but the paying market and contestation signal are thin in CEE
(cadrage: profondeur suit la donnée, présence à coût quasi nul), so v0 stays presence + energy.
"""

from . import eu
from .country import build_draft, run_cli
from .http import SourceUnavailable, get_json


def fetch_commune(lat: float, lon: float) -> dict:
    """{name, county, voivodeship} via Nominatim reverse (the only backbone wired in v0)."""
    try:
        data = get_json("https://nominatim.openstreetmap.org/reverse",
                        {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10})
    except SourceUnavailable as exc:
        raise SourceUnavailable(f"backbone geocoder unreachable: {exc}") from exc
    addr = data.get("address", {})
    name = (addr.get("city") or addr.get("town") or addr.get("municipality")
            or addr.get("village") or addr.get("county"))
    return {"name": name, "county": addr.get("county"), "voivodeship": addr.get("state"),
            "voiv_iso": addr.get("ISO3166-2-lvl4")}


_GAPS = {
    "E2": "not_collected — grid hosting capacity is per-TSO (PSE); no single national open feed (v1)",
    "E3": "not_collected — no public national connection-queue feed",
    "W1": "not_collected — no national drought machine feed wired",
    "W3": "not_collected — abstraction volumes not wired",
    "L1": "not_collected — GUS income per powiat (v1; bands are a methodology decision anyway)",
    "L3": "not_collected — Seveso (zakłady ZDR/ZZR) register not wired (v1)",
}

PL_SPEC = {
    "iso": "PL",
    "generator": "pipelines.spatial.pl v0 (EU-level only)",
    "summary": {
        "fr": "BROUILLON PL v0 (socle EU seul : carbone réseau, masse d'eau, Natura, Corine) — angle énergie. À vérifier.",
        "en": "PL DRAFT v0 (EU-level only: grid carbon, water body, Natura, Corine) — energy angle. Verify before use.",
    },
    "fetch_commune": fetch_commune,
    "identity_fields": lambda c: {
        "municipality": c.get("name") or "UNKNOWN — to fill",
        **({"admin_area": c["voiv_iso"].removeprefix("PL-")} if c.get("voiv_iso") else {}),
    },
    "collectors": [
        (("E1",), lambda ctx, prov: [x] if (x := eu.collect_e1_energy_charts("PL", ctx["accessed"])) else []),
        (("W2",), lambda ctx, prov: [x] if (x := eu.collect_w2_universal(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F1",), lambda ctx, prov: [x] if (x := eu.natura_rings(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F2",), lambda ctx, prov: _f2(ctx, prov)),
    ],
    "collectable_gaps": frozenset({"E2", "E3", "W1", "W3", "L1", "L3"}),
    "provenance_commune": lambda c: {"county": c.get("county"), "voivodeship": c.get("voivodeship")},
    "provenance_extra": lambda ctx, prov: {"known_gaps": _GAPS, "f2_crosscheck": prov.get("f2_crosscheck")},
    "manual_still_required": ["F3", "L2", "T1", "T2", "E2", "E3", "W1", "W3", "L1", "L3"],
}


def _f2(ctx, prov):
    clc_code, clc_cat = eu.corine_at_point(ctx["lat"], ctx["lon"])
    prov["f2_crosscheck"] = {"primary": None, "primary_source": None,
                             "land_cover": clc_cat, "clc_code": clc_code, "agree": None,
                             "note": "no national legal-zoning source wired in v0"}
    if clc_cat is None:
        return []
    return [{"id": "F2", "status": "measured", "value": clc_cat,
             "source": {"title": f"Corine Land Cover 2018 (EEA) — CLC code {clc_code} at point "
                                 f"(EU-wide; no national zoning source in v0)",
                        "url": eu.EEA_CORINE, "accessed": ctx["accessed"]}}]


def collect(lat: float, lon: float, *, name: str, operator: str, power_mw: float | None,
            project_status: str, accessed: str) -> tuple[dict, dict, list[str]]:
    """Return (schema_valid_fragment, provenance_sidecar, skipped_indicator_ids)."""
    return build_draft(PL_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv: list[str] | None = None) -> int:
    return run_cli(PL_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
