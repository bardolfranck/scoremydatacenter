# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Belgium — tier-1 draft collection from coordinates alone.

    python -m pipelines.spatial.be.collect --lat 50.46767 --lon 3.86446 \
        --name "..." --operator "..." --out <newsroom>/drafts/datacenters

The assembly skeleton lives in country.py (shared by every country); this module is the BELGIAN
SPEC. Documented gaps (see README.md): E3 stays "missing" (the metric has no public Belgian
source), W1/W3/L1/W2-Flanders pad as "not_collected" (collectable, just not by this version).
"""

from ..country import build_draft, run_cli
from . import sources
from .elia import collect_e1, collect_grid_capacity


def _wrap(fn):
    def collector(ctx, prov):
        result = fn(ctx)
        return [result] if result else []
    return collector


def _collect_f2(ctx, prov):
    ind, crosscheck = sources.collect_f2(
        ctx["lat"], ctx["lon"], ctx["commune"]["region"], ctx["accessed"])
    prov["f2_crosscheck"] = crosscheck
    return [ind] if ind else []


_GAPS = {
    "E3": "missing — no public BE equivalent of Caparéseau's connection-queue fill rate "
          "(Elia headroom is already E2's signal)",
    "W1": "not_collected — no machine drought feed found (Wallonia: Aquawal/RTBF widget trace "
          "pending; Flanders: waterinfo KiWIS needs a token)",
    "W3": "not_collected — SPW EAU/CAPTAGES exposes abstraction points but volumes are mostly "
          "null; no BNPE-like commune table",
    "L1": "not_collected — raw Statbel value in provenance (l1_raw); FR bands not transposable, "
          "BE bands pending methodology",
}

BE_SPEC = {
    "iso": "BE",
    "generator": "pipelines.spatial.be v1",
    "summary": {
        "fr": "BROUILLON pré-rempli par le pipeline spatial BE — à vérifier avant tout usage.",
        "en": "DRAFT pre-filled by the BE spatial pipeline — verify before any use.",
    },
    "fetch_commune": sources.fetch_commune,
    "identity_fields": lambda c: {
        "municipality": c.get("name") or "UNKNOWN — to fill",
        **({"admin_area": c["province_iso"].removeprefix("BE-")} if c.get("province_iso") else {}),
    },
    "collectors": [
        (("E1",), _wrap(lambda ctx: collect_e1(ctx["accessed"]))),
        (("W2",), _wrap(lambda ctx: sources.collect_w2(
            ctx["lat"], ctx["lon"], ctx["commune"]["region"], ctx["accessed"]))),
        (("F1",), _wrap(lambda ctx: sources.collect_f1(
            ctx["lat"], ctx["lon"], ctx["commune"]["region"], ctx["accessed"]))),
        (("L3",), _wrap(lambda ctx: sources.collect_l3(
            ctx["lat"], ctx["lon"], ctx["commune"]["region"], ctx["accessed"]))),
        (("F2",), _collect_f2),
        (("E2",), lambda ctx, prov: collect_grid_capacity(ctx["lat"], ctx["lon"], ctx["accessed"])),
    ],
    "collectable_gaps": frozenset({"W1", "W3", "L1", "W2"}),
    "provenance_commune": lambda c: {
        "region": c.get("region"),
        "commune_nis": c.get("nis"),
    },
    "provenance_extra": lambda ctx, prov: {
        "known_gaps": _GAPS,
        "l1_raw": sources.collect_l1_raw(ctx["commune"].get("nis"))
                  or "unavailable (no NIS resolved or Statbel unreachable)",
        "f2_crosscheck": prov.get("f2_crosscheck"),
    },
    "manual_still_required": ["F3", "L2", "T1", "T2", "W1", "W3", "L1(bands)"],
}


def collect(lat: float, lon: float, *, name: str, operator: str, power_mw: float | None,
            project_status: str, accessed: str) -> tuple[dict, dict, list[str]]:
    """Return (schema_valid_fragment, provenance_sidecar, skipped_indicator_ids)."""
    return build_draft(BE_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv: list[str] | None = None) -> int:
    return run_cli(BE_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
