# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Détecteur de géo fabriquée (pipelines.geo_audit.centroid_check) — source reconstruite à partir
du bytecode orphelin (la 4ᵉ commande fantôme du chantier). Ces tests figent le CRITÈRE COMBINÉ,
qui porte un gate de publication (engine.validate._geo_gate) : près d'un oracle géocodeur ET pas
sur un bâtiment. Hors réseau — on teste la décision, pas les oracles.
"""

from pipelines.geo_audit import centroid_check as C


def test_metres_distance_connue():
    # ~111,2 m pour 0,001° de latitude.
    assert abs(C.metres((48.0, 2.0), (48.001, 2.0)) - 111.2) < 1.0
    assert C.metres((48.0, 2.0), (48.0, 2.0)) == 0.0


def test_pres_oracle_et_pas_sur_batiment_est_fabriquee():
    # Le cas Fouju : la coordonnée tombe sur le point du géocodeur ET pas sur un bâtiment.
    assert C.classer(0.0, "off_building") == "fabriquee"
    assert C.classer(149.0, "no_building") == "fabriquee"


def test_pres_oracle_mais_sur_batiment_est_faux_positif():
    # Un vrai DC d'une petite commune dense : près du centroïde MAIS sur un bâtiment réel.
    assert C.classer(19.7, "on_building") == "faux_positif"
    assert C.classer(10.0, "near_building") == "faux_positif"


def test_pres_oracle_mais_batiment_inconnu_est_non_evalue():
    # Fail-open corrigé : un verdict bâtiment manquant près d'un centroïde n'est JAMAIS « sain ».
    # Une fiche jamais mesurée ne doit pas ressembler à une fiche mesurée et saine.
    assert C.classer(0.0, None) == "non_evalue"
    assert C.classer(149.0, None) == "non_evalue"
    # mais loin de tout oracle, un verdict manquant n'a aucune importance (pas près d'un centroïde).
    assert C.classer(500.0, None) is None


def test_loin_de_tout_oracle_nest_pas_signale():
    assert C.classer(151.0, "off_building") is None       # au-delà du seuil
    assert C.classer(5000.0, "no_building") is None
    assert C.classer(None, "off_building") is None         # aucun oracle n'a répondu


def test_seuil_est_bien_150():
    assert C.THRESHOLD_M == 150.0
    assert C.classer(150.0, "off_building") == "fabriquee"   # borne incluse
