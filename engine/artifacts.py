# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Generated artifacts — the data contract of the site (and of the future API).

Deterministic by construction: no timestamps, no environment values. The same
repository content always produces byte-identical artifacts (this is tested).
"""

import re
from pathlib import Path

from .core import ARTIFACTS_DIR, GateError, load_watchlist, write_json
from .scoring import reply_deadline, score_datacenter

# Gate 7 extended to generated prose (2026-07-10): a grade must never be rendered
# outside <ScoreBadge> — including inside the LLM-written synthesis. Prose citing a
# letter duplicates computed state and is guaranteed to drift at the next methodology
# revision (seen live: an accroche pinned at "site C, piliers D" rendered next to
# recomputed badges saying D and E). The letter belongs to the badge; the prose
# carries the *why*, never the letter.
_GRADE_IN_PROSE = re.compile(
    r"(?:\bnote\b[^.!?]{0,80}?|\bnoté[e]?s?\s+|\bpilier[s]?\b[^.!?]{0,80}?|\bgrade[sd]?\b[^.!?]{0,40}?"
    r"|\brated\s+|\bpillar[s]?\b[^.!?]{0,80}?|\bscored?\s+)(?<![A-Za-zÀ-ÿ])([A-E])(?![A-Za-zÀ-ÿ0-9+])"
)


def synthesis_grade_citations(dc: dict) -> list[str]:
    """Return every grade-letter citation found in the DC's synthesis prose."""
    hits = []
    for badge, texts in (dc.get("synthesis") or {}).items():
        if not isinstance(texts, dict):
            continue
        for lang, text in texts.items():
            if not isinstance(text, str):
                continue
            for m in _GRADE_IN_PROSE.finditer(text):
                hits.append(f"{dc['id']}: synthesis.{badge}.{lang} cites grade {m.group(1)!r} in prose ({m.group(0)!r})")
    return hits


def _summary(dc: dict, result: dict) -> dict:
    identity = dc["identity"]
    pub = dc.get("publication") or {}
    return {
        "id": dc["id"],
        "name": identity["name"],
        "operator": identity["operator"],
        "municipality": identity["municipality"],
        "country": identity["country"],
        "project_status": identity["project_status"],
        "power_mw": identity.get("power_mw"),
        # commissioning year (identity.vintage) — the ranking sorts on it; null = not disclosed
        "expected_commissioning": (identity.get("vintage") or {}).get("expected_commissioning"),
        "grades": result["grades"],
        "confidence": result["confidence"],
        "pillars": result["pillars"],
        "citable_quote": result["citable_quote"],
        # Publication doctrine A-26: letter + score are public in every state; the deadline
        # (notification + NOTICE_DAYS, deterministic) drives the "right of reply in progress"
        # display. The clock lives in the view, never in the data.
        "publication_status": pub.get("status"),
        "reply_deadline": reply_deadline(pub.get("operator_notified_at")),
    }


def _watchlist_kind(entry: dict) -> str:
    """Feature-level marker kind, derived from the entry's facts (facts stay untouched).

    moratorium (official act) > opposition (citizen signal) > announced_project (bare listing).
    """
    kinds = {f.get("kind") for f in (entry.get("facts") or [])}
    if "moratorium" in kinds:
        return "moratorium"
    if "opposition" in kinds:
        return "opposition"
    return "announced_project"


