# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le bruit en BANDES structurées : point de mesure × période (jour/nuit) × valeur ou plage.

Les avis donnent le bruit apparié — « en limite est de propriété : 62,5–65 dB(A) le jour,
59,5–62 la nuit ». Sorti à plat (quatre dB(A) sans lien), l'appariement est perdu et un
« 65 dB(A) » seul n'apprend rien. Ce module reconstitue la bande, sans jamais rien inventer :
une période muette reste absente, une valeur hors contexte n'est pas rattachée.

DEUX GRANDEURS À NE PAS MÉLANGER (on a déjà payé le mélange une fois) :
  · le NIVEAU ambiant décrit surtout l'environnement (souvent une route) ;
  · l'ÉMERGENCE est l'écart avec/sans l'installation — le seul chiffre qui parle du data
    center lui-même, surtout en marche dégradée (groupes en fonctionnement).
Champs séparés, `parse_levels` et `parse_emergences`.

ON RAPPORTE, ON NE CONCLUT PAS. Si l'avis cite un seuil réglementaire, il est rapporté comme
citation ; on ne calcule JAMAIS la conformité nous-mêmes (« +14,6 dB pour un seuil de 3 »
serait un constat d'infraction — c'est l'État qui conclut).

La MÉTRIQUE est stockée toujours : un Lden (indice 24 h pénalisé) n'est pas comparable à un
LAeq, et les afficher dans la même colonne ferait mentir le tableau.
"""

from __future__ import annotations

import re

_NUM = r"[+]?\d{1,3}(?:[.,]\d+)?"
_DBA = r"dB\s*\(?\s*A\s*\)?"
_SEP = r"(?:entre\s+|de\s+)?"           # amorce de plage facultative
_RANGE = r"(?:et|à|a|-|–|—|/)"          # connecteur de plage (le « et » nu existe : « 51,7 et 56,7 »)

_DAY = r"(?:de\s+jour|le\s+jour|la\s+journée|en\s+p[ée]riode\s+diurne|p[ée]riode\s+diurne|diurnes?|en\s+diurne)"
_NIGHT = r"(?:de\s+nuit|la\s+nuit|en\s+p[ée]riode\s+nocturne|p[ée]riode\s+nocturne|nocturnes?|en\s+nocturne|\bLn\b\s+la\s+nuit)"
# Un Lden « sur 24 h » occupe la colonne de gauche (indice global), signalé par la métrique.
_DAY24 = r"(?:Lden[^.]{0,8}(?:sur\s*)?24\s*h|(?:sur\s*)?24\s*h[^.]{0,8}Lden)"

_POINTS = (
    r"en\s+limites?\s+(?:est|ouest|nord|sud|nord-est|nord-ouest|sud-est|sud-ouest)?\s*de\s+(?:propriété|projet|site)",
    r"au\s+point\s+le\s+plus\s+exposé",
    r"(?:au\s+)?point\s+n[°ºo]\s*\d+",
    r"à\s+proximité\s+du?\s+(?:lycée|collège|école|groupe\s+scolaire|hôpital|crèche)[\w’' -]*",
    r"au\s+niveau\s+des\s+habitations",
    r"au\s+voisinage",
    r"zones?\s+à\s+émergence\s+réglementée|\bZER\b",
)
_METRICS = ((r"\bLden\b", "Lden"), (r"\bL\s*Aeq\b|\bLaeq\b", "LAeq"), (r"\bLn\b", "Ln"))
# Une valeur NORMATIVE (seuil OMS, valeur maximale recommandée, objectif de santé) n'est pas
# une mesure du site : la rapporter comme telle peindrait une cible en constat. On ne garde
# que ce que l'avis mesure ou calcule, pas ce qu'une autorité recommande ailleurs.
_NORM = re.compile(
    r"\bOMS\b|organisation\s+mondiale|\bseuils?\b|effet\s+néfaste|pouvant\s+déclencher|"
    r"valeurs?\s+maximales?\s+(?:définies?|recommandées?)|valeur\s+cible", re.I)


def _num(s: str) -> float:
    return float(s.replace("+", "").replace(" ", "").replace(" ", "").replace(",", "."))


def _band_at(seg: str, marker: str):
    """La bande (plage ou valeur) rattachée à une période, dans les deux ordres rencontrés.

    Renvoie (bande_dict, match) ou (None, None). `match` sert à neutraliser la portion déjà
    consommée avant de chercher la période suivante — c'est ce qui évite d'apparier la valeur
    de jour avec le marqueur de nuit dans « …est de 60,5 dB(A) et 54,5 en période nocturne ».
    """
    # 1) PLAGE, valeurs AVANT le marqueur : « entre 62,5 et 65 dB(A) de jour » (« et » nu admis
    #    car le jour est apparié en premier puis neutralisé, cf. _parse).
    m = re.search(rf"{_SEP}({_NUM})\s*(?:{_DBA})?\s*{_RANGE}\s*({_NUM})\s*(?:{_DBA})?[^.]{{0,20}}?{marker}",
                  seg, re.I)
    if m:
        return {"min": _num(m.group(1)), "max": _num(m.group(2))}, m
    # 2) PLAGE APRÈS le marqueur : « de jour est compris entre 43 et 44,5 dB(A) ». On EXIGE
    #    « entre » : sans lui, « est de 60,5 dB(A) et 54,5 en période nocturne » apparierait à
    #    tort la valeur de jour (60,5) avec celle de nuit (54,5).
    m = re.search(rf"{marker}[^.]{{0,30}}?(?:compris\s+)?entre\s+({_NUM})\s*(?:{_DBA})?\s*(?:et|à)\s*({_NUM})",
                  seg, re.I)
    if m:
        return {"min": _num(m.group(1)), "max": _num(m.group(2))}, m
    # 3) VALEUR simple AVANT le marqueur : « 61,9 dB(A) le jour », « 54,5 en période nocturne »
    m = re.search(rf"({_NUM})\s*(?:{_DBA})?[^.]{{0,14}}?{marker}", seg, re.I)
    if m:
        return {"valeur": _num(m.group(1))}, m
    # 4) VALEUR simple APRÈS le marqueur : « le niveau de jour … est de 60,5 dB(A) »
    m = re.search(rf"{marker}[^.]{{0,30}}?(?:est\s+de|de|:|à)\s*({_NUM})\s*{_DBA}", seg, re.I)
    if m:
        return {"valeur": _num(m.group(1))}, m
    return None, None


def _blank(seg: str, m) -> str:
    return seg[:m.start()] + " " * (m.end() - m.start()) + seg[m.end():] if m else seg


def _metric_near(seg: str, m) -> str | None:
    if not m:
        return None
    window = seg[max(0, m.start() - 10): m.end() + 12]
    for pat, name in _METRICS:
        if re.search(pat, window, re.I):
            return name
    return None


def _point(seg: str) -> str | None:
    for pat in _POINTS:
        m = re.search(pat, seg, re.I)
        if m:
            return re.sub(r"\s+", " ", m.group(0)).strip()
    return None


def _metric_label(day_metric: str | None, night_metric: str | None) -> str | None:
    if day_metric and night_metric and day_metric != night_metric:
        return f"{day_metric}/{night_metric}"
    return day_metric or night_metric


def _segments(sentence: str) -> list[str]:
    # « … la nuit CONTRE … au niveau des habitations » = deux points dans une phrase.
    return [s for s in re.split(r"\bcontre\b", sentence, flags=re.I) if s.strip()]


def _parse(sentence: str, emergence: bool) -> list[dict]:
    out: list[dict] = []
    for seg in _segments(sentence):
        if not re.search(_DBA, seg, re.I):
            continue  # sans dB(A), les nombres sont des horaires (« 22 h – 7h »), pas du bruit
        if _NORM.search(seg):
            continue  # cible normative (OMS, seuil), pas une mesure du site
        # « émergence(s) » SAUF « émergence réglementée » (qui nomme une ZONE, la ZER).
        emg_value = re.search(r"émergences?(?!\s+réglementées?)", seg, re.I) is not None
        if emergence and not emg_value:
            continue
        if not emergence and emg_value:
            continue  # une valeur d'émergence ne va pas dans le champ des niveaux

        day_marker = f"(?:{_DAY}|{_DAY24})" if not emergence else _DAY
        day, dm = _band_at(seg, day_marker)
        night, nm = _band_at(_blank(seg, dm), _NIGHT)
        if not day and not night:
            continue
        rec: dict = {"point": _point(seg)}
        metric = _metric_label(_metric_near(seg, dm), _metric_near(seg, nm))
        if metric:
            rec["metrique"] = metric
        if day:
            rec["jour"] = day
        if night:
            rec["nuit"] = night
        if emergence:
            seuil = re.search(rf"seuil[^.]{{0,30}}?({_NUM})\s*dB|limite\s+réglementaire[^.]{{0,20}}?({_NUM})\s*dB",
                              seg, re.I)
            if seuil:
                rec["seuil_cite"] = _num(next(g for g in seuil.groups() if g))
        out.append(rec)
    return out


def parse_levels(sentence: str) -> list[dict]:
    """Bandes de NIVEAU sonore (jour/nuit), une par point de mesure."""
    return _parse(sentence, emergence=False)


def parse_emergences(sentence: str) -> list[dict]:
    """Bandes d'ÉMERGENCE (jour/nuit). Le seuil n'est rapporté que s'il est cité ; jamais de
    calcul de conformité."""
    return _parse(sentence, emergence=True)
