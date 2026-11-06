# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Barrière d'avant-mise-en-ligne : un lien interne servi MÈNE QUELQUE PART, et avec sa barre finale.

🔴 LA SECONDE FAUTE A ÉTÉ TROUVÉE PAR FRANCK, EN CLIQUANT (2026-11-06). Le menu néerlandais
annonçait sept pages qui n'existent pas — `/nl/kaart/`, `/nl/kerncijfers/`, `/nl/nieuws/`,
`/nl/pers/`, `/nl/over-ons/`, `/nl/ontwikkelaars/`, `/nl/het-cijfer-stap-voor-stap/` — en
haut de CHAQUE page de l'édition : 3 572 liens morts en production. Et le même jour, le
périmètre d'édition a fait tomber 47 liens de l'accueil néerlandais vers les pages de fiches
étrangères qu'il ne bâtit plus. Cette barrière lisait déjà toutes ces adresses ; elle ne
vérifiait que leur barre finale. Elle regardait la bonne chose au mauvais niveau
[[controle-au-mauvais-niveau]].

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
# 🔴 UN LIEN ANCRÉ REDIRIGE AUSSI. La première version écartait tout href portant un `#`,
# donc `/fr/comprendre#questions` — qui répond 308 vers `/fr/comprendre/` exactement comme
# son jumeau nu (vérifié en production). On lit la partie CHEMIN et on laisse l'ancre de côté.
HREF = re.compile(r'href="(/[^"?#]*)(#[^"]*)?"')


def _sources_de_redirection(dossier: Path) -> set[str]:
    """Les adresses que `_redirects` fait suivre : elles mènent quelque part, par règle.

    Une fiche fusionnée garde son adresse et redirige en 301 — la cible existe, la source
    non. Un garde qui l'ignorerait accuserait la règle de réécriture elle-même.
    """
    fichier = dossier / "_redirects"
    if not fichier.exists():
        return set()
    sources = set()
    for ligne in fichier.read_text(encoding="utf-8", errors="replace").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#"):
            sources.add(ligne.split()[0])
    return sources


def _liens_morts(dossier: Path) -> tuple[collections.Counter[str], dict[str, str]]:
    """Les adresses internes servies qui ne mènent à aucun fichier, aucune règle, aucune
    fonction.

    Trois façons LÉGITIMES pour une adresse de ne pas être un fichier de `dist`, et les trois
    sont des faits de production, pas des exceptions de confort :
    · `/api/…` est servi par une fonction Cloudflare (`site/functions/`) ;
    · une source de `_redirects` répond 301 vers une cible qui, elle, existe ;
    · un répertoire est servi par son `index.html`.
    """
    redirections = _sources_de_redirection(dossier)

    def mene_quelque_part(href: str) -> bool:
        if href.startswith("/api/"):
            return True
        if href in redirections or href.rstrip("/") + "/" in redirections:
            return True
        rel = href.strip("/")
        if not rel:
            return (dossier / "index.html").is_file()
        cible = dossier / rel
        return cible.is_file() or (cible / "index.html").is_file()

    morts: collections.Counter[str] = collections.Counter()
    ou: dict[str, str] = {}
    for fichier in dossier.rglob("*.html"):
        for m in HREF.finditer(fichier.read_text(encoding="utf-8", errors="replace")):
            href = m.group(1)
            if not href or mene_quelque_part(href):
                continue
            morts[href] += 1
            ou.setdefault(href, str(fichier.relative_to(dossier)))
    return morts, ou


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
            if not href:
                continue  # un href qui n'est QUE l'ancre (`#faq`) ne va nulle part d'autre
            # Une adresse de FICHIER garde son extension (`/assets/x.svg`, `/sitemap.xml`) :
            # elle n'a pas de barre finale et n'en veut pas.
            if href.endswith("/") or "." in href.rsplit("/", 1)[-1]:
                continue
            fautes[href] += 1
            ou.setdefault(href, str(fichier.relative_to(dossier)))

    if not pages:
        print(f"liens servis : aucune page dans {dossier}", file=sys.stderr)
        return 1

    morts, ou_morts = _liens_morts(dossier)
    if morts:
        total = sum(morts.values())
        print(
            f"liens servis : {len(morts)} adresse(s) interne(s) ne mènent À RIEN, "
            f"{total} occurrence(s) sur {pages} pages — chacune est un 404 servi :",
            file=sys.stderr,
        )
        for href, n in morts.most_common(30):
            print(f"  {n:5} × {href}   (ex. {ou_morts[href]})", file=sys.stderr)
        if len(morts) > 30:
            print(f"  … et {len(morts) - 30} autre(s)", file=sys.stderr)
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
    print(
        f"✓ liens servis : {pages} pages — aucune adresse morte, aucune sans barre finale"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
