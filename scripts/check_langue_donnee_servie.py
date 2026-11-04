# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""La DONNÉE servie parle-t-elle chaque langue ? — vérifié APRÈS le build.

🔴 POURQUOI UNE BARRIÈRE ET PLUS UN TEST. Ce contrôle existait dans la suite
(`test_i18n_parity.py`). Il lisait `site/public/data/`, qui est ignoré par git parce qu'il
est ÉCRIT par `make build`. Or `make deploy` lance la suite AVANT le build. Le 2026-11-04,
dans l'arbre de déploiement, un artefact du 2 novembre a fait tomber la suite en annonçant
« 18 999 objets ne portent pas le néerlandais — un pipeline a cessé de l'émettre ». Aucun
pipeline n'avait cessé : `engine/scoring.py` émettait bien les trois langues. Le fichier
datait d'avant. Le contrôle mesurait au mauvais niveau, et son diagnostic accusait un
innocent.

Un sous-produit ne se vérifie qu'une fois produit. Les épreuves de la suite se taisent
maintenant sur un artefact périmé ; les dents sont ici, sur le fichier frais.

DEUX CHOSES VÉRIFIÉES, ET ELLES NE DISENT PAS LA MÊME :
  1. chaque objet par-langue porte toutes les langues VIVANTES — sinon la page sert de
     l'anglais à un lecteur qui ne l'a pas demandé, sans erreur et sans blanc ;
  2. chaque objet par-langue porte `nl`, langue DÉCLARÉE mais pas encore ouverte — c'est le
     jalon que le garde des langues vivantes ne peut pas dire, puisqu'il ne regarde que ce
     qui est déjà servi. Le jour où il tombe, on le sait AVANT d'ouvrir la langue.

ANGLE MORT DÉCLARÉ (repris du test) : on ne parcourt que `scores.json` et
`methodology.json`, qui portent le vocabulaire PARTAGÉ. Les fiches portent EN PLUS leur
prose propre ; c'est `check_langue_servie.py` qui la regarde, sur le HTML servi.
"""
import json
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
DONNEE_SERVIE = RACINE / "site" / "public" / "data"
LANGUES_TS = RACINE / "site" / "src" / "content" / "langues.ts"
FICHIERS = ("scores.json", "methodology.json")

# Langue déclarée, pas encore vivante, dont on tient le jalon.
JALON = "nl"


def _langues(nom: str) -> list[str]:
    """Lues à leur source unique — jamais recopiées ici."""
    m = re.search(rf"{nom} = \[([^\]]*)\]", LANGUES_TS.read_text(encoding="utf-8"))
    if not m:
        print(f"✗ {nom} introuvable dans {LANGUES_TS.name} — la barrière ne sait plus "
              f"quelles langues comparer")
        sys.exit(1)
    return re.findall(r'"(\w+)"', m.group(1))


def _objets_par_langue(noeud, sortie: list) -> None:
    if isinstance(noeud, dict):
        if "fr" in noeud and "en" in noeud and all(
            isinstance(v, str) for v in noeud.values() if v is not None
        ):
            sortie.append(noeud)
            return
        for v in noeud.values():
            _objets_par_langue(v, sortie)
    elif isinstance(noeud, list):
        for v in noeud:
            _objets_par_langue(v, sortie)


def main() -> int:
    manquants = [n for n in FICHIERS if not (DONNEE_SERVIE / n).is_file()]
    if manquants:
        # Après un build, ces fichiers EXISTENT. Leur absence ici n'est pas « rien à
        # comparer » : c'est un build qui n'a pas écrit ce qu'il doit écrire.
        print(f"✗ donnée servie absente APRÈS le build : {', '.join(manquants)} — "
              f"`make build` ne l'a pas écrite, la barrière ne peut rien garantir")
        return 1

    objets: list = []
    for nom in FICHIERS:
        objets_avant = len(objets)
        _objets_par_langue(
            json.loads((DONNEE_SERVIE / nom).read_text(encoding="utf-8")), objets
        )
        if len(objets) == objets_avant:
            print(f"✗ aucun objet par-langue dans {nom} — le relevé ne cherche plus au "
                  f"bon endroit, il ne garde rien")
            return 1

    vivantes = set(_langues("LANGUES_VIVANTES"))
    if len(vivantes) < 2:
        print(f"✗ une seule langue vivante ({sorted(vivantes)}) : rien à comparer")
        return 1

    code = 0

    muettes = {tuple(sorted(o.items())) for o in objets if vivantes - set(o)}
    if muettes:
        exemple = dict(sorted(muettes)[0])
        print(f"✗ {len(muettes)} chaîne(s) distinctes de la donnée servie ne portent pas "
              f"toutes les langues vivantes ({sorted(vivantes)}) : servies telles quelles, "
              f"elles sortent en ANGLAIS sur une page qui ne l'est pas — sans erreur et "
              f"sans blanc. Exemple : {exemple}")
        code = 1

    sans_jalon = [o for o in objets if JALON not in o]
    if sans_jalon:
        print(f"✗ {len(sans_jalon)} objet(s) sur {len(objets)} ne portent pas « {JALON} » — "
              f"un pipeline a cessé de l'émettre. Exemple : {sans_jalon[0]}")
        code = 1

    if code == 0:
        print(f"✓ donnée servie : {len(objets)} objets par-langue · "
              f"{'+'.join(sorted(vivantes))} vivantes servies · « {JALON} » tenu")
    return code


if __name__ == "__main__":
    sys.exit(main())
