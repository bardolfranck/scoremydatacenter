# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""SIREN operator_type matcher — pure-logic tests (no network). Pins the load-bearing disciplines:
token-equality (not substring), NAF grid + coreness (COLT → COLT TECHNOLOGY SERVICES), ordered-exact,
the generic-token and single-generic no-guess tightens, and the developer never-auto-demote flag."""
from pipelines.status_proof import siren


def _search(results):
    """Injected register search: ignores the query, returns canned results (pure, no network)."""
    return lambda q, cp=None, **k: list(results)


def _r(nom, naf, commune=None, sirenv="000"):
    return {"nom_complet": nom, "activite_principale": naf, "siren": sirenv,
            "siege": {"libelle_commune": commune or ""}}


def _fiche(name, operator="unknown"):
    return {"id": "fr-x", "name": name, "operator": operator}   # no lat/lon → commune resolver unused


def test_token_equality_not_substring():
    # brand «colt» must NOT match «COLTER» (substring) — no candidate → unknown
    out = siren.match(_fiche("Colt"), search=_search([_r("COLTER", "47.91A")]))
    assert out["operator_type"] == "unknown" and out["resolved"] is None


def test_colt_coreness_picks_canonical_operator():
    # bare «COLT» 62.01Z vs «COLT TECHNOLOGY SERVICES» 61.10Z → NAF-coreness picks the telecom entity
    res = [_r("COLT", "62.01Z", sirenv="BARE"), _r("COLT TECHNOLOGY SERVICES", "61.10Z", sirenv="REAL")]
    out = siren.match(_fiche("Colt"), search=_search(res))
    assert out["resolved"]["siren"] == "REAL"
    assert out["match_strength"] == "superset" and out["emit_tier"] == "lower_confidence"


def test_naf_reject_homonym_off_trade():
    # «orange» ⊆ «ADAM ORANGE» but NAF 81.21Z (cleaning) → rejected → unknown, never a false operator
    out = siren.match(_fiche("Orange"), search=_search([_r("ADAM ORANGE", "81.21Z", "REIMS")]))
    assert out["operator_type"] == "unknown"


def test_generic_only_token_is_unknown():
    # «C-datacenters» reduces to the generic word «datacenters» → must not match TITAN DATACENTERS
    out = siren.match(_fiche("C-datacenters"), search=_search([_r("TITAN DATACENTERS FRANCE", "63.11Z")]))
    assert out["operator_type"] == "unknown" and "generic" in out["reason"]


def test_ordered_exact_beats_reordered_and_coreness():
    # same token-set, different order: «RESEAU CONCEPT» (ordered, 62.02A) must win over «CONCEPT RESEAU»
    # (reordered, even with a more-core 61.10Z) — a reordered name is a different company
    res = [_r("CONCEPT RESEAU", "61.10Z", sirenv="WRONG"), _r("RESEAU CONCEPT", "62.02A", sirenv="RIGHT")]
    out = siren.match(_fiche("Réseau Concept"), search=_search(res))
    assert out["resolved"]["siren"] == "RIGHT"


def test_single_generic_token_non_core_tightens_to_unknown():
    # single short token «SIGMA» landing a non-core operator NAF (62.01Z) → no-guess → unknown
    out = siren.match(_fiche("SIGMA"), search=_search([_r("SIGMA", "62.01Z")]))
    assert out["operator_type"] == "unknown"


def test_single_token_core_naf_is_kept():
    # single token but CORE NAF (61.10Z) is trustworthy → confident operator-fill
    out = siren.match(_fiche("D-LAKE"), search=_search([_r("D-LAKE", "61.10Z", sirenv="DL")]))
    assert out["operator_type"] == "operator" and out["emit_tier"] == "confident"


def test_confident_exact_operator():
    out = siren.match(_fiche("DATACAMPUS"), search=_search([_r("DATACAMPUS", "63.11Z", sirenv="DCP")]))
    assert out["emit_tier"] == "confident" and out["resolved"]["siren"] == "DCP"


def test_developer_flagged_needs_confirm_never_auto():
    # a promotion-immobilière entity → developer, but flagged needs_confirm (feeds no auto-demote)
    out = siren.match(_fiche("TAS Group"), search=_search([_r("TAS GROUPE", "41.10A", sirenv="TAS")]))
    assert out["operator_type"] == "developer"
    assert out["emit_tier"] == "developer_needs_confirm" and out["needs_confirm"] is True


def test_fetch_error_is_loud_not_silent():
    def boom(q, cp=None, **k):
        raise siren.SirenFetchError("network down")
    try:
        siren.match(_fiche("Equinix"), search=boom)
    except siren.SirenFetchError:
        return
    raise AssertionError("match must propagate SirenFetchError, never swallow it into a silent unknown")
