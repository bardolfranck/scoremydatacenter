# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Propose per-site IT power (MW) for the NL corpus from the RVO/EED disclosure — gate input.

    python -m pipelines.eed.propose <corpus_datacenters_dir>

Same doctrine as pipelines/dcwatch/propose.py: recall THEN precision, the human gate decides,
NOTHING is ever written to the corpus by this tool. An RVO row binds to a corpus DC only if they
share an operator token AND a distinctive name token. Several RVO rows matching one corpus DC with
different powers => AMBIGUOUS, never averaged, never picked.

One extra decision class this source needs, which DCWatch did not: `withheld`. Equinix (all 12 of
its Dutch sites), NorthC, QTS and Global Switch file the report but leave the power cell empty on
commercial-confidentiality grounds. That is NOT "absent" — the facility is in the register and the
blank is contestable under the Dutch open-government act. Saying so is the honest reading.

The `basis` field (INSTALLED vs RATED) rides with every proposal and must survive into whatever
consumes it: RATED is nameplate and sits above INSTALLED, so the two are not interchangeable
labels. Collapsing them is precisely the mislabel that makes aggregator data unusable.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from .reader import fetch

_OPERATOR_TOKENS = re.compile(
    r"EQUINIX|INTERXION|DIGITAL REALTY|DIGITAL HOOFDDORP|CYRUSONE|NTT|MICROSOFT|GOOGLE|QTS"
    r"|GLOBAL SWITCH|NORTHC|IRON MOUNTAIN|ATOS|SWITCH|DATACENTER GROEP|EI DATA|SERVERIUS"
)
_GENERIC = {"data", "center", "centre", "datacenter", "datacenters", "the", "group", "netherlands",
            "nederland", "amsterdam", "bv", "b.v."}


def _norm(s: str | None) -> str:
    return re.sub(r"[^A-Z0-9 ]+", " ", (s or "").upper()).strip()


def _operator_token(*fields: str | None) -> str | None:
    m = _OPERATOR_TOKENS.search(" ".join(_norm(f) for f in fields))
    return m.group(0) if m else None


def _name_tokens(name: str | None) -> set[str]:
    """Distinctive tokens: site codes (AMS17, AM3, ZW1) and words >= 5 chars, generics dropped."""
    toks = set()
    for t in _norm(name).split():
        if t.lower() in _GENERIC:
            continue
        if re.fullmatch(r"[A-Z]{2,4}\d{1,3}", t) or len(t) >= 5:
            toks.add(t)
    return toks


def propose(corpus_dir: Path, records: list[dict]) -> list[dict]:
    out = []
    for path in sorted(corpus_dir.glob("*.json")):
        if path.name.endswith(".provenance.json") or path.name.endswith(".draft.json"):
            continue
        dc = json.loads(path.read_text())
        ident = dc.get("identity", {})
        if (ident.get("country") or "").upper() != "NL":
            continue
        dc_op = _operator_token(ident.get("operator"), ident.get("name"))
        dc_toks = _name_tokens(ident.get("name"))
        same_operator = [r for r in records
                         if dc_op and _operator_token(r.get("operator"), r.get("owner"),
                                                      r.get("name")) == dc_op]
        hits = [r for r in same_operator if dc_toks and _name_tokens(r.get("name")) & dc_toks]
        # Recall fallback: the operator is in the register but our corpus name shares no token with
        # its site codes (corpus "Interxion AMS1-AMS4" vs RVO AMS03/05/06…, "Agriport A7" vs
        # AMSESG1/2). The facility is NOT absent — it is unresolved. Surface the candidates and let
        # the gate pick; never auto-bind on operator alone.
        operator_only = not hits and bool(same_operator)
        if operator_only:
            hits = same_operator
        entry = {"dc_id": dc["id"], "name": ident.get("name"), "operator": ident.get("operator")}
        powered = [h for h in hits if h.get("it_power_mw") is not None]
        if not hits:
            entry["decision"] = "absent"
        elif not powered:
            # In the register, power cell empty — commercial confidentiality, not missing data.
            entry.update(decision="withheld",
                         matched=[{"name": h["name"], "lau": h["lau_code"]} for h in hits])
        elif operator_only or len({h["it_power_mw"] for h in powered}) > 1:
            entry.update(decision="ambiguous",
                         reason=("name tokens did not match — operator-only candidates"
                                 if operator_only else "several sites, different powers"),
                         candidates=[{"name": h["name"], "mw": h["it_power_mw"],
                                      "basis": h["it_power_basis"], "lau": h["lau_code"]}
                                     for h in powered])
        else:
            h = powered[0]
            entry.update(decision="propose", mw=h["it_power_mw"], basis=h["it_power_basis"],
                         rvo_name=h["name"], lau=h["lau_code"],
                         computer_room_m2=h.get("computer_room_m2"),
                         source="RVO — EED Art. 12 disclosure (Netherlands)")
        out.append(entry)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus_dir", type=Path)
    args = ap.parse_args(argv)
    records = fetch()
    for entry in propose(args.corpus_dir, records):
        print(json.dumps(entry, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
