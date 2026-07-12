# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Ireland — an EU member on the shared factory, with the one deviation e1=False.

W2/F1/F2 work out of the box (full EU member). The single hole: energy-charts does not serve the
Irish synchronous zone (probed: HTTP 500 for `ie`). Fitting — Ireland's real story is grid
CAPACITY (Dublin's moratorium = EirGrid halted connections), a deep national indicator (EirGrid/
SEMO), not the EU carbon feed. v0 is presence + the contestation angle (Grange Castle).
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

IE_SPEC = make_eu_member_spec("IE", e1=False, summary={
    "fr": "BROUILLON IE v0 (socle EU : masse d'eau, Natura, Corine) — angle contestation (moratoire Dublin). À vérifier.",
    "en": "IE DRAFT v0 (EU-level: water body, Natura, Corine) — contestation angle (Dublin moratorium). Verify before use.",
}, extra_gaps={
    "E1": "not_collected — energy-charts does not serve the Irish zone (HTTP 500); EirGrid CO2 API (v1)",
    "E2": "not_collected — EirGrid/SEMO capacity — THE Irish story (Dublin moratorium), a deep national adapter (v1)",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(IE_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(IE_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
