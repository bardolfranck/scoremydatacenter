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

SPECS = {
    "FR": FR_SPEC,
    "BE": BE_SPEC,
    "NL": NL_SPEC,
    "LU": LU_SPEC,
    "DE": DE_SPEC,
    "PL": PL_SPEC,
}


def get_spec(iso: str) -> dict:
    """Return the spec for an ISO 3166-1 alpha-2 code (case-insensitive)."""
    iso = iso.upper()
    if iso not in SPECS:
        raise KeyError(f"no spatial adapter for country {iso!r}; known: {sorted(SPECS)}")
    return SPECS[iso]
