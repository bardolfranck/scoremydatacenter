# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""L'invariant de l'applicabilité par pays.

Ce que ces tests protègent : un indicateur NON APPLICABLE dans un pays ne doit pas élargir
la bande de ce pays. Confondre « non applicable » et « non collecté » ferait porter à
l'Allemagne une incertitude qu'elle ne pourra jamais combler — donc une plage large à
perpétuité, sur un indicateur qui n'a aucun sens chez elle.

Et la réciproque compte autant : un indicateur APPLICABLE mais non collecté doit CONTINUER
d'élargir. Sans ce second test, on pourrait « réparer » nos trous de collecte en les
déclarant non applicables, ce qui reviendrait à blanchir l'ignorance.
"""

import copy

from engine.core import load_methodology
from engine.plage_bands import CONTESTATION_ADJACENT, _not_applicable, base_definitions


def _meth_with_applicability(rule: dict) -> dict:
    m = copy.deepcopy(load_methodology())
    m["applicability"] = rule
    return m


def test_contestation_is_blind_everywhere_without_any_declaration():
    """Le comportement historique est un CAS PARTICULIER de la primitive, pas une exception."""
    m = load_methodology()
    for country in ("FR", "DE", None):
        assert _not_applicable(country, m) == CONTESTATION_ADJACENT


def test_declared_country_only_indicator_is_blind_elsewhere_and_live_at_home():
    m = _meth_with_applicability({"E6": {"countries_only": ["FR"]}})
    assert "E6" not in _not_applicable("FR", m), "applicable chez lui : il doit swinguer"
    assert "E6" in _not_applicable("DE", m), "non applicable ailleurs : il doit être aveugle"
    # et l'aveuglement historique n'est jamais perdu en chemin
    assert CONTESTATION_ADJACENT <= _not_applicable("DE", m)


def test_an_undeclared_indicator_is_applicable_everywhere():
    """Le défaut est APPLICABLE. Un trou de collecte ne se blanchit pas par omission —
    il faut une déclaration explicite pour rendre un indicateur aveugle."""
    m = load_methodology()
    base_ids = {d["id"] for d in base_definitions(m)} - CONTESTATION_ADJACENT
    for country in ("FR", "DE"):
        assert not (base_ids & _not_applicable(country, m))


def test_empty_map_changes_nothing():
    """La primitive doit pouvoir être livrée INERTE : sans déclaration, comportement identique."""
    assert _not_applicable("DE", _meth_with_applicability({})) == CONTESTATION_ADJACENT
