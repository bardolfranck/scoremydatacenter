# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le GROUPE de puissance d'un site — l'unique lecture autorisée de la puissance pour comparer.

⭐ POURQUOI UN GROUPE ET PAS UNE VALEUR (décision Franck, 2026-10-15). Le comparateur avait été
retiré de la production parce qu'il comparait des TERRITOIRES faute de pouvoir comparer des
OBJETS : « si tu dis à un pro que Marseille dense est comparable à Marly, tu n'es pas
crédible ». La puissance est le critère de comparabilité — mais sur 221 puissances françaises,
**zéro n'est mesurée** : 126 sont annoncées, 92 estimées. Comparer sur un axe CONTINU fait de
valeurs annoncées et estimées revendiquerait une précision qu'on n'a pas.

Le groupe règle ça : une estimation de 12 MW à ±50 % reste dans « 6–50 MW ». **La bande
absorbe l'imprécision que le point exposait**, et la grille du métier est de toute façon
ordinale. Le comparateur ne lit donc JAMAIS `power_mw` : il lit un groupe, ce qui rend la
provenance (mesurée, annoncée, estimée, fourchette) sans effet sur la comparaison.

## DEUX ÉTAGES, parce que c'est ainsi qu'on lit (Franck)

> « on ne mélange pas Marly si petit avec Marseille hyperscaler, c'est une comparaison
> mentale grossière ; ensuite on affine côté Marly petit-petit ou petit-moyen. Comme un arbre
> de décision : d'abord la ZONE de l'arbre où tombe la décision, ensuite la CASE. On stocke
> les deux. »

🔴 L'étage grossier est une **AGRÉGATION** du fin, jamais un découpage parallèle — sinon
« zone → case » n'est pas un arbre et une fiche pourrait tomber dans deux branches
incohérentes.

⭐ ET C'EST L'ÉTAGE GROSSIER QUI SAUVE LES FOURCHETTES. « 60 à 240 MW » est ambigu au fin
(50–100 ou 100–500) et **tranché au grossier** : grand, quelle que soit la valeur réelle.
C'est un FAIT, pas un choix à défendre. Mesuré au passage : l'étage grossier sépare
aujourd'hui MIEUX que le fin (les hyperscalers n'existent que dans « grand », les télécoms
captifs n'y entrent jamais), parce qu'au fin les 221 fiches s'éparpillent sur six cases dont
deux n'en contiennent que 3 et 4.

## QUAND MÊME LE GROSSIER EST AMBIGU : le MAXIMUM, et seulement là

« 3–8 MW » est petit-ou-moyen, « 40–60 » moyen-ou-grand. On retient alors le **haut** de la
fourchette. Minorer la puissance d'un projet le rendrait moins impactant qu'il n'est —
l'erreur dans le sens FAVORABLE, celle qu'on s'interdit partout ailleurs
([[favorable-par-absence-de-detection]]).

⚠️ Le maximum et le MILIEU de fourchette ne coïncident pas : « 60–110 » donne « 100–500 » par
le haut et « 50–100 » par le milieu. La règle déclarée est le **maximum** ; le milieu n'est
pas un second avis qui la confirmerait.

## FRAGILITÉ AU BORD

Une valeur proche d'une limite de groupe est fragile : 5 MW estimés à ±20 % basculent entre
« 1–5 » et « 6–50 ». Le groupe porte donc `au_bord`, faute de quoi on recréerait au SEUIL ce
qu'on vient de supprimer au POINT — exactement la leçon des bandes de distance sensibles à la
coordonnée ([[bande-distance-sensible-coord-mairie]]).
"""

from __future__ import annotations

# Les bornes HAUTES de chaque case, dans l'ordre. Grille du métier (Yves Grandmontagne,
# DCmag) : 0-1 / 1-5 / 6-50 / 50-100 (début hyperscaler) / 100-500 / 500 MW+.
CASES: tuple[tuple[float, str], ...] = (
    (1, "0–1"), (5, "1–5"), (50, "6–50"), (100, "50–100"), (500, "100–500"),
    (float("inf"), "500+"),
)

# L'étage grossier AGRÈGE le fin — chaque case appartient à une zone et une seule.
ZONES: dict[str, str] = {
    "0–1": "petit", "1–5": "petit",
    "6–50": "moyen",
    "50–100": "grand", "100–500": "grand", "500+": "grand",
}

# Un point à moins de 10 % d'une borne de case est déclaré au bord.
MARGE_BORD = 0.10


def case(mw: float) -> str:
    """La case fine qui contient cette puissance."""
    return next(nom for haut, nom in CASES if mw <= haut)


def zone(nom_de_case: str) -> str:
    return ZONES[nom_de_case]


def _au_bord(mw: float) -> bool:
    for haut, _ in CASES:
        if haut == float("inf"):
            continue
        if abs(mw - haut) <= haut * MARGE_BORD:
            return True
    return False


def groupe(identite: dict) -> dict | None:
    """{zone, case, determine, au_bord, origine} — ou None si aucune puissance connue.

    `determine` dit à quel étage la fourchette a pu être tranchée SANS recourir au maximum :
    `"case"` (les deux étages), `"zone"` (le grossier seulement), `"maximum"` (ni l'un ni
    l'autre — la règle de prudence a tranché). C'est cette clé qui permet à l'affichage de
    dire « groupe non déterminé au niveau fin » au lieu de faire passer un arbitrage pour une
    mesure.
    """
    i = identite or {}
    plage = i.get("power_mw_range") or {}
    bas, haut = plage.get("min"), plage.get("max")
    if bas is not None and haut is not None:
        bas, haut = float(bas), float(haut)
        if bas > haut:
            raise ValueError(f"fourchette inversée : min={bas} > max={haut}")
        c_bas, c_haut = case(bas), case(haut)
        if c_bas == c_haut:
            return {"zone": zone(c_haut), "case": c_haut, "determine": "case",
                    "au_bord": _au_bord(bas) or _au_bord(haut), "origine": "fourchette"}
        if zone(c_bas) == zone(c_haut):
            # L'étage grossier tranche là où le fin ne peut pas : un FAIT, pas un arbitrage.
            return {"zone": zone(c_haut), "case": None, "determine": "zone",
                    "au_bord": False, "origine": "fourchette"}
        # Les deux étages sont ambigus → le haut de la fourchette, jamais le bas.
        return {"zone": zone(c_haut), "case": c_haut, "determine": "maximum",
                "au_bord": False, "origine": "fourchette"}

    mw = i.get("power_mw")
    if mw is None:
        return None
    mw = float(mw)
    c = case(mw)
    return {"zone": zone(c), "case": c, "determine": "case", "au_bord": _au_bord(mw),
            "origine": i.get("power_mw_status") or "non_documente"}
