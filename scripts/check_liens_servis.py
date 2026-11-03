# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Barrière d'avant-mise-en-ligne : aucun lien interne servi ne perd sa barre finale.

Une adresse interne sans barre finale répond 308 en production (vérifié : `/map` →
`/map/`). Le lecteur paye un aller-retour, le moteur suit une chaîne de redirection, et
rien ne le signale — une redirection est muette.

🔴 CE CONTRÔLE SE FAIT SUR CE QUI EST SERVI, PAS SUR LE CODE. Les adresses du site se
composent : un préfixe `/fr/dc` dans un composant, l'identifiant du site ajouté ailleurs.
Un garde qui lirait les sources devrait distinguer un PRÉFIXE d'un LIEN, et crierait sur
les premiers — un garde qui crie à faux finit désactivé. Le HTML rendu, lui, ne porte que
des liens finis.

Usage : python3 scripts/check_liens_servis.py [dossier] (défaut : site/dist)
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
HREF = re.compile(r'href="(/[^"#?]*)"')


def main() -> int:
    dossier = Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / "site" / "dist"
    if not dossier.is_dir():
        print(f"liens servis : {dossier} n'existe pas — rien à vérifier", file=sys.stderr)
        return 1

    fautes: collections.Counter[str] = collections.Counter()
    ou: dict[str, str] = {}
    pages = 0
    for fichier in dossier.rglob("*.html"):
        pages += 1
        for m in HREF.finditer(fichier.read_text(encoding="utf-8", errors="replace")):
            href = m.group(1)
            # Une adresse de FICHIER garde son extension (`/assets/x.svg`, `/sitemap.xml`) :
            # elle n'a pas de barre finale et n'en veut pas.
            if href.endswith("/") or "." in href.rsplit("/", 1)[-1]:
                continue
            fautes[href] += 1
            ou.setdefault(href, str(fichier.relative_to(dossier)))

    if not pages:
        print(f"liens servis : aucune page dans {dossier}", file=sys.stderr)
        return 1
    if fautes:
        total = sum(fautes.values())
        print(
            f"liens servis : {len(fautes)} adresse(s) sans barre finale, {total} occurrence(s) "
            f"sur {pages} pages — chacune est une redirection 308 payée par le lecteur :",
            file=sys.stderr,
        )
        for href, n in fautes.most_common():
            print(f"  {n:5} × {href}   (ex. {ou[href]})", file=sys.stderr)
        return 1
    print(f"✓ liens servis : aucune adresse interne sans barre finale sur {pages} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
