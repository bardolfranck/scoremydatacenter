# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the Israel spec (pipelines/spatial/il.py) — the first scored country
outside the EU/EEA commons, built on the world bricks + national AGOL/CKAN finds."""

from pipelines.spatial import il
from pipelines.spatial.registry import SPECS


def test_registry_has_il_spec():
    spec = SPECS["IL"]
    assert spec["iso"] == "IL"
    declared = {i for ids, _fn in spec["collectors"] for i in ids}
    assert {"E1", "W1", "F1", "F2"} <= declared
    # the walls stay declared gaps — never silently absent
    assert {"E2", "E3", "W2", "W3", "L3"} <= set(spec["collectable_gaps"])


def test_fetch_locality_prefers_jurisdiction_polygon(monkeypatch):
    def fake_query(url, layer, lat, lon, dist, **kw):
        if "GvulotShput" in url:
            return [{"attributes": {"Muni_Eng": "Shoham", "Muni_Heb": "שהם",
                                    "CR_LAMAS": "1304", "Machoz": "מרכז"}}]
        raise AssertionError("fallback must not be called when a jurisdiction matches")

    import pipelines.spatial.geo as geo
    monkeypatch.setattr(geo, "arcgis_point_query", fake_query)
    monkeypatch.setattr(il, "_population_by_locality", lambda: {1304: 24996})
    c = il.fetch_locality(32.02, 34.96)
    assert (c["code"], c["name"], c["population"]) == (1304, "Shoham", 24996)
    assert c["backbone"] == "jurisdiction_polygon"


def test_fetch_locality_fallback_is_flagged(monkeypatch):
    def fake_query(url, layer, lat, lon, dist, **kw):
        if "GvulotShput" in url:
            return []
        return [{"attributes": {"SETL_CODE": 663, "ENG_NAME": "Tirat Yehuda",
                                "HEB_NAME": "טירת יהודה",
                                "Population_size___Israeli_local": 2000},
                 "geometry": {"x": 34.961, "y": 32.021}}]

    import pipelines.spatial.geo as geo
    monkeypatch.setattr(geo, "arcgis_point_query", fake_query)
    c = il.fetch_locality(32.02, 34.96)
    assert c["code"] == 663
    # an approximation must never look like an administrative fact
    assert c["backbone"].startswith("nearest_settlement_point_")


def test_w1_carries_the_desalination_caveat(monkeypatch):
    monkeypatch.setattr(il.eu, "collect_w1_aqueduct", lambda lat, lon, acc: {
        "id": "W1", "status": "measured", "value": "zre_or_crisis",
        "source": {"title": "WRI Aqueduct at point", "url": "u", "accessed": acc}})
    frags = il._w1_desal({"lat": 32.0, "lon": 34.9, "accessed": "2026-08-02"}, {})
    assert "desalination" in frags[0]["source"]["title"]      # §7.3: referential + its known limit


def test_l1_soec_is_provenance_only_never_an_indicator(monkeypatch):
    monkeypatch.setattr(il, "soec_for_locality", lambda code: {
        "cluster_2021": 9, "cluster_2019": 9, "index_value_2021": 1.68, "rank_2021": 247})
    prov = {}
    out = il._l1_raw({"commune": {"code": 1304}, "accessed": "2026-08-02"}, prov)
    assert out == []                                          # declares NO indicator
    assert prov["l1_soec"]["cluster_2021"] == 9
    assert "methodology-lead" in prov["l1_soec"]["note"]
