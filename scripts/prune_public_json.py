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
import json
import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
DIST = RACINE / "site" / "dist"
DATA = DIST / "data"
# Copie complète des geojson pour les fonctions /api/carte/* et /api/veille/* : elle part
# dans le paquet de la fonction, jamais comme fichier servi. Ignorée par git.
FONCTIONS_DATA = RACINE / "site" / "functions" / "_data"

# 🔴 CE QUE LE NAVIGATEUR REÇOIT EN UN SEUL FICHIER (Franck 2026-11-09). La carte publiait
# les 3 339 fiches avec nom, opérateur, commune et lettre dans /data/map.geojson : un
# `curl` emportait tout le plancher gratuit. Le fichier servi ne garde plus que ce qu'il
# faut pour PEINDRE la carte — position à ~1 km, couleur, taille, pays (cadrage Europe) —
# et `t`, le rang qui permet de demander UN site au serveur quand on clique dessus.
# Tout ce qui nomme un site passe par functions/api/carte/*, un site par requête.
# Liste FERMÉE : un champ ajouté à l'artefact ne fuit pas tant qu'on ne l'ajoute pas ici.
CHAMPS_POINT_SITE = ("grade_site", "size_tier", "band_central", "country")
CHAMPS_POINT_VEILLE = ("kind", "country")


def anonymiser(geo: dict, champs: tuple) -> dict:
    """Le geojson servi : géométrie + `t` (rang) + la liste fermée de champs de peinture."""
    sortie = []
    for t, f in enumerate(geo["features"]):
        p = f.get("properties") or {}
        garde = {k: p[k] for k in champs if k in p and p[k] is not None}
        sortie.append({"type": "Feature", "geometry": f["geometry"], "properties": {"t": t, **garde}})
    return {"type": "FeatureCollection", "features": sortie}


def carte_cote_serveur() -> str:
    """Copie complète → fonctions ; version anonyme → dist. Dans CET ordre : la copie
    lit le fichier complet que l'anonymisation va écraser."""
    FONCTIONS_DATA.mkdir(parents=True, exist_ok=True)
    faits = []
    for fichier, cible, champs in (("map.geojson", "carte.json", CHAMPS_POINT_SITE),
                                   ("watchlist.geojson", "veille.json", CHAMPS_POINT_VEILLE)):
        src = DATA / fichier
        if not src.exists():
            # La fonction importe ce fichier : l'absence casserait le paquet au déploiement.
            # On écrit une collection vide, et la carte affiche ce qu'il y a — rien.
            (FONCTIONS_DATA / cible).write_text('{"type":"FeatureCollection","features":[]}')
            continue
        geo = json.loads(src.read_text())
        if geo["features"] and "name" not in (geo["features"][0].get("properties") or {}):
            # Déjà anonymisé (prune relancé deux fois sur le même dist) : la copie
            # serveur du premier passage est la bonne, ne pas l'écraser par l'anonyme.
            faits.append(f"{fichier} déjà anonyme")
            continue
        (FONCTIONS_DATA / cible).write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":")))
        src.write_text(json.dumps(anonymiser(geo, champs), ensure_ascii=False, separators=(",", ":")))
        faits.append(f"{fichier} anonymisé ({len(geo['features'])} points)")
    return " · ".join(faits)

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

    carte = carte_cote_serveur()
    geo = " ".join(sorted(p.name for p in DATA.glob("*.geojson")))
    tranches = len([p for p in (DATA / "lieux").glob("*.json") if p.name != "regions.json"]) \
        if (DATA / "lieux").is_dir() else 0
    print(f"prune: {retires} fichiers retirés + {len(regles)} règle(s) de réécriture, "
          f"{sur_place} bouchés sur place ; geojson gardés → {geo} ({carte}) · "
          f"dictionnaire de lieux servi ({tranches} tranches + table des régions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
