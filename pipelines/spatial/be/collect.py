# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Assemble a *draft* Belgian datacenter fragment from coordinates alone.

    python -m pipelines.spatial.be.collect --lat 50.46767 --lon 3.86446 \
        --name "..." --operator "..." --out <newsroom>/drafts/datacenters

Same contract as pipelines.spatial.collect (FR): schema-shaped draft, every value sourced, NO
score ever written, human review mandatory. Belgian specifics: region routing (Wallonia /
Flanders / Brussels adapters), and four documented gaps — E3 (no public connection queue),
W1 (no machine drought feed), W3 (withdrawal volumes patchy), L1 (raw Statbel value goes to the
provenance sidecar; FR income bands are not transposable, BE bands pending methodology).
"""

import argparse
import json
import re
import sys
from datetime import date

from ..http import SourceUnavailable
from . import sources
from .elia import collect_e1, collect_grid_capacity


def _all_indicator_ids() -> list[str]:
    try:
        from engine.core import load_methodology
        return [i["id"] for i in load_methodology()["indicators"]]
    except Exception:
        return []


def _indicator_blocks() -> dict[str, str]:
    try:
        from engine.core import load_methodology
        return {i["id"]: i["block"] for i in load_methodology()["indicators"]}
    except Exception:
        return {}


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[àâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    text = re.sub(r"[îï]", "i", text)
    text = re.sub(r"[ôö]", "o", text)
    text = re.sub(r"[ûü]", "u", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


_GAPS = {
    "E3": "missing — no public BE equivalent of Caparéseau's connection-queue fill rate "
          "(Elia headroom is already E2's signal)",
    "W1": "not_collected — no machine drought feed found (Wallonia: Aquawal/RTBF widget trace "
          "pending; Flanders: waterinfo KiWIS needs a token)",
    "W3": "not_collected — SPW EAU/CAPTAGES exposes abstraction points but volumes are mostly "
          "null; no BNPE-like commune table",
}


def collect(lat: float, lon: float, *, name: str, operator: str, power_mw: float | None,
            project_status: str, accessed: str) -> tuple[dict, dict, list[str]]:
    """Return (schema_valid_fragment, provenance_sidecar, skipped_indicator_ids)."""
    commune = sources.fetch_commune(lat, lon)  # backbone; raises if unreachable
    region = commune["region"]
    slug = _slugify(name) or _slugify(commune.get("name") or "unknown")
    dc_id = f"be-{slug}"

    indicators, skipped, collected = [], [], []
    collectors = {
        "E1": lambda: collect_e1(accessed),
        "W2": lambda: sources.collect_w2(lat, lon, region, accessed),
        "F1": lambda: sources.collect_f1(lat, lon, region, accessed),
        "L3": lambda: sources.collect_l3(lat, lon, region, accessed),
    }
    for ind_id, fn in collectors.items():
        result = fn()
        if result is None:
            skipped.append(ind_id)
        else:
            indicators.append(result)
            collected.append(ind_id)

    f2_ind, f2_check = sources.collect_f2(lat, lon, region, accessed)
    if f2_ind is None:
        skipped.append("F2")
    else:
        indicators.append(f2_ind)
        collected.append("F2")

    for ind in collect_grid_capacity(lat, lon, accessed):
        indicators.append(ind)
        collected.append(ind["id"])
    if "E2" not in collected:
        skipped.append("E2")

    # Raw commune income for the provenance sidecar — never an indicator value (see sources).
    l1_raw = sources.collect_l1_raw(commune.get("nis"))

    # Block-aware padding, identical rule to the FR pipeline: an unfetched BASE datum is our
    # collection gap → "missing"; an unread PROJECT/PROCESS datum is "not_collected".
    filled_ids = {i["id"] for i in indicators}
    blocks = _indicator_blocks()
    for ind_id in _all_indicator_ids():
        if ind_id not in filled_ids:
            default = "not_collected" if blocks.get(ind_id) in ("project", "process") else "missing"
            if ind_id in ("W1", "W3", "L1", "W2"):
                # Collectable, just not by this v0 (human dig or v1 backlog) — never assert
                # "verified absent" for a datum that exists. E3 stays "missing": the metric
                # itself has no public Belgian source.
                default = "not_collected"
            indicators.append({"id": ind_id, "status": default})

    identity_extra = {}
    if commune.get("province_iso"):  # ISO 3166-2 province, e.g. BE-WHT → WHT
        identity_extra["admin_area"] = commune["province_iso"].removeprefix("BE-")

    fragment = {
        "schema_version": "1.0",
        "id": dc_id,
        "identity": {
            "name": name,
            "operator": operator,
            "municipality": commune.get("name") or "UNKNOWN — to fill",
            **identity_extra,
            "country": "BE",
            "coordinates": {"lat": lat, "lon": lon},
            "project_status": project_status,
            "summary": {
                "fr": "BROUILLON pré-rempli par le pipeline spatial BE (v0) — à vérifier avant tout usage.",
                "en": "DRAFT pre-filled by the BE spatial pipeline (v0) — verify before any use.",
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

    provenance = {
        "draft_of": fragment["id"],
        "generator": "pipelines.spatial.be v0",
        "generated_at": accessed,
        "coordinates_input": {"lat": lat, "lon": lon},
        "region": region,
        "commune_nis": commune.get("nis"),
        "indicators_filled": collected,
        "indicators_skipped": sorted(set(skipped)),
        "known_gaps": _GAPS,
        "l1_raw": l1_raw or "unavailable (no NIS resolved or Statbel unreachable)",
        "f2_crosscheck": f2_check,
        "manual_still_required": ["F3", "L2", "T1", "T2", "W1", "W3", "L1(bands)"],
        "review_required": True,
        "warning": "Pipeline proposes, it does not publish. Human review mandatory before use.",
    }
    return fragment, provenance, skipped


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Draft Belgian tier-1 collection from GPS coordinates.")
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
    print(f"Filled {len(filled)} indicators: {filled} · skipped: {sorted(set(skipped))}", file=sys.stderr)
    print("Review required before this fragment enters the circuit.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
