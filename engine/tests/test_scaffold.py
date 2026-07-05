"""Phase 0 smoke tests — the real test suite (gates, transparency floor,
retrospective fixtures, golden files) arrives in phase 1."""

from engine import score, validate


def test_validate_passes_on_scaffold():
    assert validate.main() == 0


def test_score_passes_on_scaffold():
    assert score.main() == 0
