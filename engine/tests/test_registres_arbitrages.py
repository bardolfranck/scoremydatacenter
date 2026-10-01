# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Liste des arbitrages (point 3/4) : `rattachement-a-arbitrer.json`.

Un cas AMBIGU, c'est plusieurs fiches à score égal que la machine ne doit pas départager. Pour
que l'humain tranche SANS ouvrir le corpus, on lui donne le triplet « fiche (opérateur, commune) »
à côté du pétitionnaire de l'avis. Tests sur fixture, pas sur le corpus réel (sinon le test change
quand la donnée change) — la prod du jour compte 5 ambigus, mais c'est le MÉCANISME qu'on fige.
"""

import json

from pipelines.registers import match, match_run


def _avis(intitule, commune=None, petitionnaire=None):
    proc = {"intitule": intitule}
    if commune:
        proc["commune"] = commune
    if petitionnaire:
        proc["petitionnaire"] = petitionnaire
    return {"schema": "smdc.registre-ae/1", "procedure": proc, "installation": {"faits": {}}}


# Deux fiches, deux exploitants connus DIFFÉRENTS, même commune, pas de géométrie : score égal,
# indiscernables → ambigu (ni rattache_multiple, ni projet_absent).
_CORPUS_AMBIGU = {
    "fr-a": {"municipality": "Marseille", "operator": "Telehouse", "coordinates": None},
    "fr-b": {"municipality": "Marseille", "operator": "Phocea DC", "coordinates": None},
}


def test_arbitrages_formate_le_triplet():
    avis = {"paca-x": _avis("DC à Marseille", commune="Marseille")}
    props = match.proposer(avis, _CORPUS_AMBIGU)
    assert props[0].statut == "ambigu"
    cas = match.arbitrages(props, avis, _CORPUS_AMBIGU)
    assert len(cas) == 1
    assert cas[0]["avis"] == "paca-x"
    assert cas[0]["petitionnaire"] is None
    assert set(cas[0]["candidats"]) == {"fr-a (Telehouse, Marseille)", "fr-b (Phocea DC, Marseille)"}


def test_petitionnaire_vient_de_lavis_et_unknown_est_montre():
    # Une fiche à opérateur inconnu empêche le basculement en projet_absent → reste ambigu ;
    # le pétitionnaire de l'avis (qui ne matche personne) est reporté ; `unknown` est affiché.
    corpus = dict(_CORPUS_AMBIGU, **{"fr-c": {"municipality": "Marseille", "operator": "unknown",
                                              "coordinates": None}})
    avis = {"paca-y": _avis("projet mixte à Marseille", commune="Marseille", petitionnaire="SEGRO")}
    props = match.proposer(avis, corpus)
    assert props[0].statut == "ambigu"
    cas = match.arbitrages(props, avis, corpus)
    assert cas[0]["petitionnaire"] == "SEGRO"
    assert "fr-c (unknown, Marseille)" in cas[0]["candidats"]


def test_seuls_les_ambigus_sortent():
    # Un avis nettement rattaché (géométrie proche + commune) n'est PAS un arbitrage.
    corpus = {"fr-nozay": {"municipality": "Nozay", "operator": "DATA4",
                           "coordinates": {"lat": 48.659, "lon": 2.197}}}
    avis = {"idf-nozay": _avis("DC à Nozay", commune="Nozay")}
    avis["idf-nozay"]["procedure"]["centroid"] = {"lat": 48.659, "lon": 2.197}
    props = match.proposer(avis, corpus)
    assert props[0].statut != "ambigu"
    assert match.arbitrages(props, avis, corpus) == []


def test_ecrire_arbitrages_envelope_et_idempotent(tmp_path):
    avis = {"paca-x": _avis("DC à Marseille", commune="Marseille")}
    props = match.proposer(avis, _CORPUS_AMBIGU)
    out = tmp_path / "rattachement-a-arbitrer.json"
    doc = match.ecrire_arbitrages(props, avis, _CORPUS_AMBIGU, out, "2026-10-01")
    assert doc["schema"] == "smdc.registre-ae.arbitrage/1"
    assert len(doc["cas"]) == 1
    premier = out.read_text()
    match.ecrire_arbitrages(match.proposer(avis, _CORPUS_AMBIGU), avis, _CORPUS_AMBIGU, out, "2026-10-01")
    assert out.read_text() == premier    # idempotent


# ── le point d'entrée écrit le fichier à chaque passage ───────────────────────

def _fake_corpus(_cal):
    dcs = {f"fr-filler-{i}": {"identity": {"municipality": f"Ville{i}", "operator": "X",
                                           "coordinates": {"lat": 40 + i * 0.001, "lon": 2.0}}}
           for i in range(600)}
    dcs["fr-a"] = {"identity": {"municipality": "Marseille", "operator": "Telehouse", "coordinates": None}}
    dcs["fr-b"] = {"identity": {"municipality": "Marseille", "operator": "Phocea DC", "coordinates": None}}
    return dcs


def test_point_dentree_ecrit_le_fichier_darbitrage(tmp_path, monkeypatch):
    cal = tmp_path / "calibration"
    (cal / "datacenters").mkdir(parents=True)
    reg = tmp_path / "registres"
    reg.mkdir()
    (reg / "paca-x.json").write_text(json.dumps(_avis("DC à Marseille", commune="Marseille")), encoding="utf-8")
    monkeypatch.setattr(match_run, "load_datacenters", _fake_corpus)
    assert match_run.main(["--out", str(reg), "--calibration", str(cal)]) == 0
    doc = json.loads((reg / "rattachement-a-arbitrer.json").read_text())
    assert doc["schema"] == "smdc.registre-ae.arbitrage/1"
    assert [c["avis"] for c in doc["cas"]] == ["paca-x"]
    assert set(doc["cas"][0]["candidats"]) == {"fr-a (Telehouse, Marseille)", "fr-b (Phocea DC, Marseille)"}
