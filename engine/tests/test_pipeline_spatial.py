# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the spatial pipeline's pure logic (no network).

The collectors' network paths are exercised by hand against live APIs (see RECON.md); here we
pin the deterministic mapping/geometry that must never drift, and the anti-fabrication contract.
"""

import json

from pipelines.spatial.http import haversine_m, circle_geojson
from pipelines.spatial.sources import (
    _zone_to_category, _VIGIEAU_TO_CATEGORY, _f1_result, _w3_category, _l1_category)
from pipelines.spatial import capareseau


def test_haversine_known_distance():
    # Paris ↔ Marseille ≈ 660 km.
    d = haversine_m(48.8566, 2.3522, 43.2965, 5.3698)
    assert 650_000 < d < 670_000


def test_circle_geojson_is_closed_ring_of_right_radius():
    ring = json.loads(circle_geojson(48.6, 2.8, 1000))["coordinates"][0]
    assert ring[0] == ring[-1]  # closed
    # every vertex sits ~1 km from the centre
    for lon, lat in ring:
        assert 950 < haversine_m(48.6, 2.8, lat, lon) < 1050


def test_corine_land_cover_maps_to_soil_category():
    from pipelines.spatial.sources import _clc_to_category
    assert _clc_to_category("111") == "artificialized"   # continuous urban
    assert _clc_to_category("121") == "artificialized"   # industrial/commercial
    assert _clc_to_category("211") == "agricultural"      # arable land
    assert _clc_to_category("311") == "natural_or_enaf"   # forest
    assert _clc_to_category("512") == "natural_or_enaf"   # water body
    assert _clc_to_category("133") == "transitional"      # construction site
    assert _clc_to_category("324") == "transitional"      # transitional woodland-shrub
    assert _clc_to_category(None) is None


def test_plu_zone_maps_to_soil_category():
    assert _zone_to_category("U") == "artificialized"
    assert _zone_to_category("Ua") == "artificialized"
    assert _zone_to_category("AUc") == "transitional"   # AU before U
    assert _zone_to_category("A") == "agricultural"
    assert _zone_to_category("N") == "natural_or_enaf"
    assert _zone_to_category("") is None                # unknown ⇒ no fabricated value


def test_vigieau_severity_maps_monotonically():
    order = ["vigilance", "alerte", "alerte_renforcee", "crise"]
    cats = [_VIGIEAU_TO_CATEGORY[k] for k in order]
    assert cats == ["moderate", "high", "high", "zre_or_crisis"]


def test_w2_wfd_status_maps_to_methodology_categories():
    from pipelines.spatial.sources import _WISE_STATUS_TO_CATEGORY
    # WFD class 1..5 (High→Bad) must map onto the methodology's very_good→bad, in order.
    assert [_WISE_STATUS_TO_CATEGORY[str(i)] for i in range(1, 6)] == \
        ["very_good", "good", "moderate", "poor", "bad"]


def test_wise_query_targets_fr_current_cycle():
    from pipelines.spatial import wise
    # Guard the two facts that make the join correct: France, and the 2022 reporting cycle.
    assert "countryCode='FR'" in wise._SQL
    assert "cYear=2022" in wise._SQL


def test_l1_income_bands_and_ethics():
    assert _l1_category(18000) == "sensitive"    # poorer commune → never strong_fit
    assert _l1_category(23000) == "neutral"
    assert _l1_category(30000) == "strong_fit"
    # ethical monotonicity: lower income never yields a higher-scoring band
    order = {"sensitive": 0, "neutral": 1, "strong_fit": 2}
    incomes = [18000, 23000, 30000]
    bands = [order[_l1_category(i)] for i in incomes]
    assert bands == sorted(bands)


def test_w3_withdrawal_pressure_bands():
    assert _w3_category(0.1) == "low"
    assert _w3_category(2) == "moderate"
    assert _w3_category(20) == "high"
    assert _w3_category(200) == "very_high"


def test_capareseau_number_parsing():
    # Caparéseau mixes formats; the parser must survive all of them.
    assert capareseau._num("100 %") == 100.0
    assert capareseau._num("41.7") == 41.7
    assert capareseau._num("1,6") == 1.6
    assert capareseau._num("1.88  k€/MW") == 1.88
    assert capareseau._num("") is None
    assert capareseau._num(None) is None


def test_capareseau_capacity_categories():
    assert capareseau._e2_category(120) == "ample"
    assert capareseau._e2_category(40) == "adequate"
    assert capareseau._e2_category(8) == "constrained"
    assert capareseau._e2_category(0) == "saturated"
    assert capareseau._e3_category(10) == "low"
    assert capareseau._e3_category(50) == "moderate"
    assert capareseau._e3_category(85) == "high"
    assert capareseau._e3_category(100) == "critical"


def test_capareseau_nearest_picks_closest_substation():
    postes = [
        {"code": "FAR", "X": "3.0", "Y": "49.0", "values": {}},
        {"code": "NEAR", "X": "2.81", "Y": "48.60", "values": {}},
    ]
    poste, dist = capareseau._nearest(48.599, 2.806, postes)
    assert poste["code"] == "NEAR" and dist < 2000


def test_collector_output_carries_a_source_and_no_note():
    ind = _f1_result("overlap", "2026-07-07")
    assert ind["id"] == "F1" and ind["status"] == "measured"
    assert ind["value"] == "overlap"
    assert set(ind["source"]) == {"title", "url", "accessed"}  # sourced, closed shape
    assert "note" not in ind and "score" not in ind            # the contract: values + sources only


def test_batch_reads_csv_and_tolerates_bad_rows(tmp_path):
    from pipelines.spatial.batch import _read_sites
    f = tmp_path / "sites.csv"
    f.write_text("name,operator,lat,lon,power_mw\n"
                 "Good,Op,48.6,2.8,30\n"
                 "Bad,Op,notanumber,2.8,\n"          # bad lat → skipped, batch survives
                 "NoPower,Op,43.6,3.9,\n")
    sites = _read_sites(f)
    assert [s["name"] for s in sites] == ["Good", "NoPower"]
    assert sites[0]["power_mw"] == 30.0 and sites[1]["power_mw"] is None


def test_batch_reads_json_array(tmp_path):
    from pipelines.spatial.batch import _read_sites
    f = tmp_path / "sites.json"
    f.write_text('[{"name":"A","operator":"Op","lat":48.6,"lon":2.8}]')
    sites = _read_sites(f)
    assert sites[0]["name"] == "A" and sites[0]["project_status"] == "announced"
