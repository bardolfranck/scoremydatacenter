# Méthodologie de notation — ScoreMyDataCenter

**The data center acceptability-risk score** · observatoire indépendant · fondé par Franck Bardol
Version **0.1.0-draft** · brouillon non figé · licence **CC BY-SA 4.0**
Document généré depuis `methodology.json` (la grille est de la donnée versionnée, pas de la prose).

> Document de travail du calibrage — **PROVISOIRE**, pédagogique et citable.

---

## 1. La note, comme un bulletin scolaire

Un data center reçoit un bulletin. Les cinq **piliers** sont les matières : Énergie (25 %) · Eau (20 %) · Foncier & biodiversité (20 %) · Impact local (20 %) · Transparence & gouvernance (15 %).
Chaque matière a des **contrôles** — les indicateurs.

**Deux bulletins, en réalité.** Un pour le **SITE** — le terrain que le projet subit (carbone du réseau,
stress hydrique, foncier) — et un pour le **PROJET & PROCESSUS** — ce que l'opérateur choisit (efficacité,
refroidissement, concertation, transparence). Plus une information qu'un vrai bulletin n'a pas : la
**confiance documentaire**. Elle dit à quel point le correcteur a pu vraiment corriger la copie. Sous
40 % de couverture, la note ne s'affiche pas : on écrit « données insuffisantes ». **On ne note pas l'inconnu.**

**L'échelle A–E :** A ≥ 80 · B ≥ 65 · C ≥ 50 · D ≥ 35 · E ≥ 0.

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

### Énergie — 25 %

