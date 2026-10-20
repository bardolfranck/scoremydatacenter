# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Numbers asserted here were computed BY HAND from the draft methodology —
they are an independent check of the engine, not a copy of its output."""

from engine.scoring import score_datacenter


def test_alpha_dual_grades(methodology, alpha):
    r = score_datacenter(alpha, methodology)
    site = r["grades"]["site"]
    # no editorial gloss: the letter and the one-decimal score, nothing else
    # 79,3 -> 79,8 le 2026-10-17 : L1 est passé en `penalty_only`, donc son état « aucune
    # pénalité » est inerte et ne tire plus la moyenne du pilier. La LETTRE ne bouge pas.
    assert (site["grade"], site["score"]) == ("B", 79.8)
    assert "close_to" not in site
    pp = r["grades"]["project_process"]
    # v0.2.0: heat recovery split out of F5 → E7 (project) entered MVP; alpha discloses no
    # E7 commitment (missing) → project coverage 0.871 and the project/process score 50.6
    # under the reweighted Energy grid.
    assert (pp["grade"], pp["score"], pp["coverage"]) == ("C", 50.6, 0.871)


def test_alpha_confidence_two_causes(methodology, alpha):
    c = score_datacenter(alpha, methodology)["confidence"]
    assert c["level"] == "high"
    # v0.2.0: E7 (heat-recovery commitment) undisclosed by alpha → a sliver of missing_data;
    # the unverifiable_declarative share renormalizes over the reweighted importance pool.
    assert c["causes"]["missing_data"] == 0.018
    assert c["causes"]["unverifiable_declarative"] == 0.096


def test_beta_site_grade_on_rounded_score(methodology, beta):
    site = score_datacenter(beta, methodology)["grades"]["site"]
    # iter-2 base thresholds move beta to 30.0 -> E. The rounding guarantee this
    # test pins (letter graded on the rounded published score, so number and letter
    # can never contradict) holds at any value; re-pin a .x5 boundary case at freeze.
    # 30,0 -> 29,5 le 2026-10-17 : beta porte L1=`sensitive`, et une colonne à pénalité seule
    # ne peut plus faire MONTER son pilier (elle le faisait : 29,5 -> 30,0, c'est la contrainte
    # éthique qui l'a attrapé). La LETTRE ne bouge pas.
    assert (site["grade"], site["score"]) == ("E", 29.5)


def test_beta_project_process_insufficient_data(methodology, beta):
    pp = score_datacenter(beta, methodology)["grades"]["project_process"]
    assert pp == {"grade": "insufficient_data", "coverage": 0.0}


def test_beta_confidence_missing_cause(methodology, beta):
    c = score_datacenter(beta, methodology)["confidence"]
    assert c["level"] == "medium"
    # v0.2.0: E6/E7 entered MVP; beta discloses no project data and its heat-network E6 is
    # not collected, nudging missing_data up to 0.336.
    assert c["causes"]["missing_data"] == 0.336
    assert c["causes"]["unverifiable_declarative"] == 0.0


def test_une_sous_note_calculee_est_affichee_quelle_que_soit_sa_couverture(methodology, beta):
    """Une couverture basse ne retire plus la sous-note (Franck, 2026-10-20).

    Jusqu'à cette date une sous-note sous `min_coverage` était remplacée par un tiret, pour
    ne pas infliger « une lettre punitive tirée d'inconnues ». Mais cette lettre entrait DÉJÀ
    dans la note de site publiée, au même poids : la cacher ne protégeait pas l'opérateur,
    elle privait le lecteur du pilier qui explique la note. Ce qu'on ignore se dit en toutes
    lettres à côté, pas par un tiret muet.
    """
    pillars = score_datacenter(beta, methodology)["pillars"]
    assert pillars["energy"]["coverage"] == 0.602 and pillars["energy"]["grade"] == "E"
    # 0,4 était exactement le seuil ; il n'y a plus de seuil du tout.
    assert pillars["local_impact"]["coverage"] == 0.4 and pillars["local_impact"]["grade"] == "E"
    # couverture NULLE et pourtant une lettre — et c'est juste : T1 et T2 sont `missing`,
    # c'est-à-dire LUS ET ABSENTS du dossier. Une opacité vérifiée est l'information même que
    # le pilier transparence mesure, pas un trou de collecte. La couverture, elle, ne compte
    # que les données substantielles : elle ne sait pas distinguer « rien lu » de « lu et vide ».
    assert pillars["transparency_governance"]["coverage"] == 0.0
    assert pillars["transparency_governance"]["grade"] == "E"


def test_pas_de_lettre_quand_il_n_y_a_rien_a_agreger(methodology, beta):
    """Le seul cas où le tiret dit la vérité — et la garde se pose sur l'AGRÉGAT.

    Elle ne peut pas se poser sur la couverture : les deux ensembles ne coïncident pas. Un
    indicateur de polarité « ne peut que pénaliser » dans son état neutre est INERTE (il ne
    déplace pas la note) tout en comptant dans la couverture. Un pilier peut donc afficher
    une couverture non nulle sans avoir une seule valeur à moyenner — c'est le cas de
    fr-cloudata en production, et garder la couverture comme garde faisait planter le moteur
    sur cette fiche-là (`NoneType __round__`).
    """
    import copy
    muet = copy.deepcopy(beta)
    for ind in muet["indicators"]:
        if ind["id"] == "L1":                       # penalty_only : « aucune pénalité » = inerte
            ind["value"], ind["status"] = "neutral", "measured"
        elif ind["id"] in ("L2", "L3", "L4", "L5", "L6", "L7"):
            ind["status"], ind["value"] = "not_collected", None
    local = score_datacenter(muet, methodology)["pillars"]["local_impact"]
    assert local["grade"] == "insufficient_data"
    assert local["coverage"] > 0                     # la couverture, elle, n'est PAS nulle
    assert "documentation" not in local              # pas de lettre, donc pas de pastille


def test_alpha_pillar_subscores(methodology, alpha):
    pillars = score_datacenter(alpha, methodology)["pillars"]
    # F5 (heat recovery) entered MVP (0.1.0-draft (f)) and alpha does not disclose it;
    # F5=0 pulls the land pillar from 87.5 (over F1–F4) to 78.8 (78.75 rounded), dropping A→B.
    assert pillars["land_biodiversity"]["grade"] == "B"
    assert pillars["land_biodiversity"]["score"] == 78.8
    assert set(pillars) == {"energy", "water", "land_biodiversity", "local_impact", "transparency_governance"}


def test_documentation_accompanies_every_grade(methodology, alpha):
    # Product rule n°1: a letter is never shown without its documentation chip.
    r = score_datacenter(alpha, methodology)
    for badge in ("site", "project_process"):
        doc = r["grades"][badge]["documentation"]
        assert doc["level"] in {"high", "medium", "low"}
        assert 1 <= doc["dots"] <= 4
        assert set(doc["label"]) == {"fr", "en"}
    for pillar, detail in r["pillars"].items():
        assert 1 <= detail["documentation"]["dots"] <= 4, pillar
        assert set(detail["documentation"]["label"]) == {"fr", "en"}


def test_no_documentation_without_a_grade(methodology, beta):
    # insufficient_data means no letter — and therefore no documentation chip either.
    # Porté sur l'AXE depuis le 2026-10-20 : les sous-notes par pilier ne sont plus retirées
    # pour couverture basse, donc beta n'a plus de pilier sans lettre. Le cas « pilier sans
    # rien à agréger » est figé par test_pas_de_lettre_quand_il_n_y_a_rien_a_agreger.
    r = score_datacenter(beta, methodology)
    assert r["grades"]["project_process"] == {"grade": "insufficient_data", "coverage": 0.0}
    assert "documentation" not in r["grades"]["project_process"]


def test_citable_quote_contrasts_when_a_pillar_is_worse(methodology, beta):
    # iter-2: beta's site fell to E, so it can no longer have a strictly-worse pillar.
    # Rebuild the contrast case from beta with a healthy grid (E2 ample, E3 low):
    # site rises to D while local_impact stays E (16.2) -> the headline names the contrast.
    import copy
    contrast = copy.deepcopy(beta)
    for ind in contrast["indicators"]:
        if ind["id"] == "E2": ind["value"] = "ample"
        if ind["id"] == "E3": ind["value"] = "low"
    q = score_datacenter(contrast, methodology)["citable_quote"]
    # Le pilier désigné est passé d'« Impact local » à « Transparence & gouvernance » quand
    # les sous-notes ont cessé d'être masquées (2026-10-20) : la phrase choisit le pilier le
    # plus bas parmi celles qui sont notées, et démasquer change cet ensemble. Transparence
    # est à 0.0 ici — T1 et T2 lus et absents du dossier, deux zéros vérifiés, donc une assise
    # de deux indicateurs : le titre est recevable.
    assert q["fr"].replace(chr(0xa0), " ") == "Noté D sur le site, mais E sur « Transparence & gouvernance »."
    assert q["en"] == "Rated D on site, but E on “Transparency & governance”."


def test_la_phrase_citable_ne_designe_pas_un_pilier_porte_par_un_seul_indicateur(methodology, beta):
    """MONTRER ET METTRE EN AVANT SONT DEUX MÉTIERS (Franck, 2026-10-20).

    Toutes les sous-notes s'affichent sur la fiche, sans plancher — mais là elles se lisent à
    côté des indicateurs manquants, nommés. La phrase citable, elle, voyage seule et finit
    dans un article. Mesuré avant la règle : 815 fiches sur 2 973 auraient donné un titre
    reposant sur UN indicateur, parfois à 13 % du poids du pilier.

    Ce n'est pas un plancher de couverture déguisé : la lettre reste publiée et comptée dans
    la note, c'est le TITRE qui se tait et retombe sur la phrase factuelle.
    """
    import copy
    from engine.scoring import _citable_quote
    site = {"grade": "B"}
    pp = {"grade": "C"}
    piliers = {"water": {"grade": "E", "score": 10.0, "coverage": 0.3}}

    seul = _citable_quote(site, pp, piliers, methodology, assise={"water": 1})
    assert "Eau" not in seul["fr"] and "mais" not in seul["fr"], \
        "un seul indicateur : le titre ne désigne pas le pilier"
    assert seul["fr"] == "Noté B sur le site, C en projet & processus."

    deux = _citable_quote(site, pp, piliers, methodology, assise={"water": 2})
    assert deux["fr"].replace(chr(0xa0), " ") == "Noté B sur le site, mais E sur « Eau »."


def test_citable_quote_is_factual_without_a_worse_pillar(methodology, alpha):
    # alpha: no graded pillar worse than site B -> no invented contrast, both notes stated.
    q = score_datacenter(alpha, methodology)["citable_quote"]
    assert q["fr"] == "Noté B sur le site, C en projet & processus."
    assert q["en"] == "Rated B on site, C on project & process."


def test_grade_boundary_is_inclusive(methodology, alpha):
    thresholds = {t["grade"]: t["min"] for t in methodology["grade_thresholds"]}
    assert thresholds["B"] == 65  # sanity: draft grid
    from engine.scoring import _grade
    assert _grade(65.0, methodology)["grade"] == "B"
    assert _grade(64.949, methodology)["grade"] == "C"  # rounds to 64.9


def test_estimated_is_a_distinct_confidence_cause(methodology, alpha):
    # 1c contract: estimated dents confidence with the SAME penalty weight as declarative,
    # but stays a DISTINCT cause (the pre-mortem two-causes discipline, extended to three).
    import copy
    dc = copy.deepcopy(alpha)
    e4 = next(e for e in dc["indicators"] if e["id"] == "E4")
    assert e4["status"] == "announced"
    baseline = score_datacenter(alpha, methodology)["confidence"]
    e4["status"] = "estimated"
    shifted = score_datacenter(dc, methodology)["confidence"]
    moved = shifted["causes"]["model_estimated"]
    assert moved > 0
    # share moved cause, not weight (±0.0015: causes are rounded independently, plus float eps)
    assert abs(shifted["causes"]["unverifiable_declarative"] + moved
               - baseline["causes"]["unverifiable_declarative"]) <= 0.0015
    assert shifted["score"] == baseline["score"]                # same penalty → same confidence
