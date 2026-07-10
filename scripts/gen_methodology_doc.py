# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Generate the citable methodology document from the versioned methodology.json.

The doctrine is prose (edited here); the 24-indicator grid is DATA (methodology.json)
rendered into the doc — so the document and the site can never diverge. Reproducible:
`python scripts/gen_methodology_doc.py` rewrites docs/methodologie-notation.md.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M = json.loads((ROOT / "site/public/data/methodology.json").read_text())
OUT = ROOT / "docs/methodologie-notation.md"

BLOCK = {"base": "Site (subi)", "project": "Projet (choisi)", "process": "Processus"}
DIR = {"lower_is_better": "plus bas = mieux", "higher_is_better": "plus haut = mieux",
       "encoded_in_scoring": "qualitatif", "non_monotonic": "nuancé"}
pct = lambda x: f"{round(x * 100)} %"


def ref(i: dict) -> str:
    tb = i.get("threshold_basis") or {}
    label = tb.get("reference") or tb.get("justification") or "—"
    return f"[{label}]({tb['url']})" if tb.get("url") else label


def grid() -> str:
    out = []
    for p in M["pillars"]:
        items = [i for i in M["indicators"] if i["pillar"] == p["id"] and i.get("mvp")]
        if not items:
            continue
        out.append(f"\n### {p['label']['fr']} — {pct(p['weight'])}\n")
        out.append("| Indicateur | Bloc | Coef. | Sens | Référentiel de seuil | Source |")
        out.append("|---|---|---|---|---|---|")
        for i in items:
            coef = pct(i["weight_in_pillar"]) if i.get("weight_in_pillar") is not None else "—"
            src = ", ".join(i.get("sources") or []) or "—"
            out.append(f"| **{i['label']['fr']}** | {BLOCK.get(i['block'], i['block'])} | {coef} "
                       f"| {DIR.get(i['direction'], i['direction'])} | {ref(i)} | {src} |")
    return "\n".join(out)


REFERENCES = [
    ("ISO/IEC 30134 (2 PUE · 3 REF · 4 CUE) — indicateurs de performance des centres de données", "https://www.iso.org/standard/63451.html"),
    ("EU Code of Conduct for Data Centres (JRC)", "https://e3p.jrc.ec.europa.eu/communities/data-centres-code-conduct"),
    ("Directive Efficacité Énergétique (EED) 2023/1791", "https://eur-lex.europa.eu/eli/dir/2023/1791/oj"),
    ("WRI Aqueduct — stress hydrique de bassin", "https://www.wri.org/aqueduct"),
    ("Directive Cadre sur l'Eau 2000/60/CE — état des masses d'eau", "https://eur-lex.europa.eu/eli/dir/2000/60/oj"),
    ("ADEME Base Empreinte — facteurs d'émission du réseau", "https://base-empreinte.ademe.fr/"),
    ("RTE eCO2mix / Caparéseau — carbone et capacité du réseau", "https://www.rte-france.com/eco2mix"),
    ("Cadre « Social Licence to Operate » — acceptabilité sociale des projets", "https://en.wikipedia.org/wiki/Social_license"),
]
piliers = " · ".join(f"{p['label']['fr']} ({pct(p['weight'])})" for p in M["pillars"])
scale = " · ".join(f"{t['grade']} ≥ {t['min']}" for t in sorted(M["grade_thresholds"], key=lambda t: -t["min"]))

