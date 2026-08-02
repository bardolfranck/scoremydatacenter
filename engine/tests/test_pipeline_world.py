# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the WORLD commons (pipelines/spatial/world.py) — the keyless bricks
that work for any point/country (W1-Aqueduct class): Ember E1 + global land cover F2."""

from pipelines.spatial import world
from pipelines.spatial.bands import io_lulc_to_category
from pipelines.spatial.http import SourceUnavailable


def _ember_csv(tmp_path):
    p = tmp_path / "ember.csv"
    p.write_text(
        "Area,ISO 3 code,Year,Area type,Category,Subcategory,Variable,Unit,Value\n"
        "Israel,ISR,2023,Country or economy,Power sector emissions,CO2,CO2 intensity,gCO2/kWh,558.83\n"
        "Israel,ISR,2025,Country or economy,Power sector emissions,CO2,CO2 intensity,gCO2/kWh,492.69\n"
        "Israel,ISR,2024,Country or economy,Power sector emissions,CO2,CO2 intensity,gCO2/kWh,540.55\n"
        "Israel,ISR,2025,Country or economy,Electricity generation,Total,Total generation,TWh,80\n"
    )
    return p


def test_ember_picks_latest_intensity_year(tmp_path, monkeypatch):
    monkeypatch.setattr(world, "cached_path", lambda url, name, refresh=False: _ember_csv(tmp_path))
    world._ember_memo.clear()
    frag = world.collect_e1_ember("ISR", "2026-07-27")
    assert frag["id"] == "E1" and frag["status"] == "measured"
    assert frag["value"] == 492.69                       # 2025, not 2023/2024
    assert "2025" in frag["source"]["title"] and "Ember" in frag["source"]["title"]


def test_ember_unknown_country_degrades_to_none(tmp_path, monkeypatch):
    monkeypatch.setattr(world, "cached_path", lambda url, name, refresh=False: _ember_csv(tmp_path))
    world._ember_memo.clear()
    assert world.collect_e1_ember("XXX", "2026-07-27") is None


def test_io_lulc_category_mapping_never_guesses():
    assert io_lulc_to_category("7") == "artificialized"   # built
    assert io_lulc_to_category("5") == "agricultural"     # crops
    assert io_lulc_to_category("11") == "natural_or_enaf" # rangeland
    assert io_lulc_to_category("10") is None              # clouds → no verdict
    assert io_lulc_to_category(None) is None


def test_f2_global_landcover_spec_contract(monkeypatch):
    monkeypatch.setattr(world, "get_json", lambda url, params=None: {
        "samples": [{"value": "7", "rasterId": 7}]})
    ctx = {"lat": 66.045, "lon": -17.343, "accessed": "2026-07-27"}
    prov = {}
    frags = world.collect_f2_global_landcover(ctx, prov)
    assert frags[0]["id"] == "F2" and frags[0]["value"] == "artificialized"
    assert "CC BY 4.0" in frags[0]["source"]["title"]
    assert prov["f2_crosscheck"]["io_lulc_class"] == "7"  # sidecar fact for review


def test_f2_falls_back_to_previous_year_then_degrades(monkeypatch):
    calls = []

    def flaky(url, params=None):
        calls.append(params["time"])
        raise SourceUnavailable("down")

    monkeypatch.setattr(world, "get_json", flaky)
    ctx = {"lat": 0.0, "lon": 0.0, "accessed": "2026-07-27"}
    assert world.collect_f2_global_landcover(ctx, {}) == []   # degrades, never fabricates
    assert len(calls) == len(world._LULC_YEARS)               # tried every year window
