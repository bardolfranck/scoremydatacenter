# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Détecteur de CENTROÏDE DE GÉOCODEUR dans les fiches de registre.

Un registre qui rend la même coordonnée pour deux dossiers peut vouloir dire deux choses, et
seul le PÉTITIONNAIRE les sépare :

  · même point, exploitants DIFFÉRENTS → c'est un géocodeur : le registre a géocodé la
    commune/zone au lieu de localiser le site (signature « Fouju », vue de l'intérieur du
    registre sans oracle externe) ;
  · même point, MÊME exploitant → c'est la vérité : le même data center, examiné par deux
    procédures. La géométrie partagée est juste, il ne faut PAS la jeter.

C'est pourquoi l'égalité des coordonnées NE SUFFIT PAS comme critère — elle était trop large,
comme « ordre du jour » l'était pour les procès-verbaux (leçon du chef, 2026-10-01). Mesuré ce
jour-là sur 40 fiches :

  · 43.287981, 5.402336 → DIGITAL MRS5 (sans pétitionnaire) et SEGRO (zone Actisud) : porteurs
    différents, ~5 km d'écart réel → géocodeur (le centre de « Marseille ») ;
  · 48.646436, 2.214727 → DATA 4 SAS et DATA 4 SERVICES à Marcoussis : MÊME exploitant, deux
    procédures sur LE MÊME site → pas un géocodeur, géométrie vraie.

Quand l'un des deux dossiers n'a pas de pétitionnaire (c'est le cas de MRS5), on ne peut pas
trancher : on marque `indetermine` plutôt que de supposer dans un sens ou dans l'autre.

Le comparateur d'exploitants N'EST PAS réécrit ici : on réutilise `match._meme_exploitant`
(il reconnaît « DATA 4 SAS » ≈ « DATA 4 SERVICES » ≈ « Data4 »), injecté par l'appelant pour
éviter une dépendance circulaire (match importe geocoder).

Deux consommateurs : la comptabilité (`run.py --audit-centroides` → section
`centroides_partages` de couverture.json) et le rattachement (`match.py` n'utilise pas une
géométrie `geocodeur`/`indetermine` comme signal — seule `meme_site` reste une vraie géométrie).
"""

from __future__ import annotations

from typing import Callable

# Catégories d'un centroïde partagé par ≥ 2 dossiers distincts.
GEOCODEUR = "geocodeur"       # porteurs différents → coordonnée de commune/zone, pas un site
MEME_SITE = "meme_site"       # même exploitant → même data center, géométrie vraie (à garder)
INDETERMINE = "indetermine"   # au moins un dossier sans pétitionnaire → on ne tranche pas

# Les catégories où la géométrie partagée n'est PAS digne de confiance comme signal.
_SUSPECTES = frozenset({GEOCODEUR, INDETERMINE})


def centroid_key(centroid: dict | None) -> tuple[float, float] | None:
    """Clé comparable d'un `procedure.centroid` ({lat, lon}), ou None s'il n'y en a pas."""
    if not isinstance(centroid, dict):
        return None
    lat, lon = centroid.get("lat"), centroid.get("lon")
    if lat is None or lon is None:
        return None
    return (round(float(lat), 6), round(float(lon), 6))


def petitionnaire(doc: dict) -> str | None:
    p = ((doc or {}).get("procedure") or {}).get("petitionnaire")
    return p if (p and str(p).strip()) else None


def group_by_centroid(docs: dict[str, dict]) -> dict[tuple[float, float], list[str]]:
    """{(lat, lon): [noms de dossiers]} pour tout centroïde porté par ≥ 2 dossiers."""
    groups: dict[tuple[float, float], list[str]] = {}
    for nom, doc in docs.items():
        key = centroid_key(((doc or {}).get("procedure") or {}).get("centroid"))
        if key is not None:
            groups.setdefault(key, []).append(nom)
    return {key: sorted(noms) for key, noms in groups.items() if len(noms) >= 2}


def _categorie(noms: list[str], docs: dict[str, dict],
               same_operator: Callable[[str | None, str | None], bool]) -> str:
    """Trancher un groupe partageant un point : geocodeur / meme_site / indetermine."""
    pets = [petitionnaire(docs[n]) for n in noms]
    if any(p is None for p in pets):
        return INDETERMINE          # un dossier sans porteur → on ne peut pas comparer
    # Tous présents : même exploitant si chacun s'accorde avec le premier (inclusion de marque).
    return MEME_SITE if all(same_operator(pets[0], p) for p in pets[1:]) else GEOCODEUR


def classify(docs: dict[str, dict],
             same_operator: Callable[[str | None, str | None], bool]) -> dict[tuple[float, float], dict]:
    """{clé: {"dossiers": [...], "categorie": ...}} pour chaque centroïde partagé (≥2 dossiers)."""
    out: dict[tuple[float, float], dict] = {}
    for key, noms in group_by_centroid(docs).items():
        out[key] = {"dossiers": noms, "categorie": _categorie(noms, docs, same_operator)}
    return out


def suspect_keys(docs: dict[str, dict],
                 same_operator: Callable[[str | None, str | None], bool]) -> set[tuple[float, float]]:
    """Clés dont la géométrie est à ÉCARTER au rattachement (geocodeur ou indetermine)."""
    return {k for k, v in classify(docs, same_operator).items() if v["categorie"] in _SUSPECTES}
