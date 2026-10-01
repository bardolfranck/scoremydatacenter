# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Bruit en BANDES structurées — un test par TOURNURE, avec la phrase RÉELLE de l'avis.

Le bruit se publie apparié (point × période × bande), pas en dB(A) à plat. Chaque test porte
une tournure réellement rencontrée dans les 43 avis ; l'appariement jour/nuit est l'invariant.
Deux grandeurs séparées : niveau (environnement) et émergence (le data center lui-même). On ne
garde que ce que l'avis mesure — ni cible OMS, ni horaire pris pour un niveau.
"""

import json

from pipelines.registers import bruit, run


# ── NIVEAUX : les tournures d'appariement ────────────────────────────────────────────────────

def test_plage_jour_nuit_avec_point_et_metrique():
    # Villebon : plage jour / plage nuit, point nommé, métrique LAeq explicite.
    s = ("Les niveaux acoustiques en limites de propriété oscillent entre 57 et 61 dB(A) de "
         "jour (LAeq moyenné sur 7h-22h), et entre 50,5 et 57 dB(A) de nuit (LAeq moyenné sur "
         "22h-7h).")
    [b] = bruit.parse_levels(s)
    assert b["jour"] == {"min": 57.0, "max": 61.0}
    assert b["nuit"] == {"min": 50.5, "max": 57.0}
    assert b["point"] == "en limites de propriété"
    assert b["metrique"] == "LAeq"


def test_valeur_simple_jour_nuit():
    # Rungis : valeurs simples jour et nuit, point « au point le plus exposé ».
    s = ("Les données de l’état initial présentent les niveaux sonores les plus élevés à 61,9 "
         "dB(A) le jour et 55 dB(A) la nuit au point le plus exposé.")
    [b] = bruit.parse_levels(s)
    assert b["jour"] == {"valeur": 61.9}
    assert b["nuit"] == {"valeur": 55.0}
    assert b["point"] == "au point le plus exposé"


def test_ordre_inverse_valeur_simple_lycee():
    # Tremblay, ligne de la maquette : « de jour … est de 60,5 dB(A) et 54,5 en période
    # nocturne » — marqueur avant la valeur de jour, valeur de nuit avant son marqueur.
    s = ("Concernant le point de mesure situé à proximité du lycée, le niveau sonore de jour "
         "et en semaine est de 60,5 dB(A) et 54,5 en période nocturne.")
    [b] = bruit.parse_levels(s)
    assert b["jour"] == {"valeur": 60.5}
    assert b["nuit"] == {"valeur": 54.5}          # 60,5 (jour) n'est PAS apparié avec 54,5
    assert b["point"] == "à proximité du lycée"


def test_ordre_inverse_plage():
    # Nozay : plage APRÈS le marqueur (« de jour est compris entre 43 et 44,5 »), exige « entre ».
    s = ("Dans les zones à émergence réglementée (ZER), le bruit ambiant calculé en "
         "fonctionnement normal de jour est compris entre 43 et 44,5 dB(A), et entre 41,5 "
         "dB(A) et 44,5 dB(A) de nuit.")
    [b] = bruit.parse_levels(s)
    assert b["jour"] == {"min": 43.0, "max": 44.5}
    assert b["nuit"] == {"min": 41.5, "max": 44.5}


def test_deux_points_dans_une_phrase():
    # Aulnay : « … la nuit CONTRE … au niveau des habitations » = deux points de mesure.
    s = ("Les niveaux acoustiques en limite de projet varient entre 56,6 et 62,6 dB (A) le "
         "jour et 51,7 et 56,7 dB (A) la nuit contre 53,9 et 57 dB (A) le jour et 49,8 et 53 "
         "dB (A) la nuit au niveau des habitations.")
    bands = bruit.parse_levels(s)
    assert len(bands) == 2
    assert bands[0]["point"] == "en limite de projet"
    assert bands[0]["jour"] == {"min": 56.6, "max": 62.6}
    assert bands[1]["point"] == "au niveau des habitations"
    assert bands[1]["nuit"] == {"min": 49.8, "max": 53.0}


def test_metrique_lden_signalee():
    # Meudon : un Lden (24 h) n'est pas comparable à un LAeq — la métrique doit être stockée.
    s = ("Les cartes stratégiques de bruit se situent entre 45 et 60 dB(A) Lden sur 24 h et "
         "40 à 50 dB(A) Ln la nuit.")
    [b] = bruit.parse_levels(s)
    assert b["metrique"] == "Lden/Ln"
    assert b["jour"] == {"min": 45.0, "max": 60.0}
    assert b["nuit"] == {"min": 40.0, "max": 50.0}


# ── ÉMERGENCE : grandeur séparée ─────────────────────────────────────────────────────────────

def test_emergence_jour_nuit_separee_des_niveaux():
    # Meudon, marche dégradée (groupes en fonctionnement) : émergence jour/nuit.
    s = ("Toutefois, en situation dégradée (déclenchement de l’ensemble des groupes "
         "électrogènes), les émergences atteignent jusqu’à 9,1 dB(A) le jour et 14,6 dB(A) la "
         "nuit.")
    assert bruit.parse_levels(s) == []            # une émergence n'est PAS un niveau
    [e] = bruit.parse_emergences(s)
    assert e["jour"] == {"valeur": 9.1}
    assert e["nuit"] == {"valeur": 14.6}


def test_zer_zone_est_un_niveau_pas_une_emergence():
    # « zones à émergence réglementée (ZER) » nomme une ZONE : les dB(A) y sont des NIVEAUX.
    s = ("L’étude mentionne au niveau des zones à émergence réglementée (ZER) des niveaux "
         "sonores de 55-56 dB(A) de jour et de 46 à 53 dB(A) de nuit.")
    assert bruit.parse_emergences(s) == []
    [b] = bruit.parse_levels(s)
    assert b["jour"] == {"min": 55.0, "max": 56.0}


# ── Ce qu'on NE capture pas : cible normative, horaire sans dB ────────────────────────────────

def test_cible_oms_ecartee():
    # Valeur recommandée par l'OMS = une cible, pas une mesure du site. Rien ne sort.
    s = ("rechercher les conditions d’atteinte d’un niveau sonore de 54 dB(A) en diurne et de "
         "45 dB(A) en nocturne pour se rapprocher des valeurs maximales définies par "
         "l’Organisation mondiale de la santé.")
    assert bruit.parse_levels(s) == []


def test_horaires_sans_db_ecartes():
    # « nocturne (22 h – 7h) » : le 7 est un horaire, pas un niveau — aucune dB(A) dans la phrase.
    s = ("Une étude acoustique a été réalisée sur les périodes réglementaires diurne "
         "(7 h - 22 h) et nocturne (22 h – 7h) en limite de propriété et au niveau des "
         "habitations les plus proches.")
    assert bruit.parse_levels(s) == []
    assert bruit.parse_emergences(s) == []


# ── La dérivation réseau-free (`--rederive-bruit`) : ajoute, trace à part, idempotente ────────

def test_rederive_bruit_ajoute_trace_a_part_et_idempotent(tmp_path):
    fiche = {"installation": {"faits": {"bruit": [{
        "indicateur": "bruit_niveau_dba", "valeur": 62.5, "page": 20,
        "phrase": ("Les niveaux acoustiques en limite est de propriété oscillent entre 62,5 "
                   "dB(A) et 65 dB(A) de jour, et entre 59,5 dB(A) et 62 dB(A) en période "
                   "nocturne."),
    }]}}}
    (tmp_path / "f.json").write_text(json.dumps(fiche, ensure_ascii=False), encoding="utf-8")

    s1 = run.rederive_bruit(tmp_path)
    assert s1["fiches_touchees"] == 1 and s1["bandes_ajoutees"] == 1
    d = json.loads((tmp_path / "f.json").read_text())
    bandes = [f for f in d["installation"]["faits"]["bruit"] if f["indicateur"] == "bruit_bandes"]
    assert bandes and bandes[0]["valeur"]["point"] == "en limite est de propriété"
    # trace DISTINCTE du revalidate (deux opérations, deux traces)
    assert "derivation_bruit" in d and "revalidation" not in d
    assert "PLANCHER" in d["derivation_bruit"]["reserve"]
    # couche brute conservée
    assert any(f["indicateur"] == "bruit_niveau_dba" for f in d["installation"]["faits"]["bruit"])
    # idempotente : un second passage n'ajoute rien
    assert run.rederive_bruit(tmp_path)["bandes_ajoutees"] == 0
