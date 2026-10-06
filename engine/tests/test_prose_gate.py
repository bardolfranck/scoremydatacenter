# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""GATE PROSE — une synthèse servie ne peut pas affirmer une absence que la valeur contredit.

Né d'un défaut réel : la démotion L3 du 2026-10-04 a corrigé 333 NOTES et laissé la PROSE.
97 fiches servies (ES 41, IT 53, FI 3) ont annoncé deux jours durant « aucun site à risque
industriel dans un rayon de 5 km » alors que leur L3 disait « non mesuré ». Un contrôle à la
RÉDACTION n'aurait rien vu : ces textes étaient justes le jour de leur écriture et sont devenus
faux quand la valeur a changé sous eux. D'où un gate sur ce qui est SERVI, à chaque build.
"""
import json

from engine.validate import prose_gate


def _fiche(tmp_path, nom, l3: dict, prose: str):
    p = tmp_path / f"{nom}.json"
    p.write_text(json.dumps({
        "id": nom,
        "indicators": [l3],
        "synthesis": {"site": {"lead": {"fr": "Titre", "en": "Title"},
                               "fr": prose, "en": prose}},
    }))
    return p


ABSENCE = "Le terrain est artificialisé et aucun site à risque industriel (Seveso) n'est recensé dans un rayon de 5 km."
MUETTE = "Le terrain est artificialisé et le réseau local est peu carboné."


def test_refuse_une_absence_affirmee_quand_la_valeur_dit_non_mesure(tmp_path):
    p = _fiche(tmp_path, "zz-demote", {"id": "L3", "status": "missing"}, ABSENCE)
    pb = prose_gate([p])
    assert len(pb) == 1 and "GATE PROSE" in pb[0] and "missing" in pb[0]


def test_refuse_une_absence_affirmee_quand_un_seveso_est_mesure(tmp_path):
    p = _fiche(tmp_path, "zz-present",
               {"id": "L3", "status": "measured", "value": "seveso_high_within_2km"}, ABSENCE)
    assert len(prose_gate([p])) == 1


def test_accepte_l_absence_affirmee_quand_la_valeur_l_etablit(tmp_path):
    p = _fiche(tmp_path, "zz-ok",
               {"id": "L3", "status": "measured", "value": "none_within_5km"}, ABSENCE)
    assert prose_gate([p]) == []


def test_une_prose_MUETTE_passe_meme_sur_une_valeur_defavorable(tmp_path):
    """INCOMPLET N'EST PAS FAUX. Le gate ne vérifie pas que la prose dit tout — sinon il
    exigerait de régénérer 305 textes véridiques, et on apprendrait à l'ignorer. Il vérifie
    la seule chose indéfendable : affirmer une absence que la mesure contredit."""
    p = _fiche(tmp_path, "zz-muette",
               {"id": "L3", "status": "measured", "value": "seveso_high_within_2km"}, MUETTE)
    assert prose_gate([p]) == []


def test_une_fiche_sans_synthese_ne_declenche_rien(tmp_path):
    p = tmp_path / "zz-nue.json"
    p.write_text(json.dumps({"id": "zz-nue", "indicators": [{"id": "L3", "status": "missing"}]}))
    assert prose_gate([p]) == []


def test_nearest_km_est_optionnel_nullable_et_refuse_le_negatif():
    """LA MARGE AU SEUIL DOIT SE LIRE SUR UN NOMBRE, pas par regex sur `source.title`.

    Un indicateur catégoriel (aucun / ≤5 km / ≤2 km) ne dit pas de combien on est loin de la
    bascule : savoir si une coordonnée imprécise peut faire changer la classe demande la
    distance. Ce test fige les trois propriétés dont dépend la rétro-compatibilité : le champ
    est OPTIONNEL (les 1565 fiches antérieures valident sans lui), il est NULLABLE (« la source
    n'a pas rendu de distance » ≠ zéro), et une distance négative est refusée.
    """
    from jsonschema import Draft202012Validator

    from engine.core import DATA_DIR, load_json

    schema = load_json(DATA_DIR / "schema" / "datacenter.schema.json")
    ind = schema["$defs"]["indicator"]
    valide = Draft202012Validator({**schema, **ind}, ).is_valid

    assert "nearest_km" not in ind["required"]
    assert valide({"id": "L3", "status": "missing"})                       # sans le champ
    assert valide({"id": "L3", "status": "missing", "nearest_km": None})   # nullable
    assert valide({"id": "L3", "status": "measured", "value": "none_within_5km",
                   "source": {"title": "t", "url": "https://e.org", "accessed": "2026-10-06"},
                   "nearest_km": 7.7})
    assert not valide({"id": "L3", "status": "missing", "nearest_km": -1})
