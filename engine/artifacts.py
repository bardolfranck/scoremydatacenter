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

# A-28: the credit travels WITH the data — every object artifact carries it
# (scores.json/audit.json are arrays: adding a key would break consumers;
# the site footer and the fiche pages carry the credit for those).
CREDIT = "scoremydatacenter.org · data: licence by source (ODbL, Licence Ouverte…) · methodology CC BY-SA 4.0"
from .scoring import score_datacenter
from .stats import build_stats
from .indices import build_indices, update_history
from .showcase import build_showcase

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
            # `lead` is per-language now ({fr,en}); flatten one nested level so a grade letter in a
            # localized title is caught, not skipped. Body fields stay plain strings.
            fields = text.items() if isinstance(text, dict) else [(lang, text)]
            for sublang, value in fields:
                if not isinstance(value, str):
                    continue
                for m in _GRADE_IN_PROSE.finditer(value):
                    hits.append(f"{dc['id']}: synthesis.{badge}.{sublang} cites grade "
                                f"{m.group(1)!r} in prose ({m.group(0)!r})")
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
        # Direct publication (2026-07-15, legal review): lifecycle is draft -> published.
        "publication_status": pub.get("status"),
    }


def _watchlist_kind(entry: dict) -> str:
    """Feature-level marker kind, derived from the entry's facts (facts stay untouched).

    moratorium (official act) > opposition (citizen/legal contestation) > announced_project
    (bare listing). A legal `appeal` is a contestation signal — it maps to the opposition
    marker, not to the neutral "just announced" pin.
    """
    kinds = {f.get("kind") for f in (entry.get("facts") or [])}
    if "moratorium" in kinds:
        return "moratorium"
    if kinds & {"opposition", "appeal", "petition"}:
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

        # ── Anti-pillage (Franck 2026-07-22): map.geojson is the ONE data file
        # the site MUST serve publicly (the map fetches it client-side), so it
        # is the paywall's real frontier. It carries ONLY the free "Seau A"
        # floor — the identity + the site LETTER — and NOTHING sellable. Dropped
        # here (premium, Seau B, sold via the API): operator grade, per-pillar
        # scores, exact power_mw, the citable quote, confidence, precise GPS.
        # Coordinates are rounded to ~1 km (2 decimals); a coarse size_tier
        # keeps the map's dot-sizing without disclosing the MW figure.
        coords = dc["identity"]["coordinates"]
        mw = dc["identity"].get("power_mw")
        size_tier = 0 if not isinstance(mw, (int, float)) else (1 if mw < 10 else 2 if mw < 50 else 3)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(coords["lon"], 2), round(coords["lat"], 2)],
            },
            "properties": {
                "id": dc_id,
                "name": dc["identity"]["name"],
                "operator": dc["identity"]["operator"],
                "municipality": dc["identity"]["municipality"],
                "country": dc["identity"]["country"],
                "grade_site": result["grades"]["site"]["grade"],
                # A-25 reserve is part of the public letter's presentation, not a sold field.
                **({"reserved_site": True} if result["grades"]["site"].get("reserved_from") == "A" else {}),
                "project_status": dc["identity"]["project_status"],
                "size_tier": size_tier,
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
            "credit": CREDIT,
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
        # Coords rounded to ~1 km like the graded layer (no precise GPS in a public file).
        "geometry": {"type": "Point", "coordinates": [round(e["coordinates"]["lon"], 2), round(e["coordinates"]["lat"], 2)]},
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
    # T0 « Les chiffres du parc » — corpus aggregates, one file per build
    # (cadrage §4.10). Data only: labels and editorial framing live site-side.
    write_json(out_dir / "stats.json", build_stats(datacenters, methodology, watchlist, results))
    # Country SITE index (brief 2026-07-18/19): artifact + append-only history.
    indices = build_indices(datacenters, methodology, results)
    write_json(out_dir / "indices.json", indices)
    write_json(out_dir / "indices_history.json", update_history(indices, out_dir / "indices_history.json"))
    # Home showcase (2026-07-20): who appears on the front page is a RULE,
    # not an accident of filtering — the engine ranks, the site renders.
    write_json(out_dir / "home_showcase.json", build_showcase(datacenters, results, watchlist))
    write_json(out_dir / "map.geojson", {"type": "FeatureCollection", "credit": CREDIT, "features": features})
    write_json(out_dir / "watchlist.geojson", {"type": "FeatureCollection", "credit": CREDIT, "features": watch_features})
    write_json(out_dir / "audit.json", sorted(audit, key=lambda e: (e["date"], e["dc_id"])))
    write_json(out_dir / "methodology.json", methodology)
    return results
