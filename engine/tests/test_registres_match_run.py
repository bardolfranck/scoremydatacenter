# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Point d'entrée du rattachement (`match_run`). Tests sur FIXTURE, jamais sur le corpus réel
(sinon le test change quand la donnée change). On fige : le filtre par schéma, la réduction du
corpus, la règle du même exploitant (Marcoussis = même site → rattache_multiple ; porteurs
différents → ambigu), l'idempotence, le fait que rien n'est confirmé ni le corpus touché, et
l'échec bruyant (corpus absent/tronqué → sortie non nulle)."""

import copy
import json

from pipelines.registers import match, match_run


def _avis(intitule, commune=None, centroid=None, petitionnaire=None):
    proc = {"intitule": intitule}
    if commune:
        proc["commune"] = commune
    if centroid:
        proc["centroid"] = centroid
    if petitionnaire:
        proc["petitionnaire"] = petitionnaire
    return {"schema": "smdc.registre-ae/1", "procedure": proc, "installation": {"faits": {}}}


def _write(d, p):
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


# ── glue du point d'entrée ───────────────────────────────────────────────────

def test_charger_avis_ne_garde_que_les_fiches_extraction(tmp_path):
    _write(_avis("DC à Nozay", commune="Nozay"), tmp_path / "idf-nozay.json")
    _write({"schema": "smdc.registre-ae.index/1"}, tmp_path / "index.json")
    _write({"schema": "smdc.registre-ae.couverture/1"}, tmp_path / "couverture.json")
    _write({"schema": "smdc.registre-ae.rattachement/1"}, tmp_path / "rattachement.json")
    _write({"fiches": []}, tmp_path / "operateurs-a-renseigner.json")
    assert set(match_run.charger_avis(tmp_path)) == {"idf-nozay"}


def test_corpus_depuis_dcs_reduit_a_commune_operateur_point():
    dcs = {"fr-a": {"identity": {"municipality": "Nozay", "operator": "DATA4",
                                 "coordinates": {"lat": 48.659, "lon": 2.197}, "power_mw": 10}}}
    assert match_run.corpus_depuis_dcs(dcs) == {
        "fr-a": {"municipality": "Nozay", "operator": "DATA4", "coordinates": {"lat": 48.659, "lon": 2.197}}}


# ── la règle du même exploitant (Marcoussis / Marseille) ─────────────────────

def test_meme_exploitant_meme_commune_est_rattache_multiple():
    # Un dossier, deux fiches du MÊME exploitant sur la MÊME commune/point : l'avis couvre un
    # SITE que le corpus découpe en bâtiments → rattache_multiple, pas un choix au hasard.
    corpus = {
        "fr-data4-marcoussis-a": {"municipality": "Marcoussis", "operator": "DATA 4 SAS",
                                  "coordinates": {"lat": 48.6464, "lon": 2.2147}},
        "fr-data4-marcoussis-b": {"municipality": "Marcoussis", "operator": "DATA 4 SERVICES",
                                  "coordinates": {"lat": 48.6464, "lon": 2.2147}},
    }
    avis = {"idf-marcoussis": _avis("data center à Marcoussis", commune="Marcoussis",
                                    centroid={"lat": 48.6464, "lon": 2.2147})}
    p = {x.avis: x for x in match.proposer(avis, corpus)}["idf-marcoussis"]
    assert p.statut == "rattache_multiple"
    assert set(p.fiches) == {"fr-data4-marcoussis-a", "fr-data4-marcoussis-b"}


def test_porteurs_differents_meme_commune_est_ambigu():
    # Même commune/point, exploitants DIFFÉRENTS : on ne choisit pas → ambigu (attend un humain).
    corpus = {
        "fr-op-a": {"municipality": "Marseille", "operator": "SEGRO",
                    "coordinates": {"lat": 43.3, "lon": 5.4}},
        "fr-op-b": {"municipality": "Marseille", "operator": "Interxion France",
                    "coordinates": {"lat": 43.3, "lon": 5.4}},
    }
    avis = {"paca-mrs": _avis("data center à Marseille", commune="Marseille",
                              centroid={"lat": 43.3, "lon": 5.4})}
    p = {x.avis: x for x in match.proposer(avis, corpus)}["paca-mrs"]
    assert p.statut == "ambigu"


