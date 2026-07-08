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
            human_sources = src_links or [_UMAP_MAP]
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


def fetch_gdelt(query: str, accessed: str, *, timespan: str = "3m", maxrecords: int = 50) -> list[dict]:
    """Press-detection articles for a query. DETECTION only — never a score input, never weighted.

    GDELT is throttled (one request / 5 s) and OR-matches multiword terms; anchor queries with
    near20:"operator commune" and a contestation lexicon upstream. Degrades to [] on 429/empty.
    """
    params = {"query": query, "mode": "artlist", "format": "json",
              "maxrecords": min(maxrecords, 250), "timespan": timespan}
    try:
        raw = get_text(_GDELT + "?" + _urlencode(params))
        data = json.loads(raw)                              # 429 returns a plain-text notice → JSONDecodeError
    except (SourceUnavailable, json.JSONDecodeError):
        return []
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


def _urlencode(params: dict) -> str:
    import urllib.parse
    return urllib.parse.urlencode(params)
