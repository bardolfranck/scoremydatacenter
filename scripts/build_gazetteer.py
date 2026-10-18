#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Dictionnaire de lieux embarqué — chercher une COMMUNE, pas seulement nos fiches.

POURQUOI (Franck, 2026-10-18). Chercher « Ferney-Voltaire » rendait « Telehouse Paris
Voltaire », à 460 km, et manquait les cinq data centers situés à 5, 7, 7, 8 et 21 km. Ces
cinq-là sont en SUISSE : aucune recherche textuelle ne les trouvera jamais, parce qu'elle
cherche dans le texte de nos fiches et qu'une frontière n'est pas un mot. Seule la
géographie répond à une question géographique.

POURQUOI PAS UNE API DE GÉOCODAGE. Appeler un service à chaud, c'est envoyer à un tiers le
nom de la commune que tape le lecteur — et nos lecteurs sont souvent des gens inquiets d'un
projet près de chez eux. On embarque donc le dictionnaire : la recherche se fait dans le
navigateur, rien ne sort. C'est aussi une dépendance de moins.

CE QU'ON RETIENT, ET POURQUOI CE N'EST PAS UN SEUIL DE POPULATION SEC :
  · toute COMMUNE (unité administrative ADM4/ADM5), quelle que soit sa taille — l'habitant
    d'un village de 400 personnes est exactement notre lecteur, et la France porte ses
    35 000 communes à ce niveau ;
  · tout lieu habité d'au moins 100 habitants.
Le reste — hameaux à zéro habitant, lieux-dits — quadruplerait le poids pour des noms que
personne ne tape. Mesuré : 731 000 lieux sans filtre (8,7 Mo), 165 000 avec (2,2 Mo).

DÉCOUPE. Personne ne charge le dictionnaire entier : il part en tranches nommées par les
deux premières lettres, et le navigateur ne télécharge que la sienne. Pire tranche mesurée
137 ko, neuf tranches sur dix sous 15 ko.

