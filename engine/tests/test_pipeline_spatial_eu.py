# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Pure-function tests for the shared multi-country skeleton and the NL/LU specs — no network."""

from pipelines.spatial.bands import e2_category, l3_value
from pipelines.spatial.geo import laea3035
from pipelines.spatial.lu import _pag_to_category
from pipelines.spatial.nl import _AFNAME_E2, _AFNAME_E3


def test_laea3035_projection_center_is_exact():
    # EPSG:3035 is defined with false origin (4321000, 3210000) at 52°N 10°E.
    x, y = laea3035(52.0, 10.0)
    assert abs(x - 4321000.0) < 0.01 and abs(y - 3210000.0) < 0.01


def test_laea3035_distances_match_haversine_locally():
    from pipelines.spatial.http import haversine_m
    a, b = (49.783, 6.083), (49.5049, 6.1135)  # Bissen ↔ Bettembourg
    ax, ay = laea3035(*a)
    bx, by = laea3035(*b)
    planar = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
    true = haversine_m(a[0], a[1], b[0], b[1])
    assert abs(planar - true) / true < 0.005  # LAEA is near-true at country scale


def test_l3_unknown_tier_never_guesses_a_hazard_class():
    unknown_far = {"upper_tier": None, "dist_km": 2.4}
    unknown_close = {"upper_tier": None, "dist_km": 1.5}
    # Beyond 2 km the tier cannot change the band — unknown is safe.
    assert l3_value([unknown_far]) == "seveso_low_within_5km"
    # Inside 2 km an unknown tier makes the band undecidable — never guess.
    assert l3_value([unknown_close]) is None
    # A KNOWN upper tier inside 2 km still dominates over an unknown one.
    assert l3_value([unknown_close, {"upper_tier": True, "dist_km": 1.0}]) == "seveso_high_within_2km"


def test_lu_pag_zoning_maps_to_soil_categories():
    assert _pag_to_category("AGR") == "agricultural"           # the contested Bissen plot
    assert _pag_to_category("SPEC") == "artificialized"        # ZAE Wolser, Bettembourg
    assert _pag_to_category("HAB-1") == "artificialized"
    assert _pag_to_category("FOR") == "natural_or_enaf"
    assert _pag_to_category("ZAD") == "transitional"
    assert _pag_to_category("XYZ") is None                     # unknown zoning never guesses


def test_nl_afname_classes_map_into_the_shared_e2_bands():
    # The NL feed is a class, not MW — its mapping must stay inside the shared enum,
    # and monotonically: more congestion never reads as more capacity. Class 0 ("capacity
    # available") must be present — dropping it lost every uncongested feed area.
    assert 0 in _AFNAME_E2 and 0 in _AFNAME_E3
    e2_order = ["ample", "adequate", "constrained", "saturated"]
    e3_order = ["low", "moderate", "high", "critical"]
    for mapping, order in ((_AFNAME_E2, e2_order), (_AFNAME_E3, e3_order)):
        mapped = [mapping[k] for k in sorted(mapping)]
        assert all(v in order for v in mapped)
        assert [order.index(v) for v in mapped] == sorted(order.index(v) for v in mapped)
    # MW-based countries keep using the shared cutoffs — one scale, two feeds.
    assert e2_category(1.5) == "saturated" and e2_category(150) == "ample"
