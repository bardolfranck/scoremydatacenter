# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""La FICHE : un dossier de registre + son avis, assemblés en un JSON d'EXTRACTION.

Troisième maillon : `index.py` donne le dossier et le lien, `avis.py` lit le PDF, ici on
assemble. Deux blocs SÉPARÉS, et la séparation n'est pas cosmétique :

  · `procedure` vient du REGISTRE. C'est un acte administratif : le pétitionnaire, la
    commune, les dates, le statut. Fiable, structuré, daté.
  · `installation` vient du PDF. C'est ce que le dossier du pétitionnaire déclare et ce que
    l'autorité en retient. Chaque valeur porte sa phrase et sa page — donc vérifiable, mais
    d'une autre nature : une déclaration de projet, pas un acte.

Les mélanger produirait un objet dont on ne pourrait plus dire ce qui est opposable.

CE FICHIER NE FAIT AUCUNE ANALYSE (arbitrage Franck, 2026-09-30). Pas de note, pas de
conclusion, pas de rapprochement avec une fiche notée du corpus : rattacher un dossier à un
site, c'est déjà décider, et ça appartient à l'étage d'après. Ici on relève, on source, on
pagine, rien de plus. Cette discipline est ce qui rend le JSON redistribuable tel quel.

L'URL du PDF est portée UNE SEULE FOIS, en tête, dans `source`. Elle vaut pour tout le
fichier : chaque fait porte déjà sa page, et répéter l'adresse à chaque bloc n'ajoute rien
qu'un poids.
"""

from __future__ import annotations

from .avis import Avis
from .index import Dossier

CREDIT = ("Registre : avis de l'autorité environnementale, DREAL/DRIEAT, Licence Ouverte v2. "
          "Avis : document public, lié et non réhébergé. Extraction ScoreMyDataCenter.")


def build_national(doc, avis: Avis) -> dict:
    """Même schéma, mais depuis l'INDEX DOCUMENTAIRE national (site des MRAe).

    `procedure` est volontairement maigre : le site ne publie ni pétitionnaire, ni INSEE, ni
    géométrie, ni statut. Le champ `origine` porte la différence, et il est obligatoire — un
    lecteur doit pouvoir dire, sans enquêter, si la fiche vient d'un acte administratif
    indexé ou d'un document trouvé par un moteur de recherche.
    """
    inst = avis.as_dict()
    pdf_meta = inst.pop("source")
    pdf_meta.pop("doc_url", None)
    return {
        "schema": "smdc.registre-ae/1",
        "source": {
            "doc_url": doc.doc_url,
            "origine": doc.origine,
            "registre": None,
            "pdf": pdf_meta,
        },
        "procedure": {"intitule": doc.titre, "date_avis": doc.date},
        "installation": inst,
        "credit": CREDIT,
    }


def build(dossier: Dossier, avis: Avis) -> dict:
    proc = dossier.as_dict()
    inst = avis.as_dict()
    pdf_meta = inst.pop("source")
    doc_url = proc.pop("doc_url", "") or pdf_meta.pop("doc_url", "")
    pdf_meta.pop("doc_url", None)
    return {
        "schema": "smdc.registre-ae/1",
        # L'adresse du document, une fois pour tout le fichier. Chaque fait porte sa page.
        "source": {
            "doc_url": doc_url,
            "registre": {"region": proc.pop("region", ""), "licence": "Licence Ouverte v2"},
            "pdf": pdf_meta,
        },
        "procedure": proc,
        "installation": inst,
        "credit": CREDIT,
    }
