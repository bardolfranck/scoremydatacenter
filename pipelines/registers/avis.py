# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""L'AVIS : un PDF d'autorité environnementale → des faits, chacun avec sa phrase et sa page.

Deuxième maillon de la chaîne registre → PDF → JSON. Le premier (`index.py`) donne le lien ;
celui-ci lit le document et en sort ce qui est relevable.

TROIS RÈGLES, toutes payées par une erreur réelle.

1. ON NE CHERCHE PAS UN NOMBRE SUIVI D'UNE UNITÉ, ON CHERCHE LA PHRASE QUI AFFIRME LE FAIT.
   Un motif « nombre + MW » a capté « 1 000 MW » comme puissance d'Aulnay : c'était la ligne
   de GLOSSAIRE définissant le gigawattheure. Chaque champ porte donc un ANCRE — le contexte
   qui fait de la phrase une affirmation — en plus du motif de valeur.

2. CHAQUE VALEUR VOYAGE AVEC SA PHRASE ET SON NUMÉRO DE PAGE. C'est ce qui fait la valeur du
   produit (un chiffre vérifiable en un clic) ET ce qui permet de repérer un glossaire capté
   par erreur. Un champ sans phrase ne sort pas.

3. PAS D'OCR. Testé sur 7 avis 2023–2025, Île-de-France et PACA : 7/7 ont une couche texte
   (27 000 à 110 000 caractères) — ce sont des exports bureautiques, pas des scans. Un
   document sans couche texte est SIGNALÉ, jamais océrisé : une erreur de chiffre sur une
   fiche publique coûte plus cher que ce document ne rapporte.

Et une limite mesurée, à ne pas oublier en lisant une sortie vide : LA PROFONDEUR VARIE PAR
RÉGION, pas le format. Un avis d'Île-de-France fait 20 à 35 pages et dit tout ; un avis PACA
fait 11 pages et ne parle NI de bruit, NI de groupes, NI de cuves. Un champ absent décrit
l'avis, pas l'installation.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
import urllib.request
from dataclasses import dataclass, field
from io import BytesIO

from . import bruit

UA = "ScoreMyDataCenter/1.0 (+https://scoremydatacenter.org)"
TIMEOUT = 180

# Nombre à la française : « 9 781 », « 1 000 » (espace fine insécable comprise), « 7,5 ».
NUM = r"\d[\d   ]*(?:[.,]\d+)?"
# Ces PDF sont des exports bureautiques : l'exposant se perd. « 9 781 m2 » et « 120 m3 » sont
# la règle, pas l'exception — un motif qui n'accepte que m²/m³ rate la moitié des surfaces.
M2, M3 = r"m²|m2", r"m³|m3"
# Un effectif ou un nombre d'équipements s'écrit AUSSI en toutes lettres (« Douze cuves
# enterrées de 120 m3 chacune » : le seul chiffre de la phrase est le volume, pas le compte).
WORDS = {"une": 1, "un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
         "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "treize": 13, "quatorze": 14,
         "quinze": 15, "seize": 16, "vingt": 20, "trente": 30, "quarante": 40, "cinquante": 50,
         "soixante": 60, "cent": 100}
WORD_RE = "|".join(sorted(WORDS, key=len, reverse=True))
# Une ligne de sommaire (« … ............ 12 ») ou de glossaire (« MWh : unité de … ») n'affirme rien.
TOC = re.compile(r"\.{4,}|…{2,}")
GLOSSARY = re.compile(r"^\s*[A-Za-zÉé/³²\s\-]{1,28}\s*:\s*(?:unité|symbole|équivaut|correspond à|soit\s+\d)", re.I)
# Abréviations suivies d'un nombre : « p. 171 », « n° 2 », « art. 3 ». Leur point n'est
# pas une fin de phrase.
ABBREV_DOT = re.compile(r"\b(?:pp?|nn?o?|art|cf|fig|al|r[ée]f|vol|chap|tab)\.(?=\s*\d)", re.I)
DEFINES_UNIT = re.compile(r"(?:un|une|le|la)\s+(?:mégawatt|gigawatt|kilowatt|wattheure|décibel)", re.I)

# Une phrase qui chiffre L'ENSEMBLE d'un site, et non la tranche objet de l'avis, ne décrit
# pas l'installation examinée. Mesuré à l'échelle (Marcoussis, extension du data center 4) :
# « …vingt-trois data centers AU TOTAL seront en capacité de fonctionner sur LE SITE QUI
# COMPRENDRA 151 groupes électrogènes et 87 cuves… » — 151 et 87 sont les totaux des 23 DC,
# pas de l'extension. On ne répartit pas au prorata (on ne devine pas) : le compte reste vide,
# et c'est honnête. Garde-fou réservé aux COMPTES (groupes, cuves), où la confusion mord.
AGGREGAT_SITE = (r"(?:data\s*centers?|centres?\s+de\s+données)\s+au\s+total|"
                 r"le\s+site\s+qui\s+comprendra|l['’]ensemble\s+du\s+site|\bà\s+terme\b")

# Une ligne de NOMENCLATURE ICPE énonce des SEUILS, jamais une mesure du projet. Elle fuit des
# chiffres dans tout champ numérique dont l'ancre y apparaît : « …surface… SUPÉRIEURE À 1 HA mais
# INFÉRIEURE À 20 HA » (parcelle, Meudon) ; « …puissance… ÉGALE OU SUPÉRIEURE À 50 MW 6
# Prélèvement d'eau… » (eau, nomenclature). Un seuil réglementaire n'est pas une mesure (classe A).
ICPE_SEUIL = (r"\brubrique\b|nomenclature|"
              r"supérieure?\s+à[^.]{0,70}inférieure?\s+à|"
              r"égale?\s+ou\s+supérieure?\s+à")

# Un PROJET MIXTE inclut, OUTRE le data center, un PROGRAMME bâti distinct (logements, crèche,
# commerces, aqualudique, co-living). Ses chiffres de programme (80 000 m² de logements, « 8 000
# emplois ») ne sont PAS ceux du data center. On ne démêle pas fiche par fiche (faux-ami) : on DRAPE
# la fiche pour que l'étage d'après lise ces chiffres avec prudence. Signal d'INCLUSION au PROJET
# (« construction de N logements », « co-living »), pas de VOISINAGE (« habitations à 200 m »).
# Mesuré sur l'étalon : Courbevoie 62 occ., Bruges 38, Rungis 2 ; les 10 autres 0, dont
# Saint-Priest (habitations proches mais 0 programme) — voisins ≠ programme. On rapporte ces
# occurrences et les signaux captés ; on ne gradue pas (pas de seuil « léger/lourd » défendable).
MIXED_PROGRAM = re.compile(
    r"village\s+delage|aqualudique|co-?living|résidences?-services?|"
    r"projets?\s+(?:mixtes?|urbains?)|programme\s+(?:mixte|urbain)|"
    r"\d[\d   ]*\s*(?:m2|m²)?\s*(?:de\s+)?logements|logements\s+(?:familiaux|sociaux)|"
    r"crèche\s+de\b|gymnase\b|groupe\s+scolaire\s+de\b", re.I)

# PLUSIEURS INSTALLATIONS dans un même avis (campus). Compté à partir des FAITS, pas de mots-clés :
# les mots-clés sur-déclenchent (« deux data centers » dans une comparaison de voisinage ; « DC1 »
# pris dans le nom de société PIPA-DC1). Le signal fiable est le CONTENU extrait — plusieurs
# puissances IT distinctes = plusieurs bâtiments (Nozay 75/37,5/15) — complété par les étiquettes
# de bâtiment DC01/DC02/DC03 (zéro de tête = convention de bâtiment, écarte « PIPA-DC1 »).
# On ne compte JAMAIS par somme : on énumère des installations, on n'additionne pas des valeurs.
DC_LABEL = re.compile(r"\bDC0(\d)\b")

