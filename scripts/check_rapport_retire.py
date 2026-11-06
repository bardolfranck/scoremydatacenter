# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Barrière d'avant-mise-en-ligne : un rapport RETIRÉ n'est plus servi, ni présenté.

🔴 POURQUOI CETTE BARRIÈRE EXISTE. Le 7 octobre 2026, le rapport Pays-Bas a été retiré :
le registre Seveso national avait fait tomber les deux notes A sur lesquelles le document
était bâti — pas un passage, le CADRAGE. Trois surfaces ont bien tiré la conséquence (la
fonction de livraison répond 410, l'aperçu a été remplacé par la note de retrait, la prise
d'adresse refuse). Une quatrième ne l'a pas tirée : la PAGE a continué de vendre le rapport
pendant un mois — pastille « Rapport · gratuit », titre d'accroche, « le chiffre qui
dérange », « ce qu'il y a dedans », maquette de couverture avec ses pastilles A→E — et le
MENU l'annonçait sur chaque page du site, dans les deux langues.

Présenter un rapport, c'est le servir. Le défaut n'était donc pas « un lien oublié » : trois
surfaces sur quatre avaient raison, et la quatrième rassurait en étant la plus visible.

AUCUN TEST DE LA SUITE NE PEUT VOIR ÇA. La suite tourne sur les sources, AVANT le build, et
la CI ne construit pas (décision 2026-10-28) : ce qui est servi n'existe qu'au deploy. Le
contrôle porte donc sur ce qui PART — et il se refuse à juger sur des MOTS (ils changent de
langue), il juge sur la STRUCTURE : les classes de la vitrine de rapport, le formulaire de
prise d'adresse, et les liens du menu.

CE QUE LE RETRAIT NE TOUCHE PAS, et que ce contrôle EXIGE : l'adresse répond toujours, et
elle porte la note DATÉE. Un 404 ne rétracte rien — il efface la rétractation, pas le
rapport, dont des copies circulent. C'est la même raison que le 410 de la fonction.

Usage : python3 scripts/check_rapport_retire.py [dossier] (défaut : site/dist)
"""
from __future__ import annotations

import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
TABLE_ETAT = RACINE / "site" / "src" / "config" / "reportStatus.ts"
MENU = RACINE / "site" / "src" / "config" / "nav.ts"
PAGES = RACINE / "site" / "src" / "pages"

# La vitrine d'un rapport, par ses CLASSES : le chiffre citable, la maquette de couverture,
# le sommaire, et le formulaire de prise d'adresse. Des mots auraient demandé une liste par
# langue — et la langue suivante serait passée au travers.
VITRINE = {
    "rd-scoop": "le chiffre d'accroche",
    "rd-cover": "la maquette de couverture",
    "rd-inside": "le sommaire « ce qu'il y a dedans »",
    "data-report-form": "le formulaire de prise d'adresse",
}
# Ce qu'une page de rétractation doit porter, elle.
RETRACTATION = "rd-withdrawn"
NAV = re.compile(r"<nav\b.*?</nav>", re.S)
# 🔴 LE CONTRÔLE PORTE SUR LE DOCUMENT, PAS SUR SON OUTILLAGE. À sa première exécution, ce
# script a accusé les deux pages de servir « le formulaire de prise d'adresse » : le seul
# `data-report-form` de la page était le SÉLECTEUR, dans le script du formulaire (`if (!form)
# return` — il ne trouve rien et s'arrête). Un garde qui lit les scripts nomme une faute qui
# n'est pas là, et un garde qui se trompe une fois n'est plus lu.
SCRIPT_OU_STYLE = re.compile(r"<script.*?</script>|<style.*?</style>", re.S)


def _litteral(texte: str, declaration: str) -> str:
    """Le littéral objet de `const <declaration> … = {…}`, accolades équilibrées.

    Les chaînes sont sautées : une accolade dans une phrase ne doit pas décaler la lecture.
    """
    m = re.search(rf"const {re.escape(declaration)}\b[^=\n]*=\s*\{{", texte)
    if not m:
        raise AssertionError(
            f"`const {declaration}` introuvable dans {TABLE_ETAT.name} — un contrôle qui ne "
            f"trouve plus sa table ne garde rien, et son silence ressemble à un succès"
        )
    i = texte.index("{", m.start())
    profondeur, j = 0, i
    while j < len(texte):
        c = texte[j]
        if c in "\"'`":
            fin = j + 1
            while fin < len(texte) and texte[fin] != c:
                fin += 2 if texte[fin] == "\\" else 1
            j = fin + 1
            continue
        if c == "{":
            profondeur += 1
        elif c == "}":
            profondeur -= 1
            if profondeur == 0:
                return texte[i : j + 1]
        j += 1
    raise AssertionError(f"accolade non fermée pour `{declaration}`")


def etats(texte: str) -> dict[str, str]:
    """Les entrées de premier niveau de la table d'état : slug → corps de son objet."""
    corps = _litteral(texte, "REPORT_STATUS")
    sortie: dict[str, str] = {}
    cle = re.compile(r'[{,]\s*(?:"([\w-]+)"|([A-Za-z_][\w-]*))\s*:\s*\{')
    pos = 0
    while True:
        m = cle.search(corps, pos)
        if not m:
            return sortie
        slug = m.group(1) or m.group(2)
        debut = corps.index("{", m.end() - 1)
        profondeur, j = 0, debut
        while j < len(corps):
            if corps[j] == "{":
                profondeur += 1
            elif corps[j] == "}":
                profondeur -= 1
                if profondeur == 0:
                    break
            j += 1
        # Les clés imbriquées (`withdrawn`, `erratum`) ne sont pas des slugs : on reprend
        # la recherche APRÈS l'objet du slug courant, jamais à l'intérieur.
        sortie[slug] = corps[debut : j + 1]
        pos = j + 1


def slugs_retires(texte: str) -> set[str]:
    return {slug for slug, corps in etats(texte).items() if re.search(r"\bwithdrawn\s*:", corps)}


def url_de_page(p: pathlib.Path, pages: pathlib.Path) -> str:
    """Le chemin SERVI d'une page Astro — la dérivation qu'Astro fait du nom de fichier."""
    rel = p.relative_to(pages).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "index":
        parts.pop()
    return "/" + "".join(f"{s}/" for s in parts)


def urls_servies(slug: str, pages: pathlib.Path = PAGES) -> set[str]:
    """Les adresses servies du rapport : les pages qui PASSENT ce slug au gabarit."""
    marque = re.compile(rf'report=["\']{re.escape(slug)}["\']')
    return {
        url_de_page(p, pages)
        for p in sorted(pages.rglob("*.astro"))
        if marque.search(p.read_text(encoding="utf-8"))
    }


def liens_de_menu(texte_menu: str, url: str) -> bool:
    return f'"{url}"' in texte_menu


def menu_fautif(
    table_texte: str, menu_texte: str, pages: pathlib.Path = PAGES
) -> list[tuple[str, str]]:
    """Les (slug, adresse) d'un rapport retiré que le MENU annonce encore.

    Décidable sur les SOURCES, donc tenu aussi par la suite de tests : c'est la seule
    partie du contrôle qui n'a pas besoin de l'artefact, et c'est celle qui avait tenu un
    mois — le menu est la surface la plus visible du site.
    """
    return [
        (slug, url)
        for slug in sorted(slugs_retires(table_texte))
        for url in sorted(urls_servies(slug, pages))
        if liens_de_menu(menu_texte, url)
    ]


def controle(dist: pathlib.Path) -> list[str]:
    retires = slugs_retires(TABLE_ETAT.read_text(encoding="utf-8"))
    if not retires:
        print("✓ aucun rapport retiré dans la table d'état — rien à contrôler")
        return []

    menu = MENU.read_text(encoding="utf-8")
    fautes: list[str] = []
    attendues: dict[str, str] = {}  # url servie → slug

    for slug, url in menu_fautif(TABLE_ETAT.read_text(encoding="utf-8"), menu):
        fautes.append(
            f"{slug} : {MENU.name} annonce encore {url} — on ne met pas en vitrine un "
            f"rapport qu'on ne sert plus, et le menu est sur CHAQUE page."
        )

    for slug in sorted(retires):
        urls = urls_servies(slug)
        if not urls:
            fautes.append(
                f"{slug} : retiré dans la table d'état, mais AUCUNE page ne porte ce slug. "
                f"Un contrôle qui ne trouve pas de page ne contrôle rien — soit la page a "
                f"été supprimée (et l'adresse rend un 404 qui ne rétracte rien), soit le "
                f"gabarit ne reçoit plus `report=\"{slug}\"`."
            )
            continue
        for url in sorted(urls):
            attendues[url] = slug
            page = dist / url.strip("/") / "index.html"
            if not page.exists():
                fautes.append(
                    f"{slug} : {url} n'est pas servie ({page.relative_to(dist.parent)} "
                    f"absente). L'adresse d'un rapport retiré doit répondre et porter la "
                    f"note datée : un 404 efface la rétractation, pas les copies sorties."
                )
                continue
            html = page.read_text(encoding="utf-8", errors="replace")
            visible = SCRIPT_OU_STYLE.sub("", html)
            for marque, quoi in VITRINE.items():
                if marque in visible:
                    fautes.append(
                        f"{slug} : {url} sert encore {quoi} (`{marque}`) — présenter un "
                        f"rapport, c'est le servir."
                    )
            if RETRACTATION not in html:
                fautes.append(
                    f"{slug} : {url} ne porte pas la note de retrait (`{RETRACTATION}`) — "
                    f"une page muette ne rétracte rien."
                )

    # Le menu est servi sur chaque page : on le relit dans l'ARTEFACT, pas seulement dans
    # sa source. Un lien peut venir d'ailleurs (une liste dérivée, un gabarit de langue).
    #
    # 🔴 SAUF SUR LES PAGES DU RAPPORT LUI-MÊME. À sa première exécution, ce script a
    # reproché aux deux rétractations de se lier l'une à l'autre : c'est le sélecteur de
    # langue du chrome, et il DOIT pointer la rétractation jumelle — une page néerlandaise
    # qui renverrait ailleurs perdrait son lecteur. Le mandat est « aucune AUTRE page ne
    # l'annonce », pas « ces adresses n'apparaissent nulle part ».
    propres = {f"{url.strip('/')}/index.html" for url in attendues}
    for page in sorted(dist.rglob("*.html")):
        if str(page.relative_to(dist)) in propres:
            continue
        navs = "".join(NAV.findall(page.read_text(encoding="utf-8", errors="replace")))
        if not navs:
            continue
        for url, slug in attendues.items():
            if f'href="{url}"' in navs:
                fautes.append(
                    f"{slug} : le menu servi de {page.relative_to(dist)} lie {url}"
                )
                break
    return fautes


def main() -> int:
    dist = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / "site" / "dist"
    if not dist.exists():
        print(f"✗ {dist} absent — lancez `make build` d'abord", file=sys.stderr)
        return 2
    fautes = controle(dist)
    if fautes:
        print("✗ rapport retiré encore servi :", file=sys.stderr)
        for f in fautes:
            print(f"  · {f}", file=sys.stderr)
        return 1
    print("✓ rapports retirés : aucune surface ne les présente, et leur adresse porte la note")
    return 0


if __name__ == "__main__":
    sys.exit(main())
