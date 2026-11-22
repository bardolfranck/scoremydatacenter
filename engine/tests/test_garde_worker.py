# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le garde anti-aspiration du Worker (site/worker/garde.ts, décision Franck 2026-11-22) est
testé en TypeScript avec `node --test`. Ce test l'embarque dans `make test`, donc dans le
filet qui précède chaque déploiement : un garde qui ne bloque plus, ou qui bloque un lecteur
ordinaire, arrête la mise en ligne."""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / "site" / "worker" / "garde.test.ts"


@pytest.mark.skipif(shutil.which("node") is None, reason="node absent")
def test_le_garde_du_worker_tient_ses_regles():
    r = subprocess.run(["node", "--test", str(TESTS)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]
