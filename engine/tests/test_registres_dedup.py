# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Dédup PAR IDENTITÉ DE CONTENU : le même avis servi deux fois (registre + site national) ne
compte qu'une fois. Le discriminant n'est ni le sha256 du fichier (aveugle aux ré-exports de
quelques octets) ni le texte brut (qu'un seul caractère change), mais l'identité STRUCTURELLE —
pagination + triplets de faits extraits (indicateur, valeur, page). Garde-fous : jamais sur une
identité vide (scan sans couche texte, ou avis sans fait = documents qu'on ne sait pas comparer),
et on garde la fiche de REGISTRE (acte administratif) en consignant l'URL de l'autre service.
"""

import json

from pipelines.registers import run


def _fiche(url, phrase, *, registre, texte=True, valeur=60, page=2, pages=25):
    return {"installation": {"faits": {"bruit": [
                {"indicateur": "bruit_niveau_dba", "valeur": valeur, "phrase": phrase, "page": page}]},
            "recommandations_autorite": []},
            "source": {"doc_url": url,
                       "registre": {"region": "IDF"} if registre else None,
                       "pdf": {"couche_texte": texte, "pages": pages}}}


def test_dedup_contenu_garde_registre_consigne_url(tmp_path):
    phrase = "Les niveaux acoustiques en limite de propriété sont de 60 dB(A) de jour."
    (tmp_path / "idf-x.json").write_text(
        json.dumps(_fiche("http://reg/a.pdf", phrase, registre=True), ensure_ascii=False))
    (tmp_path / "mrae-x.json").write_text(
        json.dumps(_fiche("http://nat/a.pdf", phrase, registre=False), ensure_ascii=False))

    s = run.dedup_contenu(tmp_path)
    assert len(s["fiches_fusionnees"]) == 1
    assert (tmp_path / "idf-x.json").exists()           # registre gardé (porte l'acte)
    assert not (tmp_path / "mrae-x.json").exists()       # doublon national fusionné
    d = json.loads((tmp_path / "idf-x.json").read_text())
    assert "http://nat/a.pdf" in d["source"]["sources_alternatives"]   # URL consignée, pas jetée
    assert "dedup" in d
    # idempotent : un second passage ne fusionne rien.
    assert run.dedup_contenu(tmp_path)["fiches_fusionnees"] == []


def test_dedup_fusionne_un_reexport_meme_faits_texte_different(tmp_path):
    # Cas Corbeil : même PDF ré-exporté — 25 pages des deux côtés, les FAITS identiques, mais UN
    # caractère d'écart dans le texte (ici un espace en plus). L'empreinte de texte brut ratait ce
    # cas ; l'identité structurelle (pagination + triplets) le reconnaît.
    (tmp_path / "idf-x.json").write_text(json.dumps(
        _fiche("http://reg/a.pdf", "Le niveau est de 60 dB(A) de jour.", registre=True), ensure_ascii=False))
    (tmp_path / "mrae-x.json").write_text(json.dumps(
        _fiche("http://nat/a.pdf", "Le niveau est de 60 dB(A) de jour. ", registre=False), ensure_ascii=False))
    s = run.dedup_contenu(tmp_path)
    assert len(s["fiches_fusionnees"]) == 1
    assert (tmp_path / "idf-x.json").exists() and not (tmp_path / "mrae-x.json").exists()


def test_dedup_ne_fusionne_pas_des_faits_differents(tmp_path):
    # Même pagination mais une valeur différente = documents distincts : jamais fusionnés.
    (tmp_path / "a.json").write_text(json.dumps(
        _fiche("http://x/a.pdf", "p", registre=True, valeur=60), ensure_ascii=False))
    (tmp_path / "b.json").write_text(json.dumps(
        _fiche("http://x/b.pdf", "p", registre=False, valeur=61), ensure_ascii=False))
    assert run.dedup_contenu(tmp_path)["fiches_fusionnees"] == []
    assert (tmp_path / "a.json").exists() and (tmp_path / "b.json").exists()


def test_dedup_epargne_les_avis_sans_fait_meme_avec_texte(tmp_path):
    # Couche texte présente mais AUCUN fait extrait : identité vide → on ne regroupe pas à
    # l'aveugle (sinon deux avis distincts sans fait seraient fusionnés à tort).
    vide = {"installation": {"faits": {}, "recommandations_autorite": []},
            "source": {"doc_url": "http://x/1", "registre": None, "pdf": {"couche_texte": True, "pages": 10}}}
    (tmp_path / "v1.json").write_text(json.dumps(vide, ensure_ascii=False))
    vide2 = json.loads(json.dumps(vide)); vide2["source"]["doc_url"] = "http://x/2"
    (tmp_path / "v2.json").write_text(json.dumps(vide2, ensure_ascii=False))
    assert run.dedup_contenu(tmp_path)["fiches_fusionnees"] == []
    assert (tmp_path / "v1.json").exists() and (tmp_path / "v2.json").exists()


def test_dedup_contenu_epargne_les_sans_couche_texte(tmp_path):
    # Deux scans illisibles (empreinte de contenu vide) sont des documents DISTINCTS,
    # pas des doublons — ne jamais les regrouper sur une empreinte vide.
    (tmp_path / "nt1.json").write_text(
        json.dumps({"installation": {"faits": {}, "recommandations_autorite": []},
                    "source": {"doc_url": "http://n/1", "registre": None,
                               "pdf": {"couche_texte": False}}}, ensure_ascii=False))
    (tmp_path / "nt2.json").write_text(
        json.dumps({"installation": {"faits": {}, "recommandations_autorite": []},
                    "source": {"doc_url": "http://n/2", "registre": None,
                               "pdf": {"couche_texte": False}}}, ensure_ascii=False))
    s = run.dedup_contenu(tmp_path)
    assert s["fiches_fusionnees"] == []
    assert (tmp_path / "nt1.json").exists() and (tmp_path / "nt2.json").exists()


def test_codes_region_normalises_vers_les_noms():
    # Le code de spec et le nom lu désignent la même région — sinon le tableau la compte deux fois.
    assert run._region_name("IDF") == "Île-de-France"
    assert run._region_name("paca") == "Provence-Alpes-Côte d'Azur"
    assert run._region_name("Île-de-France") == "Île-de-France"   # déjà un nom : inchangé
    assert run._region_name(None) == "?"


def test_coverage_fond_registre_et_national_en_une_region(tmp_path):
    reg = {"installation": {"faits": {"x": [{"indicateur": "a"}]}},
           "source": {"registre": {"region": "IDF"}, "pdf": {"couche_texte": True}}}
    nat = {"installation": {"faits": {"x": [{"indicateur": "a"}]}},
           "source": {"region_detectee": "Île-de-France", "registre": None, "pdf": {"couche_texte": True}}}
    (tmp_path / "idf.json").write_text(json.dumps(reg, ensure_ascii=False))
    (tmp_path / "mrae.json").write_text(json.dumps(nat, ensure_ascii=False))
    _champs, regions, retenus = run._coverage_from_fiches(tmp_path)
    assert regions["Île-de-France"] == 2 and "IDF" not in regions
    assert retenus == 2
