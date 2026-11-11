# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Build gates (ARCHITECTURE section 6.3) — every failure names its gate and its fix.

Gate 1  JSON Schema validation of all data files.
Gate 2  Announced vs measured never merged: an indicator that the methodology
        declares 'declarative' can only be measured with verification evidence.
Gate 3  Methodology coherence: threshold traceability (schema), weights sum to 1,
        unique ids, direction contract, declared-but-unenforced ethical
        constraints cannot claim 'calibrated'.
Gate 4  (removed 2026-07-15) The prior-notice mechanism was retired on legal
        review: grades publish directly; the permanent response space remains.
Gate 5  Methodology anteriority: exactly one active version; a real (non-zz)
        DC cannot be scored against a draft methodology; score_history entries
        must reference the current version.
Gate 6  Retrospective fixtures + transparency floor: enforced by the test
        suite (make test), which CI runs before make build.
Gate 7  No grade rendered outside <ScoreBadge>: template lint, arrives with
        the site components (plan phase 2).
Gate 9  L2 power provenance (memo 2026-07-19): a 'measured' L2 may only rest on a
        regulatory-tier power figure (EED register); a positively-identified
        aggregator/press/operator MW is a third-party claim -> 'announced'.
Gate 8  Extraction coherence: a project indicator may only be 'missing' (an
        opacity claim) with a read-trace source once T2 attests a public dossier;
        'not_collected' (nobody looked) is a draft-only state and blocks publication.
Journal gate: every score_history entry after the first carries a rationale.
"""

import math
import re
import os
import sys
import unicodedata
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .core import (
    DATA_DIR, FICTIONAL_PREFIX, GateError, load_json, load_methodology,
    datacenter_paths, watchlist_paths,
)
from .scoring import score_datacenter

# Gate 9 — canonical tier definition lives in pipelines/labels/power_tier.py; the two patterns
# are mirrored here because the engine imports nothing from pipelines. Unify the day the schema
# gains a structured power_source field (A-16).
_L2_POWER_PROSE = re.compile(r"puissance\s+[\d.]+\s*MW\s*\(([^)]+)\)", re.I)
_L2_REGULATORY = re.compile(r"EED|RVO|registre r[ée]glementaire|regulatory register", re.I)

# A watchlist entry is FACTS ONLY (A-19/A-21): a grade must be structurally
# impossible. additionalProperties:false already blocks these keys; this explicit
# scan turns any leak into a named gate failure instead of a generic schema error.
GRADE_LIKE_KEYS = {"grade", "grades", "score", "confidence", "letter", "note", "documentation"}


def _grade_leak(node) -> str | None:
    """Return the first grade-like key found anywhere in a watchlist entry, or None."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in GRADE_LIKE_KEYS:
                return k
            leak = _grade_leak(v)
            if leak:
                return leak
    elif isinstance(node, list):
        for v in node:
            leak = _grade_leak(v)
            if leak:
                return leak
    return None


def _schema_errors(instance, schema, label: str) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"GATE 1: {label}: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(instance), key=str)
    ]


# LE SEUL GATE QUE SEUL `make rescore` PEUT LEVER. `engine.score.record()` refuse de tourner
# tant qu'un gate échoue — règle juste en général, mais qui rendait ce remède-ci INATTEIGNABLE :
# le gate réclamait un re-score, et le re-score refusait à cause du gate. Toute montée de version
# de méthodo tombait donc dans cette boucle (constaté au passage en v0.3.0, 2026-10-06). La
# phrase est nommée ici pour que `record()` la reconnaisse sans recopier un bout de message —
# un gate et son remède ne doivent pas pouvoir dériver l'un de l'autre.
STALE_METHODOLOGY_REMEDY = "record a methodology_change re-score (make rescore)"

GEO_WAIVERS = {
    # Dérogations EXPLICITES, datées et motivées. Une dérogation n'est pas une exception
    # silencieuse : elle est listée ici, le gate l'imprime à chaque passage, et elle doit
    # disparaître. Toute fiche ajoutée ici sans motif ni date est un aveu d'échec.
    # fr-cloudhq / fr-digital-realty / fr-gazel-energie : CORRIGÉES 2026-09-29 (vrai site localisé,
    # détecteur 2-oracles + test bâtiment passés) — sorties des dérogations.
    "fr-microsoft": "2026-09-29 — Petit-Landau : greenfield agricole ~36 ha le long du Rhin, site réel non localisé (permis suspendus MRAe) ; coordonnée au niveau commune, indicateurs de point en not_collected ; déblocage = plan cadastral du dossier d'enquête",
    "ch-green-datacenter-zurich-metro": "2026-09-29 — périmètre EU, correction à cadrer",
    "ch-stack-infrastucture-zur01": "2026-09-29 — périmètre EU, correction à cadrer",
    "ch-stack-infrastucture-zurl1": "2026-09-29 — périmètre EU, correction à cadrer",
    "es-aws-aragon-villanueva-de-gallego": "2026-09-29 — périmètre EU, correction à cadrer",
    "es-aws-aragon-el-burgo-de-ebro": "2026-09-29 — périmètre EU, correction à cadrer",
    "es-meta-talavera-de-la-reina": "2026-09-29 — périmètre EU, correction à cadrer",
    # FAUX POSITIF MESURÉ, pas une correction à cadrer : le point N'EST PAS un centre de commune.
    # PeeringDB déclare pour cette installation lat 37.80561 / lon -0.83857 — exactement la
    # coordonnée de la fiche — à « Avda Balsicas, 6, 30730 San Javier ». Géocodage de cette rue
    # (Nominatim, 2026-10-16) : 30 m du point. Le centre GeoNames de la commune tombe à 128 m
    # parce que l'installation est EN CENTRE-VILLE, pas parce que la coordonnée a été fabriquée.
    # Le verdict `off_building` s'explique par une petite installation dans un bâti mixte non
    # tracé en bâtiment sur OSM. Arbitre retenu : l'adresse déclarée par l'opérateur.
    # Levée de la dérogation = empreinte bâtiment OSM, ou une adresse opérateur contredisant
    # celle-ci. (Inscrite par codeur-site, qui est le gate de publication, pas la lane EU : à
    # ré-examiner par EU quand la session revient.)
    "es-amune-networks-cpd": "2026-10-16 — faux positif : point = adresse opérateur déclarée "
                             "(PeeringDB, Avda Balsicas 6) à 30 m du géocodage de la rue ; la "
                             "proximité du centre GeoNames (128 m) vient du site en centre-ville",
    # EU 2026-10-16 (ré-examen après mesure codeur-site par la méthode Amune) : DEUX vrais DC (opérateur
    # connu), mais — contrairement à Amune — la coordonnée N'EST PAS confirmée par l'adresse déclarée.
    # Ce ne sont donc PAS des faux positifs prouvés : des géocodes NIVEAU VILLE, non vérifiés au bâtiment,
    # assumés TEMPORAIREMENT. Ce qui les rend inoffensifs : les indicateurs de POINT sont déjà en
    # not_collected (aucune valeur fabriquée) — la dérogation N'AFFIRME PAS « c'est correct », elle dit
    # « coord grossière connue comme telle ». Levée = adresse opérateur / cadastre / empreinte bâtiment OSM.
    # ORIGINE ÉTABLIE le 2026-10-17 (lane EU) : ce n'est ni un annuaire ni une saisie, c'est la
    # DÉCLARATION RÉGLEMENTAIRE qui ne descend pas plus bas. La directive EED (RVO) déclare à la
    # maille GEMEENTE — la fiche porte `lau_code GM0753` et AUCUNE adresse —, donc le pipeline a
    # géocodé la commune. Il n'existe rien de plus fin À RECALER DEPUIS CETTE SOURCE : le défaut
    # n'est pas dans le point, il est dans la granularité du registre. Le déblocage passe donc
    # obligatoirement par une source HORS EED (adresse opérateur, cadastre).
    "nl-rabobank-datacenter-best": "2026-10-17 — Rabobank Datacenter Best, vrai DC ; coordonnée = géocode "
                                   "du code commune (EED/RVO, lau_code GM0753, déclaration sans adresse), "
                                   "à 109 m du centre de Best, hors bâtiment ; aucune entrée PeeringDB, donc "
                                   "pas d'arbitre adresse ; indicateurs de point en not_collected (rien de "
                                   "fabriqué) ; déblocage = adresse bâtiment d'une source hors EED",
    # ⚠️ MESURE CORRIGÉE le 2026-10-17 — et elle AFFAIBLIT la thèse du géocode de ville.
    # Les « 122 m de la rue Kościelna » venaient du point REPRÉSENTATIF de la rue, c'est-à-dire
    # de son milieu : un mauvais témoin, puisqu'une rue n'est pas un point. Mesuré sur le bâti
    # OSM, le point de la fiche est à 58 m de « Kościelna 8 », DERNIER numéro cartographié de
    # la rue — et le n° 10 n'existe pas dans OSM. Autrement dit le point tombe là où la rue se
    # poursuit, pas sur le centre-ville (120 m). Lecture honnête : vraisemblablement l'adresse
    # déclarée, impossible à confirmer au bâtiment faute du n° 10.
    # La dérogation reste donc PRUDENTE et les indicateurs de point restent neutralisés : on ne
    # repositionne pas vers une cible qu'on ne peut pas désigner. Aucun recalage à faire ici.
    # 🔴 DÉROGATION AVEC REMÈDE EN PLACE, pas une exception de confort (2026-11-02).
    # Cette fiche est publique depuis le 2026-10-30 avec un C bâti sur cinq indicateurs de
    # point ; le re-run du détecteur l'a classée « géo fabriquée probable » (GeoNames à 104 m
    # du centre de Ballycoolen, hors bâtiment) et la coordonnée n'a PAS changé — c'est la
    # mesure qui ne l'avait jamais vue, le sidecar du jour du deploy datant de dix jours.
    # Ce qui rend la dérogation tenable, et c'est la condition : la LETTRE est désormais
    # retenue mécaniquement (`grade_withheld` posé au build sur toute coordonnée tenue par
    # `coord_trust.coord_hold`, propagé par `scrub-grades` à la fiche, au classement et à la
    # carte), la carte de contexte l'était déjà, et les cinq indicateurs de point sont
    # suspendus dans la source. La fiche ne publie donc plus aucune valeur issue de ce point.
    # Sans cette dérogation le gate gèle TOUT le site pour une fiche — ce qui est la bonne
    # réaction quand rien ne retient la lettre, et une mauvaise maintenant qu'elle l'est.
    # LEVÉE = reposition par la lane EU (chantier sous-traité le 2026-11-02 : le dossier de
    # permis GeoHive devrait porter une adresse ou une parcelle).
    # ie-k2-strategic-infrastructure-ireland-limited : DÉROGATION SUPPRIMÉE le 2026-11-02,
    # sa condition de levée étant remplie. La lane EU a recalé le point sur le dossier de
    # permis FW19A/0089 ; la re-mesure donne `near_building` à 24,1 m d'un bâtiment OSM
    # (way/1340216913) QUI EST TAGGÉ data centre — donc le vrai site K2. Le détecteur la
    # classe « faux positif sur un vrai bâtiment », plus « fabriquée », et `coord_hold` ne
    # la tient plus du tout : sa lettre revient d'elle-même au prochain build.
    # Une dérogation qu'on garde après la levée de sa condition est une exception silencieuse.
    "pl-orange-polska-bia-ystok": "2026-10-17 — Orange Polska Białystok, vrai DC (opérateur connu) ; "
                                  "coordonnée = déclaration PeeringDB « Kościelna 10 », à 58 m du n° 8 "
                                  "(dernier numéro cartographié de cette rue) et à 120 m du centre GeoNames ; "
                                  "le n° 10 est absent d'OSM, donc NON vérifiable au bâtiment ; indicateurs "
                                  "de point en not_collected ; déblocage = n° 10 cartographié ou cadastre",
}


