# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Synthesis redaction — the post-scoring WORKFLOW phase (A-22, stage 3).

Turns a *scored* DC into its narrative `synthesis` and writes it back onto the source DC, so the
engine passes it through on every rebuild (never computed at render). Orthogonal to country: it reads
each DC's own measured indicators + normalised scores — no hard-coded per-country assumption. Built to
scale to 10k DCs: deterministic prompt + validation, one pluggable model call, idempotent batch.

Determinism lives here; only the prose is delegated. The model call is a seam (`llm`) so the LLM owner
plugs their client in without this module hard-wiring a vendor. Every output is validated against the
engine's Gate 7 (no grade letter in prose) and the editorial bans BEFORE it is written — an invalid
draft never lands on a source file.

    from pipelines.synthesize import synthesize_panel
    synthesize_panel(source_dir, artifacts_dir, llm=my_client)   # writes synthesis onto sources

CLI:  python -m pipelines.synthesize --source <dir> --artifacts <dir> [--force]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable

from engine.artifacts import synthesis_grade_citations  # Gate 7 (prose): the single source of truth

LLM = Callable[[str], str]

# Editorial bans (analyst tone, no legal-attack framing) — see calibration/SYNTHESIS-GENERATION.md.
BANNED = ["mauvais", "scandaleu", "inacceptable", "catastroph", "désastr", "honteu",
          "ils cachent", "ils négligent", "militant"]

# project_process withheld → one honest, country-neutral statement (no model call needed).
FIXED_PROJECT = {
    "lead": "En attente de documentation",
    "fr": ("Les éléments propres au projet et à son processus — efficacité annoncée, engagements sur "
           "l'eau et l'énergie, concertation, transparence du dossier — ne sont pas encore documentés "
           "au seuil requis. La note projet & processus n'est donc pas attribuée : sous le seuil de "
           "couverture, l'observatoire écrit « données insuffisantes » plutôt que de noter l'inconnu."),
    "en": ("The project- and process-specific elements — announced efficiency, water and energy "
           "commitments, public consultation, dossier transparency — are not yet documented to the "
           "required threshold. The project & process grade is therefore withheld: below the coverage "
           "threshold, the observatory writes “insufficient data” rather than grading the unknown."),
}


def _band(score) -> str:
    """Engine-consistent reading of a normalised indicator score (senseBand)."""
    if score is None:
        return "n/a"
    if score >= 66:
        return "favorable"
    if score >= 40:
        return "nuancé"
    return "contrainte"


def measured_signals(scored: dict) -> list[dict]:
    """The site's measured indicators with their normalised reading — the only ground for the prose."""
    out = []
    for ind in scored.get("indicators", []):
        if ind.get("status") != "measured" or ind.get("score") is None:
            continue
        # Site axis = what the project inherits: base indicators (+ measured process/transparency).
        if ind.get("block") not in ("base", "process"):
            continue
        out.append({
            "id": ind["id"],
            "label": (ind.get("label") or {}).get("fr", ind["id"]),
            "value": ind.get("value"),
            "score": ind.get("score"),
            "reading": _band(ind.get("score")),
        })
    return out


def build_prompt(source: dict, scored: dict) -> str:
    """Deterministic, country-neutral prompt. The model only writes prose within these rails."""
    idy = source.get("identity", {})
    place = " · ".join(str(x) for x in (idy.get("municipality"), idy.get("country")) if x)
    site_grade = scored["grades"]["site"]["grade"]
    pp_grade = scored["grades"]["project_process"]["grade"]
    signals = measured_signals(scored)
    fav = [s for s in signals if s["reading"] == "favorable"]
    con = [s for s in signals if s["reading"] == "contrainte"]
    nu = [s for s in signals if s["reading"] == "nuancé"]

    def fmt(items):
        return "\n".join(f'    - {s["label"]} = {s["value"]} (score {s["score"]:.0f})' for s in items) or "    (aucun)"

    want_pp = pp_grade != "insufficient_data"
    shape = '{"site": {"lead","fr","en"}' + (', "project_process": {"lead","fr","en"}' if want_pp else "") + "}"
    return f"""Tu écris la SYNTHÈSE d'une fiche data center pour un observatoire indépendant. Analyste sérieux,
factuel, jamais militant. Tu ne juges pas, tu paraphrases des mesures sourcées. Orthogonal au pays :
tu décris LES VALEURS CI-DESSOUS, jamais un présupposé (ex. « peu carbonée » n'a de sens que si le score l'indique).

Projet : {idy.get("name")} — {place}

Le VOLET SITE (le contexte subi) doit être cohérent avec la note de site déjà calculée
(pour information seulement, INTERDIT de l'écrire) : site = {site_grade}.
Indicateurs mesurés du site, avec leur lecture normalisée du moteur :
  FAVORABLES (score ≥ 66) :
{fmt(fav)}
  CONTRAINTES (score < 40) :
{fmt(con)}
  NUANCÉS (40–65) :
{fmt(nu)}

RÈGLES (dures) :
- **Gate 7** : AUCUNE lettre de note A–E dans le texte. Écris « situe la note du site », jamais « en note C ».
- Cite 1–3 favorables et 1–3 contraintes, les plus saillants ; termine en situant la note du site (sans lettre).
- Vocabulaire GÉNÉRIQUE (réseau électrique local, zones naturelles protégées, site Seveso, masse d'eau,
  terrain artificialisé/agricole) — jamais un opérateur ou une source nationale.
- Ne crédite AUCUNE mitigation projet dans le volet site.
- Interdits : « mauvais », « scandaleux », accusations/intentions, angle juridique. Emploie « médiocre/dégradé ».
{"- VOLET PROJET & PROCESSUS : cohérent avec la note projet déjà calculée (INTERDIT de l'écrire) = " + pp_grade + " ; décris les engagements documentés, plafond « annoncé, pas prouvé »." if want_pp else ""}

`lead` ≤ 6 mots, neutre. `fr` 2–3 phrases. `en` traduction fidèle.
Réponds UNIQUEMENT par un objet JSON valide de forme {shape} — aucun texte autour, aucune balise."""


