"""Dual scoring, confidence and grading.

Missing-data semantics (the transparency floor, pre-mortem R3):

- BASE indicators (context the project endures — public facts): a missing
  datum is OUR collection gap, not the operator's opacity. It is excluded and
  the remaining weights are renormalized; the gap is reported through
  confidence (cause: missing_data), not through the substantive score.
- PROJECT/PROCESS indicators (operator choices and disclosures): a missing
  datum counts as 0. Hiding a datum can therefore never beat disclosing it —
  disclosing anything scores >= 0. This is what makes the transparency-floor
  property hold by construction. The insufficient_data escape (coverage below
  parameters.min_coverage_project_process) prevents grading an operator on
  near-zero information.

Only MVP indicators are scored; tier-3 out-of-MVP indicators are ignored for
both score and confidence.
"""

from .normalize import normalized_score

BLOCK_BASE = "base"
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
    rounded = round(score, 1)
    thresholds = sorted(methodology["grade_thresholds"], key=lambda t: t["min"], reverse=True)
    margin = methodology["parameters"]["borderline_margin"]
    grade = next(t["grade"] for t in thresholds if rounded >= t["min"])
    result = {"grade": grade, "score": rounded}
    better = [t for t in thresholds if t["min"] > rounded]
    if better and (better[-1]["min"] - rounded) <= margin:
        result["close_to"] = better[-1]["grade"]
    return result


def _aggregate(per_indicator: dict[str, float | None], definitions: list[dict],
               pillar_weights: dict[str, float], missing_counts_as_zero: bool) -> float | None:
    """Two-level weighted mean. Missing entries are either dropped (base) or scored 0 (project/process)."""
    pillar_scores: dict[str, float] = {}
    for pillar, weight in pillar_weights.items():
        defs = [d for d in definitions if d["pillar"] == pillar]
        if not defs:
            continue
        pairs = []
        for d in defs:
            s = per_indicator[d["id"]]
            if s is None:
                if missing_counts_as_zero:
                    pairs.append((d["weight_in_pillar"], 0.0))
            else:
                pairs.append((d["weight_in_pillar"], s))
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
        if status == "missing":
            missing += importance
        elif status == "announced":
            declarative += importance
    missing_share = missing / total
    declarative_share = declarative / total
    raw = 1.0 - missing_share - params["declarative_confidence_penalty"] * declarative_share
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


def score_datacenter(dc: dict, methodology: dict) -> dict:
    """Compute the full scoring result for one data center (pure function, no I/O)."""
    params = methodology["parameters"]
    definitions = _mvp(methodology)
    pillar_weights = _pillar_weights(methodology)
    entries = {e["id"]: e for e in dc["indicators"]}

    per_indicator = {d["id"]: normalized_score(d, entries[d["id"]], params) for d in definitions}

    base_defs = [d for d in definitions if d["block"] == BLOCK_BASE]
    pp_defs = [d for d in definitions if d["block"] in BLOCKS_PROJECT_PROCESS]

    site_score = _aggregate(per_indicator, base_defs, pillar_weights, missing_counts_as_zero=False)
    site = _grade(site_score, methodology)

    pp_total_w = sum(pillar_weights[d["pillar"]] * d["weight_in_pillar"] for d in pp_defs)
    pp_filled_w = sum(
        pillar_weights[d["pillar"]] * d["weight_in_pillar"]
        for d in pp_defs if per_indicator[d["id"]] is not None
    )
    coverage = pp_filled_w / pp_total_w
    if coverage < params["min_coverage_project_process"]:
        project_process = {"grade": INSUFFICIENT_DATA, "coverage": round(coverage, 3)}
    else:
        pp_score = _aggregate(per_indicator, pp_defs, pillar_weights, missing_counts_as_zero=True)
        project_process = _grade(pp_score, methodology) | {"coverage": round(coverage, 3)}

    # Display sub-score per pillar (public scorecard): same per-block semantics —
    # missing base data is dropped, missing project/process data counts as 0.
    with_pp_zeroed = {
        d["id"]: (0.0 if per_indicator[d["id"]] is None and d["block"] in BLOCKS_PROJECT_PROCESS
                  else per_indicator[d["id"]])
        for d in definitions
    }
    pillar_details = {}
    for pillar in pillar_weights:
        defs = [d for d in definitions if d["pillar"] == pillar]
        if not any(per_indicator[d["id"]] is not None for d in defs):
            # Nothing known at all about this pillar: we do not grade pure absence
            # (the opacity-counts-as-zero rule needs at least one disclosed datum).
            pillar_details[pillar] = {"grade": INSUFFICIENT_DATA}
            continue
        combined = _aggregate(with_pp_zeroed, defs, {pillar: 1.0}, missing_counts_as_zero=False)
        if combined is not None:
            pillar_details[pillar] = _grade(combined, methodology)

    return {
        "grades": {"site": site, "project_process": project_process},
        "confidence": _confidence(entries, definitions, pillar_weights, methodology),
        "pillars": pillar_details,
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
