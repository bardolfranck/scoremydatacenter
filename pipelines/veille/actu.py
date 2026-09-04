# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Actu producer — GDELT harvest → Sonnet classifier → `actu.json` (news + project leads).

The "B-LLM" lane (Franck 2026-07-28): GDELT is a better NEWSLETTER engine than a project detector,
so we run every harvested headline through the model ONCE to split news / project / noise, extract
operator+location, and write OUR neutral summary. Two products from one harvest:
  • NEWS  → the site's "Actu"(FR)/"News"(EN) press-review section.
  • PROJET → the veille lane (geocode → dedup → onboard/score).

    uv run python -m pipelines.veille.actu --newsroom ../smdc-newsroom [--timespan 1m --limit 40]

TWO-LOCK anti-leak (agreed with agent-codeur-site), on TWO fields with DISTINCT meanings:
  • `publishable` = LICENCE level (classifier): the source is open/attributable → publishable.
    Same meaning as veille/provenance.publishable. A commercial-only source would be false.
  • `approved`    = HUMAN GATE: Franck approved it in the chat. Set by `promote()`, NEVER the model.
Deposits:
  • `newsroom/actu/<date>/actu.json`  — PRIVATE, ALL relevant items (pending/rejected included).
  • `site/public/data/actu/latest.json` — DEPLOYED, ONLY `approved:true` items (lock 1, at the DATA
    level — a hidden item is still scrapable from baked JSON, so the gate is on the data, not the
    page). Always emitted, even empty `{"items":[]}`, so the site's build-time import never breaks.

A-20 / copyright: `summary` is OUR neutral, abstractive words (≤30), NEVER the article text; the
verbatim `headline` is the link label + attribution. No grade/score ANYWHERE (en-veille doctrine).
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from ..press import signal
from .fr import operators_in, load_corpus, _norm

TOPICS = {"projet", "debat", "activisme", "souverainete", "moratoire", "reglementation", "marche"}
_MAXW = 30  # summary hard cap (words)

_PROMPT = """Tu es l'assistant de veille d'un observatoire INDÉPENDANT des data centers. On te donne un
TITRE de presse (+ domaine, langue). Tu réponds UNIQUEMENT par un objet JSON, rien autour.

Titre : {title}
Domaine : {domain}   Langue probable : {lang}

Renvoie :
{{
 "relevant": true|false,        // PARLE-T-IL d'un data center (projet, débat, régulation, opposition,
                                //   marché) ? false si HORS-SUJET (éco générale, fusion sans lien DC…).
 "topic": "projet|debat|activisme|souverainete|moratoire|reglementation|marche",
 "is_project": true|false,      // un PROJET concret (site + opérateur + acte : permis, chantier,
                                //   inauguration, investissement) ? sinon c'est de la news de secteur.
 "lang": "fr"|"en",
 "summary": "<TON résumé neutre, factuel, ≤30 mots, DANS TES MOTS — jamais une copie du titre ni de
             l'article. Zéro militantisme : « opposition citoyenne signalée à X », jamais « scandale ».>",
 "entities": {{"operator": "<si identifiable, sinon null>", "location": "<commune/région FR si citée, sinon null>", "act": "<permis|chantier|inauguration|investissement|annonce|null>"}},
 "person_named": true|false,    // une PERSONNE PHYSIQUE nommée (élu, militant, dirigeant…) ? (risque diffamation)
 "confidence": "high|medium|low" // ta confiance dans CE classement (topic + pertinence)
}}
RÈGLES : neutralité absolue (on mesure, on ne milite pas). Résumé abstractif, jamais d'extraction.
Si non pertinent, relevant=false (le reste peut être approximatif). JSON valide STRICT."""


def _slug(url: str, title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (title or "").lower())[:48].strip("-") or "actu"
    tail = re.sub(r"[^a-z0-9]", "", (url or "").lower())[-6:] or "000000"
    return f"fr-actu-{base}-{tail}".strip("-")


