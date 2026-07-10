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


# --- Firewall + grade-triggered contradictoire (brief 2026-07-06 §1/§3) ---------
# The "we help the project, never the grade" firewall and the grade-triggered
# right of reply must stay stated where they do legal/positioning work.
_SITE = REPO_ROOT / "site" / "src" / "pages"
FIREWALL_SOURCES = {
    "landing-fr": PAGES["fr"],
    "mentions-legales": (_SITE / "fr" / "mentions-legales.astro").read_text(),
    "methodologie": (_SITE / "fr" / "methodologie.astro").read_text(),
    "readme": (REPO_ROOT / "README.md").read_text(),
}


def test_firewall_line_present_where_required():
    for name, text in FIREWALL_SOURCES.items():
        low = text.lower()
        assert "jamais la note" in low or "never the grade" in low, (
            f"{name} no longer carries the firewall ('on aide le projet, jamais la note')"
        )


def test_contradictoire_is_grade_triggered_not_all_nominative():
    fr = PAGES["fr"]
    assert re.search(r"notes?\s+A[–\-]C|D\s+ou\s+E", fr), (
        "landing no longer states the grade-triggered contradictoire (A–C direct, D/E right of reply)"
    )
    assert "publication nominative" not in fr.lower(), (
        "landing still promises the OLD all-nominative 15-day hold — the contradictoire is grade-triggered now"
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


# --- Gate 7 (prose): a grade letter is never rendered outside <ScoreBadge> --------
# Seen live (2026-07-10): an LLM-written accroche pinned at "site C, piliers D"
# rendered next to recomputed badges saying D and E after a recalibration. Prose
# citing a letter duplicates computed state and WILL drift; the badge carries the
# letter, the prose carries the why.

from engine.artifacts import build_artifacts, synthesis_grade_citations
from engine.core import GateError, load_datacenters


def _stale_dc():
    return {
        "id": "zz-stale",
        "synthesis": {"site": {
            "fr": "La note de site C reflète cet équilibre (piliers Énergie D et Foncier D).",
            "en": "These signals place the site at grade C.",
        }},
    }


def test_synthesis_prose_citing_letters_is_detected():
    hits = synthesis_grade_citations(_stale_dc())
    assert len(hits) >= 3  # note de site C, piliers ... D, at grade C


def test_letter_free_prose_passes():
    clean = {"id": "zz-clean", "synthesis": {"site": {
        "fr": "La note de site reflète cet équilibre : mesures ERC engagées, PUE 1,2 annoncé. À noter.",
        "en": "The site grade reflects the constraint; the Energy pillar stays low. E-fuels and ERC measures.",
    }}}
    assert synthesis_grade_citations(clean) == []


def test_build_refuses_grade_letters_in_prose(methodology, tmp_path, alpha):
    stale = dict(alpha, **{"synthesis": _stale_dc()["synthesis"]})
    with pytest.raises(GateError, match="GATE 7 \\(prose\\)"):
        build_artifacts({stale["id"]: stale}, methodology, out_dir=tmp_path, watchlist=[])


def test_committed_corpus_prose_is_letter_free():
    for dc in load_datacenters().values():
        assert synthesis_grade_citations(dc) == []
