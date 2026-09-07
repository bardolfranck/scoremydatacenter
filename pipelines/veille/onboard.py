# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Phase-1 « site vivant » : route detected EU pipeline projects to the PUBLIC « en veille » lane.

    python -m pipelines.veille.onboard --dry-run          # preview candidates, writes NOTHING served
    python -m pipelines.veille.onboard --out cand.json    # write review candidates (NOT the served file)

DOCTRINE (Franck 2026-09-06, « paywall par cycle de vie ») — an ANNOUNCED project is PUBLIC only as
« en veille » : a sourced FACT with NO grade. A-19 is enforced structurally by watchlist.schema.json
(`additionalProperties:false` → a letter/score is impossible in a watchlist entry). This module
NEVER emits a grade, NEVER writes the served watchlist, NEVER deploys. It produces REVIEW CANDIDATES
for the red lane (a project always needs a human eye — voie rouge), not an auto-publish.

Pipeline: osm_projects (unbiased OSM discovery) → gates → dedup → schema-valid « en veille » entries.

GATES (conservative on purpose):
  - NAMED OPERATOR only. ~40% of OSM captures carry no operator; an « operator unknown » public
    fiche is not worth showing → those wait in a queue, never auto-onboarded.
  - DEDUP vs the SERVED corpus (map.geojson, ~1 km cell + operator) AND vs the existing watchlist:
    a project already public (graded OR en-veille) is not re-listed.
  - A project is VOIE ROUGE (human review), never auto-published — this emits candidates only.
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from engine.core import ARTIFACTS_DIR, load_watchlist
from pipelines.press import osm_projects

_NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
_CELL_DP = 2  # served map.geojson coords are 2 dp (~1.1 km) — dedup at the served resolution
_LEGAL = {"gmbh", "oy", "oyj", "ab", "ltd", "limited", "sa", "sas", "sarl", "bv", "ag",
          "plc", "llc", "inc", "srl", "spa", "as", "nv", "kg", "kgaa", "se", "corp", "co"}
_PUBLISHABLE_STATUS = {"announced", "under_construction"}


def _norm_op(op: str | None) -> str:
    toks = [t for t in re.split(r"[^a-z0-9]+", (op or "").lower()) if t and t not in _LEGAL]
    s = "".join(toks)
    return s if s and not s.startswith("unknown") else ""


def _is_named(op: str | None) -> bool:
    return bool(_norm_op(op))


def _cell(lat, lon):
    try:
        return (round(float(lat), _CELL_DP), round(float(lon), _CELL_DP))
    except (TypeError, ValueError):
        return None


