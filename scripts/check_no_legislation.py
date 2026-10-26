# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Barrière avant mise en ligne : un TEXTE DE LOI n'est pas un data center.

🔴 CE QUI S'EST PASSÉ (2026-10-26). Le corpus servi contenait 16 « fiches » dont le nom
était un projet de loi américain — HB 1333, SB 212 - Right to Compute Act, POWER Act
(HB 3546)… — avec pour commune la CAPITALE DE L'ÉTAT, c'est-à-dire le siège de la
législature. Chacune avait sa fiche technique, son portrait dans les deux langues, son
épingle sur la carte, sa ligne au classement et son entrée au sitemap. Le titre public
annonçait « HB 1333 — data center in Indianapolis », et la plage de couverture leur
attribuait une note probable.

Dix-sept entrées « en veille » portaient la même faute sur la carte, avec un libellé
affirmant « projet de data center contesté localement ».

Ce n'est pas une erreur de mesure, c'est une erreur sur la NATURE de l'objet : un
observatoire qui note une loi comme il note un bâtiment ne se trompe pas de chiffre, il
se trompe de monde. Le lecteur qui tombe dessus n'en conclut pas que la donnée est
perfectible ; il en conclut que nous ne savons pas de quoi nous parlons.

⚠️ Aucun test de cohérence ne l'attrapait : chaque fiche était INDIVIDUELLEMENT valide
(un nom, une commune, des coordonnées, des indicateurs). La faute n'est visible que si
l'on regarde ce que le nom DÉSIGNE. D'où ce garde-fou, qui lit ce qui part.
"""
import json
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
PUBLIC = RACINE / "site" / "public" / "data"

# Trois formes, et la deuxième est SENSIBLE À LA CASSE — apprise d'un faux positif au
# premier passage : « ACT Buffalo », « ACT Gillette », « ACT Colstrip » sont de vrais sites
# d'Advanced Communications Technology dans le Wyoming et le Montana. Un sigle d'exploitant
# en capitales n'est pas le mot « Act » d'un intitulé de loi, qui s'écrit en casse de titre.
# Confondre les deux aurait fait retirer six sites réels pour cause de nom mal lu — soit
# exactement la faute qu'on corrige, dans l'autre sens.
LOI_SIGLE = re.compile(r"^(HB|SB|AB|HF|SF|LB|HR|SR|LD|LC)[\s.\-]?\d", re.I)
LOI_MOT = re.compile(r"\b(Act|Bill)\b")
LOI_DESC = re.compile(r"\b(moratorium|transparency)\s+(bill|amendment)\b", re.I)


def _est_un_texte(nom: str) -> bool:
    return bool(LOI_SIGLE.search(nom) or LOI_MOT.search(nom) or LOI_DESC.search(nom))


def _noms():
    """(origine, id, nom) pour tout ce qui sera servi comme objet nommé."""
    for p in sorted((PUBLIC / "dc").glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        yield "fiche", d.get("id", p.stem), d.get("name") or ""
    for nom in ("map.geojson", "watchlist.geojson"):
        f = PUBLIC / nom
        if not f.exists():
            continue
        for e in json.loads(f.read_text(encoding="utf-8")).get("features", []):
            pr = e.get("properties", {})
            yield nom.split(".")[0], pr.get("id", "?"), pr.get("name") or ""


def main() -> int:
    fautes = [(o, i, n) for o, i, n in _noms() if _est_un_texte(n)]
    if fautes:
        print("✘ deploy REFUSÉ — un texte de loi est servi comme data center :")
        for origine, ident, nom in fautes[:40]:
            print(f"    · [{origine}] {ident} — « {nom} »")
        if len(fautes) > 40:
            print(f"    … et {len(fautes) - 40} autres")
        print("\n  Une loi se cite dans la procédure, elle ne se note pas et ne prend pas")
        print("  d'épingle. Retirer l'entrée à la source (calibration/), puis rebâtir.")
        return 1
    print("deploy: aucun texte de loi dans le corpus servi ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
