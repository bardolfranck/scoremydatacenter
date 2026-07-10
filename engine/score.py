# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Score computation CLI — two modes, one invariant: grades only change on the record.

Build mode (default, what `make score` runs):
    python -m engine.score
Computes everything and writes the artifacts, but FAILS if any DC's computed
grades differ from the last recorded score_history entry (or if there is no
entry). Builds are deterministic and never mutate source data; a grade change
without a recorded, justified event cannot reach production.

Record mode (what `make rescore` runs):
    python -m engine.score --record --event <event> --rationale "why" [--date YYYY-MM-DD]
Appends a score_history entry to every DC whose computed grades changed (or
which has none yet), then the next build passes. Rationale is mandatory for
every entry after a DC's first (journal gate).
"""

import argparse
import sys
from datetime import date

from .core import DATA_DIR, GateError, load_json, load_methodology, datacenter_paths, write_json
from .scoring import history_entry_fields, score_datacenter
from .validate import run_gates

VALID_EVENTS = ["initial_scoring", "ex_post_rescore", "right_of_reply_revision",
                "data_correction", "methodology_change"]


def _changed(dc: dict, methodology: dict) -> dict | None:
    """Return the would-be history core if grades/confidence/version differ from the last entry."""
    current = history_entry_fields(score_datacenter(dc, methodology), methodology)
    history = dc["score_history"]
    if history:
        last = history[-1]
        recorded = {k: last[k] for k in ("methodology_version", "grades", "confidence")}
        if recorded == current:
            return None
    return current


def build() -> int:
    problems = run_gates()
    if problems:
        print("score: gates failed — run `make validate` for details", file=sys.stderr)
        return 1
    methodology = load_methodology()
    unrecorded = []
    datacenters = {}
    for path in datacenter_paths():
        dc = load_json(path)
        datacenters[dc["id"]] = dc
        if _changed(dc, methodology) is not None:
            unrecorded.append(dc["id"])
    if unrecorded:
        print(
            "JOURNAL GATE: computed grades are not recorded in score_history for: "
            + ", ".join(unrecorded)
            + '\nA grade cannot change silently. Record it with a justified event:\n'
            '  make rescore EVENT=<'
            + "|".join(VALID_EVENTS)
            + '> RATIONALE="why the grade moved"',
            file=sys.stderr,
        )
        return 1
    from .artifacts import build_artifacts
    results = build_artifacts(datacenters, methodology)
    for dc_id in sorted(results):
        g = results[dc_id]["grades"]
        pp = g["project_process"]["grade"]
        print(f"score: {dc_id}: site={g['site']['grade']} project_process={pp} "
              f"confidence={results[dc_id]['confidence']['level']}")
    print(f"score: artifacts written for {len(results)} datacenter(s)")
    # Notification load (brief 2026-07-06 §1, phase 5): only D/E grades — on either the site or
    # the project note — trigger the ≥15-day right of reply before publication. Count them so the
    # contradictory workload is dimensioned automatically.
    de = [dc_id for dc_id, r in results.items()
          if {r["grades"]["site"]["grade"], r["grades"]["project_process"]["grade"]} & {"D", "E"}]
    print(f"score: right-of-reply load — {len(de)} DC(s) exposed at D/E (need ≥15-day notice): "
          + (", ".join(sorted(de)) if de else "none"))
    return 0


def record(event: str, rationale: str | None, on: str) -> int:
    problems = run_gates()
    if problems:
        print("rescore: gates failed — run `make validate` for details", file=sys.stderr)
        return 1
    methodology = load_methodology()
    changed_any = False
    for path in datacenter_paths():
        dc = load_json(path)
        core = _changed(dc, methodology)
        if core is None:
            continue
        if dc["score_history"] and not rationale:
            raise GateError(
                f"JOURNAL GATE: {dc['id']} already has a score history — a RATIONALE is mandatory "
                "for every revision"
            )
        entry = {"date": on, **core, "event": event}
        if rationale:
            entry["rationale"] = rationale
        dc["score_history"].append(entry)
        write_json(path, dc)
        print(f"rescore: {dc['id']}: recorded {event} -> site={core['grades']['site']} "
              f"project_process={core['grades']['project_process']} confidence={core['confidence']}")
        changed_any = True
    if not changed_any:
        print("rescore: nothing to record — computed grades already match the journal")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="engine.score")
    parser.add_argument("--record", action="store_true", help="append justified score_history entries")
    parser.add_argument("--event", choices=VALID_EVENTS)
    parser.add_argument("--rationale")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    try:
        if args.record:
            if not args.event:
                parser.error("--record requires --event")
            return record(args.event, args.rationale, args.date)
        return build()
    except GateError as e:
        print(f"score: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
