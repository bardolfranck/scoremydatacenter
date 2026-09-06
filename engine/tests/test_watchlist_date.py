# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Phase-1: the served watchlist projection carries a DETECTION DATE (never a grade date).

The « derniers projets repérés » banner needs to sort « latest »; the served projection had no
date. `detected_at` = the entry-level source.accessed (a FACT date). A-19 unchanged: no grade.
"""
import json
import tempfile
from pathlib import Path

from engine.artifacts import build_artifacts
from engine.core import load_methodology


def test_watchlist_feature_has_detected_at_and_no_grade():
    wl = [{"id": "fr-demo-projet", "name": "Demo projet", "country": "FR",
           "coordinates": {"lat": 48.8, "lon": 2.3}, "project_status": "announced",
           "source": {"title": "OSM", "url": "https://www.openstreetmap.org/way/1", "accessed": "2026-09-07"},
           "facts": []}]
    with tempfile.TemporaryDirectory() as d:
        build_artifacts({}, load_methodology(), out_dir=Path(d), watchlist=wl)
        props = json.loads((Path(d) / "watchlist.geojson").read_text())["features"][0]["properties"]
    assert props["detected_at"] == "2026-09-07"
    assert props["watchlist_status"] == "en_veille"
    assert "grade" not in json.dumps(props).lower()   # A-19: an en-veille feature is never graded