# ── propositions, pas des faits ; corpus intact ──────────────────────────────

def test_rien_nest_confirme_et_corpus_intact():
    corpus = {"fr-a": {"municipality": "Nozay", "operator": "DATA4",
                       "coordinates": {"lat": 48.659, "lon": 2.197}}}
    avant = copy.deepcopy(corpus)
    props = match.proposer({"idf-nozay": _avis("DC Nozay", commune="Nozay")}, corpus)
    assert all(not p.confirme for p in props)       # jamais auto-confirmé
    assert corpus == avant                          # proposer ne modifie pas le corpus


def test_ecrire_idempotent(tmp_path):
    corpus = {"fr-a": {"municipality": "Nozay", "operator": "DATA4",
                       "coordinates": {"lat": 48.659, "lon": 2.197}}}
    avis = {"idf-nozay": _avis("DC à Nozay", commune="Nozay", centroid={"lat": 48.659, "lon": 2.197})}
    out = tmp_path / "rattachement.json"
    match.ecrire(match.proposer(avis, corpus), out, "2026-10-01")
    premier = out.read_text()
    match.ecrire(match.proposer(avis, corpus), out, "2026-10-01")
    assert out.read_text() == premier


# ── échec bruyant ────────────────────────────────────────────────────────────

def test_main_refuse_registre_absent(tmp_path):
    assert match_run.main(["--out", str(tmp_path / "pas-la")]) == 2


def test_main_refuse_corpus_absent(tmp_path):
    (tmp_path / "registres").mkdir()
    assert match_run.main(["--out", str(tmp_path / "registres"),
                           "--calibration", str(tmp_path / "pas-de-corpus")]) == 2


def test_main_refuse_corpus_tronque(tmp_path, monkeypatch):
    cal = tmp_path / "calibration"
    (cal / "datacenters").mkdir(parents=True)
    reg = tmp_path / "registres"
    reg.mkdir()
    monkeypatch.setattr(match_run, "load_datacenters", lambda c: {"fr-a": {"identity": {}}})
    assert match_run.main(["--out", str(reg), "--calibration", str(cal)]) == 2   # 1 < 500


def test_main_ecrit_et_idempotent_sur_fixture(tmp_path, monkeypatch):
    cal = tmp_path / "calibration"
    (cal / "datacenters").mkdir(parents=True)
    reg = tmp_path / "registres"
    reg.mkdir()
    _write(_avis("data center à Nozay", commune="Nozay", centroid={"lat": 48.659, "lon": 2.197}),
           reg / "idf-nozay.json")

    def fake(_c):
        dcs = {f"fr-filler-{i}": {"identity": {"municipality": f"Ville{i}", "operator": "X",
                                               "coordinates": {"lat": 40 + i * 0.001, "lon": 2.0}}}
               for i in range(600)}
        dcs["fr-data4-nozay"] = {"identity": {"municipality": "Nozay", "operator": "DATA4",
                                              "coordinates": {"lat": 48.659, "lon": 2.197}}}
        return dcs

    monkeypatch.setattr(match_run, "load_datacenters", fake)
    assert match_run.main(["--out", str(reg), "--calibration", str(cal)]) == 0
    doc = json.loads((reg / "rattachement.json").read_text())
    assert doc["schema"] == "smdc.registre-ae.rattachement/1"
    assert all(p["confirme"] is False for p in doc["propositions"])
    premier = (reg / "rattachement.json").read_text()
    match_run.main(["--out", str(reg), "--calibration", str(cal)])
    assert (reg / "rattachement.json").read_text() == premier   # idempotent de bout en bout
