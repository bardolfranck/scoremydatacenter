# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Propose per-site power (MW) for a corpus from the DCWatch common — gate input.

    python -m pipelines.dcwatch.propose <corpus_datacenters_dir> [--csv <local.csv>]

Deterministic-binding rule (recall THEN precision, human gate decides):
a DCWatch row is proposed for a corpus DC only if they share the commune AND
either an operator token (EQUINIX, OVH, SFR…) or a strong name overlap. One
candidate power value per DC or nothing — an ambiguous commune (several
plausible rows with different powers) is reported as AMBIGUOUS, never guessed.
Prints one JSON line per corpus DC: {dc_id, decision: propose|ambiguous|absent, …}.
Nothing is ever written to the corpus by this tool.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from .reader import fetch, normalize_name, parse

_OPERATOR_TOKENS = re.compile(
    r"EQUINIX|OVH|SFR|COLT|SCALEWAY|FREE|ILIAD|TELEHOUSE|INTERXION|DIGITAL REALTY|DATA4"
    r"|COGENT|ORANGE|BOUYGUES|ADISTA|ETIX|ATOS|KYNDRYL|IBM|EDF|GROUPAMA|AMAZON|MICROSOFT"
    r"|GOOGLE|PHOCEA|BLUECOM|SUNGARD|TDF|CELESTE|ZAYO|JAGUAR|EUCLYDE|TELIA|NEXEREN"
)
# Paris arrondissements ("PARIS 11EME") collapse to the commune
_ARRONDISSEMENT = re.compile(r"\s+\d+\s*EME?( ARRONDISSEMENT)?$")


def _commune_key(name: str | None) -> str:
    return _ARRONDISSEMENT.sub("", normalize_name(name))


def _name_overlap(a: str, b: str, commune: str = "") -> bool:
    """Strong overlap: a distinctive word (>= 5 chars, not a generic) shared by both keys.
    The commune's own words never count as distinctive — 'DC Université de STRASBOURG'
    must not bind to 'SFR Netcenter STRASBOURG' on the city name alone (gate reject,
    2026-07-13; same class as Lille Blanqui != Boitelle)."""
    generics = {"DATACENTER", "DATA", "CENTER", "CENTRE", "PARIS", "FRANCE", "PROJET", "CLOUD"}
    generics |= set(commune.split())
    words = {w for w in a.split() if len(w) >= 5 and w not in generics}
    return any(w in b.split() for w in words)


def _bind(identity: dict, rows: list[dict]) -> list[dict]:
    """Deterministic binding: same commune AND (operator token OR strong name overlap)."""
    dc_key = normalize_name(f"{identity['name']} {identity['operator']}")
    dc_tokens = set(_OPERATOR_TOKENS.findall(dc_key))
    commune = _commune_key(identity["municipality"])
    hits = []
    for r in rows:
        row_key = normalize_name(f"{r['name']} {r['operator']}")
        row_tokens = set(_OPERATOR_TOKENS.findall(row_key))
        if (dc_tokens & row_tokens) or _name_overlap(dc_key, row_key, commune):
            hits.append(r)
    return hits


def propose(corpus_dir: Path, records: list[dict]) -> list[dict]:
    by_commune: dict[str, list[dict]] = {}
    for r in records:
        if r["power_mw"] or r.get("year"):
            by_commune.setdefault(_commune_key(r["commune"]), []).append(r)

    out = []
    for path in sorted(corpus_dir.glob("*.json")):
        dc = json.loads(path.read_text())
        identity = dc["identity"]
        hits = _bind(identity, by_commune.get(_commune_key(identity["municipality"]), []))

        # power (original behaviour, line shape unchanged): only for DCs missing it
        if not identity.get("power_mw"):
            power_hits = [r for r in hits if r["power_mw"]]
            powers = {round(r["power_mw"], 1) for r in power_hits}
            if len(powers) == 1:
                r = power_hits[0]
                out.append({
                    "dc_id": dc["id"], "decision": "propose", "power_mw": round(r["power_mw"], 2),
                    "dcwatch_name": r["name"], "dcwatch_status": r["status"],
                    "source_url": r["source_url"], "provenance": r["provenance"],
                })
            elif power_hits:
                out.append({"dc_id": dc["id"], "decision": "ambiguous",
                            "candidates": [{"name": r["name"], "power_mw": r["power_mw"]} for r in power_hits]})
            else:
                out.append({"dc_id": dc["id"], "decision": "absent"})

        # commissioning year ('date_service'): same binding, own field — a DC whose
        # power is already known can still receive a year proposal
        if not (identity.get("vintage") or {}).get("expected_commissioning"):
            year_hits = [r for r in hits if r.get("year")]
            years = {r["year"] for r in year_hits}
            if len(years) == 1:
                r = year_hits[0]
                out.append({
                    "dc_id": dc["id"], "field": "year", "decision": "propose", "year": r["year"],
                    "dcwatch_name": r["name"], "dcwatch_status": r["status"],
                    "source_url": r["source_url"], "provenance": r["provenance"],
                })
            elif year_hits:
                out.append({"dc_id": dc["id"], "field": "year", "decision": "ambiguous",
                            "candidates": [{"name": r["name"], "year": r["year"]} for r in year_hits]})
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus_dir", type=Path)
    ap.add_argument("--csv", type=Path, help="local DCWatch CSV (skips the network fetch)")
    args = ap.parse_args(argv)
    records = parse(args.csv.read_text()) if args.csv else fetch()
    records = [r for r in records if r["country"] == "FR"] if not args.csv else records
    for line in propose(args.corpus_dir, records):
        print(json.dumps(line, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
