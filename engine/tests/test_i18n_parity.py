# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""FR ↔ EN parity invariant (i18n §13) — the build breaks when a language drifts.

EN silently lagged FR twice (old contradictoire copy, fiche links landing on FR).
Doctrine: shared templates + per-language t objects; this test makes the drift
mechanical to catch: every FR page has its EN twin, and paired thin pages define
t objects with the SAME top-level keys (a string added on one side without its
translation breaks the suite).
"""

import re

from engine.core import REPO_ROOT

PAGES = REPO_ROOT / "site" / "src" / "pages"

# (FR page, EN twin, compare t keys?) — routes differ by design (localised slugs).
PAIRS = [
    ("fr/index.astro", "index.astro", True),
    ("fr/dc/[id].astro", "dc/[id].astro", True),
    ("fr/classement.astro", "ranking.astro", True),
    ("fr/carte.astro", "map.astro", False),          # inline labels, no t object
    ("fr/methodologie.astro", "methodology.astro", True),
    ("fr/mentions-legales.astro", "legal.astro", False),  # t.sections carry prose, headings differ per language
    ("fr/contact.astro", "contact.astro", False),
    ("fr/comprendre.astro", "understand.astro", True),
    ("fr/comprendre/one-pager.astro", "understand/one-pager.astro", False),
    ("fr/bibliotheque.astro", "intelligence.astro", True),
    ("fr/bibliotheque/tous.astro", "intelligence/all.astro", True),
]
# FR-only internal tooling, exempt from parity: fr/apercu-partage.astro (OG preview gallery).

# Deliberate asymmetries: keys one language needs and the other, by design, does not.
# understand (EN) flags the France-centric content ("In France" tags + context notice);
# the FR page needs no such flag. Anything NOT listed here must exist on both sides.
EXTRA_OK: dict[str, set[str]] = {
    "understand.astro": {"contextNotice", "inFranceLabel"},
}


def _t_keys(text: str, label: str) -> set[str]:
    m = re.search(r"^const t = \{$(.*?)^\};$", text, re.S | re.M)
    assert m, f"{label}: no `const t = {{...}};` block found — thin pages carry their copy in t"
    # top-level keys only: exactly two spaces of indent
    return set(re.findall(r"^  ([A-Za-z_]\w*):", m.group(1), re.M))


def test_every_fr_page_has_its_en_twin():
    for fr, en, _ in PAIRS:
        assert (PAGES / fr).exists(), f"FR page missing: {fr}"
        assert (PAGES / en).exists(), (
            f"EN twin missing for {fr}: expected {en} — FR and EN advance together (i18n §13)"
        )


def test_paired_t_objects_share_their_keys():
    for fr, en, compare in PAIRS:
        if not compare:
            continue
        fr_keys = _t_keys((PAGES / fr).read_text(), fr) - EXTRA_OK.get(fr, set())
        en_keys = _t_keys((PAGES / en).read_text(), en) - EXTRA_OK.get(en, set())
        missing_en = fr_keys - en_keys
        missing_fr = en_keys - fr_keys
        assert not missing_en and not missing_fr, (
            f"t-object drift between {fr} and {en}: "
            f"missing in EN={sorted(missing_en)} · missing in FR={sorted(missing_fr)} — "
            "add the translation on the other side, never let one language lag"
        )