def _haversine_m(a_lat, a_lon, b_lat, b_lon) -> float:
    from math import radians, sin, cos, asin, sqrt
    dl, do = radians(b_lat - a_lat), radians(b_lon - a_lon)
    x = sin(dl / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(do / 2) ** 2
    return 2 * 6371000 * asin(sqrt(x))


_INTERNAL_DEDUP_M = 250  # two candidates within 250 m + same operator = the same project (2 OSM ways)


def _dedup_internal(cands: list[dict]) -> tuple[list[dict], int]:
    """Candidate-vs-candidate dedup: 2 OSM ways of one project (e.g. DR Hattersheim 484/485, 75 m)
    survive the vs-served cell pass but are the SAME project. Merge by proximity + same operator,
    keeping the first (stable order). Returns (kept, n_merged)."""
    kept, merged = [], 0
    for c in cands:
        op = _norm_op(c.get("operator"))
        cc = c["coordinates"]
        dup = next((k for k in kept if _norm_op(k.get("operator")) == op
                    and _haversine_m(float(cc["lat"]), float(cc["lon"]),
                                     float(k["coordinates"]["lat"]), float(k["coordinates"]["lon"])) <= _INTERNAL_DEDUP_M),
                   None)
        if dup is None:
            kept.append(c)
        else:
            merged += 1
    return kept, merged


def _reverse_geocode(lat: float, lon: float, *, sleep=time.sleep) -> dict:
    """Nominatim reverse → {country (ISO2 upper), municipality}. Empty on miss (never raises)."""
    sleep(1.1)  # Nominatim policy: 1 req/s
    q = urllib.parse.urlencode({"lat": lat, "lon": lon, "format": "json", "zoom": 10})
    req = urllib.request.Request(f"{_NOMINATIM}?{q}",
                                 headers={"User-Agent": "scoremydatacenter-onboard/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            addr = (json.load(r) or {}).get("address") or {}
    except Exception:  # noqa: BLE001 — a geocode miss drops one candidate, never the run
        return {}
    muni = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality")
    return {"country": (addr.get("country_code") or "").upper(), "municipality": muni}


def _served_cells_ops():
    """{cell: {operator_key,…}} from the served map.geojson (the only served surface with coords)."""
    mp = ARTIFACTS_DIR / "map.geojson"
    by_cell: dict = {}
    if mp.exists():
        for f in json.loads(mp.read_text()).get("features", []):
            lon, lat = (f.get("geometry", {}).get("coordinates") or [None, None])[:2]
            c = _cell(lat, lon)
            if c:
                by_cell.setdefault(c, set()).add(_norm_op(f.get("properties", {}).get("operator")))
    return by_cell


def _watchlist_cells_ops():
    by_cell: dict = {}
    for e in load_watchlist():
        c = e.get("coordinates") or {}
        cell = _cell(c.get("lat"), c.get("lon"))
        if cell:
            by_cell.setdefault(cell, set()).add(_norm_op(e.get("operator")))
    return by_cell


def _slug(*parts: str) -> str:
    s = "-".join(p for p in parts if p)
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s) or "site"


def _entry(row: dict, geo: dict, today: str) -> dict:
    """A schema-valid « en veille » entry: sourced FACT, NO grade (structurally impossible)."""
    iso = (geo.get("country") or "").upper()
    entry = {
        "id": _slug(iso.lower() or "eu", row["operator"], geo.get("municipality") or "",
                    str(row.get("source_url", "")).rsplit("/", 1)[-1]),
        "name": row.get("name") or f"{row['operator']} data center",
        "operator": row["operator"],
        "country": iso if re.fullmatch(r"[A-Z]{2}", iso) else "",
        "coordinates": {"lat": float(row["lat"]), "lon": float(row["lon"])},
        "project_status": row.get("project_status", "announced"),
        "source": {
            "title": "OpenStreetMap contributors (ODbL) — data center lifecycle tag",
            "url": row.get("source_url", "https://www.openstreetmap.org/"),
            "accessed": today,
        },
        "facts": [],   # a bare announced project: justified by the entry-level source, no fake fact
    }
    if geo.get("municipality"):
        entry["municipality"] = geo["municipality"]
    return entry


def build_candidates(rows=None, *, today=None, geocode=_reverse_geocode) -> tuple[list, dict]:
    """Detected pipeline projects → « en veille » candidates + a stats/report dict. Writes nothing."""
    today = today or date.today().isoformat()
    rows = rows if rows is not None else osm_projects.collect()
    served, watch = _served_cells_ops(), _watchlist_cells_ops()
    cand, dropped = [], {"unnamed": 0, "status": 0, "served_dup": 0, "watchlist_dup": 0, "no_country": 0}
    for r in rows:
        if r.get("project_status") not in _PUBLISHABLE_STATUS:
            dropped["status"] += 1; continue
        if not _is_named(r.get("operator")):
            dropped["unnamed"] += 1; continue
        cell, op = _cell(r["lat"], r["lon"]), _norm_op(r.get("operator"))
        if op in served.get(cell, set()):
            dropped["served_dup"] += 1; continue
        if op in watch.get(cell, set()):
            dropped["watchlist_dup"] += 1; continue
        geo = geocode(float(r["lat"]), float(r["lon"]))
        e = _entry(r, geo, today)
        if not e["country"]:
            dropped["no_country"] += 1; continue
        cand.append(e)
    cand, internal_merged = _dedup_internal(cand)   # candidate-vs-candidate (2 OSM ways of one project)
    dropped["internal_merged"] = internal_merged
    report = {"candidates": len(cand), "dropped": dropped, "input": len(rows)}
    return cand, report


def _validate(entries: list) -> list[str]:
    """Best-effort schema check (jsonschema if available, else a structural fallback)."""
    errs = []
    try:
        import jsonschema  # noqa: PLC0415
        schema = json.loads((Path(__file__).resolve().parents[2] / "data" / "schema" / "watchlist.schema.json").read_text())
        for i, e in enumerate(entries):
            for err in jsonschema.Draft202012Validator(schema).iter_errors([e]):
                errs.append(f"[{i}] {err.message}")
    except ModuleNotFoundError:
        for i, e in enumerate(entries):
            for k in ("id", "name", "country", "coordinates", "source"):
                if k not in e:
                    errs.append(f"[{i}] missing {k}")
            if "grade" in json.dumps(e).lower():
                errs.append(f"[{i}] FORBIDDEN grade-like field in an en-veille entry")
    return errs


def review_markdown(candidates: list) -> str:
    """A human-readable one-per-row table for Franck's VOIE ROUGE gate: he validates/rejects each
    candidate before ANY publication. Facts only (operator, place, status, source) — no grade."""
    head = (f"# Gate voie-rouge — {len(candidates)} projets « en veille » candidats (à valider un par un)\n\n"
            "> Aucune note. Chaque ligne = un projet annoncé détecté (OSM). Valider = publier « en veille » ; "
            "rejeter = écarter. Rien n'est publié sans ta validation.\n\n"
            "| # | Projet | Opérateur | Pays | Statut | Source (OSM) |\n"
            "|---|--------|-----------|------|--------|--------------|\n")
    rows = []
    for i, c in enumerate(candidates, 1):
        muni = c.get("municipality") or ""
        name = f"{c['name']}" + (f" — {muni}" if muni else "")
        rows.append(f"| {i} | {name} | {c.get('operator','')} | {c['country']} | "
                    f"{c.get('project_status','')} | {c['source']['url']} |")
    return head + "\n".join(rows) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Phase-1 en-veille onboarding — candidates only, never served.")
    ap.add_argument("--dry-run", action="store_true", help="preview only (default if no --out)")
    ap.add_argument("--out", help="write review candidates JSON to this file (NOT the served watchlist)")
    ap.add_argument("--review", help="write the human-readable voie-rouge gate table (markdown) to this file")
    args = ap.parse_args(argv)
    cand, report = build_candidates()
    errs = _validate(cand)
    print(f"onboard: {report['input']} détectés → {report['candidates']} candidats « en veille »", file=sys.stderr)
    print(f"  écartés : {report['dropped']}", file=sys.stderr)
    print(f"  schéma watchlist : {'OK ✅' if not errs else '❌ ' + str(errs[:5])}", file=sys.stderr)
    print("  ⛔ AUCUNE note émise (A-19) · AUCUN fichier servi écrit · AUCUN deploy · voie ROUGE (revue humaine).", file=sys.stderr)
    if errs:
        return 1
    if args.review:
        Path(args.review).write_text(review_markdown(cand))
        print(f"  table de gate voie-rouge (POUR REVUE Franck) → {args.review}", file=sys.stderr)
    if args.out and not args.dry_run:
        Path(args.out).write_text(json.dumps(cand, ensure_ascii=False, indent=2) + "\n")
        print(f"  candidats JSON (POUR REVUE, non servis) → {args.out}", file=sys.stderr)
    elif not args.review:
        print(json.dumps(cand, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