SEUIL_POSITION_M = 1.0   # sous le mètre, deux fiches désignent le même point, pas deux points


def _metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance plane locale — à l'échelle du mètre, la projection ne coûte rien."""
    dy = (lat1 - lat2) * 111_320.0
    dx = (lon1 - lon2) * 111_320.0 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dx, dy)


# LA PROSE EST UNE VALEUR SERVIE, DONC ELLE SE GATE. Né d'un défaut que j'ai laissé passer :
# la démotion L3 du 2026-10-04 a corrigé 333 NOTES et laissé la PROSE affirmer l'absence qu'on
# venait de retirer — 97 fiches servies (ES 41, IT 53, FI 3) ont annoncé pendant deux jours
# « aucun site à risque industriel dans un rayon de 5 km » alors que leur indicateur disait
# « non mesuré ». Un contrôle au moment de la RÉDACTION n'aurait rien vu : ces textes étaient
# justes le jour où ils ont été écrits, et sont devenus faux quand la VALEUR a changé sous eux.
# Le contrôle doit donc porter sur ce qui est SERVI, à chaque build.
#
# Portée volontairement étroite : on ne vérifie pas que la prose dit tout, on vérifie qu'elle
# n'AFFIRME pas une absence que la valeur contredit. Une prose muette est incomplète, pas fausse.
# La table se lit comme la méthodo : par indicateur, les valeurs qui autorisent l'affirmation.
# Les langues que porte la synthèse, lues au SCHÉMA — pas recopiées. Le schéma est ce qui
# décide ce qu'une fiche peut contenir ; une seconde liste ici finirait par ne plus dire la
# même chose, et c'est le gate qui se tairait [[liste-a-deux-endroits-ment]].
def _langues_de_la_synthese() -> tuple[str, ...]:
    schema = load_json(DATA_DIR / "schema" / "datacenter.schema.json")
    bloc = schema["properties"]["synthesis"]["properties"]["site"]["properties"]
    return tuple(k for k in bloc if k != "lead")


LANGUES_SYNTHESE = _langues_de_la_synthese()

ABSENCE_AFFIRMEE = {
    "L3": (
        re.compile(r"(aucun (?:site|établissement)[^.;]{0,60}(?:risque|seveso)"
                   r"|no (?:site|establishment)[^.;]{0,60}(?:risk|seveso)"
                   r"|aucun seveso)", re.I),
        {"none_within_5km"},
    ),
}


def prose_gate(paths: list[Path]) -> list[str]:
    """GATE PROSE — une synthèse ne peut pas affirmer une absence que la valeur servie contredit.

    Déterministe, zéro réseau : ne lit que le corpus. Rend un problème par fiche fautive, en
    nommant l'indicateur et sa valeur, pour que la fiche aille à la régénération de prose et pas
    à une retouche manuelle (la prose se DÉRIVE de l'artefact noté, elle ne s'édite pas à la main).
    """
    problems = []
    for p in paths:
        try:
            d = load_json(p)
        except Exception:  # noqa: BLE001 — l'illisibilité est signalée ailleurs
            continue
        syn = d.get("synthesis")
        if not syn:
            continue
        # 🔴 LE GATE DOIT LIRE TOUTES LES LANGUES DE LA SYNTHÈSE, pas les deux premières.
        # Il cherche une AFFIRMATION D'ABSENCE (« aucun site Seveso à proximité ») que la
        # donnée ne soutient pas. Figé à ("fr", "en"), il laisserait passer la même
        # affirmation fausse en néerlandais : la phrase traduite dit la même chose, et le
        # gate ne la lirait pas. On lit les langues DÉCLARÉES, pas une paire en dur.
        texte = " ".join(
            v.get(lang, "") or ""
            for v in syn.values()
            if isinstance(v, dict)
            for lang in LANGUES_SYNTHESE
        )
        entrees = {i["id"]: i for i in d.get("indicators", [])}
        for iid, (motif, valeurs_ok) in ABSENCE_AFFIRMEE.items():
            e = entrees.get(iid)
            if e is None or not (m := motif.search(texte)):
                continue
            servie = e.get("value") if e.get("status") not in ("missing", "not_collected") else e["status"]
            if servie in valeurs_ok:
                continue
            problems.append(
                f"GATE PROSE: {p.name}: la synthèse affirme « {m.group(0).strip()} » alors que "
                f"{iid} vaut « {servie} » — régénérer la synthèse (la prose se dérive de l'artefact noté)"
            )
    return problems


# ── GATE OPÉRATEUR ──────────────────────────────────────────────────────────────────────────
# Une absence d'exploitant s'écrit `null`. Écrite en prose, elle se fait passer pour un nom.
#
# NÉ D'UNE FUITE SERVIE (2026-10-17). La lane US écrivait « opérateur non identifié », la lane
# EU « unknown », une troisième « UNKNOWN — to fill ». Côté site, quatre endroits répondaient à
# « l'opérateur est-il identifié ? » avec quatre listes de graphies différentes : aucune ne les
# connaissait toutes. Servi en production sur 329 sites de la carte et 162 fiches — dont le
# balisage schema.org, qui AFFIRMAIT à une machine que l'exploitant du site est une société
# nommée « opérateur non identifié ». 871 fiches ont été migrées vers `null`.
#
# POURQUOI UN GATE ET PAS UNE CONSIGNE. Le filtre d'affichage ne peut pas connaître la
# prochaine graphie, et il échoue en silence : il n'affiche pas une erreur, il affiche un nom.
# Le gate déplace l'échec là où quelqu'un le voit — le build casse, nommément.
#
# SON MANDAT EST LE CORPUS SERVI, et rien d'autre. Le coffre d'étude `validation/` garde ses
# placeholders : c'est une cohorte pré-enregistrée scellée, qui n'est jamais publiée et qu'on
# ne réécrit pas après coup. Elle sort du mandat par CONSTRUCTION (le gate ne lit que les
# chemins servis), pas par une exception ajoutée à la main — une exception se perd.
#
# ⚠️ DEUX FORMES DE COMPARAISON, ET C'EST DÉLIBÉRÉ. Les jetons courts sont comparés en ÉGALITÉ
# sur forme normalisée ; les seules recherches par inclusion sont des locutions assez longues
# pour ne rien attraper d'autre. Une inclusion naïve mentirait : en cherchant « n/a » dans la
# chaîne, « Amazon/AWS » devient une absence — le faux positif a été rencontré en écrivant ce
# gate, sur cinq fiches réelles.
_ABSENCE_EXACTE = {
    "", "unknown", "none", "null", "nil", "n/a", "na", "nc", "inconnu", "indetermine",
    "non identifie", "non renseigne", "a renseigner", "to fill", "tbd",
}
_ABSENCE_LOCUTION = (
    "non identifie", "not identified", "to fill", "a renseigner",
    "etat inconnu", "operateur inconnu", "unknown operator",
)