# PÉTITIONNAIRE (maître d'ouvrage) depuis le PDF. 23 avis sur 39 viennent de l'index national qui
# ne le publie pas, et c'est là que le détecteur de projets est aveugle. Le nom est en tête d'avis,
# dans des tournures stables. On capte le nom APRÈS la tournure (« maître d'ouvrage … est X »,
# « porté/présenté/déposé par X ») ; jamais le repli « la société X » nu, qui attrape un financier
# ou un foncier (BNP Paribas) au lieu du data center. NAME est CASSE-SENSIBLE (vraies majuscules) :
# sinon on avale « situé », « est », « le »… et on confond le boilerplate avec le nom. Mesuré sur
# les 39 : 21 pétitionnaires, zéro faux visible (lead-only).
_PET_PREFIX = (r"(?:la\s+soci[ée]t[ée]\s+|la\s+(?:SAS|SASU|SNC|SCI|SCCV|SA|SARL|holding)\s+|"
               r"l['’]entreprise\s+|l['’][ée]tablissement\s+public\s+territorial\s+)?")
_PET_LEAD = (r"ma[îi]tre\s+d['’]ouvrage[^.]{0,40}?est\s+" + _PET_PREFIX + r"|"
             r"port[ée]e?\s+par\s+" + _PET_PREFIX + r"|"
             r"présent[ée]e?\s+par\s+" + _PET_PREFIX + r"|"
             r"déposée?\s+par\s+" + _PET_PREFIX + r"|"
             r"pétitionnaire[^.]{0,8}?(?:est|:)\s+" + _PET_PREFIX + r"|"
             r"demande\s+[^.]{0,40}?présentée\s+par\s+" + _PET_PREFIX)
_PET_NAME = r"([A-ZÉÈÀ0-9][\w&'’\-]*(?:\s+[A-ZÉÈÀ0-9][\w&'’\-]*){0,5})"
_PET_STOP = (r"(?=\s*(?:,|\.|;|\(|:|\bsur\b|\bà\b|\bsitu[ée]|\bdont\b|\bpour\b|\bqui\b|\ba\s+déposé|"
             r"\brepr[ée]sent|\bau\s+titre|\ben\s+vue|\bsollicit|\bconsiste|\bse\s+situe|"
             r"\bs['’]implante|\brelati|\best\b|\bafin\b|['’]|$))")
# LEAD insensible à la casse (?i:…), NAME/STOP sensibles. LEAD groupé pour que NAME lie TOUTES
# les branches (sinon, précédence du « | » : NAME ne s'applique qu'à la dernière).
_PET_RE = re.compile(r"(?i:" + _PET_LEAD + r")" + _PET_NAME + _PET_STOP)


def petitionnaire_from_pages(pages: list[str], head: int = 3) -> str | None:
    """Le maître d'ouvrage, lu dans les premières pages de l'avis. None si aucune tournure claire
    ne le nomme (on DÉCLARE l'absence plutôt que de deviner un tiers)."""
    txt = re.sub(r"\s+", " ", _norm(" ".join(pages[:head])))
    m = _PET_RE.search(txt)
    if m and m.group(1) and m.group(1).strip(" .,;"):
        return m.group(1).strip(" .,;")
    return None


def _n(s: str) -> float:
    key = s.strip().lower()
    if key in WORDS:
        return float(WORDS[key])
    return float(re.sub(r"[   ]", "", s).replace(",", "."))


# Certains exports PDF remplacent les ESPACES par des caractères de largeur nulle. Le texte
# paraît normal à l'œil et devient du charabia pour une machine : les mots sont soudés, toutes
# les ancres meurent, et le document rend quelques faits au lieu de quarante — SANS LE MOINDRE
# SIGNAL. C'est le faux silence dans sa forme la plus pure.
#
# Mesuré sur l'avis de Bonneuil (34 pages) : 2,9 % d'espaces contre 13,9 à 14,6 % sur les
# treize autres avis de l'étalon, et 57 516 caractères invisibles. Une fois remplacés par des
# espaces, la densité revient à 14,1 % — exactement la plage saine — et le document rend
# 40 faits et 16 recommandations au lieu de dix.
#
# On RÉPARE donc avant de juger. Signaler le document comme illisible, c'était jeter quarante
# faits justes à cause d'un défaut d'export. Le signalement garde son rôle, mais en dernier
# recours, pour ce qui résiste à la réparation.
ZERO_WIDTH = re.compile("[\u200b\u200c\u200d\u2060\ufeff]+")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = ZERO_WIDTH.sub(" ", s)
    return re.sub(r"[ \t ]+", " ", s)


@dataclass(frozen=True)
class Field:
    """Un champ relevable. `anchor` est ce qui fait de la phrase une AFFIRMATION."""

    id: str
    label: str
    theme: str
    unit: str | None
    anchor: str                 # doit matcher la phrase
    value: str | None = None    # capture la valeur ; None => champ textuel (présence/qualification)
    kind: str = "number"        # number | text | enum | list
    choices: tuple[tuple[str, str], ...] = ()   # enum : (motif, valeur)
    multiple: bool = False      # list : toutes les occurrences
    # Ce qui DISQUALIFIE la phrase même si l'ancre matche. Deux cas rencontrés :
    #   · « le PUE moyen des centres de données EN FRANCE est de 1,6 » — une référence
    #     nationale rappelée par l'autorité, pas la valeur du projet ;
    #   · « puissance totale installée de 405 MW » dans la phrase des GROUPES — c'est la
    #     puissance du secours, pas celle du site.
    # Sans ce garde-fou, les deux sortaient en tant que fait du projet.
    reject: str | None = None
    as_text: bool = False       # number : rendre la valeur en chaîne (rubrique ICPE, pas un flottant)
    # Bornes de PLAUSIBILITÉ physique. Elles n'existent que parce que le passage à l'échelle
    # les a rendues nécessaires : sur 49 avis, une « cuve » de 120 000 m³ (c'était un volume
    # de terrassement) et un « niveau sonore » de 2,5 dB(A) (c'était une émergence) sont
    # sortis sans que rien ne les arrête. Une valeur hors bornes est ÉCARTÉE, pas corrigée :
    # on ne devine pas ce que l'avis voulait dire.
    bounds: tuple[float, float] | None = None
    # Certains faits ne sont pas scalaires : le bruit s'exprime en BANDES (point × période ×
    # plage), et sortir les dB(A) à plat perd l'appariement. Un `parser(phrase) -> list[dict]`
    # produit alors des valeurs STRUCTURÉES (une par point de mesure), chacune gardant sa phrase.
    parser: object = None


