# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Rebuild the PRODUCTION site artifacts from the private newsroom calibration.

Two-repo hazard: `make score` reads the PUBLIC repo (only the zz- test fixtures) and
overwrites site/public/data with those 2 DCs — wiping the real corpus and the
watchlist from the served map. The production DCs (every `datacenters*` panel) and
the "En veille" watchlist live in the newsroom; this rebuilds the served artifacts
from there. Deterministic; no gate run (the calibration holds work-in-progress
drafts) — use `make score` / `make validate` for the public fixtures.

    make prod-artifacts                 # ../smdc-newsroom/calibration
    NEWSROOM_CAL=/path make prod-artifacts
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so `engine` imports when run as a file

from engine.artifacts import build_artifacts
from engine.core import ARTIFACTS_DIR, load_datacenters, load_methodology, load_watchlist

CAL = Path(os.environ.get("NEWSROOM_CAL", Path(__file__).resolve().parent.parent.parent / "smdc-newsroom" / "calibration"))

# Media env (HMAC secret + public base URL) lives OUTSIDE both repos —
# ~/.smdc/media.env — loaded here so `make prod-artifacts` just works.
_MEDIA_ENV = Path.home() / ".smdc" / "media.env"
if _MEDIA_ENV.is_file():
    for line in _MEDIA_ENV.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def patch_satellite_images() -> int:
    """Brief 9-img-sat: every fiche artifact gets its satellite_image
    {url, thumb, credit} — URL derived from the frozen id + HMAC secret
    (A-28 non-enumerable keys). Only when the media env is configured;
    the engine build and the golden never see this."""
    secret = os.environ.get("SMDC_MEDIA_SECRET")
    base = (os.environ.get("SMDC_MEDIA_BASE") or "").rstrip("/")
    if not secret or not base:
        return 0
    from engine.core import write_json
    from pipelines.media.satellite import media_key
    patched = 0
    for f in sorted((ARTIFACTS_DIR / "dc").glob("*.json")):
        d = json.loads(f.read_text())
        if d["id"].startswith("zz-"):
            continue
        key = media_key(d["id"], secret)
        d["satellite_image"] = {
            "url": f"{base}/{key}",
            "thumb": f"{base}/{key.replace('.webp', '-thumb.webp')}",
            "credit": "Esri, Maxar, Earthstar Geographics",
        }
        write_json(f, d)
        patched += 1
    return patched


def main() -> int:
    if not (CAL / "datacenters").is_dir():
        raise SystemExit(f"newsroom calibration not found at {CAL} — clone smdc-newsroom or set NEWSROOM_CAL")
    dcs = load_datacenters(CAL)          # every datacenters* panel (FR, BE, …)
    # The zz- fixtures NEVER ship to production (Franck 2026-07-17): they are
    # internal plumbing for CI and the public clone (`make score`), not
    # something visitors should meet. Prod = the real corpus only.
    dcs = {k: v for k, v in dcs.items() if not k.startswith("zz-")}
    watchlist = load_watchlist(CAL)      # "En veille" 🗣️ layer
    results = build_artifacts(dcs, load_methodology(), out_dir=ARTIFACTS_DIR, watchlist=watchlist)
    # Purge stale per-DC artifacts (build_artifacts writes, never deletes):
    # anything on disk that is not in this corpus would silently resurrect
    # as a fiche page — the exact leak this script must prevent.
    stale = [f for f in (ARTIFACTS_DIR / "dc").glob("*.json") if f.stem not in dcs]
    for f in stale:
        f.unlink()
    if stale:
        print(f"prod-artifacts: purged {len(stale)} stale fiche artifact(s): " + ", ".join(f.stem for f in stale))
    de = sorted(i for i, r in results.items()
                if {r["grades"]["site"]["grade"], r["grades"]["project_process"]["grade"]} & {"D", "E"})
    print(f"prod-artifacts: {len(dcs)} DC + {len(watchlist)} watchlist entries → {ARTIFACTS_DIR}")
    print(f"prod-artifacts: exposure — {len(de)} DC(s) at D/E: " + (", ".join(de) if de else "none"))
    patched = patch_satellite_images()
    if patched:
        print(f"prod-artifacts: satellite_image patched on {patched} fiches (media env configured)")
    else:
        print("prod-artifacts: satellite_image skipped (SMDC_MEDIA_SECRET/BASE not set — see ~/.smdc/media.env)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
