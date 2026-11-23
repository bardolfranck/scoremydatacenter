# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Une fiche fusionnée redirige (301) vers la fiche conservée — dérivé de `retraits.json`.

Pourquoi un script : les 301 s'écrivaient À LA MAIN dans site/public/_redirects, une liste à
deux endroits. Mesuré le 2026-11-23 : 24 fusions sur 42 n'avaient AUCUN 301 (les 17 fusions
US du 11-20, Sigma Carquefou, les 5 fusions FR du jour) et aucune fiche n'était redirigée en
néerlandais. Le lien indexé ou partagé tombait sur un 404. La source de la fusion est
`calibration/retraits.json` (newsroom) ; ce script en dérive les redirections, après le build
Astro, EN TÊTE de dist/_redirects.

Règles :
  - une fusion = 6 lignes STATIQUES : 3 langues (/, /fr/, /nl/) × (page, portrait) ;
    statiques, parce que Cloudflare plafonne les redirections dynamiques (:splat) à 100 ;
  - une source déjà présente dans _redirects (écrite à la main, avec son histoire) est gardée ;
  - la cible suit la chaîne (A → B → C si B a lui-même été fusionné) ;
  - une cible absente de dist/ est une ERREUR (page de base) : un 301 vers un 404 serait pire
    qu'un 404 ; une édition de langue absente (NL par pays) ou un portrait absent est sautée.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "site" / "dist"
CAL = Path(os.environ.get("NEWSROOM_CAL", ROOT.parent / "smdc-newsroom" / "calibration"))
LANGUES = ("", "fr/", "nl/")
SOUS_PAGES = ("", "portrait/")
ENTETE = "# --- GÉNÉRÉ par scripts/build_redirects_fusions.py depuis calibration/retraits.json — ne pas éditer ---"
FIN = "# --- fin du bloc généré ---"


def cible_finale(fid: str, fusions: dict[str, str]) -> str:
    vus = set()
    while fid in fusions:
        if fid in vus:
            raise SystemExit(f"redirections: boucle de fusions autour de {fid}")
        vus.add(fid)
        fid = fusions[fid]
    return fid


def lignes(retraits: list[dict], existant: str, dist: Path) -> tuple[list[str], list[str]]:
    fusions = {r["id"]: r["survivante"] for r in retraits if r.get("type") == "fusion" and r.get("survivante")}
    deja = set(re.findall(r"^(\S+)", existant, re.M))
    out, fautes = [], []
    for fid in sorted(fusions):
        cible = cible_finale(fid, fusions)
        for lg in LANGUES:
            for sp in SOUS_PAGES:
                dst = f"/{lg}dc/{cible}/{sp}"
                src = f"/{lg}dc/{fid}/{sp}"
                if src in deja or f"{src}*" in deja:
                    continue
                if not (dist / dst.strip("/") / "index.html").is_file():
                    # La page de base (anglais) existe pour toute fiche servie : son absence est
                    # une erreur. Une édition de langue (le néerlandais n'est servi que pour
                    # certains pays) ou un portrait absents : rien à rediriger.
                    if not lg and not sp:
                        fautes.append(f"{fid} → {dst} : cible absente de dist/")
                    continue
                out.append(f"{src} {dst} 301")
    return out, fautes


def main() -> int:
    red = DIST / "_redirects"
    if not red.is_file():
        print("redirections: dist/_redirects absent — lancer le build Astro d'abord", file=sys.stderr)
        return 1
    rt = CAL / "retraits.json"
    if not rt.is_file():
        print(f"redirections: {rt} absent — aucune fusion à rediriger")
        return 0
    texte = red.read_text("utf-8")
    if FIN in texte:  # bloc d'un passage précédent : on le régénère
        texte = texte.split(FIN, 1)[1].lstrip("\n")
    out, fautes = lignes(json.loads(rt.read_text("utf-8")), texte, DIST)
    if fautes:
        print("redirections: ERREUR —\n  " + "\n  ".join(fautes), file=sys.stderr)
        return 1
    # EN TÊTE du fichier, jamais à la fin : Cloudflare compte comme DYNAMIQUE toute règle placée
    # après la première règle à motif (:splat, *), et les dynamiques sont plafonnées à 100.
    # Mis en queue, ces 132 lignes statiques ont fait refuser le deploy du 2026-11-23
    # (« Maximum number of dynamic _redirects rules limit of 100 exceeded », ligne 170).
    red.write_text(ENTETE + "\n" + "\n".join(out) + "\n" + FIN + "\n\n" + texte, "utf-8")
    print(f"redirections: {len(out)} lignes 301 générées depuis retraits.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
