# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Spain — a plain EU member on the shared factory. The angle is WATER.

Spain is fully in the commons (WISE + Natura + Corine + energy-charts + Eurostat income), so the
adapter is one line. What makes ES worth adding is the signal the EU bricks already carry: Madrid —
the third European DC hub after FLAP — and Barcelona sit on WRI Aqueduct **Extremely High** baseline
water stress (W1 = zre_or_crisis). Spain's data-center boom is happening on some of Europe's most
water-stressed ground; W1 says so out of the box. L3 via the EEA IED has_seveso flag (populated for
Spain — 171 sites in 2024). Deeper national wiring (REE grid capacity, INE income bands) is a v1
national adapter; the hyperscale water-controversy campuses (Meta Talavera, AWS Aragón) are not in
the interconnection scrape and are the priority DC-list addition.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

ES_SPEC = make_eu_member_spec("ES", l3_ied=True, summary={
    "fr": "BROUILLON ES (socle EU + Seveso EEA + revenu Eurostat) — angle EAU : Madrid/Barcelone sur stress hydrique « extrêmement élevé » (Aqueduct). À vérifier.",
    "en": "ES DRAFT (EU-level + EEA Seveso + Eurostat income) — WATER angle: Madrid/Barcelona on 'extremely high' water stress (Aqueduct). Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(ES_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(ES_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
