# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Contrats de SIGNATURE des fonctions empruntées par une autre couche (la couche fiche du site
importe `run._content_fp` et `fiche.date_corroboree`). Une dérive doit casser ICI, à la SOURCE,
pas chez l'emprunteur : on a vu le coût de l'inverse — `date_corroboree` est passée de 2 à 3
valeurs de retour, l'appel aval aurait dû lever un ValueError mais ne l'a pas, parce que son
propre filtre amont avait rendu ce code inatteignable. Casse latente, qui attendait une réparation
sans rapport pour sortir. Ces tests figent la forme du retour pour que le prochain changement la
fasse échouer le jour même.
"""

from pipelines.registers import fiche, run


def test_contrat_content_fp_renvoie_une_empreinte_ou_none():
    # run._content_fp(d) -> str | None (une valeur simple, JAMAIS un tuple). La couche fiche
    # l'importe pour détecter les doublons à la publication.
    plein = {"installation": {"faits": {"e": [{"indicateur": "a", "valeur": 1, "page": 2}]}},
             "source": {"pdf": {"pages": 10}}}
    fp = run._content_fp(plein)
    assert isinstance(fp, str) and fp                      # une empreinte
    assert run._content_fp({"installation": {"faits": {}}}) is None   # aucun fait -> None
    # déterministe : même entrée, même empreinte (c'est ce sur quoi repose le garde-fou aval).
    assert run._content_fp(plein) == fp


def test_contrat_date_corroboree_renvoie_un_triplet():
    # fiche.date_corroboree(date_index, url) -> (date_avis, statut, date_mise_en_ligne).
    # Trois valeurs : la couche fiche déballe les trois. Changer l'arité doit casser ce test.
    r = fiche.date_corroboree("2025-05-07", "http://x/2025-05-07_a.pdf")
    assert isinstance(r, tuple) and len(r) == 3
    date_avis, statut, mel = r
    assert isinstance(date_avis, str)
    assert statut in {"confirmee", "corrigee", "non_confirmee"}
    assert mel is None or isinstance(mel, str)