# ─────────────────────────────────────────────────────────────────────────────────────────
# LA LISTE. Volontairement la plus large que les documents supportent — y compris ce que
# notre grille ne note PAS (bruit, groupes, cuves, emplois, GES, fluides), parce que c'est
# précisément le centre de gravité de ces avis et la matière de la feature nuisances.
# ─────────────────────────────────────────────────────────────────────────────────────────
FIELDS: tuple[Field, ...] = (
    # ── Énergie ──────────────────────────────────────────────────────────────────────────
    # `multiple` : un CAMPUS porte plusieurs installations (Nozay : DC01 75, DC02 37,5, DC03 15 MW IT).
    # Ce ne sont pas plusieurs valeurs d'un champ mais plusieurs bâtiments — chacun garde sa phrase
    # (qui nomme le bâtiment), comme les GES poste par poste. On ne somme JAMAIS : on ne sait pas si
    # les tranches sont simultanées ni si la dernière est encore au projet.
    Field("puissance_it_mw", "Puissance des salles informatiques", "energie", "MW",
          r"salles?\s+informatiques?.{0,80}puissance|puissance\s+(?:prévue|informatique|des\s+salles)",
          rf"puissance[^.]{{0,60}}?({NUM})\s*MW", multiple=True, bounds=(0.1, 2000.0)),
    # `puissance_site_mw` : RETIRÉ puis ROUVERT. Je l'avais supprimé sur un 0/43, en concluant
    # que « la notion n'existe pas dans ces avis ». C'était déduire une absence d'un silence —
    # la quatrième fois cette semaine, et cette fois contre moi-même. L'étalon l'a démenti au
    # DEUXIÈME document annoté : l'avis Interxion MRS4 écrit « la puissance électrique appelée
    # (80 MW) ». La notion existe, c'est notre motif qui ne la voyait pas.
    #
    # « Appelée » est le terme technique : la puissance que le site tire du réseau, distincte
    # de la puissance des salles informatiques et de celle des groupes de secours. Le rejet sur
    # les groupes reste, sans quoi 405 MW de secours entreraient ici.
    Field("puissance_site_mw", "Puissance électrique appelée du site", "energie", "MW",
          r"puissance\s+(?:électrique\s+)?(?:appelée|souscrite|totale\s+du\s+site|raccordée)",
          rf"(?:appelée|souscrite|raccordée|totale\s+du\s+site)[^.]{{0,20}}?\(?({NUM})\)?\s*MW",
          reject=r"groupes?\s+électrogènes?|secours", bounds=(0.1, 2000.0)),
    Field("consommation_gwh_an", "Consommation électrique annuelle", "energie", "GWh/an",
          r"consommation\s+(?:électrique|annuelle|d['’]électricité|énergétique)",
          rf"({NUM})\s*GWh"),
    # Photovoltaïque sur site. L'étalon le montre 5 fois, mais SANS unité commune : 646 panneaux
    # (Tremblay), 153 et 580 MWh/an (Saint-Priest, Bonneuil), 3 000 m² (Rungis), 581 kWc. Forcer
    # une unique unité trahirait ; « mentionné » n'est pas un fait (règle du chef). On capte donc
    # la VALEUR telle que déclarée, avec son unité, en texte — le chiffre voyage, la phrase tranche.
    Field("photovoltaique", "Photovoltaïque sur site (valeur déclarée)", "energie", None,
          r"photovolta[ïi]que|panneaux?\s+(?:solaires?|photovolta[ïi]ques?)|\bPV\b",
          rf"({NUM}\s*(?:panneaux|kWc|MWc|MWh(?:\s*/\s*an|\s+(?:annuels?|par\s+an))?|m2|m²|GWh))",
          multiple=True, as_text=True),
    # Le PUE se déclare en DEUX temps dans ces avis, et l'ordre compte. Spécification la plus
    # précise d'abord : le MOTEUR s'arrête au premier spec qui capte un champ donné pour une
    # phrase, donc déclarer deux fois `pue` du plus spécifique au plus général donne une
    # priorité, sans machinerie supplémentaire.
    #
    # 1) La phrase qui OPPOSE une référence nationale à la valeur du projet :
    #    « le PUE moyen des centres de données en France est de 1,6 … et celui ATTENDU pour le
    #    projet est ESTIMÉ à 1,3 ». Mon premier correctif rejetait la phrase ENTIÈRE sur
    #    « PUE moyen » — il écartait la moyenne nationale ET le 1,3 du projet avec elle.
    #    Faux négatif que je m'étais fabriqué en corrigeant un faux positif ; relevé par une
    #    extraction indépendante sur le même avis (Tremblay, 2026-10-01).
    Field("pue", "PUE annoncé pour le projet", "energie", None,
          r"\bPUE\b",
          rf"(?:attendue?|estimée?|visée?|annoncée?|cible)[^.]{{0,40}}?({NUM})",
          reject=r"ne\s+saurait|proche\s+de|plus\s+l['’]\s*indice|d['’]autant\s+plus"),
    # 2) La phrase simple, sans opposition : « le PUE est passé de 1,8 en 2018 à 1,67 ».
    #    Ici on refuse en revanche la tournure de référence nationale, qui donnerait 1,6.
    Field("pue", "PUE annoncé pour le projet", "energie", None,
          r"\bPUE\b",
          rf"PUE[^.]{{0,40}}?(?:de|:)\s*({NUM})",
          # « Plus l'indice PUE est PROCHE DE 1 et plus la performance… » est la DÉFINITION du
          # PUE, pas la valeur du projet — elle sortait « pue=1 » (Bailly-Romainvilliers).
          reject=r"PUE\s+moyen|en\s+France\s+est|ne\s+saurait|rappelle|"
                 r"proche\s+de|plus\s+l['’]\s*indice|d['’]autant\s+plus"),
    Field("raccordement_kv", "Tension de raccordement", "energie", "kV",
          r"raccordement|liaison\s+électrique|poste\s+source|réseau\s+de\s+transport",
          rf"({NUM})\s*(?:000\s*V|kV)"),

    # ── Le « caché » : secours au fioul ───────────────────────────────────────────────────
    Field("groupes_nombre", "Groupes électrogènes (nombre)", "secours", "groupes",
          r"groupes?\s+électrogènes?",
          rf"(?:au\s+nombre\s+de\s+({NUM})|({NUM}|{WORD_RE})\s+groupes?\s+électrogènes?)",
          reject=AGGREGAT_SITE, bounds=(1.0, 400.0)),
    Field("groupes_puissance_unitaire_mw", "Puissance unitaire d'un groupe", "secours", "MW",
          r"groupes?\s+électrogènes?[^.]{0,80}puissance\s+unitaire|puissance\s+unitaire[^.]{0,60}groupe",
          rf"unitaire\s+de\s+({NUM})\s*MW"),
    Field("groupes_puissance_totale_mw", "Puissance installée des groupes", "secours", "MW",
          r"puissance\s+totale\s+installée|puissance\s+(?:cumulée|installée)\s+des\s+groupes",
          rf"(?:totale\s+installée|cumulée|installée\s+des\s+groupes)\s+de\s+({NUM})\s*MW"),
    # Puissance THERMIQUE de combustion (rubrique ICPE 3110). L'étalon la montre 4 fois (59,29 /
    # 103,18 / 160 / 547 MWth). Grandeur DISTINCTE de la puissance ÉLECTRIQUE des groupes : c'est
    # le classement ICPE de l'installation de combustion. L'unité « MWth / MW thermiques » est dans
    # le motif de valeur, donc une puissance électrique en MW ne peut PAS y entrer.
    Field("puissance_thermique_combustion_mwth", "Puissance thermique de combustion (ICPE 3110)",
          "secours", "MWth",
          r"puissance\s+thermique(?:\s+(?:nominale|de\s+(?:combustion|production)))?",
          # Deux écritures : « …thermique nominale atteindra 59,29 MW » (MW nu, « thermique » avant)
          # et « 547 MWth ». On prend le 1er nombre qui suit « thermique », ou la forme MWth explicite.
          rf"thermique[^.]{{0,45}}?({NUM})\s*MW|({NUM})\s*MW\s*(?:th\b|thermiques?)",
          # « …égale ou supérieure à 50 MW » est le SEUIL de la rubrique 3110, pas la puissance réelle.
          # On rejette la seule tournure de SEUIL — pas « rubrique » nu, car la vraie valeur (« 160
          # MWth ») est souvent énoncée dans la MÊME phrase que « rubrique 3110 ».
          reject=r"(?:égale?\s+ou\s+)?sup[ée]rieure?\s+à|inf[ée]rieure?\s+à",
          bounds=(1.0, 2000.0)),
    Field("groupes_carburant", "Carburant des groupes", "secours", None,
          r"groupes?\s+électrogènes?[^.]{0,120}(?:aliment|fonctionn)|carburant",
          kind="enum",
          choices=((r"huile\s+végétale\s+hydrotraitée|HVO", "huile végétale hydrotraitée (HVO)"),
                   (r"fioul\s+domestique", "fioul domestique"),
                   (r"gazole\s+non\s+routier|GNR", "gazole non routier"),
                   (r"\bgazole\b|\bfioul\b", "fioul/gazole"))),
    # `multiple` : campus / split enterrées vs aériennes vs par bâtiment (Nozay 28 ent. + 87 aér. ;
    # Normandie ND1 6×100 + ND2 8×80). Chaque occurrence garde sa phrase ; jamais de somme.
    Field("cuves_nombre", "Cuves de carburant (nombre)", "secours", "cuves",
          r"cuves?[^.]{0,80}(?:stocker|carburant|fioul|gazole|enterrées?|aériennes?)",
          rf"({NUM}|{WORD_RE})\s+cuves?", reject=AGGREGAT_SITE, multiple=True, bounds=(1.0, 400.0)),
    Field("cuves_volume_unitaire_m3", "Volume unitaire d'une cuve", "secours", "m³",
          r"cuves?[^.]{0,60}(?:de|chacune)",
          rf"({NUM})\s*(?:{M3})\s*chacune|cuves?\s+(?:enterrées?\s+|aériennes?\s+)?de\s+({NUM})\s*(?:{M3})",
          multiple=True, bounds=(1.0, 2000.0)),
    Field("cuves_volume_total_m3", "Volume total de carburant stocké", "secours", "m³",
          r"volume\s+total|capacité\s+(?:totale\s+)?de\s+stockage|stockage\s+total",
          rf"({NUM})\s*(?:{M3})",
          # « Le volume total des eaux traitées par infiltration sera de 220 m3 » (Rungis) : un
          # volume d'EAUX PLUVIALES capté comme volume de fioul — l'ancre « volume total » ne
          # dit pas de QUOI. On exclut le contexte hydraulique ; bon nombre, mauvais objet.
          reject=r"eaux?\s+pluviales?|infiltr|pluies?|rétention|bassin|assainissement",
          multiple=True, bounds=(1.0, 50000.0)),
    Field("cuves_enterrees", "Cuves enterrées", "secours", None,
          r"cuves?\s+enterrées?", kind="text"),
    Field("autonomie_heures", "Autonomie en secours", "secours", "h",
          r"autonomie|fonctionnement\s+pendant|assurer\s+le\s+fonctionnement",
          rf"pendant\s+({NUM})\s*(?:heures?|h\b)|autonomie[^.]{{0,40}}?({NUM})\s*(?:heures?|h\b)", bounds=(1.0, 720.0)),
    Field("essais_groupes", "Essais périodiques des groupes", "secours", None,
          r"essais?[^.]{0,60}groupes?\s+électrogènes?|groupes?[^.]{0,60}essais?\s+(?:périodiques|mensuels|de\s+maintenance)",
          kind="text"),

    # ── Bruit : sujet n°1 de l'État dans ces avis, zéro indicateur chez nous ──────────────
    # STRUCTURÉ, pour la publication : point de mesure × période (jour/nuit) × plage ou valeur.
    # C'est ce qui rend le bloc bruit lisible (« en limite est : 62,5–65 le jour, 59,5–62 la
    # nuit ») là où les dB(A) à plat ne disaient rien. Deux grandeurs SÉPARÉES — niveau ambiant
    # (surtout l'environnement) et émergence (le seul chiffre qui parle du data center) :
    Field("bruit_bandes", "Bruit par point et période", "bruit", None,
          r"dB\s*\(?\s*A\)?", parser=bruit.parse_levels),
    Field("bruit_emergence_bandes", "Émergence par période", "bruit", None,
          r"émergences?", parser=bruit.parse_emergences),
    # Couche BRUTE conservée (jamais publiée telle quelle : un niveau sans sa période ni son
    # point n'apprend rien) — tous les niveaux relevés, CHACUN AVEC SA PHRASE : c'est la phrase
    # qui dit s'il s'agit
    # du jour ou de la nuit, d'un point de mesure ou d'une limite de propriété, d'une valeur
    # ferme ou d'une borne de fourchette. Réduire ce champ à un scalaire produit des demi-
    # vérités — « 62 dB(A) la nuit » alors que l'avis écrit « entre 59,5 et 62 dB(A) ».
    Field("bruit_niveau_dba", "Niveaux sonores relevés", "bruit", "dB(A)",
          r"niveaux?\s+(?:sonores?|acoustiques?|de\s+bruit)|bruit\s+(?:ambiant|résiduel)|émergence|\bLAeq\b",
          rf"({NUM})\s*dB\s*\(?A\)?", multiple=True, bounds=(25.0, 120.0)),
    # `bruit_nuit_dba` (scalaire) RETIRÉ : remplacé par `bruit_bandes` ci-dessous, qui garde
    # l'appariement jour/nuit. Une valeur présente à deux endroits finit par diverger.
    # L'ÉMERGENCE n'est pas un niveau sonore : c'est l'écart entre le bruit avec et sans
    # l'installation (3 à 6 dB(A) selon l'heure). Mélangée aux niveaux, elle tirait la série
    # vers un « minimum » de 2,5 dB(A) qui ne veut rien dire. Champ distinct, borné en écart.
    Field("bruit_emergence_dba", "Émergence sonore", "bruit", "dB(A)",
          r"émergence",
          rf"émergence[^.]{{0,60}}?({NUM})\s*dB|({NUM})\s*dB[^.]{{0,40}}?d['’]émergence",
          bounds=(0.5, 15.0)),
    Field("bruit_emergence", "Émergence réglementaire (mention)", "bruit", None,
          r"émergence", kind="text"),
    Field("bruit_point_mesure", "Points de mesure du bruit", "bruit", None,
          r"point\s+de\s+mesure|points?\s+de\s+mesures?\s+(?:situés?|placés?)", kind="text"),
    Field("bruit_zer", "Zones à émergence réglementée", "bruit", None,
          r"zones?\s+à\s+émergence\s+réglementée|\bZER\b", kind="text"),

    # ── Chaleur fatale (notre E6/E7, ici en toutes lettres) ───────────────────────────────
    Field("chaleur_fatale_mw_th", "Chaleur fatale produite", "chaleur", "MW thermiques",
          r"chaleur\s+fatale",
          rf"({NUM})\s*MW\s*(?:thermiques?|th\b)"),
    Field("chaleur_valorisation", "Valorisation de la chaleur", "chaleur", None,
          r"chaleur\s+fatale|récupération\s+de\s+(?:la\s+)?chaleur|réseau\s+de\s+chaleur",
          kind="enum",
          # « étude » ne peut PAS s'attraper par le mot « étude » : « étude d'impact » est dans
          # chaque avis, et le champ sortait « étude » sur 35 fiches sur 35 — une uniformité qui
          # n'était pas un résultat mais un faux. On exige une tournure qui porte sur la CHALEUR.
          choices=((r"contrat|convention\s+(?:signée|de\s+raccordement)|raccordé[e]?\s+au\s+réseau\s+de\s+chaleur", "contrat/raccordement"),
                   (r"(?:à\s+l['’]étude|envisagée?|potentielle?|projet\s+de\s+valorisation|"
                    r"étude\s+de\s+(?:faisabilité|valorisation|raccordement))", "étude"),
                   (r"n['’]est\s+pas\s+(?:prévue|envisagée|valorisée)|aucune\s+valorisation|"
                    r"pas\s+de\s+(?:valorisation|récupération)", "aucune"))),
    Field("reseau_chaleur_distance", "Distance au réseau de chaleur", "chaleur", "m",
          r"réseau\s+de\s+chaleur[^.]{0,80}(?:distance|situé|éloigné|à)",
          rf"({NUM})\s*(?:m|mètres|km)\b"),

    # ── Eau ──────────────────────────────────────────────────────────────────────────────
    Field("eau_m3_an", "Consommation d'eau annuelle", "eau", "m³/an",
          r"consommation\s+d['’]eau|besoins?\s+en\s+eau|prélèvement[^.]{0,40}eau",
          rf"({NUM})\s*(?:{M3})",
          # Trois objets qui ne sont PAS une conso annuelle : l'eau d'EXTINCTION incendie, donnée
          # en m³/HEURE (« 60 m3/heure », Ferrières ; « 180 m3/h », Val-de-Reuil) ; l'eau de PHASE
          # TRAVAUX, one-shot de chantier (« 4 220 m3 pour la phase travaux », Saint-Priest) ; et un
          # SEUIL de nomenclature ICPE (« …supérieure à 50 MW 6 Prélèvement d'eau… »). Objet/unité faux.
          reject=r"extinction|incendie|phase\s+(?:de\s+)?travaux|chantier|"
                 r"m3\s*/\s*(?:heure|h)|m³\s*/\s*(?:heure|h)|/\s*heure|" + ICPE_SEUIL),
    Field("refroidissement_type", "Mode de refroidissement", "eau", None,
          r"refroidissement|free[- ]cooling|adiabatique",
          kind="enum",
          choices=((r"adiabatique", "adiabatique (consommateur d'eau)"),
                   (r"free[- ]cooling|air\s+extérieur", "free-cooling / air"),
                   (r"circuit\s+fermé|boucle\s+fermée", "circuit fermé"))),
    Field("rejets_aqueux", "Rejets aqueux", "eau", None,
          r"rejets?\s+(?:aqueux|d['’]eaux\s+(?:usées|industrielles))", kind="text"),
    Field("eaux_pluviales", "Gestion des eaux pluviales", "eau", None,
          r"eaux\s+pluviales", kind="text"),

    # ── Emprise et sols ──────────────────────────────────────────────────────────────────
    Field("parcelle_ha", "Superficie de la parcelle", "foncier", "ha",
          r"parcelle|terrain\s+d['’]assiette|s['’]implante\s+sur|superficie",
          rf"({NUM})\s*(?:hectares?|ha)\b",
          # « …rubrique 2.1.5.0 … la surface totale du projet … supérieure à 1 ha mais inférieure
          # à 20 ha » (Meudon) : le « 1 ha » est le SEUIL de la nomenclature ICPE, pas la parcelle.
          reject=ICPE_SEUIL, bounds=(0.01, 1000.0)),
    # « Les salles informatiques représentent 9 781 m2 d'emprise au sol » n'est PAS l'emprise
    # au sol du projet : c'est celle d'un local. Sans ce rejet, les deux champs sortaient la
    # même valeur et l'un des deux mentait.
    Field("emprise_sol_m2", "Emprise au sol du projet", "foncier", "m²",
          r"emprise\s+au\s+sol",
          rf"({NUM})\s*(?:{M2})",
          reject=r"salles?\s+informatiques?|locaux\s+techniques"),
    Field("surface_plancher_m2", "Surface de plancher", "foncier", "m²",
          r"surface\s+de\s+plancher",
          rf"({NUM})\s*(?:{M2})"),
    # `multiple` : surfaces de salles par bâtiment sur un campus (Nozay DC01/02/03). Chacune sa phrase.
    Field("surface_salles_m2", "Surface des salles informatiques", "foncier", "m²",
          r"salles?\s+informatiques?[^.]{0,80}(?:emprise|surface|représentent)",
          rf"salles?\s+informatiques?\s+(?:représentent|occupent)?\s*({NUM})\s*(?:{M2})", multiple=True),
    Field("surface_locaux_techniques_m2", "Surface des locaux techniques", "foncier", "m²",
          r"locaux\s+techniques",
          rf"locaux\s+techniques\s*({NUM})\s*(?:{M2})"),
    Field("hauteur_m", "Hauteur des bâtiments", "foncier", "m",
          r"hauteur[^.]{0,60}(?:bâtiments?|construction)",
          rf"({NUM})\s*(?:m|mètres)\b",
          # « un écran acoustique d'une hauteur de 5 mètres en toiture du bâtiment » (Les Ulis) :
          # l'ancre voit « hauteur … bâtiment » mais l'objet mesuré est l'ÉCRAN, pas le bâtiment.
          reject=r"écran\s+acoustique|merlon|clôture|portail|mur\s+(?:anti|acoustique)"),
    Field("artificialisation", "Artificialisation / imperméabilisation", "foncier", None,
          r"imperméabilis|artificialis|\bZAN\b|zéro\s+artificialisation", kind="text"),

    # ── Climat, air, fluides ─────────────────────────────────────────────────────────────
    # Ces avis chiffrent les GES POSTE PAR POSTE (construction, électricité, poids lourds,
    # véhicules des salariés). On les relève TOUS avec leur phrase : c'est la phrase qui dit
    # de quel poste il s'agit, et agréger à l'aveugle produirait un total qui n'existe pas.
    Field("ges_teqco2", "Émissions de gaz à effet de serre (par poste)", "climat", "t eq. CO2",
          r"gaz\s+à\s+effet\s+de\s+serre|\bGES\b|empreinte\s+carbone|"
          r"émissions?[^.]{0,40}CO\s*2|t\s*eq\.?\s*CO\s*2",
          rf"({NUM})\s*(?:t|tonnes?)\s*(?:eq\.?\s*CO\s*2|CO\s*2\s*eq)", multiple=True),
    # DEUX champs, pas un (correctif chef). 27 avis discutent des frigorigènes, 11 seulement en
    # nomment un : garder la PRÉSENCE À CÔTÉ du nom permet de distinguer « discuté mais non nommé »
    # (not_disclosed — lacune de l'exploitant, une information) de « pas abordé du tout ». Remplacer
    # la présence par le nom effacerait cette distinction, celle-là même qu'on passe la semaine à
    # défendre. (« Mentionné n'est pas un fait » était une règle d'AFFICHAGE, pas de stockage.)
    Field("fluides_frigorigenes", "Fluides frigorigènes (présence)", "climat", None,
          r"fluides?\s+frigorig[èe]nes?|frigorig[èe]nes?", kind="text"),
    # Le NOM du fluide quand l'avis le donne (R134a, R-1234ze, propane). Ancré sur une phrase
    # frigorigène ; « R. 122-7 » (article de code, avec point) n'y entre pas — les frigorigènes
    # s'écrivent sans point (« R134a »). `multiple` : un avis peut en nommer plusieurs.
    Field("fluide_frigorigene_nom", "Fluide frigorigène (désignation)", "climat", None,
          r"frigorig[èe]nes?|frigorifiques?",
          r"(\bR-?\d{2,4}[a-zA-Z]{0,2}\b|\bpropane\b|\bammoniac\b|\bNH3\b)",
          multiple=True, as_text=True),
    # Ce champ est une MASSE de frigorigène (tonnes/kg), PAS un équivalent carbone. « …les fuites
    # de fluide frigorigène à hauteur d'environ 500 t eq. » (Aulnay) donnait « 500 t » de
    # frigorigène, alors que « t eq. » = tonnes équivalent CO2. On REJETTE la forme équivalent-CO2
    # ici (classe D, confusion d'unité) ; on ne la route PAS d'office vers `ges_teqco2` — déplacer
    # une valeur parce qu'on croit avoir compris, c'est de l'interprétation, et on est en extraction.
    Field("fuites_frigorigenes_t", "Fuites de fluide frigorigène", "climat", "t",
          r"fuites?\s+de\s+fluides?\s+frigorigènes?",
          rf"({NUM})\s*(?:tonnes?|t|kg)\b(?!\s*(?:eq|éq))",
          reject=r"t\s*eq|éq|équivalent\s*CO|eq\.?\s*CO"),
    Field("nox", "Oxydes d'azote / polluants atmosphériques", "air", None,
          r"\bNOx\b|oxydes\s+d['’]azote|polluants\s+atmosphériques", kind="text"),
    Field("qualite_air_campagne", "Campagne de mesure de la qualité de l'air", "air", None,
          r"campagne\s+de\s+(?:prélèvements?|mesures?)[^.]{0,60}(?:air|qualité)", kind="text"),

    # ── Voisinage : ce que l'élu regarde en premier ───────────────────────────────────────
    Field("habitations_distance_m", "Distance aux premières habitations", "voisinage", "m",
          r"habitations?\s+les\s+plus\s+proches|premières?\s+habitations?|zone\s+résidentielle[^.]{0,40}proche",
          rf"({NUM}|{WORD_RE})\s*(?:m\b|mètres?|km)", bounds=(1.0, 20000.0)),
    # La distance à une école ou un lycée est le fait le plus parlant de ces avis pour un élu,
    # et elle s'écrit souvent EN TOUTES LETTRES : « un établissement scolaire est situé à
    # QUINZE MÈTRES de l'installation » (Tremblay, p.21). Un motif qui n'accepte que les
    # chiffres le perd — on avait réglé ce piège pour les cuves, jamais pour les distances.
    Field("etablissement_sensible_distance_m", "Distance au premier établissement sensible",
          "voisinage", "m",
          r"(?:établissement\s+scolaire|école|lycée|collège|crèche|hôpital)[^.]{0,80}"
          r"(?:situé|implanté|se\s+trouve|à)|"
          r"(?:situé|implanté)[^.]{0,40}(?:de|du)\s+(?:l['’]établissement|l['’]école|lycée)",
          rf"({NUM}|{WORD_RE})\s*(?:m\b|mètres?)", bounds=(1.0, 20000.0)),
    Field("etablissements_sensibles", "Établissements sensibles à proximité", "voisinage", None,
          r"école|crèche|hôpital|collège|lycée|EHPAD|établissements?\s+sensibles?", kind="text"),
    Field("trafic_pl", "Trafic poids lourds", "voisinage", None,
          r"poids\s+lourds|trafic[^.]{0,60}(?:véhicules|camions)", kind="text"),

    # ── Biodiversité ─────────────────────────────────────────────────────────────────────
    Field("natura2000", "Natura 2000 / ZNIEFF", "biodiversite", None,
          r"Natura\s*2000|ZNIEFF|zone\s+de\s+protection\s+spéciale", kind="text"),
    Field("zones_humides", "Zones humides", "biodiversite", None, r"zones?\s+humides?", kind="text"),
    Field("especes_protegees", "Espèces protégées / dérogation", "biodiversite", None,
          r"espèces?\s+protégées?|dérogation\s+espèces", kind="text"),

    # ── Sols, risques, procédure ─────────────────────────────────────────────────────────
    Field("pollution_sols", "Pollution des sols / site industriel antérieur", "sols", None,
          r"pollution\s+des\s+sols|sols\s+pollués|ancienne\s+(?:usine|installation)|friche", kind="text"),
    Field("pfas", "PFAS / contaminants émergents", "sols", None,
          r"\bPFAS\b|perfluor|polyfluor|contaminants?\s+émergents?", kind="text"),
    Field("icpe_rubriques", "Rubriques ICPE", "procedure", None,
          r"rubriques?\s+\d{4}|installations?\s+classées",
          r"rubriques?\s+(\d{4})", multiple=True, as_text=True),
    Field("incendie", "Risque incendie / moyens de défense", "risques", None,
          r"incendie|défense\s+extérieure\s+contre\s+l['’]incendie|\bDECI\b", kind="text"),

    # ── Emploi : l'axe contestataire que ces avis traitent très peu — c'est un constat ────
    # Le chiffre, quand il existe, est noyé dans une phrase d'exploitation (« l'effectif sur
    # site sera d'environ 300 personnes », « le scénario majorant est d'environ 90 personnes »).
    # Son ABSENCE est elle-même une information : l'État n'interroge presque jamais l'emploi
    # dans ces avis, alors que c'est un argument central du débat public.
    Field("emplois_effectif", "Effectif sur site annoncé", "emploi", "personnes",
          r"effectif\s+sur\s+site|emplois?\s+(?:créés?|directs?|attendus?)|"
          r"(?:environ|estimé à)\s+\d[\d  ]*\s*(?:personnes|salariés|emplois|ETP)",
          rf"({NUM})\s*(?:personnes|salariés|emplois|ETP)",
          # « …200 000 m2 d'activités (environ 8 000 emplois)… » (Village Delage, Courbevoie) :
          # les 8 000 emplois sont ceux d'un PROJET URBAIN MIXTE (logements + équipements +
          # activités), pas du data center. On ne tranche pas la part du DC — champ vide (classe C).
          reject=r"logements?|parc\s+urbain|équipements?\s+publics?|programme\s+mixte|groupe\s+scolaire",
          bounds=(1.0, 20000.0)),
    # « emploi » au sens juridique — « fabrication, EMPLOI ou stockage de gaz fluorés » — n'a
    # rien à voir avec l'emploi salarié. Le motif nu remontait des nomenclatures ICPE.
    Field("emplois_mention", "Mention de l'emploi", "emploi", None,
          r"emplois?\s+(?:créés?|directs?|indirects?|locaux|attendus?|permanents?)|"
          r"créations?\s+d['’]emplois?|effectif\s+sur\s+site|salariés?|\bETP\b", kind="text",
          reject=r"emploi\s+ou\s+stockage|fabrication,?\s+emploi"),
)

