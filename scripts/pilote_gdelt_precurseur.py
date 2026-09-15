#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Precursor-validation pilot — retrospective GDELT contestation intensity per site.

Spec: 2-methodo-scoring/pilote-gdelt-retrospectif-spec.md (R&D). For 15 anchor sites, run TWO
retrospective GDELT DOC queries — a TOTAL coverage query (operator + commune + DC context) and a
CONTESTATION query (TOTAL + contestation terms) — then report volume, ratio, and a hand-auditable
sample of contestation items so R&D can judge precision. The estimand is the ratio; the sample is
for the precision read.

NOTE-BLIND BY CONSTRUCTION: this reads only operator + commune (public identity), talks only to
GDELT, and writes only counts + article samples. It never reads or writes any grade/score/letter
— nothing here touches the scoring path (validation must stay note-blind, R&D non-circularity go).

Runs from the CLOUD (GitHub Actions) because GDELT hard-429s a laptop IP; reuses signal.py's proven
GDELT client + throttle/backoff (no bespoke HTTP driver).

    uv run python scripts/pilote_gdelt_precurseur.py [--out ../smdc-newsroom] [--start 20230101000000]
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from pipelines.press import signal

# 15 anchor sites (note-blind: operator + commune only, NO grade). `group` = the chief's a-priori
# label for R&D's discrimination read (known-contestation vs background) — a contestation status,
# never a grade.
SITES = [
    {"id": "fr-digital-realty-mrs4", "operator": "Digital Realty", "commune": "Marseille", "group": "positive"},
    {"id": "fr-google", "operator": "Google", "commune": "Étrechet", "group": "positive"},
    {"id": "fr-campus-ia-fouju", "operator": "Mistral", "commune": "Fouju", "group": "positive"},
    {"id": "fr-digital-realty", "operator": "Digital Realty", "commune": "Bouc-Bel-Air", "group": "positive"},
    {"id": "sesterce-rovaltain", "operator": "Sesterce", "commune": "Rovaltain", "group": "positive"},
    {"id": "fr-nexeren-06-montpellier", "operator": "Nexeren", "commune": "Saint-Aunès", "group": "background"},
    {"id": "fr-nexeren-05-reventin-vaugris", "operator": "Nexeren", "commune": "Reventin-Vaugris", "group": "background"},
    {"id": "nl-equinix-en1-enschede", "operator": "Equinix", "commune": "Enschede", "group": "background"},
    {"id": "de-3u-rechenzentrum-berlin", "operator": "3U", "commune": "Berlin", "group": "background"},
    {"id": "de-itenos-berlin-ber1", "operator": "ITENOS", "commune": "Kleinmachnow", "group": "background"},
    {"id": "de-planet-ic-v-schwerin", "operator": "PLANET IC", "commune": "Schwerin", "group": "background"},
    {"id": "fr-cogent-tours", "operator": "Cogent", "commune": "Tours", "group": "background"},
    {"id": "fr-datacenter-atos", "operator": "Atos", "commune": "Aubervilliers", "group": "background"},
    {"id": "fr-datacube", "operator": "Datacube", "commune": "Dax", "group": "background"},
    {"id": "fr-dc2scale-velizy-latecoere", "operator": "dc2scale", "commune": "Vélizy-Villacoublay", "group": "background"},
]

DC_CONTEXT = '("data center" OR datacenter OR "centre de données" OR Rechenzentrum)'
CONTESTATION_TERMS = ('(opposition OR recours OR moratoire OR pétition OR manifestation OR contestation '
                      'OR "enquête publique" OR protest OR lawsuit OR referendum OR Klage '
                      'OR Bürgerinitiative OR bezwaar)')
RATIO_FLOOR = 5          # ratio is NA below this many total articles (R&D floor — thin denominator)
SAMPLE_N = 12            # contestation items shown per site for the manual precision read
MAXRECORDS = 250        # GDELT DOC cap (a site above this is flagged: total capped → ratio distorted)


def _queries(site: dict) -> tuple[str, str]:
    total = f'"{site["operator"]}" "{site["commune"]}" {DC_CONTEXT}'
    return total, f"{total} {CONTESTATION_TERMS}"


def _fetch(query: str, start: str, *, retries: int = 3, sleep=time.sleep) -> dict:
    """One retrospective GDELT DOC call with signal.py's retry/backoff (429 penalty box outlasts the
    nominal throttle — back off in growing steps; give up loudly rather than silently miss a site)."""
    for attempt in range(retries):
        try:
            return signal._gdelt_fetch_raw(query, maxrecords=MAXRECORDS, startdatetime=start)
        except (signal.SourceUnavailable, json.JSONDecodeError) as exc:
            if attempt == retries - 1:
                print(f"gdelt pilote: gave up after {retries} attempts ({exc})", file=sys.stderr)
                return {}
            sleep(signal._GDELT_THROTTLE_S * 5 * (attempt + 1))
    return {}


def _articles(data: dict) -> list[dict]:
    return data.get("articles") or []


def _sample(articles: list[dict], n: int) -> list[dict]:
    out = []
    for a in articles[:n]:
        out.append({"title": (a.get("title") or "").strip(), "url": a.get("url"),
                    "domain": a.get("domain"), "seendate": a.get("seendate")})
    return out


def run(start: str, *, sleep=time.sleep) -> dict:
    accessed = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = []
    for i, site in enumerate(SITES):
        total_q, contest_q = _queries(site)
        if i:
            sleep(signal._GDELT_THROTTLE_S)
        total = _articles(_fetch(total_q, start, sleep=sleep))
        sleep(signal._GDELT_THROTTLE_S)
        contest = _articles(_fetch(contest_q, start, sleep=sleep))
        total_n, contest_n = len(total), len(contest)
        ratio = round(contest_n / total_n, 3) if total_n >= RATIO_FLOOR else f"NA(<{RATIO_FLOOR})"
        results.append({
            "id": site["id"], "operator": site["operator"], "commune": site["commune"],
            "group": site["group"],
            "total_n": total_n, "contestation_n": contest_n, "ratio": ratio,
            "total_capped": total_n >= MAXRECORDS,      # cap hit → ratio distorted, flag for R&D
            "queries": {"total": total_q, "contestation": contest_q},
            "contestation_sample": _sample(contest, SAMPLE_N),
        })
        print(f"  {site['id']:32} total={total_n:>3} contest={contest_n:>3} ratio={ratio}", file=sys.stderr)
    return {
        "generated_at": accessed,
        "spec": "2-methodo-scoring/pilote-gdelt-retrospectif-spec.md",
        "note_blind": True,          # no grade read/written — estimand is the contestation ratio
        "window": {"startdatetime": start, "enddatetime": "now"},
        "params": {"maxrecords": MAXRECORDS, "ratio_floor": RATIO_FLOOR, "mode": "artlist",
                   "sourcecountry": None, "dc_context": DC_CONTEXT, "contestation_terms": CONTESTATION_TERMS},
        "sites": results,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Retrospective GDELT contestation-intensity pilot (note-blind).")
    ap.add_argument("--out", type=Path, default=Path("../smdc-newsroom"),
                    help="newsroom root; result → <out>/validation/pilote-gdelt-<date>.json")
    ap.add_argument("--start", default="20230101000000", help="GDELT startdatetime YYYYMMDDHHMMSS")
    args = ap.parse_args(argv)
    payload = run(args.start)
    day = datetime.now(timezone.utc).date().isoformat()
    dest = args.out / "validation" / f"pilote-gdelt-{day}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"written {dest}  ({len(payload['sites'])} sites)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
