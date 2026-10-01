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


def test_yymmdd_et_numeros_davis_ne_sont_pas_des_dates():
    # 6 chiffres : on ne tente pas (collision numéros d'avis) → pas de date devinée.
    assert fiche.date_du_nom_de_fichier("http://x/mrae-180208-avis.pdf") is None
    assert fiche.date_du_nom_de_fichier("http://x/mrae-p-2024-15721-avis.pdf") is None


# ── corroboration ─────────────────────────────────────────────────────────────

def test_corroboration_confirmee_et_arbitrage_et_correction():
    url = "http://x/2025-05-07_rungis.pdf"
    assert fiche.date_corroboree("2025-05-07", url) == ("2025-05-07", "confirmee")
    assert fiche.date_corroboree("2025-05-08", url) == ("2025-05-08", "a_arbitrer")   # +1 j : gardé
    assert fiche.date_corroboree("2020-07-06", url) == ("2025-05-07", "corrigee")     # 5 ans : corrigé
    assert fiche.date_corroboree("2025-05-07", "http://x/mrae-p-2024-15721.pdf") == ("2025-05-07", "non_confirmee")
    assert fiche.date_corroboree(None, url) == ("2025-05-07", "corrigee")             # pas d'index → nom de fichier


# ── build_national applique la corroboration ──────────────────────────────────

class _FakeAvis:
    petitionnaire = None
    def as_dict(self):
        return {"source": {"doc_url": "x", "pages": 25}, "faits": {}}


class _FakeDoc:
    def __init__(self, date, url):
        self.date, self.doc_url, self.titre, self.origine = date, url, "t", "site MRAe"


def test_build_national_corrige_le_gros_ecart_garde_le_leger():
    gros = fiche.build_national(_FakeDoc("2020-07-06", "http://x/2025-05-07_corbeil.pdf"), _FakeAvis())
    assert gros["procedure"]["date_avis"] == "2025-05-07"          # corrigé vers le nom de fichier
    leger = fiche.build_national(_FakeDoc("2025-05-08", "http://x/2025-05-07_rungis.pdf"), _FakeAvis())
    assert leger["procedure"]["date_avis"] == "2025-05-08"          # ±1 j : index gardé


# ── passe hors ligne sur les fiches stockées ──────────────────────────────────

def _national(date_avis, url):
    return {"schema": "smdc.registre-ae/1", "installation": {"faits": {}},
            "source": {"doc_url": url, "registre": None, "pdf": {"couche_texte": True, "pages": 25}},
            "procedure": {"intitule": "t", "date_avis": date_avis}}


def test_corriger_dates_corrige_arbitre_et_epargne_le_registre(tmp_path):
    (tmp_path / "gros.json").write_text(json.dumps(_national("2020-07-06", "http://x/2025-05-07_a.pdf")))
    (tmp_path / "leger.json").write_text(json.dumps(_national("2025-05-08", "http://x/2025-05-07_b.pdf")))
    # une fiche de REGISTRE, avec la même anomalie apparente : doit être épargnée (date d'acte).
    reg = _national("2020-01-01", "http://x/2025-05-07_c.pdf")
    reg["source"]["registre"] = {"region": "IDF"}
    (tmp_path / "idf-reg.json").write_text(json.dumps(reg))

    r = run.corriger_dates(tmp_path)
    assert [c["avis"] for c in r["corrigees"]] == ["gros"]
    assert json.loads((tmp_path / "gros.json").read_text())["procedure"]["date_avis"] == "2025-05-07"
    assert "date_corrigee" in json.loads((tmp_path / "gros.json").read_text())
    assert [c["avis"] for c in r["a_arbitrer"]] == ["leger"]
    assert json.loads((tmp_path / "leger.json").read_text())["procedure"]["date_avis"] == "2025-05-08"  # inchangé
    assert json.loads((tmp_path / "idf-reg.json").read_text())["procedure"]["date_avis"] == "2020-01-01"  # registre épargné
    # idempotent : un second passage ne corrige plus rien.
    assert run.corriger_dates(tmp_path)["corrigees"] == []
