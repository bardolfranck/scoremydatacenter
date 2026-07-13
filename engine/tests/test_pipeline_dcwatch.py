# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""DCWatch reader + proposer: French-locale parsing, deterministic-binding matching."""

import json

from pipelines.dcwatch.reader import parse, _num, normalize_name
from pipelines.dcwatch.propose import propose

CSV = """nom,adresse,latitude_longitude,nom_commune,code_postal,code_insee,operateur,etat_avancement_synthèse,puiss_MW,PUE_officiel,lien_fournisseur,provenance,code_pays
EQUINIX_-_ZZ1,,"",TESTVILLE,00000,00001,Equinix,En Exploitation,"15,3","1,2",https://example.org/pdf,carte.example,FR
AUTRE_-_DC,,"",TESTVILLE,00000,00001,Autre SAS,En Exploitation,"7,0",,,base,FR
SANS_POWER,,"",TESTVILLE,00000,00001,Equinix,En Projet,,,,,FR
OVH_-_ROUBAIX 7,,"",ROUBAIX,59100,59512,OVHcloud,En Exploitation,"5,0",,,carte.example,FR
OVH_-_ROUBAIX 8,,"",ROUBAIX,59100,59512,OVHcloud,En Exploitation,"8,0",,,carte.example,FR
DE_SITE,,"",BERLIN,10115,,Equinix,En Exploitation,"9,0",,,,DE
"""


def _dc(tmp_path, dc_id, name, operator, municipality):
    p = tmp_path / f"{dc_id}.json"
    p.write_text(json.dumps({
        "id": dc_id,
        "identity": {"name": name, "operator": operator, "municipality": municipality},
    }))
    return p


def test_french_locale_numbers():
    assert _num("15,3") == 15.3
    assert _num("1 400") == 1400.0
    assert _num("") is None and _num("0") is None and _num("#REF!") is None


def test_parse_normalizes_records():
    records = parse(CSV)
    eq = records[0]
    assert (eq["power_mw"], eq["pue_disclosed"], eq["country"]) == (15.3, 1.2, "FR")
    assert eq["source_url"] == "https://example.org/pdf"
    assert normalize_name("Vélizy-Villacoublay") == "VELIZY VILLACOUBLAY"


def test_propose_requires_operator_or_name_binding(tmp_path):
    _dc(tmp_path, "fr-equinix-zz1", "Equinix ZZ1", "Equinix", "Testville")
    records = [r for r in parse(CSV) if r["country"] == "FR"]
    out = {o["dc_id"]: o for o in propose(tmp_path, records)}
    # matches the Equinix row (token), NOT the same-commune "Autre SAS" row
    assert out["fr-equinix-zz1"]["decision"] == "propose"
    assert out["fr-equinix-zz1"]["power_mw"] == 15.3


def test_propose_never_guesses_between_two_powers(tmp_path):
    _dc(tmp_path, "fr-ovh-roubaix", "OVHcloud Roubaix", "OVHcloud", "Roubaix")
    records = [r for r in parse(CSV) if r["country"] == "FR"]
    out = {o["dc_id"]: o for o in propose(tmp_path, records)}
    assert out["fr-ovh-roubaix"]["decision"] == "ambiguous"  # 5.0 vs 8.0 — the gate decides


def test_propose_reports_absent(tmp_path):
    _dc(tmp_path, "fr-nowhere", "Datacenter X", "X Corp", "Nullepart")
    records = [r for r in parse(CSV) if r["country"] == "FR"]
    out = {o["dc_id"]: o for o in propose(tmp_path, records)}
    assert out["fr-nowhere"]["decision"] == "absent"
