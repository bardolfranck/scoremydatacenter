# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Indicator normalization: raw sourced value -> 0-100 sub-score.

Implements the prudent-declarative rule: an 'announced' (unverified) value can
never contribute above parameters.declarative_score_cap. A 'measured' value on
a declarative indicator is only possible with a verification_source (schema)
and is then uncapped — that is the ex-post re-score.
"""

from .core import GateError


def _thresholds(norm: dict, value: float) -> float:
    above = None
    for step in norm["thresholds"]:
        if step.get("above"):
            above = step["score"]
        elif value <= step["up_to"]:
            return float(step["score"])
    if above is None:
        raise GateError(f"thresholds normalization has no 'above' step for value {value}")
    return float(above)


def _bounded_linear(norm: dict, direction: str, value: float) -> float:
    lo, hi = norm["min"], norm["max"]
    frac = (min(max(value, lo), hi) - lo) / (hi - lo)
    if direction == "lower_is_better":
        frac = 1 - frac
    return 100.0 * frac


def _categorical(norm: dict, value, indicator_id: str) -> float:
    if value not in norm["categories"]:
        raise GateError(
            f"GATE 1: indicator {indicator_id}: value {value!r} is not one of {sorted(norm['categories'])}"
        )
    return float(norm["categories"][value])


def _proxy_rubric(norm: dict, proxies: dict, indicator_id: str) -> float:
    total = 0.0
    for key, points in norm["rubric"].items():
        if key not in proxies:
            raise GateError(f"GATE 1: indicator {indicator_id}: rubric key {key!r} absent from proxies")
        raw = proxies[key]
        if isinstance(raw, bool):
            label = "true" if raw else "false"
        elif isinstance(raw, int):
            label = str(raw) if str(raw) in points else "2_or_more"
        else:
            label = str(raw)
        if label not in points:
            raise GateError(
                f"GATE 1: indicator {indicator_id}: proxy {key}={raw!r} has no rubric entry (keys: {sorted(points)})"
            )
        total += float(points[label])
    return total


def normalized_score(definition: dict, entry: dict, parameters: dict) -> float | None:
    """Return the 0-100 sub-score for one indicator entry, or None if missing."""
    if entry["status"] == "missing":
        return None
    norm = definition["normalization"]
    kind = norm["type"]
    if kind == "thresholds":
        score = _thresholds(norm, entry["value"])
    elif kind == "bounded_linear":
        score = _bounded_linear(norm, definition["direction"], entry["value"])
    elif kind == "categorical":
        score = _categorical(norm, entry["value"], definition["id"])
    elif kind == "proxy_rubric":
        score = _proxy_rubric(norm, entry["proxies"], definition["id"])
    else:  # unreachable if schema validation ran
        raise GateError(f"unknown normalization type {kind!r}")
    if entry["status"] == "announced":
        score = min(score, float(parameters["declarative_score_cap"]))
    return score
