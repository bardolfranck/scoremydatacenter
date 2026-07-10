# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Every gate must actually block: each test breaks the data one way and
asserts the right gate fires with an explicit message."""

from datetime import date

from engine.core import load_methodology, load_datacenters
from engine.scoring import history_entry_fields, score_datacenter
from engine.score import _changed
from engine.validate import run_gates

TODAY = date(2026, 7, 5)

ALPHA = "datacenters/zz-test-alpha.json"
BETA = "datacenters/zz-test-beta.json"
METH = "methodology/v0.1.0-draft.json"


def _ind(doc, indicator_id):
    return next(e for e in doc["indicators"] if e["id"] == indicator_id)


def test_repository_data_passes_all_gates():
    assert run_gates() == []


def test_gate1_missing_source(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "E1").pop("source"))
    assert any("GATE 1" in p and "source" in p for p in run_gates(root, TODAY))


def test_gate1_verdict_on_t1(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "T1").update(value="poor consultation"))
    assert any("GATE 1" in p for p in run_gates(root, TODAY))


def test_gate1_undeclared_missing_indicator(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: d["indicators"].remove(_ind(d, "E5")))
    assert any("status: missing" in p for p in run_gates(root, TODAY))


def test_gate2_declarative_measured_without_verification(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: _ind(d, "E4").update(status="measured"))
    problems = run_gates(root, TODAY)
    # caught structurally by the schema (gate 1) and semantically by gate 2
    assert any("verification_source" in p for p in problems)


def test_gate3_broken_weights(data_copy):
    root, edit = data_copy
    edit(METH, lambda m: m["pillars"][0].update(weight=0.5))
    assert any("GATE 3" in p and "sum" in p for p in run_gates(root, TODAY))


def test_gate3_ethical_lock_rejects_vulnerability_scoring_higher(data_copy):
    root, edit = data_copy

    def reward_vulnerability(m):
        l1 = next(i for i in m["indicators"] if i["id"] == "L1")
        l1["normalization"]["categories"]["sensitive"] = 95  # fragile municipality scores best

    edit(METH, reward_vulnerability)
    assert any("GATE 3" in p and "ethical lock" in p for p in run_gates(root, TODAY))


def test_gate3_vulnerability_order_must_cover_categories(data_copy):
    root, edit = data_copy

    def broken_order(m):
        l1 = next(i for i in m["indicators"] if i["id"] == "L1")
        l1["vulnerability_order"] = ["strong_fit", "sensitive"]

    edit(METH, broken_order)
    assert any("GATE 3" in p and "vulnerability_order" in p for p in run_gates(root, TODAY))


def test_gate4_unpublished_dc_in_public_repo(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: d["publication"].update(status="draft"))
    assert any("GATE 4" in p and "smdc-newsroom" in p for p in run_gates(root, TODAY))


def test_gate4_de_right_of_reply_not_over(data_copy):
    # zz-test-beta is site E — a D/E grade needs the 15-day right of reply before publishing.
    root, edit = data_copy
    edit(BETA, lambda d: d["publication"].update(operator_notified_at="2026-07-01"))
    assert any("GATE 4" in p and "right of reply" in p for p in run_gates(root, TODAY))


def test_gate4_ac_publishes_directly(data_copy):
    # zz-test-alpha is A–C — publication directe: no notification hold, even with none recorded.
    root, edit = data_copy
    edit(ALPHA, lambda d: d["publication"].update(operator_notified_at=None))
    assert not any("GATE 4" in p and "right of reply" in p for p in run_gates(root, TODAY))


def test_gate5_real_dc_against_draft_methodology(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: d.update(id="fr-test-alpha"))
    (root / "datacenters" / "zz-test-alpha.json").rename(root / "datacenters" / "fr-test-alpha.json")
    assert any("GATE 5" in p and "draft" in p for p in run_gates(root, TODAY))


def test_gate5_stale_methodology_version(data_copy):
    root, edit = data_copy
    edit(ALPHA, lambda d: d["score_history"][0].update(methodology_version="0.0.9"))
    assert any("GATE 5" in p and "methodology_change" in p for p in run_gates(root, TODAY))


def test_journal_gate_revision_without_rationale(data_copy):
    root, edit = data_copy

    def add_unjustified_revision(d):
        entry = dict(d["score_history"][0])
        entry.pop("rationale")
        entry["event"] = "data_correction"
        d["score_history"].append(entry)

    edit(ALPHA, add_unjustified_revision)
    assert any("JOURNAL GATE" in p and "rationale" in p for p in run_gates(root, TODAY))


def test_journal_gate_detects_unrecorded_grade_change():
    methodology = load_methodology()
    alpha = load_datacenters()["zz-test-alpha"]
    assert _changed(alpha, methodology) is None  # journal is in sync
    alpha["score_history"][-1]["grades"]["site"] = "A"  # pretend the record says A
    assert _changed(alpha, methodology) is not None  # engine refuses the silent mismatch


def test_history_entry_fields_shape(methodology):
    alpha = load_datacenters()["zz-test-alpha"]
    fields = history_entry_fields(score_datacenter(alpha, methodology), methodology)
    assert fields == {
        "methodology_version": methodology["version"],
        "grades": {"site": "B", "project_process": "C"},
        "confidence": "high",
    }
