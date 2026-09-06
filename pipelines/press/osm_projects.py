# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Neutral, UNBIASED discovery of EU data-center PIPELINE projects from OpenStreetMap.

    python -m pipelines.press.osm_projects --out sites-eu-pipeline.csv

WHY (validation cohort, pre-registration « note = indicateur avancé », 2026-09-05): the
precursor study needs a cohort of pipeline DC projects whose INCLUSION never looked at whether
the project is contested — otherwise it is selection-on-outcome and any "signal" is an artefact.
OSM is the unbiased frame: volunteers map a proposed/under-construction data center whether or not
anyone opposes it, and the tag carries COORDINATES — all the structural scorer needs (no LLM).

Contestation is joined LATER as an OUTCOME, never as an inclusion filter (R&D invariant).

Every row carries `detection_source` (osm_construction / osm_proposed) so R&D can run a
per-channel robustness check — no source is perfectly neutral (a DC is only mapped when someone
cares), and the tag lets the study test whether the association holds within one channel alone.

DETECTION only, like every press/OSM record (A-21): a triage lead, never a score input.
"""

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request

# Public Overpass mirrors — tried in order; a slow/429 mirror falls through to the next.
_OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

# Continental-EU bounding box (S, W, N, E). Wide enough for IE/PT west to the eastern members and
# FI/SE north; the spatial enrichment (--country EU) scopes the actual member set downstream.
_EU_BBOX = (34.0, -25.0, 72.0, 45.0)

# Pipeline = NOT-yet-operational. OSM expresses this with lifecycle prefixes (construction:/
# proposed:) or a construction=* / future start_date on an otherwise-tagged data center. We do NOT
# select plain operational `man_made=data_center` (those are the running fleet, not the pipeline).
_LICENSE = "OpenStreetMap contributors, ODbL 1.0"


def _overpass_query(bbox=_EU_BBOX) -> str:
    s, w, n, e = bbox
    b = f"{s},{w},{n},{e}"
    clauses = []
    for key in ("man_made", "telecom"):
        clauses += [
            f'nwr["construction:{key}"="data_center"]({b});',
            f'nwr["proposed:{key}"="data_center"]({b});',
            f'nwr["{key}"="data_center"]["construction"]({b});',
            f'nwr["{key}"="data_center"]["start_date"]({b});',
        ]
    return f"[out:json][timeout:180];\n(\n  " + "\n  ".join(clauses) + "\n);\nout center tags;"


def _fetch_overpass(query: str, *, sleep=time.sleep, retries: int = 2) -> dict:
    """POST the query to Overpass, falling through mirrors and backing off on transient failure."""
    data = query.encode("utf-8")
    last = None
    for endpoint in _OVERPASS_ENDPOINTS:
        for attempt in range(retries):
            try:
                req = urllib.request.Request(
                    endpoint, data=data,
                    headers={"User-Agent": "scoremydatacenter-validation/1.0 (research cohort)"},
                )
                with urllib.request.urlopen(req, timeout=200) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last = exc
                if attempt < retries - 1:
                    sleep(5 * (attempt + 1))
    raise RuntimeError(f"Overpass unreachable on all mirrors: {last}")


def _future_start(tags: dict, today: str) -> bool:
    """True iff start_date is a parseable date STRICTLY IN THE FUTURE.

    A bare start_date is unreliable as a pipeline signal: on an operational DC it records the PAST
    commissioning date (ForHLR II, Leonardo, ECMWF all came back this way). Only a future date is
    a planned/not-yet-built signal — a past one means operational and must NOT enter the pipeline
    cohort (it would pollute the frame with the running fleet)."""
    sd = (tags.get("start_date") or "").strip()
    if not sd:
        return False
    # OSM start_date is often just a year, sometimes YYYY-MM or YYYY-MM-DD. Compare left-padded.
    return sd[:10] > today[:10] or (len(sd) == 4 and sd > today[:4])


def _status_and_source(tags: dict) -> tuple[str, str]:
    """Map OSM lifecycle tags → (project_status, detection_source). Blind to contestation."""
    if any(k.startswith("construction:") for k in tags) or tags.get("construction") not in (None, "no"):
        return "under_construction", "osm_construction"
    # proposed:* prefix, or a future start_date → an announced/planned project
    return "announced", "osm_proposed"


def _is_pipeline(tags: dict, today: str) -> bool:
    """Keep NOT-yet-operational data centers only; drop dead/operational lifecycles.

    Reliable pipeline signals: construction:*/proposed:* lifecycle prefixes, construction=* (not
    'no'), or a FUTURE start_date. A past/absent start_date on a plain data_center = operational."""
    if any(tags.get(k) in ("yes", "1", "true") for k in ("disused", "abandoned", "demolished", "razed")):
        return False
    if any(k.startswith(("disused:", "abandoned:", "demolished:", "razed:")) for k in tags):
        return False
    return (
        any(k.startswith(("construction:", "proposed:")) for k in tags)
        or tags.get("construction") not in (None, "no")
        or _future_start(tags, today)
    )


def _element_coords(el: dict) -> tuple[float, float] | None:
    if el.get("type") == "node":
        return el.get("lat"), el.get("lon")
    c = el.get("center") or {}
    if c.get("lat") is not None and c.get("lon") is not None:
        return c["lat"], c["lon"]
    return None


def collect(bbox=_EU_BBOX, *, fetch=_fetch_overpass, today: str | None = None) -> list[dict]:
    """EU pipeline DC projects from OSM → rows the spatial batch consumes, each with provenance.

    Row: name, operator, lat, lon, power_mw, project_status, detection_source, source_url, license.
    """
    from datetime import date
    today = today or date.today().isoformat()
    payload = fetch(_overpass_query(bbox))
    rows, seen = [], set()
    for el in payload.get("elements", []):
        tags = el.get("tags") or {}
        if not _is_pipeline(tags, today):
            continue
        coords = _element_coords(el)
        if not coords or coords[0] is None:
            continue
        lat, lon = float(coords[0]), float(coords[1])
        # Dedupe within OSM by rounded coord (~100 m) — the same site mapped as node + way.
        key = (round(lat, 3), round(lon, 3))
        if key in seen:
            continue
        seen.add(key)
        status, source = _status_and_source(tags)
        # Every name carries its OSM element ref (globally unique) so the derived fiche id is ALWAYS
        # unique — two distinct sites sharing an operator+commune (e.g. two Digital Realty Frankfurt
        # halls) would otherwise slug to one id and overwrite each other. Internal study cohort:
        # correctness of the id beats a pretty name.
        base = (tags.get("name") or tags.get("official_name")
                or tags.get("construction:name") or "data center").strip() or "data center"
        name = f"{base} OSM {el.get('type')} {el.get('id')}"
        operator = (tags.get("operator") or tags.get("brand")
                    or tags.get("owner") or "").strip() or "UNKNOWN — to fill"
        pw = tags.get("power_mw") or tags.get("plant:output:electricity")
        try:
            power_mw = float(str(pw).split()[0]) if pw else None
        except (ValueError, IndexError):
            power_mw = None
        rows.append({
            "name": name,
            "operator": operator,
            "lat": lat,
            "lon": lon,
            "power_mw": power_mw,
            "project_status": status,
            "detection_source": source,
            "source_url": f"https://www.openstreetmap.org/{el.get('type')}/{el.get('id')}",
            "license": _LICENSE,
        })
    return rows


def _write(rows: list[dict], out: str) -> None:
    if out.endswith(".json"):
        with open(out, "w") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
        return
    cols = ["name", "operator", "lat", "lon", "power_mw", "project_status",
            "detection_source", "source_url", "license"]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Collect EU pipeline DC projects from OSM (unbiased frame).")
    ap.add_argument("--out", default="sites-eu-pipeline.csv", help="CSV (batch input) or .json")
    args = ap.parse_args(argv)
    rows = collect()
    _write(rows, args.out)
    by_src = {}
    for r in rows:
        by_src[r["detection_source"]] = by_src.get(r["detection_source"], 0) + 1
    print(f"osm_projects: {len(rows)} EU pipeline DC projects → {args.out}", file=sys.stderr)
    print(f"  by detection_source: {by_src}", file=sys.stderr)
    named = sum(1 for r in rows if not r["operator"].startswith("UNKNOWN"))
    print(f"  with named operator: {named}/{len(rows)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