| Indicateur | Bloc | Coef. | Sens | Référentiel de seuil | Source |
|---|---|---|---|---|---|
| **Intensité carbone du réseau local** | Site (subi) | 15 % | plus bas = mieux | [ADEME Base Empreinte — grid emission factors](https://base-empreinte.ademe.fr/) | RTE eCO2mix |
| **Capacité / proximité de raccordement** | Site (subi) | 35 % | qualitatif | — | RTE Caparéseau, S3REnR |
| **Congestion / file d'attente réseau** | Site (subi) | 25 % | qualitatif | — | RTE / ODRÉ |
| **PUE (efficacité énergétique annoncée)** | Projet (choisi) | 15 % | plus bas = mieux | — | ICPE filing, press |

### Eau — 20 %

| Indicateur | Bloc | Coef. | Sens | Référentiel de seuil | Source |
|---|---|---|---|---|---|
| **Stress hydrique de la zone** | Site (subi) | 30 % | qualitatif | [ZRE zoning + Propluvia restriction levels (French regulatory framework)](https://www.eaufrance.fr/) | ZRE, Propluvia, Hub'Eau |
| **État de la masse d'eau** | Site (subi) | 20 % | qualitatif | [EU Water Framework Directive ecological status classes](https://environment.ec.europa.eu/topics/water/water-framework-directive_en) | Hub'Eau |
| **Pression de prélèvement du bassin** | Site (subi) | 20 % | qualitatif | — | BNPE, Hub'Eau |
| **Refroidissement + volume d'eau annoncé** | Projet (choisi) | 20 % | qualitatif | — | ICPE filing |

### Foncier & biodiversité — 20 %

| Indicateur | Bloc | Coef. | Sens | Référentiel de seuil | Source |
|---|---|---|---|---|---|
| **Recouvrement / distance zones protégées** | Site (subi) | 20 % | qualitatif | — | INPN, Natura 2000, ZNIEFF |
| **Statut du sol (artificialisé / ENAF / agricole)** | Site (subi) | 35 % | qualitatif | [Cerema artificialization inventory + ZAN framework categories](https://artificialisation.developpement-durable.gouv.fr/) | Cerema, RPG |
| **Continuités écologiques (TVB)** | Site (subi) | 20 % | qualitatif | — | SRADDET, INPN |
| **Surface au sol du projet** | Projet (choisi) | 15 % | plus bas = mieux | — | ICPE filing, building permit |
| **Mesures ERC / récupération de chaleur** | Projet (choisi) | 10 % | qualitatif | [ISO/IEC 30134-6 — Energy Reuse Factor (ERF), le référentiel international de la réutilisation de la chaleur fatale des data centers](https://www.iso.org/standard/79095.html) | operator, permitting file |

### Impact local — 20 %

| Indicateur | Bloc | Coef. | Sens | Référentiel de seuil | Source |
|---|---|---|---|---|---|
| **Profil socio-économique de la commune** | Site (subi) | 15 % | nuancé | — | INSEE |
| **Capacité d'absorption (taille du projet vs commune)** | Site (subi) | 15 % | plus bas = mieux | — | INSEE |
| **Aléa technologique / Seveso environnant** | Site (subi) | 10 % | qualitatif | — | Géorisques |
| **Emplois annoncés** | Projet (choisi) | 15 % | plus haut = mieux | — | press releases, press |
| **Retombées fiscales annoncées** | Projet (choisi) | 10 % | qualitatif | — | council deliberations, press |
| **Niveau de contestation observé** | Site (subi) | 20 % | qualitatif | — | press, petitions, local groups |
| **Position des élus (faits votés uniquement)** | Site (subi) | 15 % | qualitatif | — | council deliberations, recorded votes |

### Transparence & gouvernance — 15 %

| Indicateur | Bloc | Coef. | Sens | Référentiel de seuil | Source |
|---|---|---|---|---|---|
| **Concertation / consentement / gouvernance (proxies procéduraux)** | Processus | 60 % | qualitatif | — | public inquiry, environmental authority opinion, CNDP, legal appeals, council deliberations |
| **Transparence documentaire / disponibilité du dossier** | Processus | 40 % | qualitatif | — | registries, official publication |

## 6. Ce qui est verrouillé par construction

- **Annoncé ≠ mesuré** : un chiffre déclaré par l'opérateur est tagué « annoncé », noté avec prudence, re-vérifiable ex-post.
- **Plancher de transparence** : divulguer une donnée ne peut jamais dégrader la note par rapport à l'avoir cachée.
- **Verrou éthique** : la vulnérabilité d'une commune ne peut jamais améliorer la note d'un projet.
- **Gouvernance** : toute évolution de la grille passe par une version taguée et un changelog justifié et signé.

## 7. Statut, limites & calibration

Cette version est **préliminaire et pourra évoluer**.
Ce que la note **n'est pas** : un modèle prédictif validé statistiquement, ni un oracle.
Ce qu'elle **est** : une grille experte, sourcée, versionnée et reproductible.

- **Poids et seuils provisoires** — ils sont calibrés par **validation rétrospective** sur des cas au dénouement connu (projets acceptés / abandonnés), pas affirmés a priori.
- **Traçabilité** — chaque note est datée et rattachée à une version de méthode ; un « A » signifie « le meilleur atteignable aujourd'hui ».

## 8. Références & standards

- [ISO/IEC 30134 (2 PUE · 3 REF · 4 CUE) — indicateurs de performance des centres de données](https://www.iso.org/standard/63451.html)
- [EU Code of Conduct for Data Centres (JRC)](https://e3p.jrc.ec.europa.eu/communities/data-centres-code-conduct)
- [Directive Efficacité Énergétique (EED) 2023/1791](https://eur-lex.europa.eu/eli/dir/2023/1791/oj)
- [WRI Aqueduct — stress hydrique de bassin](https://www.wri.org/aqueduct)
- [Directive Cadre sur l'Eau 2000/60/CE — état des masses d'eau](https://eur-lex.europa.eu/eli/dir/2000/60/oj)
- [ADEME Base Empreinte — facteurs d'émission du réseau](https://base-empreinte.ademe.fr/)
- [RTE eCO2mix / Caparéseau — carbone et capacité du réseau](https://www.rte-france.com/eco2mix)
- [Cadre « Social Licence to Operate » — acceptabilité sociale des projets](https://en.wikipedia.org/wiki/Social_license)

---

*Franck Bardol · ScoreMyDataCenter · méthode 0.1.0-draft · CC BY-SA 4.0.*
*Grille de référence machine-lisible : `site/public/data/methodology.json`. Doc reproductible : `python scripts/gen_methodology_doc.py`.*
