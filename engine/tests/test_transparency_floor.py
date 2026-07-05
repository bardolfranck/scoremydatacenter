"""Transparency floor (pre-mortem R3, gate 6): disclosing a datum can NEVER
beat hiding it. Property-tested by hiding every disclosed project/process
indicator of every DC in the corpus and asserting nothing improves."""

import copy

import pytest

from engine.core import load_datacenters
from engine.scoring import score_datacenter

PP_BLOCKS = ("project", "process")


def _pp_score(result):
    pp = result["grades"]["project_process"]
    return None if pp["grade"] == "insufficient_data" else pp["score"]


def _cases():
    datacenters = load_datacenters()
    from engine.core import load_methodology
    methodology = load_methodology()
    pp_ids = {i["id"] for i in methodology["indicators"] if i["mvp"] and i["block"] in PP_BLOCKS}
    for dc_id, dc in datacenters.items():
        for entry in dc["indicators"]:
            if entry["id"] in pp_ids and entry["status"] != "missing":
                yield pytest.param(dc, entry["id"], id=f"{dc_id}:{entry['id']}")


@pytest.mark.parametrize("dc,indicator_id", list(_cases()))
def test_hiding_a_disclosed_datum_never_improves_anything(methodology, dc, indicator_id):
    baseline = score_datacenter(dc, methodology)

    hidden = copy.deepcopy(dc)
    entry = next(e for e in hidden["indicators"] if e["id"] == indicator_id)
    entry.clear()
    entry.update({"id": indicator_id, "status": "missing"})
    result = score_datacenter(hidden, methodology)

    # substantive project/process score: hiding can only lower it (or void it)
    base_pp, hidden_pp = _pp_score(baseline), _pp_score(result)
    if base_pp is not None and hidden_pp is not None:
        assert hidden_pp <= base_pp
    # site score is untouched (base indicators only)
    assert result["grades"]["site"] == baseline["grades"]["site"]
    # confidence can only degrade
    assert result["confidence"]["score"] <= baseline["confidence"]["score"]
    # public pillar sub-scores: hiding never raises any of them
    for pillar, graded in result["pillars"].items():
        base_graded = baseline["pillars"][pillar]
        if "score" in graded and "score" in base_graded:
            assert graded["score"] <= base_graded["score"]
