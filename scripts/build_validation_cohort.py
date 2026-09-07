# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Assemble the INTERNAL precursor-validation cohort (T0b) from an unbiased pipeline-project frame.

    python scripts/build_validation_cohort.py --sites sites-eu-pipeline.csv \
        --corpus ../smdc-newsroom/validation/corpus --snapshot ../smdc-newsroom/validation/<date>/baseline-scores-T0b.json \
        --manifest data/validation_study_ids.json [--limit N]

Pipeline (all INTERNAL — the study corpus is NEVER read by build_prod_artifacts; A-19 firewall):
  1. read the OSM pipeline sites (from pipelines.press.osm_projects — inclusion blind to contest)
  2. reverse-geocode each to its ISO country (to pick the spatial adapter)
  3. spatial enrich per country → draft fiches in the ISOLATED study corpus
  4. structural score each draft (engine.scoring.score_datacenter — coords-only, blind to contest)
  5. write the T0b snapshot (same shape as baseline-scores-T0) + arm the manifest with study ids

Study ids are prefixed `study-` so they can NEVER collide with a served corpus id (defence in
depth for the firewall tripwire). The site grade is an INTERNAL exposure variable; publicly the
projects stay « en veille ». Contestation is joined LATER as an outcome, never an inclusion filter.
"""

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from engine.core import load_methodology
from engine.scoring import score_datacenter
from pipelines.spatial import batch
from pipelines.spatial.eu_member import make_eu_member_spec
from pipelines.spatial.registry import get_spec

_NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
_PILLARS = ["energy", "water", "land_biodiversity", "local_impact", "transparency_governance"]


def _country(lat: float, lon: float, *, sleep=time.sleep) -> str | None:
    sleep(1.1)  # Nominatim usage policy: max 1 req/s
    q = urllib.parse.urlencode({"lat": lat, "lon": lon, "format": "json", "zoom": 5})
    req = urllib.request.Request(f"{_NOMINATIM}?{q}",
                                 headers={"User-Agent": "scoremydatacenter-validation/1.0 (research)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            addr = (json.load(r) or {}).get("address") or {}
        return (addr.get("country_code") or "").upper() or None
    except Exception as exc:  # noqa: BLE001 — a geocode miss skips one site, never the run
        print(f"  geocode fail {lat},{lon}: {exc}", file=sys.stderr)
        return None


def _spec_for(iso: str) -> dict:
    """Registered national adapter if we have one, else the generic EU-member socle."""
    try:
        return get_spec(iso)
    except KeyError:
        return make_eu_member_spec(iso)


def _snapshot_item(draft: dict, scored: dict, iso: str, detection_source: str) -> dict:
    idn = draft.get("identity", {})
    coords = idn.get("coordinates", {})
    grades = scored.get("grades", {})
    pd = scored.get("pillar_details", {})
    site = grades.get("site", {})
    return {
        "id": f"study-{draft['id']}",
        "name": idn.get("name"),
        "country": iso,
        "operator": idn.get("operator"),
        "municipality": idn.get("municipality"),
        "project_status": idn.get("project_status"),
        "power_mw": idn.get("power_mw"),
        "grade_site": site.get("grade"),
        "grade_operator": grades.get("project_process", {}).get("grade"),
        "pillars": {p: pd.get(p, {}).get("grade") for p in _PILLARS},
        "confidence": (site.get("documentation") or {}).get("level", "low"),
        "lon": coords.get("lon"),
        "lat": coords.get("lat"),
        "detection_source": detection_source,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", required=True)
    ap.add_argument("--corpus", required=True, help="isolated study corpus dir (private newsroom)")
    ap.add_argument("--snapshot", required=True, help="T0b snapshot json to write")
    ap.add_argument("--manifest", required=True, help="data/validation_study_ids.json to arm")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    rows = list(csv.DictReader(Path(args.sites).read_text().splitlines()))
    if args.limit:
        rows = rows[: args.limit]
    accessed = date.today().isoformat()

    # 1-2. resolve country per site, keep detection_source keyed by rounded coord
    by_iso: dict[str, list[dict]] = {}
    src_by_coord: dict[tuple, str] = {}
    for r in rows:
        try:
            lat, lon = float(r["lat"]), float(r["lon"])
        except (KeyError, ValueError):
            continue
        iso = _country(lat, lon)
        if not iso:
            continue
        src_by_coord[(round(lat, 3), round(lon, 3))] = r.get("detection_source") or "osm"
        by_iso.setdefault(iso, []).append({
            "name": r.get("name"), "operator": r.get("operator"), "lat": lat, "lon": lon,
            "power_mw": float(r["power_mw"]) if r.get("power_mw") else None,
            "project_status": r.get("project_status") or "announced",
        })
    print(f"cohort: {sum(len(v) for v in by_iso.values())} sites in {len(by_iso)} countries: "
          f"{ {k: len(v) for k, v in sorted(by_iso.items())} }", file=sys.stderr)

    # 3. spatial enrich per country → isolated study corpus
    corpus = Path(args.corpus)
    for iso, sites in sorted(by_iso.items()):
        try:
            rep = batch.run(sites, corpus, accessed, _spec_for(iso))
            ok = sum(1 for x in rep["results"] if x.get("ok"))
            print(f"  enrich {iso}: {ok}/{len(sites)} drafts", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 — one country failing must not sink the cohort
            print(f"  enrich {iso} FAILED: {exc}", file=sys.stderr)

    # 4-5. score each draft → snapshot + manifest
    methodology = load_methodology()
    snapshot, ids = {}, []
    for draft_path in sorted(corpus.glob("*.draft.json")):
        draft = json.loads(draft_path.read_text())
        coords = draft.get("identity", {}).get("coordinates", {})
        key = (round(coords.get("lat", 0), 3), round(coords.get("lon", 0), 3))
        iso = (draft.get("identity", {}).get("country") or "").upper()
        try:
            scored = score_datacenter(draft, methodology)
        except Exception as exc:  # noqa: BLE001
            print(f"  score {draft['id']} FAILED: {exc}", file=sys.stderr)
            continue
        item = _snapshot_item(draft, scored, iso, src_by_coord.get(key, "osm"))
        snapshot[item["id"]] = item
        ids.append(item["id"])

    Path(args.snapshot).parent.mkdir(parents=True, exist_ok=True)
    Path(args.snapshot).write_text(json.dumps(snapshot, ensure_ascii=False, indent=1) + "\n")

    # arm the manifest (merge, keep it sorted + unique)
    man = json.loads(Path(args.manifest).read_text())
    man["ids"] = sorted(set(man.get("ids", [])) | set(ids))
    Path(args.manifest).write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")

    dist = {}
    for it in snapshot.values():
        dist[it["grade_site"]] = dist.get(it["grade_site"], 0) + 1
    print(f"\nT0b cohort scored: {len(snapshot)} → {args.snapshot}", file=sys.stderr)
    print(f"  grade_site distribution: {dict(sorted(dist.items(), key=lambda x: str(x[0])))}", file=sys.stderr)
    print(f"  manifest armed: {len(man['ids'])} study ids", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