SOURCE : GeoNames (CC BY 4.0) — l'attribution est obligatoire, elle est portée par la page
qui s'en sert. Les dumps sont déjà en cache côté pipelines ; ce script ne télécharge RIEN.
"""

import json
import os
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SORTIE = REPO / "site" / "public" / "data" / "lieux"
CACHE = Path(os.environ.get(
    "SMDC_GEONAMES", REPO.parent / "smdc-newsroom" / ".media-sat" / "geonames"))

POP_MINIMALE = 100
LONGUEUR_PREFIXE = 2
# ADM4/ADM5 = commune (ou équivalent). C'est à ce niveau que GeoNames porte les communes
# françaises, et elles entrent SANS condition de population.
CODES_COMMUNE = {"ADM4", "ADM5"}


def normalise(nom: str) -> str:
    """Forme de comparaison : sans accents, sans casse, sans ponctuation.

    « Ferney-Voltaire », « ferney voltaire » et « FERNEY–VOLTAIRE » doivent se rejoindre,
    sinon le lecteur qui tape vite ne trouve rien. Le client applique EXACTEMENT la même
    fonction (voir Ranking.astro) — une normalisation à deux endroits qui divergent rendrait
    des tranches introuvables, et le silence est le mode d'échec de ce genre de panne.
    """
    base = unicodedata.normalize("NFD", nom.lower())
    base = "".join(c for c in base if unicodedata.category(c) != "Mn")
    return " ".join("".join(c if c.isalnum() else " " for c in base).split())


def regions(cache: Path) -> tuple[dict[str, str], dict[str, dict]]:
    """Table des régions : code admin1 → nom, dans les DEUX langues du site.

    POURQUOI UNE RÉGION (Franck, 2026-10-18) : la suggestion « Berlin (US) » ne permet pas
    de choisir, il y a plusieurs Berlin aux États-Unis. Le pays ne situe rien À L'INTÉRIEUR
    d'un pays — c'est l'État ou la région qui le fait, et c'est le repère que le lecteur a.

    On prend admin1 (État américain, région française) et non admin2 (comté, département) :
    une seule règle pour tous les pays, et c'est le niveau qui tranche le cas rencontré.

    POURQUOI LES DEUX LANGUES : la table de référence de GeoNames est anglicisée. La page
    française affichait « Vernon (Normandy · FR) » juste au-dessus de « Nation Data Center
    – Normandie » — le même territoire, deux orthographes, dans la même liste. On relit donc
    le nom local dans les noms alternatifs, par langue.

    ET POURQUOI UNE TABLE À PART plutôt qu'un nom dans chaque fiche : il y a 165 000 lieux
    pour quelques centaines de régions. Porter le nom dans chaque enregistrement le
    répéterait, en double (fr + en). La fiche garde le CODE, court et très répétitif, et la
    table se charge une fois.
    """
    table = cache / "admin1CodesASCII.txt"
    if not table.is_file():
        # Le dictionnaire reste utilisable sans : les suggestions perdent la région, pas la
        # commune. On le DIT plutôt que de rendre un champ vide sans explication.
        print(f"gazetteer: {table.name} absent — suggestions sans région", file=sys.stderr)
        return {}, {}

    # code admin1 → (nom de référence, identifiant GeoNames de la région)
    reference: dict[str, tuple[str, str]] = {}
    for ligne in table.read_text(encoding="utf-8", errors="replace").splitlines():
        champs = ligne.split("\t")
        if len(champs) >= 4 and champs[0]:
            reference[champs[0]] = (champs[1], champs[3])

    # Noms alternatifs : on ne lit QUE les identifiants des régions, pas les 12 millions de
    # lignes du fichier. `isPreferredName` l'emporte quand la langue en propose plusieurs.
    voulus = {gid: code for code, (_, gid) in reference.items()}
    locaux: dict[str, dict[str, tuple[str, bool]]] = defaultdict(dict)
    dossier_alt = cache / "alt"
    for fichier in sorted(dossier_alt.glob("*.txt")) if dossier_alt.is_dir() else []:
        with fichier.open(encoding="utf-8", errors="replace") as fh:
            for ligne in fh:
                champs = ligne.rstrip("\n").split("\t")
                if len(champs) < 4:
                    continue
                code = voulus.get(champs[1])
                if code is None or champs[2] not in ("fr", "en"):
                    continue
                prefere = len(champs) > 4 and champs[4] == "1"
                courant = locaux[code].get(champs[2])
                if courant is None or (prefere and not courant[1]):
                    locaux[code][champs[2]] = (champs[3], prefere)

    noms: dict[str, dict] = {}
    for code, (defaut, _) in reference.items():
        fr = locaux.get(code, {}).get("fr", (defaut, False))[0]
        en = locaux.get(code, {}).get("en", (defaut, False))[0]
        noms[code] = {"fr": fr, "en": en} if fr != en else {"fr": fr, "en": fr}
    return {code: v["en"] for code, v in noms.items()}, noms


def lieux_du_fichier(chemin: Path, noms_regions: dict[str, str]):
    """Rend (nom affichable, pays, lat, lon, population, région) des lignes retenues."""
    with chemin.open(encoding="utf-8", errors="replace") as fh:
        for ligne in fh:
            champs = ligne.rstrip("\n").split("\t")
            if len(champs) < 15:
                continue
            classe, code = champs[6], champs[7]
            commune = classe == "A" and code in CODES_COMMUNE
            if classe != "P" and not commune:
                continue
            try:
                lat, lon = float(champs[4]), float(champs[5])
                pop = int(champs[14] or 0)
            except ValueError:
                continue
            if not commune and pop < POP_MINIMALE:
                continue
            pays = champs[8]
            # On porte le CODE, pas le nom : court, très répétitif (donc quasi gratuit
            # une fois compressé), et traduisible à l'affichage.
            code = f"{pays}.{champs[10]}" if champs[10] else ""
            yield champs[1], pays, lat, lon, pop, (code if code in noms_regions else "")


def main() -> int:
    if not CACHE.is_dir():
        print(f"gazetteer: cache GeoNames absent ({CACHE}) — dictionnaire NON reconstruit",
              file=sys.stderr)
        # Non fatal : le site se construit sans, la recherche par lieu se tait proprement
        # (le client traite une tranche absente comme « aucun lieu de ce nom »). Mais on le
        # DIT, parce qu'une fonctionnalité qui disparaît en silence est pire qu'absente.
        return 0

    fichiers = sorted(CACHE.glob("*.txt"))
    if not fichiers:
        print(f"gazetteer: aucun dump dans {CACHE} — dictionnaire NON reconstruit",
              file=sys.stderr)
        return 0

    # GeoNames porte souvent la commune (ADM4) ET son chef-lieu (P) sous le même nom, au même
    # endroit. Deux entrées pour un lieu, c'est du poids pour rien et une liste qui bégaie.
    noms_regions, regions_par_langue = regions(CACHE)
    vus: set = set()
    tranches: dict[str, list] = defaultdict(list)
    retenus = 0
    for fichier in fichiers:
        if fichier.name == "admin1CodesASCII.txt":
            continue                      # table de correspondance, pas un dump de pays
        for nom, pays, lat, lon, pop, code_region in lieux_du_fichier(fichier, noms_regions):
            cle_nom = normalise(nom)
            if not cle_nom:
                continue
            cle = (cle_nom, pays, round(lat, 2), round(lon, 2))
            if cle in vus:
                continue
            vus.add(cle)
            retenus += 1
            # Une région qui répète la commune n'aide personne à choisir : les villes-États
            # rendent « Berlin (State of Berlin) », « Wien (Vienna) », « Hamburg (Hamburg) ».
            # On la tait — la région n'est là QUE pour départager des homonymes ; quand
            # elle redit le nom, elle ne départage rien. Vérifié dans les DEUX langues :
            # il suffit qu'une seule répète pour que la mention soit du bruit.
            libelles = regions_par_langue.get(code_region, {})
            if code_region and any(cle_nom in normalise(v) for v in libelles.values()):
                code_region = ""
            tranches[cle_nom[:LONGUEUR_PREFIXE]].append([nom, pays, round(lat, 4),
                                                         round(lon, 4), pop, code_region])

    if SORTIE.is_dir():
        for vieux in SORTIE.glob("*.json"):
            vieux.unlink()
    SORTIE.mkdir(parents=True, exist_ok=True)

    # La table des régions, à part : quelques centaines d'entrées pour 165 000 lieux, et
    # elle porte les deux langues. Le client la charge une fois et traduit le code.
    # Restreinte aux régions RÉELLEMENT citées par le dictionnaire : la table de GeoNames
    # couvre le monde entier (3 865 entrées, 47 ko compressés) alors que nos dix-neuf pays
    # en utilisent une fraction. Le lecteur la télécharge à sa première recherche ; lui
    # envoyer les régions du Paraguay serait payer pour rien.
    citees = {item[5] for items in tranches.values() for item in items if item[5]}
    (SORTIE / "regions.json").write_text(
        json.dumps({c: v for c, v in sorted(regions_par_langue.items()) if c in citees},
                   separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

    octets = 0
    for prefixe, items in tranches.items():
        # Le plus peuplé d'abord : « Ferney » existe aussi deux fois aux États-Unis, dont une
        # à zéro habitant. À nom égal, on propose la vraie ville, et le pays lève le doute.
        items.sort(key=lambda x: -x[4])
        # Un nom de fichier ne peut pas porter n'importe quoi : les préfixes sont normalisés
        # (alphanumériques et espaces), on code l'espace pour rester sur un nom plat.
        cible = SORTIE / f"{prefixe.replace(' ', '_')}.json"
        texte = json.dumps(items, separators=(",", ":"), ensure_ascii=False)
        cible.write_text(texte, encoding="utf-8")
        octets += len(texte.encode())

    print(f"gazetteer: {retenus:,} lieux · {len(tranches)} tranches · "
          f"{octets/1e6:.1f} Mo non compressés → {SORTIE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
