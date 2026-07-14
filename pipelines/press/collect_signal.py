# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Harvest the four open contestation-signal feeds into a DRAFT watchlist (facts, never a grade).

    python -m pipelines.press.collect_signal --out ../smdc-newsroom/drafts/watchlist
    python -m pipelines.press.collect_signal --gdelt-query 'datacenter (opposition OR moratorium)'

Output (private newsroom, human-reviewed before any publication):
  * watchlist.draft.geojson    — geolocated sourced facts from uMap (FR) + fights (US) + moratoria
                                 (US). Each feature is "En veille": facts + source, NO letter,
                                 NO confidence (A-19 / A-21). The engine never reads this.
  * press_detections.draft.json — GDELT articles for --gdelt-query (DETECTION only, for triage).
  * _signal_coverage.md        — per-source counts.

It PROPOSES; it never publishes. A matched entry is a sourced fact for review, not a score — the
letter still moves only on the voie-A procedural facts (T1). See RECON-contestation-signal.md.
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

from . import signal


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def _dedupe_key(rec: dict):
    """Same project seen in two feeds → one entry. Key on country + rounded coords, else name."""
    c = rec.get("coordinates")
    if c and c.get("lat") is not None and c.get("lon") is not None:
        return (rec.get("country"), round(c["lat"], 3), round(c["lon"], 3))
    return (rec.get("country"), _norm(rec.get("name") or ""))


def harvest(accessed: str, *, gdelt_query: str | None = None,
            countries: tuple[str, ...] = ()) -> tuple[list[dict], list[dict], dict]:
    """Return (watchlist_records, press_detections, per_source_counts).

    `countries` adds per-country GDELT press detection (declarative specs in
    signal.GDELT_COUNTRY_SPECS) — the generalization path for countries with no geo feed (CA…).
    """
    geo = signal.fetch_umap_layers(accessed) + signal.fetch_fights(accessed) + signal.fetch_moratoria(accessed)
    counts = {}
    for r in geo:
        counts[r["source"]] = counts.get(r["source"], 0) + 1

    # Dedupe, merging sources/groups when the same site appears in more than one feed.
    merged: dict = {}
    for r in geo:
        k = _dedupe_key(r)
        if k in merged:
            m = merged[k]
            m["sources"] = list(dict.fromkeys((m.get("sources") or []) + (r.get("sources") or [])))
            m.setdefault("also_in", []).append(r["source"])
            if not m.get("opposition_groups") and r.get("opposition_groups"):
                m["opposition_groups"] = r["opposition_groups"]
        else:
            merged[k] = dict(r)
    watchlist = list(merged.values())

    press = signal.fetch_gdelt(gdelt_query, accessed) if gdelt_query else []
    counts["gdelt"] = len(press)
    for iso in countries:
        found = signal.fetch_gdelt_country(iso, accessed)
        press += found
        counts[f"gdelt-{iso.lower()}"] = len(found)
    counts["_watchlist_after_dedupe"] = len(watchlist)
    return watchlist, press, counts


def _to_geojson(records: list[dict]) -> dict:
    """FeatureCollection of "En veille" entries — facts only. No grade/letter/confidence field."""
    features = []
    for r in records:
        c = r.get("coordinates")
        geometry = ({"type": "Point", "coordinates": [c["lon"], c["lat"]]}
                    if c and c.get("lat") is not None and c.get("lon") is not None else None)
        props = {k: v for k, v in r.items() if k != "coordinates"}
        props["watchlist_status"] = "en_veille"   # sourced facts only; never scored (A-19)
        features.append({"type": "Feature", "geometry": geometry, "properties": props})
    return {
        "type": "FeatureCollection",
        "_note": "DRAFT contestation signal — sourced facts, NO grade (A-19/A-21). "
                 "Propose only; human review before any publication. The engine never reads this.",
        "features": features,
    }


def _coverage(counts: dict) -> str:
    lines = ["# Contestation-signal coverage (voie B — draft)", "",
             "| Source | Records |", "|--------|---------|"]
    labels = {"umap-fr": "uMap FR (opposition + projects)", "us-fights": "US fights (CC BY 4.0)",
              "us-moratorium": "US moratoria (CC BY 4.0)", "gdelt": "GDELT press detection",
              "_watchlist_after_dedupe": "**watchlist entries (deduped)**"}
    ordered = ["umap-fr", "us-fights", "us-moratorium", "gdelt"]
    ordered += sorted(k for k in counts if k.startswith("gdelt-"))     # per-country detections
    ordered.append("_watchlist_after_dedupe")
    for key in ordered:
        if key in counts:
            label = labels.get(key) or f"GDELT press detection ({key.split('-', 1)[1].upper()})"
            lines.append(f"| {label} | {counts[key]} |")
    lines += ["", "Facts only, no grade. Draft for human review (A-19/A-21)."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Harvest open contestation-signal feeds into a draft watchlist.")
    p.add_argument("--out", default="../smdc-newsroom/drafts/watchlist",
                   help="Directory for the draft artifacts (private newsroom).")
    p.add_argument("--gdelt-query", default=None,
                   help="If set, fetch GDELT press-detection articles for this query (detection only).")
    p.add_argument("--country", action="append", default=[], metavar="ISO",
                   help="Add per-country GDELT press detection (spec in signal.GDELT_COUNTRY_SPECS). "
                        "Repeatable: --country CA --country …")
    args = p.parse_args(argv)

    accessed = date.today().isoformat()
    watchlist, press, counts = harvest(accessed, gdelt_query=args.gdelt_query,
                                       countries=tuple(args.country))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "watchlist.draft.geojson").write_text(
        json.dumps(_to_geojson(watchlist), indent=2, ensure_ascii=False) + "\n")
    if args.gdelt_query is not None or args.country:
        (out_dir / "press_detections.draft.json").write_text(
            json.dumps(press, indent=2, ensure_ascii=False) + "\n")
    report = _coverage(counts)
    (out_dir / "_signal_coverage.md").write_text(report + "\n")

    print(report, file=sys.stderr)
    print(f"\nWrote {len(watchlist)} watchlist draft entries → {out_dir}", file=sys.stderr)
    if args.gdelt_query is not None or args.country:
        print(f"Wrote {len(press)} press detections → {out_dir}", file=sys.stderr)
    print("Facts only, no grade. Propose only — human review before any publication (A-19/A-21).",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