_FIELDS_BY_ID = {f.id: f for f in FIELDS}


def rejection_reason(field_id: str, value, sentence: str) -> str | None:
    """Pour la REVALIDATION d'un fait DÉJÀ stocké : la règle courante le REJETTE-t-elle ?

    Renvoie un motif si le fait est POSITIVEMENT rejeté (champ retiré du schéma, motif de rejet
    qui matche la phrase, ou valeur hors borne), sinon None (= on le garde).

    Cette fonction ne dit JAMAIS « non reproduit ». Un rejeu qui ne retrouve pas un fait est un
    SILENCE, pas une preuve — comme « zéro résultat » sur la recherche MRAe n'est pas « aucun
    avis ». On ne retire que ce qu'une règle rejette explicitement ; un fait dont la phrase ne
    déclenche aucun rejet reste en place, même si on ne le régénère pas à l'identique.
    """
    spec = _FIELDS_BY_ID.get(field_id)
    if spec is None:
        return "champ retiré du schéma"
    if spec.reject:
        m = re.search(spec.reject, sentence, re.I)
        if m:
            frag = re.sub(r"\s+", " ", m.group(0)).strip()
            return f"rejet sur « {frag[:40]} »"
    if spec.bounds and isinstance(value, (int, float)) and not isinstance(value, bool):
        lo, hi = spec.bounds
        if not (lo <= value <= hi):
            return f"hors borne [{lo:g}, {hi:g}]"
    return None

