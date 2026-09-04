# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Offline tests for the actu producer (no network — a stub LLM returns canned classifications).

Pins the deterministic guardrails around the model call: off-topic is DROPPED, the summary is OUR
words within a hard cap (never the headline verbatim — A-20), and the DEPLOYED latest.json is the
HUMAN-GATE lock (`approved:true` only, set by promote(), never by the model).
"""

import json

from pipelines.veille import actu


def _rec(title, url="https://ex.org/a", lang="French"):
    return {"name": title, "sources": [url], "source_url": url, "retrieved": "2026-09-04",
            "facts": {"domain": "ex.org", "language": lang, "seendate": "20260904T000000Z"}}


def _llm(payload):
    """A stub LLM returning a fixed JSON string, ignoring the prompt."""
    return lambda _prompt: json.dumps(payload)


def test_offtopic_is_dropped():
    llm = _llm({"relevant": False, "topic": "marche", "is_project": False, "lang": "en",
                "summary": "x", "entities": {}})
    assert actu.classify(_rec("IMF sees global economy resilient"), llm) is None


def test_summary_copy_of_headline_refused():
    title = "Microsoft obtient un feu vert pour son datacenter"
    llm = _llm({"relevant": True, "topic": "projet", "is_project": True, "lang": "fr",
                "summary_fr": title, "summary_en": "x", "entities": {"operator": "Microsoft"}})
    assert actu.classify(_rec(title), llm) is None      # native (fr) summary == headline → A-20 refusal


def test_summary_capped_at_30_words():
    long = " ".join(["mot"] * 50)
    llm = _llm({"relevant": True, "topic": "debat", "is_project": False, "lang": "fr",
                "summary_fr": long, "summary_en": long, "entities": {}})
    item = actu.classify(_rec("Un titre distinct du résumé"), llm)
    assert item is not None
    assert len(item["summary_i18n"]["fr"].split()) <= actu._MAXW + 1   # +1 for the trailing ellipsis token
    assert len(item["summary_i18n"]["en"].split()) <= actu._MAXW + 1


def test_valid_item_shape_and_i18n():
    llm = _llm({"relevant": True, "topic": "projet", "is_project": True, "lang": "en",
                "headline_fr": "Feu vert pour le datacenter Microsoft dans le Haut-Rhin",
                "headline_en": "Microsoft data center gets green light in Haut-Rhin",
                "summary_fr": "Microsoft obtient une autorisation pour un centre de données dans le Haut-Rhin.",
                "summary_en": "Microsoft secures a permit for a data center in the Haut-Rhin.",
                "entities": {"operator": "Microsoft", "location": "Haut-Rhin", "act": "permis"}})
    item = actu.classify(_rec("Microsoft data center gets green light in Haut-Rhin", lang="English"), llm)
    assert item["topic"] == "projet"
    assert item["publishable"] is True and item["approved"] is False
    assert item["lang"] == "en"                                  # REAL source language
    assert item["headline"] == "Microsoft data center gets green light in Haut-Rhin"  # VO verbatim
    assert item["headline_i18n"]["en"] == item["headline"]       # original in its own lang
    assert "datacenter" in item["headline_i18n"]["fr"].lower()   # the other lang = AI translation
    assert set(item["summary_i18n"]) == {"fr", "en"}             # our summary in BOTH languages
    assert item["summary"] == item["summary_i18n"]["en"]         # back-compat = native-language summary


def test_unknown_topic_falls_back():
    llm = _llm({"relevant": True, "topic": "n_importe_quoi", "is_project": False, "lang": "fr",
                "summary_fr": "Un résumé neutre distinct du titre source.",
                "summary_en": "A neutral summary distinct from the source title.", "entities": {}})
    item = actu.classify(_rec("Titre"), llm)
    assert item["topic"] in actu.TOPICS         # coerced into the signed enum


def test_public_latest_excludes_unapproved():
    items = [{"id": "a", "approved": True}, {"id": "b", "approved": False}, {"id": "c"}]
    out = actu._public_latest(items)
    assert [i["id"] for i in out["items"]] == ["a"]     # only approved:true travels to the deployed file


_CORPUS = [
    {"id": "fr-microsoft", "operator": "Microsoft", "municipality": "Petit-Landau"},
    {"id": "fr-segro", "operator": "Segro", "municipality": "Le Bourget"},
    {"id": "fr-segro-marseille", "operator": "Segro", "municipality": "Marseille"},
]


def test_linked_dc_single_operator_match():
    item = {"headline": "Microsoft Haut-Rhin feu vert", "entities": {"operator": "Microsoft", "location": "Haut-Rhin"}}
    assert actu.link_to_corpus(item, _CORPUS) == {"id": "fr-microsoft"}


def test_linked_dc_disambiguates_by_location():
    item = {"headline": "Segro à Marseille", "entities": {"operator": "Segro", "location": "Marseille"}}
    assert actu.link_to_corpus(item, _CORPUS) == {"id": "fr-segro-marseille"}


def test_linked_dc_ambiguous_returns_none():
    # Two Segro sites, location too vague to disambiguate → never guess a wrong fiche
    item = {"headline": "Segro coentreprise Pure DC", "entities": {"operator": "Segro", "location": "France"}}
    assert actu.link_to_corpus(item, _CORPUS) is None


def test_linked_dc_no_match_returns_none():
    item = {"headline": "Un opérateur inconnu ouvre un site", "entities": {"operator": "Zzz Corp", "location": "Lyon"}}
    assert actu.link_to_corpus(item, _CORPUS) is None


def test_linked_dc_carries_no_grade():
    item = {"headline": "Microsoft", "entities": {"operator": "Microsoft"}}
    link = actu.link_to_corpus(item, _CORPUS)
    assert set(link) == {"id"}          # only the id travels — never a grade/score into the actu card


_ALLOW = {"lemonde.fr", "reuters.com"}


def _gitem(**over):
    it = {"topic": "marche", "publishable": True, "source": {"publisher": "lemonde.fr"},
          "_gate": {"confidence": "high", "person_named": False}}
    it.update(over)
    return it


def test_gate_green_all_conditions():
    assert actu.gate(_gitem(), _ALLOW) is True


def test_gate_red_project_topic():
    assert actu.gate(_gitem(topic="projet"), _ALLOW) is False   # a project → human eye mandatory


def test_gate_red_named_person():
    assert actu.gate(_gitem(_gate={"confidence": "high", "person_named": True}), _ALLOW) is False


def test_gate_red_low_confidence():
    assert actu.gate(_gitem(_gate={"confidence": "medium", "person_named": False}), _ALLOW) is False


def test_gate_red_source_not_allowlisted():
    assert actu.gate(_gitem(source={"publisher": "randomblog.example"}), _ALLOW) is False


def test_gate_red_activism_and_debate():
    assert actu.gate(_gitem(topic="activisme"), _ALLOW) is False
    assert actu.gate(_gitem(topic="debat"), _ALLOW) is False
    assert actu.gate(_gitem(topic="moratoire"), _ALLOW) is False   # sensitive → not green


def test_domain_ok_handles_www_and_subdomain():
    assert actu._domain_ok("www.lemonde.fr", _ALLOW) is True
    assert actu._domain_ok("live.reuters.com", _ALLOW) is True
    assert actu._domain_ok("notlemonde.fr", _ALLOW) is False


def test_allowlist_loads_and_excludes_dcmag():
    dom = actu.load_allowlist()
    assert "lemonde.fr" in dom and "reuters.com" in dom
    assert not any("dcmag" in d or "datacenter-magazine" in d for d in dom)   # commercial, excluded


def _recent():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def test_actu_latest_approved_windowed_and_stripped(tmp_path):
    nr, pub = tmp_path / "newsroom", tmp_path / "public"
    d = nr / "actu" / "2026-09-04"; d.mkdir(parents=True)
    items = [
        {"id": "g", "approved": True, "topic": "marche", "source": {"published_at": _recent()}, "_gate": {"confidence": "high"}},
        {"id": "r", "approved": False, "topic": "debat", "source": {"published_at": _recent()}},
        {"id": "old", "approved": True, "topic": "marche", "source": {"published_at": "20200101T000000Z"}},
    ]
    (d / "actu.json").write_text(json.dumps({"items": items}))
    actu.actu_latest(nr, pub, days=14)
    latest = json.loads((pub / "actu" / "latest.json").read_text())
    assert [i["id"] for i in latest["items"]] == ["g"]   # approved+fresh only (r unapproved, old out of window)
    assert "_gate" not in latest["items"][0]             # transient signal never public


def test_promote_persists_approval_to_archive(tmp_path):
    nr, pub, date = tmp_path / "newsroom", tmp_path / "public", "2026-09-04"
    d = nr / "actu" / date; d.mkdir(parents=True)
    (d / "actu.json").write_text(json.dumps({"items": [
        {"id": "keep", "topic": "projet", "publishable": True, "approved": False, "source": {"published_at": _recent()}},
        {"id": "skip", "topic": "news", "publishable": True, "approved": False, "source": {"published_at": _recent()}},
    ]}))
    actu.promote(["keep"], newsroom_root=nr, public_data=pub, date=date)
    arch = {i["id"]: i for i in json.loads((d / "actu.json").read_text())["items"]}
    assert arch["keep"]["approved"] is True and arch["skip"]["approved"] is False   # persisted in the archive
    latest = json.loads((pub / "actu" / "latest.json").read_text())["items"]
    assert [i["id"] for i in latest] == ["keep"]         # regenerated approved-only from the archive


def test_promote_sets_approved_and_writes_latest(tmp_path):
    date = "2026-09-04"
    nr = tmp_path / "newsroom"
    (nr / "actu" / date).mkdir(parents=True)
    archive = {"date": date, "items": [
        {"id": "keep", "topic": "projet", "publishable": True, "approved": False},
        {"id": "skip", "topic": "news", "publishable": True, "approved": False},
    ]}
    (nr / "actu" / date / "actu.json").write_text(json.dumps(archive))
    pub = tmp_path / "public"
    res = actu.promote(["keep"], newsroom_root=nr, public_data=pub, date=date)
    latest = json.loads((pub / "actu" / "latest.json").read_text())
    ids = {i["id"]: i for i in latest["items"]}
    assert "keep" in ids and ids["keep"]["approved"] is True   # approved by the gate
    assert "skip" not in ids                                   # never approved → never public
    assert res["public_total"] == 1
