# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Détecteur de centroïde de géocodeur. Le critère n'est PAS l'égalité des coordonnées (trop
large, comme « ordre du jour » l'était pour les procès-verbaux) mais le PÉTITIONNAIRE :

  · Marseille (2026-10-01) : DIGITAL MRS5 et SEGRO partagent 43.287981,5.402336, porteurs
    différents, ~5 km d'écart réel → géocodeur. Mais MRS5 n'a pas de pétitionnaire extrait →
    on ne peut pas trancher → INDÉTERMINÉ (on ne suppose pas).
  · Marcoussis : DATA 4 SAS et DATA 4 SERVICES partagent 48.646436,2.214727 — MÊME exploitant,
    deux procédures sur LE MÊME site → pas un géocodeur, géométrie vraie, à garder.

On réutilise `match._meme_exploitant` comme comparateur (il reconnaît « DATA 4 SAS » ≈
« DATA 4 SERVICES »), on n'en écrit pas un second.
"""

from pipelines.registers import geocoder, match
from pipelines.registers.geocoder import (GEOCODEUR, INDETERMINE, MEME_SITE,
                                          classify, suspect_keys)

CMP = match._meme_exploitant


def _doc(intitule, centroid, petitionnaire=None):
    proc = {"intitule": intitule, "centroid": centroid}
    if petitionnaire:
        proc["petitionnaire"] = petitionnaire
    return {"procedure": proc}


MRS5 = _doc("data-center DIGITAL MRS5 à Marseille (13)", {"lat": 43.287981, "lon": 5.402336})
SEGRO = _doc("data-center + entrepôt, zone Actisud, Marseille", {"lat": 43.287981, "lon": 5.402336}, "SEGRO")
M_SAS = _doc("Extension du DATA IV à Marcoussis", {"lat": 48.646436, "lon": 2.214727}, "DATA 4 SAS")
M_SRV = _doc("Modification de l'implantation, Marcoussis", {"lat": 48.646436, "lon": 2.214727}, "DATA 4 SERVICES")
NOZAY = _doc("data center DATA4 à Nozay (91)", {"lat": 48.659, "lon": 2.197}, "DATA 4")


def test_meme_exploitant_meme_point_est_le_meme_site_pas_un_geocodeur():
    # Marcoussis : le point partagé est la VÉRITÉ, pas un artefact — ne pas le marquer.
    cats = classify({"m5308": M_SAS, "m7366": M_SRV}, CMP)
    assert cats[(48.646436, 2.214727)]["categorie"] == MEME_SITE
    assert suspect_keys({"m5308": M_SAS, "m7366": M_SRV}, CMP) == set()


def test_porteurs_differents_meme_point_est_un_geocodeur():
    a = _doc("projet A", {"lat": 43.3, "lon": 5.4}, "SEGRO")
    b = _doc("projet B", {"lat": 43.3, "lon": 5.4}, "Interxion France")
    cats = classify({"a": a, "b": b}, CMP)
    assert cats[(43.3, 5.4)]["categorie"] == GEOCODEUR
    assert (43.3, 5.4) in suspect_keys({"a": a, "b": b}, CMP)


def test_un_porteur_manquant_est_indetermine_pas_un_choix():
    # Marseille réel : MRS5 sans pétitionnaire + SEGRO → on ne tranche pas.
    cats = classify({"mrs5": MRS5, "segro": SEGRO}, CMP)
    assert cats[(43.287981, 5.402336)]["categorie"] == INDETERMINE
    # indéterminé reste suspect pour le rattachement (on ne fait pas confiance au point non confirmé).
    assert (43.287981, 5.402336) in suspect_keys({"mrs5": MRS5, "segro": SEGRO}, CMP)


def test_point_unique_nest_pas_signale():
    assert classify({"nozay": NOZAY}, CMP) == {}
    assert classify({"mrs5": MRS5, "nozay": NOZAY}, CMP) == {}


def test_match_garde_la_geometrie_du_meme_site():
    # Marcoussis : la fiche du corpus doit garder son signal géométrie (vrai site).
    corpus = {"fr-data4-marcoussis": {"municipality": "Marcoussis", "operator": "DATA4",
                                      "coordinates": {"lat": 48.646436, "lon": 2.214727}}}
    props = {p.avis: p for p in match.proposer({"m5308": M_SAS, "m7366": M_SRV}, corpus)}
    for avis in ("m5308", "m7366"):
        assert props[avis].centroid_partage is None
        assert "geometrie" in props[avis].signaux


def test_match_ecarte_la_geometrie_de_geocodeur_et_indetermine():
    corpus = {"fr-x": {"municipality": "Marseille", "operator": None,
                       "coordinates": {"lat": 43.287981, "lon": 5.402336}}}
    props = {p.avis: p for p in match.proposer({"mrs5": MRS5, "segro": SEGRO}, corpus)}
    for avis in ("mrs5", "segro"):
        assert props[avis].centroid_partage == INDETERMINE
        assert "geometrie" not in props[avis].signaux
