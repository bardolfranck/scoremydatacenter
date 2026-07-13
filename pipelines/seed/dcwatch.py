# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Seed exporter for DCWatch (Hubblo) — the starting table of the corpus.

    python -m pipelines.seed.dcwatch --release 2026.04.09 --country FR \
        --exclude-panel ../smdc-newsroom/calibration/datacenters --out seeds/

DCWatch (dcwatch.hubblo.org · gitlab.com/hubblo/datacenter-watch) is Hubblo's
OPEN digital common for data centre footprints: downloadable ODbL data published
as GitLab release archives. NOT to be confused with "Data Center Watch"
(datacenterwatch.org, 10a Labs, US) — a closed commercial product; no relation,
just a similar name.

This module sits UPSTREAM of the one run path: it converts a DCWatch release
into a sites CSV (name,operator,lat,lon,power_mw,project_status) that feeds the
existing `pipelines.spatial.batch` runner — it is a seed exporter, never a new
driver. It writes a provenance sidecar (release tag, ODbL attribution, accessed
date) next to the CSV; the spatial pipeline then re-derives every indicator from
its own primary sources.

ODbL note: extracting a substantial part of the DCWatch database triggers
attribution AND share-alike on any publicly-used derived database. Attribution
is carried by the provenance sidecar; the share-alike implication for our
published artifacts is a pending legal-review item (see JOURNAL 2026-07-13) —
until it is settled, seed output stays a private working file in the newsroom.
"""

import argparse
import csv
import io
import json
import sys
import tarfile
from datetime import date
from pathlib import Path

from ..spatial.http import USER_AGENT, SourceUnavailable, haversine_m

ARCHIVE_URL = "https://gitlab.com/hubblo/datacenter-watch/-/archive/{tag}/datacenter-watch-{tag}.tar.gz"
LICENSE = "ODbL-1.0"
ATTRIBUTION = "DCWatch — Hubblo (gitlab.com/hubblo/datacenter-watch), ODbL"

# DCWatch country names → ISO code (their table mixes full names and codes).
COUNTRY_ISO = {
    "France": "FR", "Belgium": "BE", "Switzerland": "CH", "Luxemburg": "LU",
    "Luxembourg": "LU", "Monaco": "MC", "DE": "DE", "Germany": "DE",
}
# DCWatch progress steps → our project_status vocabulary.
STATUS = {"operating": "operational", "project": "announced"}

# A DCWatch site closer than this to an existing panel entry is the same site.
DEDUP_RADIUS_M = 300.0


def fetch_dump(tag: str, cache_dir: Path) -> Path:
    """Download and extract a release archive once; return the dump/ directory."""
    dump = cache_dir / f"datacenter-watch-{tag}" / "dump"
    if dump.is_dir():
        return dump
    import urllib.request

    url = ARCHIVE_URL.format(tag=tag)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except Exception as exc:
        raise SourceUnavailable(f"{url}: {exc}") from exc
    cache_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        tar.extractall(cache_dir, filter="data")
    if not dump.is_dir():
        raise SourceUnavailable(f"{url}: archive has no dump/ directory")
    return dump


def _read(dump: Path, name: str) -> list[dict]:
    with open(dump / f"{name}.csv", newline="") as fh:
        return list(csv.DictReader(fh))


def load_sites(dump: Path, country: str) -> list[dict]:
    """Join the dump tables into batch-runner site rows for one country."""
    iso = {row["id"]: COUNTRY_ISO.get(row["name"], row["name"]) for row in _read(dump, "countries")}
    steps = {row["id"]: row["name"] for row in _read(dump, "progress_steps")}
    companies = {row["id"]: row["name"] for row in _read(dump, "companies")}
    operator_of: dict[str, str] = {}
    for link in _read(dump, "company_operates_datacenter"):
        # first listed operator wins; the panel review refines multi-operator sites
        operator_of.setdefault(link["datacenter_id"], companies.get(link["company_id"], ""))

    sites = []
    for row in _read(dump, "datacenters"):
        if iso.get(row["country_id"]) != country:
            continue
        if not row["latitude"].strip() or not row["longitude"].strip():
            continue  # the batch runner needs coordinates; nothing to seed without them
        sites.append({
            "name": row["name"].strip(),
            "operator": operator_of.get(row["id"], "").strip() or "UNKNOWN — to fill",
            "lat": float(row["latitude"]),
            "lon": float(row["longitude"]),
            "power_mw": row["power_total_mw"].strip() or "",
            "project_status": STATUS.get(steps.get(row["progress_step_id"], ""), "announced"),
        })
    return sites


def panel_coordinates(panel_dirs: list[Path]) -> list[tuple[float, float, str]]:
    coords = []
    for panel in panel_dirs:
        for path in sorted(panel.glob("*.json")):
            identity = json.loads(path.read_text()).get("identity") or {}
            point = identity.get("coordinates") or {}
            if isinstance(point.get("lat"), (int, float)) and isinstance(point.get("lon"), (int, float)):
                coords.append((point["lat"], point["lon"], identity.get("name") or path.stem))
    return coords


def dedupe(sites: list[dict], known: list[tuple[float, float, str]]) -> tuple[list[dict], list[dict]]:
    fresh, seen = [], []
    for s in sites:
        match = next((n for lat, lon, n in known
                      if haversine_m(s["lat"], s["lon"], lat, lon) <= DEDUP_RADIUS_M), None)
        (seen if match else fresh).append({**s, "panel_match": match} if match else s)
    return fresh, seen


def export(sites: list[dict], out_dir: Path, tag: str, country: str,
           accessed: str, seen: list[dict]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"dcwatch-{tag}-{country.lower()}.csv"
    with open(out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "operator", "lat", "lon", "power_mw", "project_status"])
        writer.writeheader()
        writer.writerows(sites)
    provenance = {
        "source": "DCWatch (Hubblo)",
        "url": ARCHIVE_URL.format(tag=tag),
        "release": tag,
        "license": LICENSE,
        "attribution": ATTRIBUTION,
        "accessed": accessed,
        "country": country,
        "exported": len(sites),
        "already_in_panel": [{"name": s["name"], "panel_match": s["panel_match"]} for s in seen],
    }
    out.with_suffix(".provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export a DCWatch (Hubblo) release as a spatial-batch sites CSV.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--release", help="GitLab release tag to download (e.g. 2026.04.09)")
    src.add_argument("--dump", type=Path, help="already-extracted dump/ directory (offline runs, tests)")
    ap.add_argument("--country", default="FR", help="ISO country code to export (default FR)")
    ap.add_argument("--exclude-panel", type=Path, action="append", default=[],
                    help="newsroom panel dir; sites within 300 m of an existing entry are set aside (repeatable)")
    ap.add_argument("--out", type=Path, default=Path("seeds"), help="output directory")
    ap.add_argument("--cache", type=Path, default=Path(".cache/dcwatch"), help="release download cache")
    args = ap.parse_args(argv)

    dump = args.dump if args.dump else fetch_dump(args.release, args.cache)
    tag = args.release or dump.parent.name.removeprefix("datacenter-watch-")
    sites = load_sites(dump, args.country.upper())
    fresh, seen = dedupe(sites, panel_coordinates(args.exclude_panel))
    out = export(fresh, args.out, tag, args.country.upper(), date.today().isoformat(), seen)

    print(f"DCWatch {tag} · {args.country.upper()}: {len(sites)} sites, "
          f"{len(seen)} already in panel, {len(fresh)} exported -> {out}")
    print(f"  license: {LICENSE} — attribution + share-alike; provenance sidecar written.")
    print(f"  next: uv run python -m pipelines.spatial.batch {out} --country {args.country.upper()} --out <drafts>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
