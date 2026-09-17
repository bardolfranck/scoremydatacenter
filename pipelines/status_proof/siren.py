# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""SIREN operator_type — resolve a fiche's operator against the French company register (public API,
no key) so a labeling function can read `operator` identity and NAF class instead of `unknown`.

R&D-signed spec: newsroom analysis/status-proof-v1/siren-operator-type-recon.md (2026-09-17). The hard
lesson is that short French brands collide by name (« COLT » the entity ≠ COLT TECHNOLOGY SERVICES;
« SIGMA » real-estate ≠ Sigma Informatique), so name-equality alone is not enough:

  - token-EQUALITY, never substring (kills Colt ⊂ COLTER);
  - a NAF grid votes operator / developer / ambiguous, and REJECTS off-trade homonyms (cleaning, façade);
  - two paths — a nationally distinctive brand (siège anywhere) and a commune-anchored local one;
  - ordered-exact + NAF-coreness rank the canonical operator above a same-name holding;
  - a single GENERIC or short-generic token that only lands a non-core NAF returns `unknown` — no guess.

`match()` is pure over injected fetchers (testable, no network). Emit tiers, hand-audited on the FR
`operator=unknown` bucket: `confident` (exact + operator NAF) ≥94 %; `lower_confidence` (superset +
operator NAF) ≈93 %; `developer_needs_confirm` NEVER auto-demotes; `ambiguous`/`unknown` assert nothing.
Only `confident` (and, once measured, `lower_confidence`) should feed operator-fill; a public operator
label is a separate Franck gate. Non-FR fiches are out of scope (need per-country registers).
"""

import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

SEARCH_API = "https://recherche-entreprises.api.gouv.fr/search"
GEO_API = "https://geo.api.gouv.fr/communes"
UA = "smdc-status-proof/1.0 (scoremydatacenter.org)"
PER_PAGE = 20            # canonical operators sit below same-name homonyms; a short page hides them

# NAF grid (positive include). operator = DC-plausible; developer = pure promotion (feeds NOTHING
# automatically); ambiguous = real-estate/holding (identity only, class unresolved); else = reject.
NAF_OPERATOR = {"63.11Z", "63.12Z", "61.10Z", "61.20Z", "61.90Z", "62.01Z", "62.02A", "62.02B",
                "62.03Z", "62.09Z", "58.29A", "58.29B", "58.29C", "26.20Z", "95.11Z"}
NAF_DEVELOPER = {"41.10A", "41.10B", "41.20A", "41.20B", "68.10Z"}
NAF_AMBIGUOUS = {"68.20A", "68.20B", "64.20Z", "70.10Z", "70.22Z", "82.99Z", "84.13Z", "35.11Z", "35.14Z"}
# NAF coreness WITHIN operator-class: the real DC operator is telecom/hosting, not a same-name
# programming/misc homonym — lets « COLT TECHNOLOGY SERVICES » (61.10Z) beat a bare « COLT » (62.01Z).
NAF_CORE = {"63.11Z", "63.12Z", "61.10Z", "61.20Z", "61.90Z"}
NAF_MID = {"62.02A", "62.02B", "62.03Z", "62.09Z", "58.29A", "58.29B", "58.29C"}

# words stripped before matching: legal forms, and site/role markers that pollute a brand query
LEGAL = {"sas", "sasu", "sarl", "sa", "eurl", "snc", "sci", "ste", "societe", "group", "groupe",
         "france", "holding", "san", "scop", "gie", "spl", "syndicat", "mixte", "conseil", "net"}
NOISE = {"dc", "nro", "netcenter", "datacenter", "data", "center", "campus", "site", "paris",
         "ou", "no", "the", "by", "ex"}
# generic words that must NEVER be the ONLY distinctive brand token (« C-datacenters » must not match
# TITAN DATACENTERS on the shared word « datacenters »). A brand that is all-generic → unknown.
GENERIC = {"datacenter", "datacenters", "data", "center", "centre", "cloud", "clouds", "hosting",
           "network", "networks", "telecom", "telecoms", "digital", "services", "service", "systeme",
           "systemes", "systems", "system", "technologies", "technology", "info", "tech", "infra",
           "infrastructure", "infrastructures", "numerique", "communication", "communications"}


class SirenFetchError(RuntimeError):
    """The register/geo API stayed unreachable — raised loudly so a batch never silently fills nothing."""


def _strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", _strip_accents((s or "").lower()))


def _tokens(s, drop_legal=True):
    return [t for t in _norm(s).split() if len(t) >= 3 and (not drop_legal or t not in LEGAL)]


def brand_query(name, commune=None):
    """A clean brand string from a noisy fiche name (« COGENT_-_TOULOUSE », « SFR / X_-_Y »): keep the
    lead brand, drop the site tail, site numbers, NOISE words and the fiche's own commune name."""
    n = name.replace("_", " ")
    n = re.split(r"\s[-–]\s|\s{2,}", n)[0].split("/")[0]
    n = re.sub(r"[#?].*$", "", n)
    com = set(_norm(commune).split()) if commune else set()
    toks = [t for t in n.split() if not re.fullmatch(r"\d+", t)]
    kept = [t for t in toks if _norm(t) and _norm(t) not in NOISE and _norm(t) not in com]
    return re.sub(r"\s+", " ", " ".join(kept or toks)).strip()