def _forme_normalisee(valeur: str) -> str:
    """Casse, accents et espaces multiples ne doivent pas rouvrir la porte : « Opérateur Non
    Identifié » doit mourir comme « operateur non identifie », sans qu'on écrive les deux."""
    sans_accent = unicodedata.normalize("NFD", valeur.strip().lower())
    sans_accent = "".join(c for c in sans_accent if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sans_accent)


def operator_gate(paths: list[Path]) -> list[str]:
    """GATE OPÉRATEUR — un opérateur servi NOMME un exploitant, ou vaut `null`."""
    problems = []
    for p in paths:
        try:
            d = load_json(p)
        except Exception:  # noqa: BLE001 — l'illisibilité est signalée ailleurs
            continue
        valeur = d.get("identity", {}).get("operator")
        if valeur is None:
            continue  # l'absence déclarée : exactement ce que le gate demande
        forme = _forme_normalisee(str(valeur))
        if forme in _ABSENCE_EXACTE or any(loc in forme for loc in _ABSENCE_LOCUTION):
            problems.append(
                f"GATE OPÉRATEUR: {p.name}: operator vaut « {valeur} » — une absence d'exploitant "
                f"s'écrit `null`, pas en prose. Écrite ainsi elle s'affiche comme un nom de "
                f"société, groupe des fiches sous « même opérateur » et part dans le balisage "
                f"structuré de la page."
            )
    return problems


def position_gate(paths: list[Path]) -> list[str]:
    """GATE POSITION — deux fiches au même point doivent avoir été TRANCHÉES.

    Pourquoi un gate et pas une consigne de collecte : la coordonnée seule ne distingue pas
    un doublon d'un campus ni d'un immeuble partagé. Seule une source le fait — adresse
    postale, registre, relevé. Le gate n'exige donc pas l'absence de paires, il exige
    l'ADJUDICATION : `position_adjudication` dans la provenance de l'une des deux fiches.

    Il existe parce que le contrôle a d'abord été appliqué à un seul lot. J'ai retenu 13
    fiches britanniques sur ce critère, puis mesuré le corpus entier : 78 paires à un mètre
    ou moins étaient DÉJÀ servies, sur neuf autres pays, dont des doublons manifestes. Le
    standard était bon, son périmètre était faux.

    Les paires d'alors sont inventoriées dans `position_waivers` — une dette datée qui doit
    décroître, pas une permission. Toute paire nouvelle est refusée.

    Le gate est DÉTERMINISTE : il ne lit que le corpus et les sidecars de provenance, aucun
    réseau. Mesure dehors, décision dedans, comme le gate géo.
    """
    from .position_waivers import POSITION_WAIVERS

    pts: list[tuple[str, float, float]] = []
    tranchees: set[str] = set()
    for p in paths:
        try:
            d = load_json(p)
        except Exception:  # noqa: BLE001 — l'illisibilité est déjà signalée ailleurs
            continue
        c = ((d.get("identity") or {}).get("coordinates")) or {}
        if not isinstance(c.get("lat"), (int, float)) or not isinstance(c.get("lon"), (int, float)):
            continue
        pts.append((p.stem, float(c["lat"]), float(c["lon"])))
        prov = p.with_name(p.stem + ".provenance.json")
        if prov.is_file():
            try:
                if "position_adjudication" in load_json(prov):
                    tranchees.add(p.stem)
            except Exception:  # noqa: BLE001
                pass

    # Balayage par latitude croissante : deux points à moins d'un mètre le sont d'abord en
    # latitude, donc la fenêtre se referme tout de suite. Le corpus entier en une passe.
    pts.sort(key=lambda t: t[1])
    out: list[str] = []
    vues: set[tuple[str, str]] = set()
    for i, a in enumerate(pts):
        for b in pts[i + 1:]:
            if (b[1] - a[1]) * 111_320.0 > SEUIL_POSITION_M:
                break
            if _metres(a[1], a[2], b[1], b[2]) > SEUIL_POSITION_M:
                continue
            paire = tuple(sorted((a[0], b[0])))          # type: ignore[assignment]
            if paire in vues:
                continue
            vues.add(paire)
            if paire[0] in tranchees or paire[1] in tranchees:
                continue                                  # tranchée : elle passe au mérite
            if paire in POSITION_WAIVERS:
                continue                                  # dette inventoriée, datée, à résorber
            out.append(
                f"GATE POSITION: {paire[0]!r} et {paire[1]!r} occupent le même point "
                f"(≤ {SEUIL_POSITION_M:.0f} m) sans adjudication — trancher (doublon, campus "
                f"ou immeuble partagé) et écrire `position_adjudication` en provenance"
            )
    reste = len(POSITION_WAIVERS)
    if reste:
        print(f"GATE POSITION: {reste} paire(s) co-localisées héritées restent à trancher "
              f"(engine/position_waivers.py) — cette dette doit décroître", file=sys.stderr)
    return out


