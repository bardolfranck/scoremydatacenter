# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Pure-function tests for the Belgian spatial adapter — no network."""

import io
import zipfile

from pipelines.spatial.be.elia import _parse_sheet
from pipelines.spatial.be.sources import _l3_value, _min_vertex_km, _pds_to_category
from pipelines.spatial.wise import _sql_for


def test_pds_zone_maps_to_soil_category():
    assert _pds_to_category("Activité économique industrielle") == "artificialized"
    assert _pds_to_category("Zone d'habitat") == "artificialized"
    assert _pds_to_category("Zone agricole") == "agricultural"
    assert _pds_to_category("Zone forestière") == "natural_or_enaf"
    assert _pds_to_category("Zone d'aménagement communal concerté") == "transitional"
    assert _pds_to_category("Zone inconnue") is None  # unknown zoning never guesses


def test_l3_banding_matches_methodology():
    close_upper = {"upper_tier": True, "dist_km": 1.9}
    far_upper = {"upper_tier": True, "dist_km": 3.0}
    low = {"upper_tier": False, "dist_km": 0.2}
    assert _l3_value([close_upper, low]) == "seveso_high_within_2km"
    assert _l3_value([far_upper, low]) == "seveso_low_within_5km"  # upper tier only bites <= 2 km
    assert _l3_value([low]) == "seveso_low_within_5km"
    assert _l3_value([]) == "none_within_5km"


def test_min_vertex_km_tolerates_both_axis_orders():
    # Same physical point (~Brussels) encoded [lon, lat] and [lat, lon]
    assert abs(_min_vertex_km(50.85, 4.35, [[4.36, 50.85]]) - _min_vertex_km(50.85, 4.35, [[50.85, 4.36]])) < 0.01


def test_wise_sql_parameterized_by_country_keeps_cycle():
    assert "countryCode='BE'" in _sql_for("BE")
    assert "cYear=2022" in _sql_for("BE")  # same reporting cycle as FR — codes must align


def test_elia_xlsx_inline_string_parser():
    # Elia's export uses inline strings (no sharedStrings.xml) — build a minimal workbook.
    sheet = (
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        '<row r="1"><c r="A1" t="inlineStr"><is><t>Site</t></is></c></row>'
        '<row r="2"><c r="B2" t="inlineStr"><is><t>BAUDO 150</t></is></c>'
        '<c r="D2"><v>3.85</v></c><c r="E2"><v>50.47</v></c><c r="F2"><v>5.5</v></c></row>'
        "</sheetData></worksheet>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    rows = _parse_sheet(zipfile.ZipFile(buf), "xl/worksheets/sheet1.xml")
    assert rows[0]["A"] == "Site"
    assert rows[1]["B"] == "BAUDO 150"
    assert rows[1]["D"] == 3.85 and rows[1]["E"] == 50.47 and rows[1]["F"] == 5.5
