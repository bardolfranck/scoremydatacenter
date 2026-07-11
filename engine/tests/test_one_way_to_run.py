# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""There is ONE way to rebuild the served data — the wrong ways must fail loudly."""

from pathlib import Path

from engine.score import _refuse_if_newsroom_present


def test_build_refuses_when_newsroom_is_next_door(tmp_path, monkeypatch, capsys):
    cal = tmp_path / "calibration"
    cal.mkdir()
    monkeypatch.setenv("NEWSROOM_CAL", str(cal))
    monkeypatch.delenv("SMDC_PUBLIC_FIXTURES", raising=False)
    assert _refuse_if_newsroom_present() is True
    err = capsys.readouterr().err
    assert "make prod-artifacts" in err  # the message names the ONE way


def test_build_allows_public_fixtures_when_explicit(tmp_path, monkeypatch):
    cal = tmp_path / "calibration"
    cal.mkdir()
    monkeypatch.setenv("NEWSROOM_CAL", str(cal))
    monkeypatch.setenv("SMDC_PUBLIC_FIXTURES", "1")
    assert _refuse_if_newsroom_present() is False


def test_build_runs_normally_without_a_newsroom(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWSROOM_CAL", str(tmp_path / "nope"))  # CI / external cloners
    monkeypatch.delenv("SMDC_PUBLIC_FIXTURES", raising=False)
    assert _refuse_if_newsroom_present() is False
