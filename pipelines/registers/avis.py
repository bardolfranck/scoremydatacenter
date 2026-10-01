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


def _n(s: str) -> float:
    key = s.strip().lower()
    if key in WORDS:
        return float(WORDS[key])
    return float(re.sub(r"[   ]", "", s).replace(",", "."))


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
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


# ─────────────────────────────────────────────────────────────────────────────────────────
# LA LISTE. Volontairement la plus large que les documents supportent — y compris ce que
# notre grille ne note PAS (bruit, groupes, cuves, emplois, GES, fluides), parce que c'est
# précisément le centre de gravité de ces avis et la matière de la feature nuisances.
# ─────────────────────────────────────────────────────────────────────────────────────────
FIELDS: tuple[Field, ...] = (
    # ── Énergie ──────────────────────────────────────────────────────────────────────────
    Field("puissance_it_mw", "Puissance des salles informatiques", "energie", "MW",
          r"salles?\s+informatiques?.{0,80}puissance|puissance\s+(?:prévue|informatique|des\s+salles)",
          rf"puissance[^.]{{0,60}}?({NUM})\s*MW", bounds=(0.1, 2000.0)),
    # `puissance_site_mw` RETIRÉ (contrôle à l'échelle, 0/43 avis). Ces avis donnent la
    # puissance des SALLES informatiques (`puissance_it_mw`) et la puissance des GROUPES
    # séparément, jamais une « puissance appelée du site » globale : la notion n'existe pas
    # dans la matière. Un champ toujours nul, exposé en API, se lirait comme une absence
    # RÉELLE au lieu d'une notion inexistante. Si les 391 le démentent, on le remet.
    Field("consommation_gwh_an", "Consommation électrique annuelle", "energie", "GWh/an",
          r"consommation\s+(?:électrique|annuelle|d['’]électricité|énergétique)",
          rf"({NUM})\s*GWh"),
    Field("pue", "PUE annoncé pour le projet", "energie", None,
          r"\bPUE\b",
          rf"PUE[^.]{{0,40}}?(?:de|:)\s*({NUM})",
          # « Plus l'indice PUE est PROCHE DE 1 et plus la performance… » est la DÉFINITION du
          # PUE, pas la valeur du projet — elle sortait « pue=1 » (Bailly-Romainvilliers). Une
          # définition n'est pas une mesure (même classe que « étude d'impact » → chaleur).
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
    Field("groupes_carburant", "Carburant des groupes", "secours", None,
          r"groupes?\s+électrogènes?[^.]{0,120}(?:aliment|fonctionn)|carburant",
          kind="enum",
          choices=((r"huile\s+végétale\s+hydrotraitée|HVO", "huile végétale hydrotraitée (HVO)"),
                   (r"fioul\s+domestique", "fioul domestique"),
                   (r"gazole\s+non\s+routier|GNR", "gazole non routier"),
                   (r"\bgazole\b|\bfioul\b", "fioul/gazole"))),
    Field("cuves_nombre", "Cuves de carburant (nombre)", "secours", "cuves",
          r"cuves?[^.]{0,80}(?:stocker|carburant|fioul|gazole|enterrées?|aériennes?)",
          rf"({NUM}|{WORD_RE})\s+cuves?", reject=AGGREGAT_SITE, bounds=(1.0, 400.0)),
    Field("cuves_volume_unitaire_m3", "Volume unitaire d'une cuve", "secours", "m³",
          r"cuves?[^.]{0,60}(?:de|chacune)",
          rf"({NUM})\s*(?:{M3})\s*chacune|cuves?\s+(?:enterrées?\s+|aériennes?\s+)?de\s+({NUM})\s*(?:{M3})", bounds=(1.0, 2000.0)),
    Field("cuves_volume_total_m3", "Volume total de carburant stocké", "secours", "m³",
          r"volume\s+total|capacité\s+(?:totale\s+)?de\s+stockage|stockage\s+total",
          rf"({NUM})\s*(?:{M3})",
          # « Le volume total des eaux traitées par infiltration sera de 220 m3 » (Rungis) : un
          # volume d'EAUX PLUVIALES capté comme volume de fioul — l'ancre « volume total » ne
          # dit pas de QUOI. On exclut le contexte hydraulique ; bon nombre, mauvais objet.
          reject=r"eaux?\s+pluviales?|infiltr|pluies?|rétention|bassin|assainissement",
          bounds=(1.0, 50000.0)),
    Field("cuves_enterrees", "Cuves enterrées", "secours", None,
          r"cuves?\s+enterrées?", kind="text"),
    Field("autonomie_heures", "Autonomie en secours", "secours", "h",
          r"autonomie|fonctionnement\s+pendant|assurer\s+le\s+fonctionnement",
          rf"pendant\s+({NUM})\s*(?:heures?|h\b)|autonomie[^.]{{0,40}}?({NUM})\s*(?:heures?|h\b)", bounds=(1.0, 720.0)),
    Field("essais_groupes", "Essais périodiques des groupes", "secours", None,
          r"essais?[^.]{0,60}groupes?\s+électrogènes?|groupes?[^.]{0,60}essais?\s+(?:périodiques|mensuels|de\s+maintenance)",
          kind="text"),

    # ── Bruit : sujet n°1 de l'État dans ces avis, zéro indicateur chez nous ──────────────
    # Tous les niveaux relevés, CHACUN AVEC SA PHRASE : c'est la phrase qui dit s'il s'agit
    # du jour ou de la nuit, d'un point de mesure ou d'une limite de propriété, d'une valeur
    # ferme ou d'une borne de fourchette. Réduire ce champ à un scalaire produit des demi-
    # vérités — « 62 dB(A) la nuit » alors que l'avis écrit « entre 59,5 et 62 dB(A) ».
    Field("bruit_niveau_dba", "Niveaux sonores relevés", "bruit", "dB(A)",
          r"niveaux?\s+(?:sonores?|acoustiques?|de\s+bruit)|bruit\s+(?:ambiant|résiduel)|émergence|\bLAeq\b",
          rf"({NUM})\s*dB\s*\(?A\)?", multiple=True, bounds=(25.0, 120.0)),
    # Le niveau de nuit est souvent écrit SANS son unité, adossé au niveau de jour :
    # « 60,5 dB(A) et 54,5 en période nocturne ». Un motif qui exige l'unité le perd.
    # On refuse en revanche les phrases à fourchette : une borne n'est pas une valeur.
    Field("bruit_nuit_dba", "Niveau sonore nocturne (valeur ferme)", "bruit", "dB(A)",
          r"(?:nocturne|de\s+nuit|période\s+nuit)",
          rf"({NUM})\s*(?:dB\s*\(?A\)?\s*)?(?:en\s+période\s+nocturne|de\s+nuit|la\s+nuit)",
          reject=r"\bentre\b[^.]{0,60}\bet\b|oscillent", bounds=(25.0, 120.0)),
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
    Field("surface_salles_m2", "Surface des salles informatiques", "foncier", "m²",
          r"salles?\s+informatiques?[^.]{0,80}(?:emprise|surface|représentent)",
          rf"salles?\s+informatiques?\s+(?:représentent|occupent)?\s*({NUM})\s*(?:{M2})"),
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
    Field("fluides_frigorigenes", "Fluides frigorigènes", "climat", None,
          r"fluides?\s+frigorigènes?", kind="text"),
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
          rf"({NUM})\s*(?:m|mètres|km)\b", bounds=(1.0, 20000.0)),
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
TYPOGRAPHIC_RECO = re.compile(
    r"recommandations\s+sont\s+portées\s+en\s+(?:italique|gras)|"
    r"recommandations\s+(?:figurent|apparaissent)\s+en\s+(?:italique|gras)", re.I)


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
        d = {"indicateur": self.field_id, "libelle": self.label, "theme": self.theme,
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

    def as_dict(self) -> dict:
        by_theme: dict[str, list[dict]] = {}
        for f in self.facts:
            by_theme.setdefault(f.theme, []).append(f.as_dict())
        return {
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


def pages_of(pdf: bytes) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf))
    return [_norm(p.extract_text() or "") for p in reader.pages]


def _sentences(page_text: str) -> list[str]:
    flat = re.sub(r"\s*\n\s*", " ", page_text)
    # la césure de fin de ligne recolle les mots coupés (« réglemen- tée »)
    flat = re.sub(r"(\w)-\s+(\w)", r"\1\2", flat)
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+", flat) if 25 <= len(s.strip()) <= 420]


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
    avis = Avis(doc_url=doc_url, n_pages=len(pages), n_chars=sum(len(p) for p in pages), sha256=sha256)
    if avis.n_chars < 500 * max(1, len(pages)) // 10:
        avis.has_text_layer = False
        avis.warnings.append(
            "couche texte absente ou trop maigre — document SIGNALÉ, pas océrisé "
            "(une erreur de chiffre sur une fiche publique coûte plus que ce document ne rapporte)")
        return avis

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
    for m in RECO.finditer(full):
        txt = re.sub(r"\s+", " ", m.group(0)).strip()
        page = next((i for i, p in enumerate(pages, 1) if txt[:60] in re.sub(r"\s+", " ", p)), None)
        avis.recommandations.append({"texte": txt, "page": page})
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
