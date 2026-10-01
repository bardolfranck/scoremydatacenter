# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Détecteur de CENTROÏDE DE GÉOCODEUR dans les fiches de registre.

Un registre qui rend EXACTEMENT la même coordonnée pour deux dossiers DISTINCTS n'a pas
localisé de site : il a géocodé la commune (ou la zone). C'est la signature « Fouju » — une
coordonnée fabriquée — mais vue À L'INTÉRIEUR du registre, en amont du géocodage externe que
mesure `pipelines.geo_audit` : on n'a pas besoin d'interroger un oracle pour voir que deux
projets différents portent le même point, il suffit de les comparer entre eux.

Mesuré le 2026-10-01 : les deux avis PACA de Marseille — DIGITAL MRS5 (ancien silo à sucre
Saint-Louis, dans l'enceinte du GPMM) et le projet mixte SEGRO (zone Actisud, Saint-André),
deux sites réels distants d'environ 5 km — portaient le même `procedure.centroid`
43.287981, 5.402336. Aucun des deux n'est là : c'est le centre géocodé de « Marseille ».

Pourquoi un module, et pas une vérification à l'œil : la leçon doit être DÉTECTÉE à chaque
lot, pas redécouverte à chaque fois (arbitrage Franck : « les gates sont dans le workflow,
pas dans la tête de l'opérateur »). Deux consommateurs :

  · la COMPTABILITÉ (`run.py --audit-centroides` écrit la section `centroides_geocodeur`
    dans couverture.json) — on COMPTE le défaut, on ne le raconte pas ;
  · le RATTACHEMENT (`match.py` n'utilise PAS une géométrie partagée comme signal — sinon il
    propose la même fiche du corpus pour deux projets distincts, un faux rattachement).

Le discriminant est l'ÉGALITÉ EXACTE (6 décimales ≈ 0,1 m), pas un rayon. Deux géométries de
SITES réels distincts ne coïncident jamais au décimètre ; deux campus voisins légitimes
tombent sous un rayon mais pas sous l'égalité stricte. Un rayon attraperait les vrais voisins
(Nozay) ; l'égalité stricte n'attrape que le géocodeur. Les vrais doublons de contenu (même
dossier servi deux fois) sont fusionnés en amont par `--dedup-contenu` : ce qui partage encore
un centroïde après dédup est donc bien DISTINCT.
"""

from __future__ import annotations


def centroid_key(centroid: dict | None) -> tuple[float, float] | None:
    """Clé comparable d'un `procedure.centroid` ({lat, lon}), ou None s'il n'y en a pas."""
    if not isinstance(centroid, dict):
        return None
    lat, lon = centroid.get("lat"), centroid.get("lon")
    if lat is None or lon is None:
        return None
    return (round(float(lat), 6), round(float(lon), 6))


def shared_centroids(docs: dict[str, dict]) -> dict[tuple[float, float], list[str]]:
    """{(lat, lon): [noms de dossiers]} pour tout centroïde porté par ≥ 2 dossiers DISTINCTS.

    `docs` : {nom_dossier: fiche} (la fiche porte `procedure.centroid`). Un centroïde partagé
    par plusieurs dossiers est une coordonnée de géocodeur (commune/zone), pas un site.
    """
    groups: dict[tuple[float, float], list[str]] = {}
    for nom, doc in docs.items():
        key = centroid_key(((doc or {}).get("procedure") or {}).get("centroid"))
        if key is not None:
            groups.setdefault(key, []).append(nom)
    return {key: sorted(noms) for key, noms in groups.items() if len(noms) >= 2}


def geocoder_keys(docs: dict[str, dict]) -> set[tuple[float, float]]:
    """L'ensemble des clés de centroïde à ÉCARTER comme géométrie (partagées = géocodeur)."""
    return set(shared_centroids(docs))
