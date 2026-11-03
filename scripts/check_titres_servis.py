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

AUCUN TEST NE PEUT ATTRAPER ÇA : la suite tourne AVANT le build, sur les sources, et le
défaut n'existe que dans l'artefact. La vérification porte donc sur ce qui PART.
"""
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
DIST = RACINE / "site" / "dist"

TITRE = re.compile(r"<title>(.*?)</title>", re.S)
DESCRIPTION = re.compile(r'<meta name="description" content="(.*?)"', re.S)
# Un souligné entre deux lettres, ou un accident de rendu. Tout le reste est du langage.
INTERNE = re.compile(r"\b\w+_\w+\b|\bundefined\b|\bNaN\b|\bnull\b")


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
    print(f"✓ titres et descriptions : aucun mot interne sur {pages} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
