# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Poland — a plain EU member on the shared factory (the energy angle comes for free).

No national quirk: PL is fully described by the EU-level bricks. The point is the angle E1 carries
alone — the Polish grid is the dirtiest in Europe (~650 gCO2/kWh, coal) while Warsaw is the
fastest-growing EU hub. Deep indicators (PSE capacity, GUS income, Seveso) are a national adapter
later; CEE is presence + energy, not a revenue market (cadrage: profondeur suit la donnée).
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

PL_SPEC = make_eu_member_spec("PL", summary={
    "fr": "BROUILLON PL v0 (socle EU) — angle énergie : la grille la plus sale d'Europe (~650 g/kWh). À vérifier.",
    "en": "PL DRAFT v0 (EU-level) — energy angle: Europe's dirtiest grid (~650 gCO2/kWh). Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(PL_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(PL_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
