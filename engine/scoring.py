# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Dual scoring, confidence and grading.

Missing-data semantics (the transparency floor, pre-mortem R3):

- BASE indicators (context the project endures — public facts): a missing
  datum is OUR collection gap, not the operator's opacity. It is excluded and
  the remaining weights are renormalized; the gap is reported through
  confidence (cause: missing_data), not through the substantive score.
- PROJECT/PROCESS indicators (operator choices and disclosures): a `missing`
  datum — verified absent from a dossier we actually read — counts as 0. Hiding a
  datum can therefore never beat disclosing it. But a `not_collected` datum (nobody
  has looked yet) is NOT a 0: it is dropped from the score and instead lowers
  coverage. A 0 for something we never read would be as false as an A of complacency
  (RED FLAG fix, decision Franck Bardol 2026-07-09). The insufficient_data escape
  (overall pp coverage below parameters.min_coverage, OR no project-block indicator
  looked at) prevents grading an operator on near-zero — or un-examined — information.

Only MVP indicators are scored; tier-3 out-of-MVP indicators are ignored for
both score and confidence.
"""

from datetime import date, timedelta

from .normalize import normalized_score

# Right-of-reply window length (doctrine A-24/A-26). Single source; validate re-exports it.
NOTICE_DAYS = 15

BLOCK_BASE = "base"
BLOCK_PROJECT = "project"
BLOCKS_PROJECT_PROCESS = ("project", "process")
INSUFFICIENT_DATA = "insufficient_data"


def _mvp(methodology: dict) -> list[dict]:
    return [i for i in methodology["indicators"] if i["mvp"]]


def _pillar_weights(methodology: dict) -> dict[str, float]:
    return {p["id"]: p["weight"] for p in methodology["pillars"]}


def _grade(score: float, methodology: dict) -> dict:
    # Graded on the ROUNDED score: the published number and the published letter
    # must never contradict each other (a public "35.0" graded E while the grid
    # says D starts at 35 would be a free shot for any counter-expert).
    # No editorial gloss ("close to X"): the one-decimal score already shows
    # boundary proximity, and any asymmetric wording would dent independence
    # (methodology-lead review 2026-07-05).
    rounded = round(score, 1)
    thresholds = sorted(methodology["grade_thresholds"], key=lambda t: t["min"], reverse=True)
    grade = next(t["grade"] for t in thresholds if rounded >= t["min"])
    return {"grade": grade, "score": rounded}


def _aggregate(scored: dict[str, float | None], definitions: list[dict],
               pillar_weights: dict[str, float]) -> float | None:
    """Two-level weighted mean over the entries that carry a substantive value.
    A None is dropped (renormalized away); the caller pre-encodes a verified-absent
    project/process datum as an explicit 0.0 before aggregating (see `_substantive`)."""
    pillar_scores: dict[str, float] = {}
    for pillar in pillar_weights:
        pairs = [(d["weight_in_pillar"], scored[d["id"]])
                 for d in definitions if d["pillar"] == pillar and scored[d["id"]] is not None]
        if pairs:
            total_w = sum(w for w, _ in pairs)
            pillar_scores[pillar] = sum(w * s for w, s in pairs) / total_w
    if not pillar_scores:
        return None
    total_pw = sum(pillar_weights[p] for p in pillar_scores)
    return sum(pillar_weights[p] * s for p, s in pillar_scores.items()) / total_pw


def _confidence(dc_entries: dict[str, dict], definitions: list[dict],
                pillar_weights: dict[str, float], methodology: dict) -> dict:
    params = methodology["parameters"]
    tier_w = methodology["confidence"]["tier_weights"]
    total = missing = declarative = 0.0
    for d in definitions:
        importance = pillar_weights[d["pillar"]] * d["weight_in_pillar"] * tier_w[str(d["tier"])]
        total += importance
        status = dc_entries[d["id"]]["status"]
        if status in ("missing", "not_collected"):
            missing += importance  # both are data gaps that dent confidence (not the substantive score)
        elif status == "announced":
            declarative += importance
    missing_share = missing / total
    declarative_share = declarative / total
    raw = max(0.0, 1.0 - missing_share - params["declarative_confidence_penalty"] * declarative_share)
    levels = params["confidence_thresholds"]
    level = "high" if raw >= levels["high"] else "medium" if raw >= levels["medium"] else "low"
    return {
        "level": level,
        "score": round(raw, 3),
        "causes": {
            "missing_data": round(missing_share, 3),
            "unverifiable_declarative": round(declarative_share, 3),
        },
    }


_DOC_LABELS = {
    "high": {"fr": "documentation solide", "en": "well documented"},
    "medium": {"fr": "documentation moyenne", "en": "moderately documented"},
    "low": {"fr": "documentation faible", "en": "sparsely documented"},
}

_GRADE_ORDER = "ABCDE"  # index rises with severity (A best, E worst)


def _dots(score: float) -> int:
    """Documentation availability on the 0-4 scorecard scale (the ●●●○ dots).
    A graded thing always shows at least one dot — it was documented enough to grade."""
    if score >= 0.80:
        return 4
    if score >= 0.60:
        return 3
    if score >= 0.40:
        return 2
    return 1


def _documentation(conf: dict) -> dict:
    """Turn a (possibly scoped) confidence result into the public documentation chip:
    the label the badge shows and the dots the scorecard shows. A grade never appears
    without it (product rule n°1: a letter is always coupled with its documentation)."""
    return {
        "level": conf["level"],
        "score": conf["score"],
        "dots": _dots(conf["score"]),
        "label": _DOC_LABELS[conf["level"]],
    }


def _citable_quote(site: dict, project_process: dict, pillar_details: dict, methodology: dict) -> dict:
    """The headline the journalist screenshots — GENERATED, never editorial, so it stays
    opposable: it only makes the contrast claim ('B overall, but E on water') when a graded
    pillar is strictly worse than the site letter; otherwise it states both notes factually.
    No adjectives, same discipline as the grade (no 'close to X')."""
    labels = {p["id"]: p["label"] for p in methodology["pillars"]}
    site_grade = site["grade"]
    graded = {pid: d for pid, d in pillar_details.items() if d["grade"] != INSUFFICIENT_DATA}
    if graded:
        worst_id = max(graded, key=lambda pid: (_GRADE_ORDER.index(graded[pid]["grade"]), -graded[pid]["score"]))
        worst = graded[worst_id]
        if _GRADE_ORDER.index(worst["grade"]) > _GRADE_ORDER.index(site_grade):
            lab = labels[worst_id]
            return {
                "fr": f"Noté {site_grade} sur le site, mais {worst['grade']} sur « {lab['fr']} ».",
                "en": f"Rated {site_grade} on site, but {worst['grade']} on “{lab['en']}”.",
            }
    pp = project_process["grade"]
    if pp == INSUFFICIENT_DATA:
        return {
            "fr": f"Noté {site_grade} sur le site ; données de projet insuffisantes pour une note projet & processus.",
            "en": f"Rated {site_grade} on site; project data insufficient to grade project & process.",
        }
    return {
        "fr": f"Noté {site_grade} sur le site, {pp} en projet & processus.",
        "en": f"Rated {site_grade} on site, {pp} on project & process.",
    }


def score_datacenter(dc: dict, methodology: dict) -> dict:
    """Compute the full scoring result for one data center (pure function, no I/O)."""
    params = methodology["parameters"]
    definitions = _mvp(methodology)
    pillar_weights = _pillar_weights(methodology)
    entries = {e["id"]: e for e in dc["indicators"]}

    per_indicator = {d["id"]: normalized_score(d, entries[d["id"]], params) for d in definitions}

    base_defs = [d for d in definitions if d["block"] == BLOCK_BASE]
    pp_defs = [d for d in definitions if d["block"] in BLOCKS_PROJECT_PROCESS]
    project_defs = [d for d in definitions if d["block"] == BLOCK_PROJECT]

    # Substantive value per indicator (fed to the score aggregate):
    #   base missing / not_collected -> None (dropped, weights renormalized)
    #   project/process `missing`    -> 0.0  (verified absent = opacity; hiding never beats disclosing)
    #   project/process not_collected-> None (nobody looked yet; a 0 would be as false as an A of
    #                                          complacency — decision Franck Bardol, 2026-07-09)
    def _substantive(d: dict) -> float | None:
        s = per_indicator[d["id"]]
        if s is not None:
            return s
        if d["block"] in BLOCKS_PROJECT_PROCESS and entries[d["id"]]["status"] == "missing":
            return 0.0
        return None
    scored = {d["id"]: _substantive(d) for d in definitions}

    site_score = _aggregate(scored, base_defs, pillar_weights)
    site = _grade(site_score, methodology)
    # Per-badge documentation (block-scoped confidence): the site badge is documented
    # by its BASE indicators only, the project badge by its project/process indicators.
    site["documentation"] = _documentation(_confidence(entries, base_defs, pillar_weights, methodology))

    # Coverage = share of pp weight for which we hold a substantive datum (a value or a
    # verified 0). `missing` and `not_collected` both lack one → both lower coverage.
    pp_total_w = sum(pillar_weights[d["pillar"]] * d["weight_in_pillar"] for d in pp_defs)
    pp_filled_w = sum(
        pillar_weights[d["pillar"]] * d["weight_in_pillar"]
        for d in pp_defs if per_indicator[d["id"]] is not None
    )
    coverage = pp_filled_w / pp_total_w
    # "Did we even LOOK at the substantive project core?" A project/process grade may not
    # rest on governance alone: if no project-block indicator has been looked at (all
    # `not_collected`), the operator has not been examined — insufficient_data, never a
    # transparency-floor E drawn from indicators nobody read (RED FLAG fix, 2026-07-09).
    looked_project_w = sum(d["weight_in_pillar"] for d in project_defs
                           if entries[d["id"]]["status"] != "not_collected")
    project_total_w = sum(d["weight_in_pillar"] for d in project_defs)
    project_looked = looked_project_w / project_total_w if project_total_w else 1.0
    if coverage < params["min_coverage"] or project_looked < params["min_coverage"]:
        project_process = {"grade": INSUFFICIENT_DATA, "coverage": round(coverage, 3)}
    else:
        pp_score = _aggregate(scored, pp_defs, pillar_weights)
        project_process = _grade(pp_score, methodology) | {"coverage": round(coverage, 3)}
        project_process["documentation"] = _documentation(_confidence(entries, pp_defs, pillar_weights, methodology))

    # Display sub-score per pillar (public scorecard): same per-block semantics as the
    # aggregate — `scored` already carries pp `missing` as 0 and pp `not_collected` as None.
    with_pp_zeroed = scored
    # The insufficient_data escape CASCADES to sub-scores (methodology-lead
    # review 2026-07-05): a pillar below the coverage floor is never given a
    # punitive letter drawn from unknowns — saying "not enough data to grade
    # the operator" while displaying "local impact: E" would be contradictory
    # and attackable.
    pillar_details = {}
    for pillar in pillar_weights:
        defs = [d for d in definitions if d["pillar"] == pillar]
        total_w = sum(d["weight_in_pillar"] for d in defs)
        filled_w = sum(d["weight_in_pillar"] for d in defs if per_indicator[d["id"]] is not None)
        pillar_coverage = filled_w / total_w
        if pillar_coverage < params["min_coverage"]:
            pillar_details[pillar] = {"grade": INSUFFICIENT_DATA, "coverage": round(pillar_coverage, 3)}
            continue
        combined = _aggregate(with_pp_zeroed, defs, {pillar: 1.0})
        pillar_details[pillar] = _grade(combined, methodology) | {"coverage": round(pillar_coverage, 3)}
        # Per-pillar documentation dots (●●●○): a graded pillar always carries its own
        # documentation availability, scoped to that pillar's indicators.
        pillar_details[pillar]["documentation"] = _documentation(
            _confidence(entries, defs, pillar_weights, methodology)
        )

    return {
        "grades": {"site": site, "project_process": project_process},
        "confidence": _confidence(entries, definitions, pillar_weights, methodology),
        "pillars": pillar_details,
        "citable_quote": _citable_quote(site, project_process, pillar_details, methodology),
        "indicators": {
            d["id"]: None if per_indicator[d["id"]] is None else round(per_indicator[d["id"]], 1)
            for d in definitions
        },
    }


def history_entry_fields(result: dict, methodology: dict) -> dict:
    """The comparable core of a score_history entry (no date, no event, no rationale)."""
    pp = result["grades"]["project_process"]["grade"]
    return {
        "methodology_version": methodology["version"],
        "grades": {"site": result["grades"]["site"]["grade"], "project_process": pp},
        "confidence": result["confidence"]["level"],
    }


def worst_exposed_grade(grades: dict) -> str | None:
    """Most severe LETTER grade across the two head notes (None if neither is a letter).

    `insufficient_data` is not a letter — it never exposes a right-of-reply window.
    """
    letters = [g for g in (grades.get("site"), grades.get("project_process")) if g in _GRADE_ORDER]
    return max(letters, key=_GRADE_ORDER.index) if letters else None


def reply_window_start(score_history: list[dict]) -> str | None:
    """Date the CURRENT D/E right-of-reply window opened, or None if none is required (A-26).

    The window attaches to the *unfavorable note*, not the DC. It opens when the worst head-grade
    enters D/E or worsens within it (≤C→D/E, D→E) and keeps counting while the grade is stable
    (weights-only re-scores never re-open it). Any improvement (E→D, D/E→≤C) closes it — a milder
    or better grade never opens a window. Derived from stored facts only (no `now()`).
    """
    start = None
    prev = None
    for e in score_history:
        w = worst_exposed_grade(e["grades"])
        if w in ("D", "E") and (prev is None or _GRADE_ORDER.index(w) > _GRADE_ORDER.index(prev)):
            start = e["date"]                                  # entered / worsened into D/E → (re)open
        elif prev in ("D", "E") and (w is None or _GRADE_ORDER.index(w) < _GRADE_ORDER.index(prev)):
            start = None                                       # improvement → close the window
        prev = w
    return start


def reply_deadline(notified: str | None) -> str | None:
    """Right-of-reply deadline = notification + NOTICE_DAYS, ISO. Deterministic — never `now()`."""
    return (date.fromisoformat(notified) + timedelta(days=NOTICE_DAYS)).isoformat() if notified else None
