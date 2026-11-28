# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""L'état du permis voyage jusqu'à la fiche, à côté du stade (Franck, 2026-11-27).

Trois fiches disaient « annoncé » alors que leurs actes officiels disaient plus : Icade avait
son autorisation environnementale, le permis de Sesterce était suspendu par le juge, celui de
Segro retiré par le maire. Le stade ne porte pas ces faits ; `identity.permit_state` les porte,
datés au jour de l'acte et sourcés par lui. Il n'entre pas dans la note."""

import copy
import json
import re
from pathlib import Path

from engine.artifacts import build_artifacts
from engine.core import DATA_DIR, load_datacenters, load_json, load_methodology
from engine.scoring import score_datacenter
from engine.validate import _schema_errors

REPO = Path(__file__).resolve().parents[2]
FICHE = REPO / "site" / "src" / "content" / "fiche.ts"
ACTE = {"title": "TA Grenoble, ordonnance n° 2605946",
        "url": "https://grenoble.tribunal-administratif.fr/content/download/240702/document/2605946_Datacenter.pdf",
        "accessed": "2026-11-27"}
TYPES = ("authorization_granted", "building_permit_suspended", "building_permit_withdrawn")


def _un_dc():
    return copy.deepcopy(next(iter(load_datacenters().values())))


def test_l_etat_du_permis_passe_le_schema_et_atteint_la_fiche(tmp_path):
    dc = _un_dc()
    dc["identity"]["permit_state"] = {"kind": "building_permit_suspended", "date": "2026-07-10", "source": ACTE}
    assert _schema_errors(dc, load_json(DATA_DIR / "schema" / "datacenter.schema.json"), "t") == []
    build_artifacts({dc["id"]: dc}, load_methodology(), out_dir=tmp_path, watchlist=[])
    servi = json.loads((tmp_path / "dc" / f"{dc['id']}.json").read_text())
    assert servi["permit_state"]["kind"] == "building_permit_suspended"
    assert servi["permit_state"]["source"]["url"] == ACTE["url"]


def test_un_etat_sans_date_ou_sans_acte_est_refuse():
    schema = load_json(DATA_DIR / "schema" / "datacenter.schema.json")
    for mauvais in ({"kind": "building_permit_withdrawn", "source": ACTE},
                    {"kind": "building_permit_withdrawn", "date": "2026-06", "source": ACTE},
                    {"kind": "building_permit_withdrawn", "date": "2026-06-12"},
                    {"kind": "permis_annule", "date": "2026-06-12", "source": ACTE}):
        dc = _un_dc()
        dc["identity"]["permit_state"] = mauvais
        assert _schema_errors(dc, schema, "t"), mauvais


def test_l_etat_du_permis_n_entre_pas_dans_la_note():
    dc = _un_dc()
    avant = score_datacenter(dc, load_methodology())
    dc["identity"]["permit_state"] = {"kind": "authorization_granted", "date": "2025-10-29", "source": ACTE}
    assert score_datacenter(dc, load_methodology()) == avant


def test_chaque_etat_a_son_libelle_date_dans_chaque_langue():
    texte = FICHE.read_text(encoding="utf-8")
    blocs = re.findall(r"permitState: \{(.*?)\n  \},", texte, re.S)
    assert len(blocs) == 3, "un bloc permitState par langue (fr, en, nl)"
    for bloc in blocs:
        for kind in TYPES:
            ligne = re.search(rf'{kind}: "([^"]+)"', bloc)
            assert ligne and "{date}" in ligne.group(1), kind