def geo_gate(data_dir: Path) -> list[str]:
    """GATE GÉO — une coordonnée fabriquée ne doit pas pouvoir entrer dans le corpus.

    Pourquoi ce gate est ICI et pas dans une consigne envoyée à un agent (Franck, 2026-09-29,
    « les gates sont dans le WORKFLOW, pas distribués au bon vouloir de x ou y ») : une règle
    qui vit dans un message se perd au prochain agent, au prochain contexte, au prochain mois.
    Celle-ci a coûté cher — 6 fiches publiques et notées sur des coordonnées de géocodeur,
    dont le plus gros projet de France.

    La MESURE est hors-ligne (elle interroge deux géocodeurs, donc du réseau, ce que le build
    déterministe ne fait pas) : c'est `pipelines.geo_audit.centroid_check`, qui écrit le
    sidecar. Le GATE, lui, est déterministe : il lit le sidecar et refuse. Mesure dehors,
    décision dedans.

    Deux refus : une fiche classée « géo fabriquée probable » sans dérogation explicite, et
    une fiche du corpus ABSENTE du sidecar — sinon il suffirait de ne pas lancer la mesure
    pour passer le gate.
    """
    # Le sidecar vit dans le newsroom PRIVÉ, que data_dir pointe dessus ou non.
    newsroom = Path(os.environ.get("NEWSROOM_CAL",
                                   Path(__file__).resolve().parents[2] / "smdc-newsroom" / "calibration"))
    # 🔴 LE CORPUS COMPTÉ DOIT ÊTRE CELUI QUE LE SIDECAR DÉCRIT — même défaut que le gate
    # statut, découvert ici le 2026-11-02 en resserrant la couverture : sidecar du newsroom,
    # corpus de `data_dir`, donc depuis le dépôt public ce gate comparait 3 293 fiches
    # mesurées à 2 fixtures. Un gate qui compare deux populations différentes ne mesure rien.
    racine_geo = next((r for r in (data_dir, newsroom)
                       if (r / "geo-audit" / "centroid-check.json").is_file()), None)
    sidecar = None if racine_geo is None else racine_geo / "geo-audit" / "centroid-check.json"
    if sidecar is None:
        # SANS newsroom monté, il n'y a pas de corpus réel à protéger : `data_dir` est alors
        # le jeu de fixtures du dépôt (2 fiches zz-), et exiger un sidecar y fait échouer la
        # CI et tout clone frais, sur une mesure qui demande du réseau et un corpus privé.
        # Le gate garde en revanche toutes ses dents dès que le newsroom EXISTE : un sidecar
        # manquant est alors un vrai manquement, et c'est le cas qu'on veut attraper — sinon
        # il suffirait de ne pas lancer la mesure pour passer.
        # Défaut introduit en câblant ce gate (2026-09-29) : vert en local, rouge en CI, et
        # il a bloqué la PR d'un coéquipier sur un sujet sans rapport.
        if not newsroom.is_dir():
            return []
        return ["GATE GÉO: sidecar centroid-check.json absent — lancer "
                "`python -m pipelines.geo_audit.centroid_check` avant d'onboarder"]
    report = load_json(sidecar)
    flagged = {e["id"] for e in report.get("fabriquees_probables", [])}
    out: list[str] = []
    for fid in sorted(flagged - set(GEO_WAIVERS)):
        out.append(f"GATE GÉO: {fid!r} a une coordonnée de géocodeur (centre de commune) — "
                   f"localiser le site réel, ou inscrire une dérogation motivée et datée")
    # NON ÉVALUÉES — près d'un centroïde, mais sans verdict bâtiment, donc INDÉCIDABLES.
    # Elles étaient comptées « faux positif », c'est-à-dire saines : une fiche jamais mesurée
    # ressemblait à une fiche mesurée et propre, et le détecteur paraissait d'autant plus net
    # qu'on lui ajoutait des fiches qu'il ne savait pas juger. Le troisième état est venu
    # d'agent-data-pipeline-FR ; ici on en tire la conséquence, qui est de REFUSER. Une fiche
    # qu'on ne sait pas juger ne part pas en ligne — c'est tout l'objet de ce gate.
    for fid in sorted({e["id"] for e in report.get("non_evalues", [])} - set(GEO_WAIVERS)):
        out.append(f"GATE GÉO: {fid!r} est près d'un centroïde de commune et n'a PAS de verdict "
                   f"bâtiment — indécidable, donc refusée : lancer l'audit bâtiment "
                   f"(`python -m pipelines.geo_audit.audit`) sur cette fiche")
    # Couverture : le sidecar ne liste que les cas remarquables, pas les fiches saines. On
    # vérifie donc que la MESURE a bien porté sur tout le corpus — sinon il suffirait de ne
    # pas relancer le détecteur après un onboarding pour passer le gate sans être vu.
    #
    # 🔴 CE CONTRÔLE ÉTAIT UN `>=` SUR UN COMPTE, ET IL A LAISSÉ PASSER CE QU'IL DEVAIT
    # ARRÊTER. Le 2026-10-30, 8 fiches irlandaises neuves sont parties en production avec un
    # sidecar daté du 2026-10-20 : il annonçait **3 283 fiches testées** pour un corpus de
    # **3 275**, donc `3283 >= 3275` passait — alors qu'aucune des 8 n'avait été mesurée. Les
    # 3 283 étaient d'autres fiches, dont certaines disparues depuis. Le re-run du 2026-11-02
    # a classé l'une d'elles « géo fabriquée probable » : elle était publique depuis deux
    # jours, notée C, sur cinq indicateurs calculés depuis ce point.
    #
    # UN COMPTE NE PROUVERA JAMAIS UNE COUVERTURE D'ENSEMBLE. Deux remèdes, du plus fort au
    # plus faible, et le gate prend le plus fort que le sidecar permet :
    #   1. `meta.ids_testees` — la LISTE des fiches mesurées. Comparaison d'ensembles, exacte.
    #      C'est le contrat demandé à la lane qui produit le détecteur.
    #   2. à défaut, ÉGALITÉ STRICTE du compte : un sidecar qui a mesuré PLUS que le corpus
    #      n'est pas rassurant, il est périmé par construction (des fiches ont disparu), et
    #      c'est précisément ce profil qui a laissé passer les 8.
    meta = report.get("meta") or {}
    covered = (meta.get("counts") or {}).get("testées")
    ids_testees = meta.get("ids_testees")
    # La racine qui porte les FICHES n'est pas toujours celle qui porte le sidecar : dans le
    # dépôt public, `data_dir` a les fixtures et le sidecar vit dans le newsroom. On compte
    # donc les fiches là où il y en a.
    racine_corpus = racine_geo if datacenter_paths(racine_geo) else data_dir
    corpus_ids = {p.stem for p in datacenter_paths(racine_corpus)}
    corpus = len(corpus_ids)
    if ids_testees is not None:
        jamais = sorted(corpus_ids - set(ids_testees))
        if jamais:
            out.append(
                f"GATE GÉO: {len(jamais)} fiche(s) du corpus n'ont JAMAIS été mesurées "
                f"({jamais[:5]}) — relancer `python -m pipelines.geo_audit.centroid_check` "
                f"avant de publier. Une fiche qu'on ne sait pas juger ne part pas en ligne."
            )
    elif covered is None:
        out.append("GATE GÉO: le sidecar ne dit pas combien de fiches ont été testées")
    elif covered != corpus:
        sens = "moins" if covered < corpus else "PLUS"
        out.append(
            f"GATE GÉO: détecteur de centroïde périmé — {covered} fiches testées pour "
            f"{corpus} au corpus (il en a mesuré {sens}). Relancer avant de publier, et "
            f"faire émettre `meta.ids_testees` au détecteur : un compte ne prouve pas une "
            f"couverture d'ensemble, et c'est ce `>=` qui a laissé partir 8 fiches jamais "
            f"mesurées le 2026-10-30."
        )
    # CE QUE CE GATE NE DIT PAS, dit à chaque passage. Vert ici ne signifie pas « coordonnées
    # certifiées » : il signifie « mesurées, et ne tombant pas dans le motif connu ». Deux
    # angles morts sont établis, et le silence sur eux serait le vrai danger — c'est en
    # croyant un gate plus large qu'il n'est qu'on publie une coordonnée fabriquée.
    #
    #   · il ne teste que le centroïde de COMMUNE : une coordonnée reprise d'une aire plus
    #     fine (district postal, quartier) passe dessous — la classe qui a fait retenir
    #     gb-virtus-london5-stockley-park ;
    #   · il compare à UN répertoire géographique : un point fabriqué depuis un AUTRE
    #     répertoire peut en être à plus de 150 m et n'être jamais signalé. Quatre fiches
    #     suisses décrites comme des centroïdes de commune par agent-data-pipeline-EU
    #     n'apparaissent dans aucune des deux listes du sidecar.
    #
    # Et la provenance ne comble pas le trou : au 2026-09-28, 1285 coordonnées sur 1430 sont
    # `source: unrecorded`. On ne peut donc pas remonter à la source d'un point ; le test
    # géométrique est tout ce qu'on a.
    if not out:
        angle = ((report.get("meta") or {}).get("angle_mort")
                 or "ne teste que le centroïde de commune, sur un seul répertoire")
        print(f"GATE GÉO: {covered} fiches mesurées, rien à signaler — ce test {angle}",
              file=sys.stderr)
    return out


# 🔴 LE CLIQUET DE STATUT — le compte EXACT des fiches servies qui affirment « en service »
# sans qu'aucune source ne le dise. Arbitrage Franck du 2026-10-29 : « operational repasse en
# non-mesuré, plus un cliquet au compte exact des fiches déjà servies dans ce cas ».
#
# Pourquoi un COMPTE et pas une liste de dérogations comme `GEO_WAIVERS` : parce qu'il y en a
# 1 197. Une liste de 1 197 entrées ne se relit pas, donc ne garde rien ; un nombre qui ne peut
# que baisser, si. C'est la forme déjà éprouvée sur la dette i18n.
#
# CE QU'IL EMPÊCHE, et qui est arrivé trois fois : qu'une fiche NOUVELLE naisse en affirmant
# « en service » sans source. Le défaut a été trouvé à la main chaque fois — le lot DCmag
# (6 faux), les 361 invérifiables, puis les 8 fiches irlandaises de licence EPA du 2026-10-29,
# où le statut était forcé dans l'entrée du run. Une licence d'émissions prouve une
# installation autorisée, pas un site qui tourne.
#
# CE QU'IL NE DIT PAS : que les 1 197 soient fausses. Elles sont NON ÉTABLIES, ce qui n'est pas
# la même chose — et on ne remplace pas une affirmation non sourcée par une autre (la leçon des
# 35 : un flip de masse vers `announced` fabriquerait de faux « annoncés » sur de vrais sites en
# service). Elles baissent par la preuve, fiche à fiche, jamais par lot.
#
# DEUX FAÇONS D'ÊTRE SOURCÉ, et une seule suffit :
#   · le sidecar hebdomadaire de preuve de statut dit `verified` — des réseaux sont
#     interconnectés DANS ce bâtiment (PeeringDB) ; c'est une preuve intrinsèque d'exploitation ;
#   · la fiche porte un `project_status_provenance` qui justifie `operational` avec sa source.
STATUT_NON_SOURCE = 1189


