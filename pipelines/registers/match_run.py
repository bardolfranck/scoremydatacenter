# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le POINT D'ENTRÉE du rattachement : `python -m pipelines.registers.match_run`.

La logique vit dans `match.py` (proposer / ecrire / projets_candidats) ; ce module n'est que
sa commande — l'étage qui manquait. Jusqu'ici le rattachement était lancé par des scripts
écrits dans un terminal puis jetés : les fichiers existaient dans le newsroom, mais personne
ne pouvait les régénérer, et `WORKFLOW.md` annonçait une commande (`match_run`) qui n'existait
pas. Une commande fantôme est pire qu'une absence : elle fait croire au suivant que le process
est là. Celui-ci EST là.

Ce qu'il fait, et RIEN d'autre :
  · lit le corpus noté (engine.core.load_datacenters) et les fiches d'extraction du registre ;
  · appelle `match.proposer` puis `match.ecrire` → `registres/rattachement.json`.

Les garde-fous qui en font un process et pas un script :
  · AUCUN réseau — tout se calcule depuis les fichiers d'extraction et le corpus ;
  · IDEMPOTENT — deux passages de suite donnent le même fichier ;
  · le corpus n'est JAMAIS modifié, et rien n'est auto-confirmé (`confirme: false` partout) ;
  · ÉCHEC BRUYANT — corpus absent ou tronqué → sortie non nulle, comme `validate-corpus`,
    pour qu'un `--out` qui pointe à côté ne produise pas un rattachement vide qui aurait l'air
    valide.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from engine.core import load_datacenters

from . import match

# L'extraction écrit ces fichiers DANS le dossier du registre : ce ne sont pas des avis.
# On ne filtre pas par nom (fragile) mais par SCHÉMA : seule une fiche d'extraction porte
# « smdc.registre-ae/1 ». index.json, couverture.json, rattachement*.json, operateurs-*.json
# en sont donc exclus d'office, quel que soit leur nom.
FICHE_SCHEMA = "smdc.registre-ae/1"

# Tripwire anti-troncature : le corpus noté (FR + panneaux EU) compte ~1 438 fiches. En dessous
# de ce plancher, `--out`/calibration pointe sur un checkout partiel ou les mauvaises fixtures —
# et un rattachement calculé sur un corpus amputé rattacherait faux en silence. On s'arrête.
MIN_FICHES_DEFAUT = 500


def corpus_depuis_dcs(dcs: dict[str, dict]) -> dict[str, dict]:
    """Réduit chaque fiche notée à ce dont le rattachement a besoin : commune, opérateur, point."""
    return {
        fid: {
            "municipality": (v.get("identity") or {}).get("municipality"),
            "operator": (v.get("identity") or {}).get("operator"),
            "coordinates": (v.get("identity") or {}).get("coordinates"),
        }
        for fid, v in dcs.items()
    }


def charger_avis(reg_dir: Path) -> dict[str, dict]:
    """{nom_de_fichier: fiche} pour les seules fiches d'EXTRACTION (schéma smdc.registre-ae/1)."""
    avis: dict[str, dict] = {}
    for p in sorted(reg_dir.glob("*.json")):
        try:
            d = json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            continue
        if isinstance(d, dict) and d.get("schema") == FICHE_SCHEMA:
            avis[p.stem] = d
    return avis


def _calibration_dir(out: Path) -> Path:
    """Le corpus noté est le voisin du registre : <newsroom>/calibration. Surchargeable."""
    env = os.environ.get("NEWSROOM_CAL")
    return Path(env) if env else out.parent / "calibration"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m pipelines.registers.match_run",
        description="Rattacher chaque avis de registre à une fiche du corpus (propositions, jamais des faits).")
    ap.add_argument("--out", type=Path, required=True,
                    help="dossier du registre (ex. ../smdc-newsroom/registres) ; rattachement.json y est écrit")
    ap.add_argument("--calibration", type=Path, default=None,
                    help="dossier du corpus noté ; par défaut <out>/../calibration (ou $NEWSROOM_CAL)")
    ap.add_argument("--min-fiches", type=int, default=MIN_FICHES_DEFAUT,
                    help=f"plancher anti-troncature du corpus (défaut {MIN_FICHES_DEFAUT})")
    a = ap.parse_args(argv)

    if not a.out.is_dir():
        print(f"match_run : dossier registre introuvable — {a.out}", file=sys.stderr)
        return 2
    cal = a.calibration or _calibration_dir(a.out)
    if not (cal / "datacenters").is_dir():
        print(f"match_run : corpus noté introuvable — {cal}/datacenters "
              f"(cloner smdc-newsroom ou passer --calibration / $NEWSROOM_CAL)", file=sys.stderr)
        return 2

    dcs = load_datacenters(cal)
    if len(dcs) < a.min_fiches:
        print(f"match_run : corpus tronqué — {len(dcs)} fiches < {a.min_fiches} attendues ; "
              f"refus de rattacher sur un corpus amputé (vérifier {cal})", file=sys.stderr)
        return 2

    corpus = corpus_depuis_dcs(dcs)
    avis = charger_avis(a.out)
    if not avis:
        print(f"match_run : aucune fiche d'extraction (schéma {FICHE_SCHEMA}) dans {a.out}", file=sys.stderr)
        return 2

    date = time.strftime("%Y-%m-%d")
    props = match.proposer(avis, corpus)
    doc = match.ecrire(props, a.out / "rattachement.json", date)
    arb = match.ecrire_arbitrages(props, avis, corpus, a.out / "rattachement-a-arbitrer.json", date)
    ops = match.ecrire_operateurs(props, avis, corpus, a.out / "operateurs-a-renseigner.json", date)

    print(f"match_run : {len(avis)} avis × {len(dcs)} fiches → rattachement.json", file=sys.stderr)
    for statut, n in sorted(doc["resume"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {statut}", file=sys.stderr)
    print(f"  projets_a_collecter    : {len(doc['projets_a_collecter'])}", file=sys.stderr)
    print(f"  à arbitrer (ambigu)    : {len(arb['cas'])} → rattachement-a-arbitrer.json", file=sys.stderr)
    print(f"  opérateurs à renseigner: {len(ops['fiches'])} → operateurs-a-renseigner.json", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
