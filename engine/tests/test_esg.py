# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Lecture ESG : l'IEF ne s'affiche que sur des FAITS, et la note n'en dépend pas."""

import copy
import json

import pytest

from engine.artifacts import build_artifacts
from engine.core import load_datacenters, load_methodology
from engine.esg import esg_fields, ief

SOURCE = {"title": "Dossier ICPE (test)", "url": "https://example.org/icpe", "accessed": "2026-11-11"}


def fiche(mw=40.0, statut="announced", ha=8.0, f4_statut="announced", f4_source=SOURCE,
          sol="artificialized", f2_statut="measured", plage=None):
    ident = {"power_mw": mw}
    if statut is not None:
        ident["power_mw_status"] = statut
    if plage is not None:
        ident["power_mw_range"] = plage
    return {
        "identity": ident,
        "indicators": [
            {"id": "F4", "status": f4_statut, "value": ha, **({"source": f4_source} if f4_source else {})},
            {"id": "F2", "status": f2_statut, "value": sol},
        ],
    }


def test_ief_formule_du_guide():
    # 40 MW sur 8 ha = 40 000 kW / 80 000 m² = 0,5 kW/m² ; sol déjà artificialisé → × 2.
    r = ief(fiche())
    assert r["value"] == 1.0 and r["unit"] == "kW/m²"
    assert r["inputs"]["trf"] == 1 and r["inputs"]["footprint_source"] == SOURCE
    # Terre agricole ou naturelle : TRF = 0, pas de doublement.
    assert ief(fiche(sol="agricultural"))["value"] == 0.5
    assert ief(fiche(sol="natural_or_enaf"))["value"] == 0.5


@pytest.mark.parametrize("variation", [
    {"statut": "estimated"},          # notre modèle, pas un fait
    {"statut": None},                 # remplissage hérité, provenance non déclarée
    {"mw": None, "plage": {"min": 60, "max": 240}},  # une fourchette n'est pas un nombre
    {"mw": 0},
    {"ha": None, "f4_statut": "not_collected"},
    {"f4_source": None},              # emprise sans source
    {"f4_statut": "missing"},
    {"ha": 0},
    {"sol": "transitional"},          # TRF indéterminé
    {"sol": None, "f2_statut": "missing"},
])
def test_ief_rien_plutot_qu_une_valeur_approchee(variation):
    assert ief(fiche(**variation)) is None
    assert esg_fields(fiche(**variation)) == {}


def test_la_note_ne_depend_pas_de_l_esg(tmp_path):
    # Même corpus, une fiche rendue éligible à l'IEF : la note et les sous-notes restent
    # identiques au caractère près ; seul le champ additif `esg` apparaît.
    dcs = load_datacenters()
    dc_id = "zz-test-alpha"
    base = build_artifacts(dcs, load_methodology(), out_dir=tmp_path / "a")
    dcs2 = copy.deepcopy(dcs)
    dcs2[dc_id]["identity"]["power_mw_status"] = "announced"
    f4 = next(e for e in dcs2[dc_id]["indicators"] if e["id"] == "F4")
    f4.setdefault("source", SOURCE)
    avec = build_artifacts(dcs2, load_methodology(), out_dir=tmp_path / "b")
    assert base[dc_id] == avec[dc_id]

    a = json.loads((tmp_path / "a" / "dc" / f"{dc_id}.json").read_text())
    b = json.loads((tmp_path / "b" / "dc" / f"{dc_id}.json").read_text())
    assert "esg" not in a and "ief" in b["esg"]
    b.pop("esg")
    # Seule l'entrée qu'on a modifiée pour rendre la fiche éligible peut différer.
    for d in (a, b):
        d.pop("power_mw_status", None)
    assert a == b
