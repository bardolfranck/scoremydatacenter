# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Developer-when-known: publish a SOURCED register fact only for an R&D-signed developer case in a
real-estate development NAF — never our own verdict, never a name-matched needs_confirm homonym."""
import json

import scripts.build_prod_artifacts as B


def _sidecar(tmp_path, monkeypatch, fiches):
    d = tmp_path / "status-proof"
    d.mkdir(parents=True)
    (d / "operator_identity.json").write_text(json.dumps({"fiches": fiches}))
    monkeypatch.setattr(B, "CAL", tmp_path)


def _dcs(*ids):
    return {i: {"identity": {"operator": "unknown", "name": i}} for i in ids}


def _entry(tier, naf, denom="ICADE PROMOTION", siren="784606576"):
    return {"emit_tier": tier, "resolved": {"denomination": denom, "naf": naf, "siren": siren}}


def test_unsigned_developer_candidate_is_never_published(tmp_path, monkeypatch):
    _sidecar(tmp_path, monkeypatch, {"fr-x": _entry("developer_needs_confirm", "41.10A")})
    dcs = _dcs("fr-x")
    assert B.apply_developer_identity(dcs) == {}                 # needs_confirm → nothing, ever
    assert dcs["fr-x"]["identity"]["operator"] == "unknown"      # and no operator fill


def test_signed_developer_in_promotion_naf_publishes_a_sourced_fact(tmp_path, monkeypatch):
    _sidecar(tmp_path, monkeypatch, {"fr-x": _entry("developer_confirmed", "41.10A")})
    dcs = _dcs("fr-x")
    src = B.apply_developer_identity(dcs)["fr-x"]
    assert src["naf"] == "41.10A" and src["activity_fr"] == "promotion immobilière"
    assert src["siren"] == "784606576" and "annuaire-entreprises" in src["url"]
    assert dcs["fr-x"]["identity"]["operator"] == "ICADE PROMOTION"   # operator filled when unknown


def test_signed_but_non_promotion_naf_is_not_published(tmp_path, monkeypatch):
    # 68.10Z (marchand de biens) is NOT a development activity → not published even when signed.
    _sidecar(tmp_path, monkeypatch, {"fr-x": _entry("developer_confirmed", "68.10Z", denom="LA CITADELLE")})
    assert B.apply_developer_identity(_dcs("fr-x")) == {}
