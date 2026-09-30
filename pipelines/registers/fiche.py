# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""La FICHE : un dossier de registre + son avis, assemblés en un JSON redistribuable.

Troisième maillon : `index.py` donne le dossier et le lien, `avis.py` lit le PDF, ici on
assemble. Deux blocs SÉPARÉS, et la séparation n'est pas cosmétique :

  · `procedure` vient du REGISTRE. C'est un acte administratif : le pétitionnaire, la
    commune, les dates, le statut. Fiable, structuré, daté.
  · `installation` vient du PDF. C'est ce que le dossier du pétitionnaire déclare et ce que
    l'autorité en retient. Chaque valeur porte sa phrase et sa page — donc vérifiable, mais
    d'une autre nature : une déclaration de projet, pas un acte.

Les mélanger produirait un objet dont on ne pourrait plus dire ce qui est opposable.

Le rattachement à une fiche notée du corpus est PROPOSÉ, jamais affirmé : le registre porte
le centroïde du DOSSIER, notre corpus porte le bâtiment. Quelques centaines de mètres
d'écart sont normales, et une coïncidence de commune n'est pas une identité. Le champ dit la
distance et laisse la décision à un humain — c'est la leçon des coordonnées fabriquées.
"""

from __future__ import annotations

import math

from .avis import Avis
from .index import Dossier

CREDIT = ("Registre : avis de l'autorité environnementale, DREAL/DRIEAT, Licence Ouverte v2. "
          "Avis : document public, lié et non réhébergé. Extraction ScoreMyDataCenter.")


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def build(dossier: Dossier, avis: Avis, corpus: dict[str, dict] | None = None) -> dict:
    """corpus : {fiche_id: {"municipality": str, "coordinates": {"lat","lon"}}} — facultatif."""
    out = {
        "schema": "smdc.registre-ae/1",
        "procedure": dossier.as_dict(),
        "installation": avis.as_dict(),
        "rattachement_corpus": None,
        "credit": CREDIT,
    }
    if corpus and dossier.centroid:
        near = []
        for fid, f in corpus.items():
            c = f.get("coordinates") or {}
            if not c:
                continue
            d = _haversine_m(dossier.centroid, (c["lat"], c["lon"]))
            if d <= 3000:
                near.append((d, fid, f.get("municipality")))
        near.sort()
        if near:
            d, fid, commune = near[0]
            out["rattachement_corpus"] = {
                "fiche_proposee": fid,
                "commune_fiche": commune,
                "distance_m": round(d),
                "confirme": False,
                "note": ("proposition géométrique : le registre porte le centroïde du DOSSIER, "
                         "le corpus porte le bâtiment. À confirmer par un humain — une commune "
                         "commune n'est pas une identité."),
                "autres_candidats": [{"fiche": f, "distance_m": round(x)} for x, f, _ in near[1:4]],
            }
    return out
