# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""indices.json + indices_history.json — country SITE index (brief 2026-07-18/19).

The five laws, encoded:
1. kind is ALWAYS "site_index" (an operator index will be a distinct artifact).
2. A country grade never travels without its documentation; the ONLY floor is
   n >= 5 published site scores (documentation is displayed, never a filter).
3. The A-25 reserve lives INSIDE the aggregation: score >= 80 with no
   third-party verification anywhere in the country -> grade B,
   reserved_from "A", real score kept. Never a display-time patch.
4. equal_weight is the default; mw_weighted is emitted ONLY where local MW
   labels exist (>= 5 sites with known MW), always NEXT TO equal_weight;
   sensitivity_delta stays null until the run-1 estimator exists.
5. Editorial labels are {fr, en} objects and always say SITE.
6. The perimeter is stated, never hidden: every published site score enters
   the mean (announced sites included — the site score measures the
   territory); n_operational / n_announced are emitted for the footer.

History (§1 bis): append-only; an index EVENT is only a grade change, a
reserve flip, an eligibility flip, or a new country. The continuous score
drifts at every build and lives in indices.json, never in the history.
Deterministic: dates come from the corpus (its freshest source access date),
never from a clock — two builds on the same corpus emit identical bytes
(golden + idempotence gates).
"""

import json
from pathlib import Path

from collections import Counter

SCHEMA_VERSION = "1.0"
MIN_N = 5
DOC_BANDS = [(0.75, "solide"), (0.5, "moyenne"), (0.0, "faible")]
LABELS = {
    "title": {"fr": "Indice SITE — ce que les territoires offrent",
              "en": "SITE index — what the territories offer"},
}

_PIPELINE_STATUSES = ("announced", "permitting", "under_construction")


def _corpus_date(sites: list[dict]) -> str | None:
    # The corpus's freshest information date — MAX over BOTH score_history and
    # source.accessed (their UNION), never one-or-the-other. The old
    # "score_history else accessed" short-circuited on a handful of scored FR
    # DCs (dated 2026-07-19) and ignored 5900+ sources freshly accessed on
    # 2026-07-21 when a new country batch landed — dating the whole index two
    # days stale. Deterministic (still corpus-derived, no clock); golden safe.
    dates = [e.get("date") for dc in sites for e in dc.get("score_history", []) if e.get("date")]
    dates += [src["accessed"] for dc in sites for entry in dc["indicators"]
              if isinstance((src := entry.get("source")), dict) and src.get("accessed")]
    return max(dates) if dates else None


def _grade_for(score: float, thresholds: list[dict]) -> str:
    for t in sorted(thresholds, key=lambda x: -x["min"]):
        if score >= t["min"]:
            return t["grade"]
    return thresholds[-1]["grade"]


def _doc_band(median: float) -> str:
    for floor, band in DOC_BANDS:
        if median >= floor:
            return band
    return "faible"


def _median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return round(s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2, 3)


def _country_has_verification(sites: list[dict]) -> bool:
    """A-25: third-party operational proof anywhere in the country."""
    return any(entry.get("verification_source")
               for dc in sites for entry in dc["indicators"])


def build_indices(datacenters: dict[str, dict], methodology: dict,
                  results: dict[str, dict]) -> dict:
    """The site_index artifact — computed by the ENGINE at build, never front-side."""
    thresholds = methodology["grade_thresholds"]
    sites = [dc for dc_id, dc in sorted(datacenters.items()) if not dc_id.startswith("zz-")]
    by_country: dict[str, list[dict]] = {}
    for dc in sites:
        by_country.setdefault(dc["identity"]["country"], []).append(dc)

    countries: dict[str, dict] = {}
    for cc, c_sites in sorted(by_country.items()):
        scored = [(dc, results[dc["id"]]) for dc in c_sites if dc["id"] in results]
        published = [(dc, r) for dc, r in scored
                     if isinstance(r["grades"]["site"].get("score"), (int, float))]
        n = len(published)
        if n < MIN_N:
            # Law 2: below the floor, no mean is a mean — no score is emitted.
            countries[cc] = {"n": n, "eligible": False}
            continue

        scores = [r["grades"]["site"]["score"] for _, r in published]
        score = round(sum(scores) / n, 1)
        grade = _grade_for(score, thresholds)
        reserved_from = None
        if grade == "A" and not _country_has_verification(c_sites):
            # Law 3 — the A-25 reserve INSIDE the aggregation, never at display.
            grade, reserved_from = "B", "A"

        # « doc site » = the SITE-axis documentation score (grades.site.
        # documentation.score), NOT the global documentary confidence — the
        # §1 ter reconciliation gate caught exactly this divergence on run 1.
        doc_median = _median([r["grades"]["site"]["documentation"]["score"] for _, r in published])
        statuses = Counter(dc["identity"]["project_status"] for dc, _ in published)

        entry = {
            "n": n,
            "aggregation": "equal_weight",
            "score": score,
            "grade": grade,
            "reserved_from": reserved_from,
            "documentation": {"median": doc_median, "band": _doc_band(doc_median)},
            "eligible": True,
            "n_operational": statuses.get("operational", 0),
            "n_announced": sum(statuses.get(s, 0) for s in _PIPELINE_STATUSES),
        }

        mw_pairs = [(dc["identity"]["power_mw"], r["grades"]["site"]["score"])
                    for dc, r in published
                    if isinstance(dc["identity"].get("power_mw"), (int, float))
                    and dc["identity"]["power_mw"] > 0]
        if len(mw_pairs) >= MIN_N:
            total_mw = sum(mw for mw, _ in mw_pairs)
            entry["mw_weighted"] = {
                "score": round(sum(mw * sc for mw, sc in mw_pairs) / total_mw, 1),
                "n_mw_known": len(mw_pairs),
                "sensitivity_delta": None,  # run-1 estimator (separate brief)
            }
        countries[cc] = entry

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "site_index",
        "labels": LABELS,
        "methodology_version": methodology["version"],
        # Deterministic: the corpus's own date, never a build clock (golden +
        # §1 bis idempotence gates would both break on now()).
        "computed_at": _corpus_date(sites),
        "credit": "scoremydatacenter.org · data: licence by source (ODbL, Licence Ouverte…) · methodology CC BY-SA 4.0",
        "countries": countries,
    }


def _state_of(entry: dict) -> dict:
    return {
        "grade": entry.get("grade"),
        "reserved_from": entry.get("reserved_from"),
        "eligible": entry.get("eligible", False),
    }


def update_history(indices: dict, history_path: Path) -> list[dict]:
    """Append-only §1 bis: one event per REAL move (grade change, reserve flip,
    eligibility flip, new country). Same corpus twice -> identical file."""
    history: list[dict] = []
    if history_path.is_file():
        history = json.loads(history_path.read_text())

    last: dict[str, dict] = {}
    known: set[str] = set()
    for ev in history:
        known.add(ev["country"])
        last[ev["country"]] = ev["to"]

    date = indices["computed_at"]
    events: list[dict] = []
    for cc, entry in sorted(indices["countries"].items()):
        now = _state_of(entry)
        to = {**now, "score": entry.get("score"), "n": entry["n"]}
        if cc not in known:
            events.append({"country": cc, "date": date, "event": "new_country",
                           "from": {"grade": None}, "to": to, "cause": "first_publication"})
            continue
        prev = last[cc]
        prev_state = {"grade": prev.get("grade"), "reserved_from": prev.get("reserved_from"),
                      "eligible": prev.get("eligible", False)}
        if prev_state == now:
            continue
        if prev_state["eligible"] != now["eligible"]:
            event = "eligibility_change"
        elif prev_state["grade"] != now["grade"]:
            event = "grade_change"
        else:
            event = "reserve_change"
        events.append({"country": cc, "date": date, "event": event,
                       "from": prev_state, "to": to, "cause": "recompute"})

    return history + events
