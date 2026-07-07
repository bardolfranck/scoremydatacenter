# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""EEA WISE — national WFD ecological status table, cached (the W2 join).

France's DCE status is federated across 6 agences on slow/unreliable ArcGIS servers, but every
country reports the same figures to the EEA, whose WISE database exposes them through one public
SQL API (Discodata). One query returns all ~11 400 French water bodies (2022 reporting cycle) with
their ecological status class, keyed by the same code Sandre's WFS resolves at a point. We cache
that once and join locally.
"""

import json
import urllib.parse

from .cache import cached_path
from .http import SourceUnavailable

# All French surface water bodies, current (2022) reporting cycle: code + ecological status class.
_SQL = ("SELECT euSurfaceWaterBodyCode, swEcologicalStatusOrPotentialValue "
        "FROM [WISE_WFD].[latest].[SWB_SurfaceWaterBody] "
        "WHERE countryCode='FR' AND cYear=2022")
_DISCO_URL = "https://discodata.eea.europa.eu/sql?" + urllib.parse.urlencode(
    {"query": _SQL, "p": 1, "nrOfHits": 20000})

_status_index: dict[str, str] | None = None


def load_wise_status() -> dict[str, str]:
    """{water_body_code: status_class '1'..'5'} for France, from the cached WISE extract."""
    global _status_index
    if _status_index is not None:
        return _status_index
    path = cached_path(_DISCO_URL, "wise_wfd_fr_2022.json")
    results = json.loads(path.read_text()).get("results", [])
    _status_index = {
        r["euSurfaceWaterBodyCode"]: r["swEcologicalStatusOrPotentialValue"]
        for r in results if r.get("euSurfaceWaterBodyCode")
    }
    if not _status_index:
        raise SourceUnavailable("WISE extract parsed to zero rows")
    return _status_index
