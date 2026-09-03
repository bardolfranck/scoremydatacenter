# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Veille FR — the daily driver: detect new-project announcements → candidate drafts → digest.

    uv run python -m pipelines.veille.fr --out ../smdc-newsroom/veille        # live GDELT-FR
    uv run python -m pipelines.veille.fr --out … --timespan 1w --limit 30

v1 = GDELT DOC API (keyless, throttled) with an ANNOUNCE-intent FR query — a PRESS RADAR. The DOC
artlist gives title+url+domain+date only (no structured commune/operator), so v1 candidates are
COORDLESS press leads: no geocoding, no tier-1 enrichment. That is deliberate, not a gap — the
richer path (GKG V2Locations/V2Organizations via BigQuery → geocode → tier-1) is v2. The digest
renders the coordless case honestly ("contexte tier-1 : en attente de géocodage").

Doctrine held by construction: DETECTION only → sourced facts → `state:"en_veille"`, never a score
(A-19/A-21). Operators are matched recall-first (a triage lead, the human gate confirms). The
driver DETECTS + builds the DIGEST + deposits it in the private newsroom; it NEVER deploys,
publishes, or sends mail (the send leg is CF-side).
"""

import argparse
import json
import re
from datetime import date as _date, datetime, timezone
from pathlib import Path

from . import digest as digestmod
from ..press import signal

# The ANNOUNCE-intent FR query lives in signal.GDELT_COUNTRY_SPECS["FR"] (reused via
# fetch_gdelt_country, with its sourcecountry filter + throttle backoff) — not duplicated here.
GDELT_LICENSE = "GDELT DOC API — libre avec attribution"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def _slug(url: str, title: str) -> str:
    base = _norm(title)[:48].strip().replace(" ", "-") or "sans-titre"
    tail = re.sub(r"[^a-z0-9]", "", (url or "").lower())[-6:] or "000000"
    return f"fr-veille-gdelt-{base}-{tail}".strip("-")


def load_corpus(art_dir: Path) -> list[dict]:
    """Existing scored DCs (for coordless dedup): id, name, operator, municipality."""
    scores = art_dir / "scores.json"
    if not scores.is_file():
        return []
    out = []
    for r in json.loads(scores.read_text()):
        out.append({"id": r.get("id"), "name": r.get("name"), "operator": r.get("operator"),
                    "municipality": r.get("municipality")})
    return out


def operators_in(text: str) -> list[str]:
    """Canonical operators named in the text — reuse signal's operator lexicon, no re-derivation."""
    return [op for op, rx in signal._OPERATOR_RE.items() if rx.search(text or "")]


def _dedup(title: str, operators: list[str], corpus: list[dict]) -> dict:
    """Coordless dedup vs the scored corpus (press leads have no coords). Recall-first: a false
    'new' is fine (the human triages) — the aim is not to MISS an existing site silently."""
    t = _norm(title)
    for dc in corpus:
        name = _norm(dc.get("name"))
        muni = _norm(dc.get("municipality"))
        op_hit = bool(operators) and any(o in operators for o in operators_in(dc.get("operator") or ""))
        # same full name in the headline, or same operator AND same commune named → likely known
        if (name and len(name) > 8 and name in t) or (op_hit and muni and muni in t):
            return {"status": "near_known", "nearest_id": dc["id"], "distance_km": None}
    return {"status": "new", "nearest_id": None, "distance_km": None}


