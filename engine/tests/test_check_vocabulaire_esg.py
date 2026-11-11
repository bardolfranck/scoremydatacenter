# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le garde de vocabulaire ESG mord sur ce qu'il doit refuser, et laisse passer ce que nous écrivons."""

import importlib.util

import pytest

from engine.core import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "check_vocabulaire_esg", REPO_ROOT / "scripts" / "check_vocabulaire_esg.py")
garde = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(garde)


@pytest.mark.parametrize("texte", [
    "<p>La notation ESG du site</p>",
    "<p>Notre score ESG</p>",
    "<p>une note&nbsp;ESG</p>",
    "<p>le classement ESG des opérateurs</p>",
    "<p>An ESG rating for every site</p>",
    "<p>ESG-scores per operator</p>",
    '{"title": "ESG scoring of data centers"}',
    "<p>het ESG-cijfer van de site</p>",
    "<p>een ESG-beoordeling</p>",
])
def test_le_garde_refuse(tmp_path, texte):
    (tmp_path / "page.html").write_text(texte, encoding="utf-8")
    assert garde.fautes(tmp_path), texte
    assert garde.main(["x", str(tmp_path)]) == 1


@pytest.mark.parametrize("texte", [
    "<p>Lecture ESG : données ESG au niveau du site</p>",
    "<p>ESG reporting · ESG reading · site-level ESG data</p>",
    "<p>ESG-leeswijzer · ESG-gegevens per site</p>",
    "<p>Correspondance avec les cadres ESG (ESRS E1, E3, E4, S3)</p>",
])
def test_le_garde_laisse_passer(tmp_path, texte):
    (tmp_path / "page.html").write_text(texte, encoding="utf-8")
    assert garde.fautes(tmp_path) == []
    assert garde.main(["x", str(tmp_path)]) == 0


def test_dossier_absent_n_est_pas_un_succes(tmp_path):
    assert garde.main(["x", str(tmp_path / "absent")]) == 1
