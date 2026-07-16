# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""stats.json — the corpus aggregates behind « Les chiffres du parc » (T0).

Contract (cadrage §4.10, brief 2026-07-15):
- aggregates PUBLISHED/SOURCED values only; `missing` and `not_collected`
  sites are excluded from the denominator AND counted apart (never a silent
  truncation);
- every stat carries its n, the list of aggregated countries, and the file
  carries the corpus date + methodology version;
- a stat NEVER aggregates a country where its indicator is not wired
  (wired = the collection campaign ran there, i.e. at least one site
  assessed); unwired countries are listed, not merged;
- a share below STATS_MIN_N sites is not published (min_coverage logic) —
  it moves to the perimeter's `gated` map;
- deterministic: same repository content → byte-identical stats.json
  (no timestamps; the date is the corpus's own latest event date).

The engine emits DATA only. Labels, phrasing, sections and the
bonus/friction editorial rule live site-side (i18n), never here.
"""

from collections import Counter

# Below this many assessed sites a percentage is noise, not a fact.
# 5, pas 10 (Franck, 2026-07-16) : une part sur 8 sites se publie — avec son n
# affiché, le lecteur juge. Sous 5, c'est une anecdote déguisée en moyenne.
STATS_MIN_N = 5

# Indicator statuses that mean "a published/sourced value exists".
_ASSESSED = ("measured", "announced", "verified")

# French department → region (slug). The only admin mapping wired so far;
# other countries fall back to no regional breakdown (admin areas are not
# comparable units across countries — cadrage §4.10, international by
# construction means we never fake a common grid).
_FR_DEPT_REGION = {
    # Île-de-France
    "75": "ile-de-france", "77": "ile-de-france", "78": "ile-de-france", "91": "ile-de-france",
    "92": "ile-de-france", "93": "ile-de-france", "94": "ile-de-france", "95": "ile-de-france",
    # Hauts-de-France
    "02": "hauts-de-france", "59": "hauts-de-france", "60": "hauts-de-france",
    "62": "hauts-de-france", "80": "hauts-de-france",
    # Grand Est
    "08": "grand-est", "10": "grand-est", "51": "grand-est", "52": "grand-est",
    "54": "grand-est", "55": "grand-est", "57": "grand-est", "67": "grand-est",
    "68": "grand-est", "88": "grand-est",
    # Normandie
    "14": "normandie", "27": "normandie", "50": "normandie", "61": "normandie", "76": "normandie",
    # Bretagne
    "22": "bretagne", "29": "bretagne", "35": "bretagne", "56": "bretagne",
    # Pays de la Loire
    "44": "pays-de-la-loire", "49": "pays-de-la-loire", "53": "pays-de-la-loire",
    "72": "pays-de-la-loire", "85": "pays-de-la-loire",
    # Centre-Val de Loire
    "18": "centre-val-de-loire", "28": "centre-val-de-loire", "36": "centre-val-de-loire",
    "37": "centre-val-de-loire", "41": "centre-val-de-loire", "45": "centre-val-de-loire",
    # Bourgogne-Franche-Comté
    "21": "bourgogne-franche-comte", "25": "bourgogne-franche-comte", "39": "bourgogne-franche-comte",
    "58": "bourgogne-franche-comte", "70": "bourgogne-franche-comte", "71": "bourgogne-franche-comte",
    "89": "bourgogne-franche-comte", "90": "bourgogne-franche-comte",
    # Auvergne-Rhône-Alpes
    "01": "auvergne-rhone-alpes", "03": "auvergne-rhone-alpes", "07": "auvergne-rhone-alpes",
    "15": "auvergne-rhone-alpes", "26": "auvergne-rhone-alpes", "38": "auvergne-rhone-alpes",
    "42": "auvergne-rhone-alpes", "43": "auvergne-rhone-alpes", "63": "auvergne-rhone-alpes",
    "69": "auvergne-rhone-alpes", "73": "auvergne-rhone-alpes", "74": "auvergne-rhone-alpes",
    # Nouvelle-Aquitaine
    "16": "nouvelle-aquitaine", "17": "nouvelle-aquitaine", "19": "nouvelle-aquitaine",
    "23": "nouvelle-aquitaine", "24": "nouvelle-aquitaine", "33": "nouvelle-aquitaine",
    "40": "nouvelle-aquitaine", "47": "nouvelle-aquitaine", "64": "nouvelle-aquitaine",
    "79": "nouvelle-aquitaine", "86": "nouvelle-aquitaine", "87": "nouvelle-aquitaine",
    # Occitanie
    "09": "occitanie", "11": "occitanie", "12": "occitanie", "30": "occitanie",
    "31": "occitanie", "32": "occitanie", "34": "occitanie", "46": "occitanie",
    "48": "occitanie", "65": "occitanie", "66": "occitanie", "81": "occitanie", "82": "occitanie",
    # Provence-Alpes-Côte d'Azur
    "04": "provence-alpes-cote-d-azur", "05": "provence-alpes-cote-d-azur",
    "06": "provence-alpes-cote-d-azur", "13": "provence-alpes-cote-d-azur",
    "83": "provence-alpes-cote-d-azur", "84": "provence-alpes-cote-d-azur",
    # Corse
    "2A": "corse", "2B": "corse", "20": "corse",
    # Outre-mer
    "971": "outre-mer", "972": "outre-mer", "973": "outre-mer", "974": "outre-mer", "976": "outre-mer",
}

# Share stats — the numerator is a set of published values (or a predicate on
# identity for `field` stats). `denominator` chooses the base population:
#   assessed — sites whose indicator carries a published value (the default);
#   sites    — every site of a wired country (for "who publishes X?" stats,
#              where not_collected IS the finding: nothing was published).
_SHARE_STATS = [
    {"id": "grid_saturated", "indicator": "E2", "values": {"saturated"}, "denominator": "assessed"},
    {"id": "grid_queue_critical", "indicator": "E3", "values": {"critical", "high"}, "denominator": "assessed"},
    {"id": "water_stress_high", "indicator": "W1", "values": {"high", "zre_or_crisis"}, "denominator": "assessed"},
    {"id": "water_no_stress", "indicator": "W1", "values": {"no_stress"}, "denominator": "assessed"},
    {"id": "soil_artificialized", "indicator": "F2", "values": {"artificialized"}, "denominator": "assessed"},
    {"id": "protected_area_close", "indicator": "F1", "values": {"adjacent_under_1km", "overlap"}, "denominator": "assessed"},
    {"id": "seveso_high_2km", "indicator": "L3", "values": {"seveso_high_within_2km"}, "denominator": "assessed"},
    {"id": "pue_published", "indicator": "E4", "values": None, "denominator": "sites"},
    {"id": "heat_reuse", "indicator": "F5", "values": None, "denominator": "sites"},
]

_PIPELINE_STATUSES = ("announced", "permitting", "under_construction")


def _region(dc: dict) -> str | None:
    ident = dc["identity"]
    if ident["country"] != "FR":
        return None
    return _FR_DEPT_REGION.get(str(ident.get("admin_area") or ""))


def _indicator(dc: dict, iid: str) -> dict | None:
    for entry in dc["indicators"]:
        if entry["id"] == iid:
            return entry
    return None


def _share(spec: dict, sites: list[dict]) -> tuple[dict | None, int]:
    """Compute one share stat over `sites`. Returns (stat or None, n) — None
    when gated (n < STATS_MIN_N) or when no country is wired."""
    iid = spec["indicator"]
    # wired = the collection campaign ran in that country (≥1 assessed site)
    assessed_by_country: Counter = Counter()
    for dc in sites:
        entry = _indicator(dc, iid)
        if entry and entry["status"] in _ASSESSED:
            assessed_by_country[dc["identity"]["country"]] += 1
    wired = {c for c, n in assessed_by_country.items() if n > 0}
    excluded_countries = sorted({dc["identity"]["country"] for dc in sites} - wired)
    if not wired:
        return None, 0

    num = 0
    n = 0
    excluded: Counter = Counter()
    for dc in sites:
        if dc["identity"]["country"] not in wired:
            continue
        entry = _indicator(dc, iid)
        status = entry["status"] if entry else "not_collected"
        if status in _ASSESSED:
            in_num = True if spec["values"] is None else (entry.get("value") in spec["values"])
            n += 1
            num += 1 if in_num else 0
        elif spec["denominator"] == "sites":
            # "who publishes?" stats: silence IS the observation — it stays
            # in the denominator (and is still reported apart).
            n += 1
            excluded[status] += 1
        else:
            excluded[status] += 1

    if n < STATS_MIN_N:
        return None, n
    return {
        "kind": "share",
        "pct": round(100.0 * num / n, 1),
        "num": num,
        "n": n,
        "countries": sorted(wired),
        "excluded": dict(sorted(excluded.items())),
        "countries_excluded": excluded_countries,
    }, n


def _pipeline(sites: list[dict]) -> dict | None:
    pipe = [dc for dc in sites if dc["identity"]["project_status"] in _PIPELINE_STATUSES]
    if not pipe:
        return None
    mw = [dc["identity"]["power_mw"] for dc in pipe
          if isinstance(dc["identity"].get("power_mw"), (int, float))]
    return {
        "kind": "pipeline",
        "projects": len(pipe),
        "mw_announced": round(sum(mw)),
        "mw_disclosed_n": len(mw),
        "mw_undisclosed_n": len(pipe) - len(mw),
        "by_status": dict(sorted(Counter(dc["identity"]["project_status"] for dc in pipe).items())),
        "countries": sorted({dc["identity"]["country"] for dc in pipe}),
    }


def _power_disclosed(sites: list[dict]) -> dict | None:
    n = len(sites)
    if n < STATS_MIN_N:
        return None
    num = sum(1 for dc in sites if isinstance(dc["identity"].get("power_mw"), (int, float)))
    return {
        "kind": "share",
        "pct": round(100.0 * num / n, 1),
        "num": num,
        "n": n,
        "countries": sorted({dc["identity"]["country"] for dc in sites}),
        "excluded": {},
        "countries_excluded": [],
    }


def _watchlist_stat(entries: list[dict], countries: set[str]) -> dict | None:
    inside = [e for e in entries if e.get("country") in countries]
    if not inside:
        return None
    kinds: Counter = Counter()
    for e in inside:
        fact_kinds = {f.get("kind") for f in (e.get("facts") or [])}
        if "moratorium" in fact_kinds:
            kinds["moratorium"] += 1
        elif fact_kinds & {"opposition", "appeal", "petition"}:
            kinds["opposition"] += 1
        else:
            kinds["announced_project"] += 1
    return {
        "kind": "watchlist",
        "entries": len(inside),
        "kinds": dict(sorted(kinds.items())),
        "countries": sorted({e["country"] for e in inside}),
    }


def _coverage_mean_pct(sites: list[dict], mvp_ids: list[str]) -> float:
    if not sites or not mvp_ids:
        return 0.0
    total = 0.0
    for dc in sites:
        assessed = sum(1 for e in dc["indicators"] if e["id"] in mvp_ids and e["status"] in _ASSESSED)
        total += assessed / len(mvp_ids)
    return round(100.0 * total / len(sites), 1)


def _perimeter(sites: list[dict], watchlist: list[dict], mvp_ids: list[str]) -> dict:
    countries = sorted({dc["identity"]["country"] for dc in sites})
    stats: dict[str, dict] = {}
    gated: dict[str, int] = {}
    for spec in _SHARE_STATS:
        stat, n = _share(spec, sites)
        if stat is None:
            gated[spec["id"]] = n
        else:
            stats[spec["id"]] = stat
    if (pd := _power_disclosed(sites)) is not None:
        stats["power_disclosed"] = pd
    else:
        gated["power_disclosed"] = len(sites)
    if (pipe := _pipeline(sites)) is not None:
        stats["pipeline"] = pipe
    if (watch := _watchlist_stat(watchlist, set(countries))) is not None:
        stats["oppositions"] = watch
    return {
        "n_sites": len(sites),
        "countries": countries,
        "coverage_mean_pct": _coverage_mean_pct(sites, mvp_ids),
        "by_status": dict(sorted(Counter(dc["identity"]["project_status"] for dc in sites).items())),
        "stats": stats,
        "gated": dict(sorted(gated.items())),
    }


def build_stats(datacenters: dict[str, dict], methodology: dict,
                watchlist: list[dict] | None = None) -> dict:
    """Compute the full stats.json payload (see module docstring for the contract)."""
    watchlist = watchlist or []
    sites = [dc for dc_id, dc in sorted(datacenters.items()) if not dc_id.startswith("zz-")]
    mvp_ids = [i["id"] for i in methodology["indicators"] if i.get("mvp")]

    # Deterministic corpus date: the latest date the corpus itself records —
    # score events first, else the freshest source access date ("data as of").
    dates = [e.get("date") for dc in sites for e in dc.get("score_history", []) if e.get("date")]
    if not dates:
        dates = [src["accessed"] for dc in sites for entry in dc["indicators"]
                 if isinstance((src := entry.get("source")), dict) and src.get("accessed")]
    corpus_date = max(dates) if dates else None

    perimeters: dict[str, dict] = {"europe": _perimeter(sites, watchlist, mvp_ids)}
    for country in sorted({dc["identity"]["country"] for dc in sites}):
        c_sites = [dc for dc in sites if dc["identity"]["country"] == country]
        peri = _perimeter(c_sites, watchlist, mvp_ids)
        regions: dict[str, dict] = {}
        for slug in sorted({r for dc in c_sites if (r := _region(dc))}):
            r_sites = [dc for dc in c_sites if _region(dc) == slug]
            regions[slug] = _perimeter(r_sites, watchlist, mvp_ids)
        if regions:
            peri["regions"] = regions
        perimeters[country] = peri

    return {
        "schema": "stats/1",
        "methodology_version": methodology["version"],
        "corpus_date": corpus_date,
        "min_n": STATS_MIN_N,
        "perimeters": perimeters,
    }
