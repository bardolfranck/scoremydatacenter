# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Liste des opérateurs à renseigner (point 4/4) : `operateurs-a-renseigner.json`.

Un avis nomme le pétitionnaire d'un projet ; quand ce projet est rattaché avec confiance à une
fiche SANS opérateur, l'avis peut combler le manque — l'acte EST la provenance (patron Goodman).
La liste SIGNALE, elle ne décide pas : elle inclut une fiche même sans pétitionnaire (fr-equinix),
pour qu'un humain la voie sans que rien ne soit écrit à sa place. Tests sur fixture — la prod du
jour en compte deux (fr-goodman ← Goodman France ; fr-equinix ← pétitionnaire absent).
"""

import json

from pipelines.registers import match, match_run

_P = {"lat": 48.659, "lon": 2.197}


def _avis(intitule, commune=None, centroid=None, petitionnaire=None):
    proc = {"intitule": intitule}
    if commune:
        proc["commune"] = commune
    if centroid:
        proc["centroid"] = centroid
    if petitionnaire:
        proc["petitionnaire"] = petitionnaire
    return {"schema": "smdc.registre-ae/1", "procedure": proc, "installation": {"faits": {}}}


def test_propose_operateur_inconnu_est_liste_avec_le_petitionnaire():
    corpus = {"fr-x": {"municipality": "Nozay", "operator": "unknown", "coordinates": _P}}
    avis = {"idf-nozay": _avis("DC à Nozay", commune="Nozay", centroid=_P, petitionnaire="DATA 4")}
    props = match.proposer(avis, corpus)
    assert props[0].statut == "rattache_propose"
    rows = match.operateurs_a_renseigner(props, avis, corpus)
    assert rows == [{"fiche": "fr-x", "commune": "Nozay", "avis": "idf-nozay",
                     "petitionnaire": "DATA 4", "statut_rattachement": "rattache_propose"}]


def test_operateur_connu_nest_pas_liste():
    corpus = {"fr-y": {"municipality": "Nozay", "operator": "DATA4", "coordinates": _P}}
    avis = {"idf-nozay": _avis("DC à Nozay", commune="Nozay", centroid=_P)}
    props = match.proposer(avis, corpus)
    assert match.operateurs_a_renseigner(props, avis, corpus) == []


def test_multiple_ne_liste_que_la_fiche_inconnue_meme_sans_petitionnaire():
    # fr-equinix réel : rattache_multiple, une fiche sans opérateur, l'avis ne nomme personne →
    # listée avec petitionnaire None (signalée, surtout pas renseignée).
    corpus = {"fr-a": {"municipality": "Marseille", "operator": "Equinix", "coordinates": _P},
              "fr-b": {"municipality": "Marseille", "operator": "unknown", "coordinates": _P}}
    avis = {"idf-m": _avis("DC à Marseille", commune="Marseille", centroid=_P)}
    props = match.proposer(avis, corpus)
    assert props[0].statut == "rattache_multiple"
    rows = match.operateurs_a_renseigner(props, avis, corpus)
    assert rows == [{"fiche": "fr-b", "commune": "Marseille", "avis": "idf-m",
                     "petitionnaire": None, "statut_rattachement": "rattache_multiple"}]


def test_a_confirmer_et_ambigu_ne_sont_pas_renseignes():
    # Deux exploitants connus différents, commune seule → ambigu : pas assez établi pour renseigner.
    corpus = {"fr-a": {"municipality": "Marseille", "operator": "Telehouse", "coordinates": None},
              "fr-b": {"municipality": "Marseille", "operator": "Phocea DC", "coordinates": None}}
    avis = {"paca-x": _avis("DC à Marseille", commune="Marseille")}
    props = match.proposer(avis, corpus)
    assert props[0].statut == "ambigu"
    assert match.operateurs_a_renseigner(props, avis, corpus) == []


def test_ecrire_operateurs_envelope_et_idempotent(tmp_path):
    corpus = {"fr-x": {"municipality": "Nozay", "operator": "unknown", "coordinates": _P}}
    avis = {"idf-nozay": _avis("DC à Nozay", commune="Nozay", centroid=_P, petitionnaire="DATA 4")}
    props = match.proposer(avis, corpus)
    out = tmp_path / "operateurs-a-renseigner.json"
    doc = match.ecrire_operateurs(props, avis, corpus, out, "2026-10-01")
    assert doc["schema"] == "smdc.registre-ae.operateurs/1"
    assert len(doc["fiches"]) == 1
    premier = out.read_text()
    match.ecrire_operateurs(match.proposer(avis, corpus), avis, corpus, out, "2026-10-01")
    assert out.read_text() == premier


def _fake_corpus(_cal):
    dcs = {f"fr-filler-{i}": {"identity": {"municipality": f"Ville{i}", "operator": "X",
                                           "coordinates": {"lat": 40 + i * 0.001, "lon": 2.0}}}
           for i in range(600)}
    dcs["fr-x"] = {"identity": {"municipality": "Nozay", "operator": "unknown", "coordinates": _P}}
    return dcs


def test_point_dentree_ecrit_le_fichier_operateurs(tmp_path, monkeypatch):
    cal = tmp_path / "calibration"
    (cal / "datacenters").mkdir(parents=True)
    reg = tmp_path / "registres"
    reg.mkdir()
    (reg / "idf-nozay.json").write_text(
        json.dumps(_avis("DC à Nozay", commune="Nozay", centroid=_P, petitionnaire="DATA 4")), encoding="utf-8")
    monkeypatch.setattr(match_run, "load_datacenters", _fake_corpus)
    assert match_run.main(["--out", str(reg), "--calibration", str(cal)]) == 0
    doc = json.loads((reg / "operateurs-a-renseigner.json").read_text())
    assert doc["schema"] == "smdc.registre-ae.operateurs/1"
    assert [f["fiche"] for f in doc["fiches"]] == ["fr-x"]
    assert doc["fiches"][0]["petitionnaire"] == "DATA 4"
