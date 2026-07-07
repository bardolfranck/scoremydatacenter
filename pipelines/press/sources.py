# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Voie-A governance collectors — official procedural facts behind T1/T2.

Two kinds of output, kept strictly apart:

  * DETERMINISTIC proxies read from official structured sources — CNDP referral (the national
    "Saisines de la CNDP" register) and judged administrative appeals (the administrative-court
    open data). These come back as sourced values a reviewer can trust on sight.

  * REVIEW LEADS — the exact URLs/PDFs a human (or the iter-1 LLM stage) must open to establish
    the proxies that need judgment: the environmental-authority opinion's tenor, the public
    inquiry's conclusion, the council's stance. "The press points, the registry proves": we never
    infer a tenor here; we hand over the primary document.

No collector returns a score, a note, or a verdict. Anything unreachable degrades to None — the
pipeline proposes, never fabricates. Reuses the spatial pipeline's stdlib HTTP + cache bricks.
"""

import csv
import re
import unicodedata

from pipelines.spatial.http import SourceUnavailable, get_json, get_text
from pipelines.spatial.cache import cached_path

_DATACENTER_KEYWORDS = ("data center", "datacenter", "data centers", "datacenters",
                        "centre de donnees", "centres de donnees")


def _norm(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace — for accent-insensitive token matching."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def _word_in(word: str, haystack: str) -> bool:
    """True if `word` (already normalized) appears as a whole word in normalized `haystack`."""
    if not word:
        return False
    return re.search(rf"\b{re.escape(word)}\b", haystack) is not None


def _source(title: str, url: str, accessed: str) -> dict:
    return {"title": title, "url": url, "accessed": accessed}


# --- CNDP referral (national "Saisines de la CNDP" register, cached CSV) ---------------------

_CNDP_DATASET = "https://www.data.gouv.fr/api/1/datasets/saisines-de-la-cndp/"
# Pinned fallback if the dataset API is unreachable — the pipeline still runs from the last CSV.
_CNDP_CSV_FALLBACK = ("https://static.data.gouv.fr/resources/saisines-de-la-cndp/"
                      "20260304-104039/saisines-cndp-au-4-mars-2026.csv")
_CNDP_NAME_COL = "Nom du projet/plan/programme"
_CNDP_DECISION_COL = "Décision CNDP sur saisine"
_CNDP_YEAR_COL = "Année décision CNDP"
_CNDP_PAGE_COL = "Page web sur site CNDP"
# Decisions that mean "seized but no public procedure took place" — a referral still occurred.
_CNDP_NO_PROCEDURE = ("pas de procedure", "saisine irrecevable", "irrecevable", "rejet")


def _resolve_cndp_csv_url() -> str:
    """Latest CSV resource URL from the data.gouv dataset (falls back to the pinned snapshot)."""
    try:
        data = get_json(_CNDP_DATASET)
        csvs = [r for r in data.get("resources", [])
                if (r.get("format") or "").lower() == "csv"
                or (r.get("url") or "").lower().endswith(".csv")]
        if csvs:  # the dataset carries one CSV + a description PDF; take the CSV
            return csvs[0]["url"]
    except (SourceUnavailable, KeyError, IndexError):
        pass
    return _CNDP_CSV_FALLBACK


def _load_cndp_rows() -> list[dict]:
    """The saisines register as a list of dict rows (cp1252, ';'-delimited). Cached once."""
    path = cached_path(_resolve_cndp_csv_url(), "cndp_saisines.csv")
    # The register is Windows-1252 with a ';' separator (verified in RECON).
    text = path.read_text(encoding="cp1252", errors="replace")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))


def collect_cndp(commune_name: str, dept: str | None, accessed: str) -> dict | None:
    """Deterministic `cndp_referral` from the saisines register.

    Match is by commune name as a whole word in the project label (the register embeds the
    commune in the free-text name). Returns the proxy value, the decision type/year, the CNDP
    fiche URL, plus any dept-level data-center candidates for the reviewer to disambiguate.
    None only if the register itself could not be loaded.
    """
    try:
        rows = _load_cndp_rows()
    except SourceUnavailable:
        return None

    target = _norm(commune_name)
    dept_tag = f"({dept})" if dept else None
    matches, dept_candidates = [], []
    for row in rows:
        label = row.get(_CNDP_NAME_COL) or ""
        norm_label = _norm(label)
        is_dc = any(k in norm_label for k in _DATACENTER_KEYWORDS)
        if _word_in(target, norm_label):
            matches.append(row)
        elif dept_tag and dept_tag in norm_label and is_dc:
            # Same département + a data-center project, but no commune-name hit → a lead, not proof.
            dept_candidates.append(label.strip())

    if matches:
        # A commune-name hit in the saisines register = the project was referred to the CNDP.
        row = matches[0]
        decision = (row.get(_CNDP_DECISION_COL) or "").strip()
        year = (row.get(_CNDP_YEAR_COL) or "").strip()
        page = (row.get(_CNDP_PAGE_COL) or "").strip()
        no_procedure = any(k in _norm(decision) for k in _CNDP_NO_PROCEDURE)
        return {
            "cndp_referral": True,
            "decision_type": decision or None,
            "decision_year": year or None,
            "seized_no_procedure": no_procedure,
            "source": _source(
                f"CNDP — Saisines register: '{(row.get(_CNDP_NAME_COL) or '').strip()}' "
                f"→ {decision or 'referral recorded'} ({year or 'n/d'})",
                page or "https://www.data.gouv.fr/datasets/saisines-de-la-cndp/",
                accessed),
            "other_dept_candidates": dept_candidates,
        }
    # No commune-name hit. The CSV is punctual (~2 snapshots/yr), so absence is NOT proof of
    # "no referral" for a recent project — the reviewer confirms via the debatpublic.fr overlay.
    return {
        "cndp_referral": False,
        "decision_type": None,
        "decision_year": None,
        "seized_no_procedure": False,
        "source": _source(
            f"CNDP — Saisines register: no entry naming commune '{commune_name}' "
            f"(punctual dataset; confirm recent projects via the debatpublic.fr overlay)",
            "https://www.data.gouv.fr/datasets/saisines-de-la-cndp/",
            accessed),
        "other_dept_candidates": dept_candidates,
    }


# --- Judged administrative appeals (administrative-court open data, hidden search API) --------

_JA_API = "https://opendata.justice-administrative.fr/recherche/api/model_search_juri/openData"


def _ta_code(dept: str | None) -> str | None:
    """Best-effort tribunal-administratif code from a département number.

    The competent TA usually sits in the department itself (verified: TA77=Melun, TA67=Strasbourg),
    so TA{dept} is the right guess for the common case. Departments whose litigation is heard by a
    TA seated elsewhere are the exception — the search URL is always emitted as a lead so the
    reviewer can re-query the right court. Provisional by construction.
    """
    if not dept:
        return None
    return f"TA{dept.strip()}"


_TERM_STOPWORDS = {"le", "la", "les", "de", "du", "des", "sur", "sous", "en", "aux", "au",
                   "saint", "sainte", "st", "ste"}


def _search_term(commune_name: str) -> str:
    """The most distinctive token of a commune name for the court full-text search.

    The API path takes one term and OR-matches; a distinctive token (longest non-stopword) keeps
    the query precise for names like 'Le Mée-sur-Seine' while staying a single path segment.
    """
    tokens = [t for t in re.split(r"[\s-]+", commune_name.strip()) if t]
    meaningful = [t for t in tokens if _norm(t) not in _TERM_STOPWORDS and len(t) >= 3]
    pool = meaningful or tokens
    return max(pool, key=len) if pool else commune_name


def collect_appeals_judged(commune_name: str, dept: str | None, accessed: str) -> dict | None:
    """`legal_appeals_count` over JUDGED cases at the competent TA — a PROVISIONAL upper bound.

    The court search matches the commune term in the full decision text server-side; the API then
    returns only metadata (dossier number, date, court), so the count cannot be tightened further
    here — it is a provisional upper bound, deduplicated by dossier, with the full dossier list for
    the reviewer to confirm relevance AND direction (developer-vs-commune ≠ opponents-vs-project).
    Judged cases only — a filed-but-unjudged appeal is a separate review lead (press → R.600-7).
    Returns None if the court API could not be reached.
    """
    ta = _ta_code(dept)
    if not ta:
        return None
    term = _search_term(commune_name)
    url = f"{_JA_API}/{ta}/{term}/200"
    try:
        data = get_json(url)
    except SourceUnavailable:
        return None
    try:
        hits = data["decisions"]["body"]["hits"]["hits"]
    except (KeyError, TypeError):
        hits = []

    dossiers = {}
    court = ta
    for h in hits:
        src = h.get("_source") or {}
        court = src.get("Nom_Juridiction") or court
        num = src.get("Numero_Dossier")
        if num and num not in dossiers:  # server already text-matched the term; just dedup
            dossiers[num] = src.get("Date_Lecture")
    return {
        "legal_appeals_count": len(dossiers),
        "basis": "provisional_upper_bound",
        "dossiers": [{"number": n, "date": d} for n, d in dossiers.items()],
        "court": court,
        "scope": "judged_only",
        "source": _source(
            f"Administrative-court open data — {court}: {len(dossiers)} judged decision(s) "
            f"matching '{term}' (provisional upper bound; judged only; verify relevance and "
            f"appeal direction — see caveats)",
            f"https://opendata.justice-administrative.fr/#/recherche/{ta}/{term}",
            accessed),
    }


# --- Review leads — the primary documents the human/LLM stage must open ----------------------

def _department_slug(dept: str | None) -> str | None:
    """Département number → name slug for the prefecture site (77 → 'seine-et-marne')."""
    if not dept:
        return None
    try:
        d = get_json(f"https://geo.api.gouv.fr/departements/{dept}", {"fields": "nom"})
    except SourceUnavailable:
        return None
    name = _norm(d.get("nom") or "") if isinstance(d, dict) else ""
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-") or None


def _town_hall_site(insee: str | None) -> str | None:
    """Commune INSEE → official town-hall website via the service-public directory API."""
    if not insee:
        return None
    url = ("https://api-lannuaire.service-public.fr/api/explore/v2.1/catalog/datasets/"
           "api-lannuaire-administration/records")
    where = f'pivot like "mairie" and code_insee_commune="{insee}"'
    try:
        res = get_json(url, {"where": where, "limit": 1})
    except SourceUnavailable:
        return None
    recs = res.get("results") or res.get("records") or []
    if not recs:
        return None
    rec = recs[0].get("record", {}).get("fields", recs[0]) if "record" in recs[0] else recs[0]
    site = rec.get("site_internet") or rec.get("site")
    if isinstance(site, list) and site:
        site = site[0].get("valeur") if isinstance(site[0], dict) else site[0]
    if isinstance(site, str):
        try:
            return __import__("json").loads(site)[0]["valeur"] if site.startswith("[") else site
        except Exception:
            return site
    return None


def gather_leads(commune_name: str, insee: str | None, dept: str | None,
                 cndp: dict | None) -> dict:
    """URLs the reviewer/LLM opens to establish the judgment-bearing proxies + T2."""
    from urllib.parse import quote_plus
    q = quote_plus(commune_name)
    dept_slug = _department_slug(dept)
    leads = {
        # environmental_authority_opinion — read the MRAe avis PDF, extract tenor (do NOT infer here)
        "mrae_search": ("https://www.mrae.developpement-durable.gouv.fr/spip.php?"
                        f"page=recherche&recherche={q}"),
        # public_inquiry_held (+ commissaire-enquêteur conclusion) — sweep participation sections
        "prefecture_publications": (f"https://www.{dept_slug}.gouv.fr/Publications"
                                    if dept_slug else None),
        # council_deliberations — the town-hall site's minutes/deliberations
        "town_hall_site": _town_hall_site(insee),
        # T2 documentation transparency — is the dossier online? (registry / prefecture / aggregator)
        "impact_study_aggregator": "https://www.projets-environnement.gouv.fr/pages/home/",
        # legal_appeals_count (pending) — press points; prove via the R.600-7 registry certificate
        "pending_appeals_note": ("Pending (unjudged) appeals are not in open data — detect in "
                                 "press, prove with an art. R.600-7 certificat de non-recours "
                                 "from the competent TA registry."),
    }
    if cndp and cndp.get("cndp_referral") and cndp["source"].get("url"):
        leads["cndp_fiche"] = cndp["source"]["url"]
    return leads
