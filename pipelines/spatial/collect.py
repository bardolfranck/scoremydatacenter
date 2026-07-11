# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""France — tier-1 draft collection from coordinates alone.

    python -m pipelines.spatial.collect --lat 48.599 --lon 2.806 \
        --name "..." --operator "..." --power-mw 30 --out <newsroom>/drafts/datacenters

The assembly skeleton (collector loop, padding, fragment, provenance, CLI) lives in country.py
and is shared by every country; this module is the FRENCH SPEC — the wiring of the national
sources (geo.api.gouv.fr backbone, RTE, VigiEau, API Carto, Géorisques, BNPE, Filosofi, Sandre,
Caparéseau) onto that skeleton. Output contract unchanged: a schema-shaped DRAFT, every value
sourced, NO score ever written, human review mandatory before the fragment enters the circuit.
"""

from . import sources
from .capareseau import collect_grid_capacity
from .country import build_draft, run_cli, slugify as _slugify  # _slugify: orchestrate/press compat


def _wrap(fn):
    """Single-indicator collector → skeleton contract (0..n indicators)."""
    def collector(ctx, prov):
        result = fn(ctx)
        return [result] if result else []
    return collector


def _collect_f2(ctx, prov):
    ind, crosscheck = sources.collect_f2(ctx["lat"], ctx["lon"], ctx["accessed"])
    prov["f2_crosscheck"] = crosscheck
    return [ind] if ind else []


def _collect_grid(ctx, prov):
    return collect_grid_capacity(
        ctx["lat"], ctx["lon"], ctx["commune"].get("codeRegion"), ctx["accessed"])


FR_SPEC = {
    "iso": "FR",
    "generator": "pipelines.spatial v1",
    "summary": {
        "fr": "BROUILLON pré-rempli par le pipeline spatial — à vérifier avant tout usage.",
        "en": "DRAFT pre-filled by the spatial pipeline — verify before any use.",
    },
    "fetch_commune": sources.fetch_commune,
    "identity_fields": lambda c: {
        "municipality": c["nom"],
        "admin_area": c.get("codeDepartement"),
    },
    "collectors": [
        (("E1",), _wrap(lambda ctx: sources.collect_e1(ctx["accessed"]))),
        (("W1",), _wrap(lambda ctx: sources.collect_w1(ctx["lat"], ctx["lon"], ctx["accessed"]))),
        (("F1",), _wrap(lambda ctx: sources.collect_f1(ctx["lat"], ctx["lon"], ctx["accessed"]))),
        (("L3",), _wrap(lambda ctx: sources.collect_l3(ctx["lat"], ctx["lon"], ctx["accessed"]))),
        (("W3",), _wrap(lambda ctx: sources.collect_w3(ctx["commune"]["code"], ctx["accessed"]))),
        (("L1",), _wrap(lambda ctx: sources.collect_l1(ctx["commune"]["code"], ctx["accessed"]))),
        (("W2",), _wrap(lambda ctx: sources.collect_w2(ctx["lat"], ctx["lon"], ctx["accessed"]))),
        (("F2",), _collect_f2),
        (("E2", "E3"), _collect_grid),
    ],
    "collectable_gaps": frozenset(),
    "provenance_commune": lambda c: {
        "commune_insee": c["code"],
        "commune_population": c.get("population"),
        "commune_surface_ha": c.get("surface"),
    },
    "provenance_extra": lambda ctx, prov: {"f2_crosscheck": prov.get("f2_crosscheck")},
    "manual_still_required": ["F3", "L2", "T1", "T2"],
}


def collect(lat: float, lon: float, *, name: str, operator: str, power_mw: float | None,
            project_status: str, accessed: str) -> tuple[dict, dict, list[str]]:
    """Return (schema_valid_fragment, provenance_sidecar, skipped_indicator_ids)."""
    return build_draft(FR_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv: list[str] | None = None) -> int:
    return run_cli(FR_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
