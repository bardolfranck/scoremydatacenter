# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Méthodologie v0.5.0 (décision Franck, 2026-11-16) — les deux changements, figés.

1. L4 (emplois) et L5 (retombées fiscales) deviennent INFORMATIONNELS : publiés quand ils
   existent, jamais notés, jamais exigés par GATE 8. Leur absence vérifiée (`missing`) ne vaut
   plus 0.
2. Statut SANS OBJET (`not_applicable`) : l'instrument ne s'applique pas à ce site (F5 pour un
   DC sous le seuil de l'étude d'impact). Exclu du score ET de la couverture — ni 0 ni lacune —
   et permis SEULEMENT là où la méthodologie l'ouvre, avec une source qui dit pourquoi.
"""

import copy

from jsonschema import Draft202012Validator

from engine.core import REPO_ROOT, load_json
from engine.scoring import score_datacenter

SCHEMA = load_json(REPO_ROOT / "data" / "schema" / "datacenter.schema.json")


def _set(dc: dict, iid: str, **fields) -> dict:
    dc = copy.deepcopy(dc)
    for e in dc["indicators"]:
        if e["id"] == iid:
            for k in list(e):
                if k not in ("id",):
                    del e[k]
            e.update(fields)
    return dc


def test_l4_l5_sont_informationnels_et_le_pilier_somme_a_un(methodology):
    by_id = {i["id"]: i for i in methodology["indicators"]}
    for iid in ("L4", "L5"):
        assert by_id[iid]["informational"] is True and by_id[iid]["weight_in_pillar"] == 0
        assert by_id[iid]["mvp"] is True, "informationnel = publié : mvp reste vrai"
    # Poids RETIRÉ, non redistribué : les poids de base du pilier ne bougent pas (0,75), et la
    # somme avec le poids retiré de L4/L5 (0,25) fait 1 — GATE 3 reste vrai.
    li = [i for i in methodology["indicators"] if i["pillar"] == "local_impact"]
    assert abs(sum(i["weight_in_pillar"] for i in li) - 0.75) < 1e-9
    assert abs(sum(i["weight_in_pillar"] + i.get("retired_weight_in_pillar", 0) for i in li) - 1.0) < 1e-9


def test_un_l4_absent_du_dossier_ne_vaut_plus_zero(methodology, alpha):
    """Le cas Meudon : un L4 `missing` comptait 0 sur l'axe projet. Il ne pèse plus rien —
    la note de projet est la même qu'il soit lu et absent, ou jamais cherché."""
    lu_absent = _set(alpha, "L4", status="missing", value=None)
    jamais = _set(alpha, "L4", status="not_collected", value=None)
    a = score_datacenter(lu_absent, methodology)["grades"]["project_process"]
    b = score_datacenter(jamais, methodology)["grades"]["project_process"]
    assert (a.get("grade"), a.get("score"), a.get("coverage")) == (b.get("grade"), b.get("score"), b.get("coverage"))


def test_sans_objet_sort_du_score_et_de_la_couverture(methodology, alpha):
    """F5 sans objet = F5 absent de la méthodologie pour CETTE fiche : la note de projet est
    exactement celle qu'on obtient en retirant F5 des définitions — ni 0 (comme `missing`),
    ni lacune de couverture (comme `not_collected`)."""
    na = _set(alpha, "F5", status="not_applicable", value=None,
              source={"title": "DC de 1,25 MW en sous-sol : sous le seuil de l'étude d'impact", "url": None})
    r = score_datacenter(na, methodology)

    sans_f5 = copy.deepcopy(methodology)
    sans_f5["indicators"] = [i for i in sans_f5["indicators"] if i["id"] != "F5"]
    alpha_sans = copy.deepcopy(alpha)
    alpha_sans["indicators"] = [e for e in alpha_sans["indicators"] if e["id"] != "F5"]
    ref = score_datacenter(alpha_sans, sans_f5)

    assert r["grades"]["project_process"] == ref["grades"]["project_process"]
    assert r["grades"]["site"] == ref["grades"]["site"]
    # la ligne reste PUBLIÉE (sous-score vide), elle ne disparaît pas de la fiche
    assert "F5" in r["indicators"] and r["indicators"]["F5"] is None

    missing = score_datacenter(_set(alpha, "F5", status="missing", value=None), methodology)
    assert r["grades"]["project_process"]["coverage"] > missing["grades"]["project_process"]["coverage"] \
        or r["grades"]["project_process"]["score"] != missing["grades"]["project_process"]["score"]


def test_sans_objet_doit_dire_pourquoi():
    """Affirmer qu'un instrument ne s'applique pas se SOURCE : sans source, le schéma refuse."""
    v = Draft202012Validator(SCHEMA)
    alpha = load_json(REPO_ROOT / "data" / "datacenters" / "zz-test-alpha.json")
    sans_source = _set(alpha, "F5", status="not_applicable", value=None)
    avec_source = _set(alpha, "F5", status="not_applicable", value=None,
                       source={"title": "sous le seuil EIE", "url": None, "accessed": "2026-11-16"})
    assert any(True for _ in v.iter_errors(sans_source))
    assert not list(v.iter_errors(avec_source))


def test_sans_objet_nest_ouvert_que_sur_f5(methodology):
    ouverts = {i["id"] for i in methodology["indicators"] if i.get("not_applicable_allowed")}
    assert ouverts == {"F5"}
