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
from pipelines.veille import dedup   # ONE source of truth for norm_op / cell / match_served / dedup_internal

_NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
_PUBLISHABLE_STATUS = {"announced", "under_construction"}


def _is_named(op: str | None) -> bool:
    return bool(dedup.norm_op(op))


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


def _served_index():
    """Served map.geojson → dedup index {cell: [(id, operator)]} (the shared-util shape)."""
    mp = ARTIFACTS_DIR / "map.geojson"
    return dedup.served_index(json.loads(mp.read_text()).get("features", []) if mp.exists() else [])


def _watchlist_index():
    return dedup.index_from_entries(load_watchlist())


_CONTEST_KINDS = {"opposition", "moratorium", "appeal", "petition"}
# Franck-sensitive territories → ALWAYS manual_gate (never auto-published), even clean/en-veille.
# Iceland ([[islande-watchlist-par-choix]]) : « IS = mon territoire, escalade » — the EU bbox catches
# IS projects, but any IS onboarding is Franck's call, not auto. Add a country here to force his eye.
_MANUAL_COUNTRIES = {"IS"}
# AUTO-PUBLICATION POLICY (Phase-1) — a clean detected project auto-publishes « en veille » (no
# grade) WITHOUT the manual gate. This amends the standing rule [[gate-voie-verte]] (« projet =
# voie rouge ») for CLEAN en-veille projects only; contested projects STAY manual_gate.
# ACTIVATED 2026-09-07 on Franck's DIRECT, REPEATED, verbatim go to his designated orchestrator
# (agent-codeur-site), who holds his authorization and relayed it faithfully (Franck explicitly
# declined to re-type it per-channel). Fail-closed until this moment: nothing was published before.
# Even ON, onboard only DEPOSITS auto-eligible entries to the private newsroom watchlist (no grade,
# schema-forbidden) — PUBLICATION to the served site is the separate deploy step (agent-site).
AUTO_PUBLISH_ENABLED = True


def _contested_index():
    """dedup index {cell:[(id,op)]} of watchlist entries carrying a CONTESTATION fact — a candidate
    matching one (exact/brand, via dedup.match_served) is litigious → manual gate, never auto."""
    contested = [e for e in load_watchlist()
                 if {f.get("kind") for f in (e.get("facts") or [])} & _CONTEST_KINDS]
    return dedup.index_from_entries(contested)


def _lane(entry: dict, contested_idx: dict) -> str:
    """Routing lane (schema forbids storing it IN the entry): 'manual_gate' if the candidate
    collides (exact op or brand) with a CONTESTED watchlist site — litigious, Franck's eye — else
    'auto_eligible' (would auto-publish en-veille ONLY if AUTO_PUBLISH_ENABLED + Franck's sign-off).
    Never a grade either way."""
    cc = entry["coordinates"]
    return "manual_gate" if dedup.match_served(cc["lat"], cc["lon"], entry.get("operator"), contested_idx) else "auto_eligible"


def _slug(*parts: str) -> str:
    s = "-".join(p for p in parts if p)
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s) or "site"


def _clean_name(raw: str | None, operator: str, municipality: str | None) -> str:
    """Public-facing name. The collector appends « OSM <type> <id> » to raw for id-uniqueness, but
    the entry id is already unique (via _slug + the OSM element id), so strip that suffix here. A
    generic/empty result falls back to operator (+ commune) — no ugly « data center OSM way 123 »."""
    name = re.sub(r"\s*OSM (node|way|relation)\s+\d+\s*$", "", (raw or "").strip()).strip()
    if not name or name.lower() in {"data center", "data centre", "datacenter"}:
        return f"{operator} — {municipality}" if municipality else f"{operator} data center"
    return name


