# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Norway — an EEA (not EU) member on the shared factory, with the deviation natura=False.

Norway is in the EEA, not the EU: it reports to EEA WISE (W2 works — 32k water bodies), Corine
covers it, energy-charts serves it (E1 ~30 gCO2/kWh, almost pure hydro — the cleanest grid in
Europe). Natura 2000 does not apply, but the EEA CDDA layer (nationally designated protected
areas) DOES include Norway, so F1 is recovered from that common brick — no national rebuild.
Income (L1) rides in provenance from Eurostat (Norway is covered, lagged to ~2020). Grid capacity
(E2/E3) and Seveso (L3) stay gaps: Statnett's queue map is Power BI / Excel only, and the EEA IED
`has_seveso` flag is not populated for Norway (0 sites) — a "none" reading would be a false
negative, so we do not assert it (DSB register would be the national source).
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

NO_SPEC = make_eu_member_spec("NO", natura=False, f1_cdda=True, summary={
    "fr": "BROUILLON NO (EEA : carbone réseau, masse d'eau, Corine, aires protégées CDDA + revenu Eurostat) — grille quasi 100% hydro (~30 g/kWh). À vérifier.",
    "en": "NO DRAFT (EEA: grid carbon, water body, Corine, CDDA protected areas + Eurostat income) — near-100% hydro grid (~30 gCO2/kWh). Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(NO_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(NO_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
