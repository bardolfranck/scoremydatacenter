# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Italy — a plain EU member on the shared factory. The angle is the north-south water divide.

Italy is fully in the commons, so the adapter is one line. The signal the EU bricks carry is a
geography lesson: the DC hub is Milan (the third-largest European colo market after FLAP-D), on the
water-rich Po plain — WRI Aqueduct reads no_stress there. But the south — Rome, Bari, Palermo/Sicily
— sits on Aqueduct **Extremely High** water stress (zre_or_crisis). So Italy's water risk is not
national, it is where the DC lands: abundant in the north, acute in the Mezzogiorno. L3 via the EEA
IED has_seveso flag (populated for Italy — 77 sites in 2024). Deeper national wiring (Terna grid
capacity, ISTAT income bands) is a v1 national adapter.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

IT_SPEC = make_eu_member_spec("IT", l3_ied=True, summary={
    "fr": "BROUILLON IT (socle EU + Seveso EEA + revenu Eurostat) — angle EAU : fracture nord-sud (Milan abondant, Rome/Sud en stress « extrême », Aqueduct). À vérifier.",
    "en": "IT DRAFT (EU-level + EEA Seveso + Eurostat income) — WATER angle: north-south divide (Milan abundant, Rome/South 'extremely high', Aqueduct). Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(IT_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(IT_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
