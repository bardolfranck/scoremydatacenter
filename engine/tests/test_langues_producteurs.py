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
from engine.tests.i18n_table import bloc, chemins

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


def _paires_suffixe(fichier) -> list[tuple[int, str, set[str]]]:
    """(ligne, racine, langues) de chaque champ par-langue écrit en SUFFIXE.

    🔴 LA MÊME FAUTE, UNE AUTRE ORTHOGRAPHE, ET ELLE M'A ÉCHAPPÉ. Le relevé par dict ne voit
    que `{"fr": …, "en": …}`. Trois champs s'écrivaient en clés SŒURS — `statut_fr` /
    `statut_en` dans le comparateur, `activity_fr` / `activity_en` deux fois dans les
    artefacts — et aucun ne portait `_nl`. Un garde qui ne connaît qu'une écriture de ce
    qu'il cherche mesure l'écriture, pas la chose [[controle-au-mauvais-niveau]].
    """
    try:
        arbre = ast.parse(fichier.read_text(encoding="utf-8"))
    except SyntaxError:  # pragma: no cover
        return []
    trouves = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Dict):
            continue
        cles = {
            k.value for k in noeud.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str)
        }
        racines = {c.rsplit("_", 1)[0] for c in cles if c.rsplit("_", 1)[-1] == "fr"} & {
            c.rsplit("_", 1)[0] for c in cles if c.rsplit("_", 1)[-1] == "en"
        }
        for racine in sorted(r for r in racines if r):
            langues = {
                c.rsplit("_", 1)[-1] for c in cles
                if c.startswith(f"{racine}_") and CODE_DE_LANGUE.match(c.rsplit("_", 1)[-1])
            }
            trouves.append((noeud.lineno, racine, langues))
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
        # La forme SUFFIXE : `x_fr` / `x_en` comme clés sœurs du même dict.
        for ligne, racine, langues in _paires_suffixe(fichier):
            if manquantes := attendues - langues:
                adresse = f"{rel}:{ligne}"
                if adresse in DETTES:
                    continue
                fautes.append(
                    f"  {adresse} — `{racine}_*` porte {', '.join(sorted(langues))}, il "
                    f"manque {', '.join(f'{racine}_{lg}' for lg in sorted(manquantes))}"
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


# ─────────────────────────────────────────────────────────────────────────────────────────
# Les libellés de statut : une liste de CODES, trois surfaces, et le schéma pour autorité
# ─────────────────────────────────────────────────────────────────────────────────────────

# Les pages qui portent la légende des statuts, une par langue servie ou en préparation.
PAGES_CLASSEMENT = (
    "fr/classement.astro",
    "ranking.astro",
    "nl/ranglijst.astro",
)


def _enum_project_status() -> set[str]:
    """Les codes de statut AUTORISÉS — lus au schéma, qui en est l'autorité."""
    import json

    schema = json.loads(
        (REPO_ROOT / "data" / "schema" / "datacenter.schema.json").read_text(encoding="utf-8")
    )
    pile = [schema]
    while pile:
        noeud = pile.pop()
        if isinstance(noeud, dict):
            cible = noeud.get("project_status")
            if isinstance(cible, dict) and "enum" in cible:
                return set(cible["enum"])
            pile.extend(v for v in noeud.values() if isinstance(v, (dict, list)))
        elif isinstance(noeud, list):
            pile.extend(v for v in noeud if isinstance(v, (dict, list)))
    raise AssertionError(
        "enum project_status introuvable dans datacenter.schema.json — ce test ne sait plus "
        "quels codes existent, et il ne peut donc rien affirmer"
    )


def test_les_libelles_de_statut_collent_a_l_enum_du_schema():
    """Chaque code du schéma a son libellé, et aucun libellé ne nomme un code inexistant.

    🔴 DANS LES DEUX SENS, parce que la faute trouvée le 2026-11-05 allait dans les deux.
    `build_comparator.py` portait DOUZE libellés pour les CINQ codes du schéma : il écrivait
    `construction` là où le schéma dit `under_construction`, ignorait `unknown` — deux codes
    réels sans libellé, sur 28 fiches — et déclarait huit codes qui n'existent nulle part.
    Un test qui n'aurait vérifié qu'un sens aurait laissé passer l'une ou l'autre moitié :
    « tout code a un libellé » ne voit pas les huit fantômes, « tout libellé a un code » ne
    voit pas les deux manques [[gate-deux-populations-meme-racine]].

    ⚠️ Ce n'était pas un défaut SERVI — les 28 fiches n'entrent pas dans le comparateur. Ce
    test garde le piège fermé, il ne répare pas une fuite.

    Et il compare des ENSEMBLES DE CODES, jamais des mots : le comparateur et le classement
    servent volontairement d'autres formulations pour le même statut (« Site implanté » vs
    « En service »), ce qui est un arbitrage éditorial ouvert, pas une dérive à corriger ici.
    """
    import importlib

    codes = _enum_project_status()
    attendues = set(langues_declarees())

    comparateur = importlib.import_module("scripts.build_comparator")
    statuts = getattr(comparateur, "STATUTS", None)
    assert isinstance(statuts, dict) and statuts, (
        "STATUTS a disparu de build_comparator.py — sans elle le comparateur n'a plus de "
        "libellés, et ce test ne garde plus rien"
    )
    assert set(statuts) == codes, (
        f"les libellés du comparateur ne collent pas à l'enum du schéma :\n"
        f"  codes sans libellé : {sorted(codes - set(statuts)) or '—'}\n"
        f"  libellés sans code : {sorted(set(statuts) - codes) or '—'}"
    )
    amputes = {
        code: sorted(attendues - set(libelles))
        for code, libelles in statuts.items()
        if attendues - set(libelles)
    }
    assert not amputes, (
        f"libellé(s) de statut sans toutes les langues déclarées : {amputes}"
    )

    # Et la légende du classement, dans chaque langue : mêmes codes, pas un de plus.
    for page in PAGES_CLASSEMENT:
        chemin = REPO_ROOT / "site" / "src" / "pages" / page
        assert chemin.is_file(), f"{page} a disparu — la légende des statuts n'est plus gardée"
        cles = {
            c.split(".", 1)[1]
            for c in chemins(bloc(chemin.read_text(encoding="utf-8"), "t"))
            if c.startswith("status.")
        }
        assert cles == codes, (
            f"{page} : la légende des statuts ne colle pas à l'enum du schéma\n"
            f"  codes sans libellé : {sorted(codes - cles) or '—'}\n"
            f"  libellés sans code : {sorted(cles - codes) or '—'}\n"
            f"Une légende déclarée page par page dérive de l'enum sans que rien ne crie."
        )


# ─────────────────────────────────────────────────────────────────────────────────────────
# Les tables PAR LANGUE du TypeScript : `Record<LangueDeclaree, …>` tient-il sa promesse ?
# ─────────────────────────────────────────────────────────────────────────────────────────


def _tables_par_langue_ts(texte: str) -> list[tuple[str, set[str]]]:
    """(nom, langues) de chaque `Record<LangueDeclaree, …>` du module.

    Relevé sur la FORME du type, pas sur le nom de la table : `RACINE`, `REGLE_PLURIEL`,
    `LOCALE`, `SEPARATEUR_DECIMAL` n'ont en commun que de promettre une entrée par langue.
    """
    tables = []
    # 🔴 PAS `[^>]*>` POUR LE TYPE. Première version : elle exigeait que le type ne contienne
    # aucun `>`, donc elle ne voyait PAS `Record<LangueDeclaree, (n: number) => FormePluriel>`
    # — la règle du pluriel, précisément l'une des trois qu'il faut garder. Le test passait au
    # vert sur trois tables en en ignorant une quatrième, et seul un relevé AFFICHÉ l'a dit
    # [[controle-au-mauvais-niveau]]. On repère la déclaration, puis on cherche son `= {`.
    for m in re.finditer(r"export const (\w+)\s*:\s*Record<\s*LangueDeclaree\s*,", texte):
        ouverture = texte.find("= {", m.end())
        if ouverture == -1:
            continue
        debut = texte.index("{", ouverture)
        profondeur, i = 0, debut
        while i < len(texte):
            if texte[i] == "{":
                profondeur += 1
            elif texte[i] == "}":
                profondeur -= 1
                if profondeur == 0:
                    break
            i += 1
        corps = texte[debut : i + 1]
        # Les clés de PREMIER niveau seulement : une valeur peut être un objet.
        cles, profondeur = set(), 0
        for m2 in re.finditer(r"[{}]|\b(\w+)\s*:", corps):
            if m2.group(0) == "{":
                profondeur += 1
            elif m2.group(0) == "}":
                profondeur -= 1
            elif profondeur == 1 and m2.group(1):
                cles.add(m2.group(1))
        tables.append((m.group(1), cles))
    return tables


def test_langues_ts_declare_chaque_langue():
    """Chaque `Record<LangueDeclaree, …>` de `langues.ts` porte toutes les langues déclarées.

    🔴 CE QUE LE TYPE NE GARDE PAS, ET POURQUOI CE TEST EXISTE. `site/package.json` lance
    `astro build` SANS `astro check` : `Record<LangueDeclaree, string>` est décoratif, une
    langue manquante rend `undefined` en silence. Ces tables-là sont les plus dangereuses à
    oublier, parce qu'elles ne portent pas des mots mais des RÈGLES — la racine d'une langue,
    son pluriel, sa virgule décimale. Une règle absente ne laisse pas un blanc dans la page :
    elle en applique une autre.

    Le relevé prend les tables à leur TYPE, pas à leur nom : une table ajoutée demain est
    gardée sans qu'on pense à l'inscrire ici.
    """
    texte = (REPO_ROOT / "site" / "src" / "content" / "langues.ts").read_text(encoding="utf-8")
    tables = _tables_par_langue_ts(texte)
    assert len(tables) >= 3, (
        f"{len(tables)} table(s) par langue relevée(s) dans langues.ts — le relevé ne lit "
        f"plus le fichier, et un garde qui ne trouve rien ne dit pas qu'il n'a rien trouvé"
    )
    attendues = set(langues_declarees())
    fautes = [
        f"  · {nom} — porte {', '.join(sorted(langues))}, il manque "
        f"{', '.join(sorted(attendues - langues))}"
        for nom, langues in tables
        if attendues - langues
    ]
    assert not fautes, (
        "table(s) par langue de langues.ts incomplète(s) :\n" + "\n".join(fautes)
        + "\n\nUn `Record<LangueDeclaree, …>` ne garde rien ici : le build ne lance pas "
        "`astro check`, donc la clé manquante rend `undefined` sans erreur."
    )
