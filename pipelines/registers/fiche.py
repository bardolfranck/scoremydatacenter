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

import re
from datetime import date, datetime

from .avis import Avis
from .index import Dossier

CREDIT = ("Registre : avis de l'autorité environnementale, DREAL/DRIEAT, Licence Ouverte v2. "
          "Avis : document public, lié et non réhébergé. Extraction ScoreMyDataCenter.")

# Date portée par le NOM DE FICHIER MRAe, dans l'ordre de confiance décroissante. Trois formats
# NON AMBIGUS seulement : l'année à quatre chiffres (préfixée « 20 ») lève toute hésitation. On
# n'essaie PAS le YYMMDD à six chiffres — il collisionne avec les numéros d'avis (« n022432 »,
# « 15721 ») et une date fausse est pire qu'une date absente.
_DATE_FICHIER = [
    (re.compile(r"(20\d\d)[-_](\d{2})[-_](\d{2})"), (0, 1, 2)),      # 2025-05-07
    (re.compile(r"(?<!\d)(\d{2})[-_](\d{2})[-_](20\d\d)(?!\d)"), (2, 1, 0)),  # 07-05-2025 (jour-mois-an, FR)
    (re.compile(r"(?<!\d)(20\d\d)(\d{2})(\d{2})(?!\d)"), (0, 1, 2)),  # 20250507
]


def date_du_nom_de_fichier(url: str | None) -> str | None:
    """La date lue dans le NOM DE FICHIER de l'avis MRAe (ISO), ou None si aucune sûre.

    Le nom de fichier est la seule date fiable d'un avis d'origine nationale : l'index publie
    parfois une date captée dans le CORPS du PDF (futur, décalée de mois ou d'années). On ne
    retient qu'une date réellement valide (le 31 février est rejeté).
    """
    nom = (url or "").rsplit("/", 1)[-1]
    for rx, (iy, im, idd) in _DATE_FICHIER:
        m = rx.search(nom)
        if not m:
            continue
        y, mo, da = m.group(iy + 1), m.group(im + 1), m.group(idd + 1)
        try:
            return date(int(y), int(mo), int(da)).isoformat()
        except ValueError:
            continue   # 00 ou 13 en mois, 32 en jour… : ce n'était pas une date
    return None


def _parse_date(s: str | None) -> date | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


# Au-delà de ce nombre de jours, l'écart entre la date de l'index et celle du nom de fichier n'est
# plus un décalage délibération/publication (±1-2 j) mais une date captée dans le corps du PDF.
# Mesuré : les écarts légitimes sont ≤ 2 j, les captures ≥ 355 j — n'importe quel seuil entre les
# deux marche ; 15 j laisse la marge sans risque.
SEUIL_DATE_JOURS = 15


def date_corroboree(date_index: str | None, url: str | None,
                    seuil_jours: int = SEUIL_DATE_JOURS) -> tuple[str | None, str]:
    """Croise la date de l'index avec celle du nom de fichier. Renvoie (date_retenue, statut).

    · `confirmee`    — les deux coïncident ;
    · `a_arbitrer`   — écart ≤ seuil (délibération vs publication ?) : on GARDE l'index, un humain
                       tranche (ne JAMAIS écraser en silence une date peut-être juste) ;
    · `corrigee`     — écart > seuil : l'index a capté une date du corps du PDF, on retient celle
                       du nom de fichier (date de publication, seule ancre fiable) ;
    · `non_confirmee`— pas de date sûre dans le nom de fichier : on garde l'index, non corroboré.
    """
    fd = date_du_nom_de_fichier(url)
    if fd is None:
        return date_index, "non_confirmee"
    pi = _parse_date(date_index)
    if pi is None:
        return fd, "corrigee"
    if abs((date.fromisoformat(fd) - pi).days) == 0:
        return date_index, "confirmee"
    if abs((date.fromisoformat(fd) - pi).days) <= seuil_jours:
        return date_index, "a_arbitrer"
    return fd, "corrigee"


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
    # La date de l'index national n'est pas fiable (elle capte parfois une date du corps du PDF) ;
    # on la corrobore par le nom de fichier et on retient la date de publication quand l'écart est
    # grossier. L'écart léger (délibération vs publication) est gardé tel quel, à arbitrer.
    date_avis, _statut = date_corroboree(doc.date, doc.doc_url)
    return {
        "schema": "smdc.registre-ae/1",
        "source": {
            "doc_url": doc.doc_url,
            "origine": doc.origine,
            "registre": None,
            "pdf": pdf_meta,
        },
        "procedure": {"intitule": doc.titre, "date_avis": date_avis,
                      # l'index national ne publie pas le pétitionnaire : on le lit dans le PDF.
                      **({"petitionnaire": avis.petitionnaire} if avis.petitionnaire else {})},
        "installation": inst,
        "credit": CREDIT,
    }


def build(dossier: Dossier, avis: Avis) -> dict:
    proc = dossier.as_dict()
    # Le registre donne le pétitionnaire ; s'il manque, on prend celui lu dans le PDF.
    if not proc.get("petitionnaire") and avis.petitionnaire:
        proc["petitionnaire"] = avis.petitionnaire
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
