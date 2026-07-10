# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""EEA WISE — national WFD ecological status table, cached (the W2 join).

France's DCE status is federated across 6 agences on slow/unreliable ArcGIS servers, but every
country reports the same figures to the EEA, whose WISE database exposes them through one public
SQL API (Discodata). One query returns all ~11 400 French water bodies (2022 reporting cycle) with
their ecological status class, keyed by the same code Sandre's WFS resolves at a point. We cache
that once and join locally.

The same table carries every member state (EU-recon 2026-07-09 proved BE end-to-end), so the query
is parameterized by country code — only the point→water-body-code resolution leg is national.
"""

import json
import urllib.parse

from .cache import cached_path
from .http import SourceUnavailable


def _sql_for(country: str) -> str:
    """Current (2022) reporting cycle: code + ecological status class for one member state."""
    return ("SELECT euSurfaceWaterBodyCode, swEcologicalStatusOrPotentialValue "
            "FROM [WISE_WFD].[latest].[SWB_SurfaceWaterBody] "
            f"WHERE countryCode='{country}' AND cYear=2022")


# All French surface water bodies — kept as a module constant (guarded by tests).
_SQL = _sql_for("FR")

_status_index: dict[str, dict[str, str]] = {}


def load_wise_status(country: str = "FR") -> dict[str, str]:
    """{water_body_code: status_class '1'..'5'} for one country, from the cached WISE extract."""
    if country in _status_index:
        return _status_index[country]
    url = "https://discodata.eea.europa.eu/sql?" + urllib.parse.urlencode(
        {"query": _sql_for(country), "p": 1, "nrOfHits": 20000})
    path = cached_path(url, f"wise_wfd_{country.lower()}_2022.json")
    results = json.loads(path.read_text()).get("results", [])
    index = {
        r["euSurfaceWaterBodyCode"]: r["swEcologicalStatusOrPotentialValue"]
        for r in results if r.get("euSurfaceWaterBodyCode")
    }
    if not index:
        raise SourceUnavailable(f"WISE extract for {country} parsed to zero rows")
    _status_index[country] = index
    return index
