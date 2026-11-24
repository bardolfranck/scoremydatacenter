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
  - l'exploitant et le lieu sont PROUVÉS — même adresse, ou périmètre officiel cité —, jamais
    estimés par une distance (Franck 2026-11-24, principe de parcimonie) ;
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
              "proof": "same_address"},
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
        lambda d: d["match"].update(proof="distance"),    # une preuve, jamais une distance
        lambda d: d["match"].update(proof="official_perimeter"),  # sans le périmètre cité
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
        if cle == "match":
            # même forme, sauf `dc_named` : un acte sur une autre activité ne nomme pas le DC
            mm = copy.deepcopy(defn)
            for propre in ("dc_named", "project_named"):  # n'existent que pour un acte sur le DC
                mm["properties"]["proof"]["enum"].remove(propre)
            assert meme["properties"]["match"]["properties"]["proof"]["enum"] == mm["properties"]["proof"]["enum"]
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
    (d / "_heritage_rattachement.json").write_text(json.dumps({"documents": []}))
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


def test_un_campus_se_rattache_par_son_perimetre_officiel():
    """Fouju (≈ 70 ha) : un acte au bout du campus n'est pas « à 300 m du point » — il se
    rattache parce que sa parcelle figure au périmètre d'un acte officiel, cité."""
    campus = copy.deepcopy(BINZ)
    campus["match"] = {"operator": "Campus AI SPV1", "address": "Fouju, lieu-dit Les Bordes, ZB 12",
                       "proof": "official_perimeter",
                       "perimeter_source": {"title": "Permis de construire PC 077 196 25 00001",
                                            "url": "https://www.seine-et-marne.gouv.fr/x.pdf"}}
    assert _schema_errors(_fiche(same_address_documents=[campus]), _schema(), "t") == []


def test_un_acte_officiel_nouveau_porte_son_rattachement(tmp_path):
    """Les deux rubriques, pour tous les sites : un acte officiel sans `match` n'est accepté
    que s'il est nommé dans l'héritage (servi avant le 2026-11-24)."""
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
    acte = {k: v for k, v in BINZ.items() if k not in ("activity", "site_event", "match")}
    acte["supports"] = ["existence"]
    f = tmp_path / "ch-x.json"
    f.write_text(json.dumps({"identity": {"country": "CH", "official_documents": [acte]}}))
    (d / "_heritage_rattachement.json").write_text(json.dumps({"documents": []}))
    assert documents_dictionary_gate([f], d, cat), "sans match ni héritage : refusé"
    (d / "_heritage_rattachement.json").write_text(json.dumps({"documents": [
        {"fiche_id": "ch-x", "url": acte["url"]}]}))
    assert documents_dictionary_gate([f], d, cat) == [], "servi avant : couvert par l'héritage"
    (d / "_heritage_rattachement.json").write_text(json.dumps({"documents": []}))
    f.write_text(json.dumps({"identity": {"country": "CH", "official_documents": [
        {**acte, "match": BINZ["match"]}]}}))
    assert documents_dictionary_gate([f], d, cat) == [], "avec son match : accepté"
    (d / "_heritage_rattachement.json").unlink()
    assert documents_dictionary_gate([f], d, cat), "l'héritage absent se signale"


def _dico_ch(tmp_path):
    d = tmp_path / "dictionnaire"
    d.mkdir(exist_ok=True)
    (d / "ch.json").write_text(json.dumps({"pays": "CH", "entrees": [{
        "entry_id": "ch-eshab", "categorie": "officiel", "pays": "CH",
        "statut": "validee", "go_franck": "2026-11-21", "temoin": {"fiche_id": "ch-x"},
        "sources": [{"rang": 1, "source_id": "ch-amtsblattportal"}]}]}))
    (d / "_heritage.json").write_text(json.dumps({"documents": []}))
    (d / "_heritage_rattachement.json").write_text(json.dumps({"documents": []}))
    cat = tmp_path / "catalogue.json"
    cat.write_text(json.dumps({"sources": [
        {"source_id": "ch-amtsblattportal", "access": {"url": "https://amtsblattportal.ch/api"}}]}))
    return d, cat


ZRH13 = {"type": "gazette_notice", "authority": "Stadt Winterthur", "reference": "BP-ZH01-0000060751",
         "date": "2026-05-29", "url": "https://amtsblattportal.ch/api/v1/publications/z/pdf",
         "accessed": "2026-11-21", "supports": ["project_status"],
         "match": {"operator": "Vantage Data Centers ZRH11 GmbH", "address": "Fabrikstrasse 8, Winterthur",
                   "proof": "dc_named"}}


def _fiche_ch(tmp_path, nom, operateur, commune, docs=()):
    f = tmp_path / f"{nom}.json"
    f.write_text(json.dumps({"identity": {"country": "CH", "operator": operateur, "municipality": commune,
                                          **({"official_documents": list(docs)} if docs else {})}}))
    return f


