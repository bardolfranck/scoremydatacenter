# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Austria — a plain EU member on the shared factory. The Alpine water-abundant end.

Full commons member → one line. The signal is the mirror of Iberia: Vienna (the Austrian DC hub) and
the Alpine sites read WRI Aqueduct **no_stress** — hydro-rich, cool, the low-water-risk end of the
spectrum. L3 stays a gap: the EEA IED has_seveso flag is not populated for Austria (0 sites), so a
'none within 5 km' reading would be a false negative — the national register (BMK/Länder) is the
source (v1). Deeper wiring (APG grid, Statistik Austria income bands) is a v1 national adapter.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

AT_SPEC = make_eu_member_spec("AT", summary={
    "fr": "BROUILLON AT (socle EU + revenu Eurostat) — bout alpin peu stressé en eau (Aqueduct no_stress), réseau hydro. À vérifier.",
    "en": "AT DRAFT (EU-level + Eurostat income) — Alpine low-water-stress end (Aqueduct no_stress), hydro grid. Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(AT_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(AT_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
