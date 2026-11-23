# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Une fiche fusionnée redirige vers la conservée, dans les 3 langues (2026-11-23 : 24 fusions
sur 42 tombaient sur un 404, et aucune en néerlandais)."""
import importlib.util
from pathlib import Path

S = Path(__file__).resolve().parents[2] / "scripts" / "build_redirects_fusions.py"
spec = importlib.util.spec_from_file_location("rf", S)
rf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rf)


def _dist(tmp_path, *ids):
    for i in ids:
        for lg in ("", "fr/", "nl/"):
            d = tmp_path / f"{lg}dc" / i
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text("x")
    return tmp_path


def test_une_fusion_redirige_dans_les_trois_langues(tmp_path):
    out, fautes = rf.lignes([{"id": "a", "type": "fusion", "survivante": "b"}], "", _dist(tmp_path, "b"))
    assert fautes == []
    assert out == ["/dc/a/ /dc/b/ 301", "/fr/dc/a/ /fr/dc/b/ 301", "/nl/dc/a/ /nl/dc/b/ 301"]


def test_la_cible_suit_la_chaine_et_la_main_est_gardee(tmp_path):
    r = [{"id": "a", "type": "fusion", "survivante": "b"}, {"id": "b", "type": "fusion", "survivante": "c"}]
    out, _ = rf.lignes(r, "/fr/dc/a/  /fr/dc/c/  301\n", _dist(tmp_path, "c"))
    assert "/dc/a/ /dc/c/ 301" in out and not any(l.startswith("/fr/dc/a/ ") for l in out)


def test_une_cible_absente_est_une_erreur_et_un_retrait_non_fusion_ne_redirige_pas(tmp_path):
    out, fautes = rf.lignes([{"id": "a", "type": "fusion", "survivante": "z"},
                             {"id": "p", "type": "parque_non_data_center"}], "", _dist(tmp_path))
    assert out == [] and len(fautes) == 1


def test_une_edition_de_langue_absente_est_sautee(tmp_path):
    d = tmp_path / "dc" / "b"; d.mkdir(parents=True); (d / "index.html").write_text("x")
    out, fautes = rf.lignes([{"id": "a", "type": "fusion", "survivante": "b"}], "", tmp_path)
    assert fautes == [] and out == ["/dc/a/ /dc/b/ 301"]
