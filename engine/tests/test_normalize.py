# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
import pytest

from engine.core import GateError
from engine.normalize import normalized_score


def _definition(methodology, indicator_id):
    return next(i for i in methodology["indicators"] if i["id"] == indicator_id)


def _entry(indicator_id, value, status="measured"):
    return {"id": indicator_id, "value": value, "status": status,
            "source": {"title": "t", "url": "https://example.org", "accessed": "2026-07-01"}}


def test_thresholds_boundaries_inclusive(methodology, parameters):
    e1 = _definition(methodology, "E1")  # <=50:100, <=150:60, <=400:30, above:0
    for value, expected in [(50, 100), (50.1, 60), (150, 60), (400, 30), (401, 0)]:
        assert normalized_score(e1, _entry("E1", value), parameters) == expected


def test_bounded_linear_higher_is_better_with_clamp(methodology, parameters):
    l4 = _definition(methodology, "L4")  # 0..50 jobs per 100 MW
    entry = _entry("L4", 25, status="announced")
    capped = normalized_score(l4, entry, parameters)
    assert capped == 50  # 50/100 linear, below the declarative cap
    entry_high = _entry("L4", 999, status="announced")
    assert normalized_score(l4, entry_high, parameters) == parameters["declarative_score_cap"]  # clamp then cap


def test_categorical_lookup_and_rejection(methodology, parameters):
    w1 = _definition(methodology, "W1")
    assert normalized_score(w1, _entry("W1", "zre_or_crisis"), parameters) == 0
    with pytest.raises(GateError):
        normalized_score(w1, _entry("W1", "not_a_category"), parameters)


def test_proxy_rubric_alpha_case(methodology, parameters, alpha):
    t1_def = _definition(methodology, "T1")
    t1 = next(e for e in alpha["indicators"] if e["id"] == "T1")
    # inquiry(25) + AE with reservations(15) + no CNDP(5) + 0 appeals(20) + council favorable(15)
    assert normalized_score(t1_def, t1, parameters) == 80


def test_declarative_cap_applies_to_announced_only(methodology, parameters):
    e4 = _definition(methodology, "E4")  # PUE 1.18 normalizes to 100
    announced = _entry("E4", 1.18, status="announced")
    assert normalized_score(e4, announced, parameters) == parameters["declarative_score_cap"]
    measured = _entry("E4", 1.18, status="measured")
    measured["verification_source"] = measured["source"]
    assert normalized_score(e4, measured, parameters) == 100  # ex-post verified: uncapped


def test_missing_returns_none(methodology, parameters):
    e4 = _definition(methodology, "E4")
    assert normalized_score(e4, {"id": "E4", "status": "missing"}, parameters) is None


def test_estimated_capped_like_announced_never_uncapped(methodology, parameters):
    # 1c contract (2026-07-27): our model output scores AT MOST as prudently as an operator
    # claim — the estimate can never look better-documented than a declaration.
    e4 = _definition(methodology, "E4")  # PUE 1.18 normalizes to 100 uncapped
    estimated = _entry("E4", 1.18, status="estimated")
    assert normalized_score(e4, estimated, parameters) == parameters["declarative_score_cap"]


# ---------------------------------------------------------------------------
# log_linear — une grandeur qui vit sur plusieurs décades (L2, bassin de 50 km)
# ---------------------------------------------------------------------------

def _def_log(**norm):
    """Définition minimale portant une normalisation log_linear, hors méthodologie servie :
    le barème se juge sur ses bornes, pas sur l'état du corpus du jour."""
    base = {"type": "log_linear", "ratio_full": 1e-4, "ratio_zero": 1e2}
    base.update(norm)
    return {"id": "L2", "direction": "lower_is_better", "normalization": base}


def test_log_linear_tient_ses_trois_ancres(parameters):
    """100 à l'ancre basse, 0 à l'ancre haute, 50 au milieu GÉOMÉTRIQUE.

    Le milieu d'une échelle logarithmique n'est pas la moyenne des bornes : entre 1e-4 et
    1e2, il est à 1e-1, pas à 50. Un test qui vérifierait 50 au milieu arithmétique
    validerait une courbe linéaire déguisée.
    """
    d = _def_log()
    assert normalized_score(d, _entry("L2", 1e-4), parameters) == 100
    assert normalized_score(d, _entry("L2", 1e2), parameters) == 0
    assert normalized_score(d, _entry("L2", 1e-1), parameters) == pytest.approx(50)
    # Une décade vaut 100/6 de point, puisque l'étendue fait six décades.
    assert normalized_score(d, _entry("L2", 1e-3), parameters) == pytest.approx(100 - 100 / 6)


