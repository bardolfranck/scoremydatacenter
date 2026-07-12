# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Norway — an EEA (not EU) member on the shared factory, with the deviation natura=False.

Norway is in the EEA, not the EU: it reports to EEA WISE (W2 works — 32k water bodies), Corine
covers it, energy-charts serves it (E1 ~30 gCO2/kWh, almost pure hydro — the cleanest grid in
Europe). The one gap is F1: Norway is outside Natura 2000, its equivalent is the Emerald Network
(Bern Convention) — a national/EEA protected-areas layer to wire later. So NO = 3/12, and the
EEA-vs-EU line shows up in exactly one indicator, not a whole rebuild.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

NO_SPEC = make_eu_member_spec("NO", natura=False, summary={
    "fr": "BROUILLON NO v0 (EEA : carbone réseau, masse d'eau, Corine) — grille quasi 100% hydro (~30 g/kWh). Natura remplacé par Emerald. À vérifier.",
    "en": "NO DRAFT v0 (EEA: grid carbon, water body, Corine) — near-100% hydro grid (~30 gCO2/kWh). Natura replaced by Emerald. Verify before use.",
}, extra_gaps={
    "F1": "not_collected — Norway is outside Natura 2000; the Emerald Network (Bern Convention) is the "
          "equivalent — a national/EEA protected-areas layer to wire (v1)",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(NO_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(NO_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
