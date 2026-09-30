# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Coverage-plage bands — the SINGLE shared band-tightening util (« one way to run »).

A *provisional* data center (announced/permitting) has many BASE indicators still
missing. Instead of a false-precision single letter, we express its grade as a
COVERAGE PLAGE: the interval the site grade could take given what is NOT yet known.

  - Manski (partial-identification) bounds: fill every missing BASE indicator at its
    WORST vs BEST achievable sub-score → [worst, best]. Width == coverage, by construction.
  - kNN tightening: replace an indicator's theoretical [min,max] by the empirical
    [p10,p90] among the k nearest already-scored neighbours that HAVE it (same country
    first). Fallback to theoretical when < 3 usable neighbours (never fabricate precision).
  - Status floor: a provisional plage never shows narrower than an irreducible width.

⚠️ FIREWALL — THIS IS NOT PART OF THE PUBLISHED GRADE PATH.
`score_datacenter` and `build_prod_artifacts` must NEVER import this module: a coverage
plage is a provisional/analysis object, and letting it reach a served grade would publish
a band as if it were a definitive letter. There is a guard test asserting no such import.

Non-circularity: bands are STRUCTURAL — computed from BASE indicators only, blind to
contestation (L6/L7 are treated like any other base indicator here; if they are missing
they are imputed from neighbours' *structural* values, never from contestation outcomes).

Pure functions, no I/O. Callers (study cohort, FR pipeline, onboarding) pass in a scored
reference pool + the fiche's present BASE sub-scores, and all get the SAME band.
"""

from statistics import quantiles

GRADE_ORDER = ["A", "B", "C", "D", "E"]

# Lifecycle statuses that MAY be served with a provisional band (« en veille, provisoire »).
# An operational fiche is NEVER one of these: its published grade is the DEFINITIVE letter
# from score_datacenter, and a coverage band must never replace or shadow it.
PIPELINE_STATUSES = frozenset({"announced", "permitting", "under_construction"})

# Irreducible provisional width by lifecycle status (points on 0-100). Even fully
# "declared", an announced project can still change design/operator/cooling.
STATUS_FLOOR = {"announced": 18.0, "permitting": 12.0, "under_construction": 7.0}
_DEFAULT_FLOOR = 12.0

# Contestation-adjacent BASE indicators: L6 « niveau de contestation observé », L7
# « position des élus ». They sit in the base block but are kept UNPOPULATED across the
# corpus (non-circularity invariant, engine/tests/test_noncircularity.py), so the live
# SITE grade renormalizes them away. The coverage band must represent the SAME quantity
# as that published grade — L6/L7-BLIND — so a missing L6/L7 is renormalized away here
# too, NEVER swung to its extremes. Swinging them would (1) make the band encode a
# "contestation could be anything" uncertainty (circular) and (2) measure a different
# quantity than the grade. This keeps every band STRUCTURAL.
CONTESTATION_ADJACENT = frozenset({"L6", "L7"})


# ------------------------------------------------- applicabilité PAR PAYS (primitive)
# Généralisation de l'aveuglement L6/L7 ci-dessus. Un indicateur peut être NON APPLICABLE
# dans un pays — pas « pas encore collecté », mais « il n'existe aucune donnée à collecter
# ici ». Exemple fondateur : la raccordabilité à un réseau de chaleur (E6) se dérive d'un
# jeu national français ; hors de France, il n'y a rien à mesurer, et il n'y aura rien tant
# qu'un équivalent n'existe pas.
#
# La distinction est décisive pour la BANDE, et seulement pour elle :
#   · NON APPLICABLE  → renormalisé, exactement comme L6/L7. Ce n'est pas une incertitude.
#   · APPLICABLE mais non collecté → continue de swinguer. C'est un vrai trou, et la plage
#     doit s'élargir : on ne sait pas, et on le dit.
# Confondre les deux ferait porter à l'Allemagne une incertitude qu'elle ne pourra JAMAIS
# combler, donc une plage large à perpétuité — le défaut qu'on a failli introduire.
#
# CONTESTATION_ADJACENT devient un cas particulier : non applicable PARTOUT, pour
# non-circularité. Un seul mécanisme, un seul invariant.
#
# La carte est DÉCLARATIVE (méthodologie, jamais déduite des données) : un indicateur
# absent du corpus d'un pays ne doit pas devenir « non applicable » tout seul, sinon on
# blanchirait nos propres trous de collecte en les rebaptisant. Tenue par R&D.
def _not_applicable(country: str | None, methodology: dict) -> frozenset[str]:
    """Indicateurs de base non applicables dans ce pays — renormalisés, jamais swingués."""
    declared = (methodology.get("applicability") or {})
    out = set(CONTESTATION_ADJACENT)
    for iid, spec in declared.items():
        only = spec.get("countries_only") if isinstance(spec, dict) else None
        if only and country not in only:
            out.add(iid)
    return frozenset(out)


# ---------------------------------------------------------------- methodology helpers
def base_definitions(methodology: dict) -> list[dict]:
    """The MVP BASE-block indicator definitions (the site-grade inputs)."""
    return [i for i in methodology["indicators"] if i.get("mvp") and i.get("block") == "base"]


def _pillar_weights(methodology: dict) -> dict[str, float]:
    return {p["id"]: p["weight"] for p in methodology["pillars"]}


def grade_of(score: float, methodology: dict) -> str:
    thresholds = sorted(methodology["grade_thresholds"], key=lambda t: t["min"], reverse=True)
    r = round(score, 1)
    return next(t["grade"] for t in thresholds if r >= t["min"])


def extreme_subscores(defn: dict) -> tuple[float, float]:
    """(worst, best) achievable normalized sub-score for one indicator, from its scale.
    Bounds the numeric score, not the published letter (A-25 reserve handled downstream)."""
    norm = defn["normalization"]
    t = norm["type"]
    if t == "categorical":
        vals = list(norm["categories"].values())
        return float(min(vals)), float(max(vals))
    if t == "thresholds":
        vals = [s["score"] for s in norm["thresholds"]]
        return float(min(vals)), float(max(vals))
    if t == "bounded_linear":
        return 0.0, 100.0
    raise ValueError(f"plage_bands: unexpected base normalization {t!r} on {defn['id']}")


# ---------------------------------------------------------------- aggregation (base only)
def site_score_from_subscores(scored: dict[str, float], methodology: dict) -> float:
    """Replicate the engine's two-level weighted mean over the BASE block, given an
    explicit {indicator_id: sub-score} dict (every base id present)."""
    pw = _pillar_weights(methodology)
    base = base_definitions(methodology)
    pillar: dict[str, float] = {}
    for p in pw:
        pairs = [(d["weight_in_pillar"], scored[d["id"]]) for d in base
                 if d["pillar"] == p and d["id"] in scored and scored[d["id"]] is not None]
        if pairs:
            tw = sum(w for w, _ in pairs)
            pillar[p] = sum(w * s for w, s in pairs) / tw
    if not pillar:
        return 0.0
    tpw = sum(pw[p] for p in pillar)
    return sum(pw[p] * s for p, s in pillar.items()) / tpw


# ---------------------------------------------------------------- reference pool + kNN band
def build_reference_pool(scored_fiches) -> dict[str, list]:
    """Bucket already-scored fiches by country for neighbour search.

    `scored_fiches` = iterable of dicts {"country": str, "present": {base_id: sub-score}}.
    Returns {country: [present_dict, ...]}. Present = the fiche's observed BASE sub-scores.
    """
    by_country: dict[str, list] = {}
    for r in scored_fiches:
        by_country.setdefault(r.get("country"), []).append(r["present"])
    return by_country


def neighbour_band(present: dict, country: str, indicator_id: str, defn: dict,
                   pool: dict[str, list], k: int = 8) -> tuple[float, float]:
    """[p10, p90] of `indicator_id` among the k nearest neighbours (same country first,
    else all with a soft country penalty) that HAVE it. Falls back to the theoretical
    extreme sub-scores when fewer than 3 usable neighbours — never fabricates precision.
    Distance = mean squared difference over the shared present BASE sub-scores."""
    def usable(bucket):
        return [v for v in bucket if indicator_id in v]

    cand = usable(pool.get(country, []))
    cross = False
    if len(cand) < 3:  # widen to every country
        cand = [v for bucket in pool.values() for v in usable(bucket)]
        cross = True
    dists = []
    for v in cand:
        shared = set(present) & set(v)
        d = (sum((present[s] - v[s]) ** 2 for s in shared) / len(shared)) if shared else 1e9
        if cross:
            d += 2500.0  # ~½ a full 100-pt gap: prefer same-country evidence
        dists.append((d, v[indicator_id]))
    dists.sort(key=lambda x: x[0])
    vals = [s for _, s in dists[:k]]
    w_s, b_s = extreme_subscores(defn)
    if len(vals) < 3:
        return w_s, b_s
    if len(vals) >= 4:
        qs = quantiles(sorted(vals), n=10)
        return qs[0], qs[-1]
    return float(min(vals)), float(max(vals))


# ---------------------------------------------------------------- the one public entry point
def coverage_plage(present: dict, country: str, status: str, methodology: dict,
                   pool: dict[str, list] | None = None, *, tighten: bool = True) -> dict:
    """Compute the coverage plage for one fiche.

    present : {base_id: observed sub-score} for the BASE indicators actually scored.
    pool    : reference pool from build_reference_pool (required when tighten=True).
    Returns worst/best (theoretical AND kNN), the letter span, and the credibility flag
    (span <= 1 letter == a single or adjacent-letter plage). All bands are structural.
    """
    base = base_definitions(methodology)
    base_by_id = {d["id"]: d for d in base}
    missing = [d["id"] for d in base if d["id"] not in present]
    # Only STRUCTURAL gaps widen the band; contestation-adjacent gaps (L6/L7) are
    # renormalized away, exactly as the published L6/L7-blind site grade does. This is
    # what keeps the band structural and non-circular (see CONTESTATION_ADJACENT).
    blind = _not_applicable(country, methodology)
    swing = [iid for iid in missing if iid not in blind]

    def fill(mode: str, use_knn: bool) -> float:
        scored = dict(present)  # missing L6/L7 stay absent -> renormalized away by the aggregate
        for iid in swing:
            defn = base_by_id[iid]
            if use_knn and pool is not None:
                lo, hi = neighbour_band(present, country, iid, defn, pool)
            else:
                lo, hi = extreme_subscores(defn)
            scored[iid] = lo if mode == "worst" else hi
        return site_score_from_subscores(scored, methodology)

    theo_w, theo_b = fill("worst", False), fill("best", False)
    if tighten and pool is not None:
        kw, kb = fill("worst", True), fill("best", True)
    else:
        kw, kb = theo_w, theo_b

    floor = STATUS_FLOOR.get(status, _DEFAULT_FLOOR)
    if (kb - kw) < floor:
        mid = (kb + kw) / 2
        kw, kb = mid - floor / 2, mid + floor / 2
    kw, kb = max(0.0, kw), min(100.0, kb)

    def span(a, b):
        return abs(GRADE_ORDER.index(grade_of(min(100, max(0, a)), methodology)) -
                   GRADE_ORDER.index(grade_of(min(100, max(0, b)), methodology)))

    return {
        "n_present": len(present), "n_base": len(base), "n_missing": len(missing),
        "n_structural_gaps": len(swing),  # the missing indicators that actually widen the band
        "theoretical": {"worst": round(theo_w, 1), "best": round(theo_b, 1),
                        "plage": f"{grade_of(theo_w, methodology)}–{grade_of(theo_b, methodology)}",
                        "span": span(theo_w, theo_b)},
        "knn": {"worst": round(kw, 1), "best": round(kb, 1),
                "plage": f"{grade_of(kw, methodology)}–{grade_of(kb, methodology)}",
                "span": span(kw, kb)},
        "credible": span(kw, kb) <= 1,   # single or adjacent letter (<= 2 adjacent letters)
    }


# --------------------------------------------------------------- the SERVING gate
# The single decision point for what a PUBLIC artifact may show as a provisional band.
# `build_prod_artifacts` calls THIS (never coverage_plage directly) so the project-only /
# credible-only / never-operational rules live in one place and are enforced by one test.
def _structural_base(methodology: dict) -> int:
    """Collectable base indicators = base block minus contestation-adjacent (never populated).
    DERIVED from the methodology so it can't silently drift when the base set changes (it was
    hardcoded 12 = 14 minus L6/L7; adding E6 makes it 13). Global on purpose: E6 is a
    *not-collected* indicator outside France, not a *non-applicable* one, so it belongs to the
    collectable base everywhere (see _not_applicable / the applicability primitive)."""
    return sum(1 for d in base_definitions(methodology) if d["id"] not in CONTESTATION_ADJACENT)


def _coverage_confidence(n_present: int, methodology: dict) -> str:
    """Fallback confidence when the caller doesn't pass the fiche's engine confidence:
    a proxy on STRUCTURAL coverage (present / collectable base). Documented as a proxy —
    prefer the engine's own confidence.level, passed via `confidence`."""
    ratio = n_present / _structural_base(methodology)
    return "high" if ratio >= 0.75 else "medium" if ratio >= 0.5 else "low"


