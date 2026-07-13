# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Portugal — a plain EU member on the shared factory. The angle, like Spain, is WATER.

Full commons member → one line. Portugal is pitching itself as an Atlantic-cable landing hub (Sines:
Start Campus, EllaLink), yet WRI Aqueduct reads Lisbon and Sines on **Extremely High** baseline
water stress (W1 zre_or_crisis) — the Iberian water squeeze does not stop at the coast. L3 via the
EEA IED has_seveso flag (populated for Portugal — 632 site-rows in 2024). Deeper national wiring
(REN grid, INE income bands) is a v1 national adapter.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

PT_SPEC = make_eu_member_spec("PT", l3_ied=True, summary={
    "fr": "BROUILLON PT (socle EU + Seveso EEA + revenu Eurostat) — angle EAU : Lisbonne et Sines en stress hydrique « extrême » (Aqueduct). À vérifier.",
    "en": "PT DRAFT (EU-level + EEA Seveso + Eurostat income) — WATER angle: Lisbon and Sines on 'extremely high' water stress (Aqueduct). Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(PT_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(PT_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
