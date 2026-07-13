# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""DCWatch (Hubblo) seed exporter — offline contract tests.

The exporter is upstream of the one run path: a DCWatch ODbL release in, a
`pipelines.spatial.batch`-compatible sites CSV out, with an ODbL provenance
sidecar. These tests run on a miniature dump — no network, deterministic."""

import csv
import json
from pathlib import Path

import pytest

from pipelines.seed.dcwatch import LICENSE, dedupe, export, load_sites, panel_coordinates


def _write(path: Path, header: str, rows: list[str]) -> None:
    path.write_text("\n".join([header, *rows]) + "\n")


@pytest.fixture()
def dump(tmp_path):
    d = tmp_path / "datacenter-watch-2026.04.09" / "dump"
    d.mkdir(parents=True)
    _write(d / "countries.csv", "id,name", ["1,France", "2,Switzerland"])
    _write(d / "progress_steps.csv", "id,name", ["1,operating", "2,project"])
    _write(d / "companies.csv", "id,name", ["10,OpCo", "11,OtherCo"])
    _write(d / "company_operates_datacenter.csv", "id,datacenter_id,company_id,date",
           ["1,1,10,", "2,1,11,", "3,3,10,"])
    _write(
        d / "datacenters.csv",
        "id,name,latitude,longitude,address,city_name,department,city_code,region,country_id,"
        "tier_uptime_institute,campus,total_power_per_total_floor_area_ratio,total_floor_area_sqm,"
        "IT_floor_area_sqm,cooling_technologies,power_total_mw,operation_start_year,heat_recovery,"
        "electricity_generation,PUE,WUE,ERF,REF,CUE,progress_step_id",
        [
            "1,DC Un,48.5878,2.7628,addr,FOUJU,77,77390,IdF,1,,,,100,50,,7.5,2010,,,,,,,,1",
            "2,DC Deux,45.0,4.0,addr,LYON,69,69000,ARA,1,,,,,,,,,,,,,,,,2",
            "3,DC Suisse,46.2,6.1,addr,GENEVE,,,,2,,,,,,,12,,,,,,,,,1",
            "4,DC Sans Coords,,,addr,PARIS,75,75000,IdF,1,,,,,,,,,,,,,,,,1",
        ],
    )
    return d


def test_load_sites_joins_and_maps_vocabulary(dump):
    sites = load_sites(dump, "FR")
    assert [s["name"] for s in sites] == ["DC Un", "DC Deux"]  # CH filtered, no-coords dropped
    un, deux = sites
    assert un["operator"] == "OpCo"                      # first listed operator wins
    assert un["project_status"] == "operational"         # operating -> operational
    assert un["power_mw"] == "7.5"
    assert deux["operator"] == "UNKNOWN — to fill"       # no operator link
    assert deux["project_status"] == "announced"         # project -> announced
    assert deux["power_mw"] == ""                        # never invented


def test_dedupe_sets_aside_sites_already_in_panel(dump, tmp_path):
    panel = tmp_path / "panel"
    panel.mkdir()
    (panel / "fr-dc-un.json").write_text(json.dumps(
        {"identity": {"name": "DC Un (panel)", "coordinates": {"lat": 48.5879, "lon": 2.7629}}}))
    (panel / "fr-no-coords.json").write_text(json.dumps({"identity": {"name": "sans coords"}}))
    fresh, seen = dedupe(load_sites(dump, "FR"), panel_coordinates([panel]))
    assert [s["name"] for s in fresh] == ["DC Deux"]
    assert [s["panel_match"] for s in seen] == ["DC Un (panel)"]  # ~10 m away = same site


def test_export_writes_batch_csv_and_odbl_provenance(dump, tmp_path):
    fresh, seen = dedupe(load_sites(dump, "FR"), [])
    out = export(fresh, tmp_path / "seeds", "2026.04.09", "FR", "2026-07-13", seen)
    rows = list(csv.DictReader(open(out)))
    # the CSV is the batch runner's input contract — exact header, nothing more
    assert list(rows[0]) == ["name", "operator", "lat", "lon", "power_mw", "project_status"]
    assert len(rows) == 2
    prov = json.loads(out.with_suffix(".provenance.json").read_text())
    assert prov["license"] == LICENSE and prov["release"] == "2026.04.09"
    assert prov["exported"] == 2 and prov["already_in_panel"] == []
    assert "Hubblo" in prov["attribution"]  # DCWatch (Hubblo) — never the 10a Labs homonym