def statut_gate(data_dir: Path) -> list[str]:
    """Refuse qu'une fiche de plus affirme « en service » sans source.

    Mesure dehors, décision dedans — comme le gate géo : la preuve PeeringDB demande du
    réseau, elle est produite par `pipelines.status_proof` dans un sidecar, et ce gate ne fait
    que lire et refuser.
    """
    newsroom = Path(os.environ.get("NEWSROOM_CAL",
                                   Path(__file__).resolve().parents[2] / "smdc-newsroom" / "calibration"))
    # 🔴 LE CORPUS COMPTÉ DOIT ÊTRE CELUI QUE LE SIDECAR DÉCRIT. Première version : sidecar
    # du newsroom, corpus de `data_dir` — donc, validé depuis le dépôt public (2 fiches de
    # fixture, aucune en service), un compte de 0 contre un cliquet de 1197, et le gate
    # réclamait de baisser le cliquet. Un gate qui compare deux populations différentes ne
    # mesure rien ; il faisait rougir `test_repository_data_passes_all_gates`, c'est-à-dire la
    # CI et tout clone frais.
    racine = next((r for r in (data_dir, newsroom)
                   if (r / "status-proof" / "status_check.json").is_file()), None)
    sidecar = None if racine is None else racine / "status-proof" / "status_check.json"
    if sidecar is None:
        # Même nuance que le gate géo : sans newsroom monté, `data_dir` est le jeu de fixtures
        # du dépôt et il n'y a pas de corpus réel à protéger. Exiger le sidecar ferait rougir
        # la CI et tout clone frais sur une mesure qui demande du réseau et un corpus privé.
        if not newsroom.is_dir():
            return []
        return ["GATE STATUT: sidecar status_check.json absent — lancer "
                "`python -m pipelines.status_proof.run` avant d'onboarder"]
    rapport = load_json(sidecar)
    # Le verdict du sidecar, pas un booléen : `verified` (des réseaux sont interconnectés dans
    # ce bâtiment) et `live_signal` (un signal d'exploitation observé) sont des preuves ;
    # `unverified` dit qu'on a CHERCHÉ et rien trouvé — ce n'est pas la même chose qu'une
    # fiche jamais mesurée, qui n'apparaît pas du tout.
    verifiees = {fid for fid, f in (rapport.get("fiches") or {}).items()
                 if f.get("verdict") in ("verified", "live_signal")}

    sans_source: list[str] = []
    for path in datacenter_paths(racine):
        dc = load_json(path)
        if (dc.get("identity") or {}).get("project_status") != "operational":
            continue
        if path.stem in verifiees:
            continue
        cote = path.with_name(path.stem + ".provenance.json")
        prov = (load_json(cote) if cote.is_file() else {}).get("project_status_provenance") or {}
        if prov.get("to") == "operational" and prov.get("source"):
            continue
        sans_source.append(path.stem)

    out: list[str] = []
    n = len(sans_source)
    if n > STATUT_NON_SOURCE:
        nouvelles = n - STATUT_NON_SOURCE
        out.append(
            f"GATE STATUT: {nouvelles} fiche(s) de plus affirment « en service » sans source "
            f"({n} contre un cliquet à {STATUT_NON_SOURCE}). Une licence, un annuaire ou un "
            f"défaut d'ingestion ne prouvent pas l'exploitation : poser "
            f"`project_status: \"unknown\"`, ou écrire un `project_status_provenance` qui cite "
            f"sa source. Dernières arrivées : {sorted(sans_source)[-5:]}"
        )
    elif n < STATUT_NON_SOURCE:
        # Le cliquet mord DANS LES DEUX SENS : un compte qui baisse sans que le nombre suive
        # laisse de la place pour une régression future sans rien casser. Même discipline que
        # la dette i18n — le chiffre doit rester EXACT pour rester un instrument.
        out.append(
            f"GATE STATUT: plus que {n} fiches sans source pour un cliquet à "
            f"{STATUT_NON_SOURCE} — baisser `STATUT_NON_SOURCE` à {n} dans engine/validate.py "
            f"pour que le cliquet garde sa place"
        )

    # Couverture : la mesure ne porte que sur les fiches « en service » — c'est son objet.
    # On la compare donc à CELLES-LÀ, et non au corpus entier : comparer au corpus ferait
    # crier le gate en permanence, et un gate qui crie toujours ne dit plus rien.
    # Une fiche en service jamais mesurée est déjà comptée comme non sourcée plus haut : le
    # refus est le bon. Mais on le NOMME, sinon un onboarding sans relance de la mesure
    # ressemble à une mesure propre.
    mesurees = set(rapport.get("fiches") or {})
    en_service = {p.stem for p in datacenter_paths(racine)
                  if (load_json(p).get("identity") or {}).get("project_status") == "operational"}
    jamais = sorted(en_service - mesurees)
    if jamais:
        out.append(f"GATE STATUT: preuve de statut périmée — {len(jamais)} fiche(s) « en "
                   f"service » n'ont jamais été mesurées ({jamais[:5]}) ; relancer "
                   f"`pipelines.status_proof.run`")
    if not out:
        print(f"GATE STATUT: {n} fiches servies affirment « en service » sans source "
              f"(cliquet {STATUT_NON_SOURCE}, il ne peut que baisser) — ce gate empêche la "
              f"{n + 1}ᵉ, il ne certifie pas les {n}", file=sys.stderr)
    return out


# 🔴 LE FILIGRANE DE BROUILLON NE DOIT PAS POUVOIR REVENIR DANS LE CORPUS SERVI.
# Pendant des mois, 3 113 fiches sur 3 275 ont porté dans leur résumé « BROUILLON … — à
# vérifier avant tout usage » / « DRAFT … — verify before use », et 1 702 disaient même
# « interne, hors corpus servi » alors qu'elles étaient servies et notées. Franck a fait
# nettoyer le 2026-10-30 puis le 2026-11-02 : le corpus est à ZÉRO.
#
# Ce gate existe pour que ça reste vrai. Le point d'écriture est un gabarit de pipeline
# (`pipelines/*/country.py`) : une vague suivante peut le réintroduire sans que personne ne
# relise 3 275 résumés. Un nettoyage sans gate est une fenêtre qui se rouvre.
#
# PAS DE CLIQUET ICI, et c'est voulu : le compte est à 0, donc la règle est « aucun », ce qui
# est plus simple à lire qu'un nombre et ne demande pas d'être tenu à jour.
#
# ⚠️ Les deux langues ne nomment pas la sonde pareil — « PROBE » en anglais, « SONDE » en
# français. Un motif qui n'en connaît qu'un laisse la moitié du corpus derrière lui : mesuré
# le 2026-11-02, le relevé s'arrêtait à 566 fiches sur 2 268 SANS RIEN SIGNALER.
FILIGRANES = re.compile(
    r"BROUILLON|\bDRAFT\b|^DEV\s+—|À vérifier|à vérifier|Verify before|verify before"
    r"|\bPROBE\b|\bSONDE\b|interne, hors corpus servi|internal, outside the served corpus",
    re.IGNORECASE | re.MULTILINE)


def retient_la_note(verdict: dict) -> bool:
    """La note est-elle retenue pour cette coordonnée ? — le prédicat, à UN endroit.

    `coord_hold` rend `{hold, portee, reason}` et `portee` sépare deux défauts que le booléen
    seul confond. La docstring du faisceau le dit : « le gate de service ne suspend la NOTE
    que si portee == "hold" — "carte" sert la note ».
      · "hold"  = coordonnée FAUSSE : ni carte ni note fiables.
      · "carte" = juste au km mais pas à l'échelle du bâtiment : pas de carte, NOTE SERVIE.
                  La re-mesure est bonne, seul le point d'annotation à 100 m ne l'est pas.

    🔴 J'ai câblé la rétention sur `verdict["hold"]` le 2026-11-02 et retenu la lettre de CINQ
    fiches dont la coordonnée est juste — dont `de-tkrz-greven-grv1`, que j'ai présentée comme
    la preuve que le gate marchait. La doctrine était écrite, en mots, dans la fonction que
    j'appelais ; j'ai pris le booléen. Le prédicat vit donc ici, avec sa table de vérité
    éprouvée, et le build l'APPELLE au lieu de la réécrire.
    """
    return bool(verdict.get("hold")) and verdict.get("portee") == "hold"


# 🔴 DETTE PAYÉE LE MÊME JOUR, ET C'EST LA RAISON DE LA GARDER VIDE PLUTÔT QUE DE LA SUPPRIMER.
# Ouverte le 2026-11-07 avec CINQ fiches dont le titre affirmait « ** INACTIVE ** » ou
# « - site closed » tandis que leur statut disait « stade non établi ». Elles ont été nettoyées
# dans la journée (newsroom `c9e2e466`) : marqueur de registre rangé dans le sidecar de
# provenance, titre servi débarrassé, statut inchangé. Vérifié sur le corpus servi : zéro nom
# porte encore un marqueur de fermeture.
#
# L'ensemble reste donc déclaré et VIDE. Un cliquet à zéro n'est pas décoratif : il refuse le
# PREMIER cas suivant, et il garde écrit pourquoi — sans quoi la prochaine ingestion qui
# recopie un libellé d'annuaire (« (closed) » de PeeringDB, « ** INACTIVE ** » d'EPA ECHO)
# repasserait sans bruit. Pour en sortir une légitimement, deux voies honnêtes et une seule
# interdite :
#   · sourcer la fermeture → `decommissioned` + `vintage.decommissioned_year` (+ le dossier) ;
#   · nettoyer le nom et garder le statut — le marqueur va dans la provenance, pas dans le titre ;
#   · JAMAIS inventer une année pour faire taire le gate.
DETTE_NOM_CONTREDIT_STATUT: set[str] = set()

_MARQUEURS_DE_FERMETURE = ("inactive", "closed", "decommission", "shut down", "ceased")


def nom_et_statut_gate(data_dir: Path = DATA_DIR) -> list[str]:
    """Le NOM servi ne peut pas affirmer une fermeture que le STATUT refuse d'affirmer.

    🔴 CE QUI A AMENÉ CE GARDE (2026-11-07). Huit fiches servaient « (closed) » ou
    « ** INACTIVE ** » dans leur nom — donc dans la balise de titre que Google montre — avec
    `project_status: "operational"`. Vérification faite : TROIS n'étaient pas fermées du tout
    (artefact de nom PeeringDB, interconnexions vérifiées) et leur nom a été nettoyé ; les
    CINQ autres sont passées à `unknown`, faute de source datant une fermeture.

    Reste alors une page qui se contredit elle-même : le titre AFFIRME « inactive », le champ
    de statut dit « stade non établi ». L'un des deux est faux, et le lecteur n'a aucun moyen
    de savoir lequel. `unknown` est le refus d'affirmer [[exemption-nest-pas-obligation]] : il
    ne peut pas cohabiter avec une affirmation dans le titre.

    ⚠️ CE GARDE NE DEMANDE PAS L'IMPOSSIBLE. Il n'exige pas qu'on source une fermeture — on
    n'invente pas une année pour faire taire un contrôle. Il exige que les DEUX surfaces
    disent la même chose, ce qui se règle aussi en nettoyant le nom. Et il porte une dette
    nommée des cinq cas connus : il refuse la SIXIÈME, il ne bloque pas le corpus d'aujourd'hui
    [[cliquet-nest-pas-verrou]].
    """
    fautives: list[str] = []
    for path in datacenter_paths(data_dir):
        ident = (load_json(path).get("identity") or {})
        nom = (ident.get("name") or "").lower()
        if not any(m in nom for m in _MARQUEURS_DE_FERMETURE):
            continue
        if ident.get("project_status") == "decommissioned":
            continue  # le nom et le statut disent la même chose : rien à redire
        if path.stem in DETTE_NOM_CONTREDIT_STATUT:
            continue
        fautives.append(path.stem)
    if fautives:
        return [
            "GATE NOM/STATUT: "
            f"{len(fautives)} fiche(s) servent un nom qui affirme une fermeture que leur "
            "statut n'affirme pas. Le titre dit « fermé », le champ dit autre chose : l'un "
            "des deux est faux. Deux issues — sourcer la fermeture (`decommissioned` + "
            "`vintage.decommissioned_year`), ou nettoyer le nom et laisser le statut. Jamais "
            "une année inventée : " + ", ".join(sorted(fautives))
        ]
    return []


