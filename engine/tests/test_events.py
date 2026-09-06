# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Phase-1 project-event detector — the diff semantics (no I/O). Events are FACTS, never grades."""
import json

from pipelines.veille import events


def _e(id, status="announced", facts=None, accessed="2026-09-07"):
    return {"id": id, "operator": "Op", "project_status": status,
            "source": {"accessed": accessed}, "facts": facts or []}


def test_detected_new_project():
    prev = {}
    curr = {"fr-a": _e("fr-a")}
    ev = events.diff_snapshots(prev, curr)
    assert ev == [{"type": "detected", "id": "fr-a", "event_at": "2026-09-07",
                   "project_status": "announced", "operator": "Op"}]


def test_status_change():
    prev = {"fr-a": _e("fr-a", "announced")}
    curr = {"fr-a": _e("fr-a", "permitting")}
    ev = events.diff_snapshots(prev, curr)
    assert ev == [{"type": "status_change", "id": "fr-a", "event_at": "2026-09-07",
                   "from": "announced", "to": "permitting"}]


def test_new_contestation_fact():
    opp = {"kind": "opposition", "source": {"url": "https://x/1"}}
    prev = {"fr-a": _e("fr-a")}
    curr = {"fr-a": _e("fr-a", facts=[opp])}
    ev = events.diff_snapshots(prev, curr)
    assert ev == [{"type": "contestation", "id": "fr-a", "event_at": "2026-09-07",
                   "kind": "opposition", "source_url": "https://x/1"}]


def test_no_event_when_unchanged_and_no_grade_anywhere():
    opp = {"kind": "opposition", "source": {"url": "https://x/1"}}
    snap = {"fr-a": _e("fr-a", "permitting", facts=[opp])}
    ev = events.diff_snapshots(snap, dict(snap))
    assert ev == []
    # a press fact is not a contestation event (only opposition/appeal/petition/moratorium)
    press = {"kind": "press", "source": {"url": "https://x/2"}}
    ev2 = events.diff_snapshots({"fr-a": _e("fr-a")}, {"fr-a": _e("fr-a", facts=[press])})
    assert ev2 == []
    assert "grade" not in json.dumps(events.diff_snapshots({}, snap)).lower()
