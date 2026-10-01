# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Deux drapeaux de NATURE, pas de démêlage ni de calcul :

- `projet_mixte` : l'avis couvre un programme bâti au-delà du data center. Il porte ses PREUVES
  (tournures captées + nombre), PAS un niveau inventé — on ne saurait défendre un seuil.
- `plusieurs_installations` : l'avis décrit N installations (campus). Compté sur les FAITS
  (puissances IT distinctes, étiquettes DC01/02/03), jamais sur des mots-clés — ceux-ci
  sur-déclenchent (comparaison de voisinage, nom de société « PIPA-DC1 »).

Garde-fous mesurés sur l'étalon : projet_mixte 3/13, plusieurs_installations 1/13 (le seul vrai
campus). Un voisinage d'habitations ne drape pas ; un nom de société « DC1 » ne compte pas.
"""

from pipelines.registers import avis


def _avis(text):
    return avis.extract_from_pages([text], "https://example.test/avis.pdf")


def test_projet_mixte_porte_ses_preuves_sans_niveau():
    courbevoie = (
        "Sur un site d'environ quinze hectares, le projet « Village Delage » prévoit la "
        "construction de 80 000 m2 de logements, un groupe scolaire de douze classes, une "
        "crèche de soixante berceaux, un gymnase, et un data center sur les îlots A2 et A3.")
    m = _avis(courbevoie).projet_mixte
    assert m and m["occurrences"] >= 3
    assert any("logements" in s for s in m["signaux"])
    # pas de niveau « léger/lourd » inventé : seulement les preuves.
    assert "léger" not in str(m) and "lourd" not in str(m)


def test_voisinage_n_est_pas_un_programme_mixte():
    saint_priest = (
        "Le data center s'implante en zone industrielle. Les habitations les plus proches sont "
        "à environ 20 m à l'ouest et 70 m au nord ; un groupe scolaire se trouve à 185 m.")
    assert _avis(saint_priest).projet_mixte is None


def test_data_center_seul_n_est_pas_drape():
    seul = ("Le projet consiste en la construction d'un centre d'hébergement de données avec "
            "54 groupes électrogènes de secours, des cuves de fioul et des groupes froids.")
    a = _avis(seul)
    assert a.projet_mixte is None
    assert a.plusieurs_installations is None


def test_plusieurs_installations_comptees_sur_les_faits():
    # Campus : étiquettes de bâtiment DC01/DC02/DC03 → trois installations.
    campus = ("Le campus de centres de données comprend trois bâtiments, DC01, DC02 et DC03, "
              "chacun avec ses installations techniques propres sur le site.")
    assert _avis(campus).plusieurs_installations == 3
    # Puissances IT distinctes par bâtiment → comptées aussi (multiple=True).
    deux = ("Les salles informatiques du premier bâtiment ont une puissance de 75 MW ; les "
            "salles informatiques du second bâtiment une puissance de 37,5 MW.")
    a = _avis(deux)
    assert sorted(f.value for f in a.facts if f.field_id == "puissance_it_mw") == [37.5, 75.0]
    assert a.plusieurs_installations == 2


def test_nom_de_societe_dc1_ne_compte_pas_pour_une_installation():
    # « PIPA-DC1 » est un nom de société, pas une 2e installation : DC01/02/03 (zéro de tête) seuls.
    pipa = ("Un data center unique porté par la société PIPA-DC1 sera construit sur la commune "
            "de Blyes, avec une puissance de 130 MW IT en phase finale.")
    assert _avis(pipa).plusieurs_installations is None