def test_dc_named_rattache_un_permis_de_campus_sans_adresse_de_fiche(tmp_path):
    """ZRH13 (Vantage, Fabrikstrasse 8) : vrai permis de data center, rejeté par la preuve
    d'adresse (fiche au n° 12). Il nomme l'exploitant et le DC dans la commune, et Vantage n'a
    qu'une fiche à Winterthur : rattaché."""
    assert _schema_errors(_fiche(official_documents=[ZRH13]), _schema(), "t") == []
    d, cat = _dico_ch(tmp_path)
    f = _fiche_ch(tmp_path, "ch-vantage", "Vantage Data Centers", "Winterthur", [ZRH13])
    autre = _fiche_ch(tmp_path, "ch-autre", "Green", "Winterthur")
    assert documents_dictionary_gate([f, autre], d, cat) == []


def test_dc_named_refuse_quand_l_exploitant_a_plusieurs_fiches_dans_la_commune(tmp_path):
    d, cat = _dico_ch(tmp_path)
    f = _fiche_ch(tmp_path, "ch-vantage", "Vantage Data Centers", "Winterthur", [ZRH13])
    soeur = _fiche_ch(tmp_path, "ch-vantage-2", "Vantage Data Centers Europe", "Winterthur")
    assert documents_dictionary_gate([f, soeur], d, cat), "deux fiches Vantage à Winterthur : à adjuger"


def test_dc_named_n_existe_pas_pour_une_autre_activite():
    doc = copy.deepcopy(BINZ)
    doc["match"]["proof"] = "dc_named"
    assert _schema_errors(_fiche(same_address_documents=[doc]), _schema(), "t")


def test_une_date_au_mois_porte_le_01_et_sa_precision():
    """OFEN 12665 : « Bonnes pratiques avril 2026 », aucun jour publié. On ne fabrique pas de
    jour : `date_precision: month` et le 01 comme marqueur ; un autre jour est refusé."""
    rapport = {"type": "public_report", "authority": "Office fédéral de l'énergie (OFEN)",
               "reference": "12665", "date": "2026-04-01", "date_precision": "month",
               "url": "https://pubdb.bfe.admin.ch/fr/publication/download/12665",
               "accessed": "2026-11-24", "supports": ["existence"],
               "match": {"operator": "Infomaniak", "address": "Plan-les-Ouates", "proof": "dc_named"}}
    assert _schema_errors(_fiche(official_documents=[rapport]), _schema(), "t") == []
    assert _schema_errors(_fiche(official_documents=[{**rapport, "date": "2026-04-22"}]), _schema(), "t")
    assert _schema_errors(_fiche(official_documents=[{**rapport, "date_precision": "year"}]), _schema(), "t")
    assert _schema_errors(_fiche(official_documents=[{**rapport, "date_precision": "jour"}]), _schema(), "t")


def test_project_named_rattache_par_le_nom_distinctif_du_projet(tmp_path):
    """OFEN 12665 : « Nom du projet D4 / Exploitant Infomaniak », sans adresse ni commune. Le
    nom « D4 » désigne une seule fiche du corpus : rattaché. « Campus » en désigne plusieurs :
    refusé, sans liste noire."""
    d, cat = _dico_ch(tmp_path)
    acte = {**ZRH13, "match": {"operator": "Infomaniak", "address": "au sud de Genève",
                               "proof": "project_named", "project_name": "D4"}}
    assert _schema_errors(_fiche(official_documents=[acte]), _schema(), "t") == []
    sans_nom = copy.deepcopy(acte); del sans_nom["match"]["project_name"]
    assert _schema_errors(_fiche(official_documents=[sans_nom]), _schema(), "t")

    def fiche(nom_fichier, nom, docs=()):
        f = tmp_path / f"{nom_fichier}.json"
        f.write_text(json.dumps({"identity": {"country": "CH", "name": nom, "operator": "Infomaniak",
                                              "municipality": "Genève",
                                              **({"official_documents": list(docs)} if docs else {})}}))
        return f
    d4 = fiche("ch-infomaniak-d4", "Infomaniak D4", [acte])
    autres = [fiche("ch-infomaniak-dii", "Infomaniak DII"), fiche("ch-data4", "Data4 Campus")]
    assert documents_dictionary_gate([d4, *autres], d, cat) == [], "« D4 » ≠ « Data4 » (mot entier)"
    generique = {**acte, "match": {**acte["match"], "project_name": "Campus"}}
    f = fiche("ch-infomaniak-d4", "Infomaniak D4 Campus", [generique])
    assert documents_dictionary_gate([f, *autres], d, cat), "« Campus » désigne deux fiches"
