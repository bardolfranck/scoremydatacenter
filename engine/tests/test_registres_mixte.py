# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Projet MIXTE : on DRAPE la fiche, on ne démêle pas. Un avis qui couvre un programme bâti
au-delà du data center (logements, crèche, aqualudique, co-living) porte des chiffres qui ne
sont pas ceux du DC. Le drapeau prévient ; il ne retire pas les faits (l'étage d'après tranche).

Garde-fou mesuré : un VOISINAGE (« habitations à 200 m ») n'est pas un programme — il ne drape pas.
"""

from pipelines.registers import avis


def _flag(text):
    return avis.extract_from_pages([text], "https://example.test/avis.pdf").projet_mixte


def test_programme_mixte_est_drape():
    courbevoie = (
        "Sur un site d'environ quinze hectares, le projet « Village Delage » prévoit la "
        "construction de 80 000 m2 de logements, 20 000 m2 d'équipements publics (groupe "
        "scolaire, crèche, gymnase), 200 000 m2 d'activités (environ 8 000 emplois), ainsi "
        "qu'un parc urbain et un data center sur les îlots A2 et A3.")
    assert _flag(courbevoie) in {"léger", "lourd"}


def test_niveau_lourd_quand_le_signal_est_massif():
    # « léger » vs « lourd » tient à la MASSE du signal sur le document entier (≥ 10 → lourd).
    dense = "Le programme urbain prévoit la construction de 80 000 m2 de logements. " * 12
    assert _flag(dense) == "lourd"


def test_composante_mixte_legere_est_drapee():
    rungis = (
        "Le projet de data center comprend aussi des habitations en co-living pour personnes "
        "âgées, une crèche de 200 m2 et un local commercial, en plus du bâtiment principal.")
    assert _flag(rungis) == "léger"


def test_voisinage_n_est_pas_un_programme_mixte():
    # Des habitations PROCHES ne font pas un projet mixte — sinon on draperait presque tout.
    saint_priest = (
        "Le data center s'implante en zone industrielle. Les habitations les plus proches sont "
        "à environ 20 m à l'ouest et 70 m au nord ; un groupe scolaire se trouve à 185 m.")
    assert _flag(saint_priest) is None


def test_data_center_seul_n_est_pas_drape():
    seul = (
        "Le projet consiste en la construction d'un centre d'hébergement de données avec "
        "54 groupes électrogènes de secours, des cuves de fioul et des groupes froids en toiture.")
    assert _flag(seul) is None
