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
import base64
import html as html_mod
import json
import pathlib
import re
import sys
import zlib

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


# 🔴 LE CLASSEMENT NE PUBLIE PLUS LE CORPUS EN UNE PAGE (Franck 2026-11-09). La page
# Classement rendait les 3 339 lignes — nom, commune, lettre, notes par pilier, confiance,
# position — dans un seul HTML de 10 Mo : un téléchargement, tout le corpus, mieux rangé
# que l'ancien fichier de la carte. Les lignes restent RENDUES PAR ASTRO, au même endroit,
# avec le même code : on ne réécrit pas le gabarit d'une ligne ailleurs (une ligne écrite à
# deux endroits finit par diverger). Ce script les DÉCOUPE après le build : la page n'en
# garde que les premières, dans l'ordre par défaut, et les autres partent dans la fonction
# /api/classement, qui les sert par paquets de RANG_PAR_PAGE (tri, filtre, recherche).
# 25 (Franck 2026-11-09 : « 50 c'est beaucoup, 25 est largement suffisant »).
RANG_PAR_PAGE = 25
API_CLASSEMENT = "/api/classement"
_TBODY = re.compile(r'(<table class="rank-table" id="rank-table">.*?<tbody)([^>]*)>(.*?)(</tbody>)', re.S)
_LIGNE = re.compile(r"<tr\b.*?</tr>", re.S)
_ATTR = re.compile(r'data-([a-z_-]+)="([^"]*)"')


def meta_ligne(tr: str) -> list:
    """Ce dont le serveur a besoin pour trier, filtrer, chercher et mesurer une distance —
    lu sur la ligne rendue, jamais recalculé : c'est le même attribut que lisait le
    navigateur."""
    ouverture = tr[: tr.index(">") + 1]
    a = {k: html_mod.unescape(v) for k, v in _ATTR.findall(ouverture)}
    k = {cle[2:]: float(v) for cle, v in a.items() if cle.startswith("k-") and v not in ("", "undefined")}
    num = lambda v: float(v) if v not in (None, "", "undefined") else None  # noqa: E731
    return [a.get("status", ""), a.get("country", ""), a.get("search", ""),
            num(a.get("lat")), num(a.get("lon")), k]


def ordre_par_defaut(metas: list) -> list:
    """Le tri que la page appliquait au chargement : note site, mieux noté d'abord, les
    lignes sans note (-1) en fin. Tri STABLE sur l'ordre du build, comme Array.sort."""
    idx = list(range(len(metas)))
    return sorted(idx, key=lambda i: (metas[i][5].get("site", -1) < 0, -metas[i][5].get("site", -1)))


def classement_cote_serveur() -> str:
    faits, donnees = [], {}
    for page in sorted(DIST.rglob("index.html")):
        texte = page.read_text()
        m = _TBODY.search(texte)
        if not m:
            continue
        if "data-api=" in m.group(2):
            faits.append(f"{page.parent.relative_to(DIST)} déjà découpé")
            continue
        lignes = _LIGNE.findall(m.group(3))
        metas = [meta_ligne(tr) for tr in lignes]
        chemin = "/" + str(page.parent.relative_to(DIST)).strip(".") + "/"
        chemin = chemin.replace("//", "/")
        # Le HTML des lignes, bout à bout, avec ses décalages : la fonction en découpe une
        # par `slice`. COMPRESSÉ : 10 Mo par langue en clair faisaient charger la fonction
        # en ~0,7 s, trop près de la limite de démarrage de Cloudflare (1 s) — et toutes les
        # fonctions du site partagent ce paquet. Compressé, c'est 0,5 Mo par langue, et la
        # fonction ne le décompresse qu'à la première demande (~10 ms, une fois par
        # instance). Les décalages sont comptés en unités UTF-16, comme `slice` en JS.
        off, pos = [], 0
        for tr in lignes:
            off.append(pos)
            pos += len(tr.encode("utf-16-le")) // 2
        off.append(pos)
        brut = "".join(lignes).encode("utf-8")
        comp = zlib.compressobj(9, zlib.DEFLATED, -15)
        z = base64.b64encode(comp.compress(brut) + comp.flush()).decode("ascii")
        donnees[chemin] = {"meta": metas, "z": z, "off": off, "par": RANG_PAR_PAGE}
        tete = [lignes[i] for i in ordre_par_defaut(metas)[:RANG_PAR_PAGE]]
        attributs = (f'{m.group(2)} data-api="{API_CLASSEMENT}" data-total="{len(lignes)}" '
                     f'data-par="{RANG_PAR_PAGE}"')
        page.write_text(texte[: m.start()] + m.group(1) + attributs + ">" + "".join(tete)
                        + m.group(4) + texte[m.end():])
        faits.append(f"{chemin} {len(lignes)} → {len(tete)} lignes")
    if donnees or not (FONCTIONS_DATA / "classement.json").exists():
        FONCTIONS_DATA.mkdir(parents=True, exist_ok=True)
        (FONCTIONS_DATA / "classement.json").write_text(
            json.dumps(donnees, ensure_ascii=False, separators=(",", ":")))
    return " · ".join(faits) or "aucune page de classement"


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
    classement = classement_cote_serveur()
    geo = " ".join(sorted(p.name for p in DATA.glob("*.geojson")))
    tranches = len([p for p in (DATA / "lieux").glob("*.json") if p.name != "regions.json"]) \
        if (DATA / "lieux").is_dir() else 0
    print(f"prune: {retires} fichiers retirés + {len(regles)} règle(s) de réécriture, "
          f"{sur_place} bouchés sur place ; geojson gardés → {geo} ({carte}) · "
          f"dictionnaire de lieux servi ({tranches} tranches + table des régions) · "
          f"classement : {classement}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