def validate(synthesis: dict, dc_id: str = "dc") -> list[str]:
    """Reject a draft that cites a grade letter (Gate 7) or uses a banned word. Empty = clean."""
    problems = list(synthesis_grade_citations({"id": dc_id, "synthesis": synthesis}))
    for side, block in synthesis.items():
        if not isinstance(block, dict):
            continue
        blob = " ".join(str(block.get(k, "")) for k in ("lead", "fr", "en")).lower()
        problems += [f"{dc_id}: synthesis.{side} uses banned term {w!r}" for w in BANNED if w in blob]
    return problems


def _parse(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?|\n?```$", "", raw).strip()
    return json.loads(raw)


def redact(source: dict, scored: dict, llm: LLM, *, retries: int = 2) -> dict:
    """Produce a validated `synthesis` for one scored DC. Raises if invalid after retries."""
    prompt = build_prompt(source, scored)
    last = []
    for attempt in range(retries + 1):
        p = prompt if attempt == 0 else prompt + "\n\nTa réponse précédente était invalide :\n- " + "\n- ".join(last) + "\nCorrige et renvoie UNIQUEMENT le JSON."
        syn = _parse(llm(p))
        if scored["grades"]["project_process"]["grade"] == "insufficient_data":
            syn["project_process"] = FIXED_PROJECT
        last = validate(syn, scored["id"])
        if not last:
            return syn
    raise ValueError(f"{scored['id']}: synthesis still invalid after {retries} retries: {last}")


def _is_aux(p: Path) -> bool:
    return p.name.endswith((".provenance.json", ".draft.json", ".governance.json"))


def synthesize_panel(source_dir: Path, artifacts_dir: Path, llm: LLM, *, force: bool = False) -> dict:
    """Write synthesis onto every source DC of a panel that has a scored artifact. Idempotent."""
    done, skipped, failed = [], [], []
    for src_path in sorted(Path(source_dir).glob("*.json")):
        if _is_aux(src_path):
            continue
        source = json.loads(src_path.read_text())
        art = Path(artifacts_dir) / "dc" / f"{source['id']}.json"
        if not art.exists():
            skipped.append(f"{source['id']} (not scored yet)")
            continue
        if source.get("synthesis") and not validate(source["synthesis"], source["id"]) and not force:
            skipped.append(f"{source['id']} (already synthesised)")
            continue
        try:
            source["synthesis"] = redact(source, json.loads(art.read_text()), llm)
        except Exception as e:  # noqa: BLE001 — a bad draft must never land on a source file
            failed.append(f"{source['id']}: {e}")
            continue
        src_path.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n")
        done.append(source["id"])
    return {"written": done, "skipped": skipped, "failed": failed}


def _no_llm(_prompt: str) -> str:
    raise SystemExit("No LLM wired. Inject one: synthesize_panel(..., llm=<Callable[[str],str]>). "
                     "The model call is the pipeline's one delegated step (A-22).")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Synthesis redaction phase (post-scoring, A-22 stage 3).")
    ap.add_argument("--source", required=True, type=Path, help="panel dir of source DCs (datacenters*/)")
    ap.add_argument("--artifacts", required=True, type=Path, help="built artifacts dir (has dc/<id>.json)")
    ap.add_argument("--force", action="store_true", help="re-redact even DCs that already have a valid synthesis")
    args = ap.parse_args(argv)
    result = synthesize_panel(args.source, args.artifacts, llm=_no_llm, force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
