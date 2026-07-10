# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the synthesis redaction phase (no network — the LLM is a stub).

Pins the country-agnostic ground rules: Gate 7 (no grade letter in prose) and the editorial bans are
enforced BEFORE a draft is written, insufficient project/process gets the fixed honest block, the model
call retries on an invalid draft, and the batch is idempotent.
"""

import json

import pytest

from pipelines import synthesize


def _scored(pp="insufficient_data"):
    return {
        "id": "zz-x",
        "grades": {"site": {"grade": "C"}, "project_process": {"grade": pp}},
        "indicators": [
            {"id": "E2", "label": {"fr": "Raccordement réseau"}, "block": "base", "status": "measured", "value": "saturated", "score": 0.0},
            {"id": "F2", "label": {"fr": "Statut du sol"}, "block": "base", "status": "measured", "value": "artificialized", "score": 100.0},
            {"id": "E4", "label": {"fr": "PUE"}, "block": "project", "status": "measured", "value": 1.2, "score": 90.0},
        ],
    }


_SOURCE = {"id": "zz-x", "identity": {"name": "X Campus", "municipality": "Y", "country": "ZZ"}}
_CLEAN = {"site": {"lead": "Site contraint", "fr": "Réseau saturé sur terrain artificialisé ; situe la note du site.", "en": "Saturated grid on built land; sets the site grade."}}


def test_validate_flags_grade_letter_and_banned_word():
    assert synthesize.validate({"site": {"lead": "x", "fr": "situe le site en note C.", "en": "ok"}})
    assert synthesize.validate({"site": {"lead": "x", "fr": "un réseau mauvais.", "en": "ok"}})
    assert synthesize.validate(_CLEAN) == []


def test_build_prompt_grounds_on_measured_site_signals_only():
    p = synthesize.build_prompt(_SOURCE, _scored())
    assert "Raccordement réseau" in p and "Statut du sol" in p   # base indicators present
    assert "PUE" not in p                                        # project-block indicator excluded from site ground
    assert "AUCUNE lettre" in p                                  # Gate 7 rule carried into the prompt


def test_redact_injects_fixed_block_when_project_insufficient():
    syn = synthesize.redact(_SOURCE, _scored("insufficient_data"), llm=lambda _p: json.dumps(_CLEAN))
    assert syn["project_process"] == synthesize.FIXED_PROJECT
    assert syn["site"]["lead"] == "Site contraint"


def test_redact_retries_then_raises_on_persistent_letter():
    bad = json.dumps({"site": {"lead": "x", "fr": "en note C.", "en": "grade C."}})
    calls = {"n": 0}

    def flaky(_p):
        calls["n"] += 1
        return bad if calls["n"] == 1 else json.dumps(_CLEAN)

    assert synthesize.redact(_SOURCE, _scored(), llm=flaky)["site"]["lead"] == "Site contraint"
    assert calls["n"] == 2  # retried once after the invalid first draft

    with pytest.raises(ValueError):
        synthesize.redact(_SOURCE, _scored(), llm=lambda _p: bad, retries=1)


def test_synthesize_panel_is_idempotent(tmp_path):
    (tmp_path / "datacenters").mkdir()
    (tmp_path / "art" / "dc").mkdir(parents=True)
    (tmp_path / "datacenters" / "zz-x.json").write_text(json.dumps(_SOURCE))
    (tmp_path / "art" / "dc" / "zz-x.json").write_text(json.dumps(_scored()))

    calls = {"n": 0}

    def llm(_p):
        calls["n"] += 1
        return json.dumps(_CLEAN)

    r1 = synthesize.synthesize_panel(tmp_path / "datacenters", tmp_path / "art", llm=llm)
    assert r1["written"] == ["zz-x"] and calls["n"] == 1
    r2 = synthesize.synthesize_panel(tmp_path / "datacenters", tmp_path / "art", llm=llm)
    assert r2["written"] == [] and "already synthesised" in r2["skipped"][0] and calls["n"] == 1  # no second call
