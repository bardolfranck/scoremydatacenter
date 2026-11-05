# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Un producteur n'écrit pas un champ par-langue amputé d'une langue DÉCLARÉE.

🔴 CE QUE CE GARDE A TROUVÉ LE JOUR OÙ IL A ÉTÉ ÉCRIT. Les portraits néerlandais servaient
tous, en bas de leur carte de contexte : « Straight-line distances from the reference
coordinate. The rings are distance buffers, not statutory zoning. » Cherchée dans les
gabarits : absente. Elle est écrite DANS LA DONNÉE par notre propre build
(`build_prod_artifacts.py`), en `fr` et `en` seulement — et le repli déclaré `nl → en → fr`
fait alors exactement ce pour quoi il est écrit : il sert l'anglais, sans erreur et sans
blanc [[absence-ressemble-a-zero]].

🔴 ET AUCUN GARDE EXISTANT NE POUVAIT LE VOIR, pour trois raisons qui se complètent — c'est
ça qui vaut d'être retenu :
  · les gardes de parité lisent `site/src/content/`, la copie des GABARITS. Cette phrase
    n'est pas de la copie, c'est de la donnée ;
  · `check_langue_donnee_servie.py` lit la donnée servie, mais seulement `scores.json` et
    `methodology.json` — son angle mort est DÉCLARÉ en en-tête, et la légende de la carte
    vit dans les fiches ;
  · `check_langue_servie.py` l'a bien vue, sur le HTML servi — mais il la comptait dans la
    famille « portrait », au milieu d'une dette de 9 surfaces, donc comme un trou de
    traduction à combler par un traducteur. La cause était à nous.
Trois instruments, chacun juste dans son périmètre, et un défaut qui passe entre les trois
[[controle-au-mauvais-niveau]].

