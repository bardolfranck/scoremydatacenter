# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Détection de projets (point 2/4) : les avis que l'État documente et que le corpus ignore.

La règle du chantier : `projets_a_collecter` est écrite À CHAQUE PASSAGE, pas seulement quand
quelqu'un pense à la regarder. Un détecteur qui ne vit que dans la tête de celui qui a fait le
run ne détecte rien au run suivant. Ces tests FIGENT la garantie, et la lient au POINT D'ENTRÉE
(match_run), pas seulement au helper — pour qu'une refonte future ne puisse pas laisser tomber
la clé en silence.

Les cinq d'aujourd'hui (tous `non_rattache` : Tigery, appaca43, Bonneuil-SEGRO, Blyes, Pessac)
sont la référence de production ; ici on teste le MÉCANISME sur fixture, pas ce lot (sinon le
test change quand la donnée change).
"""

import json

from pipelines.registers import match, match_run


def _avis(intitule, commune=None, centroid=None):
    proc = {"intitule": intitule}
    if commune:
        proc["commune"] = commune
    if centroid:
        proc["centroid"] = centroid
    return {"schema": "smdc.registre-ae/1", "procedure": proc, "installation": {"faits": {}}}


# ── le helper pur ─────────────────────────────────────────────────────────────

def test_projets_candidats_capture_les_non_rattaches():
    # Un avis dont la commune est inconnue du corpus, sans géométrie → aucun candidat →
    # non_rattache → doit ressortir comme projet à collecter.
    corpus = {"fr-lyon": {"municipality": "Lyon", "operator": "X", "coordinates": {"lat": 45.7, "lon": 4.8}}}
    props = match.proposer({"mrae-tigery": _avis("data center à Tigery (91)")}, corpus)
    assert props[0].statut == "non_rattache"
    cand = match.projets_candidats(props)
    assert [c["avis"] for c in cand] == ["mrae-tigery"]


def test_un_avis_rattache_nest_pas_un_projet_a_collecter():
    corpus = {"fr-nozay": {"municipality": "Nozay", "operator": "DATA4",
                           "coordinates": {"lat": 48.659, "lon": 2.197}}}
    props = match.proposer(
        {"idf-nozay": _avis("DC à Nozay", commune="Nozay", centroid={"lat": 48.659, "lon": 2.197})}, corpus)
    assert match.projets_candidats(props) == []


# ── la clé est écrite À CHAQUE PASSAGE, par le point d'entrée ──────────────────

def _fixture_newsroom(tmp_path, avis_par_nom):
    cal = tmp_path / "calibration"
    (cal / "datacenters").mkdir(parents=True)
    reg = tmp_path / "registres"
    reg.mkdir()
    for nom, doc in avis_par_nom.items():
        (reg / f"{nom}.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return cal, reg


def _fake_corpus(_cal):
    dcs = {f"fr-filler-{i}": {"identity": {"municipality": f"Ville{i}", "operator": "X",
                                           "coordinates": {"lat": 40 + i * 0.001, "lon": 2.0}}}
           for i in range(600)}
    dcs["fr-data4-nozay"] = {"identity": {"municipality": "Nozay", "operator": "DATA4",
                                          "coordinates": {"lat": 48.659, "lon": 2.197}}}
    return dcs


def test_point_dentree_ecrit_la_cle_avec_un_projet(tmp_path, monkeypatch):
    # Un avis rattachable (Nozay) + un non rattachable (Tigery) : la clé liste le second.
    cal, reg = _fixture_newsroom(tmp_path, {
        "idf-nozay": _avis("DC à Nozay", commune="Nozay", centroid={"lat": 48.659, "lon": 2.197}),
        "mrae-tigery": _avis("data center à Tigery (91)"),
    })
    monkeypatch.setattr(match_run, "load_datacenters", _fake_corpus)
    assert match_run.main(["--out", str(reg), "--calibration", str(cal)]) == 0
    doc = json.loads((reg / "rattachement.json").read_text())
    assert isinstance(doc["projets_a_collecter"], list)
    assert [c["avis"] for c in doc["projets_a_collecter"]] == ["mrae-tigery"]


def test_point_dentree_ecrit_la_cle_meme_vide(tmp_path, monkeypatch):
    # Tous les avis rattachés : la clé existe QUAND MÊME, en liste vide (pas absente).
    cal, reg = _fixture_newsroom(tmp_path, {
        "idf-nozay": _avis("DC à Nozay", commune="Nozay", centroid={"lat": 48.659, "lon": 2.197}),
    })
    monkeypatch.setattr(match_run, "load_datacenters", _fake_corpus)
    assert match_run.main(["--out", str(reg), "--calibration", str(cal)]) == 0
    doc = json.loads((reg / "rattachement.json").read_text())
    assert "projets_a_collecter" in doc
    assert doc["projets_a_collecter"] == []


def test_la_cle_est_reecrite_a_chaque_passage(tmp_path, monkeypatch):
    # Elle ne dépend pas d'un fichier préexistant : écrite identique à chaque run.
    cal, reg = _fixture_newsroom(tmp_path, {"mrae-tigery": _avis("data center à Tigery (91)")})
    monkeypatch.setattr(match_run, "load_datacenters", _fake_corpus)
    match_run.main(["--out", str(reg), "--calibration", str(cal)])
    un = json.loads((reg / "rattachement.json").read_text())["projets_a_collecter"]
    match_run.main(["--out", str(reg), "--calibration", str(cal)])
    deux = json.loads((reg / "rattachement.json").read_text())["projets_a_collecter"]
    assert un == deux == [{"avis": "mrae-tigery",
                           "intitule": "data center à Tigery (91)",
                           "statut": "non_rattache",
                           "exploitant_dans_le_document": None,
                           "communes_candidates": None}]
