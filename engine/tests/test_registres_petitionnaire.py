# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Pétitionnaire (maître d'ouvrage) lu dans le PDF. 23 avis sur 39 viennent de l'index national
qui ne le publie pas — sans ce champ, le détecteur de projets est aveugle et il faut lire à la
main. On capte le nom APRÈS une tournure d'introduction, jamais le repli « la société X » nu (qui
attrape un financier/foncier), et on DÉCLARE l'absence plutôt que de deviner un tiers.
"""

from pipelines.registers.avis import petitionnaire_from_pages as pet


def test_capte_le_nom_apres_la_tournure():
    assert pet(["Le maître d'ouvrage du projet est la société Interxion France. Le dossier…"]) == "Interxion France"
    assert pet(["Le projet, porté par la société DATA 4, s'implante sur un terrain à Nozay."]) == "DATA 4"
    assert pet(["Avis sur le projet présenté par la SAS Courbevoie Bruyères, situé à Courbevoie."]) == "Courbevoie Bruyères"
    assert pet(["Dossier déposé par Goodman France pour un centre de données."]) == "Goodman France"


def test_boilerplate_maitre_douvrage_sans_nom_ne_produit_rien():
    # « le maître d'ouvrage doit répondre » : tournure sans nom propre → aucune extraction.
    assert pet(["L'avis porte sur la qualité de l'étude d'impact ; le maître d'ouvrage doit "
                "apporter une réponse écrite à la présente analyse de l'autorité."]) is None


def test_pas_de_repli_la_societe_nu():
    # « la société X » sans tournure d'introduction (un financier, un foncier) n'est PAS le
    # pétitionnaire — on ne le devine pas.
    assert pet(["Le terrain appartient à la société BNP Paribas, qui le loue à l'exploitant du site "
                "industriel voisin depuis plusieurs années déjà sur ce secteur."]) is None


def test_nom_propre_seulement_pas_les_mots_en_minuscule():
    # casse-sensible : on ne capte pas « situé », « est », « le » collés au nom.
    assert pet(["Le maître d'ouvrage est la société Penta Lyon situé à Saint-Priest en zone "
                "industrielle à proximité des habitations les plus proches."]) == "Penta Lyon"