def naf_class(naf):
    if naf in NAF_OPERATOR:
        return "operator"
    if naf in NAF_DEVELOPER:
        return "developer"
    if naf in NAF_AMBIGUOUS:
        return "ambiguous"
    return "reject"


def naf_core_tier(naf):
    return 2 if naf in NAF_CORE else 1 if naf in NAF_MID else 0


def _denom_tokens(x):
    parts = [x.get("nom_complet"), x.get("nom_raison_sociale"), x.get("sigle")]
    for e in (x.get("matching_etablissements") or []):
        if isinstance(e, dict):
            parts.append(e.get("enseigne_1"))
    toks = set()
    for p in parts:
        toks |= set(_tokens(p or ""))
    return toks


def _covered(brand_toks, denom_toks):
    """token-EQUALITY: every distinctive brand token must EQUAL a denomination token (no substring)."""
    return bool(brand_toks) and set(brand_toks).issubset(denom_toks)


def _emit_tier(operator_type, strength):
    if operator_type == "developer":
        return "developer_needs_confirm"
    if operator_type == "operator":
        return "confident" if strength == "exact" else "lower_confidence"
    if operator_type == "ambiguous":
        return "ambiguous_identity_only"
    return "unknown"


def _unknown(fiche, reason, query, commune):
    return {"id": fiche["id"], "operator_in": fiche.get("operator"), "operator_type": "unknown",
            "emit_tier": "unknown", "resolved": None, "reason": reason, "query": query, "commune": commune}


def default_search(query, code_postal=None, retries=4, sleep=time.sleep):
    """One register search. Raises SirenFetchError on persistent failure (never a silent empty list —
    a masked failure would wrongly leave an operator `unknown`). A well-formed empty result is fine."""
    url = f"{SEARCH_API}?q={urllib.parse.quote(query)}&per_page={PER_PAGE}"
    if code_postal:
        url += f"&code_postal={code_postal}"
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r).get("results", [])
        except Exception as e:  # noqa: BLE001 — network/HTTP/JSON, retried then raised
            last = e
            print(f"siren search «{query}»: attempt {attempt + 1} failed: {e}", file=sys.stderr)
            sleep(5 * (attempt + 1))
    raise SirenFetchError(f"recherche-entreprises unreachable after {retries} attempts: {last}")


def default_commune(lat, lon, retries=3, sleep=time.sleep):
    """Reverse-geocode to (commune, code_postal); raises on persistent failure. (None, None) only when
    the API legitimately returns no commune for the point."""
    url = f"{GEO_API}?lat={lat}&lon={lon}&fields=nom,codesPostaux&format=json"
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                d = json.load(r)
            return (d[0]["nom"], d[0].get("codesPostaux", [None])[0]) if d else (None, None)
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"siren geo ({lat},{lon}): attempt {attempt + 1} failed: {e}", file=sys.stderr)
            sleep(3 * (attempt + 1))
    raise SirenFetchError(f"geo.api.gouv.fr unreachable after {retries} attempts: {last}")