# La formule change de région en région : « L'Autorité environnementale recommande »,
# « La MRAe recommande », « l'Ae recommande ». Un motif calé sur la seule tournure
# francilienne rendait ZÉRO recommandation en PACA et en Normandie — et zéro se lit comme
# « l'autorité n'a rien à redire », ce qui est le contraire de la vérité.
RECO = re.compile(
    r"(?:L['’]\s*Autorité\s+environnementale|La\s+MRAe|L['’]\s*(?:Ae|MRAe)|"
    r"La\s+mission\s+régionale\s+d['’]autorité\s+environnementale)\s+recommande[^.]{10,400}\.",
    re.I)
# Beaucoup d'avis NUMÉROTENT leurs recommandations : « (15) L'Autorité environnementale
# recommande : - d'examiner… - de modéliser… ». Ces formes-là sont des LISTES, souvent
# longues, et le motif en prose les ratait : il exigeait un point final dans les 400
# caractères, que la liste n'atteint qu'au bout de mille. Résultat mesuré sur Tremblay :
# 17 captées sur 23, et les six manquantes étaient les plus substantielles — bruit simultané
# des 54 groupes, dispersion atmosphérique, bilan GES diffus.
#
# Quand la numérotation existe, elle est le meilleur délimiteur possible : chaque
# recommandation court jusqu'à la suivante. On l'utilise d'abord, et on garde le motif en
# prose pour les avis qui ne numérotent pas.
NUMBERED_RECO = re.compile(
    r"\((\d{1,2})\)\s*(?:L['’]\s*Autorité\s+environnementale|La\s+MRAe|L['’]\s*Ae)\s+recommande",
    re.I)