def servable_band(status: str, present: dict, country: str, methodology: dict,
                  pool: dict | None = None, confidence: str | None = None) -> dict | None:
    """What a SERVED fiche may display as a provisional band — or None if it may not.

    Display contract for the ScoreBadge « loupe » (enforced by test_plage_bands_firewall):
      - status NOT pipeline (operational, decommissioned, …) -> None.
        An operational fiche keeps its DEFINITIVE letter from score_datacenter; a coverage
        band must never replace or shadow it. This is the hard firewall.
      - pipeline + plage WIDER than the status floor -> `{"kind": "en_attente"}`
        (données insuffisantes) — the neutral chip ScoreBadge already renders, NO letter.
      - pipeline + plage at the floor -> a provisional object carrying:
          central   : the letter of the renorm POINT (the BIG letter in the loupe)
          edges     : the endpoint letters OTHER than central, worst first (the small chips)
          adjacent  : edges[0] when there is exactly one, else None (kept for readers that
                      predate 3-letter plages; `edges` is the general form)
          provisional: True
          confidence: "low" | "medium" | "high" (the fiche's engine confidence if passed,
                      else a structural-coverage proxy)
        It carries NO bare `grade`/`grade_site` key, so it can never be slotted into
        `grades.site.grade`. It belongs in a SEPARATE served field (e.g. `provisional_band`).

    WHY THE CRITERION IS THE WIDTH AND NOT THE LETTER COUNT (Franck, 2026-09-30, « règle C »).
    The first version withheld the band when the plage straddled more than two letters. But a
    provisional plage is almost always exactly STATUS_FLOOR wide — an irreducible convention,
    not a measurement — so counting the letters it straddles measures WHERE the window happens
    to fall against the grade thresholds, not what we know. Measured on the live corpus: 60
    fiches displaying a band had exactly the same width as the 9 that were being blanked. Worse,
    ADDING a measured fact could blank a fiche: E6 moved Étrechet by 2.3 points, the same 18.0-pt
    window then overhung the E threshold by 1.4 pt, and the most-watched page in the corpus lost
    its note, its <title> and its OG card over that 1.4 pt.
    So: « en attente » now means the plage is WIDER than the irreducible floor — we really do not
    know enough. At the floor, the plage is as tight as this lifecycle stage can ever be, and the
    honest display is the point letter plus its edges, never a blank.
    """
    if status not in PIPELINE_STATUSES:
        return None
    band = coverage_plage(present, country, status, methodology, pool)
    kw, kb = band["knn"]["worst"], band["knn"]["best"]

    # A-25 on the band: a PIPELINE project is never operationally verified, so an A it could
    # structurally reach is RESERVED — published as B. The band must show the same A-reserved
    # ceiling as a definitive grade would, so we cap every endpoint letter at B here. This is
    # not cosmetic: it re-derives the credibility span (e.g. a raw C–A becomes C–B, span 1).
    def reserved_letter(score: float) -> str:
        g = grade_of(score, methodology)
        return "B" if g == "A" else g

    a_reserved = grade_of(kb, methodology) == "A"
    worst_letter = reserved_letter(kw)      # low end (severe letter, e.g. E)
    best_letter = reserved_letter(kb)       # high end, capped at B
    span = abs(GRADE_ORDER.index(worst_letter) - GRADE_ORDER.index(best_letter))

    # « En attente » = the plage is WIDER than the irreducible floor for this lifecycle stage,
    # i.e. a real gap in what we know. `coverage_plage` has already widened any narrower plage
    # UP to the floor, so width >= floor by construction and `> floor` is exactly "wider than
    # irreducible". Never the letter count — see the docstring.
    floor = STATUS_FLOOR.get(status, _DEFAULT_FLOOR)
    if (kb - kw) > floor + 1e-6:
        return {"kind": "en_attente", "reason": "donnees_insuffisantes",
                "span": span, "width": round(kb - kw, 1), "floor": floor}

    central = reserved_letter(site_score_from_subscores(present, methodology))
    # Endpoint letters other than the central one, WORST FIRST. Deterministic: a set literal
    # was iterated here before, which only stayed stable because a 2-letter plage can have at
    # most one such letter. A 3-letter plage has two, so the order has to be defined.
    edges = sorted({g for g in (worst_letter, best_letter) if g != central},
                   key=GRADE_ORDER.index, reverse=True)
    adjacent = edges[0] if len(edges) == 1 else None
    letters = sorted({central, *edges}, key=GRADE_ORDER.index, reverse=True)
    plage = letters[0] if len(letters) == 1 else f"{letters[0]}–{letters[-1]}"
    return {
        "kind": "provisional_band",
        "provisional": True,
        "central": central,          # renorm-point letter — the BIG letter in the loupe
        "edges": edges,              # the other endpoint letters, worst first — the small chips
        "adjacent": adjacent,        # edges[0] when there is exactly one (legacy readers)
        "a_reserved": a_reserved,    # True → the top of the band is an A held reserved (show "A réservé")
        "confidence": confidence or _coverage_confidence(band["n_present"], methodology),
        "band": plage,               # e.g. "C–B" — a RANGE (or a single letter), never a grade field
        "worst": round(kw, 1), "best": round(kb, 1), "span": span,
        "n_present": band["n_present"], "n_base": band["n_base"],
        "label": {"fr": "note provisoire (plage) — se resserre à la livraison",
                  "en": "provisional grade (range) — narrows at delivery"},
    }
