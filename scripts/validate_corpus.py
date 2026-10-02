# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""GATE de déploiement : valide le CORPUS RÉEL du newsroom (les ~1446 fiches servies),
pas les 2 fixtures du dépôt.

Raison d'être (incident 2026-09-30) : `make validate` réussissait sur les 2 fixtures
data/datacenters/ pendant que le build cassait sur les 1446 fiches du newsroom (KeyError
E6 : un indicateur de méthodo absent d'une fiche). Un gate qui ne voit pas le vrai corpus
n'est pas un gate.

Exigences (chef) :
  1. ÉCHOUE en SORTIE NON-NULLE, pas en imprimant un rapport (sinon ce n'est pas un gate).
  2. REFUSE un corpus absent ou TRONQUÉ : newsroom non monté, ou nombre de fiches sous un
     plancher (voir les 2 fixtures au lieu de 1446) → plantage, jamais vert.

Contrôles par fiche :
  · GATE 1 — jeu d'indicateurs COMPLET (chaque indicateur de la méthodo active présent) ;
  · GATE 8 — indicateur project/process mvp `not_collected` sur une fiche `published` (interdit) ;
  · SCORING — score_datacenter() ne lève AUCUNE exception (le contrôle qui aurait attrapé le
    KeyError E6).

    make validate-corpus
    NEWSROOM_CAL=/path NEWSROOM_MIN=500 make validate-corpus
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.core import datacenter_paths, load_methodology   # noqa: E402
from engine.scoring import score_datacenter                  # noqa: E402
from engine.validate import geo_gate, position_gate          # noqa: E402

CAL = Path(os.environ.get("NEWSROOM_CAL",
                          Path(__file__).resolve().parent.parent.parent / "smdc-newsroom" / "calibration"))
MIN_FICHES = int(os.environ.get("NEWSROOM_MIN", "500"))   # plancher anti-corpus-tronqué


def _methodology_sets(m: dict) -> tuple[set[str], set[str]]:
    """(tous les indicateurs, ceux project/process mvp) — lus à la source, jamais devinés.

    Une heuristique qui reconnaît un indicateur à la présence de `pillar`/`weight_in_pillar`
    ramasse aussi ce qui lui ressemble ailleurs dans la méthodo. Un gate ne devine pas le
    périmètre qu'il contrôle.
    """
    inds = m["indicators"]
    return ({i["id"] for i in inds},
            {i["id"] for i in inds if i.get("block") in ("project", "process") and i.get("mvp")})


def _fiches() -> list[Path]:
    """EXACTEMENT les fiches que le build score — `datacenter_paths`, l'accesseur du moteur.

    Un glob maison redonne un autre périmètre : `datacenters*/*.json` ramassait les 8 fiches
    `il-*.draft.json` que le build écarte volontairement (`_AUX_SUFFIXES`), soit 1446 contre
    1438. Un gate qui refuse le deploy sur un fichier qui ne part jamais en prod finit
    contourné — et un gate contourné ne protège rien.
    """
    return datacenter_paths(CAL)


def main() -> int:
    # --- garde 1 : corpus présent
    if not CAL.is_dir():
        print(f"GATE CORPUS: newsroom introuvable à {CAL} — clone smdc-newsroom ou fixe NEWSROOM_CAL",
              file=sys.stderr)
        return 2
    paths = _fiches()
    # --- garde 2 : corpus non tronqué (jamais valider 2 fixtures pour ~1446 fiches)
    if len(paths) < MIN_FICHES:
        print(f"GATE CORPUS: {len(paths)} fiche(s) trouvée(s) sous le plancher {MIN_FICHES} — "
              f"corpus tronqué ou absent ({CAL}). Refus (ce n'est pas le corpus réel).", file=sys.stderr)
        return 2

    methodology = load_methodology()
    meth_ids, scored_pp = _methodology_sets(methodology)
    problems: list[str] = []
    scored = 0

    for p in paths:
        label = p.name
        try:
            dc = json.loads(p.read_text())
        except Exception as e:  # noqa: BLE001
            problems.append(f"{label}: JSON illisible ({e})")
            continue
        inds = {i["id"]: i for i in dc.get("indicators", [])}
        # GATE 1 — set complet
        missing = meth_ids - set(inds)
        if missing:
            problems.append(f"GATE 1 {label}: indicateurs absents {sorted(missing)}")
        # GATE 8 — project/process not_collected sur published
        if (dc.get("publication") or {}).get("status") == "published":
            for iid in scored_pp:
                if inds.get(iid, {}).get("status") == "not_collected":
                    problems.append(f"GATE 8 {label}: {iid} not_collected sur une fiche publiée")
        # SCORING — aucune exception (le contrôle qui aurait attrapé le KeyError E6)
        try:
            score_datacenter(dc, methodology)
            scored += 1
        except Exception as e:  # noqa: BLE001
            problems.append(f"SCORING {label}: {type(e).__name__}: {str(e)[:120]}")

    # GATE POSITION — deux fiches au même point sans adjudication. Il vit ICI, sur le corpus
    # réel, et pas seulement dans `make validate` qui ne voit que les 2 fixtures : c'est la
    # leçon du gate géo, câblé au bon endroit mais branché sur le vide.
    problems += position_gate(paths)

    # GATE GÉO — une coordonnée fabriquée ne part pas en ligne. Il existait depuis le
    # 2026-09-29, câblé dans `run_gates()`, donc dans `make validate`, qui ne voit que les
    # 2 fixtures du dépôt : son contrôle de couverture comparait les 1447 fiches mesurées
    # à... 2, et passait trivialement. Pendant ce temps le gate de deploy, qui voit le vrai
    # corpus, ne l'appelait pas. Le gate avait toutes ses dents, braquées sur le vide.
    # Il reçoit ici le périmètre RÉEL, le même que celui qu'il compte.
    problems += geo_gate(CAL)

    if problems:
        print(f"GATE CORPUS: {len(problems)} problème(s) sur {len(paths)} fiches "
              f"(méthodo {methodology.get('version')}) :", file=sys.stderr)
        for pb in problems[:50]:
            print(f"  - {pb}", file=sys.stderr)
        if len(problems) > 50:
            print(f"  … et {len(problems) - 50} de plus", file=sys.stderr)
        return 1

    print(f"validate-corpus: OK — {len(paths)} fiches, {scored} scorées sans erreur, "
          f"jeu d'indicateurs complet (méthodo {methodology.get('version')}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
