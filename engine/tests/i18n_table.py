# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Lire une table de chaînes TypeScript depuis les tests — UNE seule implémentation.

Plusieurs tests ont besoin de la même lecture (`test_i18n_parity`, `test_content_coherence`,
le garde du gabarit) : écrite plusieurs fois, elle dériverait plusieurs fois. Un instrument
de mesure dupliqué est le même défaut qu'une énumération dupliquée.

Deux défauts vécus le 2026-10-29, tous deux du même genre — l'instrument lisait moins que
la table et son silence ressemblait à un succès :

  🔴 **Les commentaires.** L'apostrophe de `l'unité` dans un `//` ouvrait une fausse chaîne :
  les accolades du reste du commentaire cessaient d'être comptées, le littéral se fermait UNE
  ACCOLADE TROP TÔT, et la table amputée paraissait complète (la table EN de la fiche
  s'arrêtait sur `related: {…}`, et le compte de clés restait juste par chance). D'où le saut
  des commentaires ET la post-condition sur le `;` final.

  🔴 **La mise en forme.** La première version relevait les clés LIGNE PAR LIGNE, donc ne
  voyait que celles en début de ligne. Le même objet écrit `{ h2: …, corps: … }` sur une
  ligne ou sur deux donnait deux jeux de clés différents : la paire notation/rating a été
  signalée en dérive alors qu'elle était identique. Un faux positif se voit ; le faux
  NÉGATIF du même défaut — une clé vraiment absente, masquée par une ligne compacte — ne se
  voit pas. D'où la lecture caractère par caractère ci-dessous.
"""

import re

_IDENT = re.compile(r"[A-Za-z_$][\w$]*")


def _saute_blanc_et_commentaires(texte: str, i: int) -> int:
    """L'indice du prochain caractère signifiant à partir de `i`."""
    while i < len(texte):
        if texte[i].isspace():
            i += 1
        elif texte[i : i + 2] == "//":
            saut = texte.find("\n", i)
            i = len(texte) if saut < 0 else saut + 1
        elif texte[i : i + 2] == "/*":
            fin = texte.find("*/", i + 2)
            i = len(texte) if fin < 0 else fin + 2
        else:
            return i
    return i


def _fin_de_chaine(texte: str, i: int) -> int:
    """L'indice juste après la chaîne qui commence en `i` (`"`, `'` ou backtick)."""
    delim, j = texte[i], i + 1
    while j < len(texte):
        if texte[j] == "\\":
            j += 2
            continue
        if texte[j] == delim:
            return j + 1
        j += 1
    raise AssertionError("chaîne non terminée")


def bloc(texte: str, declaration: str) -> str:
    """Le littéral objet de `const <declaration> = {…}`, accolades équilibrées.

    Tolère une annotation de type (`const EN: typeof FR = {`).
    """
    m = re.search(rf"const {re.escape(declaration)}\b[^=\n]*=\s*\{{", texte)
    if not m:
        raise AssertionError(
            f"déclaration `const {declaration}` introuvable — un test qui ne trouve plus "
            f"sa table ne garde rien, et son silence ressemble à un succès"
        )
    i = texte.index("{", m.start())
    profondeur, j = 0, i
    while j < len(texte):
        c = texte[j]
        if c in "\"'`":
            j = _fin_de_chaine(texte, j)
            continue
        if texte[j : j + 2] in ("//", "/*"):
            j = _saute_blanc_et_commentaires(texte, j)
            continue
        if c == "{":
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
    """Les CHEMINS de clés d'un littéral objet : `a`, `a.b`, `a.b.c`.

    Lecture caractère par caractère, insensible à la mise en forme : une clé compte qu'elle
    soit seule sur sa ligne ou au milieu. Les éléments d'un tableau n'ajoutent pas de segment
    (ils n'ont pas de nom) — les clés de `sections: [{ h2, corps }]` sortent donc en
    `sections.h2` et `sections.corps`, et les cinq éléments se confondent, ce qui est
    exactement ce qu'on veut comparer entre deux langues.

    Le chemin et non la clé nue : `statusCheck.verified` et `confidence.high` ne se
    confondent pas, et une clé déplacée d'un groupe à l'autre se voit.

    🔴 Une clé n'est reconnue QUE là où une clé peut commencer : juste après `{`, ou après
    une virgule dans un objet. Sans cette discipline, le `:` d'un ternaire dans une valeur
    (`k: cond ? x : y`) fait passer `x` pour une clé — un fantôme qui n'existe que d'un côté
    si l'autre langue écrit la même valeur autrement.
    """
    sortie: set[str] = set()
    prefixe: list[str] = []
    # Par conteneur ouvert : (type, segment de préfixe ajouté ou None).
    pile: list[tuple[str, str | None]] = []
    attente: str | None = None  # la clé dont on attend la valeur
    attend_cle = False

    i = _saute_blanc_et_commentaires(litteral, 0)
    assert litteral[i] == "{", "un littéral objet commence par `{`"

    while i < len(litteral):
        i = _saute_blanc_et_commentaires(litteral, i)
        if i >= len(litteral):
            break
        c = litteral[i]

        if c in "{[":
            segment = attente
            pile.append(("obj" if c == "{" else "arr", segment))
            if segment is not None:
                prefixe.append(segment)
            attente = None
            attend_cle = c == "{"
            i += 1
            continue

        if c in "}]":
            if pile:
                _, segment = pile.pop()
                if segment is not None and prefixe and prefixe[-1] == segment:
                    prefixe.pop()
            attente = None
            attend_cle = bool(pile) and pile[-1][0] == "obj"
            i += 1
            continue

        if c in "\"'`":
            fin = _fin_de_chaine(litteral, i)
            apres = _saute_blanc_et_commentaires(litteral, fin)
            # une chaîne peut être une CLÉ : `"a-b": …`
            if attend_cle and apres < len(litteral) and litteral[apres] == ":":
                nom = litteral[i + 1 : fin - 1]
                sortie.add(".".join(prefixe + [nom]))
                attente, attend_cle = nom, False
                i = apres + 1
                continue
            i = fin
            continue

        m = _IDENT.match(litteral, i)
        if m:
            apres = _saute_blanc_et_commentaires(litteral, m.end())
            if attend_cle and apres < len(litteral) and litteral[apres] == ":":
                sortie.add(".".join(prefixe + [m.group()]))
                attente, attend_cle = m.group(), False
                i = apres + 1
                continue
            i = m.end()
            continue

        if c == ",":
            attente = None
            attend_cle = bool(pile) and pile[-1][0] == "obj"
        i += 1

    return sortie