def build_artifacts(datacenters: dict[str, dict], methodology: dict,
                    out_dir: Path = ARTIFACTS_DIR, watchlist: list[dict] | None = None) -> dict[str, dict]:
    """Score every DC and write all artifacts. Returns the per-DC results."""
    if watchlist is None:
        watchlist = load_watchlist()
    # Gate 7 (prose): refuse to emit an artifact whose synthesis cites grade letters —
    # the incoherent "stale letter next to a recomputed badge" state is impossible.
    prose_violations = [v for dc in datacenters.values() for v in synthesis_grade_citations(dc)]
    if prose_violations:
        raise GateError(
            "GATE 7 (prose): a grade letter is never rendered outside <ScoreBadge> — strip it "
            "from the synthesis (the badge carries the letter, the prose carries the why):\n  - "
            + "\n  - ".join(prose_violations)
        )
    results = {dc_id: score_datacenter(dc, methodology) for dc_id, dc in sorted(datacenters.items())}

    labels = {i["id"]: i["label"] for i in methodology["indicators"]}
    scores, features, audit = [], [], []

    for dc_id, dc in sorted(datacenters.items()):
        result = results[dc_id]
        scores.append(_summary(dc, result))

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [dc["identity"]["coordinates"]["lon"], dc["identity"]["coordinates"]["lat"]],
            },
            "properties": {
                "id": dc_id,
                "name": dc["identity"]["name"],
                "grade_site": result["grades"]["site"]["grade"],
                "grade_project_process": result["grades"]["project_process"]["grade"],
                # A-25: only emitted when the letter was capped from A (keeps zz fixtures byte-stable).
                **({"reserved_site": True} if result["grades"]["site"].get("reserved_from") == "A" else {}),
                **({"reserved_pp": True} if result["grades"]["project_process"].get("reserved_from") == "A" else {}),
                "confidence": result["confidence"]["level"],
                "power_mw": dc["identity"].get("power_mw"),
                "project_status": dc["identity"]["project_status"],
                # A richer popup than two letters: per-pillar grades + the generated
                # citable line (the map teaser that makes people click through).
                "pillars": [{"id": p["id"], "grade": result["pillars"][p["id"]]["grade"]}
                            for p in methodology["pillars"]],
                "quote_fr": result["citable_quote"]["fr"],
                "publication_status": dc["publication"]["status"],
                "reply_deadline": reply_deadline(dc["publication"]["operator_notified_at"]),
            },
        })

        indicator_detail = []
        entries = {e["id"]: e for e in dc["indicators"]}
        for ind in methodology["indicators"]:
            if not ind["mvp"]:
                continue
            entry = entries[ind["id"]]
            indicator_detail.append({
                "id": ind["id"],
                "label": labels[ind["id"]],
                "pillar": ind["pillar"],
                "block": ind["block"],
                "status": entry["status"],
                "value": entry.get("value"),
                "proxies": entry.get("proxies"),
                "score": result["indicators"][ind["id"]],
                "source": entry.get("source"),
                "verification_source": entry.get("verification_source"),
            })

        write_json(out_dir / "dc" / f"{dc_id}.json", {
            **_summary(dc, result),
            "summary": dc["identity"]["summary"],
            "vintage": dc["identity"].get("vintage"),
            "admin_area": dc["identity"].get("admin_area"),
            "indicators": indicator_detail,
            "publication": dc["publication"],
            "score_history": dc["score_history"],
            # Contestation signal (A-21): sourced facts published next to the note,
            # never an input to the grade. Passed through untouched.
            "contestation": dc.get("contestation"),
            # Narrative synthesis: written by the WORKFLOW's LLM redaction phase
            # AFTER scoring, then stored on the source DC. The engine only passes
            # it through — never computed at render, never re-derived here.
            "synthesis": dc.get("synthesis"),
        })

        audit += [{"dc_id": dc_id, "dc_name": dc["identity"]["name"], **event} for event in dc["score_history"]]

    # Watchlist (A-19): world "En veille" projects — sourced facts, NO grade.
    # The engine never scores these; it only passes the facts through to the map.
    watch_features = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [e["coordinates"]["lon"], e["coordinates"]["lat"]]},
        "properties": {
            "id": e["id"],
            "name": e["name"],
            "operator": e.get("operator"),
            "municipality": e.get("municipality"),
            "country": e["country"],
            "project_status": e.get("project_status"),
            "watchlist_status": "en_veille",
            # Derived marker kind so the map can style flat (styling on the nested facts[]
            # array is impractical in MapLibre expressions). A moratorium is an OFFICIAL act —
            # it outranks an opposition signal when an entry carries both. Never a grade.
            "kind": _watchlist_kind(e),
            "source": e["source"],
            "facts": e.get("facts") or [],
        },
    } for e in watchlist]

    write_json(out_dir / "scores.json", scores)
    write_json(out_dir / "map.geojson", {"type": "FeatureCollection", "features": features})
    write_json(out_dir / "watchlist.geojson", {"type": "FeatureCollection", "features": watch_features})
    write_json(out_dir / "audit.json", sorted(audit, key=lambda e: (e["date"], e["dc_id"])))
    write_json(out_dir / "methodology.json", methodology)
    return results
