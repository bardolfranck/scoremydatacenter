# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Tests hors-ligne de la découverte GB (planning.data.gov.uk). On fige la logique pure : le
détecteur DC, la géométrie, le mapping entité→Dossier, et le fait que le VIVIER réglementaire
couvre bien les nuisances que Franck priorise. Le réseau est exercé à la main (cf docstring)."""

from pipelines.registers import gb_planning as gb


def test_dc_matcher_catches_spellings_and_rejects_false_friends():
    for yes in ("Erection of a data centre", "New datacentre (Use Class B8)",
                "Colocation facility", "Hyperscale data center campus", "server farm"):
        assert gb.IS_A_DC.search(yes) and not gb.NOT_A_DC.search(yes), yes
    for no in ("Data cabling to office", "Metadata archive refurbishment",
               "Erection of single dwelling", "Data protection signage"):
        assert not (gb.IS_A_DC.search(no) and not gb.NOT_A_DC.search(no)), no


def test_centroid_is_mean_of_wkt_vertices_lonlat_order():
    # POLYGON lon lat ; centre attendu ~ (51.51, -0.13).
    c = gb._centroid("POLYGON((-0.14 51.50,-0.12 51.50,-0.12 51.52,-0.14 51.52,-0.14 51.50))")
    assert c is not None
    assert abs(c[0] - 51.51) < 0.02 and abs(c[1] - (-0.13)) < 0.02
    assert gb._centroid("") is None            # pas de géométrie → pas de point fabriqué


def test_bbox_wkt_grows_with_radius_and_is_lonlat():
    small = gb._bbox_wkt(51.5, -0.13, 100)
    big = gb._bbox_wkt(51.5, -0.13, 1000)
    # plus grand rayon → sommets plus écartés
    assert len(gb._centroid(small) or ()) == 2
    assert small.startswith("POLYGON((") and "51.5" in small


def test_entity_maps_to_dossier_without_network(monkeypatch):
    gb._COUNCIL_CACHE[109] = "Test Borough Council"   # évite l'appel réseau de council_name
    e = {"organisation-entity": 109, "reference": "24/0123/FUL",
         "description": "Construction of a data centre", "decision-date": "2024-06-01",
         "start-date": "2024-01-10", "entity": 10000000042,
         "geometry": "POLYGON((-0.14 51.50,-0.12 51.50,-0.12 51.52,-0.14 51.52,-0.14 51.50))"}
    d = gb._to_dossier(e)
    assert d.region == "GB-109" and d.commune == "Test Borough Council"
    assert d.numero_avis == "24/0123/FUL" and d.date_avis == "2024-06-01" and d.statut == "decided"
    assert d.doc_url.endswith("/10000000042") and d.centroid is not None
    # sans décision → statut 'live'
    assert gb._to_dossier({"reference": "x"}).statut == "live"


def test_required_documents_cover_the_nuisance_vein():
    docs = gb.REQUIRED_DOCUMENTS
    # chaque entrée a la même forme déclarative
    for k, v in docs.items():
        assert set(v) >= {"mandatory", "yields", "feeds"}, k
    # les nuisances prioritaires de Franck doivent être alimentées par au moins un document
    feeds = {f for v in docs.values() for f in v["feeds"]}
    for must in ("bruit", "groupes_electrogenes", "cuves_fioul", "E6_chaleur_fatale",
                 "W3_volumes", "E2_capacite"):
        assert must in feeds, must
