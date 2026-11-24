# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""« Même adresse, autre activité » (Franck 2026-11-24). Sous-rubrique des documents officiels :
des actes officiels sur une AUTRE activité de l'exploitant à la même adresse (un centre de
supervision réseau, des bureaux…). Cas d'origine : Swisscom Zurich-Binz, autorisation SECO
AB02-0000016905 pour le « Network Monitoring Center » de Binzring 17 — vraie, rare, mais pas
une preuve du data center.

Ces tests tiennent les quatre conditions :
  - chaque acte dit ce qu'il vise (libellé de contexte, FR et EN exigés, NL avec repli) ;
  - il date une étape de l'histoire du site (« pour ne pas TOUT collecter ») ;
  - l'exploitant et l'adresse sont vérifiés (≤ 300 m), jamais supposés ;
  - il ne prouve RIEN du data center : pas de `supports`, et un champ à part, que les
    lecteurs de preuves (statut, existence, couverture) ne lisent pas."""

import copy
import json
import re
from datetime import date
from pathlib import Path

from engine.artifacts import build_artifacts
from engine.core import DATA_DIR, load_datacenters, load_json, load_methodology
from engine.validate import _schema_errors, documents_dictionary_gate, official_documents_gate

REPO = Path(__file__).resolve().parents[2]
TABLE = REPO / "site" / "src" / "content" / "documents-officiels.ts"

BINZ = {
    "type": "labour_permit",
    "authority": "Staatssekretariat für Wirtschaft SECO",
    "reference": "AB02-0000016905",
    "date": "2024-09-30",
    "url": "https://amtsblattportal.ch/api/v1/publications/x/pdf",
    "accessed": "2026-11-23",
    "activity": {"fr": "centre de supervision réseau de Swisscom",
                 "en": "Swisscom network operations centre",
                 "nl": "netwerkbewakingscentrum van Swisscom"},
    "site_event": "permit",
    "match": {"operator": "Swisscom (Schweiz) AG", "address": "Binzring 17, 8045 Zürich",
              "distance_m": 28},
}


def _schema():
    return load_json(DATA_DIR / "schema" / "datacenter.schema.json")


def _items(champ):
    return _schema()["properties"]["identity"]["properties"][champ]["items"]


def _fiche(**ident):
    dc = copy.deepcopy(next(iter(load_datacenters().values())))
    dc["identity"].update(ident)
    return dc


def test_le_schema_accepte_l_acte_de_binz():
    assert _schema_errors(_fiche(same_address_documents=[BINZ]), _schema(), "t") == []


def test_le_schema_refuse_un_acte_sans_contexte_sans_etape_ou_trop_loin():
    schema = _schema()
    for mutation in (
        lambda d: d.pop("activity"),
        lambda d: d["activity"].pop("en"),               # fr et en exigés (nl : repli)
        lambda d: d["activity"].update(fr=""),
        lambda d: d.pop("site_event"),                    # ne raconte rien du site : pas collecté
        lambda d: d.update(site_event="other"),
        lambda d: d.pop("match"),
        lambda d: d["match"].update(distance_m=301),      # au-delà, c'est un autre site
        lambda d: d["match"].pop("operator"),
        lambda d: d.update(supports=["existence"]),       # jamais une preuve du data center
        lambda d: d.pop("date"),
    ):
        doc = copy.deepcopy(BINZ)
        mutation(doc)
        assert _schema_errors(_fiche(same_address_documents=[doc]), schema, "t"), f"aurait dû refuser : {doc}"


def test_les_champs_communs_sont_ceux_des_documents_officiels():
    """Une liste à deux endroits ment : la sous-rubrique reprend la forme des actes officiels
    (type, autorité, référence, dates, lien), à l'identique — seule `supports` est retirée."""
    off, meme = _items("official_documents"), _items("same_address_documents")
    for cle, defn in off["properties"].items():
        if cle == "supports":
            assert cle not in meme["properties"]
            continue
        assert meme["properties"][cle] == defn, cle
    assert set(off["required"]) - {"supports"} <= set(meme["required"])
    assert meme["allOf"] == off["allOf"]


