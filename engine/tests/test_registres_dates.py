# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""date_avis des avis d'ORIGINE NATIONALE (lot 2). L'index national capte parfois une date du
CORPS du PDF (futur, décalée de mois/années) ; la date fiable est celle du NOM DE FICHIER. On
croise les deux : écart grossier → corrigé vers le nom de fichier ; écart léger (délibération vs
publication) → GARDÉ et mis à arbitrer, jamais écrasé en silence ; nom de fichier sans date sûre
→ laissé non corroboré. On ne devine PAS un YYMMDD à six chiffres (collision avec les numéros
d'avis) : mieux vaut une date absente qu'une date fausse.
"""

import json

from pipelines.registers import fiche, run


# ── lecture de la date dans le nom de fichier ─────────────────────────────────

def test_formats_surs():
    assert fiche.date_du_nom_de_fichier("http://x/2025-05-07_corbeil_avis.pdf") == "2025-05-07"
    assert fiche.date_du_nom_de_fichier("http://x/mrae-03-07-2024-tigery.pdf") == "2024-07-03"  # JJ-MM-AAAA (FR)
    assert fiche.date_du_nom_de_fichier("http://x/mrae-20260611-apara2064-icpe.pdf") == "2026-06-11"  # AAAAMMJJ


def test_date_invalide_rejetee():
    assert fiche.date_du_nom_de_fichier("http://x/2025-13-40_truc.pdf") is None   # mois 13, jour 40


def test_yymmdd_tranche_par_la_borne_basse():
    # 6 chiffres ambigus (AAMMJJ vs JJMMAA) : on lit AAMMJJ et on REFUSE si JJMMAA est aussi
    # plausible. La borne = une MRAe régionale n'existe pas avant 2016.
    # 190110 : AAMMJJ 2019-01-10, JJMMAA 2010 (< 2016, impossible) → on garde AAMMJJ.
    assert fiche.date_du_nom_de_fichier("http://x/mrae-190110-mrae-idf-avis.pdf") == "2019-01-10"
    assert fiche.date_du_nom_de_fichier("http://x/mrae-180208-avis.pdf") == "2018-02-08"
    # 180920 : AAMMJJ 2018-09-20 ET JJMMAA 2020-09-18, les deux ≥ 2016 → ambigu → refusé.
    assert fiche.date_du_nom_de_fichier("http://x/mrae-180920-truc.pdf") is None


def test_numeros_davis_ne_sont_pas_des_dates():
    # Un numéro d'avis à 6 chiffres ne donne pas de date valide (mois 24, etc.) → None.
    assert fiche.date_du_nom_de_fichier("http://x/mrae-p-2024-15721-avis.pdf") is None
    assert fiche.date_du_nom_de_fichier("http://x/mrae-n022432-avis.pdf") is None


# ── corroboration ─────────────────────────────────────────────────────────────

def test_corroboration_le_nom_de_fichier_gagne_et_garde_la_mise_en_ligne():
    url = "http://x/2025-05-07_rungis.pdf"
    # coïncidence → date de l'avis = nom de fichier, pas de mise en ligne à part
    assert fiche.date_corroboree("2025-05-07", url) == ("2025-05-07", "confirmee", None)
    # index +1 j = mise en ligne plausible : nom de fichier gagne, index CONSERVÉ en mel
    assert fiche.date_corroboree("2025-05-08", url) == ("2025-05-07", "corrigee", "2025-05-08")
    # écart grossier : l'index a capté une date du corps du PDF → jeté (mel None)
    assert fiche.date_corroboree("2020-07-06", url) == ("2025-05-07", "corrigee", None)
    # index AVANT l'avis : une publication ne précède pas la délibération → jeté
    assert fiche.date_corroboree("2025-05-01", url) == ("2025-05-07", "corrigee", None)
    # nom de fichier sans date sûre → non corroboré, on garde l'index
    assert fiche.date_corroboree("2025-05-07", "http://x/mrae-p-2024-15721.pdf") == ("2025-05-07", "non_confirmee", None)
    assert fiche.date_corroboree(None, url) == ("2025-05-07", "corrigee", None)


# ── build_national applique la corroboration ──────────────────────────────────

class _FakeAvis:
    petitionnaire = None
    def as_dict(self):
        return {"source": {"doc_url": "x", "pages": 25}, "faits": {}}


class _FakeDoc:
    def __init__(self, date, url):
        self.date, self.doc_url, self.titre, self.origine = date, url, "t", "site MRAe"


def test_build_national_le_nom_de_fichier_gagne_et_garde_la_mise_en_ligne():
    gros = fiche.build_national(_FakeDoc("2020-07-06", "http://x/2025-05-07_corbeil.pdf"), _FakeAvis())
    assert gros["procedure"]["date_avis"] == "2025-05-07"              # nom de fichier = date de l'avis
    assert "date_mise_en_ligne" not in gros["procedure"]              # capture du corps du PDF : jetée
    leger = fiche.build_national(_FakeDoc("2025-05-08", "http://x/2025-05-07_rungis.pdf"), _FakeAvis())
    assert leger["procedure"]["date_avis"] == "2025-05-07"            # ±1 j : le nom de fichier gagne quand même
    assert leger["procedure"]["date_mise_en_ligne"] == "2025-05-08"   # index conservé à part (mise en ligne)


# ── passe hors ligne sur les fiches stockées ──────────────────────────────────

def _national(date_avis, url):
    return {"schema": "smdc.registre-ae/1", "installation": {"faits": {}},
            "source": {"doc_url": url, "registre": None, "pdf": {"couche_texte": True, "pages": 25}},
            "procedure": {"intitule": "t", "date_avis": date_avis}}


def test_corriger_dates_corrige_tout_ecart_garde_la_mise_en_ligne_epargne_le_registre(tmp_path):
    (tmp_path / "gros.json").write_text(json.dumps(_national("2020-07-06", "http://x/2025-05-07_a.pdf")))
    (tmp_path / "leger.json").write_text(json.dumps(_national("2025-05-08", "http://x/2025-05-07_b.pdf")))
    # une fiche de REGISTRE, avec la même anomalie apparente : doit être épargnée (date d'acte).
    reg = _national("2020-01-01", "http://x/2025-05-07_c.pdf")
    reg["source"]["registre"] = {"region": "IDF"}
    (tmp_path / "idf-reg.json").write_text(json.dumps(reg))

    r = run.corriger_dates(tmp_path)
    assert sorted(c["avis"] for c in r["corrigees"]) == ["gros", "leger"]   # les deux corrigés
    assert "a_arbitrer" not in r                                            # l'arbitrage est tranché

    gros = json.loads((tmp_path / "gros.json").read_text())
    assert gros["procedure"]["date_avis"] == "2025-05-07"
    assert "date_mise_en_ligne" not in gros["procedure"]   # capture jetée
    assert "date_corrigee" in gros

    leger = json.loads((tmp_path / "leger.json").read_text())
    assert leger["procedure"]["date_avis"] == "2025-05-07"              # nom de fichier gagne
    assert leger["procedure"]["date_mise_en_ligne"] == "2025-05-08"     # index conservé à part

    assert json.loads((tmp_path / "idf-reg.json").read_text())["procedure"]["date_avis"] == "2020-01-01"  # registre épargné
    # idempotent : un second passage ne corrige plus rien.
    assert run.corriger_dates(tmp_path)["corrigees"] == []
