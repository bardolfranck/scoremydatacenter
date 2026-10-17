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


# ── POLARITÉ : une colonne qui ne peut que PÉNALISER ────────────────────────────────────────
# Posé par R&D le 2026-10-17, né d'une mesure : ajouter une colonne à un pilier mince déplaçait
# 121 lettres dont 102 AVEC LA COLONNE VIDE DE SENS — l'arithmétique de renormalisation, pas la
# donnée. L'invariant qui en sort : « une colonne qui ne porte aucune information déplace ZÉRO
# lettre ».
#
# Le porteur est un FAIT DE CONCEPTION déclaré sur l'indicateur — `polarity: "penalty_only"`,
# « cet axe mesure un risque à la baisse, pas un avantage à la hausse » — et le moteur en DÉRIVE
# l'inertie du plafond. On ne liste pas à la main les états inertes : une liste tenue à la main
# dérive de l'intention qu'elle est censée servir.
#
# ⚠️ Le champ est OPT-IN par indicateur, jamais global. Rendre tout neutre inerte d'un coup
# re-noterait le corpus entier en silence — on corrigerait un re-notage accidentel par un
# re-notage massif, exactement le silence qu'on fuit.
PENALTY_ONLY = "penalty_only"


def no_penalty_ceiling(definition: dict) -> float:
    """Le score le plus haut que l'échelle DÉCLARE : l'état « aucune pénalité ».

    Dérivé, jamais listé. Sur une échelle catégorielle {pénalisant …, neutre}, le plafond EST le
    neutre — donc l'inertie se déduit du barème au lieu d'être recopiée à côté de lui.
    Volontairement limité au catégoriel : un indicateur continu n'a pas d'état « neutre »
    identifiable sans convention inventée, et inventer ici produirait une inertie silencieuse
    sur une plage de valeurs. On refuse bruyamment plutôt que de deviner."""
    norm = definition.get("normalization") or {}
    if norm.get("type") != "categorical":
        raise GateError(
            f"GATE 1: indicator {definition['id']}: polarity={PENALTY_ONLY!r} n'est défini que "
            f"pour une normalisation catégorielle (reçu {norm.get('type')!r}) — le plafond "
            f"« aucune pénalité » ne se dérive pas d'une échelle continue"
        )
    return max(float(v) for v in norm["categories"].values())


def is_inert(definition: dict, score: float | None) -> bool:
    """Vrai quand ce score ne doit PAS entrer dans l'agrégat — il n'apporte aucune pénalité.

    La fiche continue de PUBLIER la valeur : inerte veut dire « ne déplace pas la note », pas
    « n'existe pas ». C'est la même discipline que publier un fait à côté d'une note."""
    if score is None or definition.get("polarity") != PENALTY_ONLY:
        return False
    return score >= no_penalty_ceiling(definition)


def normalized_score(definition: dict, entry: dict, parameters: dict) -> float | None:
    """Return the 0-100 sub-score for one indicator entry, or None if it has no value.

    `missing` (verified absent from the public dossier) and `not_collected` (nobody
    has looked yet) both yield None here — the *block-aware* meaning of that None is
    resolved by the scorer: on project/process a `missing` becomes a scored 0 (opacity),
    whereas a `not_collected` is dropped and instead lowers coverage (toward
    insufficient_data). A 0 for something we never looked at would be as false as an
    A of complacency (decision Franck Bardol, 2026-07-09)."""
    if entry["status"] in ("missing", "not_collected"):
        return None
    # UN INDICATEUR INFORMATIONNEL N'A PAS DE SOUS-SCORE, et c'est la doctrine elle-même :
    # « oui » n'y est ni bon ni mauvais. On publie le fait, on ne le note pas. Sortir ici
    # plutôt que plus bas est nécessaire — sa `normalization` vaut `null`, donc lire
    # `norm["type"]` casserait dès qu'une fiche renseigne une valeur.
    if definition.get("informational"):
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
    if entry["status"] in ("announced", "estimated"):
        # estimated (our model output) is bounded by the SAME prudent cap as an operator
        # claim — our own estimate must never look better-documented than a declaration.
        score = min(score, float(parameters["declarative_score_cap"]))
    return score
