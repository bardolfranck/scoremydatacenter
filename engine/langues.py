# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Les langues du site, lues par le Python à la source UNIQUE qui les déclare.

🔴 POURQUOI UN LECTEUR ET PAS UNE LISTE. `site/src/content/langues.ts` décide quelles langues
sont servies et lesquelles s'écrivent encore. Le TypeScript le lit, les tests le lisent, la
barrière d'après-build le lit. Les PRODUCTEURS, eux, ne le lisaient pas : ils écrivaient
`{"fr": …, "en": …}` en dur dans la donnée. Une langue déclarée n'arrivait donc jamais jusqu'à
ce qu'ils émettent, et le repli `nl → en` servait l'anglais sans qu'une erreur ne soit levée —
trouvé le 2026-11-05 sur la légende de la carte de contexte, qui titrait en anglais sur chaque
portrait néerlandais [[absence-ressemble-a-zero]].

Recopier la liste ici serait la même faute d'un cran plus bas : une énumération à deux endroits
dérive, et c'est toujours la copie qu'on oublie [[liste-a-deux-endroits-ment]].
"""
from __future__ import annotations

import re

from engine.core import REPO_ROOT

LANGUES_TS = REPO_ROOT / "site" / "src" / "content" / "langues.ts"


def _liste(nom: str) -> list[str]:
    texte = LANGUES_TS.read_text(encoding="utf-8")
    m = re.search(rf"{nom} = \[([^\]]*)\]", texte)
    if not m:
        raise AssertionError(
            f"{nom} introuvable dans {LANGUES_TS.name} — un producteur ne sait plus quelles "
            f"langues il doit émettre, et il n'a pas le droit de le deviner"
        )
    langues = re.findall(r'"(\w+)"', m.group(1))
    if not langues:
        raise AssertionError(f"{nom} est vide dans {LANGUES_TS.name}")
    return langues


def langues_vivantes() -> list[str]:
    """Les langues SERVIES. Une page existe dans chacune."""
    return _liste("LANGUES_VIVANTES")


def langues_declarees() -> list[str]:
    """Les langues servies ET celles en cours d'écriture.

    C'est CETTE liste que doit porter un champ par-langue produit par nos outils : une langue
    en préparation se relit sur les pages de préviz, et elle ne peut pas se relire si la
    donnée ne porte pas sa colonne. Le jour de la bascule, rien n'est à rattraper.
    """
    vivantes = langues_vivantes()
    try:
        preparation = _liste("LANGUES_EN_PREPARATION")
    except AssertionError:
        preparation = []
    return vivantes + [lg for lg in preparation if lg not in vivantes]

def pays_de_la_langue() -> dict[str, list[str] | str]:
    """Quelles fiches l'édition d'une langue couvre, lu à la source unique.

    🔴 CETTE LISTE ÉTAIT RECOPIÉE ICI, en dur, dans `check_langue_servie.py`. Elle y était
    juste — et c'est ce qui rend la recopie dangereuse : le jour où la Flandre entre, le
    site bâtit les pages belges et la barrière continue de mesurer les seules `nl-`, donc
    elle se tait sur une édition entière [[liste-a-deux-endroits-ment]].

    `"tous"` veut dire le corpus entier (le français et l'anglais sont les deux éditions de
    référence) ; une liste de préfixes veut dire une édition de pays.
    """
    texte = LANGUES_TS.read_text(encoding="utf-8")
    m = re.search(r"PAYS_DE_LA_LANGUE[^=]*=\s*\{(.*?)\n\};", texte, re.DOTALL)
    if not m:
        raise AssertionError(
            f"PAYS_DE_LA_LANGUE introuvable dans {LANGUES_TS.name} — le périmètre d'une "
            f"édition ne se devine pas depuis le code de langue : il coïncide pour « nl » "
            f"et se trompe pour « en »"
        )
    table: dict[str, list[str] | str] = {}
    for ligne in m.group(1).splitlines():
        cle = re.match(r'\s*(\w+)\s*:\s*(.+?),?\s*$', ligne)
        if not cle:
            continue
        nom, valeur = cle.group(1), cle.group(2).rstrip(",")
        if valeur.strip() == '"tous"':
            table[nom] = "tous"
        elif valeur.strip().startswith("["):
            table[nom] = re.findall(r'"(\w+)"', valeur)
    manquantes = [lg for lg in langues_declarees() if lg not in table]
    if manquantes:
        raise AssertionError(
            f"PAYS_DE_LA_LANGUE ne dit rien de {', '.join(manquantes)} : une édition dont le "
            f"périmètre n'est pas déclaré n'est pas gardée"
        )
    return table


def racine_de_la_langue() -> dict[str, str]:
    """Où vit chaque édition : « / », « /fr/ », « /nl/ ». Lu, pas deviné.

    Sert à retrouver la ROUTE d'une édition depuis son code de langue — un test qui
    composerait le chemin lui-même se tromperait sur la langue servie à la racine.
    """
    texte = LANGUES_TS.read_text(encoding="utf-8")
    m = re.search(r"RACINE[^=]*=\s*\{([^}]*)\}", texte)
    if not m:
        raise AssertionError(f"RACINE introuvable dans {LANGUES_TS.name}")
    table = dict(re.findall(r'(\w+)\s*:\s*"([^"]*)"', m.group(1)))
    manquantes = [lg for lg in langues_declarees() if lg not in table]
    if manquantes:
        raise AssertionError(f"RACINE ne dit pas où vit {', '.join(manquantes)}")
    return table