TYPOGRAPHIC_RECO = re.compile(
    r"recommandations\s+sont\s+portées\s+en\s+(?:italique|gras)|"
    r"recommandations\s+(?:figurent|apparaissent)\s+en\s+(?:italique|gras)", re.I)


# Libellés ANGLAIS. Ce sont du CONTENU (ils disent ce que le champ MESURE), pas du vocabulaire de
# schéma — ils vivent donc ici, près des FIELDS, et non dans la couche de traduction (schema_en).
# Rédigés pour dire la mesure, pas traduits mot à mot. Un fait sort `libelle: {fr, en}` (bilingue),
# et la frontière `to_english` ne fait que renommer la clé. Test : un id sans libellé EN échoue.
LABELS_EN: dict[str, str] = {
    "puissance_it_mw": "Data hall (IT) power", "puissance_site_mw": "Reported site power demand",
    "consommation_gwh_an": "Annual electricity consumption",
    "photovoltaique": "On-site photovoltaics (as reported)", "pue": "Announced PUE",
    "raccordement_kv": "Grid connection voltage", "groupes_nombre": "Backup generators (count)",
    "groupes_puissance_unitaire_mw": "Backup generator unit power",
    "groupes_puissance_totale_mw": "Backup generators installed power",
    "puissance_thermique_combustion_mwth": "Combustion thermal power (ICPE 3110)",
    "groupes_carburant": "Backup generator fuel", "cuves_nombre": "Fuel tanks (count)",
    "cuves_volume_unitaire_m3": "Fuel tank unit volume",
    "cuves_volume_total_m3": "Total fuel storage volume", "cuves_enterrees": "Buried fuel tanks",
    "autonomie_heures": "Backup autonomy", "essais_groupes": "Periodic generator testing",
    "bruit_bandes": "Noise levels by point and period",
    "bruit_emergence_bandes": "Noise emergence by period", "bruit_niveau_dba": "Measured noise levels",
    "bruit_emergence_dba": "Noise emergence", "bruit_emergence": "Regulatory noise emergence (mention)",
    "bruit_point_mesure": "Noise measurement points", "bruit_zer": "Noise-regulated zones (ZER)",
    "chaleur_fatale_mw_th": "Waste heat produced", "chaleur_valorisation": "Waste heat recovery",
    "reseau_chaleur_distance": "Distance to district heating network",
    "eau_m3_an": "Annual water consumption", "refroidissement_type": "Cooling technology",
    "rejets_aqueux": "Aqueous discharges", "eaux_pluviales": "Stormwater management",
    "parcelle_ha": "Plot area", "emprise_sol_m2": "Building footprint",
    "surface_plancher_m2": "Gross floor area", "surface_salles_m2": "Data hall area",
    "surface_locaux_techniques_m2": "Technical rooms area", "hauteur_m": "Building height",
    "artificialisation": "Land take / soil sealing",
    "ges_teqco2": "Greenhouse-gas emissions (per source)",
    "fluides_frigorigenes": "Refrigerants (presence)", "fluide_frigorigene_nom": "Refrigerant (designation)",
    "fuites_frigorigenes_t": "Refrigerant leakage", "nox": "Nitrogen oxides / air pollutants",
    "qualite_air_campagne": "Air-quality measurement campaign",
    "habitations_distance_m": "Distance to nearest dwellings",
    "etablissement_sensible_distance_m": "Distance to nearest sensitive site",
    "etablissements_sensibles": "Sensitive sites nearby", "trafic_pl": "Heavy-goods-vehicle traffic",
    "natura2000": "Natura 2000 / ZNIEFF", "zones_humides": "Wetlands",
    "especes_protegees": "Protected species / derogation",
    "pollution_sols": "Soil contamination / former industrial site",
    "pfas": "PFAS / emerging contaminants", "icpe_rubriques": "ICPE categories",
    "incendie": "Fire risk / defence measures", "emplois_effectif": "Reported on-site headcount",
    "emplois_mention": "Employment (mention)",
}


