# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""La carte servie ne nomme aucun site (Franck 2026-11-09).

/data/map.geojson livrait en un fichier les 3 339 fiches avec nom, opérateur, commune et
lettre. Le build écrit désormais une version ANONYME (de quoi peindre la carte) et garde la
version complète pour les fonctions /api/carte/*, qui la servent un site à la fois.
Ce test fige les deux promesses dont tout dépend : aucun champ nominatif ne passe, et le
rang `t` désigne bien la même entité des deux côtés.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
from prune_public_json import CHAMPS_POINT_SITE, CHAMPS_POINT_VEILLE, anonymiser  # noqa: E402

NOMINATIFS = {"id", "name", "operator", "municipality", "source", "facts", "project_status"}


def _geo(props_list):
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [2.35 + i, 48.85]}, "properties": p}
        for i, p in enumerate(props_list)]}


def test_aucun_champ_nominatif_ne_passe():
    complet = _geo([
        {"id": "fr-x", "name": "X", "operator": "Op", "municipality": "Paris", "country": "FR",
         "grade_site": "B", "size_tier": 2, "first_seen": "2026-01-01", "band_central": "C",
         "band": "B–D", "reserved_site": True, "project_status": "operational", "en_veille": False},
        {"id": "fr-y", "name": "Y", "country": "FR", "grade_site": "insufficient_data", "size_tier": 0},
    ])
    servi = anonymiser(complet, CHAMPS_POINT_SITE)
    cles = {k for f in servi["features"] for k in f["properties"]}
    assert cles <= {"t", *CHAMPS_POINT_SITE}
    assert not cles & NOMINATIFS
    # La géométrie ne change pas : l'arrondi à ~1 km est fait en amont et testé ailleurs.
    assert [f["geometry"] for f in servi["features"]] == [f["geometry"] for f in complet["features"]]


def test_le_rang_designe_la_meme_entite():
    complet = _geo([{"id": f"fr-{i}", "name": str(i), "kind": "opposition", "country": "FR",
                     "facts": [], "source": {}} for i in range(5)])
    servi = anonymiser(complet, CHAMPS_POINT_VEILLE)
    for f_servi, f_complet in zip(servi["features"], complet["features"]):
        # La fonction serveur fait VEILLE[t] : le rang doit être l'index dans le complet.
        assert complet["features"][f_servi["properties"]["t"]] is f_complet
    assert {k for f in servi["features"] for k in f["properties"]} <= {"t", "kind", "country"}
