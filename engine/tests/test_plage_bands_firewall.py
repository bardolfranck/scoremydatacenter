# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Firewall — a coverage band may be SERVED on a pipeline (« en veille ») fiche, but must
never touch the DEFINITIVE grade of an operational fiche.

Franck validated serving a PUBLIC provisional band on pipeline projects (labelled
provisional). So `engine.plage_bands` is no longer forbidden everywhere — the artifact
builder may attach a band. The invariant is refined, NOT dropped:

  (A) Static — the DEFINITIVE-grade computation must stay band-free. `scoring.py`,
      `normalize.py`, `score.py` compute the published letter; if any imported plage_bands
      a band could feed the real grade. They must never import it.

  (B) Behavioural — the single serving gate `servable_band()` enforces the display rules:
      - operational (any non-pipeline) status -> None: NEVER a band (definitive letter only);
      - pipeline + non-credible (> 2 adjacent letters) -> « en veille » marker, no letter;
      - pipeline + credible (<= 2 adjacent letters) -> a provisional band object that carries
        NO bare `grade` key, so it can never be slotted into `grades.site.grade`.

Together: a band can reach the public build ONLY through `servable_band`, ONLY on a pipeline
fiche, ONLY when credible, and ALWAYS in a provisional-typed object distinct from a grade.
"""

import ast
import json
from pathlib import Path

from engine.core import load_methodology
from engine.plage_bands import servable_band, PIPELINE_STATUSES

ENGINE = Path(__file__).resolve().parent.parent
REPO = ENGINE.parent

# (A) Modules that compute the DEFINITIVE grade — must never import the band util.
DEFINITIVE_GRADE_MODULES = [
    ENGINE / "scoring.py",
    ENGINE / "normalize.py",
    ENGINE / "score.py",
]


def _imports_plage_bands(path: Path) -> bool:
    if not path.exists():
        return False
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "plage_bands" in node.module:
            return True
        if isinstance(node, ast.Import) and any("plage_bands" in a.name for a in node.names):
            return True
    return False


def test_definitive_grade_path_never_imports_plage_bands():
    offenders = [p.name for p in DEFINITIVE_GRADE_MODULES if _imports_plage_bands(p)]
    assert not offenders, (
        "coverage-band util imported by a DEFINITIVE-grade module: "
        f"{offenders}. The published letter must be computed by score_datacenter alone — "
        "a provisional band must never be able to feed grades.site.grade."
    )


# (B) The serving gate behaviour — the contract the artifact builder relies on.
_METHO = load_methodology()

# A rich present-set (structural gaps small) → a credible band.
_RICH = {"E1": 30.0, "E2": 70.0, "E3": 65.0, "W1": 60.0, "W2": 80.0, "W3": 65.0,
         "F1": 70.0, "F2": 100.0, "L1": 60.0, "L3": 100.0}
# A thin present-set (many structural gaps) → a wide, non-credible band.
_THIN = {"E1": 30.0, "W1": 60.0}


def test_operational_fiche_never_gets_a_band():
    for op_status in ("operational", "decommissioned", "unknown", None):
        assert servable_band(op_status, _RICH, "FR", _METHO, None) is None, (
            f"status {op_status!r} is not pipeline yet servable_band returned a band — "
            "an operational fiche must keep its definitive letter, never a band."
        )


def test_pipeline_credible_returns_a_provisional_object_without_a_grade_key():
    out = servable_band("announced", _RICH, "FR", _METHO, None)
    assert out is not None and out["kind"] == "provisional_band"
    assert out.get("provisional") is True
    # crucial: no bare `grade`/`grade_site` key that could be slotted into a definitive field
    assert "grade" not in out and "grade_site" not in out, (
        "a provisional band must not carry a definitive-grade key — it could be published "
        "as a real letter."
    )
    # loupe display contract: central (big) + adjacent (small) letters
    assert out["central"] in {"A", "B", "C", "D", "E"}, "central must be a letter"
    assert out["adjacent"] is None or out["adjacent"] in {"A", "B", "C", "D", "E"}
    assert out["adjacent"] != out["central"], "adjacent must differ from central (or be None)"
    assert out["confidence"] in {"low", "medium", "high"}
    assert "–" in out["band"], "a band is a RANGE (e.g. B–C), never a single letter"


def test_confidence_passthrough_wins_over_the_coverage_proxy():
    out = servable_band("announced", _RICH, "FR", _METHO, None, confidence="high")
    assert out["confidence"] == "high"


def test_pipeline_noncredible_returns_en_attente_not_a_letter():
    out = servable_band("announced", _THIN, "FR", _METHO, None)
    assert out is not None and out["kind"] == "en_attente"
    assert "grade" not in out and "band" not in out and "central" not in out, (
        "a non-credible pipeline fiche shows « en_attente », never a letter or a band."
    )


def test_pipeline_statuses_are_exactly_the_provisional_set():
    # guards against a status silently gaining/losing band-eligibility
    assert PIPELINE_STATUSES == frozenset({"announced", "permitting", "under_construction"})
