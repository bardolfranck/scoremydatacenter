# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""GATE OPÉRATEUR — une absence d'exploitant s'écrit `null`, jamais en prose.

NÉ D'UNE FUITE SERVIE (2026-10-17), pas d'une intuition. Trois lanes écrivaient trois
graphies différentes de la même absence — « unknown », « opérateur non identifié »,
« UNKNOWN — to fill » — et quatre endroits du site répondaient à « l'opérateur est-il
identifié ? » avec quatre listes qui n'en connaissaient chacune qu'une partie. Résultat en
production : 329 sites de la carte et 162 fiches affichaient le placeholder COMME UN NOM
D'EXPLOITANT, et le balisage schema.org l'affirmait aux machines.

CE QUE CE FICHIER FIGE EST L'ATTENTE, PAS LA GRAPHIE DU JOUR. Un test qui vérifierait
« aucune fiche ne vaut unknown » repasserait au vert le jour où une lane invente la
quatrième formulation — c'est exactement comme ça qu'on a servi la fuite. Ce qu'on tient
ici : *une valeur qui DÉCRIT une absence est refusée*, et la mesure qui l'a prouvé — EU a
trouvé 218 fiches là où une recherche sur « unknown » n'en voyait que 211.
"""

import json

import pytest

from engine.validate import operator_gate


def _fiche(tmp_path, nom, operator):
    p = tmp_path / f"{nom}.json"
    p.write_text(json.dumps({"id": nom, "identity": {"name": nom, "operator": operator}}))
    return p


# Les graphies RÉELLEMENT rencontrées dans le corpus, lane par lane. La liste est une trace
# d'incident, pas une spécification : le gate doit en refuser d'autres (voir le test suivant).
@pytest.mark.parametrize("valeur", [
    "unknown",                        # EU : 211 fiches (FR, CH, SE, FI)
    "Unknown",                        # map.geojson : 5 sites — une comparaison sensible à la casse les ratait
    "opérateur non identifié",        # WORLD : 162 fiches US
    "UNKNOWN — to fill",              # défaut dormant du batch ET de la CLI
    "Incertain, ex-IBM, etat inconnu",  # prose libre : aucune liste ne l'aurait devinée
    "",
    "   ",
])
def test_une_absence_en_prose_est_refusee(tmp_path, valeur):
    assert operator_gate([_fiche(tmp_path, "dc", valeur)]), (
        f"« {valeur} » est passé : le gate laisse publier une absence déguisée en nom"
    )


def test_la_forme_est_refusee_pas_la_graphie(tmp_path):
    """LE TEST QUI COMPTE. Des formulations que personne n'a encore écrites — accents,
    casse, espaces — doivent mourir aussi. Sans lui, on ne prouverait pas que le gate juge la
    FORME ; on prouverait seulement qu'il connaît les graphies d'aujourd'hui, ce qu'une
    liste codée en dur satisferait aussi — et c'est précisément ce qui a échoué en prod."""
    for inedite in ("OPÉRATEUR   NON   IDENTIFIÉ", "Non Identifié", "Operator Not Identified",
                    "À RENSEIGNER", "N/A", "nil"):
        assert operator_gate([_fiche(tmp_path, "dc", inedite)]), f"« {inedite} » est passé"


def test_un_exploitant_nomme_passe(tmp_path):
    """La porte symétrique. Un gate qui refuse tout est aussi inutile qu'un gate qui laisse
    tout passer — et plus coûteux, parce qu'il casse le build de quelqu'un qui a raison."""
    for nom in ("Equinix", "Digital Realty", "Amazon Data Services", "NTT", "Orange"):
        assert operator_gate([_fiche(tmp_path, "dc", nom)]) == [], f"« {nom} » refusé à tort"


def test_amazon_aws_n_est_pas_une_absence(tmp_path):
    """FAUX POSITIF RENCONTRÉ EN ÉCRIVANT CE GATE, sur cinq fiches réelles. Chercher « n/a »
    par inclusion dans la chaîne fait de « Amazon/AWS » une absence : le slash et les lettres
    voisines suffisent. D'où la règle du gate — égalité sur les jetons courts, inclusion
    réservée aux locutions assez longues pour ne rien attraper d'autre."""
    assert operator_gate([_fiche(tmp_path, "dc", "Amazon/AWS")]) == []


def test_null_est_la_reponse_attendue(tmp_path):
    """`null` n'est pas toléré, il est DEMANDÉ : c'est la façon correcte de dire « on ne sait
    pas ». Le gate ne pousse pas à inventer un nom, il pousse à déclarer l'absence."""
    assert operator_gate([_fiche(tmp_path, "dc", None)]) == []


def test_le_message_dit_la_fiche_la_valeur_et_le_remede(tmp_path):
    """Un gate qui dit « refusé » sans dire quoi ni comment coûte une enquête à chaque
    déclenchement, et finit contourné."""
    (msg,) = operator_gate([_fiche(tmp_path, "fr-exemple", "unknown")])
    assert "fr-exemple" in msg and "unknown" in msg and "null" in msg
