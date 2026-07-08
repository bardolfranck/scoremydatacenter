# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""The pipeline orchestrator — chain the collection bricks up to ONE human gate (A-22).

Two flows, both stopping at a single human validation gate; nothing downstream publishes without
it (A-07). See WORKFLOW.md for the full runbook.

  onboard   coords → spatial tier-1 → governance (voie A) → contestation candidates (voie B, matched
            by proximity to a pre-harvested signal) → review queue → BUNDLE in the private newsroom.
  refresh   re-harvest the signal → review queue for the delta → BUNDLE.
  promote   read the human-approved queue → apply it (write contestation[] / watchlist, add
            archived_url). Still not a public publish — that is the contradictoire PR (A-11).

Reuses pipelines.spatial + pipelines.press. Stdlib only. It PROPOSES and stages; it never scores and
never publishes to the public repo.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from pipelines.spatial.http import haversine_m
from pipelines.spatial.collect import collect as spatial_collect
from pipelines.press.collect import collect as governance_collect
from pipelines.press import collect_signal, review
from pipelines.press.archive import archive_url


# --- proximity match: contestation entries near a DC (from a pre-harvested signal) -----------

def match_contestation(lat: float, lon: float, radius_km: float, signal_path: Path | None) -> list[dict]:
    """Return watchlist review items whose point falls within radius_km of the DC (or [] if no signal)."""
    if not signal_path or not Path(signal_path).exists():
        return []
    fc = json.loads(Path(signal_path).read_text())
    hits = []
    for f in fc.get("features") or []:
        geom = f.get("geometry") or {}
        coords = geom.get("coordinates") if geom.get("type") == "Point" else None
        if not coords:
            continue
        if haversine_m(lat, lon, coords[1], coords[0]) <= radius_km * 1000:
            hits.append(review.review_feature(f))     # reduce + flag, same scaffold as the signal review
    return hits


# --- flow A: onboard a DC to score -----------------------------------------------------------

def onboard(lat: float, lon: float, *, name: str, operator: str, power_mw: float | None,
            project_status: str, accessed: str, signal_path: Path | None = None,
            radius_km: float = 25.0) -> dict:
    """Chain spatial → governance → contestation-match → review queue. Returns the bundle (no publish)."""
    fragment, provenance, skipped = spatial_collect(
        lat, lon, name=name, operator=operator, power_mw=power_mw,
        project_status=project_status, accessed=accessed)
    governance = governance_collect(lat, lon, name=name, accessed=accessed, archive=False)
    contestation_queue = match_contestation(lat, lon, radius_km, signal_path)
    return {
        "dc_id": fragment["id"],
        "generated_at": accessed,
        "fragment": fragment,                # tier-1 indicators draft (spatial)
        "provenance": provenance,
        "governance": governance,            # voie-A sidecar (CNDP/appeals + review leads)
        "contestation_review": contestation_queue,  # voie-B candidates near the DC, to validate
        "human_gate": "pending",             # nothing proceeds until a human validates
        "warning": "Bundle for review. Nothing here is scored or published. Human validation "
                   "mandatory before promotion; public publication is the separate contradictoire PR.",
    }


def write_bundle(bundle: dict, out_dir: Path) -> Path:
    """Write the per-DC bundle into the private newsroom (draft, governance, review queue, HTML sheet)."""
    dc_dir = out_dir / bundle["dc_id"]
    dc_dir.mkdir(parents=True, exist_ok=True)
    (dc_dir / f"{bundle['dc_id']}.draft.json").write_text(
        json.dumps(bundle["fragment"], indent=2, ensure_ascii=False) + "\n")
    (dc_dir / f"{bundle['dc_id']}.provenance.json").write_text(
        json.dumps(bundle["provenance"], indent=2, ensure_ascii=False) + "\n")
    (dc_dir / f"{bundle['dc_id']}.governance.json").write_text(
        json.dumps(bundle["governance"], indent=2, ensure_ascii=False) + "\n")
    with (dc_dir / "contestation.review.jsonl").open("w") as fh:
        for item in bundle["contestation_review"]:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    (dc_dir / "review.html").write_text(render_review_html(bundle["contestation_review"], bundle["dc_id"]))
    return dc_dir


# --- flow B: refresh the contestation signal -------------------------------------------------

