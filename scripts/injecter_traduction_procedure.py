#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
"""Réinjecte une traduction du bloc juridique dans `content/procedure/*.ts`.

Le bloc juridique est le seul endroit du site qui dise au lecteur quoi FAIRE. Sa
traduction ne passe donc pas par un copier-coller à la main : elle passe par ici, où
trois choses sont vérifiées AVANT d'écrire.

  1. L'ANCRAGE — on retrouve le champ par son texte français ET son anglais, pas par un
     numéro de ligne. Un champ qui a bougé n'est pas écrasé au mauvais endroit : il est
     refusé, et l'outil dit lequel.
  2. LES NOMBRES — tout nombre du français doit se retrouver dans le néerlandais. « deux
     mois » qui devient « drie maanden » est une faute de droit, pas une faute de style.
     Même critère que `engine.validate.grandeurs_gate`, IMPORTÉ et non recopié : une
     règle à deux endroits dérive.
  3. L'ORDRE — `nl` se pose juste après `en`, parce que le cliquet du test le vérifie et
     parce que des champs toujours dans le même ordre se relisent en diagonale.

Usage : python3 scripts/injecter_traduction_procedure.py <paquet.json> [--ecrire]
Sans --ecrire, l'outil ne fait que dire ce qu'il ferait.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.validate import _nombres  # la MÊME règle que le garde du corpus

# Le dossier servi. `SMDC_PROCEDURE_DIR` ne sert qu'à ÉPROUVER l'outil sur une copie :
# un outil qui écrit dans le corpus doit pouvoir être essayé ailleurs que dans le corpus.
SRC = Path(
    os.environ.get("SMDC_PROCEDURE_DIR")
    or Path(__file__).resolve().parents[1] / "site" / "src" / "content" / "procedure"
)


def _echappe(s: str) -> str:
    """Le littéral tel qu'il doit apparaître dans le .ts (les guillemets, puis rien d'autre)."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    paquet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    ecrire = "--ecrire" in sys.argv

    refus: list[str] = []
    poses = 0
    par_fichier: dict[str, str] = {}

    for champ in paquet:
        nl = (champ.get("nl") or "").strip()
        if not nl:
            continue  # pas encore traduit : ce n'est pas une faute, c'est la dette
        nom = champ["fichier"]
        texte = par_fichier.get(nom) or (SRC / nom).read_text(encoding="utf-8")

        ancre = f'fr: "{_echappe(champ["fr"])}",'
        suite = f'\n      en: "{_echappe(champ["en"])}",'
        # L'indentation varie selon la profondeur : on retrouve la paire sans la supposer.
        motif = re.compile(
            re.escape(ancre) + r'(\s*)en:\s*"' + re.escape(_echappe(champ["en"])) + r'",'
        )
        trouves = motif.findall(texte)
        if len(trouves) != 1:
            refus.append(
                f'{champ["id"]} — {len(trouves)} ancrage(s) dans {nom} : le français ou '
                f"l'anglais a changé depuis l'extraction. Ré-extraire, ne pas forcer."
            )
            continue
        if f'nl: "{_echappe(nl)}"' in texte:
            continue  # déjà posé, passe idempotente

        manquants = [n for n in _nombres(champ["fr"]) if n not in _nombres(nl)]
        if manquants:
            refus.append(
                f'{champ["id"]} — nombre(s) perdu(s) à la traduction : {manquants}. '
                f"Un délai qui change de valeur en changeant de langue est une faute de droit."
            )
            continue

        def _pose(m: re.Match) -> str:
            blanc = m.group(1)
            indent = blanc.rsplit("\n", 1)[-1] if "\n" in blanc else " "
            return m.group(0) + f'\n{indent}nl: "{_echappe(nl)}",'

        texte, n = motif.subn(_pose, texte, count=1)
        assert n == 1
        par_fichier[nom] = texte
        poses += 1

    for nom, texte in sorted(par_fichier.items()):
        if ecrire:
            (SRC / nom).write_text(texte, encoding="utf-8")
        print(f"  {nom:14} {'écrit' if ecrire else 'à écrire'}")

    print(f"{poses} champ(s) posé(s) sur {len(paquet)}")
    if refus:
        print(f"\n{len(refus)} REFUS — rien d'écrit pour ceux-là :")
        for r in refus:
            print(f"  · {r}")
    if not ecrire:
        print("\n(essai à blanc — relancer avec --ecrire)")
    return 1 if refus else 0


if __name__ == "__main__":
    raise SystemExit(main())
