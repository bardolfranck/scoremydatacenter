# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Diffusion-log recorder — covariable §10 of the leading-indicator pre-registration.

ARMED, NOT ACTIVATED. The log (`smdc-newsroom/validation/diffusion_log.json`) timestamps,
per sealed-cohort member, when its fiche starts showing a PUBLIC band and every third-party
AMPLIFICATION (press/DCmag pickup). These are the covariates that let the T0+18m analysis
STRATIFY the precursor effect against reactivity (a published grade possibly CAUSING the
contestation it predicts).

Nothing here writes a date on its own. `stamp_public_band` is called BY THE DEPLOY that
first serves a public band; `record_amplification` is called by the veille when it detects a
press pickup. Until then every date is null and `activated` is false.

⚠️ Statistical caveat (do not paper over it): if the whole cohort passes to a public band on
the SAME deploy date, `first_public_band_date` is CONSTANT across the cohort → it gives NO
stratification variance. The covariate that actually varies — and that carries the real
reactivity signal — is `amplification` (third-party pickups differ per project). Stratify on
amplification, not on the mass display switch.
"""

import json
from pathlib import Path

LOG_PATH = (Path(__file__).resolve().parent.parent.parent
            / "smdc-newsroom" / "validation" / "diffusion_log.json")


def load(path: Path = LOG_PATH) -> dict:
    return json.loads(path.read_text())


def _save(log: dict, path: Path = LOG_PATH) -> None:
    path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")


def stamp_public_band(site_id: str, date: str, path: Path = LOG_PATH) -> None:
    """Record the FIRST date a cohort member's fiche showed a public band (idempotent:
    never overwrites an earlier stamp). Flips `activated` true on first use."""
    log = load(path)
    e = log["entries"].get(site_id)
    if e is None:
        return  # not a sealed-cohort member → nothing to stratify
    if e["first_public_band_date"] is None:
        e["first_public_band_date"] = date
        log["activated"] = True
        _save(log, path)


def record_amplification(site_id: str, date: str, source: str, url: str,
                         path: Path = LOG_PATH) -> None:
    """Append a dated third-party amplification (press/DCmag) for a cohort member."""
    log = load(path)
    e = log["entries"].get(site_id)
    if e is None:
        return
    e["amplification"].append({"date": date, "source": source, "url": url})
    log["activated"] = True
    _save(log, path)


if __name__ == "__main__":
    log = load()
    stamped = sum(1 for e in log["entries"].values() if e["first_public_band_date"])
    amp = sum(len(e["amplification"]) for e in log["entries"].values())
    print(f"diffusion_log: {len(log['entries'])} cohort members, activated={log['activated']}, "
          f"band-stamped={stamped}, amplification events={amp}")
