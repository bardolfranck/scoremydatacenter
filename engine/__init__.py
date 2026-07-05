# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""ScoreMyDataCenter scoring engine.

Turns data/datacenters/*.json + a pinned methodology version into the
published artifacts (scores.json, map.geojson, dc/*.json, audit.json).
Scores exist only as build outputs — never as hand-edited inputs.
"""

__version__ = "0.0.1"