@dataclass
class Fact:
    field_id: str
    label: str
    theme: str
    value: object
    unit: str | None
    sentence: str
    page: int

    def as_dict(self) -> dict:
        # `libelle` est bilingue (contenu) : {fr, en}. La frontière ne fait que renommer la clé.
        d = {"indicateur": self.field_id,
             "libelle": {"fr": self.label, "en": LABELS_EN.get(self.field_id, self.label)},
             "theme": self.theme,
             "valeur": self.value, "phrase": self.sentence, "page": self.page}
        if self.unit:
            d["unite"] = self.unit
        return d


@dataclass
class Avis:
    doc_url: str
    n_pages: int = 0
    n_chars: int = 0
    sha256: str = ""
    has_text_layer: bool = True
    facts: list[Fact] = field(default_factory=list)
    recommandations: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # Drapeau PROJET MIXTE : {"occurrences": n, "signaux": [...]} quand l'avis couvre un programme
    # bâti au-delà du data center (voir MIXED_PROGRAM). None sinon. Le drapeau porte ses PREUVES —
    # pas de niveau « léger/lourd » : on ne saurait défendre un seuil entre 2 et 38, on montre les
    # tournures et le lecteur juge (même doctrine que « la phrase, pas la qualification »).
    projet_mixte: dict | None = None
    # Drapeau PLUSIEURS INSTALLATIONS : un entier (nombre de data centers décrits) quand l'avis le
    # donne, True si le pluriel est là sans compte. L'avis décrit N installations, pas une — cela
    # change la lecture de TOUS les chiffres, pas seulement ceux du programme.
    plusieurs_installations: object = None
    # Maître d'ouvrage lu dans le PDF (procédure, pas installation). Rempli surtout pour les avis
    # de l'index national qui ne le publient pas au registre. None si non nommé clairement.
    petitionnaire: str | None = None

    def as_dict(self) -> dict:
        by_theme: dict[str, list[dict]] = {}
        for f in self.facts:
            by_theme.setdefault(f.theme, []).append(f.as_dict())
        out = {
            # `sha256` identifie le DOCUMENT, pas son adresse : le même avis est servi par le
            # registre régional et par le site national sous deux URL différentes, et sans
            # cette empreinte le jeu contenait deux fiches pour un seul avis.
            "source": {"doc_url": self.doc_url, "pages": self.n_pages,
                       "caracteres": self.n_chars, "sha256": self.sha256,
                       "couche_texte": self.has_text_layer, "ocr": False},
            "faits": by_theme,
            "recommandations_autorite": self.recommandations,
            "avertissements": self.warnings,
        }
        if self.projet_mixte:
            # Drapeau de NATURE : lire les chiffres de programme (logements, emplois) avec prudence,
            # ils ne sont pas ceux du data center. On ne les retire pas ici — on prévient.
            out["projet_mixte"] = self.projet_mixte
        if self.plusieurs_installations:
            out["plusieurs_installations"] = self.plusieurs_installations
        return out


def pages_of(pdf: bytes) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf))
    return [_norm(p.extract_text() or "") for p in reader.pages]


def _sentences(page_text: str) -> list[str]:
    flat = re.sub(r"\s*\n\s*", " ", page_text)
    # la césure de fin de ligne recolle les mots coupés (« réglemen- tée »)
    flat = re.sub(r"(\w)-\s+(\w)", r"\1\2", flat)
    # Le point d'une ABRÉVIATION n'est pas une fin de phrase. Couper sur tout point suivi
    # d'une espace tranchait les renvois internes : « …est de 1,6 (p. 171) et que celui
    # attendu pour le projet est estimé à 1,3 » devenait deux morceaux, dont le second ne
    # contenait plus le mot « PUE ». L'ancre ne matchait donc plus et la valeur du projet
    # était perdue — un faux négatif invisible, puisqu'un champ vide ne proteste pas.
    # Révélé en comparant notre extraction à une lecture indépendante du même avis.
    #
    # On neutralise ces points-là le temps du découpage, puis on les restaure : la phrase
    # stockée reste EXACTEMENT celle du document, puisque c'est elle qui fait preuve.
    # (Première tentative : ne couper que devant une majuscule. Elle réparait ce cas mais
    # fusionnait trop ailleurs, et les phrases trop longues tombaient sous la limite de
    # taille — La Courneuve y perdait cinq champs. Un correctif doit se mesurer, pas se
    # supposer.)
    masked = ABBREV_DOT.sub(lambda m: m.group(0).replace(".", "\x00"), flat)
    parts = [p.replace("\x00", ".") for p in re.split(r"(?<=[.;:])\s+", masked)]
    return [s.strip() for s in parts if 25 <= len(s.strip()) <= 420]


def _asserts(sentence: str) -> bool:
    """Une phrase de sommaire ou de glossaire n'affirme rien — c'est le piège d'Aulnay."""
    return not (TOC.search(sentence) or GLOSSARY.match(sentence) or DEFINES_UNIT.search(sentence))


def extract(pdf: bytes, doc_url: str) -> Avis:
    return extract_from_pages(pages_of(pdf), doc_url, sha256=hashlib.sha256(pdf).hexdigest())


