# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Lecture ESG d'une fiche — des indicateurs INFORMATIFS, HORS NOTE.

Rien ici n'entre dans le calcul de la note : le moteur de notation ne lit pas ce module, et
ce que ce module produit voyage dans son propre champ (`esg`) du dc/{id}.json servi.

## IEF — Indice d'efficacité foncière

Proposé par le « Guide du Data Center Durable et Acceptable » (Ville de Demain, partie 5) :

    IEF = (puissance kW / emprise au sol m²) × (1 + TRF)

où TRF dit si le site réutilise un sol déjà artificialisé. Le guide en fait une PART de
surface ; nous n'avons qu'un indicateur de sol tranché (F2). Nous prenons donc TRF = 1 si F2
dit `artificialized`, TRF = 0 si F2 dit `agricultural` ou `natural_or_enaf`.

🔴 RIEN PLUTÔT QU'UNE VALEUR APPROCHÉE. Un indice affiché sur des entrées douteuses serait
lu comme une mesure. On ne calcule que si les TROIS entrées sont des faits :
- la puissance est un nombre UNIQUE (`power_mw`) dont la provenance est `measured` ou
  `announced` (`identity.power_mw_status`). Une puissance `estimated` vient de notre modèle ;
  une puissance sans statut est un remplissage hérité de provenance non déclarée (contrat
  du schéma) ; une fourchette n'est pas un nombre. Aucun de ces cas ne donne d'IEF ;
- l'emprise est F4 (hectares, emprise TOTALE du site), avec une valeur numérique > 0, un
  statut `measured` ou `announced` ET une source ;
- le sol F2 est tranché dans l'un des trois cas ci-dessus. `transitional` ou inconnu → rien.

L'indice favorise les grands sites denses : c'est dit dans la limite affichée, pas corrigé ici.
"""

from __future__ import annotations

# Statuts de puissance qui sont des FAITS (schéma : identity.power_mw_status).
PUISSANCE_FAITS = frozenset({"measured", "announced"})
# Statuts d'indicateur qui portent une valeur sourcée.
INDICATEUR_FAITS = frozenset({"measured", "announced"})
# F2 → TRF. Absent du dict (transitional, inconnu) = pas d'IEF.
TRF_PAR_SOL = {"artificialized": 1, "agricultural": 0, "natural_or_enaf": 0}


def _entree(dc: dict, ind_id: str) -> dict:
    return next((e for e in dc.get("indicators") or [] if e.get("id") == ind_id), {})


def ief(dc: dict) -> dict | None:
    """L'IEF d'une fiche avec ses entrées, ou None si une entrée n'est pas un fait."""
    ident = dc.get("identity") or {}
    mw = ident.get("power_mw")
    statut_mw = ident.get("power_mw_status")
    if not isinstance(mw, (int, float)) or isinstance(mw, bool) or mw <= 0:
        return None
    if statut_mw not in PUISSANCE_FAITS:
        return None

    f4 = _entree(dc, "F4")
    ha = f4.get("value")
    if (not isinstance(ha, (int, float)) or isinstance(ha, bool) or ha <= 0
            or f4.get("status") not in INDICATEUR_FAITS or not f4.get("source")):
        return None

    f2 = _entree(dc, "F2")
    sol = f2.get("value")
    if sol not in TRF_PAR_SOL or f2.get("status") not in INDICATEUR_FAITS:
        return None
    trf = TRF_PAR_SOL[sol]

    kw_par_m2 = (float(mw) * 1000) / (float(ha) * 10_000)
    return {
        "value": round(kw_par_m2 * (1 + trf), 3),
        "unit": "kW/m²",
        "inputs": {
            "power_mw": mw,
            "power_mw_status": statut_mw,
            "footprint_ha": ha,
            "footprint_status": f4.get("status"),
            "footprint_source": f4.get("source"),
            "soil": sol,
            "trf": trf,
        },
    }


def esg_fields(dc: dict) -> dict:
    """Le champ ADDITIF `esg` du dc/{id}.json — vide (donc absent) quand rien n'est calculable."""
    valeur = ief(dc)
    return {"esg": {"ief": valeur}} if valeur else {}
