# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Sweden — a plain EU member on the shared factory. The clean-grid end of the spectrum.

E1 ~23 gCO2/kWh (hydro + nuclear) — the opposite of Poland; cheap green power + cold climate is
exactly why the hyperscalers (Meta Luleå, AWS eu-north-1) went north. A-reservation means even
these near-ideal territories cap at B without operational proof — the doctrine on display.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

SE_SPEC = make_eu_member_spec("SE", summary={
    "fr": "BROUILLON SE v0 (socle EU) — grille très propre (~23 g/kWh, hydro+nucléaire). À vérifier.",
    "en": "SE DRAFT v0 (EU-level) — very clean grid (~23 gCO2/kWh, hydro+nuclear). Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(SE_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(SE_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
