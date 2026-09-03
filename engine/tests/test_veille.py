# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the veille chantier (no network) — the two anti-leak invariants that
agent-codeur-site gates on:

  (a) ZERO judgement key (score/grade/grade_site/grades/confidence/pillar/pillars) anywhere in the
      candidate drafts, the rendered digest, or the manifest — en-veille is sourced FACTS, never a
      score (A-19/A-21). The digest REFUSES to render a candidate that carries one.
  (b) `publishable:false` (a commercial lead not re-verified in the open) shows a NON-PUBLIABLE
      banner AND is excluded from the promote-to-render subset — it never travels to a served
      artifact from our side.
"""

import json
import re

import pytest

from pipelines.veille import digest as D
from pipelines.veille import fr

_JUDGEMENT_KEYS = {"score", "scores", "grade", "grades", "grade_site",
                   "grade_project_process", "confidence", "pillar", "pillars"}


def _candidate(**over):
    c = {
        "id": "fr-veille-test-1", "state": "en_veille",
        "name": "Projet centre de données — Testville", "operator": "Equinix",
        "municipality": "Testville (99)", "country": "FR", "project_status": "announced",
        "coordinates": None,
        "source": {"title": "Presse test", "url": "https://example.org/a", "accessed": "2026-07-28"},
        "facts": [{"kind": "press", "label": {"fr": "Projet annoncé", "en": "Announced project"},
                   "source": {"title": "Presse", "url": "https://example.org/a"}}],
        "provenance": {"source": "GDELT", "url": "https://example.org/a",
                       "license": "GDELT DOC API — libre avec attribution", "publishable": True},
        "detection": {"detected_at": "2026-07-28", "feed": "gdelt", "intent": "announce",
                      "dedup": {"status": "new", "nearest_id": None, "distance_km": None}},
        "tier1_preview": [],
    }
    c.update(over)
    return c


def _lead(**over):
    return _candidate(
        id="fr-veille-lead-1", operator="opérateur cité par DCMag",
        provenance={"source": "DCMag", "url": "https://dcmag.example/x", "license": "commercial",
                    "publishable": False, "lead_only": True, "note": "à re-vérifier en source ouverte"},
        **over)


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


# --- invariant (a): no judgement anywhere ----------------------------------------------------

def test_validate_rejects_a_judgement_key():
    bad = _candidate(score=42)                              # a score smuggled onto the candidate
    assert D.validate_candidate(bad), "a candidate carrying a score must be rejected"
    with pytest.raises(ValueError):
        D.render_digest([bad], "2026-07-28")


def test_validate_rejects_a_nested_judgement_key():
    bad = _candidate(facts=[{"kind": "press", "label": {"fr": "x", "en": "x"},
                             "source": {"url": "u"}, "grades": {"site": "C"}}])
    assert any("judgement" in p for p in D.validate_candidate(bad))


def test_rendered_outputs_carry_no_judgement_keys():
    cands = [_candidate(), _lead()]
    html = D.render_digest(cands, "2026-07-28")
    manifest = D.build_manifest(cands, "2026-07-28")
    # structured artifacts: no judgement KEY anywhere
    for artifact in (cands, manifest):
        leaked = _JUDGEMENT_KEYS & set(_keys(artifact))
        assert not leaked, f"judgement key leaked into a served artifact: {leaked}"
    # HTML: no A–E grade badge pattern (a bare capital letter presented as a note)
    assert not re.search(r"\bnot[eé]e?\s+[A-E]\b", html), "a grade letter leaked into the digest prose"
    # and the disclaimer states no grade is computed
    assert "pas encore not" in html.lower()


def test_validate_requires_provenance_and_facts():
    no_prov = _candidate(); no_prov.pop("provenance")
    assert any("provenance" in p for p in D.validate_candidate(no_prov))
    no_facts = _candidate(facts=[])
    assert any("facts" in p for p in D.validate_candidate(no_facts))


# --- invariant (b): publishable:false is banner + excluded from render -------------------------

def test_lead_shows_non_publishable_banner():
    html = D.render_digest([_lead()], "2026-07-28")
    assert "NON PUBLIABLE" in html


def test_promote_subset_excludes_non_publishable():
    promoted = fr.promote_subset([_candidate(), _lead()])
    ids = {c["id"] for c in promoted}
    assert "fr-veille-test-1" in ids           # publishable travels
    assert "fr-veille-lead-1" not in ids       # commercial lead never reaches the render path


def test_promote_subset_is_the_signed_shape_and_carries_provenance():
    promoted = fr.promote_subset([_candidate()])
    assert len(promoted) == 1
    p = promoted[0]
    assert set(p) <= set(fr.PROMOTE_FIELDS)
    assert "provenance" in p and p["provenance"]["publishable"] is True
    # digest-only blocks never travel to render
    assert "detection" not in p and "tier1_preview" not in p


def test_state_must_be_en_veille():
    assert any("en_veille" in p for p in D.validate_candidate(_candidate(state="armored")))
