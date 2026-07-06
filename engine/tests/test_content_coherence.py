# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Copy <-> product coherence gate (methodology-lead request, 2026-07-06).

Three consecutive review loops caught the same defect class: site copy
asserting numbers the engine does not display (close_to ranges, one-decimal
claims, notice periods). This test makes the tripwire mechanical: every
quantitative claim on the landing pages must match the methodology and the
engine constants. Change a parameter -> the build breaks until the copy is
updated (and vice versa)."""

import re
from pathlib import Path

import pytest

from engine.core import REPO_ROOT, load_methodology
from engine.validate import NOTICE_DAYS

PAGES = {
    "en": (REPO_ROOT / "site" / "src" / "pages" / "index.astro").read_text(),
    "fr": (REPO_ROOT / "site" / "src" / "pages" / "fr" / "index.astro").read_text(),
}


@pytest.fixture(scope="module")
def methodology():
    return load_methodology()


def test_indicator_count_claims_match_methodology(methodology):
    real = len(methodology["indicators"])
    for lang, text in PAGES.items():
        for claimed in re.findall(r"(\d+)\s+indicat(?:or|eur)s", text):
            assert int(claimed) == real, (
                f"{lang} copy claims {claimed} indicators, methodology defines {real}"
            )


def test_pillar_count_claims_match_methodology(methodology):
    real = len(methodology["pillars"])
    claims = {
        "en": re.findall(r"(\d+)\s+pillars", PAGES["en"]),
        "fr": re.findall(r"(\d+)\s+piliers", PAGES["fr"]) + (["5"] if "cinq piliers" in PAGES["fr"] else []),
    }
    for lang, found in claims.items():
        assert found, f"{lang} copy no longer states the pillar count — intentional?"
        for claimed in found:
            assert int(claimed) == real, f"{lang} copy claims {claimed} pillars, methodology defines {real}"


def test_coverage_threshold_claims_match_parameters(methodology):
    real_pct = round(methodology["parameters"]["min_coverage"] * 100)
    for lang, text in PAGES.items():
        for claimed in re.findall(r"(\d+)\s?%\s(?:de couverture|coverage)", text):
            assert int(claimed) == real_pct, (
                f"{lang} copy claims a {claimed}% coverage floor, parameters say {real_pct}%"
            )


def test_notice_period_claims_match_gate():
    for lang, text in PAGES.items():
        for claimed in re.findall(r"(?:au moins|at least)\s+(\d+)\s+(?:jours|days)", text):
            assert int(claimed) == NOTICE_DAYS, (
                f"{lang} copy promises {claimed} days of notice, gate 4 enforces {NOTICE_DAYS}"
            )
        assert re.search(r"(?:environ|about|around)\s+\d+\s+(?:jours|days)", text) is None, (
            f"{lang} copy hedges the notice period ('about N days') — it is an exact gate, say 'at least'"
        )


def test_no_copy_claims_removed_display_features():
    # close_to ranges were removed from the engine output; the copy must not resurrect them
    for lang, text in PAGES.items():
        assert "fourchette" not in text.lower() and "close to a grade" not in text.lower(), (
            f"{lang} copy mentions grade ranges — the engine no longer displays them"
        )


def test_pillar_weight_claims_match_methodology(methodology):
    weights = {p["id"]: round(p["weight"] * 100) for p in methodology["pillars"]}
    # the landing renders weights dynamically from methodology.json (no hardcoded
    # percentages allowed in the page sources)
    for lang, text in PAGES.items():
        hardcoded = re.findall(r"(\d+)\s?%[^)]{0,30}(?:pilier|pillar)", text)
        assert not hardcoded, f"{lang} copy hardcodes pillar weights {hardcoded} — render them from methodology.json"
    assert sum(weights.values()) == 100
