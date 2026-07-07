# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the voie-A governance pipeline's pure logic (no network).

The collectors' network paths are exercised by hand against live sources (see press/RECON.md);
here we pin the deterministic parsing/matching that must never drift, and the anti-fabrication
contract — including that nothing here ever emits a score or a complete scored T1. Fixtures use
invented communes (never a real project), matching the repo's fictional-fixture convention.
"""

import csv
import io

import pytest

from pipelines.press import sources
from pipelines.press.collect import collect, _DETERMINISTIC, _NEEDS_REVIEW


# --- normalization / matching ----------------------------------------------------------------

def test_norm_folds_accents_and_case():
    assert sources._norm("Villetest") == "villetest"
    assert sources._norm("données") == "donnees"
    assert sources._norm("  Île-de-France  ") == "ile-de-france"


def test_word_in_is_whole_word_not_substring():
    hay = sources._norm("projet a Villetest (77)")
    assert sources._word_in("villetest", hay)
    # substring must not match: 'test' is inside 'villetest' but not a whole word
    assert not sources._word_in("test", hay)
    # a commune name that is a prefix of another word must not false-match
    assert not sources._word_in("ville", hay)


# --- CNDP referral (deterministic, from a CSV fixture) ---------------------------------------

_CNDP_FIXTURE = (
    "Nom du projet/plan/programme;Décision CNDP sur saisine;Année décision CNDP;"
    "Type (projet/plan);Page web sur site CNDP;Etat de la procédure\n"
    'Projet "X" centre de données sur la commune de Villetest (77);'
    "concertation préalable (saisine L.121-17);2025;projet;https://debatpublic.fr/fiche-villetest;terminée\n"
    "Projet DATA CENTERS (91);concertation préalable (saisine L.121-17);2021;projet;non disponible;arrêtée\n"
    "Projet routier ailleurs (12);pas de procédure;2019;projet;non disponible;terminée\n"
)


@pytest.fixture
def cndp_rows(monkeypatch):
    rows = list(csv.DictReader(io.StringIO(_CNDP_FIXTURE), delimiter=";"))
    monkeypatch.setattr(sources, "_load_cndp_rows", lambda: rows)
    return rows


def test_cndp_referral_true_on_commune_name_hit(cndp_rows):
    r = sources.collect_cndp("Villetest", "77", "2026-07-07")
    assert r["cndp_referral"] is True
    assert "L.121-17" in r["decision_type"]
    assert r["decision_year"] == "2025"
    assert r["seized_no_procedure"] is False
    assert r["source"]["url"] == "https://debatpublic.fr/fiche-villetest"


def test_cndp_referral_false_without_commune_hit_but_surfaces_dept_candidate(cndp_rows):
    # Bourgville is in dept 91; there is a dept-91 data-center row but it doesn't name the commune.
    r = sources.collect_cndp("Bourgville", "91", "2026-07-07")
    assert r["cndp_referral"] is False                      # not proven → not fabricated
    assert "Projet DATA CENTERS (91)" in r["other_dept_candidates"]  # but handed to the reviewer


def test_cndp_no_procedure_flag(monkeypatch):
    # A commune whose only entry is 'saisine irrecevable' is still a referral, but flagged.
    rows = list(csv.DictReader(io.StringIO(
        "Nom du projet/plan/programme;Décision CNDP sur saisine;Année décision CNDP;"
        "Type (projet/plan);Page web sur site CNDP;Etat de la procédure\n"
        "Projet centre de données a Testburg (99);saisine irrecevable;2024;projet;x;close\n"),
        delimiter=";"))
    monkeypatch.setattr(sources, "_load_cndp_rows", lambda: rows)
    r = sources.collect_cndp("Testburg", "99", "2026-07-07")
    assert r["cndp_referral"] is True
    assert r["seized_no_procedure"] is True


def test_cndp_none_when_register_unreachable(monkeypatch):
    def boom():
        raise sources.SourceUnavailable("cache down")
    monkeypatch.setattr(sources, "_load_cndp_rows", boom)
    assert sources.collect_cndp("Villetest", "77", "2026-07-07") is None


# --- judged appeals (deterministic parse of the court API shape) -----------------------------

# The API only returns metadata (no full text); the server has already text-matched the term, so
# the collector trusts the hits and just deduplicates by dossier — reported as a provisional bound.
_JA_RESPONSE = {"decisions": {"body": {"hits": {"hits": [
    {"_source": {"Numero_Dossier": "2400001", "Date_Lecture": "2025-07-31",
                 "Nom_Juridiction": "Tribunal Administratif de VILLETEST"}},
    {"_source": {"Numero_Dossier": "2400002", "Date_Lecture": "2025-07-31",
                 "Nom_Juridiction": "Tribunal Administratif de VILLETEST"}},
    {"_source": {"Numero_Dossier": "2400002", "Date_Lecture": "2025-07-31",
                 "Nom_Juridiction": "Tribunal Administratif de VILLETEST"}},   # dup → deduped
]}}}}


def test_appeals_counts_distinct_dossiers_as_provisional_bound(monkeypatch):
    monkeypatch.setattr(sources, "get_json", lambda url, params=None: _JA_RESPONSE)
    r = sources.collect_appeals_judged("Villetest", "77", "2026-07-07")
    assert r["legal_appeals_count"] == 2            # 2400001 + 2400002, duplicate deduped
    assert {d["number"] for d in r["dossiers"]} == {"2400001", "2400002"}
    assert r["basis"] == "provisional_upper_bound"
    assert r["scope"] == "judged_only"


def test_search_term_picks_distinctive_token():
    assert sources._search_term("Villetest") == "Villetest"
    assert sources._search_term("Le Val-sur-Testin") == "Testin"   # skips le/sur stopwords, longest
    assert sources._search_term("Saint-Zephyr") == "Zephyr"        # skips 'saint'


def test_appeals_none_when_court_unreachable(monkeypatch):
    def boom(url, params=None):
        raise sources.SourceUnavailable("TA API down")
    monkeypatch.setattr(sources, "get_json", boom)
    assert sources.collect_appeals_judged("Villetest", "77", "2026-07-07") is None


def test_ta_code_guess():
    assert sources._ta_code("77") == "TA77"
    assert sources._ta_code("67") == "TA67"
    assert sources._ta_code(None) is None


# --- sidecar assembly: the anti-fabrication contract -----------------------------------------

def test_sidecar_never_emits_a_scored_or_complete_t1(monkeypatch):
    # Stub the backbone + collectors so no network is touched.
    monkeypatch.setattr("pipelines.press.collect.spatial.fetch_commune",
                        lambda lat, lon: {"nom": "Villetest", "code": "77000", "codeDepartement": "77"})
    monkeypatch.setattr(sources, "collect_cndp",
                        lambda *a, **k: {"cndp_referral": True, "decision_type": "débat public",
                                         "source": {"title": "t", "url": "u", "accessed": "d"}})
    monkeypatch.setattr(sources, "collect_appeals_judged",
                        lambda *a, **k: {"legal_appeals_count": 2, "dossiers": [], "court": "TA",
                                         "scope": "judged_only",
                                         "source": {"title": "t", "url": "u", "accessed": "d"}})
    monkeypatch.setattr(sources, "gather_leads", lambda *a, **k: {"mrae_search": "u"})

    sc = collect(48.5, 2.5, name="X", accessed="2026-07-07", archive=False)
    proxies = sc["proposed_t1_proxies"]
    # Deterministic proxies present…
    assert proxies["cndp_referral"] is True
    assert proxies["legal_appeals_count"] == 2
    # …but the judgment proxies stay null (never fabricated) → T1 can't be complete/scored here.
    assert all(proxies[k] is None for k in _NEEDS_REVIEW)
    assert sc["review_required"] is True
    assert "proposed_t1_proxies" in sc and "score" not in sc  # a proposal, not a score
    # No grade/letter anywhere in the sidecar.
    assert "grade" not in __import__("json").dumps(sc).lower()


# --- archived_url (A-20): durable snapshot of the CNDP fiche ----------------------------------

def test_archive_url_prefers_fresh_capture_then_falls_back(monkeypatch):
    from pipelines.press import archive
    # Fresh capture available → used directly.
    monkeypatch.setattr(archive, "_save_now", lambda url, timeout: "https://web.archive.org/web/1/" + url)
    monkeypatch.setattr(archive, "_closest_snapshot", lambda url, timeout: "https://web.archive.org/web/OLD/" + url)
    assert archive.archive_url("https://x.test/fiche") == "https://web.archive.org/web/1/https://x.test/fiche"
    # No fresh capture → fall back to the closest existing snapshot.
    monkeypatch.setattr(archive, "_save_now", lambda url, timeout: None)
    assert archive.archive_url("https://x.test/fiche") == "https://web.archive.org/web/OLD/https://x.test/fiche"
    # Neither → None, and never raises.
    monkeypatch.setattr(archive, "_closest_snapshot", lambda url, timeout: None)
    assert archive.archive_url("https://x.test/fiche") is None
    assert archive.archive_url(None) is None


def test_archive_helpers_swallow_network_errors(monkeypatch):
    from pipelines.press import archive
    def boom(url, timeout):
        raise OSError("network down")
    monkeypatch.setattr(archive, "_open", boom)
    # Both helpers must degrade to None rather than propagate — an archive failure never blocks.
    assert archive._save_now("https://x.test", 5) is None
    assert archive._closest_snapshot("https://x.test", 5) is None


def test_collect_writes_archived_url_on_cndp_fiche_when_referral(monkeypatch):
    monkeypatch.setattr("pipelines.press.collect.spatial.fetch_commune",
                        lambda lat, lon: {"nom": "Villetest", "code": "77000", "codeDepartement": "77"})
    monkeypatch.setattr(sources, "collect_cndp",
                        lambda *a, **k: {"cndp_referral": True, "decision_type": "débat public",
                                         "source": {"title": "t", "url": "https://debatpublic.fr/f",
                                                    "accessed": "d"}})
    monkeypatch.setattr(sources, "collect_appeals_judged", lambda *a, **k: None)
    monkeypatch.setattr(sources, "gather_leads", lambda *a, **k: {})
    monkeypatch.setattr("pipelines.press.collect.archive_url",
                        lambda url: "https://web.archive.org/web/20260707/" + url)

    sc = collect(48.5, 2.5, name="X", accessed="2026-07-07", archive=True)
    src = sc["deterministic_sources"]["cndp_referral"]["source"]
    assert src["archived_url"] == "https://web.archive.org/web/20260707/https://debatpublic.fr/f"


def test_collect_skips_archive_when_disabled_or_no_referral(monkeypatch):
    monkeypatch.setattr("pipelines.press.collect.spatial.fetch_commune",
                        lambda lat, lon: {"nom": "Villetest", "code": "77000", "codeDepartement": "77"})
    monkeypatch.setattr(sources, "collect_cndp",
                        lambda *a, **k: {"cndp_referral": False, "decision_type": None,
                                         "source": {"title": "t", "url": "https://data.gouv.fr/x",
                                                    "accessed": "d"}})
    monkeypatch.setattr(sources, "collect_appeals_judged", lambda *a, **k: None)
    monkeypatch.setattr(sources, "gather_leads", lambda *a, **k: {})
    # archive_url must not even be called when there is no referral; make it explode if it is.
    monkeypatch.setattr("pipelines.press.collect.archive_url",
                        lambda url: (_ for _ in ()).throw(AssertionError("should not archive")))
    sc = collect(48.5, 2.5, name="X", accessed="2026-07-07", archive=True)
    assert "archived_url" not in sc["deterministic_sources"]["cndp_referral"]["source"]