def match(fiche, *, search=default_search, commune=default_commune):
    """Resolve one fiche's operator. Pure over the injected `search`/`commune` callables (unit-tested
    without network). `fiche` needs id, name, lat, lon and optional operator. Returns a row with
    emit_tier / operator_type / resolved{siren,naf,denomination} / provenance, or an `unknown` row.
    """
    name = fiche["name"]
    op = str(fiche.get("operator") or "")
    known = op.lower() not in ("unknown", "", "none")
    com, cp = (commune(fiche["lat"], fiche["lon"]) if fiche.get("lat") is not None else (None, None))
    q = op if known else brand_query(name, com)
    brand_toks = [t for t in _tokens(q) if t not in NOISE]
    # no-guess: a brand with no DISTINCTIVE (non-generic) token can't be safely resolved by name
    if not [t for t in brand_toks if t not in GENERIC]:
        return _unknown(fiche, "no distinctive (non-generic) brand token", q, com)

    res = search(q, None)
    com_l = (com or "").lower()

    def covered_nonreject(x):
        return _covered(brand_toks, _denom_tokens(x)) and naf_class(x.get("activite_principale")) != "reject"

    if cp and not any(covered_nonreject(x) for x in res):     # local fallback for a buried generic brand
        seen = {x.get("siren") for x in res}
        res = res + [x for x in search(q, cp) if x.get("siren") not in seen]

    bset = set(brand_toks)
    bstr = " ".join(brand_toks)
    naf_w = {"operator": 3, "ambiguous": 1, "developer": 2}
    cands = []
    for idx, x in enumerate(res):
        dt = _denom_tokens(x)
        if not _covered(brand_toks, dt):
            continue
        cls = naf_class(x.get("activite_principale"))
        if cls == "reject":                       # off-trade homonym (cleaning/façade/VPC) — drop
            continue
        dnorm = _norm(x.get("nom_complet") or "")
        ordered = 1 if (dnorm == bstr or dnorm.startswith(bstr + " ")) else 0
        commune_hit = 1 if (x.get("siege", {}).get("libelle_commune") or "").lower() == com_l else 0
        core = naf_core_tier(x.get("activite_principale"))
        cands.append(((naf_w[cls], ordered, core, commune_hit, -idx), dt == bset, bool(commune_hit), cls, x))
    if not cands:
        off = [x for x in res if _covered(brand_toks, _denom_tokens(x))]
        reason = (f"naf_reject {off[0].get('activite_principale')} ({off[0].get('nom_complet')})"
                  if off else "no token-equality candidate")
        return _unknown(fiche, reason, q, com)

    cands.sort(key=lambda c: c[0], reverse=True)
    _, exact, commune_hit, cls, best = cands[0]
    naf = best.get("activite_principale")
    # no-guess tighten: a single short generic token on a NON-core NAF is not safely the operator
    if cls == "operator" and len(brand_toks) == 1 and naf_core_tier(naf) < 2:
        return _unknown(fiche, f"single_generic_token non-core NAF {naf} ({best.get('nom_complet')})", q, com)

    strength = "exact" if exact else "superset"
    row = {
        "id": fiche["id"], "operator_in": op, "operator_type": cls,
        "emit_tier": _emit_tier(cls, strength),
        "resolved": {"siren": best.get("siren"), "denomination": best.get("nom_complet"),
                     "naf": naf, "naf_commune": best.get("siege", {}).get("libelle_commune")},
        "matched_on": "brand+commune" if commune_hit else "brand",
        "match_strength": strength, "brand_tokens": brand_toks, "query": q, "commune": com,
        "provenance": {"source": "recherche-entreprises.api.gouv.fr",
                       "accessed": time.strftime("%Y-%m-%d"), "rule": "token-equality+naf-grid v1.1"},
    }
    if cls == "developer":   # feeds NOTHING automatically — R&D adjudicates before any demote
        row["needs_confirm"] = True
    return row
