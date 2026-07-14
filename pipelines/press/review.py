# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""watchlist-reviewer scaffold — turn raw harvester drafts into a REVIEW QUEUE (A-07).

The mechanical half of the 5-step review. For each raw watchlist feature it:
  1. reduces the rich harvester record to the LIGHT published shape (A-19 refinement) —
     identity + entry-level source + facts[] (contestation shape), facts empty for a bare
     announced project;
  2. raises mechanical flags (missing/out-of-country coords, NC licence, self-reported count,
     no name) and routes each entry to `agent` (needs source-verification + neutral {fr,en}
     label) or `human` (a hard flag needs a person);
  3. emits `watchlist.review.jsonl` (one proposal per line) + `_review_flags.md`.

It PROPOSES; it NEVER publishes. Every row carries `auto_published: false`. It writes no grade,
letter, score, or confidence — the label-polishing and the "does this source support the claim"
verdict are the LLM reviewer's job (see REVIEW.md), and a human validates before anything is
published (A-07 / A-15). Stdlib only; the optional --check-links pass is the only network use.
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

# Rough national bounding boxes — only to catch GROSS geolocation errors, not for precision.
_BBOX = {
    "FR": (41.0, 51.6, -5.6, 9.9),      # metropolitan France
    "US": (24.0, 49.5, -125.0, -66.5),  # contiguous US
}
# harvester kind → contestation fact kind (announced_project carries no fact)
_KIND_MAP = {"opposition": "opposition", "moratorium": "moratorium", "article": "press"}
_FEED_TITLE = {
    "umap-fr": "Presse / collectif — opposition recensée (carte communautaire)",
    "us-fights": "Data Center Tracker (fights dataset)",
    "us-moratorium": "US data-center moratorium inventory",
    "gdelt": "Press (GDELT index)",
}


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _templated_label(feed: str, fact_kind: str, raw_facts: dict) -> dict | None:
    """Neutral bilingual label from a STRUCTURED feed's own fields — deterministic, no judgment.

    Dataset values (status, outcome, jurisdiction type) are quoted verbatim: they are the feed's
    facts, and translating them would editorialize. Returns None for unstructured feeds → the
    raw-name proposal + LLM-reviewer path applies unchanged.
    """
    if feed == "us-fights" and fact_kind == "opposition":
        status = raw_facts.get("status")
        outcome = raw_facts.get("community_outcome")
        en = "Locally contested data-center project (named opposition groups)"
        fr = "Projet de data center contesté localement (collectifs d'opposition nommés)"
        if status:
            en += f" — status: {status}"
            fr += f" — statut : {status}"
        if outcome:
            en += f"; outcome: {outcome}"
            fr += f" ; issue : {outcome}"
        return {"fr": fr, "en": en}
    if feed == "us-moratorium" and fact_kind == "moratorium":
        jt = raw_facts.get("jurisdiction_type")
        enacted = raw_facts.get("date_enacted")
        days = raw_facts.get("duration_days")
        en, fr = "Data-center moratorium", "Moratoire sur les data centers"
        if jt:
            en += f" — {jt}"
            fr += f" — {jt}"
        if enacted:
            en += f", enacted {enacted}"
            fr += f", adopté le {enacted}"
        if days:
            en += f", {days} days"
            fr += f", {days} jours"
        return {"fr": fr, "en": en}
    return None


def _in_bbox(country: str, lat, lon) -> bool | None:
    box = _BBOX.get(country)
    if not box or lat is None or lon is None:
        return None                                   # unknown country/coords → can't judge
    s, n, w, e = box
    return s <= lat <= n and w <= lon <= e


