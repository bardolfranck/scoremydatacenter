# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Dernière barrière : aucun mot INTERNE ne part dans un titre ou une description.

🔴 POURQUOI CE SCRIPT EXISTE. Trois fois le même défaut, et à chaque fois découvert par
hasard :
  · 2026-10-02 — « note insufficient_data » dans le titre de fiches ;
  · 2026-11-02 — « note en_attente », 19 pages ;
  · 2026-11-03 — « note en_attente » encore, 8 fiches israéliennes, par un AUTRE chemin
    (note retenue sans `provisional_band`, cas qu'aucune branche ne couvrait).

Les deux premières corrections ont ÉNUMÉRÉ la valeur fautive. Énumérer les mauvaises
valeurs est une course qu'on perd : il y en a toujours une de plus, et elle sort dans
l'onglet du navigateur et dans les résultats de recherche, c'est-à-dire là où on ne
regarde jamais.

LA RÈGLE EST DONC INVERSÉE, ET GÉNÉRALE. Un titre écrit pour un lecteur ne contient pas
de souligné : `en_attente`, `insufficient_data`, `not_collected`, `under_construction`
sont des identifiants de machine. Ni `undefined`, ni `NaN`, ni `null`, qui sont des
accidents. On ne liste pas ce qu'on refuse — on décrit la FORME de ce qui est
légitime, et tout le reste est refusé d'office.

ET LA QUATRIÈME FOIS, C'ÉTAIT DANS LE CORPS DE LA PAGE. Le 2026-11-04, « en_attente » sur
la puce du MUR SATELLITE de l'accueil, et « en_attente undefined » sur la ligne Israël de la
page des indices — trois langues, pages les plus vues du site. Ce script ne regardait que le
titre et la description : il a donc vu passer, sous ses yeux, le même défaut d'un étage plus
bas.

Le corps ne se garde pas de la même façon. Un titre n'a aucune raison de porter un souligné ;
un corps de fiche en a une BONNE — la ligne de provenance cite le nom du champ interrogé
(« WRI Aqueduct 4.0 […] (bws_cat 3/4) », « EEA IED_SiteMap has_seveso »), et nommer le champ
est de la traçabilité. On ne cherche donc pas la FORME dans le corps, mais la FAMILLE : les
sentinelles de note et les mots que le langage donne au vide.

AUCUN TEST NE PEUT ATTRAPER ÇA : la suite tourne AVANT le build, sur les sources, et le
défaut n'existe que dans l'artefact. La vérification porte donc sur ce qui PART.
"""
import html
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
DIST = RACINE / "site" / "dist"

TITRE = re.compile(r"<title>(.*?)</title>", re.S)
DESCRIPTION = re.compile(r'<meta name="description" content="(.*?)"', re.S)
# Un souligné entre deux lettres, ou un accident de rendu. Tout le reste est du langage.
INTERNE = re.compile(r"\b\w+_\w+\b|\bundefined\b|\bNaN\b|\bnull\b")

# Dans le CORPS, la famille et non la forme : les sentinelles de note, et les trois mots que
# le langage donne au vide. `bws_cat` et `has_seveso` ne sont pas là — ce sont des noms de
# champs de source, cités dans la provenance, et un garde qui crierait sur 2 857 pages pour
# cela ne serait plus lu.
SENTINELLES = re.compile(
    r"\ben_attente\b|\binsufficient_data\b|\bnot_collected\b|\ben_veille\b"
    r"|\bundefined\b|\bNaN\b|\bnull\b"
)
SCRIPT_OU_STYLE = re.compile(r"<script.*?</script>|<style.*?</style>", re.S)
BALISE = re.compile(r"<[^>]+>")


def main(argv: list[str] | None = None) -> int:
    global DIST
    argv = argv if argv is not None else sys.argv[1:]
    if argv:
        DIST = pathlib.Path(argv[0])
    if not DIST.is_dir():
        print(f"✗ {DIST} absent — lancer `make build` avant", file=sys.stderr)
        return 1
    fautes: list[str] = []
    pages = 0
    for page in DIST.rglob("*.html"):
        pages += 1
        texte = page.read_text(encoding="utf-8", errors="replace")
        for motif, quoi in ((TITRE, "titre"), (DESCRIPTION, "description")):
            for valeur in motif.findall(texte):
                for mot in set(INTERNE.findall(valeur)):
                    fautes.append(f"  {page.relative_to(DIST)} · {quoi} · « {mot} »")
        # le corps : seulement la famille des sentinelles
        if "<body" in texte:
            corps = SCRIPT_OU_STYLE.sub(" ", texte[texte.index("<body"):])
            visible = html.unescape(" ".join(BALISE.sub(" ", corps).split()))
            for mot in set(SENTINELLES.findall(visible)):
                fautes.append(f"  {page.relative_to(DIST)} · corps · « {mot} »")
    if not pages:
        print(f"✗ aucune page HTML sous {DIST} — le relevé ne cherche plus", file=sys.stderr)
        return 1
    if fautes:
        print(
            f"✗ VOCABULAIRE INTERNE SERVI : {len(fautes)} occurrence(s) sur {pages} pages.\n"
            "  Un identifiant de machine part dans l'onglet du navigateur et dans les\n"
            "  résultats de recherche — l'endroit où personne ne relit.\n"
            + "\n".join(sorted(set(fautes))[:20]),
            file=sys.stderr,
        )
        return 1
    print(
        f"✓ titres, descriptions et corps : aucun mot interne ni sentinelle sur {pages} "
        f"pages"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