def _entry(row: dict, geo: dict, today: str) -> dict:
    """A schema-valid « en veille » entry: sourced FACT, NO grade (structurally impossible)."""
    iso = (geo.get("country") or "").upper()
    entry = {
        "id": _slug(iso.lower() or "eu", row["operator"], geo.get("municipality") or "",
                    str(row.get("source_url", "")).rsplit("/", 1)[-1]),
        "name": _clean_name(row.get("name"), row["operator"], geo.get("municipality")),
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
    served, watch = _served_index(), _watchlist_index()
    cand, flagged, dropped = [], set(), {"unnamed": 0, "status": 0, "served_dup": 0,
                                         "watchlist_dup": 0, "no_country": 0}
    for r in rows:
        if r.get("project_status") not in _PUBLISHABLE_STATUS:
            dropped["status"] += 1; continue
        if not _is_named(r.get("operator")):
            dropped["unnamed"] += 1; continue
        lat, lon, op = float(r["lat"]), float(r["lon"]), r.get("operator")
        sm = dedup.match_served(lat, lon, op, served)
        if sm and sm[0] == "exclude":       # already public (exact/brand) → not re-listed
            dropped["served_dup"] += 1; continue
        wm = dedup.match_served(lat, lon, op, watch)
        if wm and wm[0] == "exclude":        # already watched → not re-listed
            dropped["watchlist_dup"] += 1; continue
        geo = geocode(lat, lon)
        e = _entry(r, geo, today)
        if not e["country"]:
            dropped["no_country"] += 1; continue
        cand.append(e)
        if (sm and sm[0] == "flag") or (wm and wm[0] == "flag"):
            flagged.add(e["id"])             # dense-cluster coincidence → human review, not auto
    cand, merged = dedup.dedup_internal(cand)   # candidate-vs-candidate (2 OSM ways of one project)
    dropped["internal_merged"] = len(merged)
    contested = _contested_index()
    lanes = {"auto_eligible": [], "manual_gate": []}
    for e in cand:
        manual = (e["id"] in flagged or e.get("country") in _MANUAL_COUNTRIES
                  or _lane(e, contested) == "manual_gate")
        lanes["manual_gate" if manual else "auto_eligible"].append(e["id"])
    report = {"candidates": len(cand), "dropped": dropped, "input": len(rows),
              "lanes": lanes, "auto_publish_enabled": AUTO_PUBLISH_ENABLED}
    return cand, report


_SUPPRESS_BASENAME = "eu-projects-suppress.json"


def _suppress_path_for(watchlist_out) -> Path:
    """Franck's suppression list, co-located in calibration/ — NOT calibration/watchlist/ (the build
    globs watchlist/*.json as watchlist SOURCES; a suppress file there would be mis-read + break)."""
    return Path(watchlist_out).parent.parent / _SUPPRESS_BASENAME


def _suppressed_ids(path) -> set:
    """Ids Franck curated OUT → NEVER (re)deposited (durable un-publish). Empty/absent = none."""
    try:
        return set(json.loads(Path(path).read_text())) if Path(path).exists() else set()
    except (json.JSONDecodeError, OSError, TypeError):
        return set()


def deposit_auto_eligible(candidates, lanes, out_path, suppressed=None) -> int:
    """RECONCILE the AUTO-managed newsroom watchlist file to the CURRENT auto-eligible set MINUS
    the suppression list — schema-valid, NO grade. Auto-managed (deterministic overwrite): a project
    that leaves detection OR that Franck suppressed disappears, and the daily cron never duplicates.
    Contested/flagged/IS are NEVER here (manual_gate). Writes NOTHING if AUTO_PUBLISH_ENABLED is
    False (fail-closed). Deposits to the PRIVATE newsroom only; the served site is the deploy step.

    Fix A (durable curation): `suppressed` defaults to the on-disk suppress list next to out_path —
    Franck adds an id there and it stays un-published even if still detected (a hand-delete of a line
    here would be undone by the next reconcile; the suppress list is the durable lever he required).
    Fix B (anti-fat-finger): REFUSES to write a served artifact — the deposit only targets a source
    watchlist file, never map.geojson/scores.json/etc."""
    if not AUTO_PUBLISH_ENABLED:
        return 0
    p = Path(out_path)
    if "site/public/data" in p.as_posix() or p.name in {"map.geojson", "scores.json",
                                                        "stats.json", "watchlist.geojson", "home_showcase.json"}:
        raise SystemExit(f"REFUS dépôt : {p} est un artefact SERVI — le dépôt ne va que dans une watchlist source.")
    if suppressed is None:
        suppressed = _suppressed_ids(_suppress_path_for(p))
    auto = set(lanes.get("auto_eligible", [])) - set(suppressed)
    fresh = [c for c in candidates if c["id"] in auto]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + "\n")
    return len(fresh)


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


