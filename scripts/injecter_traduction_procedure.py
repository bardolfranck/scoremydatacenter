# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Réinjecte une traduction du bloc juridique dans `content/procedure/*.ts`.

Le bloc juridique est le seul endroit du site qui dise au lecteur quoi FAIRE. Sa
traduction ne passe donc pas par un copier-coller à la main : elle passe par ici, où
trois choses sont vérifiées AVANT d'écrire.

  1. L'ANCRAGE — par le RANG du champ dans son fichier (`us#92` = le 93e), et le texte
     français et anglais trouvé à ce rang doit être celui du paquet. Pas par le texte
     seul : 42 des 94 champs américains portent LA MÊME phrase (« la commune ou le comté
     qui zone le terrain », une fois par État), et 9 des 30 suisses pareil — 56 champs
     que le texte seul ne sait pas distinguer. Un rang qui ne porte plus le bon texte est
     REFUSÉ, jamais écrasé au petit bonheur.
  2. LES NOMBRES — tout nombre du français doit se retrouver dans le néerlandais. « deux
     mois » qui devient « drie maanden » est une faute de droit, pas une faute de style.
     Même critère que `engine.validate.grandeurs_gate`, IMPORTÉ et non recopié : une
     règle à deux endroits dérive.
  3. L'ORDRE — `nl` se pose juste après `en`, parce que le cliquet du test le vérifie et
     parce que des champs toujours dans le même ordre se relisent en diagonale.

Les champs d'un même fichier sont posés de la FIN vers le DÉBUT : une insertion décale
tout ce qui la suit, et un rang calculé avant l'écriture ne vaut plus après.

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

# Le même motif que l'extraction et que le cliquet du test : extraction, injection et garde
# doivent voir LE MÊME découpage, sinon les rangs ne parlent pas de la même chose.
PROSE = re.compile(r'fr:\s*"((?:[^"\\]|\\.)*)",(\s*)en:\s*"((?:[^"\\]|\\.)*)",', re.S)

# Un `nl` déjà posé, lu À PARTIR de la fin du champ `en` — jamais ailleurs dans le fichier.
_NL_POSE = re.compile(r'(\s*)nl:\s*"((?:[^"\\]|\\.)*)",', re.S)


def _echappe(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    paquet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    ecrire = "--ecrire" in sys.argv

    refus: list[str] = []
    a_poser: dict[str, list[tuple[int, str]]] = {}  # fichier → [(position, littéral nl)]
    a_remplacer: dict[str, list[tuple[int, int, str]]] = {}  # fichier → [(début, fin, nl)]
    textes: dict[str, str] = {}
    deja = 0

    for champ in paquet:
        nl = (champ.get("nl") or "").strip()
        if not nl:
            continue  # pas encore traduit : ce n'est pas une faute, c'est la dette
        nom = champ["fichier"]
        if nom not in textes:
            textes[nom] = (SRC / nom).read_text(encoding="utf-8")
        texte = textes[nom]

        rang = int(champ["id"].rsplit("#", 1)[1])
        trouves = list(PROSE.finditer(texte))
        if rang >= len(trouves):
            refus.append(
                f'{champ["id"]} — {nom} ne porte que {len(trouves)} champs : le fichier a '
                f"changé depuis l'extraction. Ré-extraire, ne pas forcer."
            )
            continue
        m = trouves[rang]
        if m.group(1) != _echappe(champ["fr"]) or m.group(3) != _echappe(champ["en"]):
            refus.append(
                f'{champ["id"]} — le rang {rang} de {nom} ne porte plus le texte du paquet '
                f"(trouvé : « {m.group(1)[:60]}… »). Ré-extraire, ne pas forcer."
            )
            continue

        # Déjà posé ? Le `nl` suit immédiatement le `en` : on regarde LÀ, pas dans tout le
        # fichier — un même néerlandais apparaît légitimement à plusieurs rangs (42 fois,
        # côté américain). Identique : on passe. Différent : on REMPLACE, parce qu'une passe
        # de relecture doit pouvoir corriger sans qu'on aille éditer le .ts à la main.
        #
        # 🔴 Première version non idempotente : la fenêtre de lecture était calculée trop
        # courte, le `nl` posé n'était pas vu, et une seconde passe en écrivait un DOUBLON.
        # Trouvé en relançant l'outil deux fois de suite sur la copie — un outil qu'on
        # n'essaie qu'une fois ne dit rien de ce qu'il fait la deuxième.
        existant = _NL_POSE.match(texte, m.end())
        if existant:
            if existant.group(2) == _echappe(nl):
                deja += 1
                continue
            a_remplacer.setdefault(nom, []).append(
                (existant.start(), existant.end(), f'{existant.group(1)}nl: "{_echappe(nl)}",')
            )
            continue

        manquants = [n for n in _nombres(champ["fr"]) if n not in _nombres(nl)]
        if manquants:
            refus.append(
                f'{champ["id"]} — nombre(s) perdu(s) à la traduction : {manquants}. '
                f"Un délai qui change de valeur en changeant de langue est une faute de droit."
            )
            continue

        indent = m.group(2).rsplit("\n", 1)[-1] if "\n" in m.group(2) else " "
        a_poser.setdefault(nom, []).append((m.end(), f'\n{indent}nl: "{_echappe(nl)}",'))

    poses = corriges = 0
    for nom in sorted(set(a_poser) | set(a_remplacer)):
        texte = textes[nom]
        # Un seul passage, de la FIN vers le DÉBUT : insertions et remplacements décalent
        # tout ce qui les suit, et un rang calculé avant l'écriture ne vaut plus après.
        gestes: list[tuple[int, int, str]] = [
            (p, p, lit) for p, lit in a_poser.get(nom, [])
        ] + a_remplacer.get(nom, [])
        for debut, fin, litteral in sorted(gestes, reverse=True):
            texte = texte[:debut] + litteral + texte[fin:]
        n_pose, n_corr = len(a_poser.get(nom, [])), len(a_remplacer.get(nom, []))
        poses += n_pose
        corriges += n_corr
        if ecrire:
            (SRC / nom).write_text(texte, encoding="utf-8")
        detail = f"{n_pose:3} posé(s)" + (f", {n_corr} corrigé(s)" if n_corr else "")
        print(f"  {nom:14} {detail} {'— écrit' if ecrire else '— à écrire'}")

    print(
        f"\n{poses} posé(s), {corriges} corrigé(s), {deja} déjà en place, "
        f"sur {len(paquet)} champs du paquet"
    )
    if refus:
        print(f"\n{len(refus)} REFUS — rien d'écrit pour ceux-là :")
        for r in refus:
            print(f"  · {r}")
    if not ecrire:
        print("\n(essai à blanc — relancer avec --ecrire)")
    return 1 if refus else 0


if __name__ == "__main__":
    raise SystemExit(main())
