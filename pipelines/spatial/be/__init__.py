# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Belgium tier-1 spatial adapter (v0) — EU-recon probe of 2026-07-09 turned into code.

Same contract as the French pipeline: coordinates in, sourced draft fragment out, zero scores.
Coverage v0 (see README.md): E1, E2 national via Elia; W2, F1, F2, L3 via the Walloon one-stop
ArcGIS (geoservices.wallonie.be) with EEA fallbacks for Flanders/Brussels. Known gaps carried
honestly: E3 (no public connection queue), W1 (no machine drought feed found), W3 (withdrawal
volumes patchy), L1 (raw Statbel value in provenance only — FR bands not transposable).
"""
