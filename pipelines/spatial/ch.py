# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Switzerland — EEA-cooperating non-EU country on the shared factory, natura=False.

Switzerland is EFTA (not EU, not EEA-agreement) but IS an EEA-32 member country of the
European Environment Agency: Corine covers it, CDDA (nationally designated protected
areas) includes it, and energy-charts serves the `ch` zone (~50 gCO2/kWh, hydro-dominated
with nuclear). Natura 2000 does not apply (Emerald Network) — F1 rides the CDDA brick,
same recovery as Norway. Not bound by the Water Framework Directive: if WISE returns no
water body, W2 stays an honest gap rather than a guess. Grid capacity (E2/E3, Swissgrid),
abstraction volumes (W3) and the OPAM major-accident register (L3, the Seveso analogue)
are national feeds not wired in v1 — declared gaps, never zeros.
"""

from .country import run_cli
from .eu_member import make_eu_member_spec

CH_SPEC = make_eu_member_spec("CH", natura=False, f1_cdda=True, summary={
    "fr": "BROUILLON CH (EEA-32 : carbone réseau energy-charts, Aqueduct, Corine, aires protégées CDDA + revenu Eurostat) — grille hydro-nucléaire (~50 g/kWh). Hors DCE : W2 peut rester lacunaire. À vérifier.",
    "en": "CH DRAFT (EEA-32: grid carbon, Aqueduct, Corine, CDDA protected areas + Eurostat income) — hydro-nuclear grid (~50 gCO2/kWh). Outside WFD: W2 may stay a gap. Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(CH_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(CH_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
