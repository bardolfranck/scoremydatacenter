# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Finland — the shared EU factory + the EEA Seveso brick + Eurostat income.

E1 ~64 gCO2/kWh (nuclear + hydro + wind). Google Hamina (seawater cooling), the LUMI
supercomputer — Finland is a flagship green/cold DC destination. Two deepenings that need no
national wiring: L3 via the EEA IED `has_seveso` flag (populated for Finland — 113 sites in 2024,
so the EU brick is reliable) and L1 raw via the common Eurostat NUTS2 income. Grid capacity (E2/E3)
stays a gap: Fingrid's open-data API is key-gated and national-timeseries only, not locational.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

FI_SPEC = make_eu_member_spec("FI", l3_ied=True, summary={
    "fr": "BROUILLON FI (socle EU + Seveso EEA + revenu Eurostat) — grille propre (~64 g/kWh) + climat froid. À vérifier.",
    "en": "FI DRAFT (EU-level + EEA Seveso + Eurostat income) — clean grid (~64 gCO2/kWh) + cold climate. Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(FI_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(FI_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
