# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Status proof: campus-safe join, calibrated abstention, and the bad-week guard."""

import json

from pipelines.status_proof import label_model, peeringdb, run


def fac(fid, name, lat, lon, nets):
    return {"id": fid, "name": name, "name_long": "", "aka": "", "latitude": lat, "longitude": lon,
            "net_count": nets, "ix_count": 0}


def fiche(fid, name, operator, status="operational", lat=48.585, lon=7.797, country="FR"):
    return {"id": fid, "name": name, "operator": operator, "country": country, "status": status,
            "lat": lat, "lon": lon}


def test_campus_expansion_is_not_a_bind():
    # SBG-7 (a project) sits next to SBG-1 (running): same brand, same coords, different building.
    m = peeringdb.join(fiche("x", "OVHcloud SBG-7", "OVHcloud"), [fac(1, "OVHcloud SBG-1", 48.585, 7.797, 40)])
    assert m["kind"] == "SUFFIX_MISMATCH"
    assert run.fired_lfs(m) == set()


def test_bind_with_networks_confirms():
    m = peeringdb.join(fiche("x", "Equinix PA7", "Equinix"), [fac(2, "Equinix PA7 - Paris", 48.5851, 7.797, 30)])
    assert m["kind"] == "BIND"
    p, used = label_model.p_operational(run.fired_lfs(m))
    assert label_model.decide(p) == "confirm_op" and used == ["peeringdb_live"]


def test_no_signal_abstains_and_noisy_lfs_are_silenced():
    assert label_model.decide(label_model.p_operational(set())[0]) == "abstain"
    p, used = label_model.p_operational({"osm_lifecycle", "dcwatch_project"})
    assert p is None and used == []
    # developer alone (1/1 measured) must not auto-demote
    assert label_model.decide(label_model.p_operational({"developer"})[0]) == "abstain"


def test_build_verdicts_and_internal_signals():
    facs = {"FR": [fac(2, "Equinix PA7", 48.585, 7.797, 30)]}
    fiches = [fiche("op-ok", "Equinix PA7", "Equinix"),
              fiche("op-unv", "Nowhere DC", "Nobody", lat=45.0, lon=5.0),
              fiche("ann-live", "Equinix PA7", "Equinix", status="announced")]
    out, counts = run.build(fiches, facs, "2026-09-17")
    assert out["op-ok"]["verdict"] == "verified" and out["op-ok"]["evidence"]["networks"] == 30
    assert out["op-unv"]["verdict"] == "unverified"
    assert out["ann-live"]["verdict"] == "live_signal"
    assert counts == {"verified": 1, "unverified": 1, "live_signal": 1, "demote": 0}


def test_bad_week_guard_keeps_previous_sidecar(tmp_path, monkeypatch):
    cal = tmp_path / "calibration"
    (cal / "status-proof").mkdir(parents=True)
    prev = {"counts": {"verified": 100}, "fiches": {}}
    (cal / "status-proof" / "status_check.json").write_text(json.dumps(prev))
    monkeypatch.setattr(run, "load_fiches", lambda c: [fiche("a", "Equinix PA7", "Equinix")])
    monkeypatch.setattr(peeringdb, "fetch_facilities", lambda: {})  # outage-like: nothing binds
    assert run.main(["--cal", str(cal)]) == 2
    assert json.loads((cal / "status-proof" / "status_check.json").read_text()) == prev
