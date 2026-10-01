# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Détecteur de centroïde de géocodeur. Cas fondateur réel (2026-10-01) : les deux avis PACA de
Marseille — DIGITAL MRS5 (silo Saint-Louis, GPMM) et le projet mixte SEGRO (zone Actisud) — deux
sites distants d'environ 5 km, portaient le MÊME centroid 43.287981, 5.402336 (le centre géocodé de
« Marseille »). Un même point sur deux dossiers distincts est un géocodeur, et ça doit être DÉTECTÉ,
pas redécouvert à chaque fois.
"""

from pipelines.registers import match
from pipelines.registers.geocoder import geocoder_keys, shared_centroids

# Les deux dossiers réels de Marseille, réduits à ce qui compte pour le détecteur.
MRS5 = {"procedure": {"intitule": "data-center DIGITAL MRS5 à Marseille (13)", "commune": "MARSEILLE",
                      "centroid": {"lat": 43.287981, "lon": 5.402336}}}
SEGRO = {"procedure": {"intitule": "data-center + entrepôt, zone Actisud, Marseille (13)", "commune": "MARSEILLE",
                       "centroid": {"lat": 43.287981, "lon": 5.402336}}}
# Un vrai site, ailleurs, avec SA géométrie propre.
NOZAY = {"procedure": {"intitule": "data center DATA4 à Nozay (91)", "commune": "NOZAY",
                       "centroid": {"lat": 48.659, "lon": 2.197}}}


def test_meme_point_sur_deux_dossiers_distincts_est_un_geocodeur():
    shared = shared_centroids({"mrs5": MRS5, "segro": SEGRO, "nozay": NOZAY})
    assert shared == {(43.287981, 5.402336): ["mrs5", "segro"]}
    assert (43.287981, 5.402336) in geocoder_keys({"mrs5": MRS5, "segro": SEGRO})


def test_un_point_sur_un_seul_dossier_nest_pas_signale():
    # un vrai site, seul à porter son centroïde : rien à signaler.
    assert shared_centroids({"nozay": NOZAY}) == {}
    assert shared_centroids({"mrs5": MRS5, "nozay": NOZAY}) == {}


def test_centroid_absent_ne_casse_pas():
    assert shared_centroids({"x": {"procedure": {}}, "y": {}}) == {}


def test_match_ecarte_la_geometrie_de_geocodeur():
    # Les deux dossiers partagent le point ; une fiche du corpus est pile sur ce point.
    # Sans garde-fou, les DEUX se rattacheraient à elle par « géométrie ». Avec le garde-fou, le
    # signal géométrie disparaît et chaque proposition est marquée centroid_geocodeur.
    corpus = {"fr-un-site-quelconque": {"municipality": "Marseille", "operator": None,
                                        "coordinates": {"lat": 43.287981, "lon": 5.402336}}}
    props = {p.avis: p for p in match.proposer({"mrs5": MRS5, "segro": SEGRO}, corpus)}
    for avis in ("mrs5", "segro"):
        assert props[avis].centroid_geocodeur is True
        assert "geometrie" not in props[avis].signaux
        assert "geometrie_proche" not in props[avis].signaux


def test_match_garde_la_geometrie_quand_le_point_est_unique():
    # Un centroïde NON partagé reste un signal géométrie légitime.
    corpus = {"fr-data4-nozay": {"municipality": "Nozay", "operator": "DATA4",
                                 "coordinates": {"lat": 48.659, "lon": 2.197}}}
    props = {p.avis: p for p in match.proposer({"nozay": NOZAY}, corpus)}
    assert props["nozay"].centroid_geocodeur is False
    assert "geometrie" in props["nozay"].signaux
