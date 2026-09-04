# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Veille — daily detection of NEW data-centre projects → candidate drafts (NO grade) → digest.

Flow B of the WORKFLOW, operationalised for a daily cadence (Franck 2026-07-28). The cron
DETECTS + ENRICHES + builds a DIGEST and deposits it privately; it NEVER deploys, NEVER
publishes a grade, NEVER sends mail (the send leg is CF-side, agent-codeur-site's key).

en-veille doctrine (A-19/A-21): sourced facts only, no score/confidence, `state: "en_veille"`.
License doctrine: every candidate carries `provenance` (real licence id + `publishable`); a
commercial-origin lead is `publishable: false` until re-verified against an OPEN source.
"""
