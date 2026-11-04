# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Extrait le bloc juridique en paquet de traduction — l'ARBRE est la vérité.

Le paquet n'est pas une seconde source : il est DÉRIVÉ de `content/procedure/*.ts` à
chaque passe, néerlandais déjà posé compris. C'est la seule façon de ne pas se retrouver
avec deux listes qui divergent — et ça s'est produit dès la première passe : la #304 a
réécrit l'autorité néerlandaise entre l'extraction et la traduction, et le traducteur a
rendu une version fidèle d'un texte qui n'existait plus.

Ré-extraire avant chaque passe, donc, et jamais travailler sur un paquet de la veille.

`id` est `<pays>#<rang>` : le rang du champ dans son fichier. C'est l'ancrage dont se sert
`injecter_traduction_procedure.py` au retour — 42 des 94 champs américains portent la même
phrase, le texte seul ne les distingue pas.

Usage : python3 scripts/extraire_traduction_procedure.py <sortie.json>
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SRC = Path(
    os.environ.get("SMDC_PROCEDURE_DIR")
    or Path(__file__).resolve().parents[1] / "site" / "src" / "content" / "procedure"
)

# Le même découpage que l'injecteur et que le cliquet du test : extraction, injection et
# garde doivent voir LES MÊMES champs, sinon les rangs ne parlent pas de la même chose.
PROSE = re.compile(r'fr:\s*"((?:[^"\\]|\\.)*)",\s*en:\s*"((?:[^"\\]|\\.)*)",', re.S)
NL_POSE = re.compile(r'\s*nl:\s*"((?:[^"\\]|\\.)*)",', re.S)
CITE = re.compile(r'cite:\s*"((?:[^"\\]|\\.)*)"')


def _desechappe(s: str) -> str:
    return s.replace('\\"', '"').replace("\\\\", "\\")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    sortie = Path(sys.argv[1])

    champs = []
    for chemin in sorted(SRC.glob("*.ts")):
        if chemin.name == "types.ts":
            continue  # des déclarations de type, pas des chaînes
        texte = chemin.read_text(encoding="utf-8")
        for rang, m in enumerate(PROSE.finditer(texte)):
            nl = NL_POSE.match(texte, m.end())
            # Le `cite` qui SUIT la prose : la structure met `text` puis `cite`, et le
            # traducteur doit savoir de quel article parle la phrase qu'il traduit.
            c = CITE.search(texte[m.end() : m.end() + 600])
            champs.append({
                "id": f"{chemin.stem}#{rang}",
                "fichier": chemin.name,
                "cite": c.group(1) if c else None,
                "fr": _desechappe(m.group(1)),
                "en": _desechappe(m.group(2)),
                "nl": _desechappe(nl.group(1)) if nl else "",
            })

    sortie.write_text(json.dumps(champs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reste = [c for c in champs if not c["nl"]]
    print(f"{len(champs)} champs → {sortie}")
    print(f"{len(champs) - len(reste)} déjà en néerlandais, {len(reste)} à traduire")
    par_fichier: dict[str, int] = {}
    for c in reste:
        par_fichier[c["fichier"]] = par_fichier.get(c["fichier"], 0) + 1
    if par_fichier:
        print("  " + " · ".join(f"{k.removesuffix('.ts')} {v}" for k, v in sorted(par_fichier.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
