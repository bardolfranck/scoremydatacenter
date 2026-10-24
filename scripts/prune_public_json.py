# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Anti-pillage : les points d'accès /data/ ne servent plus que des bouchons.

🔴 POURQUOI UN SCRIPT PLUTÔT QU'UN `find -exec` D'UNE LIGNE. L'ancienne version ÉCRIVAIT le
bouchon dans chacun des 3 283 fichiers de dc/ — 3 283 fichiers identiques de 98 octets. Le
jour où les portraits ont doublé le nombre de pages, le déploiement a buté sur la limite de
Cloudflare Pages : 20 000 fichiers. On en avait 20 694, dont 3 298 qui disaient tous la même
phrase.

Un répertoire entièrement bouché n'a pas besoin d'un fichier par entrée : une règle de
réécriture le couvre en entier, et le serveur rend exactement la même réponse — 200, même
corps. Ce qui change est le nombre de fichiers déployés, pas ce que reçoit l'appelant.

⚠️ L'INVARIANT EST LE 200, PAS LE FICHIER. Ces chemins ont été servis, indexés, et sont
peut-être appelés : ils doivent répondre, pas disparaître en 404. Un `rm` sans la règle de
réécriture transformerait un bouchon en trou.
"""
import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
DIST = RACINE / "site" / "dist"
DATA = DIST / "data"

BOUCHON = ('{"gone":true,"note":"Bulk data endpoints are retired - structured access '
           'is available via the API."}')

# Répertoires bouchés EN ENTIER : une règle les couvre, les fichiers partent.
# `lieux/` n'y est pas — le dictionnaire de lieux est servi pour de bon.
REPERTOIRES = ["dc", "comparator", "actu"]


def main() -> int:
    if not DATA.is_dir():
        print("prune: pas de site/dist/data — rien à faire")
        return 0

    gone = DATA / "gone.json"
    gone.write_text(BOUCHON)

    retires = 0
    regles = []
    for nom in REPERTOIRES:
        d = DATA / nom
        if not d.is_dir():
            continue
        for f in d.glob("*.json"):
            f.unlink()
            retires += 1
        regles.append(f"/data/{nom}/* /data/gone.json 200")

    # Les JSON restants à la racine de data/ sont peu nombreux : les boucher sur place
    # coûte une dizaine de fichiers et évite une règle qui masquerait map.geojson.
    sur_place = 0
    for f in DATA.glob("*.json"):
        if f.name == "gone.json":
            continue
        f.write_text(BOUCHON)
        sur_place += 1

    red = DIST / "_redirects"
    entete = ("\n# BOUCHONS /data/ — écrits par scripts/prune_public_json.py à chaque build.\n"
              "# Une règle par répertoire entièrement retiré, au lieu d'un fichier par entrée :\n"
              "# même réponse (200, même corps), des milliers de fichiers en moins dans le\n"
              "# déploiement. Cloudflare Pages en plafonne 20 000, et les portraits nous y ont\n"
              "# amenés. Ne pas supprimer ces règles sans remettre les fichiers : le bouchon\n"
              "# deviendrait un 404 sur des URL déjà servies et indexées.\n")
    red.write_text((red.read_text() if red.exists() else "") + entete + "\n".join(regles) + "\n")

    geo = " ".join(sorted(p.name for p in DATA.glob("*.geojson")))
    tranches = len([p for p in (DATA / "lieux").glob("*.json") if p.name != "regions.json"]) \
        if (DATA / "lieux").is_dir() else 0
    print(f"prune: {retires} fichiers retirés + {len(regles)} règle(s) de réécriture, "
          f"{sur_place} bouchés sur place ; geojson gardés → {geo} · "
          f"dictionnaire de lieux servi ({tranches} tranches + table des régions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
