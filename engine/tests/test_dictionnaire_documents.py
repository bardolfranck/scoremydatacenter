# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Dictionnaire des sources de documents (Franck 2026-11-21). Les documents d'un site se
cherchent là où le dictionnaire du pays dit de chercher — pas de moisson freestyle. Ces tests
tiennent : le gate (une source inconnue ne se verse pas, l'héritage ne grandit pas), le champ
« Documents des acteurs du projet » (schéma, libellés, artefact), les deux trous trouvés par
WORLD sur le servi (une URL suivie d'un commentaire, un parcel_record sans acte), et le
classement du contrôle des liens (une panne de document n'est pas une panne de source)."""

import copy
import importlib.util
import json
import re
from datetime import date
from pathlib import Path

from engine.artifacts import build_artifacts
from engine.core import DATA_DIR, load_datacenters, load_json, load_methodology
from engine.validate import (HERITAGE_DICTIONNAIRE_MAX, _schema_errors, documents_dictionary_gate,
                             official_documents_gate)

REPO = Path(__file__).resolve().parents[2]
TABLE = REPO / "site" / "src" / "content" / "documents-acteurs.ts"

DOC = {"type": "air_permit", "authority": "Virginia DEQ", "reference": "74341-1",
       "date": "2026-07-02", "url": "https://www.deq.virginia.gov/home/showpublisheddocument/35458",
       "accessed": "2026-11-21", "supports": ["existence"]}
ACTEUR = {"role": "operator", "actor": "Clean Arc", "type": "press_release",
          "title": "Clean Arc breaks ground on VA1", "date": "2025-11-20",
          "url": "https://www.cleanarc.com/news/va1", "accessed": "2026-11-21",
          "supports": ["project_status"]}


def _schema():
    return load_json(DATA_DIR / "schema" / "datacenter.schema.json")


def _fiche(**ident):
    dc = copy.deepcopy(next(iter(load_datacenters().values())))
    dc["identity"].update(ident)
    return dc


# ------------------------------------------------------------------ schéma

def test_une_url_suivie_d_un_commentaire_est_refusee():
    """Servi le 2026-11-20 : « https://…name-1071533-en.html (live URL now 404; read via
    web.archive.org…) ». Le schéma n'ancrait que le début de l'URL."""
    bad = {**DOC, "url": DOC["url"] + " (live URL now 404; read via web.archive.org)"}
    assert _schema_errors(_fiche(official_documents=[bad]), _schema(), "t")
    assert _schema_errors(_fiche(project_party_documents=[{**ACTEUR, "url": ACTEUR["url"] + " x"}]),
                          _schema(), "t")


def test_un_parcel_record_porte_un_numero_d_instrument():
    """Une page d'assesseur lue telle quelle n'est pas un acte (4 servies le 2026-11-20)."""
    parcelle = {**DOC, "type": "parcel_record", "reference": None}
    assert _schema_errors(_fiche(official_documents=[parcelle]), _schema(), "t")
    assert _schema_errors(_fiche(official_documents=[{**parcelle, "reference": "28100-2026"}]),
                          _schema(), "t") == []
    # Les autres types gardent `reference: null` (communiqué sans numéro).
    assert _schema_errors(_fiche(official_documents=[{**DOC, "reference": None}]), _schema(), "t") == []


def test_le_schema_accepte_un_document_d_acteur_daté_ou_non():
    assert _schema_errors(_fiche(project_party_documents=[ACTEUR]), _schema(), "t") == []
    assert _schema_errors(_fiche(project_party_documents=[{**ACTEUR, "date": None}]), _schema(), "t") == []
    for mutation in ({"role": "journalist"}, {"type": "article"}, {"supports": []},
                     {"title": ""}, {"date": "2025-11"}):
        assert _schema_errors(_fiche(project_party_documents=[{**ACTEUR, **mutation}]), _schema(), "t"), mutation


# ------------------------------------------------------------------ gate des hôtes (sans réseau)

def _gate_docs(tmp_path, **ident):
    f = tmp_path / "zz-x.json"
    f.write_text(json.dumps({"identity": ident}))
    return official_documents_gate([f], date(2026, 11, 21))


def test_un_agregateur_ne_se_sert_jamais(tmp_path):
    assert _gate_docs(tmp_path, project_party_documents=[{**ACTEUR, "url": "https://baxtel.com/x"}])
    assert _gate_docs(tmp_path, official_documents=[{**DOC, "url": "https://www.google.com/maps/x"}])
    assert _gate_docs(tmp_path, project_party_documents=[ACTEUR]) == []
    assert _gate_docs(tmp_path, project_party_documents=[{**ACTEUR, "date": None}]) == []


# ------------------------------------------------------------------ gate du dictionnaire

def _dico(tmp_path, entrees, heritage=()):
    d = tmp_path / "dictionnaire"
    d.mkdir(exist_ok=True)
    (d / "us.json").write_text(json.dumps({"pays": "US", "entrees": entrees}))
    (d / "_heritage.json").write_text(json.dumps({"documents": [
        {"fiche_id": f, "url": u} for f, u in heritage]}))
    cat = tmp_path / "catalogue.json"
    cat.write_text(json.dumps({"sources": [
        {"source_id": "us-va-deq", "access": {"url": "https://www.deq.virginia.gov/permits"}},
        {"source_id": "ie-epa-leap", "access": {"url": "https://data.epa.ie/leap/api/v1"}},
    ]}))
    return d, cat


def _entree(statut="validee", **extra):
    e = {"entry_id": "us-va-air", "categorie": "officiel", "pays": "US", "statut": statut,
         "go_franck": "2026-11-21", "temoin": {"fiche_id": "us-cleanarc-va1"},
         "sources": [{"rang": 1, "source_id": "us-va-deq"}]}
    e.update(extra)
    return e


def _fiches(tmp_path, **ident):
    f = tmp_path / "us-x.json"
    f.write_text(json.dumps({"identity": {"country": "US", **ident}}))
    return [f]


def test_une_source_validee_ouvre_son_hote(tmp_path):
    d, cat = _dico(tmp_path, [_entree()])
    assert documents_dictionary_gate(_fiches(tmp_path, official_documents=[DOC]), d, cat) == []


def test_une_source_non_validee_n_ouvre_rien(tmp_path):
    """candidate ou temoin_ok : la reconnaissance est faite, le GO de Franck manque."""
    for statut in ("candidate", "temoin_ok", "retiree", "en_panne"):
        d, cat = _dico(tmp_path, [_entree(statut)])
        assert documents_dictionary_gate(_fiches(tmp_path, official_documents=[DOC]), d, cat), statut


def test_un_hote_hors_dictionnaire_est_refuse_meme_officiel(tmp_path):
    d, cat = _dico(tmp_path, [_entree()])
    autre = {**DOC, "url": "https://www.loudoun.gov/permit/1"}
    assert documents_dictionary_gate(_fiches(tmp_path, official_documents=[autre]), d, cat)


def test_les_hotes_de_documents_declares_comptent(tmp_path):
    """La source est décrite au catalogue par son API ; les PDF vivent sur un autre hôte."""
    e = _entree(sources=[{"rang": 1, "source_id": "ie-epa-leap", "hotes_documents": ["leap.epa.ie"]}],
                pays="IE")
    d, cat = _dico(tmp_path, [e])
    f = tmp_path / "ie-x.json"
    f.write_text(json.dumps({"identity": {"country": "IE", "official_documents": [
        {**DOC, "url": "https://leap.epa.ie/docs/abc.pdf"}]}}))
    assert documents_dictionary_gate([f], d, cat) == []


def test_l_heritage_couvre_ce_qu_il_nomme_et_rien_d_autre(tmp_path):
    autre = {**DOC, "url": "https://www.loudoun.gov/permit/1"}
    d, cat = _dico(tmp_path, [], heritage=[("us-x", autre["url"])])
    assert documents_dictionary_gate(_fiches(tmp_path, official_documents=[autre]), d, cat) == []
    encore = {**DOC, "url": "https://www.loudoun.gov/permit/2"}
    assert documents_dictionary_gate(_fiches(tmp_path, official_documents=[autre, encore]), d, cat)


def test_l_heritage_ne_peut_pas_grandir(tmp_path):
    trop = [("us-x", f"https://h.gov/{i}") for i in range(HERITAGE_DICTIONNAIRE_MAX + 1)]
    d, cat = _dico(tmp_path, [], heritage=trop)
    assert any("héritage" in p for p in documents_dictionary_gate([], d, cat))


def test_une_entree_validee_porte_le_go_et_le_temoin(tmp_path):
    d, cat = _dico(tmp_path, [_entree(go_franck=None)])
    assert any("sans validation" in p for p in documents_dictionary_gate([], d, cat))
    d, cat = _dico(tmp_path, [_entree(temoin={})])
    assert any("témoin" in p for p in documents_dictionary_gate([], d, cat))


def test_une_source_absente_du_catalogue_est_signalee(tmp_path):
    d, cat = _dico(tmp_path, [_entree("candidate", sources=[{"rang": 1, "source_id": "inconnue"}])])
    assert any("inconnue" in p for p in documents_dictionary_gate([], d, cat))


def test_un_document_d_acteur_exige_une_entree_pour_son_role(tmp_path):
    d, cat = _dico(tmp_path, [_entree(categorie="acteurs_du_projet", role="operator", sources=[])])
    assert documents_dictionary_gate(_fiches(tmp_path, project_party_documents=[ACTEUR]), d, cat) == []
    archi = {**ACTEUR, "role": "architect"}
    assert documents_dictionary_gate(_fiches(tmp_path, project_party_documents=[archi]), d, cat)


def test_sans_dictionnaire_rien_ne_se_verse(tmp_path):
    assert documents_dictionary_gate([], tmp_path / "absent", tmp_path / "cat.json")


# ------------------------------------------------------------------ libellés et artefact

def _enum(cle: str) -> list[str]:
    items = _schema()["properties"]["identity"]["properties"]["project_party_documents"]["items"]
    p = items["properties"][cle]
    return p["enum"] if "enum" in p else p["items"]["enum"]


def test_chaque_role_type_et_fait_a_son_libelle_dans_chaque_langue():
    """Une liste à deux endroits ment : l'énumération du schéma et la table sont comparées."""
    texte = TABLE.read_text(encoding="utf-8")
    blocs = re.findall(r"^const ([A-Z]{2})(?:: typeof FR)? = \{(.*?)^\};", texte, re.S | re.M)
    assert {b[0] for b in blocs} >= {"FR", "EN", "NL"}
    for langue, corps in blocs:
        for cle, enum in (("roles", "role"), ("types", "type"), ("supports", "supports")):
            sous = re.search(rf"^  {cle}: \{{(.*?)^  \}},", corps, re.S | re.M)
            assert sous, f"{langue}: bloc {cle} introuvable"
            cles = set(re.findall(r"^    (\w+):", sous.group(1), re.M))
            assert cles == set(_enum(enum)), f"{langue}.{cle}"


def test_l_artefact_sert_les_documents_d_acteurs_datés_d_abord(tmp_path):
    vieux = {**ACTEUR, "date": "2019-03-01", "url": "https://www.cleanarc.com/a"}
    sans = {**ACTEUR, "date": None, "url": "https://www.cleanarc.com/b"}
    dc = _fiche(project_party_documents=[sans, vieux, ACTEUR])
    build_artifacts({dc["id"]: dc}, load_methodology(), out_dir=tmp_path, watchlist=[])
    servi = json.loads((tmp_path / "dc" / f"{dc['id']}.json").read_text())
    assert [d["date"] for d in servi["project_party_documents"]] == ["2025-11-20", "2019-03-01", None]


# ------------------------------------------------------------------ contrôle des liens (sans réseau)

def _controle():
    spec = importlib.util.spec_from_file_location("controle_liens", REPO / "scripts" / "controle_liens.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_le_classement_des_liens():
    c = _controle().classer
    u = "https://www.deq.virginia.gov/docs/74341.pdf"
    assert c(u, 200, [], "application/pdf") == "ok"
    assert c(u, 404, []) == "casse"
    assert c(u, 410, []) == "casse"
    assert c(u, 403, []) == "non_verifiable", "un anti-robot n'est pas un lien cassé"
    assert c(u, None, []) == "injoignable"
    assert c(u, 200, [], "text/html") == "suspect", "HTML à la place du PDF : le 200 ment"
    assert c("https://a.gov/p", 200, [], "text/html", b"<title>Page not found</title>") == "suspect"
    # Migration de la source : redirection PERMANENTE vers une autre page.
    assert c("https://co.morrow.or.us/x", 200, [(301, "https://morrowcountyor.gov/x")], "text/html") == "migre"
    # http→https, www, barre finale : même page.
    assert c("http://a.gov/p", 200, [(301, "https://www.a.gov/p/")], "text/html") == "ok"
    assert c("https://a.gov/p", 200, [(302, "https://a.gov/login")], "text/html") == "ok"


def test_seuls_les_liens_nouveaux_sont_ouverts_a_l_ecriture():
    m = _controle()
    avant = {"identity": {"official_documents": [DOC]}}
    apres = {"identity": {"official_documents": [DOC, {**DOC, "url": "https://x.gov/2"}],
                          "project_party_documents": [ACTEUR]}}
    assert m.liens_nouveaux(avant, apres) == {"https://x.gov/2", ACTEUR["url"]}
    assert m.liens_nouveaux(None, avant) == {DOC["url"]}
    assert m.liens_nouveaux(avant, avant) == set()


# ------------------------------------------------------------------ suite Franck 2026-11-21

def test_une_mise_en_demeure_est_une_mesure_de_police_pas_une_licence():
    """Une mise en demeure servie en `licence` disait le contraire de l'acte."""
    md = {**DOC, "type": "enforcement_action", "reference": "AIOT 0007404508"}
    assert _schema_errors(_fiche(official_documents=[md]), _schema(), "t") == []


def test_un_lien_mort_garde_l_acte_et_se_date(tmp_path):
    mort = {**DOC, "link_unavailable_since": "2026-11-21"}
    assert _schema_errors(_fiche(official_documents=[mort]), _schema(), "t") == []
    assert _gate_docs(tmp_path, official_documents=[mort]) == []
    assert _gate_docs(tmp_path, official_documents=[{**DOC, "link_unavailable_since": "2026-01-01"}]), \
        "mort AVANT la dernière ouverture réussie"
    assert _gate_docs(tmp_path, official_documents=[{**DOC, "link_unavailable_since": "2027-01-01"}])
    m = _controle()
    assert m.liens({"identity": {"official_documents": [mort, {**DOC, "url": "https://x.gov/2"}]}}) == {"https://x.gov/2"}


def test_un_lien_geobloque_se_sert_avec_son_pays():
    """Décision Franck 2026-11-21 : un portail qui ne répond que depuis son pays (conseils
    irlandais) est servi, avec « accessible depuis <pays> » — jamais compté comme cassé."""
    geo = {**DOC, "accessible_from": "IE"}
    assert _schema_errors(_fiche(official_documents=[geo]), _schema(), "t") == []
    assert _schema_errors(_fiche(project_party_documents=[{**ACTEUR, "accessible_from": "IE"}]), _schema(), "t") == []
    assert _schema_errors(_fiche(official_documents=[{**DOC, "accessible_from": "Ireland"}]), _schema(), "t")


def test_chaque_pays_du_corpus_a_sa_forme_accessible_depuis_dans_chaque_langue():
    """« accessible depuis l'Irlande / les Pays-Bas / Singapour » : l'article dépend du pays,
    il ne se devine pas. Une seule table (documents-officiels.ts), mêmes pays dans les 3 langues."""
    texte = (REPO / "site" / "src" / "content" / "documents-officiels.ts").read_text(encoding="utf-8")
    blocs = re.findall(r"^  paysAcces: \{(.*?)^  \}", texte, re.S | re.M)
    assert len(blocs) == 3
    jeux = [set(re.findall(r"^    ([A-Z]{2}):", b, re.M)) for b in blocs]
    assert jeux[0] == jeux[1] == jeux[2]
    corpus = {"AT", "BE", "CH", "DE", "DK", "ES", "FI", "FR", "GB", "IE", "IL", "IT", "LU", "NL",
              "NO", "PL", "PT", "SE", "SG", "US"}
    assert corpus <= jeux[0], f"manque : {corpus - jeux[0]}"


# ------------------------------------------------------------------ suite Franck 2026-11-23

_REVUE = {"agent": "agent-data-pipeline-FR", "date": "2026-11-23", "verdict": "ok"}


def test_codeur_site_valide_apres_une_revue_croisee(tmp_path):
    """Franck délègue le jugement des sources : codeur-site valide, un 2e agent a contre-examiné."""
    v = {"par": "codeur-site", "date": "2026-11-23", "revue_croisee": _REVUE}
    d, cat = _dico(tmp_path, [_entree(go_franck=None, validation=v)])
    assert documents_dictionary_gate(_fiches(tmp_path, official_documents=[DOC]), d, cat) == []


def test_une_validation_sans_revue_ok_n_ouvre_rien(tmp_path):
    for revue in (None, {}, {**_REVUE, "verdict": "reserve"}, {**_REVUE, "verdict": "refus"},
                  {**_REVUE, "agent": ""}):
        v = {"par": "codeur-site", "date": "2026-11-23", "revue_croisee": revue}
        d, cat = _dico(tmp_path, [_entree(go_franck=None, validation=v)])
        assert documents_dictionary_gate(_fiches(tmp_path, official_documents=[DOC]), d, cat), revue
    v = {"par": "agent-eu", "date": "2026-11-23", "revue_croisee": _REVUE}  # l'agent ne s'auto-valide pas
    d, cat = _dico(tmp_path, [_entree(go_franck=None, validation=v)])
    assert documents_dictionary_gate(_fiches(tmp_path, official_documents=[DOC]), d, cat)


def test_une_source_supra_s_ouvre_a_toutes_les_fiches(tmp_path):
    """BEI, Commission, Banque mondiale… : un acte qui nomme le projet, quel que soit le pays."""
    d, cat = _dico(tmp_path, [])
    (d / "supra.json").write_text(json.dumps({"pays": "*", "entrees": [_entree(
        entry_id="supra-bei-projet", pays="*", type="financing_decision",
        sources=[{"rang": 1, "source_id": "us-va-deq", "hotes_documents": ["www.eib.org"]}])]}))
    bei = {**DOC, "type": "financing_decision", "url": "https://www.eib.org/en/projects/all/20230001"}
    assert documents_dictionary_gate(_fiches(tmp_path, official_documents=[bei]), d, cat) == []
    f = tmp_path / "ie-x.json"
    f.write_text(json.dumps({"identity": {"country": "IE", "official_documents": [bei]}}))
    assert documents_dictionary_gate([f], d, cat) == []


def test_une_decision_de_financement_est_un_type_d_acte():
    fin = {**DOC, "type": "financing_decision", "reference": "EIB 2023-0001"}
    assert _schema_errors(_fiche(official_documents=[fin]), _schema(), "t") == []
