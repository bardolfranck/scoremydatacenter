"""Ethical lock (framing note section 9), executable: for every indicator
constrained by vulnerability_cannot_improve_score, moving any DC to a MORE
vulnerable category must never raise its site score — signed monotonicity
d(site_score)/d(vulnerability) <= 0, property-tested on the whole corpus
(same pattern as the transparency floor)."""

import copy
import itertools

import pytest

from engine.core import load_datacenters, load_methodology
from engine.scoring import score_datacenter


def _constrained_indicators(methodology):
    return [i for i in methodology["indicators"]
            if "vulnerability_cannot_improve_score" in i.get("constraints", [])]


def _cases():
    methodology = load_methodology()
    for dc_id, dc in load_datacenters().items():
        for ind in _constrained_indicators(methodology):
            order = ind["vulnerability_order"]
            for less, more in itertools.combinations(order, 2):  # order = least -> most vulnerable
                yield pytest.param(dc, ind["id"], less, more, id=f"{dc_id}:{ind['id']}:{less}->{more}")


def _site_score_with(dc, methodology, indicator_id, category):
    variant = copy.deepcopy(dc)
    entry = next(e for e in variant["indicators"] if e["id"] == indicator_id)
    entry.clear()
    entry.update({
        "id": indicator_id,
        "value": category,
        "status": "measured",
        "source": {"title": "property-test probe", "url": "https://example.org", "accessed": "2026-07-01"},
    })
    return score_datacenter(variant, methodology)["grades"]["site"]["score"]


@pytest.mark.parametrize("dc,indicator_id,less_vulnerable,more_vulnerable", list(_cases()))
def test_more_vulnerability_never_raises_site_score(methodology, dc, indicator_id,
                                                    less_vulnerable, more_vulnerable):
    score_less = _site_score_with(dc, methodology, indicator_id, less_vulnerable)
    score_more = _site_score_with(dc, methodology, indicator_id, more_vulnerable)
    assert score_more <= score_less, (
        f"{dc['id']}: making {indicator_id} more vulnerable ({less_vulnerable} -> {more_vulnerable}) "
        f"raised the site score {score_less} -> {score_more} — ethical lock violated"
    )


def test_l1_carries_the_executable_lock(methodology):
    l1 = next(i for i in methodology["indicators"] if i["id"] == "L1")
    assert l1["constraints"] == ["vulnerability_cannot_improve_score"]
    assert l1["vulnerability_order"] == ["strong_fit", "neutral", "sensitive"]
