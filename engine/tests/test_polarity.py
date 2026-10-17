# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""POLARITÉ — une colonne qui ne peut que pénaliser n'a pas le droit de déplacer une note
quand elle ne pénalise pas.

NÉ D'UNE MESURE, pas d'une intuition (2026-10-17). Poser L1 sur le pilier impact local européen
déplaçait 121 lettres. Rejoué avec la colonne à `neutral` PARTOUT — donc vide de sens — il en
déplaçait encore 102 : l'arithmétique de renormalisation d'un pilier mince, pas la donnée. D'où
l'invariant de calibration (R&D) : **une colonne qui ne porte aucune information déplace ZÉRO
lettre.**

CE QUE CE FICHIER FIGE EST LA DÉRIVATION, PAS UN RÉSULTAT SUR UNE COLONNE. Un test qui se
contenterait de vérifier « L1 ne bouge pas » passerait encore le jour où quelqu'un obtient ce
résultat par un autre chemin — un cas particulier codé en dur, un poids rabaissé à la main. Ce
qu'on veut tenir, c'est : `polarity=penalty_only` ⟹ le plafond de l'échelle est inerte. Et le
test SCOPÉ : la même colonne SANS la déclaration doit, elle, déplacer la note — sinon on ne
prouverait pas que c'est la polarité qui produit l'inertie.
"""

import pytest

from engine.core import GateError
from engine.normalize import is_inert, no_penalty_ceiling

# Échelle à pénalité seule : un état neutre (le plafond) et deux degrés de pénalité.
PEN = {
    "id": "XX", "mvp": True, "block": "base", "pillar": "local_impact",
    "weight_in_pillar": 1.0, "tier": 1, "polarity": "penalty_only",
    "normalization": {"type": "categorical",
                      "categories": {"neutral": 60, "sensitive": 30, "severe": 10}},
}
BIPOLAIRE = {**PEN, "polarity": None,
             "normalization": {"type": "categorical",
                               "categories": {"strong_fit": 90, "neutral": 60, "sensitive": 30}}}


def test_le_plafond_est_derive_du_bareme_pas_recopie():
    # Le plafond n'est pas une constante posée à côté de l'échelle : il EST l'échelle.
    # Une liste d'états inertes tenue à la main dériverait du barème au premier ajout.
    assert no_penalty_ceiling(PEN) == 60
    assert no_penalty_ceiling(BIPOLAIRE) == 90


def test_penalty_only_rend_le_plafond_inerte_et_laisse_penaliser_le_reste():
    assert is_inert(PEN, 60) is True      # aucune pénalité -> n'entre pas dans l'agrégat
    assert is_inert(PEN, 30) is False     # pénalise -> compte
    assert is_inert(PEN, 10) is False
    assert is_inert(PEN, None) is False   # absent reste absent, ce n'est pas la même chose


def test_sans_la_declaration_rien_n_est_inerte():
    """LE CONTRE-TEST. Sans lui, on ne prouverait pas que c'est la POLARITÉ qui produit
    l'inertie — seulement qu'une certaine colonne ne bouge pas, ce qu'un cas particulier codé
    en dur satisferait aussi."""
    for score in (90, 60, 30):
        assert is_inert(BIPOLAIRE, score) is False


def test_une_echelle_continue_refuse_bruyamment():
    """Un indicateur continu n'a pas d'état « neutre » identifiable sans convention inventée.
    Deviner ici produirait une inertie SILENCIEUSE sur une plage de valeurs — exactement la
    famille de panne qu'on passe nos journées à débusquer. On casse le build à la place."""
    continu = {**PEN, "normalization": {"type": "bounded_linear", "min": 0, "max": 100}}
    with pytest.raises(GateError, match="catégorielle"):
        no_penalty_ceiling(continu)


def test_le_mecanisme_est_opt_in_et_inerte_par_defaut(methodology):
    """Aucun indicateur servi ne déclare `polarity` aujourd'hui : poser le mécanisme ne doit
    déplacer AUCUNE note. C'est ce qui permet de l'armer AVANT la décision qui l'emploiera —
    le garde précède ce qu'il garde, au lieu de réparer après coup."""
    declarants = [i["id"] for i in methodology["indicators"] if i.get("polarity") == "penalty_only"]
    assert declarants == [], (
        f"{declarants} déclare(nt) polarity=penalty_only : ce n'est plus un no-op, et le lot "
        "de re-notation correspondant doit avoir été vu et signé avant que ce test change."
    )
