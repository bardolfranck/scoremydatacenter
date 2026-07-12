# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Ireland — tier-1 draft collection from coordinates alone (v0, EU-level only).

    python -m pipelines.spatial.ie --lat 53.3136 --lon -6.4474 \
        --name "..." --operator "..." --out <newsroom>/drafts/datacenters

Ireland is a full EU member, so the EU-level collectors work out of the box — W2 (EEA WISE
universal resolver, 4327 IE water bodies), F1 (Natura 2000 rings), F2 (Corine). No national code.

E1 is the one hole: Fraunhofer energy-charts does not serve the Irish synchronous zone (probed:
HTTP 500 for `ie`), so grid carbon stays a gap until an EirGrid adapter is wired. That is a fitting
gap for Ireland — its whole story is GRID CAPACITY, not carbon: Dublin's data-center moratorium
exists because EirGrid halted new connections on a strained grid, and capacity (E2/E3) is a deep
national indicator (EirGrid/SEMO), not the EU carbon feed. v0 is presence + the contestation angle
(Grange Castle), the deep grid story is a national adapter later.
"""

from . import eu
from .country import build_draft, run_cli
from .http import SourceUnavailable, get_json


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


_GAPS = {
    "E1": "not_collected — energy-charts does not serve the Irish zone (HTTP 500); EirGrid CO2 "
          "dashboard/API is the national source (v1)",
    "E2": "not_collected — grid capacity/queue is EirGrid/SEMO; THE Irish story (Dublin moratorium) "
          "but a deep national adapter (v1)",
    "E3": "not_collected — EirGrid connection queue (v1)",
    "W1": "not_collected — no national drought machine feed wired",
    "W3": "not_collected — abstraction volumes not wired",
    "L1": "not_collected — CSO income per county (v1; bands are a methodology decision anyway)",
    "L3": "not_collected — Seveso (COMAH) establishments register not wired (v1)",
}

IE_SPEC = {
    "iso": "IE",
    "generator": "pipelines.spatial.ie v0 (EU-level only)",
    "summary": {
        "fr": "BROUILLON IE v0 (socle EU : masse d'eau, Natura, Corine) — angle contestation (moratoire Dublin). À vérifier.",
        "en": "IE DRAFT v0 (EU-level: water body, Natura, Corine) — contestation angle (Dublin moratorium). Verify before use.",
    },
    "fetch_commune": fetch_commune,
    "identity_fields": lambda c: {
        "municipality": c.get("name") or "UNKNOWN — to fill",
        **({"admin_area": c["county_iso"].removeprefix("IE-")} if c.get("county_iso") else {}),
    },
    "collectors": [
        (("W2",), lambda ctx, prov: [x] if (x := eu.collect_w2_universal(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F1",), lambda ctx, prov: [x] if (x := eu.natura_rings(ctx["lat"], ctx["lon"], ctx["accessed"])) else []),
        (("F2",), lambda ctx, prov: _f2(ctx, prov)),
    ],
    "collectable_gaps": frozenset({"E1", "E2", "E3", "W1", "W3", "L1", "L3"}),
    "provenance_commune": lambda c: {"county": c.get("county")},
    "provenance_extra": lambda ctx, prov: {"known_gaps": _GAPS, "f2_crosscheck": prov.get("f2_crosscheck")},
    "manual_still_required": ["F3", "L2", "T1", "T2", "E1", "E2", "E3", "W1", "W3", "L1", "L3"],
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
    return build_draft(IE_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv: list[str] | None = None) -> int:
    return run_cli(IE_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
