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


def registry_display_name(denomination: str) -> str:
    """« T D F (TDF) » → « TDF », « BLUE (BLUE) » → « BLUE », « DATAONE FRANCE SAS » → « DATAONE FRANCE »:
    the register's legal denomination, made readable without inventing anything."""
    import re
    parts = [x.strip() for x in re.findall(r"\(([^)]*)\)", denomination)]
    main = re.sub(r"\s*\([^)]*\)", "", denomination).strip()
    if parts and re.fullmatch(r"(?:\S )+\S", main):   # spaced initials → use the sigle
        main = parts[0]
    return re.sub(r"\s+(SAS|SASU|SA|SARL|EURL)$", "", main).strip()


def apply_operator_identity(dcs: dict) -> dict:
    """Operator-fill (Franck go 2026-09-17): a fiche whose operator is unknown takes the company the
    French register resolves with CONFIDENCE (weekly job, pipelines/status_proof/siren.py). Only the
    `confident` tier; developer candidates / lower tiers never fill. Returns {id: source} for the
    fiche artifact's provenance link."""
    sidecar = CAL / "status-proof" / "operator_identity.json"
    if not sidecar.is_file():
        return {}
    sources = {}
    for dc_id, e in json.loads(sidecar.read_text()).get("fiches", {}).items():
        dc = dcs.get(dc_id)
        if not dc or e.get("emit_tier") != "confident" or not (e.get("resolved") or {}).get("denomination"):
            continue
        if str(dc["identity"].get("operator") or "").strip().lower() not in ("", "unknown", "none"):
            continue
        siren_id = e["resolved"]["siren"]
        dc["identity"]["operator"] = registry_display_name(e["resolved"]["denomination"])
        sources[dc_id] = {"source": "SIRENE", "siren": siren_id,
                          "url": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren_id}",
                          "checked_at": e.get("checked_at")}
    return sources


def patch_operator_source(sources: dict) -> None:
    from engine.core import write_json
    for dc_id, src in sources.items():
        f = ARTIFACTS_DIR / "dc" / f"{dc_id}.json"
        if f.is_file():
            d = json.loads(f.read_text())
            d["operator_source"] = src
            write_json(f, d)


def patch_status_check() -> int:
    """Status proof (Franck 2026-09-17): every OPERATIONAL fiche artifact gets its
    status_check {verified, checked_at, evidence?} from the weekly sidecar written by
    `make status-proof`. Only the public verdict travels — the internal live_signal /
    demote candidates never reach a served file. No sidecar → nothing added (the fiche
    shows no status label rather than a wrong one)."""
    sidecar = CAL / "status-proof" / "status_check.json"
    if not sidecar.is_file():
        return 0
    from engine.core import write_json
    checks = json.loads(sidecar.read_text()).get("fiches", {})
    patched = 0
    for f in sorted((ARTIFACTS_DIR / "dc").glob("*.json")):
        d = json.loads(f.read_text())
        c = checks.get(d["id"])
        if d.get("project_status") != "operational" or not c or c.get("verdict") not in ("verified", "unverified"):
            d.pop("status_check", None)
        else:
            d["status_check"] = {
                "verified": c["verdict"] == "verified",
                "checked_at": c.get("checked_at"),
                **({"evidence": {k: c["evidence"][k] for k in ("source", "url", "networks")}}
                   if c["verdict"] == "verified" and c.get("evidence") else {}),
            }
            patched += 1
        write_json(f, d)
    return patched


def main() -> int:
    if not (CAL / "datacenters").is_dir():
        raise SystemExit(f"newsroom calibration not found at {CAL} — clone smdc-newsroom or set NEWSROOM_CAL")
    dcs = load_datacenters(CAL)          # every datacenters* panel (FR, BE, …)
    # The zz- fixtures NEVER ship to production (Franck 2026-07-17): they are
    # internal plumbing for CI and the public clone (`make score`), not
    # something visitors should meet. Prod = the real corpus only.
    # `study-` is the A-19 firewall belt-and-suspenders (R&D, 2026-09-06): the internal
    # precursor-validation cohort lives in a SEPARATE corpus (validation/, never read here) —
    # this prefix drop is the second lock, so a study fiche mistakenly copied into a
    # datacenters* panel still can NEVER be served with a real grade.
    dcs = {k: v for k, v in dcs.items() if not k.startswith(("zz-", "study-"))}
    watchlist = load_watchlist(CAL)      # "En veille" 🗣️ layer
    operator_sources = apply_operator_identity(dcs)
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
    patch_operator_source(operator_sources)
    print(f"prod-artifacts: operator filled from the company register on {len(operator_sources)} fiches")
    checked = patch_status_check()
    print(f"prod-artifacts: status_check on {checked} operational fiches"
          if checked else "prod-artifacts: status_check skipped (no status-proof sidecar — run make status-proof)")
    patched = patch_satellite_images()
    if patched:
        print(f"prod-artifacts: satellite_image patched on {patched} fiches (media env configured)")
    else:
        print("prod-artifacts: satellite_image skipped (SMDC_MEDIA_SECRET/BASE not set — see ~/.smdc/media.env)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
