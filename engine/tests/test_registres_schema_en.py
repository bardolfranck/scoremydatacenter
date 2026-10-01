# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Frontière produit FR → EN (point 4). Décision Franck : les clés du JSON sont en anglais, en
prévision de l'API. Le moteur reste en français ; `to_english` traduit à la SORTIE.

Invariants :
- traduction INTÉGRALE (clés d'enveloppe, thèmes, indicateurs, valeurs d'énumération) ;
- ÉCHEC BRUYANT sur un identifiant/clé/thème inconnu — un identifiant FR qui franchit en silence
  serait le même faux silence qu'on traque partout ;
- couverture : chaque champ a un nom public EN (INDICATORS) et un libellé EN (LABELS_EN), chaque
  valeur d'énum a sa traduction — sinon un champ ajouté plus tard fuiterait en français.
"""

import json

import pytest

from pipelines.registers import avis
from pipelines.registers.schema_en import (ENUM_VALUES, INDICATORS, THEMES,
                                           UntranslatedKey, to_english)


def test_chaque_indicateur_a_un_libelle_anglais():
    ids = {f.id for f in avis.FIELDS}
    assert sorted(ids - set(avis.LABELS_EN)) == [], "indicateur sans libellé anglais"
    assert sorted(set(avis.LABELS_EN) - ids) == [], "libellé anglais orphelin"


def test_chaque_valeur_denum_a_sa_traduction():
    choices = {val for f in avis.FIELDS for _pat, val in f.choices}
    assert sorted(choices - set(ENUM_VALUES)) == [], "valeur d'énumération sans traduction anglaise"


def _fresh_fiche():
    txt = ("Les niveaux acoustiques en limite de propriété oscillent entre 62,5 dB(A) et 65 dB(A) "
           "de jour, et entre 59,5 dB(A) et 62 dB(A) en période nocturne. Le fluide frigorigène est "
           "le R134a. La puissance thermique nominale atteindra 59,29 MWth.")
    inst = avis.extract_from_pages([txt], "https://example.test/a.pdf").as_dict()
    return {"schema": "smdc.registre-ae/1",
            "source": {"doc_url": "x", "registre": {"region": "IDF", "licence": "lov2"},
                       "pdf": {"pages": 1, "caracteres": len(txt), "sha256": "", "couche_texte": True, "ocr": False}},
            "procedure": {"intitule": "t", "date_avis": "2025"},
            "installation": inst, "credit": "c"}


def test_to_english_traduit_integralement_sans_cle_francaise():
    en = to_english(_fresh_fiche())
    # thèmes et clés de faits traduits
    assert "facts" in en["installation"] and "faits" not in en["installation"]
    assert set(en["installation"]["facts"]) <= set(THEMES.values())
    f = en["installation"]["facts"]["noise"][0]
    assert set(f) <= {"indicator", "label", "theme", "value", "evidence_excerpt", "page_pdf", "unit"}
    assert f["indicator"] in INDICATORS.values()
    assert f["label"]["fr"] and f["label"]["en"]          # libellé bilingue, contenu
    # aucune clé française résiduelle nulle part
    FR = {"faits", "indicateur", "libelle", "valeur", "phrase", "unite", "jour", "nuit", "point"}
    def scan(o):
        if isinstance(o, dict):
            assert not (set(o) & FR), f"clé FR résiduelle : {set(o) & FR}"
            for v in o.values(): scan(v)
        elif isinstance(o, list):
            for x in o: scan(x)
    scan(en)


def test_valeur_denum_est_traduite():
    # « étude » -> under_study ; « fioul domestique » -> domestic_fuel_oil
    assert ENUM_VALUES["étude"] == "under_study"
    fiche = {"schema": "s", "installation": {"faits": {"chaleur": [
        {"indicateur": "chaleur_valorisation", "libelle": {"fr": "x", "en": "y"},
         "theme": "chaleur", "valeur": "étude", "phrase": "p", "page": 1}]}}}
    en = to_english(fiche)
    assert en["installation"]["facts"]["waste_heat"][0]["value"] == "under_study"


def test_echoue_bruyamment_sur_indicateur_inconnu():
    fiche = {"installation": {"faits": {"energie": [
        {"indicateur": "champ_fantome", "libelle": {"fr": "x", "en": "y"},
         "theme": "energie", "valeur": 1, "phrase": "p", "page": 1}]}}}
    with pytest.raises(UntranslatedKey):
        to_english(fiche)


def test_echoue_bruyamment_sur_cle_inconnue():
    with pytest.raises(UntranslatedKey):
        to_english({"source": {"cle_inventee": 1}})


def test_journal_interne_non_servi():
    # les traces FR (revalidation/dedup/derivation) ne franchissent pas la frontière.
    fiche = {"schema": "s", "installation": {"faits": {}}, "revalidation": {"date": "2026", "regle": "x"}}
    en = to_english(fiche)
    assert "revalidation" not in en and "installation" in en


def test_date_corrigee_est_un_journal_interne_et_mise_en_ligne_traduite():
    # Régression : une fiche corrigée porte la trace `date_corrigee` (journal, à NE PAS servir) et
    # un champ `date_mise_en_ligne` (donnée servie, à traduire). Sans l'un des deux, to_english
    # échouait bruyamment — c'est exactement ce que la frontière doit attraper.
    fiche = {"schema": "smdc.registre-ae/1",
             "procedure": {"intitule": "t", "date_avis": "2025-05-07", "date_mise_en_ligne": "2025-05-08"},
             "installation": {"faits": {}},
             "date_corrigee": {"date": "2026", "ancienne": "2020-07-06", "nouvelle": "2025-05-07"}}
    en = to_english(fiche)
    assert "date_corrigee" not in en                               # journal interne, non servi
    assert en["procedure"]["published_online_on"] == "2025-05-08"  # champ servi, traduit
    assert "date_mise_en_ligne" not in en["procedure"]
