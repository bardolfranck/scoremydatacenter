# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""La portée d'une sous-note : parle-t-elle DU SITE, ou du PAYS ?

Une sous-note peut être exacte et ne rien dire de ce site-là. Si le seul indicateur qui la
porte prend la même valeur partout dans le pays, la lettre décrit le pays : la publier sans
le dire laisse un élu croire que son site a été distingué de ses voisins alors qu'aucune
donnée ne les sépare. L'intensité carbone prend 26 valeurs aux États-Unis et une seule au
Royaume-Uni — le même indicateur, deux portées opposées.

Trois décisions sont figées ici parce qu'elles sont faciles à défaire par inadvertance :

1. « national » se DÉRIVE du corpus, jamais d'une liste tenue à la main — une liste dériverait
   en silence au premier pays ajouté, et mentirait là où personne ne regarde ;
2. la mesure porte sur le score NORMALISÉ, pas sur la valeur brute : deux valeurs brutes qui
   tombent dans la même classe ne séparent rien dans la note ;
3. sous le plancher de fiches, aucun verdict n'est rendu : « deux valeurs distinctes » y
   parlerait de l'effectif du pays, pas de la donnée.
"""
from engine.artifacts import _PAYS_MINIMAL_DISCERNEMENT, pillar_scope_fields
from engine.core import load_methodology


def _corpus(m, cc: str, n: int, varier: bool = False) -> tuple[dict, dict]:
    """n fiches dans le pays cc, toutes notées sur E1 (énergie). `varier` donne une valeur
    différente à la première — un seul site qui diffère suffit à rendre l'indicateur
    séparateur dans ce pays."""
    res, dcs = {}, {}
    for i in range(n):
        score = 10.0 if (varier and i == 0) else 50.0
        res[f"{cc}-{i}"] = {
            "indicators": {"E1": score},
            "pillars": {"energy": {"grade": "C", "score": score, "coverage": 0.3}},
        }
        dcs[f"{cc}-{i}"] = {"identity": {"country": cc}}
    return res, dcs


def test_un_indicateur_a_valeur_unique_dans_le_pays_est_national():
    m = load_methodology()
    res, dcs = _corpus(m, "xx", 40)
    portees = pillar_scope_fields(res, dcs, m)
    assert all(p["energy"] == "national" for p in portees.values()), \
        "40 sites, une seule valeur d'E1 : la lettre décrit le pays, pas le site"


def test_une_seule_fiche_differente_rend_l_indicateur_separateur():
    m = load_methodology()
    res, dcs = _corpus(m, "xx", 40, varier=True)
    portees = pillar_scope_fields(res, dcs, m)
    assert all(p["energy"] == "site" for p in portees.values()), \
        "dès que l'indicateur prend deux valeurs, il distingue — y compris le site médian"


def test_aucun_verdict_sous_le_plancher_de_fiches():
    """Avec trois fiches, un indicateur parfaitement national peut sembler distinguer, et
    l'inverse. Le verdict serait tiré de l'effectif, pas de la donnée."""
    m = load_methodology()
    n = _PAYS_MINIMAL_DISCERNEMENT - 1
    for varier in (False, True):
        res, dcs = _corpus(m, "yy", n, varier=varier)
        portees = pillar_scope_fields(res, dcs, m)
        assert portees and all(p["energy"] == "pays_mince" for p in portees.values()), \
            f"{n} fiches : on ne tranche pas (varier={varier})"


def test_un_pilier_sans_note_n_a_pas_de_portee():
    """La portée qualifie une lettre. Pas de lettre, rien à qualifier — l'état « en attente
    de données » se lit déjà sur la note elle-même, et le dire deux fois dériverait."""
    m = load_methodology()
    res, dcs = _corpus(m, "xx", 40)
    for r in res.values():
        r["pillars"]["water"] = {"grade": "insufficient_data", "coverage": 0.0}
    portees = pillar_scope_fields(res, dcs, m)
    assert all("water" not in p for p in portees.values())
    assert all("energy" in p for p in portees.values())


def test_la_portee_se_derive_par_pays_pas_globalement():
    """Le même indicateur peut distinguer dans un pays et pas dans l'autre. C'est le fait que
    la dérivation doit capturer : un verdict global écraserait les deux."""
    m = load_methodology()
    res_a, dcs_a = _corpus(m, "aa", 40, varier=True)   # E1 varie
    res_b, dcs_b = _corpus(m, "bb", 40, varier=False)  # E1 constant
    portees = pillar_scope_fields({**res_a, **res_b}, {**dcs_a, **dcs_b}, m)
    assert portees["aa-0"]["energy"] == "site"
    assert portees["bb-0"]["energy"] == "national"
