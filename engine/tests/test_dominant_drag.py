# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""« Ce qui pèse le plus ici » — le facteur dominant, et les deux gardes qui l'encadrent.

Le lecteur non spécialiste voit une lettre sans savoir ce qui la tire. On expose donc le
premier rang du classement des contributions. Trois décisions sont figées ici parce qu'elles
sont faciles à défaire par inadvertance :

1. le classement vient du MÊME produit que la note (importance × manque), pas d'une seconde
   hiérarchie inventée à côté de l'agrégat ;
2. un dominant de tier 2 ou 3 n'est PAS publié — il gagne faute de concurrents mesurés, pas
   parce qu'il pèse ;
3. la part par pays n'est servie qu'au-dessus d'un plancher de fiches, sinon « 89 % des sites
   portugais » reposerait sur huit fiches.

Ce qui n'est PAS testable ici mais doit être rappelé : la phrase ne se conditionne JAMAIS à la
distance au seuil. Sa seule présence serait alors la mesure de l'écart, et sur 1565 fiches elle
localiserait les seuils de calibration (arbitrage R&D, 2026-10-07). Le critère d'affichage est
la matière de la fiche, jamais sa position dans l'échelle.
"""
from engine.artifacts import dominant_drag, drag_fields
from engine.core import load_methodology


def _resultat(scores: dict) -> dict:
    return {"indicators": scores}


def test_le_dominant_est_le_premier_rang_du_produit_qui_fait_la_note():
    m = load_methodology()
    # E1 (énergie, tier 1) à 0 pèse plus que W2 (eau, tier 1) à 60 : même sens que l'agrégat.
    r = _resultat({"E1": 0.0, "W2": 60.0})
    assert dominant_drag(r, m) == "E1"
    # un score parfait ne pèse rien, donc le dominant devient l'autre
    assert dominant_drag(_resultat({"E1": 100.0, "W2": 60.0}), m) == "W2"


def test_un_dominant_de_tier_2_n_est_pas_publie():
    """E6 (tier 2) domine UNE fiche du corpus réel, faute de concurrents mesurés. Publier
    « ce qui pèse le plus ici, c'est l'absence de réseau de chaleur » serait vrai
    arithmétiquement et faux au sens commun — ça coûte plus en crédibilité que ça n'apporte."""
    m = load_methodology()
    assert {i["id"]: i.get("tier") for i in m["indicators"]}["E6"] == 2
    assert dominant_drag(_resultat({"E6": 0.0}), m) is None


def test_une_fiche_sans_indicateur_note_n_a_pas_de_facteur():
    assert dominant_drag(_resultat({}), load_methodology()) is None


def test_la_part_pays_disparait_sous_le_plancher():
    m = load_methodology()
    def corpus(n, cc):
        res = {f"{cc}-{i}": _resultat({"E1": 0.0}) for i in range(n)}
        dcs = {k: {"identity": {"country": cc}} for k in res}
        return drag_fields(res, dcs, m)
    gros = corpus(40, "xx")
    assert all(f["country_share"] == 1.0 for f in gros.values()), "40 fiches : la part se sert"
    mince = corpus(9, "yy")
    assert mince and all("country_share" not in f for f in mince.values()), \
        "9 fiches : le facteur se sert, la part NON (une part sur 9 fiches n'est pas une part)"
    assert all(f["indicator"] == "E1" for f in mince.values())
