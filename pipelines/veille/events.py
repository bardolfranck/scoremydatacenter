# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Phase-1 « site vivant » — SPEC + prototype: detect PROJECT EVENTS between two veille snapshots.

WHY (memory « observatoire vivant — rétention »): the site is a reference people RETURN to. The
return-driver is project ALERTS (reusing the email-gate infra): tell a subscriber when something
HAPPENS on a project they watch. That needs a detector: « what event, on which project, when ».

DESIGN — an event is a DIFF between two consecutive snapshots of the veille/watchlist state, keyed
by the stable project id (a project is one id, coords+operator resolved upstream):

  EVENT TYPES (all FACT-based, NEVER a grade — A-19 in public; grade-range alerts = paid API, Y2):
    - detected      : a project id present in `curr` but not in `prev` (newly « repéré »)
    - status_change : same id, identity.project_status moved (announced→permitting→…→operational)
    - contestation  : same id, a NEW fact of kind opposition/appeal/petition/moratorium appeared
    - delisted      : id in `prev` but not `curr` (withdrawn/merged) — low-priority, for audit

  WHEN: `event_at` = the curr entry's detection date (source.accessed) or the run date passed in.
  WHERE IT PLUGS: the unified veille pipeline (orchestrate.py / the cloud cron). Each run: load the
  previous committed snapshot, diff against today's, emit events → (a) the digest for Franck's red
  lane, (b) later, the email-gate alert fan-out. NEVER auto-publishes; NEVER emits a grade.

  NEUTRALITY: an event states a sourced fact (a status moved; an opposition was reported). It never
  states or implies a score. The contestation event carries the fact's own source, not our opinion.

This module is the PURE detector (no I/O, no network) so it is trivially testable and reusable; the
snapshot load/store + the alert fan-out are wired in the pipeline layer, gated behind Franck's go.
"""

from __future__ import annotations

_CONTEST_KINDS = {"opposition", "appeal", "petition", "moratorium"}


def _fact_keys(entry: dict) -> set:
    """Stable signature of a fact (kind + source url) so a re-listed identical fact is not a new event."""
    out = set()
    for f in entry.get("facts") or []:
        out.add((f.get("kind"), ((f.get("source") or {}).get("url"))))
    return out


def _status(entry: dict) -> str | None:
    return entry.get("project_status") or (entry.get("identity") or {}).get("project_status")


def diff_snapshots(prev: dict, curr: dict, *, when: str | None = None) -> list[dict]:
    """Return the list of project EVENTS between two snapshots {id: entry}.

    Each event: {"type", "id", "event_at", ...type-specific fields}. Deterministic, order = curr
    ids then delisted. FACT-based only — no grade anywhere.
    """
    events: list[dict] = []
    for pid, cur in curr.items():
        at = when or (cur.get("source") or {}).get("accessed")
        if pid not in prev:
            events.append({"type": "detected", "id": pid, "event_at": at,
                           "project_status": _status(cur), "operator": cur.get("operator")})
            continue
        old = prev[pid]
        if _status(cur) != _status(old):
            events.append({"type": "status_change", "id": pid, "event_at": at,
                           "from": _status(old), "to": _status(cur)})
        new_facts = _fact_keys(cur) - _fact_keys(old)
        for kind, url in sorted((k for k in new_facts if k[0] in _CONTEST_KINDS), key=lambda x: (x[0] or "", x[1] or "")):
            events.append({"type": "contestation", "id": pid, "event_at": at,
                           "kind": kind, "source_url": url})
    for pid in prev.keys() - curr.keys():
        events.append({"type": "delisted", "id": pid, "event_at": when})
    return events
