#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Ce déploiement va-t-il en PRODUCTION, ou dans une préviz que personne ne lit ?

🔴 CE QUI S'EST PASSÉ LE 2026-11-06, et c'est le plus sournois de la journée. `make deploy`
est allé AU BOUT : 17 764 fichiers téléversés, « ✨ Deployment complete! », cache purgé,
code de sortie 0. Et `scoremydatacenter.org` n'avait pas bougé d'un octet.

`wrangler pages deploy` prend la BRANCHE GIT courante comme nom de branche de déploiement.
Hors de la branche de production, Cloudflare Pages range le résultat en environnement
« Preview » : une URL `<hash>.pages.dev` que personne n'ouvre, avec le même message de
succès, le même compte de fichiers, le même zéro en sortie. Rien dans la sortie ne distingue
une publication d'un essai [[absence-ressemble-a-zero]].

CE QUE CETTE BARRIÈRE REFUSE, et ce qu'elle ne refuse pas. Elle refuse de lancer une
publication qui ANNONCERA la production sans la toucher. Elle n'interdit pas la préviz :
`PREVIZ=1 make deploy` la demande explicitement, et le nom de la branche devient alors une
décision et non un effet de bord. Elle ne dit rien, en revanche, de ce que la branche
CONTIENT — une branche de production en retard reste une branche de production.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

# La branche que Cloudflare Pages tient pour la production sur ce projet.
BRANCHE_DE_PRODUCTION = "main"


def branche_courante() -> str:
    return subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=RACINE, capture_output=True, text=True, check=True,
    ).stdout.strip()


def main() -> None:
    demandee = os.environ.get("PREVIZ", "").strip()
    branche = branche_courante()
    if demandee:
        print(f"⚠ publication de PRÉVIZ demandée (PREVIZ={demandee}) — branche « {branche} », "
              f"l'URL servie ne sera pas scoremydatacenter.org")
        return
    if not branche:
        raise SystemExit(
            "branche de publication : HEAD détachée, donc wrangler nommera la branche de "
            "déploiement d'après rien. Placez-vous sur une branche, ou demandez la préviz "
            "avec PREVIZ=1."
        )
    if branche != BRANCHE_DE_PRODUCTION:
        raise SystemExit(
            f"branche de publication : vous êtes sur « {branche} », la production est "
            f"« {BRANCHE_DE_PRODUCTION} ».\n"
            f"  Partir d'ici téléverserait tout, répondrait « ✨ Deployment complete! » et "
            f"sortirait en 0 — dans un environnement PREVIEW. scoremydatacenter.org ne "
            f"changerait pas, et RIEN dans la sortie ne le dirait.\n"
            f"  · pour publier : fusionnez, passez sur {BRANCHE_DE_PRODUCTION}, relancez ;\n"
            f"  · pour une préviz assumée : PREVIZ=1 make deploy."
        )
    print(f"✓ branche de publication : « {branche} » — environnement de production")


if __name__ == "__main__":
    sys.exit(main())
