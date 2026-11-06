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
