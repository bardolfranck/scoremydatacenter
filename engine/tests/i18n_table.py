# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Lire une table de chaînes TypeScript depuis les tests — UNE seule implémentation.

Trois tests ont besoin de la même lecture (`test_i18n_parity`, `test_content_coherence`,
et le garde du gabarit) : écrite trois fois, elle dériverait trois fois. Un instrument de
mesure dupliqué est le même défaut qu'une énumération dupliquée.

🔴 LE SCANNER SAUTE LES COMMENTAIRES, et ce n'est pas une précaution de principe. Sans cela,
l'apostrophe de `l'unité` dans un `//` ouvre une fausse chaîne : les accolades du reste du
commentaire cessent d'être comptées, le littéral se ferme UNE ACCOLADE TROP TÔT, et la
lecture perd sa queue sans rien dire. C'est arrivé le 2026-10-29 en sortant la table de la
fiche — la table EN s'arrêtait sur `related: {…}` au lieu du `};` final, et le compte de
clés restait juste par chance, parce que rien ne suivait. Un lecteur qui ne voit que la
moitié d'une table la déclare à parité : d'où la post-condition sur le `;` final.
"""

import re

_CLE = re.compile(r"^\s*([A-Za-z_]\w*)\s*:")


def bloc(texte: str, declaration: str) -> str:
    """Le littéral objet de `const <declaration> = {…}`, accolades équilibrées.

    Tolère une annotation de type (`const EN: typeof FR = {`). Une regex ne compte pas les
    accolades, et c'est l'imbrication qui porte le sens d'une clé : `statusCheck.verified`
    n'est pas `verified`.
    """
    m = re.search(rf"const {re.escape(declaration)}\b[^=\n]*=\s*\{{", texte)
    if not m:
        raise AssertionError(
            f"déclaration `const {declaration}` introuvable — un test qui ne trouve plus "
            f"sa table ne garde rien, et son silence ressemble à un succès"
        )
    i = texte.index("{", m.start())
    profondeur, j, chaine = 0, i, None
    while j < len(texte):
        c, duo = texte[j], texte[j : j + 2]
        if chaine:
            if c == "\\":
                j += 2
                continue
            if c == chaine:
                chaine = None
        elif duo == "//":
            j = texte.find("\n", j)
            if j < 0:
                break
            continue
        elif duo == "/*":
            fin = texte.find("*/", j + 2)
            if fin < 0:
                break
            j = fin + 2
            continue
        elif c in "\"'`":
            chaine = c
        elif c == "{":
            profondeur += 1
        elif c == "}":
            profondeur -= 1
            if profondeur == 0:
                suite = texte[j + 1 :].lstrip()
                if not suite.startswith(";"):
                    raise AssertionError(
                        f"`{declaration}` : le littéral ne se termine pas sur un `;` mais sur "
                        f"{suite[:20]!r} — la lecture s'est arrêtée au mauvais endroit, et "
                        f"tout ce qui suit n'a pas été vu"
                    )
                return texte[i : j + 1]
        j += 1
    raise AssertionError(f"accolade non fermée pour `{declaration}`")


def chemins(litteral: str) -> set[str]:
    """Les CHEMINS de clés : `a`, `a.b`, `a.b.c`.

    Le chemin et non la clé nue : `statusCheck.verified` et `confidence.high` ne se
    confondent pas, et une clé déplacée d'un groupe à l'autre se voit.
    """
    sortie: set[str] = set()
    pile: list[str] = []
    for ligne in litteral.splitlines():
        nue = ligne.strip()
        if nue.startswith("//"):
            continue
        m = _CLE.match(ligne)
        if m:
            sortie.add(".".join(pile + [m.group(1)]))
            if nue.endswith("{"):
                pile.append(m.group(1))
                continue
        if nue.startswith("}") and pile:
            pile.pop()
    return sortie
