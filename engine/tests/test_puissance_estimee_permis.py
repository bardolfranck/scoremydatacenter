# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Puissance estimée d'après le permis (Franck 2026-11-25).

Une fourchette tirée de la puissance thermique des groupes de secours autorisée est une
ESTIMATION : la fiche ne doit pas la dire « annoncée », elle cite le permis d'où vient le
chiffre, et elle ne publie jamais la règle (ni coefficient, ni formule)."""

import copy
import json
import re
from pathlib import Path

from engine.artifacts import build_artifacts
from engine.core import DATA_DIR, load_datacenters, load_json, load_methodology
from engine.validate import _schema_errors

REPO = Path(__file__).resolve().parents[2]
REGLE = REPO / "site" / "src" / "config" / "puissance.ts"

PERMIS = {"title": "Environment Agency permit EPR/FP3000LY",
          "url": "https://assets.publishing.service.gov.uk/media/624bfbd8e90e075f06b3730f/Permit_FP3000LY.pdf",
          "accessed": "2026-11-25"}


def _bloc(nom: str) -> str:
    m = re.search(rf"const {nom}: Libelle = \{{(.*?)\n\}};", REGLE.read_text(encoding="utf-8"), re.S)
    assert m, nom
    return m.group(1)


def test_une_fourchette_estimee_ne_se_dit_pas_annoncee():
    bloc = _bloc("PLAGE_ESTIMEE")
    for langue in ("fr", "en", "nl"):
        ligne = re.search(rf"^\s*{langue}: \"([^\"]+)\"", bloc, re.M)
        assert ligne and "{min}" in ligne.group(1) and "{max}" in ligne.group(1), langue
    assert not re.search(r"annonc|announc|aangekondigd", bloc, re.I)


def test_l_infobulle_cite_le_permis_sans_livrer_la_regle():
    bloc = _bloc("INFOBULLE_ESTIMATION")
    for langue in ("fr", "en", "nl"):
        ligne = re.search(rf"^\s*{langue}: \"([^\"]+)\"", bloc, re.M)
        assert ligne and "{ref}" in ligne.group(1), langue
        assert not re.search(r"\d", ligne.group(1)), f"{langue}: un chiffre dans l'infobulle = un coefficient publié"


def test_le_permis_voyage_jusqu_a_la_fiche(tmp_path):
    dc = copy.deepcopy(next(iter(load_datacenters().values())))
    dc["identity"].update(power_mw=25.0, power_mw_status="estimated",
                          power_mw_range={"min": 13, "max": 25}, power_mw_source=PERMIS)
    assert _schema_errors(dc, load_json(DATA_DIR / "schema" / "datacenter.schema.json"), "t") == []
    build_artifacts({dc["id"]: dc}, load_methodology(), out_dir=tmp_path, watchlist=[])
    servi = json.loads((tmp_path / "dc" / f"{dc['id']}.json").read_text())
    assert servi["power_mw_source"] == PERMIS
    assert "coefficient" not in json.dumps(servi).lower()
