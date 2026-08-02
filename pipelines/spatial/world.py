# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""World commons — collectors that work for ANY point/country on Earth, keyless.

The W1-Aqueduct class, extended (unlocked by the Israel recon, 2026-07-27): these bricks are
what turns the cadrage's "6-8-feature world model" (SOM map, screening API) from postulate into
buildable, and they lift every non-EU country at once (US, CA, IL, Maghreb…). Doctrine
unchanged: outside referential-rich countries these feed the watchlist and the screening
typology — NEVER a grade (A-19).

  * collect_e1_ember           — yearly national grid CO2 intensity (Ember, public CSV, cached)
  * collect_f2_global_landcover— land cover at point (Esri/Impact Observatory Sentinel-2 10m
                                 annual LULC, CC BY 4.0, ArcGIS `getSamples`)

Gotchas pinned while probing (2026-07-27):
  - The LULC ImageServer's `identify` is BROKEN by a bad default sort (`sortField: Year,
    sortValue: 2050` → type error whatever the mosaicRule). `getSamples` works keyless — use it.
  - Ember's REST API is keyed, but the full yearly CSV sits on a public bucket (49 MB) —
    downloaded once into the shared cache, then joined by ISO-3 (the Filosofi/WISE pattern).
"""

import csv

from .cache import cached_path
from .bands import io_lulc_to_category
from .http import SourceUnavailable, get_json

EMBER_YEARLY_CSV = ("https://storage.googleapis.com/emb-prod-bkt-publicdata/"
                    "public-downloads/yearly_full_release_long_format.csv")
EMBER_HUMAN_URL = "https://ember-energy.org/data/yearly-electricity-data/"
# Esri Living Atlas hosting of Impact Observatory's Sentinel-2 10m annual land cover (CC BY 4.0).
IO_LULC_IMAGESERVER = ("https://ic.imagery1.arcgis.com/arcgis/rest/services/"
                       "Sentinel2_10m_LandCover/ImageServer")
IO_LULC_HUMAN_URL = "https://livingatlas.arcgis.com/landcover/"
# time window served by the mosaic — latest full year first (fallback one back if unsampled)
_LULC_YEARS = ((2023, 1672531200000, 1704067199000), (2022, 1640995200000, 1672531199000))

_ember_memo: dict[str, tuple[int, float] | None] = {}


def _ember_intensity(iso3: str) -> tuple[int, float] | None:
    """(latest_year, gCO2_per_kWh) for a country from the cached Ember yearly dataset."""
    iso3 = (iso3 or "").upper()
    if iso3 in _ember_memo:
        return _ember_memo[iso3]
    path = cached_path(EMBER_YEARLY_CSV, "ember_yearly_long.csv")
    best: tuple[int, float] | None = None
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if (row.get("ISO 3 code") == iso3 and row.get("Variable") == "CO2 intensity"
                    and row.get("Unit") == "gCO2/kWh" and row.get("Value")):
                year = int(row["Year"])
                if best is None or year > best[0]:
                    best = (year, float(row["Value"]))
    _ember_memo[iso3] = best
    return best


def collect_e1_ember(iso3: str, accessed: str) -> dict | None:
    """E1 yearly national grid carbon for ANY country — Ember open dataset, keyless.

    A YEARLY national mean, not the 12-month rolling mean of the energy-charts brick — one
    figure per country per year, stable and citable (Ember is the referential the IEA and the
    world press quote). Where energy-charts serves a country, prefer it (finer window); Ember is
    the world fallback that never 500s on a zone.
    """
    try:
        best = _ember_intensity(iso3)
    except SourceUnavailable:
        return None
    if best is None:
        return None
    year, value = best
    return {
        "id": "E1", "status": "measured", "value": value,
        "source": {"title": f"Ember — yearly electricity data: CO2 intensity {value} gCO2/kWh "
                            f"({iso3} {year}, national grid mean)",
                   "url": EMBER_HUMAN_URL, "accessed": accessed},
    }


def lulc_class_at_point(lat: float, lon: float) -> tuple[str | None, int | None]:
    """(raw_class, year) via ArcGIS getSamples — the endpoint that works keyless."""
    geometry = ('{"x":%f,"y":%f,"spatialReference":{"wkid":4326}}' % (lon, lat))
    for year, t0, t1 in _LULC_YEARS:
        try:
            data = get_json(IO_LULC_IMAGESERVER + "/getSamples", params={
                "geometry": geometry, "geometryType": "esriGeometryPoint",
                "returnFirstValueOnly": "true", "time": f"{t0},{t1}", "f": "json"})
        except SourceUnavailable:
            continue
        samples = data.get("samples") or []
        value = samples[0].get("value") if samples else None
        if value not in (None, "", "NoData"):
            return str(value), year
    return None, None


def collect_f2_global_landcover(ctx: dict, prov: dict) -> list[dict]:
    """F2 land cover for ANY point on Earth — Impact Observatory/Esri Sentinel-2 10m (CC BY 4.0).

    Same category enum as the Corine path (comparability by construction). Cloud/nodata classes
    map to None — we never guess a soil status. Spec-shaped collector (ctx, prov)."""
    raw, year = lulc_class_at_point(ctx["lat"], ctx["lon"])
    category = io_lulc_to_category(raw)
    prov["f2_crosscheck"] = {"primary": None, "primary_source": None,
                             "land_cover": category, "io_lulc_class": raw, "agree": None,
                             "note": "global land-cover brick (no national zoning source)"}
    if category is None:
        return []
    return [{"id": "F2", "status": "measured", "value": category,
             "source": {"title": f"Sentinel-2 10m annual land cover (Impact Observatory/Esri, "
                                 f"CC BY 4.0) — class {raw} at point, {year}",
                        "url": IO_LULC_HUMAN_URL, "accessed": ctx["accessed"]}}]
