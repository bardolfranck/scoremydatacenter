# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Non-circularity guard — the SITE grade must not encode contestation.

This underwrites the « note = indicateur avancé » pre-registration
(2-methodo-scoring/preenregistrement-note-precurseur.md): the exposure (site grade
at T0) and the outcome (contestation detected AFTER T0) must be independent, or the
prospective test is circular. Two mechanical proofs, so the claim is OPPOSABLE
(re-run at every build) rather than merely attested:

  (1) A-21 display layer: the `contestation[]` array fed onto a fiche NEVER moves any
      grade. Inject fabricated opposition facts → site grade byte-identical.

  (2) The two contestation-adjacent BASE indicators — L6 « niveau de contestation
      observé » and L7 « position des élus » — sit in the site block by design, so the
      architecture PERMITS them to carry contestation into the site grade. The
      pre-registration's non-circularity therefore rests on an EMPIRICAL fact about the
      corpus, asserted here and frozen: L6 and L7 are unpopulated (`missing`) across the
      whole scored corpus, contributing exactly 0 to every site grade. If a future run
      populates them, this test fails LOUDLY — forcing the pre-registration to be
      revisited before the exposure is contaminated.
"""

import copy

from engine.core import load_datacenters, load_methodology
from engine.scoring import score_datacenter

_CONTESTATION_BASE_INDICATORS = {"L6", "L7"}


def _site(dc, methodology):
    return score_datacenter(dc, methodology)["grades"]["site"]


def test_contestation_array_never_moves_the_site_grade():
    """A-21: contestation[] is a display annotation, never a scoring input."""
    methodology = load_methodology()
    dcs = load_datacenters()
    fabricated = [
        {"kind": "opposition", "label": {"fr": "x", "en": "x"},
         "source": {"title": "t", "url": "https://e.org", "accessed": "2026-09-05"},
         "self_reported": False},
        {"kind": "moratorium", "label": {"fr": "y", "en": "y"},
         "source": {"title": "t", "url": "https://e.org", "accessed": "2026-09-05"},
         "self_reported": False},
    ]
    for dc_id, dc in dcs.items():
        before = _site(dc, methodology)
        mutant = copy.deepcopy(dc)
        mutant["contestation"] = fabricated
        after = _site(mutant, methodology)
        assert before == after, (
            f"{dc_id}: the site grade changed when contestation[] was injected — "
            "the display layer leaked into the score (A-21 violated)"
        )


def test_contestation_base_indicators_are_unpopulated_across_the_corpus():
    """Frozen empirical fact underpinning the pre-registration's exposure: the site
    grade carries no contestation because L6/L7 are missing everywhere. A future fill
    must break this test on purpose, not silently contaminate the leading-indicator
    claim."""
    dcs = load_datacenters()
    offenders = []
    for dc_id, dc in dcs.items():
        if dc_id.startswith(("zz-", "il-")):
            continue
        for e in dc["indicators"]:
            if e["id"] in _CONTESTATION_BASE_INDICATORS and e.get("status") != "missing":
                offenders.append(f"{dc_id}:{e['id']}={e.get('status')}")
    assert not offenders, (
        "L6/L7 (contestation-adjacent base indicators) are now populated on: "
        f"{offenders[:10]}… — the SITE grade would encode contestation. Revisit the "
        "'note = leading indicator' pre-registration BEFORE letting these into the exposure."
    )
