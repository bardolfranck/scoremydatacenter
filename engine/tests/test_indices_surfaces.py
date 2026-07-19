# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Indices pays — the §4 SURFACE gates (amendement 2026-07-19).

The reading insert (« Cet indice agrège les notes de SITES… ») is
NON-DETACHABLE from the map: every surface that renders the index —
canonical page, home block, OG cards — must carry it. Same mechanical
spirit as the A-26 forbidden-phrases lint: a template refactor that drops
the insert breaks the build, it does not ship."""

import re
from pathlib import Path

from engine.core import REPO_ROOT

_SRC = REPO_ROOT / "site" / "src"

# The load-bearing token of the insert, FR + EN (the sentence may be reworded
# around it, but "notes de SITES" / "SITE grades" is the invariant that says
# what is — and is not — being graded).
_FR_TOKEN = "notes de SITES"
_EN_TOKEN = "SITE grades"


def _read(rel: str) -> str:
    return (_SRC / rel).read_text()


def test_insert_welded_inside_the_map_component():
    # The insert lives INSIDE IndicesMap.astro — the only way to render the
    # map is through the component, so the insert cannot be forgotten.
    text = _read("components/IndicesMap.astro")
    assert _FR_TOKEN in text and _EN_TOKEN in text


def test_every_map_surface_goes_through_the_component():
    # No template inlines the country paths by hand: eu-map.json is imported
    # ONLY by IndicesMap.astro (bypassing the component would detach the insert).
    importers = [
        p.relative_to(_SRC)
        for p in _SRC.rglob("*.astro")
        if "eu-map.json" in p.read_text()
    ]
    assert importers == [Path("components/IndicesMap.astro")], (
        f"eu-map.json imported outside IndicesMap.astro: {importers}"
    )


def test_home_block_carries_the_insert():
    # The home top-5 block renders index grades without the map — the insert
    # text must still frame them (amendement: everywhere the index shows).
    text = _read("components/Landing.astro")
    assert _FR_TOKEN in text and _EN_TOKEN in text


def test_og_cards_carry_the_insert():
    text = _read("pages/og/indices/[key].png.ts")
    assert _FR_TOKEN in text and _EN_TOKEN in text


def test_og_cards_are_event_driven_not_drift_driven():
    # §1 bis byte-stability: the card reads grade/score/n from the country's
    # last HISTORY event, never from the continuous score in indices.json.
    text = _read("pages/og/indices/[key].png.ts")
    assert "indices_history.json" in text
    assert re.search(r"ev\??\.to\??\.(grade|score|n)", text), (
        "OG card no longer derives its figures from the last history event"
    )


def test_canonical_pages_exist_fr_and_en():
    # i18n §13: same surface, both languages, engine-fed.
    assert (_SRC / "pages" / "fr" / "indices.astro").is_file()
    assert (_SRC / "pages" / "indices.astro").is_file()
    page = _read("components/IndicesPage.astro")
    for needle in ("indices.json", "indices_history.json", "IndicesMap"):
        assert needle in page
