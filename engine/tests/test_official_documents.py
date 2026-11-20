# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Documents officiels (2026-11-20). Règle de Franck : « on ouvre la vérité, on vend le
temps » — la fiche sert le LIEN vers l'autorité et sa DATE, jamais la copie archivée,
l'extraction ou la chronologie. Ces tests tiennent les trois endroits qui doivent dire la
même chose : le schéma (forme), le gate (hôte, calendrier), la table de libellés (un libellé
par type et par langue)."""

import copy
import json
import re
from datetime import date
from pathlib import Path

from engine.artifacts import build_artifacts
from engine.core import DATA_DIR, load_datacenters, load_json, load_methodology
from engine.validate import _schema_errors, official_documents_gate

REPO = Path(__file__).resolve().parents[2]
TABLE = REPO / "site" / "src" / "content" / "documents-officiels.ts"

DOC = {
    "type": "planning_decision",
    "authority": "Mayo County Council",
    "reference": "2460708",
    "date": "2025-04-25",
    "url": "https://www.eplanning.ie/MayoCC/AppFileRefDetails/2460708/0",
    "accessed": "2026-11-20",
    "supports": ["project_status"],
}


def _schema():
    return load_json(DATA_DIR / "schema" / "datacenter.schema.json")


def _une_fiche(docs=None):
    dc = copy.deepcopy(next(iter(load_datacenters().values())))
    if docs is not None:
        dc["identity"]["official_documents"] = docs
    return dc


def _enum(cle: str) -> list[str]:
    items = _schema()["properties"]["identity"]["properties"]["official_documents"]["items"]
    p = items["properties"][cle]
    return p["enum"] if "enum" in p else p["items"]["enum"]


def test_le_schema_accepte_un_document_complet():
    assert _schema_errors(_une_fiche([DOC]), _schema(), "t") == []


def test_une_reference_absente_se_declare_null():
    """Un communiqué de gouverneur n'a pas de numéro : `null`, déclaré. Une chaîne vide, non."""
    assert _schema_errors(_une_fiche([{**DOC, "reference": None}]), _schema(), "t") == []
    assert _schema_errors(_une_fiche([{**DOC, "reference": ""}]), _schema(), "t")
    sans = {k: v for k, v in DOC.items() if k != "reference"}
    assert _schema_errors(_une_fiche([sans]), _schema(), "t"), "la clé reste obligatoire"


def test_le_schema_refuse_un_document_sans_date_ou_hors_contrat():
    schema = _schema()
    for mutation in (
        lambda d: d.pop("date"),
        lambda d: d.update(date="avril 2025"),
        lambda d: d.update(date="2026-07"),
        lambda d: d.update(type="press_article"),
        lambda d: d.update(supports=[]),
        lambda d: d.update(supports=["score"]),
        lambda d: d.update(archive_url="https://pub-x.r2.dev/a.pdf"),
        lambda d: d.update(url="eplanning.ie/x"),
    ):
        doc = copy.deepcopy(DOC)
        mutation(doc)
        assert _schema_errors(_une_fiche([doc]), schema, "t"), f"aurait dû refuser : {doc}"


def _gate(tmp_path, docs, today=date(2026, 11, 20)):
    f = tmp_path / "zz-x.json"
    f.write_text(json.dumps({"identity": {"official_documents": docs}}))
    return official_documents_gate([f], today)


def test_le_gate_laisse_passer_le_site_de_l_autorite(tmp_path):
    assert _gate(tmp_path, [DOC]) == []


def test_le_gate_refuse_nos_copies_et_les_archives(tmp_path):
    for url in ("https://pub-abc.r2.dev/ie/2460708.pdf",
                "https://scoremydatacenter.org/annexes/x.pdf",
                "https://web.archive.org/web/2025/https://www.eplanning.ie/x",
                "https://drive.google.com/file/d/x"):
        assert _gate(tmp_path, [{**DOC, "url": url}]), url


def test_le_gate_refuse_une_date_impossible_future_ou_posterieure_a_la_consultation(tmp_path):
    assert _gate(tmp_path, [{**DOC, "date": "2025-02-30"}])
    assert _gate(tmp_path, [{**DOC, "date": "2027-01-01", "accessed": "2027-01-02"}])
    assert _gate(tmp_path, [{**DOC, "accessed": "2025-01-01"}])


def test_le_gate_refuse_le_meme_lien_deux_fois(tmp_path):
    assert _gate(tmp_path, [DOC, {**DOC, "reference": "autre"}])


def test_chaque_type_et_chaque_fait_atteste_a_son_libelle_dans_chaque_langue():
    """Une liste à deux endroits ment : l'énumération du schéma et la table de libellés sont
    comparées ici. Un type sans libellé rendrait la clé brute sur la fiche, en silence."""
    texte = TABLE.read_text(encoding="utf-8")
    blocs = re.findall(r"^const ([A-Z]{2})(?:: typeof FR)? = \{(.*?)^\};", texte, re.S | re.M)
    assert {b[0] for b in blocs} >= {"FR", "EN", "NL"}
    for langue, corps in blocs:
        for cle in ("types", "supports"):
            sous = re.search(rf"^  {cle}: \{{(.*?)^  \}},", corps, re.S | re.M)
            assert sous, f"{langue}: bloc {cle} introuvable"
            cles = set(re.findall(r"^    (\w+):", sous.group(1), re.M))
            attendu = set(_enum("type" if cle == "types" else "supports"))
            assert cles == attendu, f"{langue}.{cle}: manque {attendu - cles}, en trop {cles - attendu}"


def test_l_artefact_sert_les_documents_du_plus_recent_au_plus_ancien(tmp_path):
    vieux = {**DOC, "date": "2019-03-01", "url": "https://www.pleanala.ie/x"}
    dc = _une_fiche([vieux, DOC])
    sans = copy.deepcopy(dc)
    sans["id"] = sans["id"] + "-sans"
    del sans["identity"]["official_documents"]
    build_artifacts({dc["id"]: dc, sans["id"]: sans}, load_methodology(), out_dir=tmp_path, watchlist=[])
    servi = json.loads((tmp_path / "dc" / f"{dc['id']}.json").read_text())
    assert [d["date"] for d in servi["official_documents"]] == ["2025-04-25", "2019-03-01"]
    assert "official_documents" not in json.loads((tmp_path / "dc" / f"{sans['id']}.json").read_text())
