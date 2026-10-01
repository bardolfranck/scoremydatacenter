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


# Un PROCÈS-VERBAL de séance n'est pas un avis : il liste les dossiers examinés, donc il
# parle de data centers sans en être l'évaluation. Il a franchi `confirms_datacenter` pour
# cette raison exacte — son ordre du jour citait Argenteuil, Rungis et Bonneuil. Trouvé par
# l'étalon au deuxième document annoté. Même famille que « parler de » ≠ « porter sur ».
# Seules les tournures qui NOMMENT LA NATURE du document. Un premier jet ajoutait
# « ordre du jour » et « membres présents » : les deux figurent dans de vrais avis délibérés
# (« inscrit à l'ordre du jour de la séance du… »), et le filtre rejetait Les Ulis et
# Saint-Priest. Un garde-fou qui écarte ce qu'il doit protéger est pire que pas de garde-fou.
NOT_AN_OPINION = re.compile(
    r"proc[èe]s[\s-]*verbal|compte[\s-]*rendu\s+de\s+(?:séance|réunion)|"
    r"relevé\s+de\s+décisions", re.I)

DC_MENTION = re.compile(r"data[\s\-]*cent|centre[s]?\s+de\s+donn[ée]es|h[ée]bergement\s+de\s+donn[ée]es", re.I)

# Le même avis se cherche sous six noms. « data center » seul rend 117 candidats ; l'union des
# six en rend 391. Ce n'est pas un raffinement : c'est le tiers du gisement qui manquait.
QUERIES = ("data center", "centre de données", "datacenter",
           "centre de donnees informatiques", "hébergement de données", "data-center")

# La région n'est PAS dans l'index : ni dans l'URL, ni dans le titre. Elle est en revanche
# toujours dans l'en-tête de l'avis, qui nomme la MRAe qui l'a délibéré. Sans cette lecture,
# « le Grand Est n'a rien » reste une présomption tirée de noms de fichiers.
REGIONS_FR = (
    "Île-de-France", "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne",
    "Centre-Val de Loire", "Corse", "Grand Est", "Hauts-de-France", "Normandie",
    "Nouvelle-Aquitaine", "Occitanie", "Pays de la Loire",
    "Provence-Alpes-Côte d'Azur", "Guadeloupe", "Guyane", "Martinique",
    "La Réunion", "Mayotte",
)


def _region_pattern(name: str) -> re.Pattern:
    """Tolère les variantes de césure et d'apostrophe des PDF — mais PAS la casse.

    « La Réunion » est un nom propre ; « la réunion » est un nom commun. Un motif
    insensible à la casse a classé un procès-verbal francilien en région Réunion parce
    qu'il mentionnait « la réunion publique du projet de data center d'Argenteuil ».
    La casse est ici porteuse de sens, pas de style — mais seulement par son ABSENCE de
    majuscule : les en-têtes PACA écrivent « PROVENCE-ALPES-CÔTE D'AZUR » tout en capitales,
    et exiger la casse canonique perdait la région entière. On accepte donc toute casse au
    motif, et c'est `_is_proper_noun` qui écarte la forme intégralement minuscule.
    """
    body = re.escape(name)
    body = body.replace("Île", "[IÎ]le").replace("é", "[ée]").replace("è", "[èe]")
    body = body.replace("\\'", "['’]").replace("\\-", "[\\s\\-]")
    return re.compile(body.replace("\\ ", r"[\s\-]+"), re.I)


_REGION_PATTERNS = tuple((n, _region_pattern(n)) for n in REGIONS_FR)


# L'autorité se nomme : « MRAe Île-de-France », « mission régionale d'autorité
# environnementale de Normandie ». On cherche D'ABORD un nom de région accolé à cette
# formule — c'est l'émetteur — avant de se rabattre sur une mention isolée, qui peut être
# n'importe quoi : le lieu d'un autre projet, une citation, un nom commun homonyme.
_ISSUER = re.compile(r"(?:MRAe|mission\s+régionale\s+d['’]autorité\s+environnementale)"
                     r"[\s,]*(?:de\s+la\s+|de\s+|d['’]|du\s+)?", re.I)


def _is_proper_noun(matched: str) -> bool:
    """« La Réunion » oui, « LA RÉUNION » oui, « la réunion » non."""
    return matched != matched.lower()


def region_of(pages: list[str], head: int = 2) -> str | None:
    """La région qui a délibéré l'avis, lue dans son en-tête. None si elle n'y figure pas."""
    txt = " ".join(pages[:head])
    # 1) la région accolée au nom de l'autorité émettrice — la seule qui fasse foi
    for m in _ISSUER.finditer(txt):
        suite = txt[m.end():m.end() + 40]
        for name, pat in _REGION_PATTERNS:
            m2 = pat.match(suite)
            if m2 and _is_proper_noun(m2.group(0)):
                return name
    # 2) à défaut, une mention isolée, sensible à la casse
    for name, pat in _REGION_PATTERNS:
        m = pat.search(txt)
        if m and _is_proper_noun(m.group(0)):
            return name
    return None


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
    tete = " ".join(pages[:head])
    if NOT_AN_OPINION.search(tete):
        return False
    return len(DC_MENTION.findall(tete)) >= minimum


RESULT_COUNT = re.compile(r"(\d+)\s+r[ée]sultats?")


class SearchUnavailable(RuntimeError):
    """La recherche a répondu, mais elle n'a pas cherché."""


def search(query: str = "data center", max_pages: int = 25, pause: float = 1.5) -> list[Document]:
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
            # ZÉRO CARTE N'EST PAS ZÉRO RÉSULTAT. Après quelques centaines de requêtes, ce
            # service rend une page de recherche parfaitement valide — même gabarit, HTTP 200,
            # 27 ko — mais SANS le compteur « N résultats » et sans aucune carte. Un appelant
            # naïf conclut « ce terme ne donne rien » et, pire, « cette région n'a pas d'avis ».
            # C'est exactement le faux silencieux qu'on traque partout ailleurs, subi cette
            # fois de l'autre côté. Distinguer les deux cas est la seule façon de ne pas
            # publier une absence qui n'existe pas.
            if start == 0 and not RESULT_COUNT.search(t):
                raise SearchUnavailable(
                    f"la recherche MRAe a répondu sans compteur de résultats ni carte pour "
                    f"{query!r} : service indisponible ou requêtes limitées, PAS une absence "
                    f"de résultats. Réessayer plus tard, plus lentement.")
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