def review_markdown(candidates: list, lane_of: dict | None = None) -> str:
    """A human-readable one-per-row table for Franck's gate: he validates/rejects each candidate
    before ANY publication. Facts only (operator, place, status, source) — no grade. The « Voie »
    column shows the routing (auto-éligible vs gate-contesté) so Franck sees at a glance what the
    auto-en-veille policy WOULD publish vs what needs his eye — but nothing publishes without him."""
    lane_of = lane_of or {}
    head = (f"# Gate — {len(candidates)} projets « en veille » candidats (à valider un par un)\n\n"
            "> Aucune note. Chaque ligne = un projet annoncé détecté (OSM). « Voie » = routage proposé "
            "(auto-éligible = nommé+source+dédup-propre ; gate-contesté = litige, ton œil requis). "
            "Rien n'est publié sans ta validation tant que la politique auto n'est pas activée.\n\n"
            "| # | Projet | Opérateur | Pays | Statut | Voie | Source (OSM) |\n"
            "|---|--------|-----------|------|--------|------|--------------|\n")
    rows = []
    for i, c in enumerate(candidates, 1):
        muni = c.get("municipality") or ""
        name = f"{c['name']}" + (f" — {muni}" if muni else "")
        lane = lane_of.get(c.get("id"))
        voie = "🟢 auto-éligible" if lane == "auto_eligible" else (
            "🔴 gate-contesté" if lane == "manual_gate" else "—")
        rows.append(f"| {i} | {name} | {c.get('operator','')} | {c['country']} | "
                    f"{c.get('project_status','')} | {voie} | {c['source']['url']} |")
    return head + "\n".join(rows) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Phase-1 en-veille onboarding — candidates only, never served.")
    ap.add_argument("--dry-run", action="store_true", help="preview only (default if no --out)")
    ap.add_argument("--out", help="write review candidates JSON to this file (NOT the served watchlist)")
    ap.add_argument("--review", help="write the human-readable voie-rouge gate table (markdown) to this file")
    ap.add_argument("--publish", help="MERGE auto-eligible en-veille entries into this newsroom watchlist "
                    "file (only if AUTO_PUBLISH_ENABLED; contested/flagged never auto-deposited). "
                    "Deposits to the PRIVATE newsroom — the served site is a separate deploy step.")
    args = ap.parse_args(argv)
    cand, report = build_candidates()
    errs = _validate(cand)
    lanes = report["lanes"]
    lane_of = {i: "auto_eligible" for i in lanes["auto_eligible"]}
    lane_of.update({i: "manual_gate" for i in lanes["manual_gate"]})
    print(f"onboard: {report['input']} détectés → {report['candidates']} candidats « en veille »", file=sys.stderr)
    print(f"  écartés : {report['dropped']}", file=sys.stderr)
    print(f"  voies : auto-éligible {len(lanes['auto_eligible'])} · gate-contesté {len(lanes['manual_gate'])}"
          f"  (auto_publish_enabled={report['auto_publish_enabled']})", file=sys.stderr)
    print(f"  schéma watchlist : {'OK ✅' if not errs else '❌ ' + str(errs[:5])}", file=sys.stderr)
    print(f"  ⛔ A-19 : AUCUNE note (en veille = fait sourcé). Publication auto = {'ON' if AUTO_PUBLISH_ENABLED else 'OFF'} "
          "(dépôt newsroom privé ; served = deploy séparé, agent-site).", file=sys.stderr)
    if errs:
        return 1
    if args.review:
        Path(args.review).write_text(review_markdown(cand, lane_of))
        print(f"  table de gate voie-rouge (POUR REVUE Franck) → {args.review}", file=sys.stderr)
    if args.publish:
        n = deposit_auto_eligible(cand, lanes, args.publish)
        print(f"  auto-publiés « en veille » (dépôt newsroom, non servi) : {n} → {args.publish}"
              if AUTO_PUBLISH_ENABLED else "  publication auto OFF → rien déposé", file=sys.stderr)
    if args.out and not args.dry_run:
        Path(args.out).write_text(json.dumps(cand, ensure_ascii=False, indent=2) + "\n")
        print(f"  candidats JSON (POUR REVUE, non servis) → {args.out}", file=sys.stderr)
    elif not args.review and not args.publish:
        print(json.dumps(cand, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
