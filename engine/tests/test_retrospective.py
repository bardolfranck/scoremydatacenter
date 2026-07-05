"""Retrospective fixtures (gate 6): known-outcome cases must land in their
expected grade range on every build. 'Ne jamais publier un score que la
validation rétrospective n'a pas confirmé.'"""

import json
from pathlib import Path

import pytest

from engine.core import load_datacenters
from engine.scoring import score_datacenter

CASES = json.loads((Path(__file__).parent / "retrospective_cases.json").read_text())["cases"]


@pytest.mark.parametrize("dc_id", sorted(CASES))
def test_known_outcome_case_stays_in_range(methodology, dc_id):
    dc = load_datacenters()[dc_id]
    result = score_datacenter(dc, methodology)
    expected = CASES[dc_id]
    assert result["grades"]["site"]["grade"] in expected["site"], (
        f"{dc_id}: site grade left its retrospective range — recalibrate before publishing"
    )
    assert result["grades"]["project_process"]["grade"] in expected["project_process"]


def test_every_datacenter_has_a_retrospective_range():
    assert sorted(CASES) == sorted(load_datacenters()), (
        "every DC in the corpus must carry a pinned retrospective range"
    )