Ce test juge la SOURCE des producteurs, là où la faute est écrite — pas l'artefact, qui ne
dirait que la conséquence, et pas avant un build.
"""
from __future__ import annotations

import ast
import re

import pytest

from engine.core import REPO_ROOT
from engine.langues import langues_declarees, langues_vivantes

# Les deux dossiers qui ÉMETTENT de la donnée servie. Les tests n'en sont pas : ils ont le
# droit de fabriquer un champ bilingue pour éprouver un garde.
PRODUCTEURS = ("engine", "scripts")

# Un champ par-langue se reconnaît à sa FORME : toutes ses clés sont des codes de langue à
# deux lettres, et le français et l'anglais y sont. Pas à son nom, qui change à chaque usage
# (`caveat`, `label`, `title`, `summary`…) — et une heuristique sur le nom laisserait passer
# le prochain [[liste-a-deux-endroits-ment]].
CODE_DE_LANGUE = re.compile(r"^[a-z]{2}$")

# Les dicts par-langue dont une langue manque POUR UNE RAISON ÉCRITE. Chaque entrée est une
# dette nommée, pas une exemption de confort, et le test exige qu'elle existe encore : une
# ligne qui ne correspond plus à rien est retirée, sinon la liste devient un cimetière qui
# dispense d'un défaut réel [[exemption-nest-pas-obligation]].
DETTES: dict[str, str] = {}


def _dicts_par_langue(fichier) -> list[tuple[int, set[str]]]:
    """(ligne, clés) de chaque littéral par-langue du fichier."""
    try:
        arbre = ast.parse(fichier.read_text(encoding="utf-8"))
    except SyntaxError:  # pragma: no cover — un fichier cassé est le problème d'un autre test
        return []
    trouves = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Dict):
            continue
        if any(k is None for k in noeud.keys):  # `{**autre}` : forme inconnue, on ne juge pas
            continue
        cles = {
            k.value for k in noeud.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str)
        }
        if len(cles) != len(noeud.keys) or not cles:
            continue
        if not all(CODE_DE_LANGUE.match(c) for c in cles):
            continue
        if {"fr", "en"} <= cles:
            trouves.append((noeud.lineno, cles))
    return trouves


def _sources_productrices() -> list:
    return sorted(
        p
        for dossier in PRODUCTEURS
        for p in (REPO_ROOT / dossier).rglob("*.py")
        if "tests" not in p.parts and not p.name.startswith("test_")
    )


def test_un_producteur_emet_chaque_langue_declaree():
    """Tout champ par-langue écrit par nos outils porte chaque langue DÉCLARÉE.

    DÉCLARÉE, pas vivante : une langue en préparation se relit sur les pages de préviz, et
    elle ne peut pas se relire si la donnée n'a pas sa colonne. Le jour de la bascule, il n'y
    a rien à rattraper — et c'est aussi ce qui fait que la faute se voit AVANT la mise en
    ligne plutôt qu'après.
    """
    attendues = set(langues_declarees())
    fautes = []
    for fichier in _sources_productrices():
        # Relatif quand le fichier est du dépôt, absolu sinon : une contre-épreuve
        # fabrique son producteur ailleurs, et un garde n'a pas le droit de tomber sur
        # l'éprouvette qui le vérifie.
        rel = (
            str(fichier.relative_to(REPO_ROOT))
            if fichier.is_relative_to(REPO_ROOT)
            else str(fichier)
        )
        for ligne, cles in _dicts_par_langue(fichier):
            if manquantes := attendues - cles:
                adresse = f"{rel}:{ligne}"
                if adresse in DETTES:
                    continue
                fautes.append(
                    f"  {adresse} — porte {', '.join(sorted(cles))}, il manque "
                    f"{', '.join(sorted(manquantes))}"
                )
    assert not fautes, (
        f"{len(fautes)} champ(s) par-langue produit(s) sans toutes les langues déclarées "
        f"({', '.join(sorted(attendues))}) :\n" + "\n".join(fautes)
        + "\n\nCe n'est pas une page qui manquera : c'est le repli `langue → en → fr` qui "
        "servira une autre langue, sans erreur et sans blanc. Ajoutez la colonne, ou "
        "déclarez la dette dans DETTES avec sa raison."
    )


def test_le_releve_de_champs_par_langue_voit_ce_qu_il_doit_voir():
    """Contre-épreuve du RELEVÉ, sur les formes qui l'ont piégé ou pourraient le piéger.

    Un relevé qui ne trouve rien ne dit pas qu'il n'a rien trouvé : il dit que tout va bien.
    """
    class Faux:
        def __init__(self, texte: str) -> None:
            self._t = texte

        def read_text(self, encoding: str = "utf-8") -> str:
            return self._t

    # Il voit la forme fautive, y compris étalée sur plusieurs lignes et en concaténation
    # implicite — c'est exactement l'écriture de la légende qui a été trouvée.
    vu = _dicts_par_langue(Faux(
        'x = {\n  "fr": "une phrase "\n        "coupée",\n  "en": "a split "\n'
        '        "sentence",\n}\n'
    ))
    assert vu and vu[0][1] == {"fr", "en"}

    # Il relève AUSSI les dicts complets — c'est un relevé, pas un verdict : savoir ce qui
    # manque est le travail du test, et confondre les deux niveaux m'a fait écrire une
    # contre-épreuve qui exigeait le contraire de ce que la fonction doit faire.
    assert _dicts_par_langue(Faux('x = {"fr": "a", "en": "b", "nl": "c"}'))[0][1] == {
        "fr", "en", "nl",
    }
    # Il ne relève pas un dict qui n'est pas par-langue mais qui porte des clés de langue,
    assert not _dicts_par_langue(Faux('x = {"fr": "a", "en": "b", "label": "c"}'))
    # ni sur un dict dont les clés ne sont pas des codes de langue,
    assert not _dicts_par_langue(Faux('x = {"high": "a", "low": "b"}'))
    # ni sur une forme dont il ne peut rien dire (clés calculées, `**`).
    assert not _dicts_par_langue(Faux('x = {cle: "a", "en": "b"}'))
    assert not _dicts_par_langue(Faux('x = {**autre, "fr": "a", "en": "b"}'))


def test_le_garde_des_producteurs_mord_vraiment(monkeypatch, tmp_path):
    """Contre-épreuve du GARDE : un producteur fautif fabriqué doit le faire rougir.

    Et la dette déclarée doit le taire — sinon la seule façon de livrer serait de retirer le
    garde, et un garde qu'on retire ne garde rien.
    """
    faux = tmp_path / "producteur.py"
    faux.write_text('CAVEAT = {"fr": "a", "en": "b"}\n', encoding="utf-8")
    monkeypatch.setitem(globals(), "_sources_productrices", lambda: [faux])
    monkeypatch.setitem(globals(), "langues_declarees", lambda: ["fr", "en", "nl"])

    with pytest.raises(AssertionError, match="il manque nl"):
        test_un_producteur_emet_chaque_langue_declaree()

    monkeypatch.setitem(globals(), "DETTES", {f"{faux}:1": "éprouvette"})
    test_un_producteur_emet_chaque_langue_declaree()


# ─────────────────────────────────────────────────────────────────────────────────────────
# La barrière d'après-build, vue depuis la suite — ce qu'on peut en dire SANS `site/dist`
# ─────────────────────────────────────────────────────────────────────────────────────────


def test_la_barriere_de_langue_servie_tient_debout():
    """La barrière s'importe, et son périmètre couvre chaque langue en préparation.

    🔴 ÉCRIT PARCE QUE JE L'AI CASSÉE. En réécrivant le commentaire de `DETTE_SURFACES_NL`,
    j'ai emporté la déclaration `PAYS_DE_LA_LANGUE` juste au-dessus : la barrière levait un
    `NameError` à la première famille de fiches. **Et la suite est restée verte** — 370 tests
    au vert pendant que la barrière de déploiement ne démarrait plus, parce que rien ici ne
    l'exerçait : elle réclame un `site/dist`, qui n'existe pas au moment des tests.

    Un contrôle qu'on ne peut pas faire tourner entièrement, on en vérifie la part
    décidable : qu'il s'importe, et que son périmètre déclaré couvre bien les langues qu'il
    doit garder. Le reste (le compte) appartient à l'artefact
    [[controle-au-mauvais-niveau]].
    """
    import importlib

    barriere = importlib.import_module("scripts.check_langue_servie")

    assert isinstance(getattr(barriere, "PAYS_DE_LA_LANGUE", None), dict), (
        "PAYS_DE_LA_LANGUE a disparu de check_langue_servie.py — la barrière ne sait plus "
        "quelles fiches doivent leur prose à quelle langue, et elle lève avant de compter"
    )
    assert isinstance(getattr(barriere, "DETTE_SURFACES_NL", None), int)

    vivantes = set(langues_vivantes())
    en_preparation = [lg for lg in langues_declarees() if lg not in vivantes]
    manquantes = [lg for lg in en_preparation if lg not in barriere.PAYS_DE_LA_LANGUE]
    assert not manquantes, (
        f"langue(s) en préparation sans pays déclaré dans PAYS_DE_LA_LANGUE : "
        f"{', '.join(manquantes)}. La barrière tire son échantillon de fiches par pays ; "
        f"sans entrée, elle ne saurait pas quelles fiches sont dues dans cette langue."
    )
    for lg, prefixes in barriere.PAYS_DE_LA_LANGUE.items():
        assert prefixes and all(
            isinstance(x, str) and CODE_DE_LANGUE.match(x) for x in prefixes
        ), f"préfixes de pays douteux pour {lg} : {prefixes!r}"