def to_candidate(rec: dict, accessed: str, corpus: list[dict]) -> dict:
    """One GDELT DOC record → an en-veille candidate draft (coordless press lead)."""
    title = (rec.get("name") or "").strip()
    url = (rec.get("sources") or [None])[0] or rec.get("source_url")
    facts_meta = rec.get("facts") or {}
    domain = facts_meta.get("domain") or ""
    ops = operators_in(title)
    return {
        "id": _slug(url, title),
        "state": "en_veille",
        "name": title or "(titre non disponible)",
        "operator": " / ".join(ops) if ops else "non communiqué",
        "municipality": None,                      # unknown from DOC artlist → v2 geocoding
        "country": "FR",
        "project_status": "announced",
        "coordinates": None,
        "source": {"title": title or domain, "url": url, "accessed": accessed},
        "facts": [{
            "kind": "press",
            "label": {"fr": title, "en": title},
            "source": {"title": domain or "GDELT", "url": url},
        }],
        # Open, attributable source → publishable. (A commercial lead would be publishable:false.)
        "provenance": {"source": f"GDELT (presse : {domain})" if domain else "GDELT",
                       "url": url, "license": GDELT_LICENSE, "publishable": True},
        "detection": {
            "detected_at": accessed, "feed": "gdelt", "intent": "announce",
            "query": "FR announce lexicon", "seendate": facts_meta.get("seendate"),
            "dedup": _dedup(title, ops, corpus),
        },
        "tier1_preview": [],                       # coordless in v1 → enrichment is v2
    }


def build(accessed: str, corpus: list[dict], *, timespan: str, limit: int | None) -> list[dict]:
    """Detect → candidate drafts. De-duplicated by URL; capped by `limit`.

    Uses `fetch_gdelt_country("FR", …)` — the ANNOUNCE spec lives in signal.GDELT_COUNTRY_SPECS,
    so we inherit the `sourcecountry:france` filter AND the throttle-aware retry/backoff loop
    (GDELT's 429 penalty box outlasts the nominal throttle) instead of re-deriving them here.
    """
    records = signal.fetch_gdelt_country("FR", accessed, timespan=timespan, maxrecords=min(limit or 50, 250))
    seen, cands = set(), []
    for rec in records:
        url = (rec.get("sources") or [None])[0]
        if not url or url in seen:
            continue
        seen.add(url)
        c = to_candidate(rec, accessed, corpus)
        if not digestmod.validate_candidate(c):    # only ship clean candidates
            cands.append(c)
        if limit and len(cands) >= limit:
            break
    return cands


def run(out_root: Path, *, art_dir: Path, accessed: str | None = None,
        timespan: str = "1w", limit: int | None = None) -> dict:
    """Full daily pass: detect → drafts → digest.html + manifest.json in newsroom/veille/<date>/.

    Writes ONLY into the private newsroom veille tree. No deploy, no publish, no send.
    """
    accessed = accessed or datetime.now(timezone.utc).date().isoformat()
    corpus = load_corpus(art_dir)
    candidates = build(accessed, corpus, timespan=timespan, limit=limit)

    day_dir = out_root / accessed
    day_dir.mkdir(parents=True, exist_ok=True)
    (day_dir / "candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n")
    (day_dir / "digest.html").write_text(digestmod.render_digest(candidates, accessed))
    manifest = digestmod.build_manifest(candidates, accessed)
    (day_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    n_new = sum(1 for c in candidates if c["detection"]["dedup"]["status"] == "new")
    return {"date": accessed, "candidates": len(candidates), "new": n_new,
            "near_known": len(candidates) - n_new, "dir": str(day_dir), "subject": manifest["subject"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Daily veille FR: detect new DC projects → digest (no grade, no deploy).")
    ap.add_argument("--out", required=True, type=Path, help="newsroom veille root (e.g. ../smdc-newsroom/veille)")
    ap.add_argument("--artifacts", type=Path, default=Path("site/public/data"), help="scored corpus dir (for dedup)")
    ap.add_argument("--timespan", default="1w", help="GDELT lookback (e.g. 1w, 1m, 3m)")
    ap.add_argument("--limit", type=int, default=None, help="cap candidates (dev)")
    ap.add_argument("--date", default=None, help="override accessed date (default: today UTC)")
    args = ap.parse_args(argv)
    result = run(args.out, art_dir=args.artifacts, accessed=args.date, timespan=args.timespan, limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