def test_log_linear_ecrete_aux_bornes_et_accepte_le_ratio_nul(parameters):
    """Jamais d'extrapolation, et log10(0) n'arrive pas.

    Un ratio nul est un ratio PARFAIT (aucune puissance pour des habitants), pas un
    logarithme impossible : il s'écrête à l'ancre basse. C'est la ligne qui garde la
    fonction de lever une exception sur une fiche légitime.
    """
    d = _def_log()
    assert normalized_score(d, _entry("L2", 0), parameters) == 100
    assert normalized_score(d, _entry("L2", 1e-9), parameters) == 100
    assert normalized_score(d, _entry("L2", 1e9), parameters) == 0


def test_log_linear_refuse_une_echelle_sans_sens_de_lecture(parameters):
    """Trois refus, parce qu'une échelle de ratio n'a ni zéro ni direction implicite."""
    for mauvais in ({"ratio_full": 0}, {"ratio_full": -1}, {"ratio_zero": 0}):
        with pytest.raises(GateError, match="log_linear"):
            normalized_score(_def_log(**mauvais), _entry("L2", 1), parameters)
    # bornes inversées : la pente n'aurait plus de sens
    with pytest.raises(GateError, match="ratio_zero > ratio_full"):
        normalized_score(_def_log(ratio_full=1e2, ratio_zero=1e-4), _entry("L2", 1), parameters)
    # bornes égales : étendue nulle
    with pytest.raises(GateError, match="ratio_zero > ratio_full"):
        normalized_score(_def_log(ratio_full=1.0, ratio_zero=1.0), _entry("L2", 1), parameters)
    with pytest.raises(GateError, match="ratio >= 0"):
        normalized_score(_def_log(), _entry("L2", -0.5), parameters)


def test_log_linear_sous_le_plafond_declaratif_cest_la_seule_part_visible(parameters):
    """🔴 CE QUE LA COURBE CHANGE VRAIMENT, SUR CE QUI EST SERVI.

    Aucune L2 du corpus n'est `measured` : au 2026-11-08, 194 sont `announced` et 81
    `estimated`, donc TOUTES sont plafonnées à `declarative_score_cap` (60). La courbe n'est
    donc visible que là où elle descend SOUS le plafond — au-dessus, c'est le plafond qui
    décide, et deux barèmes très différents y rendent le même nombre.

    Ce test fige ce fait, parce que c'est l'erreur qu'on a faite en mesurant le barème :
    on avait annoncé « 86 % des fiches au score 100 » en lisant la normalisation NUE, alors
    que 100 est inatteignable sur cet indicateur. Un barème se mesure après le plafond.
    """
    cap = parameters["declarative_score_cap"]
    d = _def_log()
    # Le ratio où la courbe croise le plafond : 100·(2 − log10 r)/6 = cap.
    croisement = 10 ** (2 - cap * 6 / 100)
    assert normalized_score(d, _entry("L2", croisement / 10, status="announced"), parameters) == cap
    assert normalized_score(d, _entry("L2", croisement / 10, status="measured"), parameters) > cap
    # Sous le plafond, la courbe se voit : deux ratios séparés d'une décade diffèrent.
    bas = normalized_score(d, _entry("L2", croisement * 10, status="announced"), parameters)
    plus_bas = normalized_score(d, _entry("L2", croisement * 100, status="announced"), parameters)
    assert cap > bas > plus_bas >= 0
    assert bas - plus_bas == pytest.approx(100 / 6)
    # Et le plafond n'invente pas de discrimination : au-dessus, tout est écrasé au plafond.
    assert normalized_score(d, _entry("L2", 1e-8, status="estimated"), parameters) == cap


def test_le_dispatcher_refuse_toujours_un_barème_inconnu(parameters):
    """Le garde qui rend l'ajout d'un type SÛR : un barème non câblé ne passe pas en silence."""
    d = {"id": "L2", "direction": "lower_is_better",
         "normalization": {"type": "log_lineaire_mal_orthographie"}}
    with pytest.raises(GateError, match="unknown normalization type"):
        normalized_score(d, _entry("L2", 1), parameters)
