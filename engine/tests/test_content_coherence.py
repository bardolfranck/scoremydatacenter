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


# --- Firewall (brief 2026-07-06 §1) + forbidden phrases (brief 2026-07-15 §4.I.2) ---
# The "we help the project, never the grade" firewall stays stated where it does
# legal/positioning work. The OLD prior-notice mechanism (grade-triggered right of
# reply, >=15-day hold) was retired on the 2026-07-15 legal review: its phrases are
# BANNED from every living surface so it can never crawl back through an old
# template or a copy-paste.
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


# Every phrase of the retired mechanism, FR + EN (case-insensitive, singular/plural,
# NBSP-tolerant). A hit anywhere on a living surface breaks the build.
FORBIDDEN_PHRASES = [
    r"droits?\s+de\s+réponse\s+préalables?",
    r"prior\s+rights?\s+of\s+reply",
    r"au\s+moins\s+(15|quinze)\s+jours",
    r"at\s+least\s+(15|fifteen)\s+days",
    r"[≥>]=?\s*15\s*j\b",
    r"contradictoires?\s+déclenchés?\s+par\s+la\s+note",
    r"grade-triggered",
    r"droit\s+de\s+réponse\s+en\s+cours",
    r"right\s+of\s+reply\s+in\s+progress",
    r"deux\s+droits\s+sur\s+chaque\s+fiche",
    r"two\s+rights\s+on\s+every\s+(fiche|datasheet)",
    r"sollicité,?\s+sans\s+réponse",
    r"solicited,?\s+no\s+(reply|response)",
    r"l'opérateur\s+dispose\s+d'un\s+droit\s+de\s+réponse",
]


def _living_surfaces():
    """Every user-facing source: site pages/components/content + README + docs."""
    roots = [REPO_ROOT / "site" / "src", REPO_ROOT / "docs"]
    files = [p for r in roots for p in r.rglob("*") if p.suffix in (".astro", ".ts", ".md")]
    files.append(REPO_ROOT / "README.md")
    return files


def test_forbidden_phrases_never_reappear():
    hits = []
    for path in _living_surfaces():
        text = path.read_text().replace("\u00a0", " ").lower()
        for pattern in FORBIDDEN_PHRASES:
            if re.search(pattern, text):
                hits.append(f"{path.relative_to(REPO_ROOT)}: {pattern!r}")
    assert not hits, (
        "forbidden phrase(s) of the retired prior-notice mechanism resurfaced "
        "(legal review 2026-07-15 — grades publish directly):\n" + "\n".join(hits)
    )


def test_forbidden_phrases_lint_actually_bites(tmp_path):
    # negative test: reintroduce one banned formula in a fake template -> the lint must flag it
    fake = tmp_path / "old-template.astro"
    fake.write_text("<p>Une note D ouvre un droit de réponse préalable d'au moins 15 jours.</p>")
    text = fake.read_text().lower()
    assert any(re.search(pat, text) for pat in FORBIDDEN_PHRASES), (
        "the forbidden-phrases lint no longer catches the canonical banned sentence"
    )


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

# --- Ranking register (brief 2026-07-12 · A-27): we situate, we never judge ------
# The percentile-context voice is the ONLY allowed voice on the ranking. Judgment
# words ("pire", "cancre", "mur de la honte", "flop"…) are banned from its copy.
RANKING_SOURCES = {
    "classement-fr": (REPO_ROOT / "site" / "src" / "pages" / "fr" / "classement.astro").read_text(),
    "ranking-en": (REPO_ROOT / "site" / "src" / "pages" / "ranking.astro").read_text(),
    "ranking-component": (REPO_ROOT / "site" / "src" / "components" / "Ranking.astro").read_text(),
}
JUDGMENT_WORDS = [r"\bpires?\b", r"\bcancres?\b", r"\bhonte\b", r"\bflops?\b",
                  r"\bworst\b", r"\bshame\b", r"\blosers?\b"]


def test_ranking_copy_situates_never_judges():
    for name, text in RANKING_SOURCES.items():
        low = text.lower()
        for pattern in JUDGMENT_WORDS:
            assert re.search(pattern, low) is None, (
                f"{name} uses the judgment word {pattern!r} — the ranking situates in the "
                "distribution (percentile-context register), it never judges (A-27)"
            )


def test_ranking_states_its_denominator_and_version():
    for name in ("classement-fr", "ranking-en"):
        text = RANKING_SOURCES[name]
        assert "{n}" in text and "{version}" in text, (
            f"{name} no longer states the percentile reference (N projects + methodology "
            "version) — a percentile without its denominator is a naked judgment (A-27)"
        )
