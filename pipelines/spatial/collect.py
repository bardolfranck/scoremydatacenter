# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Assemble a *draft* datacenter fragment from coordinates alone.

    python -m pipelines.spatial.collect --lat 48.599 --lon 2.806 \
        --name "..." --operator "..." --power-mw 30 --out <newsroom>/drafts/datacenters

Output = a schema-shaped file with identity + the sourced tier-1 indicators the pipeline could
fill (v1: E1, W1, F1, F2, L3). It is a DRAFT: publication.status = "draft", every value carries a
source, and NO score is ever written — the engine computes those at build time from the reviewed
file. A human must review the fragment before it enters the circuit (anti-hallucination rule; an
out-of-range API value read wrong is as dangerous as a made-up one).
"""

import argparse
import json
import re
import sys
from datetime import date

from .http import SourceUnavailable
from . import sources
from .capareseau import collect_grid_capacity


def _all_indicator_ids() -> list[str]:
    """The authoritative indicator list from the active methodology (empty on failure)."""
    try:
        from engine.core import load_methodology
        return [i["id"] for i in load_methodology()["indicators"]]
    except Exception:
        return []


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[àâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    text = re.sub(r"[îï]", "i", text)
    text = re.sub(r"[ôö]", "o", text)
    text = re.sub(r"[ûü]", "u", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def collect(lat: float, lon: float, *, name: str, operator: str, power_mw: float | None,
            project_status: str, accessed: str) -> tuple[dict, dict, list[str]]:
    """Return (schema_valid_fragment, provenance_sidecar, skipped_indicator_ids)."""
    commune = sources.fetch_commune(lat, lon)  # backbone; raises if unreachable
    slug = _slugify(name) or _slugify(commune["nom"])
    dc_id = f"fr-{slug}"

    indicators, skipped, collected = [], [], []
    collectors = {
        "E1": lambda: sources.collect_e1(accessed),
        "W1": lambda: sources.collect_w1(lat, lon, accessed),
        "F1": lambda: sources.collect_f1(lat, lon, accessed),
        "L3": lambda: sources.collect_l3(lat, lon, accessed),
        "W3": lambda: sources.collect_w3(commune["code"], accessed),
        "L1": lambda: sources.collect_l1(commune["code"], accessed),
        "W2": lambda: sources.collect_w2(lat, lon, accessed),
    }
    for ind_id, fn in collectors.items():
        result = fn()
        if result is None:
            skipped.append(ind_id)
        else:
            indicators.append(result)
            collected.append(ind_id)

    # F2 (soil) is special: PLU/RPG value with a Corine Land Cover fallback + cross-check.
    f2_ind, f2_check = sources.collect_f2(lat, lon, accessed)
    if f2_ind is None:
        skipped.append("F2")
    else:
        indicators.append(f2_ind)
        collected.append("F2")

    # E2 + E3 (grid capacity/congestion) come as a pair from one Caparéseau region fetch.
    grid = collect_grid_capacity(lat, lon, commune.get("codeRegion"), accessed)
    grid_ids = {i["id"] for i in grid}
    for ind_id in ("E2", "E3"):
        if ind_id in grid_ids:
            indicators.append(next(i for i in grid if i["id"] == ind_id))
            collected.append(ind_id)
        else:
            skipped.append(ind_id)

    # Pad every not-yet-collected indicator as an explicit "missing" placeholder so the draft is
    # immediately engine-scoreable and the reviewer sees exactly which slots still need hand work.
    # "missing" is honest for now (not yet collected) — the human upgrades each to measured/announced.
    filled_ids = {i["id"] for i in indicators}
    for ind_id in _all_indicator_ids():
        if ind_id not in filled_ids:
            indicators.append({"id": ind_id, "status": "missing"})

    fragment = {
        "schema_version": "1.0",
        "id": dc_id,
        "identity": {
            "name": name,
            "operator": operator,
            "municipality": commune["nom"],
            "admin_area": commune.get("codeDepartement"),
            "country": "FR",
            "coordinates": {"lat": lat, "lon": lon},
            "project_status": project_status,
            "summary": {
                "fr": "BROUILLON pré-rempli par le pipeline spatial — à vérifier avant tout usage.",
                "en": "DRAFT pre-filled by the spatial pipeline — verify before any use.",
            },
        },
        "indicators": indicators,
        "publication": {
            "status": "draft",
            "operator_notified_at": None,
            "operator_response": None,
        },
        "score_history": [],
    }
    if power_mw is not None:
        fragment["identity"]["power_mw"] = power_mw

    # Provenance side-car — a SEPARATE file, never part of the scored record (the DC schema is
    # closed). It also carries the commune facts (population/surface) a reviewer needs to fill the
    # manual indicators (L1/L2) by hand.
    provenance = {
        "draft_of": fragment["id"],
        "generator": "pipelines.spatial v1",
        "generated_at": accessed,
        "coordinates_input": {"lat": lat, "lon": lon},
        "commune_insee": commune["code"],
        "commune_population": commune.get("population"),
        "commune_surface_ha": commune.get("surface"),
        "indicators_filled": collected,
        "indicators_skipped": skipped,
        # F2 legal-zoning value vs. observed land cover — a disagreement is worth the reviewer's eye
        # (outdated zoning, or a site already artificialized under an agricultural zone).
        "f2_crosscheck": f2_check,
        "manual_still_required": ["F3", "L2", "T1", "T2"],
        "review_required": True,
        "warning": "Pipeline proposes, it does not publish. Human review mandatory before use.",
    }
    return fragment, provenance, skipped


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Draft tier-1 collection from GPS coordinates.")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--name", default="UNKNOWN — to fill")
    p.add_argument("--operator", default="UNKNOWN — to fill")
    p.add_argument("--power-mw", type=float, default=None)
    p.add_argument("--project-status", default="announced",
                   choices=["announced", "permitting", "under_construction", "operational"])
    p.add_argument("--out", default=None,
                   help="Directory to write <id>.draft.json into (default: stdout).")
    args = p.parse_args(argv)

    accessed = date.today().isoformat()
    try:
        fragment, provenance, skipped = collect(
            args.lat, args.lon, name=args.name, operator=args.operator,
            power_mw=args.power_mw, project_status=args.project_status, accessed=accessed)
    except SourceUnavailable as exc:
        print(f"ERROR: backbone geocoder unavailable — cannot place the point. {exc}", file=sys.stderr)
        return 2

    text = json.dumps(fragment, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        from pathlib import Path
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        draft_path = out_dir / f"{fragment['id']}.draft.json"
        prov_path = out_dir / f"{fragment['id']}.provenance.json"
        draft_path.write_text(text)
        prov_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote draft → {draft_path}", file=sys.stderr)
        print(f"Wrote provenance → {prov_path}", file=sys.stderr)
    else:
        sys.stdout.write(text)

    filled = provenance["indicators_filled"]
    print(f"Filled {len(filled)} indicators: {filled} · skipped: {skipped}", file=sys.stderr)
    print("Review required before this fragment enters the circuit.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
