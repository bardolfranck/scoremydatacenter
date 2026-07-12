# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Finland — a plain EU member on the shared factory. Clean grid, cold climate.

E1 ~64 gCO2/kWh (nuclear + hydro + wind). Google Hamina (seawater cooling), the LUMI
supercomputer — Finland is a flagship green/cold DC destination. Deep indicators are a national
adapter later; v0 is presence.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

FI_SPEC = make_eu_member_spec("FI", summary={
    "fr": "BROUILLON FI v0 (socle EU) — grille propre (~64 g/kWh) + climat froid. À vérifier.",
    "en": "FI DRAFT v0 (EU-level) — clean grid (~64 gCO2/kWh) + cold climate. Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(FI_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(FI_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
