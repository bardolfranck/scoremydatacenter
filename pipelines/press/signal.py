# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Voie-B collectors — the contestation *signal* (facts, never a grade — A-21).

Four open feeds, each normalized into a common sourced record. NONE of these ever produces a
score, a letter, or a confidence — they publish facts for the "En veille" watchlist layer (A-19)
and to annotate scored fiches. What must NEVER be weighted (press volume/tone, self-reported
signature counts) stays a detection signal only. See RECON-contestation-signal.md.

  * fetch_umap_layers  — community FR map: opposition + announced-project points (GeoJSON layers)
  * fetch_fights       — community US dataset of contested projects (JSON, CC BY 4.0)
  * fetch_moratoria    — community US moratorium inventory (CSV, CC BY 4.0)
  * fetch_gdelt        — global press detection (GDELT DOC artlist) — DETECTION only, rate-limited

Every collector degrades to an empty list on any failure — it proposes, never fabricates.
"""

import csv
import io
import json
import re

from pipelines.spatial.http import SourceUnavailable, get_json, get_text

# --- shared -----------------------------------------------------------------------------------

# A description bundles several links; rank the citable ones so a SPECIFIC press article beats a
# generic collectif homepage or a link-aggregator. The reviewer still gets the full ordered list and
# picks THE source — this only sets a sensible default so the fiche never shows a bare homepage.
_AGGREGATOR_HINTS = ("linktr.ee", "confederationciq", "greenvoice", "helloasso", "annuaire",
                     "facebook.com", "instagram.com", "twitter.com", "proton.me")
_PRESS_HINTS = ("laprovence", "marsactu", "francetvinfo", "france3-regions", "ici.fr", "ledauphine",
                "lalsace", "alterpresse", "liberation", "francebleu", "lavoixdunord", "ouest-france",
                "lemonde", "mediapart", "reporterre", "bastamag", "actu.fr", "sudouest")


def _rank_source_links(links: list[str]) -> list[str]:
    """Order candidate links best-first: specific press article > other page > homepage/aggregator."""
    from urllib.parse import urlparse

    def score(u: str) -> int:
        p = urlparse(u)
        path = (p.path or "").strip("/")
        s = -5 if not path else min(len(path) // 10, 4)   # bare homepage penalised; long slug rewarded
        if any(h in u for h in _AGGREGATOR_HINTS):
            s -= 4
        if any(d in (p.netloc or "") for d in _PRESS_HINTS):
            s += 3
        return s

    return sorted(dict.fromkeys(links), key=score, reverse=True)


def _as_urls(sources) -> list[str]:
    """Coerce a feed's `sources` (strings, or {url,title} objects) into a deduped list of URL strings."""
    out = []
    for s in sources or []:
        if isinstance(s, str):
            url = s
        elif isinstance(s, dict):
            url = s.get("url") or s.get("href") or s.get("link")
        else:
            url = None
        if url and url not in out:
            out.append(url)
    return out


def _record(source: str, source_url: str, license: str, kind: str, *, name, country,
            lat=None, lon=None, status=None, opposition_groups=None, facts=None,
            sources=None, retrieved) -> dict:
    """A single sourced contestation-signal record. Never carries a grade/letter/confidence."""
    urls = _as_urls(sources) or ([source_url] if source_url else [])
    return {
        "source": source,
        "source_url": source_url,
        "license": license,
        "kind": kind,                       # opposition | announced_project | moratorium | article
        "name": name,                       # nominative → private newsroom only, never public pre-review
        "country": country,
        "coordinates": ({"lat": lat, "lon": lon} if lat is not None and lon is not None else None),
        "status": status,
        "opposition_groups": opposition_groups,
        "facts": facts or {},               # feed-specific sourced facts — NO score, ever
        "sources": urls,
        "retrieved": retrieved,
    }


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# --- feed 1 · community FR map (uMap) — opposition + announced projects ----------------------

_UMAP_MAP = ("https://umap.openstreetmap.fr/fr/map/"
             "carte-des-data-centers-des-projets-et-des-contesta_1289485")
