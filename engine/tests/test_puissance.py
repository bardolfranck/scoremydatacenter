# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le groupe de puissance : deux étages, et ce qu'on refuse de fabriquer.

Ce qui est figé ici n'est pas une arithmétique de bornes, c'est une doctrine de comparaison :
l'étage grossier tranche des fourchettes que le fin ne peut pas, et quand les DEUX sont
ambigus on retient le haut — jamais le bas.
"""

import pytest

from engine import puissance


def test_letage_grossier_est_une_AGREGATION_du_fin():
    """🔴 « zone → case » n'est un arbre que si chaque case appartient à une zone et une
    seule. Deux découpages parallèles laisseraient une fiche tomber dans deux branches
    incohérentes."""
    cases = {nom for _, nom in puissance.CASES}
    assert set(puissance.ZONES) == cases, "toute case doit porter sa zone, et rien d'autre"
    assert set(puissance.ZONES.values()) == {"petit", "moyen", "grand"}


@pytest.mark.parametrize("mw,attendu", [
    (0.4, "0–1"), (1, "0–1"), (1.8, "1–5"), (12, "6–50"), (60, "50–100"),
    (240, "100–500"), (771, "500+"),
])
def test_une_valeur_unique_tombe_dans_sa_case(mw, attendu):
    assert puissance.case(mw) == attendu


def test_une_fourchette_contenue_dans_une_case_la_rend_telle_quelle():
    g = puissance.groupe({"power_mw_range": {"min": 8, "max": 30}})
    assert (g["case"], g["zone"], g["determine"]) == ("6–50", "moyen", "case")


def test_LE_CAS_BETHUNE_letage_grossier_tranche_ce_que_le_fin_ne_peut_pas():
    """⭐ « 60 à 240 MW » (La Voix du Nord, 2026-10-14, projet de Béthune) : ambigu au fin —
    50–100 ou 100–500 — et TRANCHÉ au grossier. C'est un FAIT : quelle que soit la valeur
    réelle dans la fourchette, le site est grand. Pas un arbitrage à défendre."""
    g = puissance.groupe({"power_mw_range": {"min": 60, "max": 240}})
    assert g["zone"] == "grand"
    assert g["case"] is None, "on ne choisit pas une case qu'on ne connaît pas"
    assert g["determine"] == "zone"


@pytest.mark.parametrize("bas,haut,zone_attendue", [(3, 8, "moyen"), (40, 60, "grand")])
def test_quand_les_DEUX_etages_sont_ambigus_on_prend_le_HAUT(bas, haut, zone_attendue):
    """Minorer la puissance d'un projet le rendrait moins impactant qu'il n'est — l'erreur
    dans le sens FAVORABLE, celle qu'on s'interdit partout."""
    g = puissance.groupe({"power_mw_range": {"min": bas, "max": haut}})
    assert g["zone"] == zone_attendue == puissance.zone(puissance.case(haut))
    assert g["determine"] == "maximum", "l'arbitrage doit se DIRE, pas se confondre avec une mesure"


def test_le_maximum_et_le_MILIEU_ne_coincident_pas():
    """⚠️ « 40–60 MW » : le haut donne « grand », le milieu (50) donnerait « moyen ». La règle
    déclarée est le MAXIMUM — le milieu n'est pas un second avis qui la confirmerait, et sur
    les cas où la règle MORD il dit souvent autre chose."""
    g = puissance.groupe({"power_mw_range": {"min": 40, "max": 60}})
    assert g["determine"] == "maximum" and g["zone"] == "grand"
    assert puissance.zone(puissance.case((40 + 60) / 2)) == "moyen"


def test_letage_grossier_tranche_plus_de_cas_quon_ne_croit():
    """Trouvé en écrivant les tests : « 60–110 » traverse deux cases (50–100 et 100–500) mais
    les deux sont dans « grand ». La règle du maximum ne mord donc PAS ici — et c'est tant
    mieux, un fait vaut mieux qu'un arbitrage."""
    g = puissance.groupe({"power_mw_range": {"min": 60, "max": 110}})
    assert (g["determine"], g["zone"], g["case"]) == ("zone", "grand", None)


def test_une_valeur_au_bord_dune_case_est_signalee():
    """5 MW estimés à ±20 % basculent entre « 1–5 » et « 6–50 ». Sans ce drapeau on recréerait
    au SEUIL ce qu'on vient de supprimer au POINT."""
    assert puissance.groupe({"power_mw": 4.8})["au_bord"] is True
    assert puissance.groupe({"power_mw": 12})["au_bord"] is False


def test_la_provenance_voyage_mais_ne_change_PAS_le_groupe():
    """Le groupe rend la provenance sans effet sur la comparaison — c'est tout son intérêt —
    mais l'origine reste lisible pour l'affichage."""
    a = puissance.groupe({"power_mw": 12, "power_mw_status": "announced"})
    b = puissance.groupe({"power_mw": 12, "power_mw_status": "estimated"})
    assert (a["zone"], a["case"]) == (b["zone"], b["case"])
    assert (a["origine"], b["origine"]) == ("announced", "estimated")


def test_sans_puissance_il_ny_a_pas_de_groupe():
    """Pas de valeur par défaut : un site sans puissance est hors de l'axe, et le dira."""
    assert puissance.groupe({}) is None
    assert puissance.groupe({"power_mw_status": "announced"}) is None


def test_une_fourchette_inversee_echoue_bruyamment():
    with pytest.raises(ValueError, match="fourchette inversée"):
        puissance.groupe({"power_mw_range": {"min": 240, "max": 60}})
