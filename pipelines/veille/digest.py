# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""The daily veille DIGEST — a self-contained HTML page + manifest over candidate drafts.

The digest is the human gate's surface: Franck reads it, reacts in the chat ("accepte A, B ;
corrige C"). It is NOT the site — it is a private daily email body. The send leg is CF-side
(agent-codeur-site's Resend key); this module only RENDERS + writes a manifest, and the driver
deposits both in the private newsroom.

Two hard invariants, checked before anything renders (`validate_candidate`):
  1. NO grade / score / confidence anywhere — en-veille is sourced FACTS only (A-19/A-21).
  2. every candidate carries `provenance{source,url,license,publishable}` — the licence tag that
     conditions what the site may ever render (a commercial lead is `publishable:false`).
A candidate that violates either never reaches the digest; it is reported, not shipped.
"""

import html
import json
from datetime import datetime, timezone

# Keys that would smuggle a judgement into an en-veille card. Belt-and-braces with the schema's
# additionalProperties:false — the digest is generated prose, so it gets its own gate. NOT "note":
# provenance.note is a legitimate free-text field in the schema (a licence caveat), not a grade —
# banning the bare key would reject a valid commercial-lead caveat. The judgement risk is the
# structural keys below, never a field literally named "note".
_FORBIDDEN_KEYS = {"grade", "grades", "score", "scores", "confidence", "pillars"}

STATUS_FR = {
    "announced": "Annoncé", "permitting": "En instruction",
    "under_construction": "En construction", "operational": "En service",
}


def validate_candidate(c: dict) -> list[str]:
    """Return the reasons this candidate must NOT ship (empty = clean)."""
    problems = []
    bad = _FORBIDDEN_KEYS & set(_walk_keys(c))
    if bad:
        problems.append(f"{c.get('id','?')}: forbidden judgement key(s) {sorted(bad)} — en-veille is facts-only")
    if c.get("state") != "en_veille":
        problems.append(f"{c.get('id','?')}: state must be 'en_veille', got {c.get('state')!r}")
    p = c.get("provenance") or {}
    for req in ("source", "license", "publishable"):
        if req not in p:
            problems.append(f"{c.get('id','?')}: provenance.{req} is required")
    if not c.get("facts"):
        problems.append(f"{c.get('id','?')}: no sourced facts — an en-veille entry is nothing without them")
    return problems


def _walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_keys(v)


def build_manifest(candidates: list[dict], date: str) -> dict:
    """The tiny index the CF sender reads: subject line + per-candidate id/name/publishable."""
    n = len(candidates)
    n_pub = sum(1 for c in candidates if (c.get("provenance") or {}).get("publishable"))
    return {
        "date": date,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": n,
        "digest_html": "digest.html",
        "subject": f"Veille SMDC — {n} projet(s) détecté(s) le {date}"
                   + ("" if n_pub == n else f" ({n - n_pub} lead(s) à re-vérifier)"),
        "candidates": [
            {
                "id": c["id"], "name": c.get("name"), "municipality": c.get("municipality"),
                "publishable": bool((c.get("provenance") or {}).get("publishable")),
            }
            for c in candidates
        ],
    }


def _e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _fact_li(f: dict) -> str:
    label = (f.get("label") or {}).get("fr") or (f.get("label") or {}).get("en") or ""
    src = f.get("source") or {}
    url = src.get("url") if isinstance(src, dict) else None
    cite = (src.get("title") if isinstance(src, dict) else src) or url or ""
    link = f' — <a href="{_e(url)}">{_e(cite)}</a>' if url else (f" — {_e(cite)}" if cite else "")
    tag = ' <span class="self">auto-déclaré</span>' if f.get("self_reported") else ""
    return f"<li>{_e(label)}{tag}{link}</li>"


def _tier1_li(ind: dict) -> str:
    src = (ind.get("source") or {}).get("title") if isinstance(ind.get("source"), dict) else ""
    tail = f' <span class="src">{_e(src)}</span>' if src else ""
    return f"<li><b>{_e(ind.get('id'))}</b> = {_e(ind.get('value'))}{tail}</li>"


def _card(c: dict) -> str:
    prov = c.get("provenance") or {}
    publishable = bool(prov.get("publishable"))
    det = c.get("detection") or {}
    dd = det.get("dedup") or {}
    coords = c.get("coordinates") or {}
    place = " · ".join(x for x in (c.get("municipality"), STATUS_FR.get(c.get("project_status"), c.get("project_status"))) if x)
    facts = "".join(_fact_li(f) for f in (c.get("facts") or []))
    t1 = c.get("tier1_preview") or []
    t1_block = (
        '<div class="t1"><span class="t1h">Contexte spatial tier-1 — <em>brut, NON NOTÉ</em></span>'
        f'<ul>{"".join(_tier1_li(i) for i in t1)}</ul></div>'
    ) if t1 else '<div class="t1 muted">Contexte tier-1 : en attente de géocodage</div>'
    lead_banner = "" if publishable else (
        '<div class="lead-banner">⚠️ LEAD — source commerciale, non re-vérifiée en source ouverte : '
        'NON PUBLIABLE en l\'état. À confirmer contre une source ouverte avant toute mise en veille.</div>'
    )
    dedup_line = (
        f'proche d\'un projet connu (<code>{_e(dd.get("nearest_id"))}</code>, {_e(dd.get("distance_km"))} km)'
        if dd.get("status") == "near_known" else "aucun projet connu à proximité"
    )
    src = c.get("source") or {}
    coords_txt = f'{coords.get("lat")}, {coords.get("lon")}' if coords else "—"
    return f"""
    <article class="card {'pub' if publishable else 'lead'}">
      {lead_banner}
      <header>
        <h3>{_e(c.get('name'))}</h3>
        <div class="sub">{_e(c.get('operator'))}{' · ' + _e(place) if place else ''}</div>
      </header>
      <ul class="facts">{facts}</ul>
      {t1_block}
      <div class="meta">
        <span class="pill">{'publiable' if publishable else 'lead — non publiable'}</span>
        <span>licence : <b>{_e(prov.get('license'))}</b></span>
        <span>détecté : {_e(det.get('feed'))} · {_e(det.get('detected_at'))}</span>
        <span>dédup : {dedup_line}</span>
        <span>coord. : {_e(coords_txt)}</span>
        {f'<span>source : <a href="{_e(src.get("url"))}">{_e(src.get("title") or src.get("url"))}</a></span>' if src.get('url') else ''}
      </div>
      <div class="act">Pour accepter en veille : réponds dans le chat « accepte {_e(c.get('id'))} ».</div>
    </article>"""


def render_digest(candidates: list[dict], date: str) -> str:
    """Self-contained HTML digest. Groups NEW first, then near-known. No grade anywhere."""
    problems = [p for c in candidates for p in validate_candidate(c)]
    if problems:
        raise ValueError("digest refused — candidates violate en-veille invariants:\n  - " + "\n  - ".join(problems))
    new = [c for c in candidates if (c.get("detection") or {}).get("dedup", {}).get("status") != "near_known"]
    known = [c for c in candidates if (c.get("detection") or {}).get("dedup", {}).get("status") == "near_known"]

    def section(title, items, note):
        if not items:
            return ""
        return f'<section><h2>{_e(title)} <span class="count">{len(items)}</span></h2><p class="note">{_e(note)}</p>{"".join(_card(c) for c in items)}</section>'

    body = section("Nouveaux projets détectés", new,
                   "Aucun projet connu à proximité — candidats à une entrée « en veille ».") \
        + section("Signaux proches d'un projet déjà connu", known,
                  "Vérifier s'il s'agit du même site (mise à jour) ou d'un projet distinct.")
    if not body:
        body = '<p class="empty">Aucun nouveau projet détecté aujourd\'hui.</p>'

    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Veille ScoreMyDataCenter — {_e(date)}</title>
<style>
  body{{margin:0;background:#f6f8fb;color:#1c2733;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
  .wrap{{max-width:760px;margin:0 auto;padding:24px}}
  .top{{border-bottom:2px solid #d7e0ea;padding-bottom:12px;margin-bottom:8px}}
  .top h1{{font-size:20px;margin:0}} .top .d{{color:#5b6b7c;font-size:13px}}
  .disclaimer{{background:#eef3f8;border:1px solid #d7e0ea;border-radius:8px;padding:10px 12px;font-size:13px;color:#3a4a5a;margin:12px 0}}
  h2{{font-size:16px;margin:26px 0 4px}} .count{{background:#33475c;color:#fff;border-radius:10px;padding:1px 8px;font-size:12px;vertical-align:middle}}
  .note{{color:#5b6b7c;font-size:13px;margin:0 0 12px}}
  .card{{background:#fff;border:1px solid #e2e9f0;border-radius:10px;padding:14px 16px;margin:12px 0;box-shadow:0 1px 2px rgba(20,40,60,.04)}}
  .card.lead{{border-color:#e6b8a0;background:#fffaf6}}
  .card h3{{margin:0;font-size:16px}} .sub{{color:#5b6b7c;font-size:13px;margin-top:2px}}
  .facts{{margin:10px 0;padding-left:18px}} .facts li{{margin:3px 0}}
  .self{{background:#eceff3;border-radius:4px;padding:0 5px;font-size:11px;color:#5b6b7c}}
  .t1{{background:#f3f7fb;border-radius:8px;padding:8px 10px;margin:8px 0;font-size:13px}}
  .t1h{{color:#3a4a5a;font-size:12px;text-transform:uppercase;letter-spacing:.03em}} .t1 ul{{margin:6px 0 0;padding-left:18px}} .t1 .src{{color:#8494a4;font-size:11px}}
  .t1.muted{{color:#8494a4;font-style:italic}}
  .meta{{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12px;color:#5b6b7c;border-top:1px dashed #e2e9f0;padding-top:8px;margin-top:8px}}
  .pill{{background:#e4efe6;color:#2f6b3a;border-radius:4px;padding:0 6px;font-weight:600}}
  .card.lead .pill{{background:#f6dfd2;color:#a2542a}}
  .lead-banner{{background:#f6dfd2;color:#8a3d17;border-radius:6px;padding:8px 10px;font-size:13px;font-weight:600;margin-bottom:10px}}
  .act{{margin-top:10px;font-size:13px;color:#33475c;background:#f3f7fb;border-radius:6px;padding:6px 10px}}
  code{{background:#eceff3;border-radius:3px;padding:0 4px;font-size:12px}}
  .empty{{color:#5b6b7c;text-align:center;padding:40px}}
  a{{color:#2a5d8f}}
</style></head><body><div class="wrap">
  <div class="top"><h1>Veille — nouveaux projets data center</h1>
    <div class="d">ScoreMyDataCenter · France · {_e(date)}</div></div>
  <div class="disclaimer"><b>Projets suivis, pas encore notés.</b> Faits sourcés uniquement, aucune note
    d'acceptabilité n'est calculée ici (doctrine « en veille » A-19/A-21). Le contexte tier-1 affiché est
    <b>brut et non noté</b>. Tu valides dans le chat ; la mise en veille et l'éventuelle notation restent des étapes ultérieures.</div>
  {body}
  <p class="note" style="margin-top:28px">Digest généré automatiquement — détection + enrichissement, sans publication ni envoi automatique de note.</p>
</div></body></html>"""


if __name__ == "__main__":
    import sys
    cands = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else []
    date = datetime.now(timezone.utc).date().isoformat()
    print(render_digest(cands, date))