_UMAP_DATALAYER = "https://umap.openstreetmap.fr/fr/datalayer/1289485/{uuid}/"
_UMAP_LICENSE = "community map (uMap/OSM) — licence unset upstream, confirm before commercial reuse"
_OPP_RE = re.compile(r"opposition|contestation|collectif|lutte|stop", re.I)
# OSM-tag keys that mark the raw-inventory layer (existing DCs) — a duplicate of Overpass, skipped.
_OSM_INVENTORY_KEYS = {"telecom", "operator", "@id", "operator:wikidata", "ref"}


def _umap_layer_uuids(accessed: str) -> list[str]:
    try:
        page = get_text(_UMAP_MAP)
    except SourceUnavailable:
        return []
    seen, out = set(), []
    for u in re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", page):
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _classify_umap_layer(features: list[dict]) -> str:
    """Content heuristic (robust to rotating layer UUIDs): opposition / project / inventory / other."""
    keys = set()
    names = []
    for f in features[:40]:
        props = f.get("properties") or {}
        keys |= set(props.keys())
        if props.get("name"):
            names.append(props["name"])
    if keys & _OSM_INVENTORY_KEYS:
        return "inventory"                                   # existing DCs → Overpass dupes, skip
    if names and sum(bool(_OPP_RE.search(n)) for n in names) >= max(1, len(names) // 2):
        return "opposition"
    if {"city", "postcode", "countrycode", "state"} & keys:  # Nominatim geocoding fields
        return "announced_project"
    return "other"


def fetch_umap_layers(accessed: str) -> list[dict]:
    """Opposition + announced-project points from the community FR map. Inventory layer is skipped."""
    out = []
    for uuid in _umap_layer_uuids(accessed):
        url = _UMAP_DATALAYER.format(uuid=uuid)
        try:
            fc = get_json(url)
        except SourceUnavailable:
            continue
        features = fc.get("features") or []
        kind = _classify_umap_layer(features)
        if kind not in ("opposition", "announced_project"):
            continue
        for f in features:
            geom = f.get("geometry") or {}
            coords = geom.get("coordinates") if geom.get("type") == "Point" else None
            props = f.get("properties") or {}
            name = (props.get("name") or "").strip()
            if not name:
                continue
            desc = (props.get("description") or "").strip()
            src_links = re.findall(r"https?://[^\s)>\]]+", desc)
            # Human-citable source = the press/collectif link in the description, NOT the machine
            # datalayer feed. Fall back to the human map page — never the raw GeoJSON endpoint
            # (a local-official reader must land on an article, not on JSON). The datalayer stays
            # only as internal provenance (source_url).
            human_sources = _rank_source_links(src_links) or [_UMAP_MAP]
            out.append(_record(
                "umap-fr", url, _UMAP_LICENSE, kind,
                name=name, country="FR",
                lat=(coords[1] if coords else None), lon=(coords[0] if coords else None),
                status=None,
                facts={"note": desc[:500]} if desc else {},
                sources=human_sources, retrieved=accessed))
    return out


# --- feed 2 · community US dataset of contested projects (fights.json, CC BY 4.0) ------------

_FIGHTS_URL = "https://datacentertracker.org/data/fights.json"
_FIGHTS_LICENSE = "CC BY 4.0 (datacentertracker.org)"


def fetch_fights(accessed: str, *, only_with_opposition: bool = True, limit: int | None = None) -> list[dict]:
    """US contested-project records. By default keeps only rows with named opposition groups."""
    try:
        rows = get_json(_FIGHTS_URL)
    except SourceUnavailable:
        return []
    if not isinstance(rows, list):
        return []
    out = []
    for r in rows:
        groups = r.get("opposition_groups") or []
        if isinstance(groups, str):
            groups = [g.strip() for g in re.split(r"[;,]", groups) if g.strip()]
        if only_with_opposition and not groups:
            continue
        lat, lon = _num(r.get("lat")), _num(r.get("lng"))
        name = (r.get("project_name") or r.get("jurisdiction") or "").strip()
        if not name:
            continue
        petition_sig = r.get("petition_signatures")
        out.append(_record(
            "us-fights", _FIGHTS_URL, _FIGHTS_LICENSE, "opposition",
            name=name, country="US", lat=lat, lon=lon,
            status=r.get("status"), opposition_groups=groups or None,
            facts={
                "company": r.get("company"), "hyperscaler": r.get("hyperscaler"),
                "action_type": r.get("action_type"), "issue_category": r.get("issue_category"),
                "community_outcome": r.get("community_outcome"),
                "investment_million_usd": r.get("investment_million_usd"),
                "megawatts": r.get("megawatts"),
                # self-reported petition count is a WEAK, gameable signal — carried, flagged, never scored
                "petition_signatures_self_reported": petition_sig,
                "last_updated": r.get("last_updated"),
            },
            sources=(r.get("sources") or []) + [_FIGHTS_URL], retrieved=accessed))
        if limit and len(out) >= limit:
            break
    return out


# --- feed 3 · community US moratorium inventory (CSV, CC BY 4.0) -----------------------------

_MORATORIUM_URL = ("https://raw.githubusercontent.com/mjbommar/moratorium-data-2026/"
                   "main/data/moratorium_inventory.csv")
_MORATORIUM_LICENSE = "CC BY 4.0 (moratorium-data-2026)"


def fetch_moratoria(accessed: str, *, data_center_only: bool = True) -> list[dict]:
    """US moratorium records (geocoded, sourced). Filtered to the data-center sector by default."""
    try:
        text = get_text(_MORATORIUM_URL)
    except SourceUnavailable:
        return []
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        sectors = (row.get("sectors") or "").lower()
        if data_center_only and "data_center" not in sectors:
            continue
        name = (row.get("jurisdiction") or "").strip()
        if not name:
            continue
        out.append(_record(
            "us-moratorium", _MORATORIUM_URL, _MORATORIUM_LICENSE, "moratorium",
            name=name, country="US",
            lat=_num(row.get("latitude")), lon=_num(row.get("longitude")),
            status=row.get("current_status"),
            facts={
                "jurisdiction_type": row.get("jurisdiction_type"),
                "date_enacted": row.get("date_enacted_iso") or row.get("date_enacted"),
                "duration_days": row.get("duration_days"),
                "legal_basis": (row.get("legal_basis") or "")[:300],
                "outcome": row.get("outcome"),
                "enacted_status": row.get("enacted_status"),
            },
            sources=[_MORATORIUM_URL], retrieved=accessed))
    return out


# --- feed 4 · global press detection (GDELT DOC artlist) — DETECTION ONLY --------------------

_GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
_GDELT_LICENSE = "GDELT — free incl. commercial use with attribution"
_GDELT_THROTTLE_S = 6                       # GDELT DOC throttle: one request every 5 s


# A new country's press detection is a SPEC (spelling variants + local contestation lexicon),
# never a cloned collector — the spatial pipeline's anti-clone rule (COUNTRIES.md) applied to
# voie B. `sourcecountry` filters by OUTLET country, not project country: Canadian outlets also
# cover US stories, so the reviewer still triages. DETECTION only, like every GDELT record.
GDELT_COUNTRY_SPECS = {
    # Canadian English writes "data centre"; Québec writes "centre de données" (BAPE = the
    # Québec public-hearing body, the CNDP analogue).
    "CA": {
        "sourcecountry": "canada",
        "queries": [
            '("data centre" OR "data center") (opposition OR protest OR moratorium OR zoning '
            'OR rezoning OR "public hearing")',
            '"centre de données" (opposition OR moratoire OR contestation OR zonage '
            'OR "consultation publique" OR BAPE)',
        ],
    },
}


def fetch_gdelt_country(iso: str, accessed: str, *, timespan: str = "6m", maxrecords: int = 75,
                        sleep=None, retries: int = 3) -> list[dict]:
    """Run every press-detection query of a country spec — throttle-aware, url-deduped, retried.

    GDELT punishes bursts by SLOW-WALKING the response past our timeout (not by a clean 429), so
    a batch that fired other requests first can silently lose the whole country — the voie-B twin
    of the spatial E1-memoize gotcha (COUNTRIES.md #2). Hence per-query retries with growing
    backoff, and a LOUD stderr line when a query is finally given up: a country harvest must never
    vanish without a trace.

    DETECTION only (A-21): articles are triage leads for the reviewer, never a score input.
    Unknown ISO → [] (a country without a spec has no press detection yet, not an error).
    """
    import sys
    import time

    spec = GDELT_COUNTRY_SPECS.get((iso or "").upper())
    if not spec:
        return []
    sleep = sleep or time.sleep
    seen, out = set(), []
    for i, q in enumerate(spec["queries"]):
        if i:
            sleep(_GDELT_THROTTLE_S)
        full = f'sourcecountry:{spec["sourcecountry"]} {q}'
        data = None
        for attempt in range(retries):
            try:
                data = _gdelt_fetch_raw(full, timespan=timespan, maxrecords=maxrecords)
                break
            except (SourceUnavailable, json.JSONDecodeError) as exc:
                if attempt == retries - 1:
                    print(f"gdelt[{iso}] query {i + 1}/{len(spec['queries'])}: gave up after "
                          f"{retries} attempts ({exc})", file=sys.stderr)
                else:
                    # A 429 penalty box outlasts the nominal 5 s throttle by minutes — back off
                    # in 30 s steps (batch context: losing a minute beats losing the country).
                    sleep(_GDELT_THROTTLE_S * 5 * (attempt + 1))
        for rec in _gdelt_records(data or {}, accessed):
            if rec["source_url"] in seen:
                continue
            seen.add(rec["source_url"])
            out.append(rec)
    return out


def _gdelt_fetch_raw(query: str, *, timespan: str, maxrecords: int) -> dict:
    """One GDELT DOC request. Raises on failure so callers can tell 'failed' from 'no articles'
    (a 429 returns a plain-text notice → JSONDecodeError; a slow-walked burst → SourceUnavailable)."""
    params = {"query": query, "mode": "artlist", "format": "json",
              "maxrecords": min(maxrecords, 250), "timespan": timespan}
    return json.loads(get_text(_GDELT + "?" + _urlencode(params)))


def _gdelt_records(data: dict, accessed: str) -> list[dict]:
    out = []
    for a in data.get("articles") or []:
        url = a.get("url")
        if not url:
            continue
        out.append(_record(
            "gdelt", url, _GDELT_LICENSE, "article",
            name=(a.get("title") or "").strip(), country=a.get("sourcecountry"),
            facts={"domain": a.get("domain"), "seendate": a.get("seendate"),
                   "language": a.get("language")},
            sources=[url], retrieved=accessed))
    return out


_GKG_FIPS_TO_ISO = {  # V2Locations carries FIPS 10-4 country codes, not ISO
    "FR": "FR", "BE": "BE", "SZ": "CH", "LU": "LU", "GM": "DE", "NL": "NL", "EI": "IE",
    "UK": "GB", "SP": "ES", "IT": "IT", "PO": "PT", "AU": "AT", "DA": "DK", "SW": "SE",
    "FI": "FI", "NO": "NO", "PL": "PL",
}


def _slug_title(url: str) -> str:
    """Rough human label from the URL slug — the GKG export has no article title.
    A triage aid for the reviewer, never displayed publicly (the gate swaps in the real title)."""
    import urllib.parse
    path = urllib.parse.urlparse(url).path.rstrip("/")
    slug = re.sub(r"\.\w{2,5}$", "", path.rsplit("/", 1)[-1])
    words = re.sub(r"[-_+]+", " ", slug).strip()
    return words[:140] if len(words) >= 8 else url[:140]


# Canonical DC operators — the OPERATOR aggregation axis. GDELT's V2Organizations carries
# free-text entity names; we map them to a canonical operator so "all contestation press
# mentioning Equinix" becomes one aggregation (and the B2B per-operator alert). Recall-first:
# a hit is a triage lead, the gate confirms the article really concerns that operator's project.
_OPERATORS = {
    "Equinix": r"equinix",
    "Digital Realty": r"digital realty|interxion",
    "Data4": r"\bdata4\b",
    "OVHcloud": r"ovh",
    "Scaleway/Iliad": r"scaleway|iliad|\bfree pro\b",
    "Microsoft": r"microsoft",
    "Amazon/AWS": r"amazon|\baws\b|amazon web services",
    "Google": r"google",
    "Meta": r"\bmeta\b|facebook",
    "Vantage": r"vantage",
    "CyrusOne": r"cyrusone",
    "NTT": r"\bntt\b",
    "Colt": r"\bcolt\b",
    "Telehouse/KDDI": r"telehouse|kddi",
    "STACK Infrastructure": r"stack infrastructure",
    "EdgeConneX": r"edgeconnex",
    "Vertiv": r"vertiv",
    "Segro": r"segro",
    "Goodman": r"goodman",
    "AtNorth": r"atnorth",
    "Nscale": r"nscale",
    "Mistral/MGX": r"mistral|\bmgx\b",
    "Microsoft/OpenAI": r"openai",
}
_OPERATOR_RE = {name: re.compile(pat, re.I) for name, pat in _OPERATORS.items()}


def _match_operators(organizations: str) -> tuple[list[str], list[str]]:
    """From a GKG V2Organizations blob ('name,offset;name,offset;…'), return
    (raw org names, canonical operators matched). Empty lists when nothing recognised."""
    names = []
    for chunk in (organizations or "").split(";"):
        nm = chunk.split(",")[0].strip()
        if nm and nm not in names:
            names.append(nm)
    joined = " ; ".join(names)
    operators = [op for op, rx in _OPERATOR_RE.items() if rx.search(joined)]
    return names[:20], operators


def fetch_gdelt_bq(source: str, accessed: str) -> list[dict]:
    """Press-detection articles from the BigQuery JSONL export (A-23) — the bulk route.

    `source` is a local file path or an HTTPS URL (signed GCS URL / public object) pointing to
    the newline-delimited JSON produced by `pipelines/press/gdelt/query.sql` (one object per
    article: url, domain, seendate, locations, themes). No cloud dependency here — BigQuery and
    the schedule live at GCP; we only read the export. DETECTION only (A-21): triage leads for
    the reviewer, never a score input. Degrades to [] on any failure (a missing export must
    never sink the rest of the harvest); malformed lines are skipped.
    """
    try:
        if re.match(r"^https?://", source):
            text = get_text(source)
        else:
            from pathlib import Path
            text = Path(source).read_text()
    except (SourceUnavailable, OSError):
        return []
    seen, out = set(), []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = row.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        fips = set(re.findall(r"#([A-Z]{2})#", row.get("locations") or ""))
        isos = sorted({_GKG_FIPS_TO_ISO[f] for f in fips if f in _GKG_FIPS_TO_ISO})
        org_names, operators = _match_operators(row.get("organizations") or "")
        out.append(_record(
            "gdelt-bq", url, _GDELT_LICENSE, "article",
            name=_slug_title(url), country=",".join(isos) or None,
            facts={"domain": row.get("domain"), "seendate": row.get("seendate"),
                   "mentioned_countries": isos, "title_is_slug": True,
                   "organizations": org_names, "operators": operators},
            sources=[url], retrieved=accessed))
    return out


def fetch_gdelt(query: str, accessed: str, *, timespan: str = "3m", maxrecords: int = 50) -> list[dict]:
    """Press-detection articles for a query. DETECTION only — never a score input, never weighted.

    GDELT is throttled (one request / 5 s) and OR-matches multiword terms; anchor queries with
    near20:"operator commune" and a contestation lexicon upstream. Degrades to [] on 429/empty.
    """
    try:
        data = _gdelt_fetch_raw(query, timespan=timespan, maxrecords=maxrecords)
    except (SourceUnavailable, json.JSONDecodeError):
        return []
    return _gdelt_records(data, accessed)


def _urlencode(params: dict) -> str:
    import urllib.parse
    return urllib.parse.urlencode(params)
