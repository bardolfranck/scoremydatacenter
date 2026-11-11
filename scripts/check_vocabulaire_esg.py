# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Barrière avant mise en ligne : nous ne nous décrivons JAMAIS comme une notation ESG.

🔴 POURQUOI UN MOT EST UNE BARRIÈRE. Le règlement (UE) 2024/3005, applicable depuis le
2 juillet 2026, encadre les « notations ESG » et les « scores ESG » (art. 3.1 et 3.3) et
soumet leurs fournisseurs à agrément (art. 3.4). Une note de SITE n'est probablement pas
dans son champ : un site physique n'est pas un « élément noté » au sens de l'art. 3.7.
Mais une page qui écrirait « notation ESG » ou « ESG rating » à propos de notre note nous
décrirait nous-mêmes dans la définition — et la page d'un observatoire est lue comme sa
déclaration. Lecture du texte : 16-ESG/04-reglement-notations-esg.md (2026-11-11).

Ce que nous écrivons : « données ESG au niveau du site », « lecture ESG », « note
environnementale du site ». Ce que ce garde refuse, dans toutes nos langues : « notation
ESG », « score ESG », « note ESG », « classement ESG », « ESG rating / score / ranking »,
« ESG-cijfer », « ESG-beoordeling ».

⚠️ PAS D'EXEMPTION. Une phrase légitime qui nierait l'être (« nous ne sommes pas une
notation ESG ») serait elle aussi refusée : on ne l'écrit pas, on dit ce que nous sommes.
Une liste d'exceptions serait invisible au garde qui la porte [[gate-qui-depasse-son-mandat]].

Il lit ce qui PART (le dist), pas les sources : une chaîne peut entrer par la donnée
(une synthèse, un titre d'actu) aussi bien que par le code.

Usage : python3 scripts/check_vocabulaire_esg.py [dossier] (défaut : site/dist)
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

# Séparateur entre « ESG » et le mot : espace, espace insécable, trait d'union.
_SEP = r"[\s  \-‑]+"
INTERDITS = re.compile(
    r"\b(?:"
    rf"notations?{_SEP}ESG|scores?{_SEP}ESG|notes?{_SEP}ESG|classements?{_SEP}ESG"
    rf"|ESG{_SEP}(?:ratings?|scores?|scoring|rankings?|rated|cijfers?|beoordelings?(?:en)?|ranglijst)"
    r")\b",
    re.IGNORECASE,
)

EXTENSIONS = {".html", ".htm", ".txt", ".xml", ".json", ".md", ".js", ".mjs"}


def fautes(dossier: Path) -> list[str]:
    trouvees: list[str] = []
    for f in sorted(dossier.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in EXTENSIONS:
            continue
        texte = html.unescape(f.read_text(encoding="utf-8", errors="replace"))
        for m in INTERDITS.finditer(texte):
            debut = max(0, m.start() - 60)
            extrait = re.sub(r"\s+", " ", texte[debut:m.end() + 60])
            trouvees.append(f"{f.relative_to(dossier)} : « {m.group(0)} » … {extrait} …")
    return trouvees


def main(argv: list[str]) -> int:
    dossier = Path(argv[1]) if len(argv) > 1 else RACINE / "site" / "dist"
    if not dossier.is_dir():
        print(f"check_vocabulaire_esg : dossier introuvable {dossier} — rien à vérifier n'est PAS un succès")
        return 1
    trouvees = fautes(dossier)
    if trouvees:
        print(f"check_vocabulaire_esg : {len(trouvees)} occurrence(s) d'un terme qui nous "
              "décrirait comme fournisseur de notations ESG (règlement UE 2024/3005) :")
        for t in trouvees[:40]:
            print("  - " + t)
        print("Écrire « données ESG au niveau du site », « lecture ESG » ou « note "
              "environnementale du site ».")
        return 1
    print("check_vocabulaire_esg : OK — aucun terme de notation ESG dans le servi")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
