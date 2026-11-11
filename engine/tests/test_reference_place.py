# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""La ville de référence (US hors limites de ville, 2026-11-11). Le recalage d'un site sur sa
parcelle en terrain non incorporé faisait passer `municipality` de la ville au comté — vrai en
droit, mais la ville que tout le monde cherche (« Yorkville data center ») sortait du titre.
`reference_place` porte la ville citée par la source ; `municipality` reste la juridiction."""

import copy

from engine.core import DATA_DIR, load_datacenters, load_json, load_methodology
from engine.artifacts import _summary
from engine.scoring import score_datacenter
from engine.validate import _schema_errors


def _une_fiche():
    dcs = load_datacenters()
    return copy.deepcopy(next(iter(dcs.values())))


def test_le_schema_accepte_une_ville_de_reference_et_refuse_une_chaine_vide():
    schema = load_json(DATA_DIR / "schema" / "datacenter.schema.json")
    dc = _une_fiche()
    dc["identity"]["reference_place"] = "Yorkville"
    assert _schema_errors(dc, schema, "t") == []
    dc["identity"]["reference_place"] = ""
    assert _schema_errors(dc, schema, "t"), "une ville de référence vide ne doit pas passer"


def test_la_ville_de_reference_est_servie_seulement_quand_elle_existe():
    meth = load_methodology()
    dc = _une_fiche()
    res = score_datacenter(dc, meth)
    assert "reference_place" not in _summary(dc, res), "absente → aucun champ (contrat inchangé)"
    dc["identity"]["reference_place"] = "Yorkville"
    assert _summary(dc, res)["reference_place"] == "Yorkville"
