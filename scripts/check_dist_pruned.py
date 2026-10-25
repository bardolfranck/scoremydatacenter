# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Dernière barrière avant la mise en ligne : le dist est-il bien blanchi ?

🔴 POURQUOI CE SCRIPT EXISTE. Le 2026-10-25, pour éviter 150 secondes de rebuild, j'ai
lancé `npx astro build` puis `wrangler pages deploy` au lieu de `make deploy`. `astro build`
n'exécute PAS le blanchiment anti-pillage : le dist est parti avec les 3 283 fiches JSON
complètes du corpus — crédit, indicateurs, valeurs, sources. Rien ne l'a signalé.

Ce qui a sauvé la mise, c'est la limite de 20 000 fichiers de Cloudflare Pages, atteinte par
pur hasard le même jour à cause des portraits. Sans elle, le corpus entier était publié.

AUCUN TEST NE PEUT ATTRAPER ÇA : la suite tourne AVANT le build, sur les sources. Le défaut
n'existe que dans l'artefact, entre le build et l'envoi. C'est donc là qu'il faut regarder —
et la vérification doit porter sur ce qui part, pas sur ce qui est censé partir.

⚠️ À appeler depuis la cible `deploy`, et à rappeler si un jour quelqu'un déploie à la main.
"""
import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
DIST = RACINE / "site" / "dist"

# Répertoires que `prune_public_json.py` doit avoir VIDÉS (le contenu passe par une règle
# de réécriture). Un seul fichier qui traîne ici est du corpus en clair.
VIDES = ["dc", "comparator", "actu"]
# Fichiers qui doivent rester des BOUCHONS, pas des données.
MARQUE = '"gone":true'


def main() -> int:
    if not DIST.is_dir():
        print("✘ deploy: site/dist absent — rien à vérifier, donc rien à déployer")
        return 1

    fautes = []
    for nom in VIDES:
        restants = list((DIST / "data" / nom).glob("*.json")) if (DIST / "data" / nom).is_dir() else []
        if restants:
            fautes.append(f"data/{nom}/ contient encore {len(restants)} fichier(s) "
                          f"(ex. {restants[0].name})")

    for f in (DIST / "data").glob("*.json"):
        if f.name == "gone.json":
            continue
        if MARQUE not in f.read_text()[:200]:
            fautes.append(f"data/{f.name} n'est pas un bouchon")

    red = DIST / "_redirects"
    if not red.exists() or "/data/dc/*" not in red.read_text():
        fautes.append("_redirects ne porte pas la règle /data/dc/* — les bouchons "
                      "deviendraient des 404 sur des URL déjà indexées")

    if fautes:
        print("✘ deploy REFUSÉ — le dist n'est pas blanchi :")
        for f in fautes:
            print(f"    · {f}")
        print("\n  Cause la plus probable : `astro build` lancé seul au lieu de `make build`.")
        print("  Remède : make prune-public-json   (puis relancer le déploiement)")
        return 1

    print("deploy: dist blanchi ✓ (corpus retiré, bouchons en place, règle de réécriture servie)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