def hors_service_gate(data_dir: Path = DATA_DIR) -> list[str]:
    """Une note d'ARCHIVE doit porter sa date, sinon elle se lit comme une note d'aujourd'hui.

    🔴 CE QUI A AMENÉ CE GARDE (2026-11-07). Huit fiches servies portaient « (closed) » ou
    « ** INACTIVE ** » dans leur nom, une note, et `project_status: "operational"` : nous
    affirmions que huit sites fermés étaient en exploitation. Décision de Franck : on NE
    retire pas — « fermé mais a existé, donc on garde la note » — on DÉCLARE la fermeture.

    Garder la note est tenable à une condition : qu'elle soit datée. Une note sans millésime
    sur un site hors service dit au lecteur « voilà l'état de ce site », au présent, alors
    qu'elle décrit un état révolu. C'est la même faute que de servir une mesure sans sa
    période. Donc : `decommissioned` SANS `vintage.decommissioned_year` est refusé.

    ⚠️ Et le garde se tait sur l'ensemble vide SANS mentir : s'il n'y a aucun site hors
    service, il n'a rien à dire — mais il DIT combien il en a vu, pour qu'un jour où
    l'ingestion en produirait mille on ne lise pas « ✓ » sans savoir sur quoi.
    """
    manquantes: list[str] = []
    vus = 0
    for path in datacenter_paths(data_dir):
        ident = (load_json(path).get("identity") or {})
        if ident.get("project_status") != "decommissioned":
            continue
        vus += 1
        annee = (ident.get("vintage") or {}).get("decommissioned_year")
        if not isinstance(annee, int):
            manquantes.append(path.stem)
    # 2026-11-11 : `withdrawn` (projet refusé ou retiré) obéit à la même règle — une note
    # d'archive sans date se lit comme le présent. La date est un JOUR (AAAA-MM-JJ).
    sans_date: list[str] = []
    for path in datacenter_paths(data_dir):
        ident = (load_json(path).get("identity") or {})
        if ident.get("project_status") != "withdrawn":
            continue
        jour = (ident.get("vintage") or {}).get("withdrawn_date")
        if not (isinstance(jour, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", jour)):
            sans_date.append(path.stem)
    out: list[str] = []
    if sans_date:
        out.append(
            "GATE HORS SERVICE: "
            f"{len(sans_date)} fiche(s) déclarent « withdrawn » sans "
            "`identity.vintage.withdrawn_date` (AAAA-MM-JJ). La note d'un projet refusé ou "
            "retiré est une ARCHIVE : sans date, elle se lit comme celle d'un projet en cours : "
            + ", ".join(sorted(sans_date)[:8]))
    if manquantes:
        return out + [
            "GATE HORS SERVICE: "
            f"{len(manquantes)} fiche(s) sur {vus} déclarent « decommissioned » sans "
            "`identity.vintage.decommissioned_year`. La note est conservée comme ARCHIVE : "
            "sans année, elle se lit comme une note d'aujourd'hui sur un site qui n'existe "
            "plus. Poser l'année de mise hors service et sa provenance dans `vintage.source` : "
            + ", ".join(sorted(manquantes)[:8])
        ]
    return out


def filigrane_gate(paths: list[Path]) -> list[str]:
    """Aucun résumé SERVI ne doit porter une mention de brouillon.

    Son mandat s'arrête au corpus servi : `validation/` (cohorte scellée) et les `.draft` en
    attente n'y sont pas, donc hors portée par construction et non par exception.
    """
    out: list[str] = []
    for path in paths:
        resume = ((load_json(path).get("identity") or {}).get("summary") or {})
        for langue, texte in sorted(resume.items()):
            if not isinstance(texte, str):
                continue
            m = FILIGRANES.search(texte)
            if m:
                out.append(
                    f"GATE FILIGRANE: {path.stem!r} ({langue}) porte « {m.group(0)} » dans son "
                    f"résumé : « {texte[:70]}… ». Un résumé servi ne dit pas qu'il est un "
                    f"brouillon — le gabarit doit DÉRIVER sa phrase des champs de la fiche "
                    f"(lieu + exploitant), pas recopier un boilerplate de pipeline"
                )
    return out


# ──────────────────────────────────────────────────────────────────────────────────────────
# Une traduction ne déplace pas une grandeur
# ──────────────────────────────────────────────────────────────────────────────────────────
# Les classes de PÉRIODE, par langue. Comparer les mots d'unité serait absurde — « g de CO2
# par kWh » et « g CO2 per kWh » ne s'écrivent pas pareil, et c'est normal. Mais une PÉRIODE
# est un fait : « par an » qui devient « per maand » fait mentir la fiche d'un facteur douze.
# C'est la faute qu'on a déjà publiée, en français, sur 74 synthèses.
# 🔴 CE GARDE NE COMPARE QUE LES NOMBRES, ET C'EST UNE DÉCISION, PAS UN OUBLI.
# J'ai essayé d'y ajouter les PÉRIODES — « par an » devenu « par mois » fait mentir une
# fiche d'un facteur douze, et c'est la faute qu'on a déjà publiée. Trois tentatives, trois
# vagues de faux positifs sur des traductions JUSTES : l'article anglais « an » compté comme
# l'année française ; « kilowatt-hour » qui se coupe là où « kilowattheure » ne se coupe pas ;
# « en moyenne annuelle » contre « as a 12-month average », puis « sur les douze derniers
# mois » où les deux mots ne se touchent même pas. 128 alertes, puis 13, puis 529.
# Une langue naturelle dit la même période de dix façons : un relevé mécanique ne les
# départage pas, et un garde qui crie sur du travail juste se fait désactiver dans la
# semaine — il aura coûté sa confiance sans avoir rien gardé.
# ANGLE MORT DÉCLARÉ, donc : une période changée SANS toucher à un nombre n'est pas vue
# ici. C'est l'échantillon humain de la relecture qui la couvre (une trentaine de fiches,
# stratifiées), et c'est le bon partage : la machine prend ce qui se vérifie à 100 %,
# l'humain prend ce qui demande de lire.


# 🔴 UN CHIFFRE COLLÉ À UNE LETTRE N'EST PAS UN NOMBRE : c'est une unité. « m3 » donnait un
# 3, « CO2 » un 2 — et le français qui écrit « 0,032 million de m3 » là où l'anglais écrit
# « cubic meters » perdait un nombre qui n'en était pas un. Le garde a crié deux fois sur
# deux traductions justes avant que je lise les textes.
_NOMBRE = re.compile(r"(?<![^\W\d_])\d[\d  .,\u202f\u00a0]*\d|(?<![^\W\d_])\d")


def _nombres(texte: str) -> list[float]:
    """Les nombres d'un texte, en VALEUR — pas en écriture.

    « 1 400 », « 1.400 » et « 1,400 » sont le même nombre écrit par trois langues ; « 370,4 »
    et « 370.4 » aussi. Comparer les chaînes ferait crier le garde sur chaque traduction
    juste. On compare donc ce que le lecteur COMPREND, pas ce qu'il lit.
    """
    sortie: list[float] = []
    for brut in _NOMBRE.findall(texte):
        net = brut.replace(" ", "").replace("\u202f", "").replace("\u00a0", "")
        # Le dernier séparateur est décimal s'il laisse 1 ou 2 chiffres derrière lui ;
        # sinon c'est un séparateur de milliers. Règle grossière, mais elle couvre les
        # trois écritures du corpus et se trompe dans le même sens des deux côtés.
        m = re.search(r"[.,](\d{1,2})$", net)
        if m:
            net = net[: m.start()].replace(".", "").replace(",", "") + "." + m.group(1)
        else:
            net = net.replace(".", "").replace(",", "")
        try:
            sortie.append(float(net))
        except ValueError:
            continue
    return sorted(sortie)


# « douze mois » et « annuel » sont la MÊME période, et les deux éditions ont le droit de
# choisir l'une ou l'autre : le français dit « en moyenne annuelle » là où l'anglais dit
# « as a 12-month average ». Sans cette normalisation le garde criait sur des traductions
# justes — et un garde qui crie sur du travail juste finit désactivé.
_DOUZE_MOIS = re.compile(
    r"\b(?:12|douze|twelve|twaalf)[-  \u202f\u00a0]?(?:mois|months?|maanden?)\b",
    re.IGNORECASE,
)


def _periodes(texte: str, langue: str) -> dict[str, int] | None:
    """Le compte de chaque classe de période, lu avec le vocabulaire de SA langue.

    Rend `None` pour une langue dont on n'a pas le vocabulaire : on ne compare pas ce qu'on
    ne sait pas lire. Un garde muet sur une langue inconnue vaut mieux qu'un garde qui crie
    parce qu'il ne la parle pas.
    """
    vocabulaire = _PERIODES.get(langue)
    if vocabulaire is None:
        return None
    compte = {cle: 0 for cle in _CLASSES}
    texte, douze = _DOUZE_MOIS.subn(" ", texte)
    compte["an"] += douze
    for mot in _MOT.findall(texte.lower()):
        for cle, mots in vocabulaire.items():
            if mot in mots:
                compte[cle] += 1
    return compte


def grandeurs_gate(data_dir: Path) -> list[str]:
    """Les grandeurs d'une synthèse doivent être les mêmes dans toutes ses langues.

    🔴 POURQUOI CE GARDE EST SUR LE SERVI ET PAS DANS LA CHAÎNE DE TRADUCTION. Le pipeline a
    déjà sa propre vérification, et elle est bonne. Mais un contrôle qui vit chez celui qui
    produit vérifie que le producteur a fait ce qu'il CROIT avoir fait ; celui-ci vérifie ce
    que le lecteur VERRA, et il tient encore si la chaîne de traduction change ou si
    quelqu'un corrige une fiche à la main six mois plus tard.

    Décision de Franck, 2026-11-03 : les synthèses néerlandaises sont une TRADUCTION du
    français, pas une seconde génération — « un observatoire ne peut pas dire deux choses du
    même site selon la langue ». Ce garde est la forme mécanique de cette décision : si les
    deux éditions ne portent pas les mêmes grandeurs, elles ne disent pas la même chose.

    Et il ne se vérifie pas par échantillon. Un tirage de trente fiches laisserait passer
    98 % d'un « par an » devenu « par mois » — la faute exacte qu'on a déjà publiée sur 74
    synthèses. Toutes les fiches, ou rien.

    ANGLE MORT DÉCLARÉ : on ne compare NI les mots d'unité (« g de CO2 par kWh » / « g CO2
    per kWh » : ils doivent différer), NI l'ordre des nombres (une langue a le droit de
    tourner sa phrase autrement). On compare l'ENSEMBLE des valeurs et le compte des classes
    de période. Une unité remplacée par une autre de même période (kWh → MWh) passerait :
    c'est le trou, il est connu, et il demanderait un dictionnaire d'unités par langue.
    """
    problemes: list[str] = []
    for chemin in datacenter_paths(data_dir):
        fiche = load_json(chemin)
        syntheses = fiche.get("synthesis") or {}
        if not isinstance(syntheses, dict):
            continue
        for nom, bloc in syntheses.items():
            if not isinstance(bloc, dict):
                continue
            textes = {k: v for k, v in bloc.items() if isinstance(v, str) and len(k) == 2}
            if "fr" not in textes or len(textes) < 2:
                continue
            ref_n = _nombres(textes["fr"])
            for langue, texte in textes.items():
                if langue == "fr":
                    continue
                n = _nombres(texte)
                # 🔴 ON EXIGE LA SURVIE DES NOMBRES DU FRANÇAIS, PAS L'ÉGALITÉ DES DEUX
                # ENSEMBLES. Première version : égalité stricte. Elle a crié 128 fois sur le
                # corpus réel — et c'étaient des traductions JUSTES : le français écrit
                # « sur douze mois » en lettres là où l'anglais écrit « a 12-month average ».
                # Un nombre EN PLUS dans l'autre langue est donc légitime ; un nombre du
                # français qui disparaît ou qui change, jamais. Le trou est déclaré : une
                # traduction qui ajoute un chiffre faux passerait.
                manquants = [x for x in ref_n if x not in n]
                if manquants:
                    problemes.append(
                        f"GATE GRANDEUR: {chemin.stem} · synthesis.{nom} · {langue.upper()} "
                        f"a perdu ou modifié {len(manquants)} nombre(s) du français : "
                        f"{manquants[:4]} — une mesure qui bouge en traduction est un errata "
                        f"sur une page qui note un site réel"
                    )
    return problemes


def run_gates(data_dir: Path = DATA_DIR, today: date | None = None) -> list[str]:
    """Return the list of gate violations (empty = all gates pass)."""
    today = today or date.today()
    problems: list[str] = []

    dc_schema = load_json(data_dir / "schema" / "datacenter.schema.json")
    meth_schema = load_json(data_dir / "schema" / "methodology.schema.json")

    try:
        methodology = load_methodology(data_dir)
    except GateError as e:
        return [str(e)]

    problems += _schema_errors(methodology, meth_schema, "methodology")
    if problems:
        return problems  # structural failures make the rest unreliable

    # Gate 3 — cross-field methodology coherence
    indicators = methodology["indicators"]
    ids = [i["id"] for i in indicators]
    if len(ids) != len(set(ids)):
        problems.append("GATE 3: duplicate indicator ids in methodology")
    if abs(sum(p["weight"] for p in methodology["pillars"]) - 1.0) > 1e-9:
        problems.append("GATE 3: pillar weights do not sum to 1")
    for pillar in methodology["pillars"]:
        s = sum(i["weight_in_pillar"] for i in indicators if i["pillar"] == pillar["id"])
        if abs(s - 1.0) > 1e-9:
            problems.append(f"GATE 3: indicator weights in pillar {pillar['id']} sum to {s}, not 1")
    pillar_ids = {p["id"] for p in methodology["pillars"]}
    for ind in indicators:
        if ind["pillar"] not in pillar_ids:
            problems.append(f"GATE 3: indicator {ind['id']} references unknown pillar {ind['pillar']}")
        if "vulnerability_cannot_improve_score" in ind.get("constraints", []):
            # Ethical lock, executable (methodology-lead rule 2026-07-05): scores must be
            # non-increasing along the declared vulnerability order — vulnerability may
            # lower a score or dent confidence, never raise it. A corpus property test
            # (test_ethical_constraints.py) additionally checks d(site_score)/d(vulnerability) <= 0.
            order = ind.get("vulnerability_order", [])
            categories = ind.get("normalization", {}).get("categories")
            if categories is None:
                problems.append(
                    f"GATE 3: indicator {ind['id']}: vulnerability_cannot_improve_score requires a "
                    "categorical normalization"
                )
            elif sorted(order) != sorted(categories):
                problems.append(
                    f"GATE 3: indicator {ind['id']}: vulnerability_order {order} must cover exactly "
                    f"the normalization categories {sorted(categories)}"
                )
            else:
                scores = [categories[c] for c in order]
                if any(a < b for a, b in zip(scores, scores[1:])):
                    problems.append(
                        f"GATE 3: indicator {ind['id']}: ethical lock violated — scores along the "
                        f"vulnerability order {order} are {scores}, but a more vulnerable profile can "
                        "never score higher (vulnerability_cannot_improve_score, framing note section 9)"
                    )
    declarative_ids = {i["id"] for i in indicators if i["nature"] == "declarative"}
    # Gate 8 protects the SCORE, so it is scoped to MVP indicators (out-of-MVP tier-3 rows
    # like E5/W5 are unscored and exempt).
    project_ids = {i["id"] for i in indicators if i["block"] == "project" and i["mvp"]}
    # …et un indicateur INFORMATIONNEL relève de la même exemption, pour la même raison : il est
    # mvp (sinon il n'atteindrait pas la fiche) mais NON NOTÉ — son `not_collected` ne retire rien
    # au score et rien à la couverture, donc il ne peut flatter personne. Le compter ici aurait
    # ajouté en catimini une OBLIGATION DE COLLECTE avant publication (lire le document
    # d'urbanisme de chaque fiche), là où la décision prise était d'ajouter deux faits INERTES.
    # Un gate qui change les conditions de publication sans que personne ne l'ait décidé est un
    # gate qui dépasse son mandat (constaté le 2026-10-06 en passant en v0.3.0).
    scored_pp_ids = {i["id"] for i in indicators
                     if i["block"] in ("project", "process") and i["mvp"] and not i.get("informational")}

    def _axe_projet_note(dc: dict, methodology: dict) -> bool:
        """L'axe projet gagne-t-il une lettre ? DÉRIVÉ, jamais lu dans un champ.

        On passe par `score_datacenter`, le même code qui produit l'artefact servi : si la
        règle réimplémentait la couverture, elle dériverait de l'affichage (vérifié — un
        comptage naïf donnait 3 fautes là où le calcul pondéré du moteur en donne 1).
        Une fiche au jeu d'indicateurs incomplet n'est pas scorable ; le contrôle de schéma
        l'a déjà signalée, donc on ne la juge pas deux fois.
        """
        try:
            note = score_datacenter(dc, methodology)["grades"]["project_process"].get("grade")
        except (KeyError, TypeError, ValueError):
            return False
        return note in ("A", "B", "C", "D", "E")

    for path in datacenter_paths(data_dir):
        dc = load_json(path)
        label = path.name
        errs = _schema_errors(dc, dc_schema, label)
        problems += errs
        if errs:
            continue

        if dc["id"] != path.stem:
            problems.append(f"GATE 1: {label}: id {dc['id']!r} does not match the filename")

        # every methodology indicator must appear exactly once (missing is declared, never implicit)
        seen = [e["id"] for e in dc["indicators"]]
        if sorted(seen) != sorted(ids):
            problems.append(
                f"GATE 1: {label}: indicator set differs from methodology "
                f"(missing={sorted(set(ids) - set(seen))}, extra={sorted(set(seen) - set(ids))}) — "
                "declare unavailable indicators explicitly with status: missing"
            )
            continue

        # Gate 2 — declarative never silently measured
        for e in dc["indicators"]:
            if e["id"] in declarative_ids and e["status"] == "measured" and "verification_source" not in e:
                problems.append(
                    f"GATE 2: {label}: {e['id']} is declarative but marked 'measured' without "
                    "verification_source — announced and measured are never merged"
                )

        # Gate 8 — extraction coherence (RED FLAG fix 2026-07-09): "dossier available +
        # substance unexamined" is an impossible state by construction (philosophy A-18).
        entries_by_id = {e["id"]: e for e in dc["indicators"]}
        t2 = entries_by_id.get("T2", {})
        dossier_available = t2.get("status") == "measured" and t2.get("value") in ("full_dossier_online", "partial")
        for e in dc["indicators"]:
            # (a) `missing` is an opacity accusation — it may only be levelled at a project
            #     indicator once a read-trace (source) proves we actually opened the dossier.
            if dossier_available and e["id"] in project_ids and e["status"] == "missing" and "source" not in e:
                problems.append(
                    f"GATE 8: {label}: {e['id']} is 'missing' (verified-absent) while T2 attests a public "
                    "dossier, but carries no source proving it was read — attach the read-trace, or mark it "
                    "'not_collected' until harvested. An E of non-extraction is as false as an A of complacency."
                )
            # (b) 🔴 CETTE RÈGLE A ÉTÉ MORTE PENDANT TOUTE LA VIE DU PROJET (constaté 2026-10-26).
            #     Elle ne se déclenchait que si `publication.status == "published"`. Or ce champ
            #     vaut `draft` sur les 3 267 fiches servies et sur les 3 824 de la source qui le
            #     portent — AUCUNE n'est `published`. Le garde-fou était désarmé par la valeur
            #     par défaut de son propre interrupteur, et rien ne le signalait.
            #
            #     Le défaut de fond : « publié » et « complet » partageaient un seul booléen. Le
            #     site publie 3 267 fiches et n'en considère aucune comme publiée, donc armer la
            #     règle telle quelle aurait refusé 3 266 fiches sur 3 267 (médiane : 9 manques
            #     sur 9) — ce n'est pas une barrière à rallumer, c'est la spécification d'un
            #     corpus qu'on n'a pas.
            #
            #     ON NE STOCKE QUE LES DÉCISIONS, ON DÉRIVE LE RESTE (arbitrage Franck
            #     2026-10-26). « Servie ou non » et « lettre retenue ou non » sont des décisions,
            #     portées ailleurs et correctement (présence du fichier, `data/veille.json`,
            #     `provisional_band`). La COMPLÉTUDE, elle, n'est pas une décision : elle se
            #     calcule. La règle demande donc à `score_datacenter` — la source unique de la
            #     dérivation, celle qui produit l'artefact — si l'axe projet gagne vraiment une
            #     lettre, au lieu de croire un drapeau que personne ne met à jour.
            #
            #     Ce qu'elle interdit désormais : une LETTRE sur l'axe projet alors qu'un de ses
            #     indicateurs notés n'a jamais été collecté. Une fiche sans axe projet reste
            #     parfaitement valide — elle affiche « données insuffisantes », ce qui est vrai.
            if e["id"] in scored_pp_ids and e["status"] == "not_collected" and _axe_projet_note(dc, methodology):
                problems.append(
                    f"GATE 8: {label}: {e['id']} is 'not_collected' while the project axis EARNS a "
                    "letter — a project grade may not rest on an indicator that was never collected. "
                    "Harvest it (announced/measured), or mark it 'missing' (verified absent) with its "
                    "read-trace."
                )

        # Gate 9 — L2 power provenance (memo signed Franck 2026-07-19): a 'measured' L2 may
        # only rest on a regulatory-tier power figure. Canonical tier definition:
        # pipelines/labels/power_tier.py (patterns mirrored here — the engine imports nothing
        # from pipelines; unify the day the schema gains a structured power_source field).
        # Lenient on unattributed prose: 'unknown' is never silently promoted NOR accused.
        l2e = entries_by_id.get("L2", {})
        if l2e.get("status") == "measured":
            _t = (l2e.get("source") or {}).get("title", "")
            _m = _L2_POWER_PROSE.search(_t)
            if _m and not _L2_REGULATORY.search(_m.group(1)):
                problems.append(
                    f"GATE 9: {label}: L2 is 'measured' on a non-regulatory power figure "
                    f"({_m.group(1).strip()[:50]!r}) — an aggregator/press/operator MW is an "
                    "unverified third-party claim: mark L2 'announced' (declarative cap + "
                    "confidence penalty) until a regulatory register (EED) confirms it"
                )

        # Gate 10 — estimated coherence (decision Franck 2026-07-27, option 1c): a model-derived
        # power figure must be tagged end-to-end. If identity.power_mw is our estimate, every
        # value-bearing L2 derived from it is 'estimated' too — never served as a fact; and an
        # L2 marked 'estimated' requires the identity marker so the fiche renders the "~ estimé"
        # chip. One untagged side = the silent-fact leak this gate exists to kill.
        pm_status = (dc.get("identity") or {}).get("power_mw_status")
        l2_status = l2e.get("status")
        if pm_status == "estimated" and l2_status in ("measured", "announced"):
            problems.append(
                f"GATE 10: {label}: identity.power_mw is 'estimated' but L2 is {l2_status!r} — "
                "an indicator fed by our own model output must carry status 'estimated'"
            )
        if l2_status == "estimated" and pm_status != "estimated":
            problems.append(
                f"GATE 10: {label}: L2 is 'estimated' but identity.power_mw_status is "
                f"{pm_status!r} — tag the identity value so the fiche renders the estimate marker"
            )

        # Gate 4 removed (2026-07-15): grades publish directly — no prior-notice hold.
        # The permanent response space (publication.operator_response) is untouched.

        # Gate 5 — anteriority
        if not dc["id"].startswith(FICTIONAL_PREFIX) and methodology["status"] != "published":
            problems.append(
                f"GATE 5: {label}: a real data center cannot be scored against a {methodology['status']} "
                "methodology — freeze and tag v0.1.0 first (plan phase 5)"
            )
        # UN JOURNAL GARDE SES VIEILLES VERSIONS — C'EST SA RAISON D'ÊTRE. Ce gate contrôlait
        # CHAQUE entrée, donc il exigeait que l'historique soit RÉÉCRIT à chaque montée de
        # méthodo : un re-score APPEND, il ne retouche pas le passé, si bien que le remède
        # imprimé ne pouvait jamais satisfaire le gate. Ce qui doit être à jour, c'est la TÊTE
        # du journal — l'état publié aujourd'hui doit avoir été calculé sous la méthodo active ;
        # les entrées antérieures référencent à bon droit la version en vigueur ce jour-là, et
        # noter cette version n'a de sens que si elle peut différer (constaté le 2026-10-06).
        if (tete := (dc["score_history"] or [None])[-1]) and \
                tete["methodology_version"] != methodology["version"]:
            problems.append(
                f"GATE 5: {label}: score_history[{len(dc['score_history']) - 1}] (la plus récente) "
                f"references methodology {tete['methodology_version']} but the active version is "
                f"{methodology['version']} — {STALE_METHODOLOGY_REMEDY}"
            )
        for n, entry in enumerate(dc["score_history"]):
            # journal gate
            if n >= 1 and not entry.get("rationale"):
                problems.append(
                    f"JOURNAL GATE: {label}: score_history[{n}] has no rationale — every revision "
                    "after the initial scoring must say why the grade moved"
                )

    # Watchlist (A-19) — sourced facts, never a grade
    watchlist_schema = load_json(data_dir / "schema" / "watchlist.schema.json")
    seen_watch_ids: set[str] = set()
    for path in watchlist_paths(data_dir):
        entries = load_json(path)
        label = f"watchlist/{path.name}"
        errs = _schema_errors(entries, watchlist_schema, label)
        problems += errs
        if errs:
            continue
        for entry in entries:
            leak = _grade_leak(entry)
            if leak:
                problems.append(
                    f"GATE (A-19): {label}: entry {entry.get('id')!r} carries a grade-like key "
                    f"{leak!r} — the watchlist publishes facts only, never a note"
                )
            if entry["id"] in seen_watch_ids:
                problems.append(f"GATE 1: {label}: duplicate watchlist id {entry['id']!r}")
            seen_watch_ids.add(entry["id"])

    problems += geo_gate(data_dir)
    problems += statut_gate(data_dir)
    problems += hors_service_gate(data_dir)
    problems += nom_et_statut_gate(data_dir)
    problems += filigrane_gate(datacenter_paths(data_dir))
    problems += grandeurs_gate(data_dir)

    return problems


def main() -> int:
    problems = run_gates()
    n_dc = len(datacenter_paths())
    if problems:
        print(f"validate: {len(problems)} gate violation(s) across {n_dc} datacenter file(s):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"validate: all gates pass ({n_dc} datacenter file(s), methodology {load_methodology()['version']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
