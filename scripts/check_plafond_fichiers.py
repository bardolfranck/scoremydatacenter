#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Combien de fichiers partent — et le plafond qui refuse TOUT au-dessus.

🔴 CE QUE CETTE BARRIÈRE A COÛTÉ AVANT D'EXISTER (2026-11-06). Franck lance `make deploy`.
La suite passe, le build passe, les sept barrières passent, et wrangler répond :
« Pages only supports up to 20,000 files in a deployment for your current plan ». 24 047
fichiers. Rien n'est publié — ni le rapport retiré qui attendait sa rétractation, ni les
151 fiches néerlandaises. Le refus est TOTAL : un plafond ne publie pas « ce qui rentre ».

CE QUI AVAIT GONFLÉ : l'édition néerlandaise bâtissait une page par fiche du monde, 1 702
américaines comprises, en prose anglaise sous une adresse néerlandaise. Ce n'était pas un
bug visible — aucune page n'y liait, aucun test ne les comptait, et le sitemap les
déclarait à Google comme du contenu dupliqué. La cause est corrigée dans
`content/langues.ts` (une édition de pays couvre son pays). Cette barrière garde le PLAFOND,
qui ne dépend pas de cette cause-là : la prochaine langue, le prochain lot de vignettes ou
le prochain pays le pousseront tout autant.

POURQUOI ELLE ALERTE AVANT DE REFUSER. Un plafond franchi est une publication refusée, donc
une panne. Une barrière qui ne parle qu'au plafond ne prévient jamais : elle constate. Elle
crie donc dès la marge, en nommant les répertoires qui pèsent — pour qu'on choisisse à
froid, et pas la nuit où ça déborde.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DIST = RACINE / "site" / "dist"

# La limite de Cloudflare Pages PAR DÉPLOIEMENT, sur le forfait courant. Ce n'est pas un
# choix d'ingénierie : c'est le refus de l'hébergeur, et il est binaire.
LIMITE = 20_000
# 🔴 LE PLAFOND SUIT LA CIBLE (2026-11-13). Le même `dist` peut partir vers deux hébergements
# tant que la bascule n'est pas faite : Cloudflare Pages (`make deploy`, 20 000 fichiers) ou
# un Worker avec fichiers statiques (`make deploy-worker`, 100 000 sur le forfait Workers
# Paid, pris le 2026-11-09). Mesurer le Worker avec le plafond de Pages refuserait une
# publication qui rentre ; l'inverse laisserait partir vers Pages un dist qu'il refusera en
# entier. La cible se déclare donc : `CIBLE=worker`. Sans rien, c'est Pages — le défaut est
# le plafond le plus bas, celui qui ne laisse rien passer par oubli.
LIMITES = {"pages": LIMITE, "worker": 100_000}
NOMS = {"pages": "Cloudflare Pages", "worker": "Cloudflare Workers (fichiers statiques)"}
# La marge où l'on veut être prévenu. 2 000 fichiers, c'est l'ordre de grandeur d'UNE
# surface nouvelle (une langue de pays, un lot de vignettes) : de quoi voir venir le mur
# avant de le prendre.
MARGE = 2_000
# Un `dist` vide ou absent compterait zéro fichier et passerait — « l'absence ressemble à
# zéro ». Un déploiement réel pèse des milliers de fichiers ; en dessous, la barrière ne sait
# pas ce qu'elle mesure et le dit.
PLANCHER_PLAUSIBILITE = 500


def compte(racine: Path) -> int:
    return sum(1 for p in racine.rglob("*") if p.is_file())


def par_repertoire(racine: Path) -> list[tuple[int, str]]:
    poids: list[tuple[int, str]] = []
    for enfant in sorted(racine.iterdir()):
        if enfant.is_dir():
            poids.append((compte(enfant), enfant.name + "/"))
    poids.append((sum(1 for p in racine.iterdir() if p.is_file()), "(racine)"))
    return sorted(poids, reverse=True)


def cible() -> str:
    """La cible déclarée par `CIBLE=…`. Une valeur inconnue est refusée, pas ramenée au
    défaut : une faute de frappe ne doit pas choisir un plafond."""
    demandee = os.environ.get("CIBLE", "").strip().lower() or "pages"
    if demandee not in LIMITES:
        raise SystemExit(
            f"plafond de fichiers : cible « {demandee} » inconnue. Cibles connues : "
            f"{', '.join(sorted(LIMITES))}."
        )
    return demandee


def refuse(total: int, limite: int = LIMITE) -> bool:
    """Au-dessus du plafond, l'hébergeur refuse la publication ENTIÈRE."""
    return total > limite


def alerte(total: int, limite: int = LIMITE) -> bool:
    """Dans la marge : ça passe encore, et il faut le savoir maintenant."""
    return total > limite - MARGE


def _tableau(racine: Path, lignes: int = 8) -> str:
    return "\n".join(f"    {n:>7d}  {nom}" for n, nom in par_repertoire(racine)[:lignes])


def main() -> None:
    if not DIST.is_dir():
        raise SystemExit(
            f"plafond de fichiers : {DIST} n'existe pas — rien à mesurer, et une barrière "
            f"qui ne mesure rien ne garde rien. Lancez le build d'abord."
        )
    vers = cible()
    limite, hebergeur = LIMITES[vers], NOMS[vers]
    total = compte(DIST)
    if total < PLANCHER_PLAUSIBILITE:
        raise SystemExit(
            f"plafond de fichiers : {total} fichier(s) dans {DIST.name}, c'est trop peu pour "
            f"être un site. Soit le build a échoué sans le dire, soit cette barrière ne "
            f"regarde pas au bon endroit — dans les deux cas elle refuse de conclure."
        )
    if refuse(total, limite):
        raise SystemExit(
            f"plafond de fichiers : {total} fichiers dans dist, la limite de {hebergeur} "
            f"est de {limite} PAR DÉPLOIEMENT. Au-dessus, la publication est refusée "
            f"EN ENTIER — pas tronquée. Ce qui pèse :\n{_tableau(DIST)}\n"
            f"  Une édition de pays couvre son pays (`PAYS_DE_LA_LANGUE` dans "
            f"`site/src/content/langues.ts`) : c'est le levier le plus net, une langue de "
            f"plus sur le corpus entier coûte ~6 600 fichiers."
        )
    if alerte(total, limite):
        print(
            f"⚠ plafond de fichiers : {total} fichiers, plafond {limite} ({hebergeur}) — il reste "
            f"{limite - total}. Ce qui pèse :\n{_tableau(DIST)}"
        )
        return
    print(f"✓ plafond de fichiers : {total} fichiers dans dist, limite {limite} ({hebergeur})")


if __name__ == "__main__":
    sys.exit(main())
