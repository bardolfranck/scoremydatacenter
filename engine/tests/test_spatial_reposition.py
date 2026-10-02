# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Repositionnement d'une fiche servie (pipelines.spatial.reposition). On fige le CONTRAT :
re-mesurer ce qui dépend du point, CONSERVER les nationaux / la saisie main / le non-collecté,
et ne JAMAIS perdre une clé ou un indicateur. Hors réseau — build_draft et E6 sont injectés."""
import json

import pytest

from pipelines.spatial import reposition as R
from pipelines.spatial.collect import FR_SPEC
from pipelines.spatial.country import national_indicators


def _servie():
    return {
        "schema_version": "1.0",
        "id": "fr-x",
        "identity": {
            "name": "X", "operator": "OpX", "municipality": "Sarzay", "admin_area": "36",
            "country": "FR", "coordinates": {"lat": 46.60, "lon": 1.88},
            "project_status": "operational",
            "summary": {"fr": "synthèse rédigée à conserver", "en": "hand-written, keep"},
        },
        "indicators": [
            {"id": "E1", "status": "measured", "value": 17.6},          # national → conservé
            {"id": "W1", "status": "measured", "value": "vieux_w1",     # point → re-mesuré
             "source": {"title": "VigiEau ancien", "url": "https://vigieau.example/x", "accessed": "2026-07-30"}},
            {"id": "F3", "status": "missing", "value": None},           # saisie main → conservé
            {"id": "E4", "status": "not_collected", "value": None},     # conservé
            {"id": "E6", "status": "measured", "value": "eloigne"},     # point hors collect()
        ],
        "publication": {"status": "draft", "operator_response": None},
        "score_history": [],
    }


def _fake_fragment():
    # build_draft au NOUVEAU point : nouvelle commune + valeurs point rafraîchies.
    return (
        {
            "identity": {
                "name": "X", "operator": "OpX", "municipality": "Sartrouville", "admin_area": "78",
                "country": "FR", "coordinates": {"lat": 48.94, "lon": 2.18},
                "project_status": "operational", "summary": {"fr": "BROUILLON", "en": "DRAFT"},
            },
            "indicators": [
                {"id": "E1", "status": "measured", "value": 99.9},       # piège : NE doit PAS écraser
                {"id": "W1", "status": "measured", "value": "neuf_w1"},  # doit écraser
                {"id": "F3", "status": "missing", "value": None},        # padding, ne doit pas écraser
                {"id": "E4", "status": "not_collected", "value": None},
                {"id": "E6", "status": "not_collected", "value": None},  # padding E6
            ],
        },
        {"commune_insee": "78586"}, [],
    )


@pytest.fixture
def patched(monkeypatch):
    monkeypatch.setattr(R, "fiche_servie", lambda dc_id, newsroom: ("p", _servie()))
    monkeypatch.setattr(R, "build_draft", lambda *a, **k: _fake_fragment())
    monkeypatch.setattr(R.heat_network, "load_fcu", lambda d: {"nets": [], "polys": []})
    monkeypatch.setattr(R.heat_network, "e6_at",
                        lambda lat, lon, fcu, accessed: {"id": "E6", "status": "measured",
                                                         "value": "raccordable"})


def _by_id(fiche):
    return {i["id"]: i for i in fiche["indicators"]}


def test_national_lu_dans_le_spec():
    assert national_indicators(FR_SPEC) == frozenset({"E1"})


def test_point_remesure_national_conserve(patched):
    res, rap = R.reposition("fr-x", 48.94, 2.18, newsroom="ns", accessed="2026-10-02",
                            fcu_dir="/fcu")
    ind = _by_id(res)
    assert ind["W1"]["value"] == "neuf_w1"       # point re-mesuré
    assert ind["E1"]["value"] == 17.6            # national CONSERVÉ (pas le 99.9 du fragment)
    assert "E1" in rap["conserves_nationaux"] and "W1" in rap["remesurees_avec_valeur"]
    assert rap["retrogradees"] == []       # rien perdu dans ce cas


def test_saisie_main_et_non_collecte_conserves(patched):
    res, _ = R.reposition("fr-x", 48.94, 2.18, newsroom="ns", accessed="2026-10-02", fcu_dir="/fcu")
    ind = _by_id(res)
    assert ind["F3"]["status"] == "missing"          # saisie main intacte
    assert ind["E4"]["status"] == "not_collected"


def test_e6_remesure_quand_fcu(patched):
    res, rap = R.reposition("fr-x", 48.94, 2.18, newsroom="ns", accessed="2026-10-02", fcu_dir="/fcu")
    assert _by_id(res)["E6"]["value"] == "raccordable"   # jamais l'ancien "eloigne"
    assert "E6" in rap["remesurees_avec_valeur"]


def test_e6_mesure_sans_fcu_refuse(patched):
    with pytest.raises(SystemExit):
        R.reposition("fr-x", 48.94, 2.18, newsroom="ns", accessed="2026-10-02", fcu_dir=None)


def test_identite_commune_et_coord_suivent_le_point(patched):
    res, _ = R.reposition("fr-x", 48.94, 2.18, newsroom="ns", accessed="2026-10-02", fcu_dir="/fcu")
    idt = res["identity"]
    assert idt["municipality"] == "Sartrouville" and idt["admin_area"] == "78"
    assert idt["coordinates"] == {"lat": 48.94, "lon": 2.18}
    # vérité servie conservée
    assert idt["name"] == "X" and idt["operator"] == "OpX"
    assert idt["summary"]["fr"] == "synthèse rédigée à conserver"


def test_rien_perdu_et_ordre_conserve(patched):
    servie = _servie()
    res, rap = R.reposition("fr-x", 48.94, 2.18, newsroom="ns", accessed="2026-10-02", fcu_dir="/fcu")
    assert [i["id"] for i in res["indicators"]] == [i["id"] for i in servie["indicators"]]
    assert rap["cles_racine_identiques"] and rap["ids_indicateurs_identiques"]
    assert res["score_history"] == []     # jamais écrit par le repositionnement (réservé moteur)


def test_retrograde_mesure_perdue_est_signale(monkeypatch):
    # Cas W3 réel : collecteur revenu vide à la nouvelle commune → la mesure servie est PERDUE.
    # On NE conserve PAS l'ancienne valeur (elle décrirait l'autre lieu) et on le SIGNALE fort.
    monkeypatch.setattr(R, "fiche_servie", lambda dc_id, newsroom: ("p", _servie()))
    monkeypatch.setattr(R.heat_network, "load_fcu", lambda d: {"nets": [], "polys": []})
    monkeypatch.setattr(R.heat_network, "e6_at",
                        lambda *a, **k: {"id": "E6", "status": "measured", "value": "eloigne"})
    frag, prov, _ = _fake_fragment()
    for i in frag["indicators"]:
        if i["id"] == "W1":                      # le collecteur W1 revient vide → padding missing
            i["status"], i["value"] = "missing", None
    monkeypatch.setattr(R, "build_draft", lambda *a, **k: (frag, prov, ["W1"]))

    res, rap = R.reposition("fr-x", 48.94, 2.18, newsroom="ns", accessed="2026-10-02", fcu_dir="/fcu")
    w1 = _by_id(res)["W1"]
    assert w1["status"] == "missing" and w1.get("value") != "vieux_w1"   # ancienne valeur PAS conservée
    assert rap["retrogradees"] == ["W1"]                 # signalé fort
    assert "W1" in rap["collecteurs_revenus_vides"]
    assert "W1" not in rap["remesurees_avec_valeur"]
    # motif publié (leçon Caparéseau) : source avec title+url+accessed, url d'origine réutilisée
    assert "revenu vide pour la commune 78586" in w1["source"]["title"]
    assert w1["source"]["url"] == "https://vigieau.example/x" and w1["source"]["accessed"] == "2026-10-02"


def test_valeurs_changees_rapportees(patched):
    _res, rap = R.reposition("fr-x", 48.94, 2.18, newsroom="ns", accessed="2026-10-02", fcu_dir="/fcu")
    assert "W1" in rap["valeurs_changees"] and "E6" in rap["valeurs_changees"]
    assert "E1" not in rap["valeurs_changees"]   # national inchangé