DOC = f"""# Méthodologie de notation — ScoreMyDataCenter

**The data center acceptability-risk score** · observatoire indépendant · fondé par Franck Bardol
Version **{M['version']}** · {M.get('published_at') or 'brouillon non figé'} · licence **CC BY-SA 4.0**
Document généré depuis `methodology.json` (la grille est de la donnée versionnée, pas de la prose).

> Document de travail du calibrage — **PROVISOIRE**, pédagogique et citable.

---

## 1. La note, comme un bulletin scolaire

Un data center reçoit un bulletin. Les cinq **piliers** sont les matières : {piliers}.
Chaque matière a des **contrôles** — les indicateurs.

**Deux bulletins, en réalité.** Un pour le **SITE** — le terrain que le projet subit (carbone du réseau,
stress hydrique, foncier) — et un pour le **PROJET & PROCESSUS** — ce que l'opérateur choisit (efficacité,
refroidissement, concertation, transparence). Plus une information qu'un vrai bulletin n'a pas : la
**confiance documentaire**. Elle dit à quel point le correcteur a pu vraiment corriger la copie. Sous
40 % de couverture, la note ne s'affiche pas : on écrit « données insuffisantes ». **On ne note pas l'inconnu.**

**L'échelle A–E :** {scale}.

## 2. Comment se calcule la note — une double moyenne

`score = Σ aᵢ·Fᵢ` est une double moyenne, exactement la logique du bulletin.
**Étage 1** : dans chaque pilier, les indicateurs sont moyennés selon leur coefficient interne.
**Étage 2** : les scores de piliers sont moyennés selon les poids de piliers.
**Principe clé — pas de croisement** : un indicateur n'appartient qu'à une matière (E1 → Énergie,
W2 → Eau) et ne compte jamais ailleurs.

**Exemple** (2 piliers, 4 indicateurs, scores normalisés 0–100) :
- Énergie (poids 25 %) — carbone 80 (coef 0,6) · PUE 40 (coef 0,4) → 80×0,6 + 40×0,4 = **64**
- Eau (poids 20 %) — stress 30 (coef 0,7) · conso 50 (coef 0,3) → 30×0,7 + 50×0,3 = **36**
- Global (poids renormalisés 25/45 et 20/45) → 64×0,56 + 36×0,44 ≈ **52** → lettre **C**.

## 3. Deux notes — et ce n'est pas la moyenne des piliers

Les deux notes de tête agrègent **par BLOC**, pas par pilier. Score **SITE** = indicateurs « base » (subis) ;
score **PROJET & PROCESSUS** = « projet » + « processus » (choisis). Les **sous-scores par pilier**, eux,
regroupent chaque thématique en mêlant subi et choisi. Les deux découpages sont orthogonaux :
**une note ne se lit pas comme la moyenne des piliers affichés.**

## 4. De la mesure à la note — deux familles de seuils

Chaque indicateur transforme une valeur brute en sous-score 0–100 via un seuil, posé de deux manières —
et la distinction est **déclarée** :

- **Famille A — référentiel externe** : on s'ancre sur un standard existant, sourcé et défendable
  (ISO 30134 pour l'efficacité, Directive Cadre sur l'Eau pour l'état des masses d'eau, WRI Aqueduct
  pour le stress hydrique…).
- **Famille B — ratio éditorial déclaré** : là où aucune norme n'existe (« quelle taille est trop
  grosse ? »), on n'invente pas un seuil absolu — on exprime un **ratio contextuel** et on **assume le
  choix éditorial**.

**Règle : maximiser le référentiel, minimiser l'éditorial — et le déclarer.**

## 5. La grille — les 24 indicateurs
{grid()}

## 6. Ce qui est verrouillé par construction

- **Annoncé ≠ mesuré** : un chiffre déclaré par l'opérateur est tagué « annoncé », noté avec prudence, re-vérifiable ex-post.
- **Plancher de transparence** : divulguer une donnée ne peut jamais dégrader la note par rapport à l'avoir cachée.
- **Verrou éthique** : la vulnérabilité d'une commune ne peut jamais améliorer la note d'un projet.
- **Firewall « projet ≠ note »** : on aide le projet, jamais la note. La note publique ne bouge que si le **projet réel** change (faits sourcés, re-scoring tracé au journal d'audit) — jamais parce qu'un opérateur a payé.
- **Gouvernance** : toute évolution de la grille passe par une version taguée et un changelog justifié et signé.

## 7. Statut, limites & calibration

Cette version est **préliminaire et pourra évoluer**.
Ce que la note **n'est pas** : un modèle prédictif validé statistiquement, ni un oracle.
Ce qu'elle **est** : une grille experte, sourcée, versionnée et reproductible.

- **Poids et seuils provisoires** — ils sont calibrés par **validation rétrospective** sur des cas au dénouement connu (projets acceptés / abandonnés), pas affirmés a priori.
- **Traçabilité** — chaque note est datée et rattachée à une version de méthode ; un « A » signifie « le meilleur atteignable aujourd'hui ».

## 8. Références & standards

{chr(10).join(f"- [{label}]({url})" for label, url in REFERENCES)}

---

*Franck Bardol · ScoreMyDataCenter · méthode {M['version']} · CC BY-SA 4.0.*
*Grille de référence machine-lisible : `site/public/data/methodology.json`. Doc reproductible : `python scripts/gen_methodology_doc.py`.*
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(DOC)
print(f"wrote {OUT} ({len(DOC.split())} words)")
