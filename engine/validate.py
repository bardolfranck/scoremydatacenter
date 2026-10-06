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
    "fr-communaute-d-agglomeration-cannes-pays-de-lerins-cacpl": "2026-09-29 — micro-DC PoliCloud décentralisé, pas d'emprise unique ; attente arbitrage Franck (suppression ou veille)",
    "fr-microsoft": "2026-09-29 — Petit-Landau : greenfield agricole ~36 ha le long du Rhin, site réel non localisé (permis suspendus MRAe) ; coordonnée au niveau commune, indicateurs de point en not_collected ; déblocage = plan cadastral du dossier d'enquête",
    "ch-green-datacenter-zurich-metro": "2026-09-29 — périmètre EU, correction à cadrer",
    "ch-stack-infrastucture-zur01": "2026-09-29 — périmètre EU, correction à cadrer",
    "ch-stack-infrastucture-zurl1": "2026-09-29 — périmètre EU, correction à cadrer",
    "es-aws-aragon-villanueva-de-gallego": "2026-09-29 — périmètre EU, correction à cadrer",
    "es-aws-aragon-el-burgo-de-ebro": "2026-09-29 — périmètre EU, correction à cadrer",
    "es-meta-talavera-de-la-reina": "2026-09-29 — périmètre EU, correction à cadrer",
}


SEUIL_POSITION_M = 1.0   # sous le mètre, deux fiches désignent le même point, pas deux points


def _metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance plane locale — à l'échelle du mètre, la projection ne coûte rien."""
    dy = (lat1 - lat2) * 111_320.0
    dx = (lon1 - lon2) * 111_320.0 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dx, dy)


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
    sidecar = next((c for c in (data_dir / "geo-audit" / "centroid-check.json",
                                newsroom / "geo-audit" / "centroid-check.json") if c.is_file()), None)
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
    covered = ((report.get("meta") or {}).get("counts") or {}).get("testées")
    corpus = len(datacenter_paths(data_dir))
    if covered is None:
        out.append("GATE GÉO: le sidecar ne dit pas combien de fiches ont été testées")
    elif covered < corpus:
        out.append(f"GATE GÉO: détecteur de centroïde périmé — {covered} fiches testées pour "
                   f"{corpus} au corpus ; relancer avant d'onboarder")
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
            # (b) `not_collected` is a transitory draft state — it can never reach the published repo.
            if e["id"] in scored_pp_ids and e["status"] == "not_collected" and dc["publication"]["status"] == "published":
                problems.append(
                    f"GATE 8: {label}: {e['id']} is 'not_collected' but the DC is published — every project/"
                    "process indicator must be harvested (announced/measured) or verified-absent (missing) "
                    "before publication"
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
