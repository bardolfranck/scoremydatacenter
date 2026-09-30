# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""La source NATIONALE : le site des MRAe, quand la région ne publie pas de registre WFS.

Quatre régions sur dix-huit exposent leur registre en service WFS (`index.py`). Pour les
quatorze autres, la chaîne registre → PDF n'existe pas. Le site national des MRAe, lui,
publie les avis de TOUTES les régions et sa recherche rend des liens DIRECTS vers les PDF :
212 résultats pour « data center » contre 22 dossiers dans les quatre registres outillés.

CE QUE CETTE SOURCE N'EST PAS. Ce n'est pas un registre : pas de géométrie, pas d'INSEE,
pas de pétitionnaire, pas de statut de procédure — donc pas de bloc `procedure` complet et
pas de rattachement géographique possible. C'est un INDEX DOCUMENTAIRE. On l'utilise pour
atteindre des avis qu'aucun registre n'indexe, en sachant qu'on perd l'acte administratif
et qu'on ne garde que le document. Les deux sources ne sont donc pas interchangeables et le
champ `origine` le dit dans chaque fiche produite.

Et c'est un moteur de recherche plein texte : il rend aussi des documents qui PARLENT des
data centers sans en être l'avis (la synthèse « La ruée vers les data centers », un cahier
d'éclairages, un glossaire où « data-center » n'apparaît qu'en note de bas de page). Le tri
fin est fait ici et reste explicite — un document écarté doit pouvoir être expliqué.
"""

from __future__ import annotations

import html
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

BASE = "https://www.mrae.developpement-durable.gouv.fr/spip.php"
UA = "ScoreMyDataCenter/1.0 (+https://scoremydatacenter.org)"
TIMEOUT = 120

CARD = re.compile(r"recherche-card__title[^>]*><a href='([^']+)'[^>]*title='([^']*)'", re.S)
DATE = re.compile(r"<time datetime='(\d{4}-\d{2}-\d{2})'")

# Un avis de projet, par opposition à une publication qui PARLE des data centers.
IS_AVIS = re.compile(r"avis|d[ée]lib[ée]r|projet|cas[\s_-]par[\s_-]cas", re.I)
NOT_AVIS = re.compile(
    r"ru[ée]e\s+vers|[ée]clairage|synth[èe]se\s+annuelle|glossaire|rapport\s+d['’]activit[ée]|"
    r"conf[ée]rence|note\s+de\s+doctrine|plaquette", re.I)


@dataclass
class Document:
    titre: str
    doc_url: str
    date: str = ""
    origine: str = "site MRAe (index documentaire national)"

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v}


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace")


def _page(query: str, start: int) -> str:
    q = urllib.parse.urlencode({
        "page": "recherche", "recherche": query, "tri": "score_desc",
        "f_date": 0, "typedoc": 0, "perimetre": "site", "r_start": start, "f_net": 0,
    })
    return _get(f"{BASE}?{q}")


DC_MENTION = re.compile(r"data[\s\-]*cent|centre[s]?\s+de\s+donn[ée]es|h[ée]bergement\s+de\s+donn[ée]es", re.I)


def confirms_datacenter(pages: list[str], head: int = 2, minimum: int = 2) -> bool:
    """Le document a-t-il un data center pour SUJET, ou le mentionne-t-il en passant ?

    Le tri par titre ne suffit pas, et c'est mesuré : sur douze documents tirés au hasard
    parmi les 117 que rend la recherche nationale, QUATRE seulement sont des avis de data
    center. Les autres sont un projet portuaire, un modèle de courrier, un projet
    stratégique — des documents où « data center » apparaît une fois, parfois en note.
    Les titres n'aident pas : le site en publie sous « MRAe Île-de-France », « Avis de la
    MRAe », voire « GOUVERNEMENT » (qui, lui, EST un avis de data center).

    D'où ce test sur les DEUX PREMIÈRES PAGES — l'objet du document y est toujours énoncé.
    Compter les mentions sur tout le document ne discrimine pas : un avis portuaire en a
    six, un vrai avis de data center en a parfois trois.
    """
    return len(DC_MENTION.findall(" ".join(pages[:head]))) >= minimum


def search(query: str = "data center", max_pages: int = 25, pause: float = 0.4) -> list[Document]:
    """Les avis PDF que la recherche nationale rend pour `query`, dédupliqués par URL.

    S'arrête dès qu'une page ne rend plus rien de neuf : le moteur boucle sur la dernière
    page plutôt que de rendre une page vide, donc compter les pages ne suffit pas à savoir
    qu'on est au bout.
    """
    out: dict[str, Document] = {}
    for start in range(max_pages):
        try:
            t = _page(query, start)
        except Exception:  # noqa: BLE001
            break
        cards = CARD.findall(t)
        if not cards:
            break
        dates = DATE.findall(t)
        before = len(out)
        for i, (url, title) in enumerate(cards):
            url = html.unescape(url)
            title = html.unescape(re.sub(r"\s*-\s*document t[ée]l[ée]chargeable$", "", title)).strip()
            if "/IMG/pdf" not in url or url in out:
                continue
            if NOT_AVIS.search(title) or not IS_AVIS.search(title + " " + url):
                continue
            out[url] = Document(titre=title, doc_url=url,
                                date=dates[i] if i < len(dates) else "")
        if len(out) == before:
            break
        time.sleep(pause)
    return list(out.values())