def extract_from_pages(pages: list[str], doc_url: str, sha256: str = "") -> Avis:
    """Variante pour les appelants qui ont DÉJÀ les pages.

    La source nationale doit lire les deux premières pages pour savoir si le document a bien
    un data center pour sujet, avant de décider de l'extraire. Sans cette entrée, il faudrait
    analyser le PDF deux fois — et sur 117 documents, ce genre de gaspillage finit par être
    « optimisé » en sautant la vérification.
    """
    # La réparation des caractères de largeur nulle vit dans `_norm`, qui n'est appliqué que
    # par `pages_of`. Un appelant qui fournit ses propres pages — la source nationale, un test,
    # un futur lot — recevrait du texte non réparé et perdrait les trois quarts de ses faits
    # en silence. On répare donc ICI aussi : c'est le point d'entrée unique de l'extraction,
    # et `_norm` est idempotent.
    pages = [_norm(p) for p in pages]
    avis = Avis(doc_url=doc_url, n_pages=len(pages), n_chars=sum(len(p) for p in pages), sha256=sha256)
    if avis.n_chars < 500 * max(1, len(pages)) // 10:
        avis.has_text_layer = False
        avis.warnings.append(
            "couche texte absente ou trop maigre — document SIGNALÉ, pas océrisé "
            "(une erreur de chiffre sur une fiche publique coûte plus que ce document ne rapporte)")
        return avis

    # Couche texte PRÉSENTE mais POLLUÉE. Certains PDF remplacent les espaces par des caractères
    # de jointure INVISIBLES (U+200D/200B/200C) : les mots se soudent, les ancres meurent, et
    # l'extraction rend une poignée de faits SANS AUCUN SIGNAL — « 33 pages, 10 faits » (Bonneuil),
    # qu'on prendrait pour une installation sobre. Un fait manquant ne proteste pas ; ici c'est tout
    # le document qui disparaît en silence. On le SIGNALE comme un scan (hors du taux), on ne l'extrait
    # pas. Seuils calibrés sur l'étalon : avis sains = 13,9–14,6 % d'espaces, 0 % de jointures ;
    # Bonneuil = 2,9 % d'espaces, 39 % de jointures. Le plancher 8 % garde 6 points de marge.
    full = "".join(pages)
    zwj = full.count("‍") + full.count("​") + full.count("‌")
    spaces = sum(1 for c in full if c in " \t ")
    space_ratio = spaces / len(full) if full else 0.0
    if len(full) >= 2000 and (space_ratio < 0.08 or zwj / len(full) > 0.02):
        avis.has_text_layer = False
        avis.warnings.append(
            f"couche texte POLLUÉE (densité d'espaces {space_ratio:.1%} contre ~14 % attendus, "
            f"{zwj} caractères de jointure invisibles) — mots soudés, ancres inopérantes : "
            "extraction NON FIABLE, document SIGNALÉ et non extrait (à sortir du taux, comme un scan)")
        return avis

    # PROJET MIXTE : l'avis couvre un programme bâti au-delà du data center → on DRAPE la fiche avec
    # ses PREUVES (tournures captées, dédupliquées en retirant les chiffres, + nombre d'occurrences).
    # Pas de niveau inventé : le lecteur juge sur les signaux. On ne retire aucun fait, on prévient.
    mixed = MIXED_PROGRAM.findall(full)
    if mixed:
        signaux = sorted({re.sub(r"[\d   ]+", " ", m).strip().lower() for m in mixed})
        avis.projet_mixte = {"occurrences": len(mixed), "signaux": signaux}

    avis.petitionnaire = petitionnaire_from_pages(pages)

    seen: set[str] = set()
    for pno, text in enumerate(pages, start=1):
        for s in _sentences(text):
            if not _asserts(s):
                continue
            for spec in FIELDS:
                if not re.search(spec.anchor, s, re.I):
                    continue
                if spec.reject and re.search(spec.reject, s, re.I):
                    continue
                if spec.parser is not None:
                    # Faits STRUCTURÉS (bandes de bruit) : une valeur-dict par point de mesure.
                    for band in spec.parser(s):
                        key = f"{spec.id}:{band}"
                        if key in seen:
                            continue
                        seen.add(key)
                        avis.facts.append(Fact(spec.id, spec.label, spec.theme, band, None, s, pno))
                    continue
                if spec.kind == "text":
                    key = f"{spec.id}:{pno}"
                    if spec.id in seen or key in seen:
                        continue
                    seen.add(spec.id)
                    avis.facts.append(Fact(spec.id, spec.label, spec.theme, True, None, s, pno))
                elif spec.kind == "enum":
                    if spec.id in seen:
                        continue
                    for pat, val in spec.choices:
                        if re.search(pat, s, re.I):
                            seen.add(spec.id)
                            avis.facts.append(Fact(spec.id, spec.label, spec.theme, val, None, s, pno))
                            break
                else:
                    # `multiple` relève TOUTES les occurrences de la phrase (les GES sont
                    # donnés poste par poste, les rubriques ICPE viennent par grappes) ;
                    # sinon la première affirmation rencontrée fait foi.
                    matches = list(re.finditer(spec.value, s, re.I)) if spec.multiple \
                        else [m for m in [re.search(spec.value, s, re.I)] if m]
                    for m in matches:
                        raw = next((g for g in m.groups() if g), None)
                        if raw is None:
                            continue
                        if spec.as_text:
                            val = raw.strip()
                        else:
                            try:
                                val = _n(raw)
                            except ValueError:
                                continue
                            if spec.bounds and not (spec.bounds[0] <= val <= spec.bounds[1]):
                                continue  # hors plausibilité physique : écartée, jamais corrigée
                        key = f"{spec.id}={val}" if spec.multiple else spec.id
                        if key in seen:
                            continue
                        seen.add(key)
                        avis.facts.append(Fact(spec.id, spec.label, spec.theme, val, spec.unit, s, pno))

    full = " ".join(pages)
    # La Normandie n'introduit pas ses recommandations par un verbe : elle les porte « en
    # italique gras ». La couche texte perd la mise en forme, donc un extracteur lexical en
    # trouve ZÉRO — et zéro se lit comme « l'autorité n'a rien à redire ». On le dit.
    if TYPOGRAPHIC_RECO.search(full):
        avis.warnings.append(
            "recommandations signalées par la MISE EN FORME (italique gras) et non par une "
            "tournure : leur nombre ici n'est pas le nombre réel. Les extraire demande la "
            "police des caractères, pas une expression régulière.")
    marques = list(NUMBERED_RECO.finditer(full))
    if marques:
        # Chaque recommandation court jusqu'à la suivante — le découpage le plus fiable.
        for i, m in enumerate(marques):
            fin = marques[i + 1].start() if i + 1 < len(marques) else min(m.end() + 1200, len(full))
            txt = re.sub(r"\s+", " ", full[m.start():fin]).strip()
            page = next((j for j, p in enumerate(pages, 1)
                         if txt[:60] in re.sub(r"\s+", " ", p)), None)
            avis.recommandations.append({"numero": int(m.group(1)), "texte": txt, "page": page})
    else:
        for m in RECO.finditer(full):
            txt = re.sub(r"\s+", " ", m.group(0)).strip()
            page = next((i for i, p in enumerate(pages, 1) if txt[:60] in re.sub(r"\s+", " ", p)), None)
            avis.recommandations.append({"texte": txt, "page": page})

    # PLUSIEURS INSTALLATIONS (campus) : compté sur les FAITS extraits, pas sur des mots-clés — ceux-ci
    # sur-déclenchent (comparaison de voisinage, nom de société « PIPA-DC1 »). Plusieurs puissances IT
    # distinctes = plusieurs bâtiments (Nozay 75/37,5/15), corroboré par les étiquettes DC01/DC02/DC03.
    n_install = max(len({f.value for f in avis.facts if f.field_id == "puissance_it_mw"}),
                    len(set(DC_LABEL.findall(full))))
    if n_install >= 2:
        avis.plusieurs_installations = n_install
    return avis


class NotADocument(RuntimeError):
    """Le lien du registre ne mène pas à un document."""


def fetch_pdf(url: str) -> bytes:
    """Télécharge et VÉRIFIE que c'est bien un PDF.

    Le Grand Est ne met pas un document dans `lien_pdf` : il met la page HTML de l'année
    (« avis de l'Ae 2016 sur les projets dans le Bas-Rhin »), qui liste des dizaines d'avis.
    Sans cette vérification, pypdf lève un `PdfStreamError` opaque au milieu d'un lot et on
    croit à un document corrompu, alors que le registre est simplement construit autrement
    dans cette région. L'erreur doit nommer ce qu'on a reçu — c'est ce qui rend la panne
    réparable au lieu d'être mise sur le compte du hasard.
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
        blob = r.read()
    if not blob.startswith(b"%PDF"):
        head = blob[:80].decode("utf-8", "replace").strip().replace("\n", " ")
        kind = "page HTML" if b"<html" in blob[:400].lower() else f"type {ctype or 'inconnu'}"
        raise NotADocument(
            f"le lien du registre ne rend pas un PDF mais une {kind} — début : {head!r}. "
            "Ce n'est pas un document corrompu : cette région publie un lien de page, pas de fichier.")
    return blob