def _gate(tmp_path, **ident):
    f = tmp_path / "ch-x.json"
    f.write_text(json.dumps({"identity": ident}))
    return official_documents_gate([f], date(2026, 11, 24))


def test_les_regles_d_hote_et_de_calendrier_s_appliquent(tmp_path):
    assert _gate(tmp_path, same_address_documents=[BINZ]) == []
    assert _gate(tmp_path, same_address_documents=[{**BINZ, "url": "https://pub-abc.r2.dev/x.pdf"}])
    assert _gate(tmp_path, same_address_documents=[{**BINZ, "url": "https://baxtel.com/x"}])
    assert _gate(tmp_path, same_address_documents=[{**BINZ, "accessed": "2024-01-01"}])


def test_un_meme_lien_ne_sert_pas_dans_les_deux_rubriques(tmp_path):
    preuve = {k: v for k, v in BINZ.items() if k not in ("activity", "site_event", "match")}
    preuve["supports"] = ["existence"]
    assert _gate(tmp_path, official_documents=[preuve], same_address_documents=[BINZ])


def test_le_dictionnaire_ouvre_ou_ferme_l_hote(tmp_path):
    d = tmp_path / "dictionnaire"
    d.mkdir()
    (d / "ch.json").write_text(json.dumps({"pays": "CH", "entrees": [{
        "entry_id": "ch-licence-seco-arbeitszeit", "categorie": "officiel", "pays": "CH",
        "statut": "validee", "go_franck": "2026-11-21", "temoin": {"fiche_id": "ch-x"},
        "sources": [{"rang": 1, "source_id": "ch-amtsblattportal"}]}]}))
    (d / "_heritage.json").write_text(json.dumps({"documents": []}))
    cat = tmp_path / "catalogue.json"
    cat.write_text(json.dumps({"sources": [
        {"source_id": "ch-amtsblattportal", "access": {"url": "https://amtsblattportal.ch/api"}}]}))
    f = tmp_path / "ch-x.json"
    f.write_text(json.dumps({"identity": {"country": "CH", "same_address_documents": [BINZ]}}))
    assert documents_dictionary_gate([f], d, cat) == []
    f.write_text(json.dumps({"identity": {"country": "CH", "same_address_documents": [
        {**BINZ, "url": "https://www.stadt-zuerich.ch/x.pdf"}]}}))
    assert documents_dictionary_gate([f], d, cat)


def test_chaque_etape_et_la_sous_rubrique_ont_leur_libelle_dans_chaque_langue():
    texte = TABLE.read_text(encoding="utf-8")
    blocs = re.findall(r"^const ([A-Z]{2})(?:: typeof FR)? = \{(.*?)^\};", texte, re.S | re.M)
    assert {b[0] for b in blocs} >= {"FR", "EN", "NL"}
    attendu = set(_items("same_address_documents")["properties"]["site_event"]["enum"])
    for langue, corps in blocs:
        sous = re.search(r"^  siteEvents: \{(.*?)^  \},", corps, re.S | re.M)
        assert sous, f"{langue}: bloc siteEvents introuvable"
        assert set(re.findall(r"^    (\w+):", sous.group(1), re.M)) == attendu, langue
        assert re.search(r"^  memeAdresse: \{\n    titre: \"[^\"]+\",\n    intro: \"[^\"]+\",", corps, re.M), langue


def test_l_artefact_sert_la_sous_rubrique_a_part_et_jamais_comme_preuve(tmp_path):
    vieux = {**BINZ, "date": "2019-03-01", "url": "https://amtsblattportal.ch/api/v1/publications/y/pdf"}
    dc = _fiche(same_address_documents=[vieux, BINZ])
    dc["identity"].pop("official_documents", None)
    build_artifacts({dc["id"]: dc}, load_methodology(), out_dir=tmp_path, watchlist=[])
    servi = json.loads((tmp_path / "dc" / f"{dc['id']}.json").read_text())
    assert [d["date"] for d in servi["same_address_documents"]] == ["2024-09-30", "2019-03-01"]
    assert "official_documents" not in servi, "un acte de la même adresse ne devient pas une preuve"
