# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Automatic status proof: is an « operational » fiche independently confirmed to run?

Weekly, no human queue (Franck 2026-09-17): signals → calibrated label model → a sidecar
the build reads. Uncertain = ABSTAIN = « statut non vérifié », never a guess. The status
check is note-blind: it never reads or changes a grade.
"""
