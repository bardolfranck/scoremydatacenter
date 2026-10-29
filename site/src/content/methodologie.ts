// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La page « Méthode » — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
// langue, « duplicated pages is how EN silently diverged »).
//
// 🔴 Cette copie vivait en littéral DANS CHACUNE des deux pages. Les clés y étaient à parité
// le jour du comptage — tenues à la main, sans rien qui les tienne demain. Ici il n'y a qu'un
// endroit, et la parité est VÉRIFIÉE par `engine/tests/test_i18n_parity.py`.
//
// 🔴 Le type ne garde RIEN au build : `site/package.json` lance `astro build` SANS
// `astro check`, donc une clé manquante ne casse pas la construction — elle rend `undefined`
// dans la page, en silence. Le garde qui mord est le test pytest, que `make deploy` lance
// AVANT le build. Ne pas confondre les deux.

import type { Langue } from "./langues";

const FR = {
  title: "Méthodologie — ScoreMyDataCenter",
  metaDescription: "La méthode de notation : une note A–E du site, une seconde du projet quand son dossier est public, confiance documentaire, 26 indicateurs en 5 piliers, seuils ancrés sur des référentiels publics. Méthode ouverte, versionnée, datée.",
  tagline: "Observatoire indépendant",
  h1: "Méthodologie",
  banner: "Version <strong>{version}</strong>. La méthode est <strong>publique, versionnée et datée</strong> (antériorité vérifiable) ; le code et la grille sont sur <a href=\"{repo}\" target=\"_blank\" rel=\"noopener\">GitHub</a>.",
  download: "Télécharger la méthodologie",
  print: "Imprimer / PDF",
  oneSentenceH2: "La note en une phrase",
  oneSentence: [
    "<p>Chaque projet reçoit <strong>deux notes de A à E</strong> — une pour le <strong>site</strong> (le contexte que le projet <span class=\"hl-yellow\">subit</span>) et une pour le <strong>projet &amp; processus</strong> (ce que l'opérateur <span class=\"hl-yellow\">choisit</span>) — assorties d'un <strong>niveau de confiance documentaire</strong>. Une note ne s'affiche jamais sans lui ; sous 40 % de couverture, on écrit « données insuffisantes ». On ne note pas l'inconnu.</p>",
    "<p>Le score est calculé à partir des seules valeurs sourcées du fichier de chaque projet.</p>",
    "<p class=\"meth-nerd\">🤓 <strong>Méthode reproductible</strong> : quiconque clone le dépôt et lance <code>make score</code> retombe exactement sur les lettres affichées.</p>",
  ],
  scaleH2: "L'échelle",
  expertCrochet: "💡 La filière note <strong>déjà</strong> en lettres (PI de A à G, DCp de A à I) — mais l'<strong>efficacité</strong> de la machine, auto-déclarée et anonyme. Nous notons l'<strong>acceptabilité</strong> d'un site réel, de l'extérieur. → <a href=\"/fr/normes\">Les normes, et où nous nous situons</a>.",
  aProvenH2: "Le A se prouve, il ne se promet pas",
  aProvenP: "<p>L'échelle a un sens précis, verrouillé par construction : <i class=\"gl gl-e\">E</i> — opaque, ou vérifié défavorable · <i class=\"gl gl-d\">D</i> / <i class=\"gl gl-c\">C</i> — promesses partielles ou bonnes · <i class=\"gl gl-b\">B</i> — promesses complètes, chiffrées, processus exemplaire · <i class=\"gl gl-a\">A</i> — <strong>réservé à l'exploitation vérifiée</strong>. Un dossier entièrement déclaratif, aussi excellent soit-il, <strong>plafonne mathématiquement sous le <i class=\"gl gl-a\">A</i></strong> : les valeurs annoncées sont notées avec prudence (« annoncé ≠ mesuré »), et seule la preuve lève ce plafond. Personne ne « reçoit » un <i class=\"gl gl-a\">A</i> — on le démontre.</p>",
  aProvenExTitle: "Opérateurs — comment obtenir votre <i class=\"gl gl-a\">A</i>",
  aProvenEx: [
    "<p>Apportez une preuve <strong>tierce</strong> de vos valeurs en exploitation : copie de votre <strong>déclaration EED</strong> transmise au régulateur, certificat d'<strong>audit ISO/IEC 30134</strong> par un organisme accrédité, ou attestation d'un bureau de contrôle — jamais une page marketing. Déposez-la via le canal public de correction (source obligatoire, déclaration d'intérêt). La donnée passe alors d'« annoncée » à « mesurée », le plafond déclaratif saute, et le re-score est <strong>tracé au journal d'audit public</strong>. Aucun courrier à attendre de notre part, aucun paiement — la preuve fait tout.</p>",
    "<p>Deux précisions qui protègent tout le monde. La preuve fait monter votre note <strong>projet &amp; processus</strong> — <strong>jamais celle du site</strong> : le territoire (eau, réseau, sol) est subi, il ne se prouve pas. Et aucune capture possible : pas de paiement, une preuve <strong>tierce</strong>, une note qui ne bouge que parce que des <strong>faits vérifiés</strong> ont bougé.</p>",
  ],
  pillarsH2: "Les 5 piliers",
  bulletinH2: "La note, comme un bulletin scolaire",
  bulletin: [
    "<p>Un data center reçoit un bulletin. Les cinq grands thèmes — les <strong>piliers</strong> — sont les matières : Énergie, Eau, Foncier &amp; biodiversité, Impact local, Transparence &amp; gouvernance. Dans chaque matière, plusieurs « contrôles » — les <strong>indicateurs</strong> — donnent des notes.</p>",
    "<p><strong>Étage 1</strong> : dans chaque pilier, les indicateurs sont moyennés selon leur coefficient interne (un contrôle compte plus qu'un autre).</p>",
    "<p><strong>Étage 2</strong> : les scores de piliers sont moyennés selon les poids ci-dessus. Un principe : <strong>pas de croisement</strong> — un indicateur ne compte que dans son pilier, jamais ailleurs.</p>",
  ],
  exampleTitle: "Exemple (2 piliers, scores déjà normalisés sur 100)",
  exampleItems: [
    "<b>Énergie</b> (poids 25 %) — carbone 80 (coef 0,6) · PUE 40 (coef 0,4) → <b>80×0,6 + 40×0,4 = 64</b>",
    "<b>Eau</b> (poids 20 %) — stress 30 (coef 0,7) · conso 50 (coef 0,3) → <b>30×0,7 + 50×0,3 = 36</b>",
    "Global (poids renormalisés 25/45 et 20/45) → 64×0,56 + 36×0,44 ≈ <b>52</b> → lettre <strong>C</strong> (seuil 50–64)",
  ],
  twoNotesH2: "Deux notes — et ce n'est pas la moyenne des piliers",
  twoNotesP: "<p>C'est la nuance qui surprend. Les deux notes de tête n'agrègent pas par pilier mais <strong>par bloc</strong> : la note <strong>site</strong> = les indicateurs <em>subis</em> (ce que le territoire impose — carbone du réseau, stress hydrique, foncier) ; la note <strong>projet &amp; processus</strong> = les indicateurs <em>choisis</em> (efficacité, refroidissement, concertation, transparence). Les <strong>sous-scores par pilier</strong>, eux, regroupent chaque thématique en mêlant subi et choisi. Les deux découpages sont orthogonaux : <strong>une note ne se lit pas comme la moyenne des piliers affichés.</strong></p>",
  thresholdsH2: "De la mesure à la note — deux familles de seuils",
  thresholdsP: "<p>Chaque indicateur transforme une valeur brute en sous-score 0–100 via un seuil. Ce seuil est posé de deux manières, et la distinction est <strong>déclarée</strong>, pas cachée :</p>",
  thresholdFamilies: [
    "<strong>Famille A — référentiel externe.</strong> On s'ancre sur un standard existant, sourcé et défendable (ISO 30134 pour l'efficacité, Directive Cadre sur l'Eau pour l'état des masses d'eau, WRI Aqueduct pour le stress hydrique…).",
    "<strong>Famille B — ratio éditorial déclaré.</strong> Là où aucune norme n'existe (« quelle taille est trop grosse ? »), on n'invente pas un seuil absolu : on exprime un <strong>ratio contextuel</strong> (projet rapporté à la commune, au bassin) et on <strong>assume le choix éditorial</strong>.",
  ],
  rule: "Règle : <strong>maximiser le référentiel, minimiser l'éditorial — et le déclarer.</strong> La colonne « Référentiel » du détail ci-dessous dit, indicateur par indicateur, sur quoi le seuil s'appuie.",
  lockedH2: "Ce qui est verrouillé par construction",
  locked: [
    "<strong>Annoncé ≠ mesuré</strong> : un chiffre déclaré par l'opérateur est tagué « annoncé », noté avec prudence, re-vérifiable ex-post.",
    "<strong>Plancher de transparence</strong> : divulguer une donnée ne peut jamais dégrader la note par rapport à l'avoir cachée.",
    "<strong>Verrou éthique</strong> : la vulnérabilité d'une commune ne peut jamais améliorer la note d'un projet.",
    "<strong>Firewall « projet ≠ note »</strong> : on aide le projet, jamais la note. La note publique ne bouge que si le <strong>projet réel</strong> change (faits sourcés, re-scoring tracé au journal d'audit) — jamais parce qu'un opérateur a payé.",
    "<strong>Gouvernance</strong> : toute évolution de la grille passe par une version taguée et une entrée de changelog justifiée et signée.",
  ],
  statusH2: "Statut, limites & calibration",
  statusP: "<p>Cette version est <strong>préliminaire et pourra évoluer</strong>. Ce que la note <strong>n'est pas</strong> : un modèle prédictif validé statistiquement, ni un oracle. Ce qu'elle <strong>est</strong> : une <strong>grille experte, sourcée, versionnée et reproductible</strong>, qui applique des seuils ancrés sur des référentiels publics et déclare ses choix éditoriaux.</p>",
  statusItems: [
    "<strong>Poids et seuils provisoires</strong> : ils sont calibrés par <strong>validation rétrospective</strong> sur des cas au dénouement connu (projets acceptés / abandonnés), pas affirmés a priori.",
    "<strong>Traçabilité</strong> : chaque note est datée et rattachée à une version de méthode ; un « A » signifie « le meilleur atteignable aujourd'hui », pas « le meilleur pour toujours ».",
  ],
  refsH2: "Références & standards",
  references: [
    { label: "ISO/IEC 30134 (2 PUE · 3 REF · 4 CUE) — indicateurs de performance des centres de données", url: "https://www.iso.org/standard/63451.html" },
    { label: "EU Code of Conduct for Data Centres (JRC)", url: "https://e3p.jrc.ec.europa.eu/communities/data-centres-code-conduct" },
    { label: "Directive Efficacité Énergétique (EED) 2023/1791 — reporting des data centers", url: "https://eur-lex.europa.eu/eli/dir/2023/1791/oj" },
    { label: "WRI Aqueduct — stress hydrique de bassin", url: "https://www.wri.org/aqueduct" },
    { label: "Directive Cadre sur l'Eau 2000/60/CE — état des masses d'eau", url: "https://eur-lex.europa.eu/eli/dir/2000/60/oj" },
    { label: "ADEME Base Empreinte — facteurs d'émission du réseau", url: "https://base-empreinte.ademe.fr/" },
    { label: "RTE eCO2mix / Caparéseau — carbone et capacité du réseau", url: "https://www.rte-france.com/eco2mix" },
    { label: "Cadre « Social Licence to Operate » — acceptabilité sociale des projets", url: "https://en.wikipedia.org/wiki/Social_license" },
  ],
  detailsSummary: "Voir le détail des 26 indicateurs",
  detailsIntro: "<p>Chaque indicateur porte son <strong>coefficient</strong> (poids dans le pilier), son <strong>sens de notation</strong>, la <strong>base de son seuil</strong> (référentiel externe ou choix éditorial déclaré) et sa <strong>source de donnée</strong> — c'est une contrainte de schéma, pas une bonne pratique.</p>",
  th: { indicator: "Indicateur", block: "Bloc", coef: "Coef.", direction: "Sens", thresholdRef: "Référentiel de seuil", source: "Source" },
  blockLabel: { base: "Site (subi)", project: "Projet (choisi)", process: "Processus" },
  dirLabel: { lower_is_better: "plus bas = mieux", higher_is_better: "plus haut = mieux", encoded_in_scoring: "qualitatif", non_monotonic: "nuancé" },
  backHref: "/fr/",
  backLabel: "← Retour à l'accueil",
};