def refresh_signal(accessed: str, *, gdelt_query: str | None = None) -> list[dict]:
    """Re-harvest the open feeds → a review queue (facts only). Returns the queue (no publish)."""
    watchlist, _press, _counts = collect_signal.harvest(accessed, gdelt_query=gdelt_query)
    fc = collect_signal._to_geojson(watchlist)
    return review.build_queue(fc["features"])


# --- promote: apply the human-approved queue (still not a public publish) ---------------------

def promote_contestation(review_items: list[dict], *, archive: bool = True) -> list[dict]:
    """Turn APPROVED review items into contestation[] entries (A-21 shape), adding archived_url (A-20).

    Only items whose `decision` is 'approve' are promoted (the human sets it in the JSONL). Nothing
    without an explicit approval is ever emitted — silence is not consent.
    """
    out = []
    for item in review_items:
        if item.get("decision") != "approve":
            continue
        entry = item["proposed"]
        for fact in entry.get("facts", []):
            fact.pop("_label_status", None)              # internal flag, not part of the published shape
            if archive and fact.get("source", {}).get("url") and "archived_url" not in fact["source"]:
                snap = archive_url(fact["source"]["url"])
                if snap:
                    fact["source"]["archived_url"] = snap
        out.append(entry)
    return out


def approved_contestation_facts(review_items: list[dict], *, archive: bool = True) -> list[dict]:
    """Flatten APPROVED review entries into DC `contestation[]` items {kind,label,source,self_reported}."""
    facts = []
    for entry in promote_contestation(review_items, archive=archive):
        for f in entry.get("facts", []):
            facts.append({k: f[k] for k in ("kind", "label", "source", "self_reported") if k in f})
    return facts


def promote_into_dc(dc: dict, review_items: list[dict], *, archive: bool = True) -> dict:
    """THE LAST MILE — write the human-approved contestation facts into the DC file's `contestation[]`.

    This is what closes the loop to the site: the confirmed facts land in the scored record so the
    engine renders them. Governance T1/T2 are completed by the human directly on the DC at the gate
    (deterministic CNDP/appeals + the 3 judgment proxies read from the leads) — never auto-scored.
    Returns the updated DC dict; the caller writes it and re-scores.
    """
    dc = dict(dc)
    facts = approved_contestation_facts(review_items, archive=archive)
    if facts:
        dc["contestation"] = (dc.get("contestation") or []) + facts
    return dc


# --- best-effort static HTML review sheet (P3: no server) ------------------------------------

