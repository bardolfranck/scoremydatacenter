# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Generated artifacts — the data contract of the site (and of the future API).

Deterministic by construction: no timestamps, no environment values. The same
repository content always produces byte-identical artifacts (this is tested).
"""

from pathlib import Path

from .core import ARTIFACTS_DIR, write_json
from .scoring import score_datacenter


def _summary(dc: dict, result: dict) -> dict:
    identity = dc["identity"]
    return {
        "id": dc["id"],
        "name": identity["name"],
        "operator": identity["operator"],
        "municipality": identity["municipality"],
        "country": identity["country"],
        "project_status": identity["project_status"],
        "power_mw": identity.get("power_mw"),
        "grades": result["grades"],
        "confidence": result["confidence"],
        "pillars": result["pillars"],
        "citable_quote": result["citable_quote"],
    }


def build_artifacts(datacenters: dict[str, dict], methodology: dict,
                    out_dir: Path = ARTIFACTS_DIR) -> dict[str, dict]:
    """Score every DC and write all artifacts. Returns the per-DC results."""
    results = {dc_id: score_datacenter(dc, methodology) for dc_id, dc in sorted(datacenters.items())}

    labels = {i["id"]: i["label"] for i in methodology["indicators"]}
    scores, features, audit = [], [], []

    for dc_id, dc in sorted(datacenters.items()):
        result = results[dc_id]
        scores.append(_summary(dc, result))

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [dc["identity"]["coordinates"]["lon"], dc["identity"]["coordinates"]["lat"]],
            },
            "properties": {
                "id": dc_id,
                "name": dc["identity"]["name"],
                "grade_site": result["grades"]["site"]["grade"],
                "grade_project_process": result["grades"]["project_process"]["grade"],
                "confidence": result["confidence"]["level"],
                "power_mw": dc["identity"].get("power_mw"),
                "project_status": dc["identity"]["project_status"],
                # A richer popup than two letters: per-pillar grades + the generated
                # citable line (the map teaser that makes people click through).
                "pillars": [{"id": p["id"], "grade": result["pillars"][p["id"]]["grade"]}
                            for p in methodology["pillars"]],
                "quote_fr": result["citable_quote"]["fr"],
            },
        })

        indicator_detail = []
        entries = {e["id"]: e for e in dc["indicators"]}
        for ind in methodology["indicators"]:
            if not ind["mvp"]:
                continue
            entry = entries[ind["id"]]
            indicator_detail.append({
                "id": ind["id"],
                "label": labels[ind["id"]],
                "pillar": ind["pillar"],
                "block": ind["block"],
                "status": entry["status"],
                "value": entry.get("value"),
                "proxies": entry.get("proxies"),
                "score": result["indicators"][ind["id"]],
                "source": entry.get("source"),
                "verification_source": entry.get("verification_source"),
            })

        write_json(out_dir / "dc" / f"{dc_id}.json", {
            **_summary(dc, result),
            "summary": dc["identity"]["summary"],
            "vintage": dc["identity"].get("vintage"),
            "admin_area": dc["identity"].get("admin_area"),
            "indicators": indicator_detail,
            "publication": dc["publication"],
            "score_history": dc["score_history"],
            # Contestation signal (A-21): sourced facts published next to the note,
            # never an input to the grade. Passed through untouched.
            "contestation": dc.get("contestation"),
        })

        audit += [{"dc_id": dc_id, "dc_name": dc["identity"]["name"], **event} for event in dc["score_history"]]

    write_json(out_dir / "scores.json", scores)
    write_json(out_dir / "map.geojson", {"type": "FeatureCollection", "features": features})
    write_json(out_dir / "audit.json", sorted(audit, key=lambda e: (e["date"], e["dc_id"])))
    write_json(out_dir / "methodology.json", methodology)
    return results
