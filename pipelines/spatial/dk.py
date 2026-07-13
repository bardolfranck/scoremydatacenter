# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Denmark — a plain EU member on the shared factory. The wind-grid, water-abundant end.

Full commons member → one line. Denmark is the wind-power poster child (the grid runs on offshore
wind) and the Nordic hyperscale magnet (Meta Odense, Apple Viborg, Google Fredericia — not in the
interconnection scrape, a priority DC-list add). WRI Aqueduct reads no_stress across the country —
flat, wet, water-abundant. L3 stays a gap: the EEA IED has_seveso flag is not populated for Denmark
(0 sites), so 'none within 5 km' would be a false negative — the national register (Miljøstyrelsen)
is the source (v1). Deeper wiring (Energinet grid, Danmarks Statistik income) is a v1 adapter.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

DK_SPEC = make_eu_member_spec("DK", summary={
    "fr": "BROUILLON DK (socle EU + revenu Eurostat) — réseau éolien, eau abondante (Aqueduct no_stress). Hyperscale nordique (Meta/Apple/Google) à ajouter. À vérifier.",
    "en": "DK DRAFT (EU-level + Eurostat income) — wind grid, water-abundant (Aqueduct no_stress). Nordic hyperscale (Meta/Apple/Google) to add. Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(DK_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(DK_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