def reduce_entry(props: dict, coords: list | None) -> dict:
    """Raw harvester feature → the proposed LIGHT watchlist entry (facts[] may be empty)."""
    country = props.get("country")
    name = (props.get("name") or "").strip()
    feed = props.get("source")
    lat = coords[1] if coords else None
    lon = coords[0] if coords else None

    urls = props.get("sources") or ([props.get("source_url")] if props.get("source_url") else [])
    entry_source = {
        "title": _FEED_TITLE.get(feed, feed),
        "url": urls[0] if urls else None,
        "accessed": props.get("retrieved"),
        # archived_url is added at PUBLISH time by the archive step (A-20) — never here.
    }

    facts = []
    fact_kind = _KIND_MAP.get(props.get("kind"))
    if fact_kind:
        # Structured US feeds carry enough fields for a DETERMINISTIC neutral bilingual label
        # (dataset values quoted verbatim — facts, not prose). Unstructured feeds keep the raw
        # name as a proposal the LLM reviewer must neutralize + translate.
        templated = _templated_label(feed, fact_kind, props.get("facts") or {})
        facts.append({
            "kind": fact_kind,
            "label": templated or {"fr": name or None, "en": None},
            "_label_status": "templated" if templated else "proposed_raw",
            "source": dict(entry_source),
            "self_reported": False,
        })
    # a self-reported petition count becomes its OWN flagged fact, never a score input
    if (props.get("facts") or {}).get("petition_signatures_self_reported") not in (None, "", 0):
        facts.append({
            "kind": "petition",
            "label": {"fr": "Pétition en ligne (nombre auto-déclaré)", "en": "Online petition (self-reported count)"},
            "_label_status": "proposed_raw",
            "source": dict(entry_source),
            "self_reported": True,
        })

    project_status = props.get("status") if props.get("kind") == "announced_project" else None
    entry = {
        "id": f"{(country or 'xx').lower()}-{_slug(name) or 'unnamed'}",
        "name": name,
        "country": country,
        "coordinates": ({"lat": lat, "lon": lon} if lat is not None and lon is not None else None),
        "project_status": project_status,
        "source": entry_source,                       # entry-level provenance (justifies listing)
        "facts": facts,                               # may be [] for a bare announced project
    }
    return entry


def flags_for(props: dict, entry: dict) -> list[str]:
    flags = []
    c = entry["coordinates"]
    if c is None:
        flags.append("missing_coords")
    elif _in_bbox(entry["country"], c["lat"], c["lon"]) is False:
        flags.append("geoloc_out_of_country")
    if not entry["name"]:
        flags.append("no_name")
    if props.get("source") == "umap-fr":
        flags.append("license_nc_umap")               # NC upstream — clear before commercial reuse
    if any(f.get("self_reported") for f in entry["facts"]):
        flags.append("self_reported_count")
    if not entry["source"].get("url"):
        flags.append("no_source_url")
    return flags


_HARD_FLAGS = {"geoloc_out_of_country", "no_name", "no_source_url"}


def review_feature(feature: dict) -> dict:
    props = feature.get("properties") or {}
    coords = (feature.get("geometry") or {}).get("coordinates")
    entry = reduce_entry(props, coords)
    flags = flags_for(props, entry)
    return {
        "proposed": entry,
        "flags": flags,
        # hard flag → a human must look; otherwise the LLM reviewer verifies source + writes label
        "route": "human" if _HARD_FLAGS & set(flags) else "agent",
        "needs_label_work": any(f.get("_label_status") == "proposed_raw" for f in entry["facts"]),
        "auto_published": False,                      # load-bearing: this tool never publishes
        "raw_ref": {"feed": props.get("source"), "name": props.get("name")},
    }


def build_queue(features: list[dict]) -> list[dict]:
    return [review_feature(f) for f in features]


def flags_report(queue: list[dict]) -> str:
    by_flag, by_route, by_country = {}, {}, {}
    for item in queue:
        by_route[item["route"]] = by_route.get(item["route"], 0) + 1
        cty = item["proposed"]["country"] or "??"
        by_country[cty] = by_country.get(cty, 0) + 1
        for f in item["flags"]:
            by_flag[f] = by_flag.get(f, 0) + 1
    lines = [f"# Watchlist review queue — {len(queue)} entries", "",
             "PROPOSALS ONLY — nothing is published. A human validates before publication (A-07).", "",
             "## Routing", "| route | count |", "|-------|-------|"]
    for r, n in sorted(by_route.items()):
        lines.append(f"| {r} | {n} |")
    lines += ["", "## By country", "| country | count |", "|---------|-------|"]
    for c, n in sorted(by_country.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {c} | {n} |")
    lines += ["", "## Flags raised", "| flag | count |", "|------|-------|"]
    for f, n in sorted(by_flag.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {f} | {n} |")
    lines += ["", "`agent` = LLM reviewer verifies the source & writes the neutral fr/en label; "
              "`human` = a hard flag (geoloc, no name, no source) needs a person. Neither publishes."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build a watchlist review queue from harvester drafts.")
    p.add_argument("draft", help="Path to watchlist.draft.geojson")
    p.add_argument("--out", default=None, help="Output dir (default: alongside the draft).")
    args = p.parse_args(argv)

    draft_path = Path(args.draft)
    fc = json.loads(draft_path.read_text())
    queue = build_queue(fc.get("features") or [])

    out_dir = Path(args.out) if args.out else draft_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "watchlist.review.jsonl").open("w") as fh:
        for item in queue:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    report = flags_report(queue)
    (out_dir / "_review_flags.md").write_text(report + "\n")

    print(report, file=sys.stderr)
    print(f"\nWrote {len(queue)} review proposals → {out_dir}/watchlist.review.jsonl", file=sys.stderr)
    print("Proposals only — nothing published. LLM reviewer + human validate before publication.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
