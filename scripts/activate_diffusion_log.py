# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Activate the diffusion log at the REAL production deploy (covariable §10).

Run ONCE, by hand, as a step of the deploy runbook — NOT from build_prod_artifacts (which
runs on every branch/test build and would stamp dates prematurely). Stamps
`first_public_band_date` on every sealed-cohort member with the deploy date (idempotent:
an already-stamped member is left untouched, so re-running is safe).

    python scripts/activate_diffusion_log.py            # stamps today
    python scripts/activate_diffusion_log.py 2026-09-08 # stamps a given date

Reminder (from the log's own caveat): the mass same-date stamp is CONSTANT across the
cohort → no stratification power. The discriminating covariate is `record_amplification`
(third-party press pickups), traced continuously by the veille — not this stamp.
"""

import sys
from datetime import date

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from scripts.diffusion_log import load, stamp_public_band  # noqa: E402


def main(argv) -> int:
    when = argv[0] if argv else date.today().isoformat()
    log = load()
    ids = list(log["entries"])
    before = sum(1 for e in log["entries"].values() if e["first_public_band_date"])
    for site_id in ids:
        stamp_public_band(site_id, when)
    after_log = load()
    after = sum(1 for e in after_log["entries"].values() if e["first_public_band_date"])
    print(f"diffusion log: stamped date {when} on {after - before} member(s) "
          f"(already stamped: {before}); cohort size {len(ids)}; activated={after_log['activated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