def render_review_html(queue: list[dict], title: str) -> str:
    """A tiny static sheet to eyeball a DC's contestation points. Decisions still land in the JSONL."""
    def esc(s):
        return (str(s) if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    rows = []
    for item in queue:
        p = item["proposed"]
        facts = p.get("facts") or []
        fact_html = "".join(
            f"<li><b>{esc(f.get('kind'))}</b>: {esc((f.get('label') or {}).get('fr'))}"
            + (f" · <a href='{esc(f['source'].get('url'))}' target='_blank' rel='noopener'>source</a>" if f.get('source', {}).get('url') else "")
            + (f" · <a href='{esc(f['source'].get('archived_url'))}' target='_blank' rel='noopener'>archivé</a>" if f.get('source', {}).get('archived_url') else "")
            + (" · <i>auto-déclaré</i>" if f.get("self_reported") else "")
            + "</li>" for f in facts) or "<li><i>aucun fait de contestation (entrée projet)</i></li>"
        flags = ", ".join(esc(x) for x in item.get("flags") or []) or "—"
        rows.append(
            f"<tr><td>{esc(p.get('name'))}</td><td>{esc(p.get('country'))}</td>"
            f"<td><ul>{fact_html}</ul></td><td>{flags}</td><td>{esc(item.get('route'))}</td>"
            f"<td class='dec'>{esc(item.get('decision') or '—')}</td></tr>")
    return (
        "<!doctype html><meta charset='utf-8'><title>Revue — " + esc(title) + "</title>"
        "<style>body{font:14px system-ui;margin:2rem;max-width:1100px}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px;vertical-align:top;text-align:left}"
        "ul{margin:0;padding-left:1.1em}.dec{font-weight:600}h1{font-size:1.2rem}"
        ".note{background:#fffbe6;border:1px solid #e8d97a;padding:8px;border-radius:6px}</style>"
        f"<h1>Revue de contestation — {esc(title)}</h1>"
        "<p class='note'>Faits sourcés, <b>aucune note</b>. Viewer en lecture — la décision "
        "(approve/edit/reject) se pose dans <code>contestation.review.jsonl</code>. Rien n'est publié ici.</p>"
        "<table><thead><tr><th>Projet</th><th>Pays</th><th>Faits</th><th>Drapeaux</th>"
        "<th>Route</th><th>Décision</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>")


# --- CLI -------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ScoreMyDataCenter pipeline orchestrator (A-22).")
    sub = p.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("onboard", help="Chain spatial+governance+contestation for one DC → bundle.")
    o.add_argument("--lat", type=float, required=True)
    o.add_argument("--lon", type=float, required=True)
    o.add_argument("--name", default="UNKNOWN — to fill")
    o.add_argument("--operator", default="UNKNOWN — to fill")
    o.add_argument("--power-mw", type=float, default=None)
    o.add_argument("--project-status", default="announced",
                   choices=["announced", "permitting", "under_construction", "operational"])
    o.add_argument("--signal", default=None, help="Path to a harvested watchlist.draft.geojson to match against.")
    o.add_argument("--radius-km", type=float, default=25.0)
    o.add_argument("--out", default="../smdc-newsroom/drafts/datacenters")

    r = sub.add_parser("refresh", help="Re-harvest the signal → review queue.")
    r.add_argument("--gdelt-query", default=None)
    r.add_argument("--out", default="../smdc-newsroom/drafts/watchlist")

    pr = sub.add_parser("promote", help="Apply a human-approved contestation review queue.")
    pr.add_argument("review_jsonl", help="Path to the reviewed contestation.review.jsonl (decision set).")
    pr.add_argument("--into", default=None,
                    help="DC draft json to WRITE the approved contestation[] into (the last mile). "
                         "Without it, the approved facts are printed only.")
    pr.add_argument("--no-archive", action="store_true")

    args = p.parse_args(argv)
    accessed = date.today().isoformat()

    if args.cmd == "onboard":
        bundle = onboard(args.lat, args.lon, name=args.name, operator=args.operator,
                         power_mw=args.power_mw, project_status=args.project_status, accessed=accessed,
                         signal_path=(Path(args.signal) if args.signal else None), radius_km=args.radius_km)
        dc_dir = write_bundle(bundle, Path(args.out))
        n = len(bundle["contestation_review"])
        print(f"Bundle → {dc_dir}  (tier-1 draft + governance + {n} contestation candidate(s) + review.html)",
              file=sys.stderr)
        print("🚦 Human gate: review contestation.review.jsonl (set decision), complete T1 from the "
              "governance leads, then `promote`. Nothing is published.", file=sys.stderr)
        return 0

    if args.cmd == "refresh":
        queue = refresh_signal(accessed, gdelt_query=args.gdelt_query)
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / "watchlist.review.jsonl").open("w") as fh:
            for item in queue:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
        (out_dir / "watchlist.review.html").write_text(render_review_html(queue, "watchlist (signal)"))
        print(f"Review queue ({len(queue)}) → {out_dir}. 🚦 Human gate before promotion.", file=sys.stderr)
        return 0

    if args.cmd == "promote":
        items = [json.loads(l) for l in Path(args.review_jsonl).read_text().splitlines() if l.strip()]
        approved = sum(1 for i in items if i.get("decision") == "approve")
        if args.into:                                    # the last mile: write into the DC file
            dc_path = Path(args.into)
            dc = json.loads(dc_path.read_text())
            dc = promote_into_dc(dc, items, archive=not args.no_archive)
            dc_path.write_text(json.dumps(dc, indent=2, ensure_ascii=False) + "\n")
            print(f"Wrote {len(dc.get('contestation', []))} contestation fact(s) into {dc_path} "
                  f"({approved} approved of {len(items)}). Re-score to render on the site.",
                  file=sys.stderr)
        else:
            promoted = promote_contestation(items, archive=not args.no_archive)
            sys.stdout.write(json.dumps(promoted, indent=2, ensure_ascii=False) + "\n")
            print(f"Promoted {len(promoted)} approved of {len(items)} reviewed "
                  f"(rest held: silence ≠ consent). Pass --into <dc.json> to write them in.",
                  file=sys.stderr)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
