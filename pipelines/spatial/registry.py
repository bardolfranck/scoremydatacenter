# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""The country registry — ONE place that maps an ISO code to its spatial spec.

Rule (2026-07-11): one way to run. The batch runner, the orchestrator, and any future caller
resolve a country here instead of importing a per-country module by hand. Adding a country =
add its spec to this dict (plus its spec file); nothing else in the run path changes.
"""

from .collect import FR_SPEC
from .be.collect import BE_SPEC
from .nl import NL_SPEC
from .lu import LU_SPEC
from .de import DE_SPEC
from .pl import PL_SPEC
from .ie import IE_SPEC
from .gb import GB_SPEC
from .se import SE_SPEC
from .fi import FI_SPEC
from .no import NO_SPEC
from .es import ES_SPEC
from .it import IT_SPEC

SPECS = {
    "FR": FR_SPEC,
    "BE": BE_SPEC,
    "NL": NL_SPEC,
    "LU": LU_SPEC,
    "DE": DE_SPEC,
    "PL": PL_SPEC,
    "IE": IE_SPEC,
    "GB": GB_SPEC,
    "SE": SE_SPEC,
    "FI": FI_SPEC,
    "NO": NO_SPEC,
    "ES": ES_SPEC,
    "IT": IT_SPEC,
}


def get_spec(iso: str) -> dict:
    """Return the spec for an ISO 3166-1 alpha-2 code (case-insensitive)."""
    iso = iso.upper()
    if iso not in SPECS:
        raise KeyError(f"no spatial adapter for country {iso!r}; known: {sorted(SPECS)}")
    return SPECS[iso]