def _parse(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?|\n?```$", "", raw).strip()
    return json.loads(raw)


def classify(record: dict, llm) -> dict | None:
    """One GDELT record → one actu item, or None if the model judges it off-topic (noise dropped).

    `publishable` (licence) is set here; `approved` (human gate) is NOT — it defaults false and is
    only ever set true by promote() after Franck's approval.
    """
    title = (record.get("name") or "").strip()
    url = (record.get("sources") or [None])[0] or record.get("source_url")
    if not title or not url:
        return None
    meta = record.get("facts") or {}
    domain = meta.get("domain") or ""
    lang_hint = (meta.get("language") or "").lower()[:2] or "fr"
    prompt = _PROMPT.format(title=title.replace("{", "(").replace("}", ")"), domain=domain, lang=lang_hint)
    try:
        got = _parse(llm(prompt))
    except Exception:
        return None                                  # a bad classify never blocks the batch
    if not got.get("relevant"):
        return None                                  # off-topic → dropped (not even archived)

    topic = got.get("topic") if got.get("topic") in TOPICS else ("projet" if got.get("is_project") else "marche")
    summary = " ".join((got.get("summary") or "").split())
    if not summary or summary.strip().lower() == title.strip().lower():
        return None                                  # empty or a copy of the headline → refuse (A-20)
    words = summary.split()
    if len(words) > _MAXW:                            # hard cap, never the article
        summary = " ".join(words[:_MAXW]).rstrip(".,;:") + "…"
    ent = got.get("entities") or {}
    return {
        "id": _slug(url, title),
        "lang": "en" if got.get("lang") == "en" else "fr",
        "topic": topic,
        "headline": title,                           # verbatim = link label + attribution
        "summary": summary,                          # OUR neutral words, ≤30
        "source": {"publisher": domain or "presse", "url": url,
                   "published_at": meta.get("seendate"), "accessed": record.get("retrieved")},
        "entities": {k: (ent.get(k) or None) for k in ("operator", "location", "act")},
        "publishable": True,                         # open press → licence OK (lock: LICENCE)
        "approved": False,                           # set by the gate: GREEN lane auto, RED lane by Franck
        # transient gating signals (stripped before persist — never public, never a "score" leak):
        "_gate": {"confidence": got.get("confidence") or "low", "person_named": bool(got.get("person_named"))},
    }


def link_to_corpus(item: dict, corpus: list[dict]) -> dict | None:
    """If the item names an operator we ALREADY score, return `{id}` of the matching fiche.

    Franck 2026-09-04: a NEWS about a project we've already assessed is a STRENGTH (« on l'a mesuré,
    voici notre fiche »), not a duplicate to hide → the actu card gets a direct link to /dc/<id>.
    NEVER a grade in the payload — the fiche page carries the letter, the news card only links to it
    (keeps the actu section note-free, same invariant as the rest of the lane). Ambiguous (several
    sites for the operator, no location tiebreak) → no link: we never guess a wrong fiche.
    """
    ent = item.get("entities") or {}
    ops = set(operators_in((ent.get("operator") or "") + " " + (item.get("headline") or "")))
    if not ops:
        return None
    cands = [d for d in corpus if set(operators_in(d.get("operator") or "")) & ops]
    if len(cands) == 1:
        return {"id": cands[0]["id"]}
    if len(cands) > 1:                                # disambiguate by location, else don't guess
        loc = _norm(ent.get("location") or "")
        if loc:
            narrowed = [d for d in cands if _norm(d.get("municipality") or "")
                        and (_norm(d["municipality"]) in loc or loc in _norm(d["municipality"]))]
            if len(narrowed) == 1:
                return {"id": narrowed[0]["id"]}
    return None


# --- the standing gate: GREEN auto-publishes, RED waits for Franck (2026-09-04) ---------------

GREEN_TOPICS = {"marche", "reglementation", "souverainete"}
_ALLOWLIST = Path(__file__).with_name("allowlist.json")


def load_allowlist() -> set[str]:
    """Trusted publisher domains (pipelines/veille/allowlist.json). Empty on any read error →
    fail CLOSED (nothing is green without a real allowlist, never fail-open to auto-publish)."""
    try:
        return {d.strip().lower() for d in json.loads(_ALLOWLIST.read_text()).get("domains", []) if d.strip()}
    except Exception:
        return set()


def _domain_ok(publisher: str, allowlist: set[str]) -> bool:
    p = (publisher or "").strip().lower()
    p = p[4:] if p.startswith("www.") else p
    return any(p == d or p.endswith("." + d) for d in allowlist)


def gate(item: dict, allowlist: set[str]) -> bool:
    """Franck's standing rule: return True (→ approved AUTO, GREEN lane) ONLY if ALL hold — an
    allowlisted source, a NEUTRAL topic (marché/réglementation/souveraineté, so never projet /
    débat / activisme / moratoire), NO named person (defamation), publishable, and HIGH confidence.
    Any miss → False (RED lane: waits for Franck's explicit OK via promote). No 'silence = publish':
    the default is RED, never flipped."""
    g = item.get("_gate") or {}
    return bool(
        item.get("publishable") is True
        and item.get("topic") in GREEN_TOPICS
        and not g.get("person_named")
        and g.get("confidence") == "high"
        and _domain_ok((item.get("source") or {}).get("publisher"), allowlist)
    )


def build(accessed: str, llm, *, timespan: str, limit: int | None) -> list[dict]:
    """Harvest GDELT-FR → classify each headline → relevant items (news + project leads)."""
    records = signal.fetch_gdelt_country("FR", accessed, timespan=timespan, maxrecords=min(limit or 50, 250))
    seen, items = set(), []
    for rec in records:
        url = (rec.get("sources") or [None])[0]
        if not url or url in seen:
            continue
        seen.add(url)
        item = classify(rec, llm)
        if item:
            items.append(item)
        if limit and len(items) >= limit:
            break
    return items


# --- the two deposits + the human gate --------------------------------------------------------

def _public_latest(items: list[dict]) -> dict:
    """The DEPLOYED payload: ONLY approved items (lock 1, data level). Always a valid object."""
    return {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "items": [i for i in items if i.get("approved") is True]}


def run(newsroom_root: Path, *, llm, public_data: Path, accessed: str | None = None,
        timespan: str = "1w", limit: int | None = None) -> dict:
    """Full pass: harvest → classify → GATE → PRIVATE archive + DEPLOYED latest.json.

    The gate (Franck 2026-09-04) sets `approved`: GREEN items (allowlisted source, neutral topic,
    no named person, not a project, high confidence) auto-publish; RED items stay approved:false in
    the archive until Franck approves them via promote(). latest.json = previously-approved ∪ today's
    GREEN — never a RED item, no 'silence = publish'. The digest becomes a SURVEILLANCE tool, not a
    mandatory passage; only the red lane needs Franck's eye.
    """
    accessed = accessed or datetime.now(timezone.utc).date().isoformat()
    items = build(accessed, llm, timespan=timespan, limit=limit)

    corpus = load_corpus(public_data)
    allowlist = load_allowlist()
    for it in items:
        # Showcase link to an already-scored fiche (Franck 2026-09-04) — a strength, not a duplicate.
        link = link_to_corpus(it, corpus)
        if link:
            it["linked_dc"] = link
        # The STANDING GATE: GREEN → approved auto; RED → stays False, waits for Franck (promote).
        it["approved"] = gate(it, allowlist)
        it.pop("_gate", None)                        # transient gating signals never persist anywhere

    day_dir = newsroom_root / "actu" / accessed
    day_dir.mkdir(parents=True, exist_ok=True)
    (day_dir / "actu.json").write_text(
        json.dumps({"date": accessed, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "items": items}, ensure_ascii=False, indent=2) + "\n")

    # Deployed latest.json = previously-approved (kept across days) ∪ today's GREEN (auto-approved).
    # RED items are archive-only until Franck approves them via promote(). Approved-only, always valid.
    latest_path = public_data / "actu" / "latest.json"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    merged = {}
    if latest_path.is_file():
        try:
            merged = {i["id"]: i for i in json.loads(latest_path.read_text()).get("items", []) if i.get("approved")}
        except Exception:
            merged = {}
    for it in items:
        if it["approved"]:
            merged[it["id"]] = it
    latest_path.write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "items": list(merged.values())},
        ensure_ascii=False, indent=2) + "\n")

    green = [i for i in items if i["approved"]]
    projects = [i for i in items if i["topic"] == "projet"]
    return {"date": accessed, "items": len(items), "green_auto_published": len(green),
            "red_pending_gate": len(items) - len(green), "projects": len(projects),
            "public_total": len(merged), "archive": str(day_dir / "actu.json")}


def promote(approved_ids: list[str], *, newsroom_root: Path, public_data: Path, date: str) -> dict:
    """THE HUMAN GATE materialised: Franck approved these ids → set approved:true, rewrite latest.json.

    Reads the day's archive, keeps the approved ids (merged with previously-approved items), and
    writes the DEPLOYED latest.json = approved-only. Nothing else can set `approved`.
    """
    archive = json.loads((newsroom_root / "actu" / date / "actu.json").read_text())["items"]
    latest_path = public_data / "actu" / "latest.json"
    kept = {i["id"]: i for i in (json.loads(latest_path.read_text()).get("items", []) if latest_path.is_file() else [])}
    for item in archive:
        if item["id"] in approved_ids and item.get("publishable"):
            kept[item["id"]] = {**item, "approved": True}
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "items": list(kept.values())}
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return {"approved_now": len(approved_ids), "public_total": len(payload["items"])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Actu producer: GDELT → Sonnet classifier → actu.json (no grade, no deploy).")
    ap.add_argument("--newsroom", type=Path, default=Path("../smdc-newsroom"))
    ap.add_argument("--public-data", type=Path, default=Path("site/public/data"))
    ap.add_argument("--timespan", default="1w")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--date", default=None)
    args = ap.parse_args(argv)
    from ..llm_client import anthropic_llm
    result = run(args.newsroom, llm=anthropic_llm(), public_data=args.public_data,
                 accessed=args.date, timespan=args.timespan, limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
