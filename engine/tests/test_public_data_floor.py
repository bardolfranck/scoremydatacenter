# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Anti-pillage floor (Franck 2026-07-22): map.geojson is the ONE data file the
site must serve publicly (the map fetches it client-side), so it is the paywall's
real frontier. It may carry ONLY the free "Seau A" floor — identity + the site
LETTER + a coarse size tier + coordinates rounded to ~1 km. Anything sellable
(operator grade, per-pillar scores, exact power_mw, the citable quote,
confidence, precise GPS) must NEVER reappear here, or the future API is pierced
before it exists. A regression that re-fattens the geojson breaks the build."""

from engine.artifacts import build_artifacts
from engine.core import load_datacenters, load_methodology

# The exact free floor. `reserved_site` is optional (only when the A-25 reserve
# applies) — it is part of the public letter's presentation, not a sold field.
SEAU_A_KEYS = {
    "id", "name", "operator", "municipality", "country",
    "grade_site", "project_status", "size_tier", "reserved_site",
}
# Fields that are worth money (Seau B) and must stay OUT of the public geojson.
FORBIDDEN = {
    "grade_project_process", "reserved_pp", "power_mw", "pillars",
    "quote_fr", "confidence", "publication_status",
}


def _map_features():
    results_dir = None
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        build_artifacts(load_datacenters(), load_methodology(), out_dir=Path(d))
        import json
        return json.loads((Path(d) / "map.geojson").read_text())["features"]


def test_map_geojson_carries_only_the_free_floor():
    for f in _map_features():
        keys = set(f["properties"])
        extra = keys - SEAU_A_KEYS
        assert not extra, f"map.geojson leaked non-free field(s) {extra} on {f['properties'].get('id')}"


def test_map_geojson_has_no_sellable_field():
    for f in _map_features():
        hit = FORBIDDEN & set(f["properties"])
        assert not hit, f"SELLABLE field(s) {hit} back in the public map.geojson ({f['properties'].get('id')})"


def test_map_geojson_coordinates_are_rounded_to_1km():
    # ~1 km == 2 decimal degrees. A precise rooftop GPS in a public file is a paid item.
    for f in _map_features():
        for c in f["geometry"]["coordinates"]:
            assert round(c, 2) == c, f"precise GPS {c} in public map.geojson ({f['properties'].get('id')})"
