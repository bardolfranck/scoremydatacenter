# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""`not_collected` vs `missing` (RED FLAG fix, 2026-07-09).

`missing` = we read the public dossier and the commitment is absent → a scored 0
(verified opacity). `not_collected` = nobody has looked yet → excluded from the
substantive score and instead lowers coverage. A 0 for something never read would
be as false as an A of complacency: an operator must not be branded opaque on
indicators we simply never extracted."""

import copy

import pytest

from engine.core import load_methodology
from engine.scoring import score_datacenter, INSUFFICIENT_DATA
from engine.validate import run_gates

MVP_PROJECT = {i["id"] for i in load_methodology()["indicators"]
               if i["mvp"] and i["block"] == "project"}


def _set(dc, indicator_id, **fields):
    e = next(x for x in dc["indicators"] if x["id"] == indicator_id)
    e.clear()
    e.update({"id": indicator_id, **fields})


def test_project_all_not_collected_is_insufficient_even_with_full_governance(methodology, alpha):
    """The Fouju case: exemplary T1/T2, but no project commitment has been read → you
    cannot grade an operator's project on governance alone."""
    dc = copy.deepcopy(alpha)
    for pid in MVP_PROJECT:
        _set(dc, pid, status="not_collected")
    result = score_datacenter(dc, methodology)
    assert result["grades"]["project_process"]["grade"] == INSUFFICIENT_DATA
    # site is untouched — base block only
    assert result["grades"]["site"] == score_datacenter(alpha, methodology)["grades"]["site"]


def test_not_collected_is_excluded_not_scored_zero(methodology, alpha):
    """Flipping one disclosed project datum to `not_collected` must never score WORSE than
    flipping it to `missing` (0): excluding is at least as good as a hard zero."""
    pid = "E4"  # announced in the alpha fixture
    as_missing = copy.deepcopy(alpha); _set(as_missing, pid, status="missing",
                                            source={"title": "read", "url": "https://example.org/x", "accessed": "2026-07-01"})
    as_notcol = copy.deepcopy(alpha); _set(as_notcol, pid, status="not_collected")
    pp_missing = score_datacenter(as_missing, methodology)["grades"]["project_process"]
    pp_notcol = score_datacenter(as_notcol, methodology)["grades"]["project_process"]
    # both still graded here (other project indicators remain), and excluding >= zeroing
    assert pp_missing["grade"] != INSUFFICIENT_DATA and pp_notcol["grade"] != INSUFFICIENT_DATA
    assert pp_notcol["score"] >= pp_missing["score"]


def test_not_collected_lowers_confidence(methodology, alpha):
    dc = copy.deepcopy(alpha)
    _set(dc, "E4", status="not_collected")
    assert score_datacenter(dc, methodology)["confidence"]["score"] <= \
        score_datacenter(alpha, methodology)["confidence"]["score"]


# --- Gate 8: extraction coherence -------------------------------------------------

def test_gate8_missing_project_needs_read_trace_when_dossier_available(data_copy):
    """T2 attests a public dossier ⇒ a project `missing` (opacity claim) without a source is rejected."""
    target, edit = data_copy
    edit("datacenters/zz-test-alpha.json",
         lambda dc: _set(dc, "F5", status="missing"))  # strip the read-trace source
    problems = run_gates(target)
    assert any("GATE 8" in p and "F5" in p for p in problems), problems


def test_gate8_not_collected_cannot_be_published(data_copy):
    """`not_collected` is a draft-only state — it can never reach a published DC."""
    target, edit = data_copy
    edit("datacenters/zz-test-alpha.json",
         lambda dc: _set(dc, "E4", status="not_collected"))
    problems = run_gates(target)
    assert any("GATE 8" in p and "E4" in p and "published" in p for p in problems), problems


def test_gate8_allows_not_collected_in_draft(data_copy):
    """The same not_collected in a DRAFT DC is fine — it only blocks publication."""
    target, edit = data_copy

    def to_draft_with_notcollected(dc):
        dc["publication"]["status"] = "draft"
        _set(dc, "E4", status="not_collected")
    edit("datacenters/zz-test-alpha.json", to_draft_with_notcollected)
    problems = run_gates(target)
    assert not any("GATE 8" in p for p in problems), problems
