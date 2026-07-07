# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Assemble a *governance sidecar* for one site — voie A, official documents, France.

    python -m pipelines.press.collect --lat 48.599 --lon 2.806 --name "..." \
        --out <newsroom>/drafts/datacenters

Output = <id>.governance.json next to the spatial draft. It carries:
  * proposed_t1_proxies — the DETERMINISTIC proxies pre-filled and sourced (cndp_referral,
    legal_appeals_count over judged cases); the judgment-bearing ones left null with a lead.
  * review_leads — the exact documents to open for the null proxies and for T2.
It is a PROPOSAL, never a publication, and it is NEVER written into the scored record: T1 requires
all five proxies, and three of them need a human/LLM to read a PDF. The reviewer transfers the
validated proxies into the draft's T1 by hand. Nothing here is a score; nothing here is fabricated.
"""

import argparse
import json
import sys
from datetime import date

from pipelines.spatial.http import SourceUnavailable
from pipelines.spatial import sources as spatial
from pipelines.spatial.collect import _slugify
from . import sources
from .archive import archive_url


# The two proxies this pipeline can establish deterministically today; the other three need the
# review leads. Kept explicit so the sidecar always states the split honestly.
_DETERMINISTIC = ("cndp_referral", "legal_appeals_count")
_NEEDS_REVIEW = ("public_inquiry_held", "environmental_authority_opinion", "council_deliberations")

_CAVEATS = [
    "Appeal direction: a project generates appeals in both directions (developer vs. commune "
    "preemption ≠ opponents vs. project authorizations). legal_appeals_count is judged-only and "
    "undirected — confirm each dossier before scoring.",
    "CNDP absence is not proof: the saisines dataset is punctual (~2 snapshots/yr) and referral is "
    "threshold-based (R.121-2 industrial-equipment cost); a pending decree may change it. Confirm "
    "recent projects via the debatpublic.fr overlay.",
    "Environmental-authority tenor: an MRAe avis is observations, not favorable/unfavorable — that "
    "enum shape belongs to the commissaire-enquêteur's inquiry conclusion. Read the PDF; do not "
    "force a verdict (methodology recalibration pending, phase 5).",
    "Coverage bias is a confidence signal, never a zero: a commune with no local press or portal "
    "is not a commune without contestation.",
]


def collect(lat: float, lon: float, *, name: str | None, accessed: str, archive: bool = True) -> dict:
    """Return the governance sidecar dict for the point (raises if the geocoder is unreachable).

    archive=True triggers a durable web-archive snapshot of rot-prone public *pages* (the CNDP
    debate fiche) and records it as `source.archived_url` (A-20). Best-effort: an archive failure
    never blocks the draft. Pass archive=False for offline/fast runs.
    """
    commune = spatial.fetch_commune(lat, lon)  # shared backbone
    commune_name = commune["nom"]
    insee = commune["code"]
    dept = commune.get("codeDepartement")
    slug = _slugify(name or "") or _slugify(commune_name)
    dc_id = f"fr-{slug}"

    cndp = sources.collect_cndp(commune_name, dept, accessed)
    appeals = sources.collect_appeals_judged(commune_name, dept, accessed)
    leads = sources.gather_leads(commune_name, insee, dept, cndp)

    # Pin the evidence (A-20). Only the CNDP fiche — a specific, rot-prone public page — is worth a
    # snapshot; the open-data court query stays re-fetchable (link, don't copy). The iter-1 LLM stage
    # will archive the avis / inquiry-conclusion PDFs the same way once it has resolved their URLs.
    if archive and cndp and cndp.get("cndp_referral"):
        snapshot = archive_url((cndp.get("source") or {}).get("url"))
        if snapshot:
            cndp["source"]["archived_url"] = snapshot

    proposed = {
        "cndp_referral": cndp["cndp_referral"] if cndp else None,
        "legal_appeals_count": appeals["legal_appeals_count"] if appeals else None,
        "public_inquiry_held": None,            # → review_leads.prefecture_publications
        "environmental_authority_opinion": None,  # → review_leads.mrae_search (read the PDF)
        "council_deliberations": None,          # → review_leads.town_hall_site
    }
    deterministic_sources = {}
    if cndp:
        deterministic_sources["cndp_referral"] = cndp
    if appeals:
        deterministic_sources["legal_appeals_count"] = appeals

    unreached = [k for k in _DETERMINISTIC if proposed[k] is None]
    return {
        "draft_of": dc_id,
        "generator": "pipelines.press v1 (voie A — official documents, FR)",
        "generated_at": accessed,
        "commune": {"name": commune_name, "insee": insee, "departement": dept},
        "coordinates_input": {"lat": lat, "lon": lon},
        # A SUGGESTION for the draft's T1 proxies object — not scored, not schema-injected here.
        # The reviewer validates each field, fills the null ones from the leads, then updates T1.
        "proposed_t1_proxies": proposed,
        "deterministic_sources": deterministic_sources,
        "needs_human_or_llm": list(_NEEDS_REVIEW),
        "review_leads": leads,
        # T2 (documentation transparency) is a human call from what the leads reveal is online.
        "proposed_t2": None,
        "t2_note": "Set full_dossier_online / partial / minimal / unavailable from whether the "
                   "dossier is reachable (registry + prefecture + impact-study aggregator leads).",
        "deterministic_unreached": unreached,
        "caveats": _CAVEATS,
        "review_required": True,
        "warning": "Pipeline proposes, it does not publish. The press points, the registry proves. "
                   "Human validation is mandatory before any proxy enters the draft's T1/T2.",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Voie-A governance sidecar from GPS coordinates.")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--name", default=None, help="Project name (for the draft id / CNDP matching aid).")
    p.add_argument("--out", default=None,
                   help="Directory to write <id>.governance.json into (default: stdout).")
    p.add_argument("--no-archive", action="store_true",
                   help="Skip the web-archive snapshot of the CNDP fiche (offline/fast runs).")
    args = p.parse_args(argv)

    accessed = date.today().isoformat()
    try:
        sidecar = collect(args.lat, args.lon, name=args.name, accessed=accessed,
                          archive=not args.no_archive)
    except SourceUnavailable as exc:
        print(f"ERROR: backbone geocoder unavailable — cannot place the point. {exc}", file=sys.stderr)
        return 2

    text = json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        from pathlib import Path
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{sidecar['draft_of']}.governance.json"
        path.write_text(text)
        print(f"Wrote governance sidecar → {path}", file=sys.stderr)
    else:
        sys.stdout.write(text)

    proposed = sidecar["proposed_t1_proxies"]
    got = {k: v for k, v in proposed.items() if v is not None and k in _DETERMINISTIC}
    print(f"Deterministic proxies filled: {got}", file=sys.stderr)
    print(f"Left for human/LLM review: {sidecar['needs_human_or_llm']}", file=sys.stderr)
    print("Review required before any proxy enters the circuit.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