const EN: typeof FR = {
  title: "Methodology — ScoreMyDataCenter",
  metaDescription: "The scoring method: an A–E grade for the site, a second for the project when its dossier is public, documentation confidence, 26 indicators across 5 pillars, thresholds anchored on public referentials. Open, versioned, dated method.",
  tagline: "Independent observatory",
  h1: "Methodology",
  banner: "Version <strong>{version}</strong>. The method is <strong>public, versioned and dated</strong> (verifiable anteriority); the code and the grid are on <a href=\"{repo}\" target=\"_blank\" rel=\"noopener\">GitHub</a>.",
  download: "Download the methodology (FR)",
  print: "Print / PDF",
  oneSentenceH2: "The grade in one sentence",
  oneSentence: [
    "<p>Each project receives <strong>two grades from A to E</strong> — one for the <strong>site</strong> (the context the project <span class=\"hl-yellow\">endures</span>) and one for the <strong>project &amp; process</strong> (what the operator <span class=\"hl-yellow\">chooses</span>) — coupled with a <strong>documentation confidence level</strong>. A grade never appears without it; below 40% coverage we write “insufficient data”. We do not grade the unknown.</p>",
    "<p>The score is computed from the sourced values of each project's file, and nothing else.</p>",
    "<p class=\"meth-nerd\">🤓 <strong>Reproducible method</strong>: anyone who clones the repository and runs <code>make score</code> lands exactly on the displayed letters.</p>",
  ],
  scaleH2: "The scale",
  expertCrochet: "💡 The industry <strong>already</strong> grades in letters (PI from A to G, DCp from A to I) — but the <strong>efficiency</strong> of the machine, self-declared and anonymous. We grade the <strong>acceptability</strong> of a real site, from the outside. → <a href=\"/standards\">The standards, and where we sit</a>.",
  aProvenH2: "An A is proven, never promised",
  aProvenP: "<p>The scale has a precise meaning, locked by construction: <i class=\"gl gl-e\">E</i> — opaque, or verified unfavorable · <i class=\"gl gl-d\">D</i> / <i class=\"gl gl-c\">C</i> — partial or good promises · <i class=\"gl gl-b\">B</i> — complete, quantified promises and an exemplary process · <i class=\"gl gl-a\">A</i> — <strong>reserved for verified operation</strong>. A fully declarative file, however excellent, <strong>mathematically caps below the <i class=\"gl gl-a\">A</i></strong>: announced values are graded with caution (“announced ≠ measured”), and only proof lifts that cap. Nobody “receives” an <i class=\"gl gl-a\">A</i> — it is demonstrated.</p>",
  aProvenExTitle: "Operators — how to earn your <i class=\"gl gl-a\">A</i>",
  aProvenEx: [
    "<p>Bring <strong>third-party</strong> proof of your values in operation: a copy of your <strong>EED filing</strong> to the regulator, an <strong>ISO/IEC 30134 audit</strong> certificate from an accredited body, or an inspection-office attestation — never a marketing page. Submit it through the public correction channel (source required, declaration of interest). The data then flips from “announced” to “measured”, the declarative cap lifts, and the re-score is <strong>traced in the public audit log</strong>. No letter to wait for, no payment — the proof does everything.</p>",
    "<p>Two clarifications that protect everyone. Proof lifts your <strong>project &amp; process</strong> grade — <strong>never the site grade</strong>: the territory (water, grid, land) is endured, it cannot be proven away. And no capture is possible: no payment, <strong>third-party</strong> proof, a grade that moves only because <strong>verified facts</strong> moved.</p>",
  ],
  pillarsH2: "The 5 pillars",
  bulletinH2: "The grade, like a school report",
  bulletin: [
    "<p>A data center receives a report card. The five main themes — the <strong>pillars</strong> — are the subjects: Energy, Water, Land &amp; biodiversity, Local impact, Transparency &amp; governance. In each subject, several “tests” — the <strong>indicators</strong> — produce marks.</p>",
    "<p><strong>Stage 1</strong>: within each pillar, indicators are averaged by their internal coefficient (one test counts more than another).</p>",
    "<p><strong>Stage 2</strong>: pillar scores are averaged by the weights above. One principle: <strong>no crossover</strong> — an indicator counts in its pillar only, never elsewhere.</p>",
  ],
  exampleTitle: "Example (2 pillars, scores already normalised to 100)",
  exampleItems: [
    "<b>Energy</b> (weight 25%) — carbon 80 (coef 0.6) · PUE 40 (coef 0.4) → <b>80×0.6 + 40×0.4 = 64</b>",
    "<b>Water</b> (weight 20%) — stress 30 (coef 0.7) · consumption 50 (coef 0.3) → <b>30×0.7 + 50×0.3 = 36</b>",
    "Global (weights renormalised 25/45 and 20/45) → 64×0.56 + 36×0.44 ≈ <b>52</b> → letter <strong>C</strong> (threshold 50–64)",
  ],
  twoNotesH2: "Two grades — and it is not the average of the pillars",
  twoNotesP: "<p>This is the nuance that surprises. The two headline grades do not aggregate by pillar but <strong>by block</strong>: the <strong>site</strong> grade = the <em>endured</em> indicators (what the territory imposes — grid carbon, water stress, land); the <strong>project &amp; process</strong> grade = the <em>chosen</em> indicators (efficiency, cooling, consultation, transparency). The <strong>pillar sub-scores</strong> group each theme, mixing endured and chosen. The two groupings are orthogonal: <strong>a grade does not read as the average of the displayed pillars.</strong></p>",
  thresholdsH2: "From measurement to grade — two families of thresholds",
  thresholdsP: "<p>Each indicator turns a raw value into a 0–100 sub-score through a threshold. That threshold is set in two ways, and the distinction is <strong>declared</strong>, not hidden:</p>",
  thresholdFamilies: [
    "<strong>Family A — external referential.</strong> We anchor on an existing, sourced, defensible standard (ISO 30134 for efficiency, the Water Framework Directive for water-body status, WRI Aqueduct for water stress…).",
    "<strong>Family B — declared editorial ratio.</strong> Where no norm exists (“what size is too big?”), we do not invent an absolute threshold: we express a <strong>contextual ratio</strong> (project relative to the municipality, to the basin) and <strong>own the editorial choice</strong>.",
  ],
  rule: "Rule: <strong>maximise the referential, minimise the editorial — and declare it.</strong> The “Threshold referential” column in the detail below states, indicator by indicator, what each threshold rests on.",
  lockedH2: "Locked by construction",
  locked: [
    "<strong>Announced ≠ measured</strong>: a figure declared by the operator is tagged “announced”, graded with caution, re-verifiable ex-post.",
    "<strong>Transparency floor</strong>: disclosing a data point can never degrade the grade relative to hiding it.",
    "<strong>Ethical lock</strong>: a municipality's vulnerability can never improve a project's grade.",
    "<strong>“Project ≠ grade” firewall</strong>: we help the project, never the grade. The public grade moves only when the <strong>real project</strong> changes (sourced facts, audit-logged re-scoring) — never because an operator paid.",
    "<strong>Governance</strong>: every grid evolution goes through a tagged version and a justified, signed changelog entry.",
  ],
  statusH2: "Status, limits & calibration",
  statusP: "<p>This version is <strong>preliminary and may evolve</strong>. What the grade <strong>is not</strong>: a statistically validated predictive model, nor an oracle. What it <strong>is</strong>: an <strong>expert, sourced, versioned and reproducible grid</strong>, applying thresholds anchored on public referentials and declaring its editorial choices.</p>",
  statusItems: [
    "<strong>Provisional weights and thresholds</strong>: they are calibrated by <strong>retrospective validation</strong> on known-outcome cases (accepted / abandoned projects), not asserted a priori.",
    "<strong>Traceability</strong>: every grade is dated and tied to a methodology version; an “A” means “the best achievable today”, not “the best forever”.",
  ],
  refsH2: "References & standards",
  references: [
    { label: "ISO/IEC 30134 (2 PUE · 3 REF · 4 CUE) — data centre performance indicators", url: "https://www.iso.org/standard/63451.html" },
    { label: "EU Code of Conduct for Data Centres (JRC)", url: "https://e3p.jrc.ec.europa.eu/communities/data-centres-code-conduct" },
    { label: "Energy Efficiency Directive (EED) 2023/1791 — data centre reporting", url: "https://eur-lex.europa.eu/eli/dir/2023/1791/oj" },
    { label: "WRI Aqueduct — basin water stress", url: "https://www.wri.org/aqueduct" },
    { label: "Water Framework Directive 2000/60/EC — water-body status", url: "https://eur-lex.europa.eu/eli/dir/2000/60/oj" },
    { label: "ADEME Base Empreinte — grid emission factors", url: "https://base-empreinte.ademe.fr/" },
    { label: "RTE eCO2mix / Caparéseau — grid carbon and capacity", url: "https://www.rte-france.com/eco2mix" },
    { label: "“Social Licence to Operate” framework — social acceptability of projects", url: "https://en.wikipedia.org/wiki/Social_license" },
  ],
  detailsSummary: "See the 26 indicators in detail",
  detailsIntro: "<p>Each indicator carries its <strong>coefficient</strong> (weight within the pillar), its <strong>scoring direction</strong>, the <strong>basis of its threshold</strong> (external referential or declared editorial choice) and its <strong>data source</strong> — a schema constraint, not a best practice.</p>",
  th: { indicator: "Indicator", block: "Block", coef: "Coef.", direction: "Direction", thresholdRef: "Threshold referential", source: "Source" },
  blockLabel: { base: "Site (endured)", project: "Project (chosen)", process: "Process" },
  dirLabel: { lower_is_better: "lower = better", higher_is_better: "higher = better", encoded_in_scoring: "qualitative", non_monotonic: "nuanced" },
  backHref: "/",
  backLabel: "← Back to the home page",
};

/** La table servie au gabarit : `METHODOLOGIE[lang]`. */
export const METHODOLOGIE: Record<Langue, typeof FR> = { fr: FR, en: EN };
