# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""The ONE draft-assembly skeleton every country adapter plugs into.

Design rule (2026-07-10): what is COMMON lives here, once — id shaping, the collector loop,
block-aware padding, fragment and provenance assembly, the CLI. A country contributes a
declarative SPEC (endpoints, collectors, documented gaps) plus code only for its genuine
national quirks (Caparéseau's scraped feed, Elia's xlsx…). No per-country copy of this skeleton
may exist: two skeletons drift, and drift across countries is a comparability bug.

A country spec is a plain dict:

    {
      "iso": "BE",                       # ISO 3166-1 alpha-2, uppercase
      "generator": "pipelines.spatial.be v1",
      "summary": {"fr": "...", "en": "..."},           # draft summary boilerplate
      "fetch_commune": fn(lat, lon) -> dict,           # backbone; raises SourceUnavailable
      "identity_fields": fn(commune) -> dict,          # municipality, admin_area…
      "collectors": [ ((ids…), fn(ctx, prov) -> [indicator…]), … ],
      "collectable_gaps": frozenset({...}),  # BASE ids a human CAN still collect → not_collected
      "provenance_commune": fn(commune) -> dict,       # country block after coordinates_input
      "provenance_extra": fn(ctx, prov) -> dict,       # after indicators_skipped (gaps, raw…)
      "manual_still_required": [...],
    }

Collector contract: receives ctx = {lat, lon, commune, accessed} and the mutable provenance
scratch `prov` (for sidecar facts like f2_crosscheck); returns 0..n schema-shaped indicator
dicts, never a score, never a fabricated value. Padding semantics (shared, non-negotiable):
an unfetched BASE datum is "missing" — unless the spec lists it as collectable-by-a-human
(then "not_collected"); an unread PROJECT/PROCESS datum is always "not_collected".
"""

import argparse
import json
import re
import sys
from datetime import date

from .http import SourceUnavailable


def _all_indicator_ids() -> list[str]:
    """The authoritative indicator list from the active methodology (empty on failure)."""
    try:
        from engine.core import load_methodology
        return [i["id"] for i in load_methodology()["indicators"]]
    except Exception:
        return []


def _indicator_blocks() -> dict[str, str]:
    """id -> block ('base' | 'project' | 'process') from the active methodology."""
    try:
        from engine.core import load_methodology
        return {i["id"]: i["block"] for i in load_methodology()["indicators"]}
    except Exception:
        return {}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[àâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    text = re.sub(r"[îï]", "i", text)
    text = re.sub(r"[ôö]", "o", text)
    text = re.sub(r"[ûü]", "u", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def build_draft(spec: dict, lat: float, lon: float, *, name: str, operator: str,
                power_mw: float | None, project_status: str,
                accessed: str) -> tuple[dict, dict, list[str]]:
    """Return (schema_valid_fragment, provenance_sidecar, skipped_indicator_ids)."""
    commune = spec["fetch_commune"](lat, lon)  # backbone; raises if unreachable
    iso = spec["iso"]
    slug = slugify(name) or slugify(str(commune.get("nom") or commune.get("name") or ""))
    dc_id = f"{iso.lower()}-{slug}"

    ctx = {"lat": lat, "lon": lon, "commune": commune, "accessed": accessed}
    prov: dict = {}
    indicators, collected, skipped = [], [], []
    for declared_ids, fn in spec["collectors"]:
        results = fn(ctx, prov) or []
        got = {i["id"] for i in results}
        indicators.extend(results)
        collected.extend(i for i in declared_ids if i in got)
        skipped.extend(i for i in declared_ids if i not in got)

    # Block-aware padding — shared semantics, see module docstring.
    filled_ids = {i["id"] for i in indicators}
    blocks = _indicator_blocks()
    collectable = spec.get("collectable_gaps", frozenset())
    for ind_id in _all_indicator_ids():
        if ind_id not in filled_ids:
            default = "not_collected" if blocks.get(ind_id) in ("project", "process") else "missing"
            if ind_id in collectable:
                default = "not_collected"
            indicators.append({"id": ind_id, "status": default})

    fragment = {
        "schema_version": "1.0",
        "id": dc_id,
        "identity": {
            "name": name,
            "operator": operator,
            **spec["identity_fields"](commune),
            "country": iso,
            "coordinates": {"lat": lat, "lon": lon},
            "project_status": project_status,
            "summary": dict(spec["summary"]),
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

    # Provenance sidecar — a SEPARATE file, never part of the scored record.
    provenance = {
        "draft_of": fragment["id"],
        "generator": spec["generator"],
        "generated_at": accessed,
        "coordinates_input": {"lat": lat, "lon": lon},
        **spec["provenance_commune"](commune),
        "indicators_filled": collected,
        "indicators_skipped": skipped,
        **(spec["provenance_extra"](ctx, prov) if spec.get("provenance_extra") else prov),
        "manual_still_required": list(spec["manual_still_required"]),
        "review_required": True,
        "warning": "Pipeline proposes, it does not publish. Human review mandatory before use.",
    }
    return fragment, provenance, skipped


def run_cli(spec: dict, argv: list[str] | None = None) -> int:
    """The shared collect CLI — every country's `python -m …collect` entry point."""
    p = argparse.ArgumentParser(
        description=f"Draft {spec['iso']} tier-1 collection from GPS coordinates.")
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
        fragment, provenance, skipped = build_draft(
            spec, args.lat, args.lon, name=args.name, operator=args.operator,
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
