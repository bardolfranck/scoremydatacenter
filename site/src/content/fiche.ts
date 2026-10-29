// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Les chaînes de la fiche, UNE SEULE FOIS, par langue (i18n §13 : un gabarit, un objet `t`
// par langue — « duplicated pages is how EN silently diverged »).
//
// 🔴 Pourquoi ce fichier existe : la table vivait en littéral DANS chacune des deux pages.
// Les 127 clés y étaient à parité, mais tenues à la main — et une énumération écrite à deux
// endroits finit par mentir. Ici il n'y a qu'un endroit, et la parité est VÉRIFIÉE par
// `engine/tests/test_i18n_fiche.py`, pas espérée.
//
// 🔴 Le type ci-dessous ne garde rien au build : `site/package.json` lance `astro build`
// SANS `astro check`, donc une clé manquante en EN ne casserait pas la construction — elle
// rendrait `undefined` dans la page, en silence. Le type sert à l'éditeur ; le garde qui
// mord est le test pytest, que `make deploy` lance AVANT le build. Ne pas confondre les deux.
//
// Ce qui n'entre pas ici : les CHEMINS (`/fr/carte/` contre `/map/`) et les FORMATS (virgule
// décimale, ordre de date) — ce ne sont pas des mots à traduire, et une langue nouvelle n'a
// rien à en dire. Ils restent en code, dans le gabarit.

export const LANGUES_FICHE = ["fr", "en"] as const;
export type LangueFiche = (typeof LANGUES_FICHE)[number];

const FR = {
  tagline: "Observatoire indépendant",
  metaDescription: "Fiche {name} ({municipality}) : note du site et note projet & processus A–E, sous-scores par pilier, indicateurs sourcés — observatoire indépendant.",
  kicker: "Fiche projet",
  fleet: {
    grid_saturated: "Ce site fait partie des {pct} du parc raccordés à un poste électrique déjà saturé.",
    water_stress_high: "Ce site fait partie des {pct} du parc implantés dans un bassin en stress hydrique fort.",
    soil_artificialized: "Ce site fait partie des {pct} du parc bâtis sur des sols déjà artificialisés.",
    cta: "Les chiffres du parc →",
  },
  status: { announced: "Annoncé", permitting: "En instruction (permitting)", under_construction: "En construction", operational: "En service" },
  statusCheck: {
    verified: "statut vérifié",
    networksSingular: "réseau interconnecté",
    networksPlural: "réseaux interconnectés",
    verifiedTip: "Confirmé automatiquement le {date} : {n} réseau(x) interconnecté(s) dans ce bâtiment (source PeeringDB). Vérification chaque semaine.",
    unverified: "statut non vérifié",
    unverifiedTip: "Statut issu de sources publiques, pas encore confirmé par un signal indépendant. Vérification automatique chaque semaine.",
  },
  operatorLabel: "Opérateur :",
  operatorFromRegister: "Identifié automatiquement dans le registre des entreprises (SIRENE)",
  developerDeclared: "activité déclarée :",
  developerRegister: "registre des entreprises",
  dwellLabel: "Premières habitations :",
  dwellBuildingShort: "bâtiment d'habitation (OpenStreetMap)",
  dwellBuilding: "Distance au bâtiment d'habitation le plus proche recensé dans OpenStreetMap, mesurée depuis les coordonnées du site (valeur approchée, jamais un relevé de bruit).",
  dwellLanduseShort: "zone résidentielle (OpenStreetMap)",
  dwellLanduse: "Aucun bâtiment d'habitation n'est encore recensé ici : la distance vise la zone résidentielle la plus proche, moins précise qu'une maison.",
  powerUnknown: "puissance non communiquée",
  powerEstimated: "estimé",
  commissioning: "mise en service",
  siteScore: "Note du site",
  ppScore: "Note projet & processus",
  naLabel: "données insuffisantes",
  reserved: "A réservé — se prouve en exploitation",
  confidence: { high: "confiance : haute", medium: "confiance : moyenne", low: "confiance : faible" },
  confidenceNote: { high: "dossier largement sourcé", medium: "dossier partiellement sourcé", low: "dossier peu sourcé" },
  confGlobal: "Confiance documentaire globale",
  openFullMap: "Ouvrir la grande carte ↗",
  miniMapAria: "Carte centrée sur ce site",
  miniMapTitle: "Territoire & voisins",
  satCaption: "Vue aérienne — {municipality}. Source :",
  satAlt: "Vue aérienne du site {name}",
  satStatusChip: { announced: "Site en projet", permitting: "Site en projet", under_construction: "En construction" },
  satStatusNote: "l'image satellite peut être antérieure au projet : le terrain visible ici peut ne pas encore accueillir le data center",
  synthEmptyNote: "Dossier peu sourcé ({pct} % de confiance documentaire) : nous ne notons pas l'inconnu, et nous ne rédigeons pas de lecture d'ensemble sans faits suffisants. Cette lecture pourra évoluer si de nouvelles informations publiques ou vérifiables deviennent disponibles.",
  share: "Partager",
  shareOn: "Partager sur",
  shareMail: "Partager par e-mail",
  copyLink: "Copier le lien",
  copied: "Lien copié",
  download: "Télécharger l'image du score",
  signal: "Signaler une erreur",
  signalSubject: "Correction ou réponse",
  signalBody: "Fiche concernée : {url}\nNature de la demande : [ ] Correction d'une donnée [ ] Réponse de l'opérateur [ ] Autre\nInformation concernée :\nCorrection ou réponse proposée :\nSource ou justificatif :\nNom et qualité du demandeur :\nLien éventuel avec le projet ou l'opérateur :\n",
  signalNote: "Corrige un fait, avec sa source — <strong>une preuve est requise</strong>.",
  methodology: "Méthodologie",
  portraitLink: "Portrait du site →",
  portraitLinkSub: "la même donnée, écrite pour un élu ou un riverain",
  subscoresTitle: "Sous-scores par pilier",
  subscoresSub: "Un pilier mêle le subi et le choisi ; une note n'est pas la moyenne des piliers.",
  whyAria: "Pourquoi la note ne se déduit pas des piliers",
  whyTip: "Les deux notes (site, projet) séparent les indicateurs selon qu'ils sont subis ou choisis — toutes thématiques confondues et pondérés. Les piliers, eux, regroupent chaque thématique en mêlant subi et choisi. Les deux découpages ne se recouvrent pas : la note du site ne se lit pas comme la moyenne des piliers affichés.",
  legendDoc: "documentation disponible",
  synthTitle: "Synthèse du projet",
  synthSub: "la lecture d'ensemble, derrière les lettres",
  synthProjectTag: "Projet & processus",
  synthSiteTag: "Site",
  quoteOpen: "« ",
  quoteClose: " »",
  indicatorsTitle: "Indicateurs suivis",
  th: { indicator: "Indicateur", value: "Valeur", reading: "Lecture", state: "État", source: "Source" },
  explanation: "Explication",
  notDisclosed: "Non communiqué",
  // Sur quoi la note d'un pilier repose RÉELLEMENT. Un pilier mince est aujourd'hui
  // renormalisé en silence : le lecteur ne voit pas qu'un seul point le porte.
  pillarBasis: { one: "1 seul indicateur publié :", some: "{k} indicateurs publiés sur {n}" },
  pillarMissing: "Manquent :",
  pillarScope: {
    national: "Note nationale — la même pour tous les sites notés dans ce pays ({pays}).",
    thin: "Trop peu de sites notés dans ce pays pour établir si cette note le distingue.",
  },
  procedureSeeSource: "Procédure (voir source)",
  notApplicable: "non applicable",
  // DEUX ABSENCES OPPOSÉES PORTAIENT LE MÊME SILENCE. `missing` veut dire « nous avons lu le
  // dossier, la donnée n'y est pas » — c'est un fait, et il compte comme un ZÉRO dans la note.
  // `not_collected` veut dire « nous n'avons pas cherché » — c'est notre lacune, retirée du
  // calcul. La fiche nommait le premier « Manquant » (ambigu : manquant pour qui ?) et ne
  // nommait pas le second du tout : 48 135 lignes du corpus affichaient une case d'état VIDE.
  indStatus: {
    measured: "Mesuré", announced: "Annoncé", estimated: "Estimé",
    missing: "Absent du dossier", not_collected: "Pas encore cherché",
  },
  indStatusHint: {
    missing: "L'information a été cherchée dans le dossier public et ne s'y trouve pas. Elle compte comme un zéro dans la note.",
    not_collected: "Nous n'avons pas encore cherché cette information. Elle est retirée du calcul, elle ne pénalise pas le site.",
  },
  accessed: "consulté le",
  archived: "archivé",
  directionHint: { lower_is_better: "Plus la valeur est basse, mieux c'est.", higher_is_better: "Plus la valeur est haute, mieux c'est." },
  hintDedupe: "mieux c'est",
  sense: { good: "favorable", mid: "moyen", bad: "défavorable" },
  proxy: {
    inquiryHeld: "Enquête publique tenue",
    inquiryNone: "Pas d'enquête publique",
    envOpinion: {
      favorable: "Avis de l'autorité environnementale : favorable",
      favorable_with_reservations: "Avis de l'autorité environnementale : favorable avec réserves",
      unfavorable: "Avis de l'autorité environnementale : défavorable",
      none: "Avis de l'autorité environnementale : aucun requis/rendu",
    },
    cndpYes: "Saisine de la CNDP",
    cndpNo: "Pas de saisine de la CNDP",
    appeals: "Recours contentieux :",
    council: {
      favorable: "Délibérations du conseil : favorables",
      mixed: "Délibérations du conseil : mitigées",
      unfavorable: "Délibérations du conseil : défavorables",
      none_recorded: "Délibérations du conseil : aucune enregistrée",
    },
  },
  opTitle: "Réponse de l'opérateur",
  opNone: "L'opérateur peut nous transmettre une réponse concernant cette fiche. Lorsqu'une réponse est reçue et publiable, elle apparaît ici, clairement attribuée et datée.",
  opNote: "Une erreur factuelle ? Utilisez « Signaler une erreur » en joignant une source ou un justificatif.",
  dataStateTitle: "État de la donnée disponible",
  dataState: "{n} indicateurs suivis · {measured} mesurés · {announced} annoncés (non vérifiés) · {missing} absents du dossier · {notCollected} pas encore cherchés.",
  contestationTitle: "Contestation & signal",
  contestationSub: "Faits sourcés — n'entrent pas dans la note.",
  press: "Presse : ",
  selfReported: "auto-déclaré",
  historyTitle: "Historique de la note",
  histSite: "Note du site à cette date",
  histPp: "Note projet & processus à cette date",
  scoredOn: "Scoré le",
  shareText: "{name} — Note du site : {grade}",
  shareSuffix: ", selon ScoreMyDataCenter",
  related: {
    title: "D'autres sites à comparer",
    // La phrase d'intro était figée au cas français : une fiche du Texas annonçait
    // « même département » au-dessus de cartes qui disent « même région ». Le mot suit
    // maintenant le pays, comme l'étiquette de la relation juste en dessous — une seule
    // réponse à « comment s'appelle la maille ici ».
    sub: "Même opérateur, {maille}, ou simplement les plus proches — notés dans la même grille.",
    subMailleFR: "même département",
    subMaille: "même région",
    seeAll: "Voir le classement complet →",
    // Sous le kilomètre, la coordonnée publiée (arrondie à ~1 km) ne mesure plus rien :
    // voir PLANCHER_KM dans DcFiche. `nearbyMi` n'a pas de pendant ici — la page française
    // reste métrique, même pour un site américain.
    relation: { operator: "même opérateur :", region: "même région", regionFR: "même département", nearby: "à {km} km", nearbyUnder: "à moins d'un kilomètre" },
  },
};

const EN: typeof FR = {
  tagline: "Independent observatory",
  metaDescription: "{name} ({municipality}): site grade and project & process grade A–E, pillar sub-scores, sourced indicators — independent observatory.",
  kicker: "Project fiche",
  fleet: {
    grid_saturated: "This site is among the {pct} of the fleet connected to an already-saturated substation.",
    water_stress_high: "This site is among the {pct} of the fleet located in a basin under high water stress.",
    soil_artificialized: "This site is among the {pct} of the fleet built on already-artificialized soil.",
    cta: "Fleet figures →",
  },
  status: { announced: "Announced", permitting: "Permitting", under_construction: "Under construction", operational: "Operational" },
  statusCheck: {
    verified: "status verified",
    networksSingular: "network interconnected",
    networksPlural: "networks interconnected",
    verifiedTip: "Automatically confirmed on {date}: {n} network(s) interconnect in this building (source: PeeringDB). Checked every week.",
    unverified: "status not verified",
    unverifiedTip: "Status taken from public sources, not yet confirmed by an independent signal. Checked automatically every week.",
  },
  operatorLabel: "Operator:",
  operatorFromRegister: "Automatically identified in the French company register (SIRENE)",
  developerDeclared: "declared activity:",
  developerRegister: "company register",
  dwellLabel: "Nearest homes:",
  dwellBuildingShort: "residential building (OpenStreetMap)",
  dwellBuilding: "Distance to the nearest residential building recorded in OpenStreetMap, measured from the site's coordinates (an approximation, never a noise measurement).",
  dwellLanduseShort: "residential area (OpenStreetMap)",
  dwellLanduse: "No residential building is mapped here yet: the distance is to the nearest residential area, less precise than a house.",
  powerUnknown: "power not disclosed",
  powerEstimated: "estimated",
  commissioning: "commissioning",
  siteScore: "Site grade",
  ppScore: "Project & process grade",
  naLabel: "insufficient data",
  reserved: "A reserved — proven in operation",
  confidence: { high: "confidence: high", medium: "confidence: medium", low: "confidence: low" },
  confidenceNote: { high: "largely sourced file", medium: "partially sourced file", low: "thinly sourced file" },
  confGlobal: "Overall documentation confidence",
  openFullMap: "Open the full map ↗",
  miniMapAria: "Map centred on this site",
  miniMapTitle: "Territory & neighbours",
  satCaption: "Aerial view — {municipality}. Source:",
  satAlt: "Aerial view of {name}",
  satStatusChip: { announced: "Planned site", permitting: "Planned site", under_construction: "Under construction" },
  satStatusNote: "the satellite image may predate the project: the land shown here may not yet host the data center",
  synthEmptyNote: "Thinly sourced file ({pct}% documentary confidence): we do not grade the unknown, and we do not write an overall reading without sufficient facts. This reading may evolve if new public or verifiable information becomes available.",
  share: "Share",
  shareOn: "Share on",
  shareMail: "Share by email",
  copyLink: "Copy the link",
  copied: "Link copied",
  download: "Download the score image",
  signal: "Report an error",
  signalSubject: "Correction or response",
  signalBody: "Datasheet concerned: {url}\nNature of the request: [ ] Data correction [ ] Operator response [ ] Other\nInformation concerned:\nProposed correction or response:\nSource or supporting document:\nName and capacity of the requester:\nAny link with the project or the operator:\n",
  signalNote: "Corrects a fact, with its source — <strong>proof is required</strong>.",
  methodology: "Methodology",
  portraitLink: "Site portrait →",
  portraitLinkSub: "the same data, written for a councillor or a neighbour",
  subscoresTitle: "Pillar sub-scores",
  subscoresSub: "A pillar mixes what is endured and what is chosen; a grade is not the average of the pillars.",
  whyAria: "Why the grade cannot be derived from the pillars",
  whyTip: "The two grades (site, project) split the indicators by whether they are endured or chosen — across all themes, weighted. The pillars group each theme, mixing endured and chosen. The two groupings do not overlap: the site grade does not read as the average of the displayed pillars.",
  legendDoc: "documentation available",
  synthTitle: "Project synthesis",
  synthSub: "the overall reading behind the letters",
  synthProjectTag: "Project & process",
  synthSiteTag: "Site",
  quoteOpen: "“",
  quoteClose: "”",
  indicatorsTitle: "Tracked indicators",
  th: { indicator: "Indicator", value: "Value", reading: "Reading", state: "State", source: "Source" },
  explanation: "Explanation",
  notDisclosed: "Not disclosed",
  // What a pillar's grade ACTUALLY rests on. A thin pillar is renormalized in
  // silence today: the reader cannot see that a single datum carries it.
  pillarBasis: { one: "1 published indicator only:", some: "{k} of {n} indicators published" },
  pillarMissing: "Missing:",
  pillarScope: {
    national: "National grade — the same for every site graded in {pays}.",
    thin: "Too few sites graded in this country to establish whether this grade sets it apart.",
  },
  procedureSeeSource: "Procedure (see source)",
  notApplicable: "not applicable",
  indStatus: {
    measured: "Measured", announced: "Announced", estimated: "Estimated",
    missing: "Absent from the file", not_collected: "Not looked for yet",
  },
  indStatusHint: {
    missing: "We read the public file and the information is not in it. It counts as a zero in the grade.",
    not_collected: "We have not looked for this yet. It is dropped from the calculation and does not penalise the site.",
  },
  accessed: "accessed",
  archived: "archived",
  directionHint: { lower_is_better: "The lower the value, the better.", higher_is_better: "The higher the value, the better." },
  hintDedupe: "the better",
  sense: { good: "favorable", mid: "middling", bad: "unfavorable" },
  proxy: {
    inquiryHeld: "Public inquiry held",
    inquiryNone: "No public inquiry",
    envOpinion: {
      favorable: "Environmental authority opinion: favorable",
      favorable_with_reservations: "Environmental authority opinion: favorable with reservations",
      unfavorable: "Environmental authority opinion: unfavorable",
      none: "Environmental authority opinion: none required/issued",
    },
    cndpYes: "CNDP referral",
    cndpNo: "No CNDP referral",
    appeals: "Legal appeals:",
    council: {
      favorable: "Council deliberations: favorable",
      mixed: "Council deliberations: mixed",
      unfavorable: "Council deliberations: unfavorable",
      none_recorded: "Council deliberations: none recorded",
    },
  },
  opTitle: "Operator response",
  opNone: "The operator can send us a response about this datasheet. When a response is received and publishable, it appears here, clearly attributed and dated.",
  opNote: "A factual error? Use “Report an error”, attaching a source or supporting document.",
  dataStateTitle: "State of the available data",
  dataState: "{n} indicators tracked · {measured} measured · {announced} announced (unverified) · {missing} absent from the file · {notCollected} not looked for yet.",
  contestationTitle: "Contestation & signal",
  contestationSub: "Sourced facts — never an input to the grade.",
  press: "Press: ",
  selfReported: "self-reported",
  historyTitle: "Grade history",
  histSite: "Site grade at this date",
  histPp: "Project & process grade at this date",
  scoredOn: "Scored on",
  shareText: "{name} — Site grade: {grade}",
  shareSuffix: ", according to ScoreMyDataCenter",
  related: {
    title: "Other sites to compare",
    sub: "Same operator, {maille}, or simply the closest — scored on the same grid.",
    subMailleFR: "same département",
    subMaille: "same region",
    seeAll: "See the full ranking →",
    // `nearbyMi` sert aux pays qui comptent leurs distances en miles (voir PAYS_EN_MILES
    // dans DcFiche) : la même phrase, l'unité du lieu.
    relation: { operator: "same operator:", region: "same region", regionFR: "same département", nearby: "{km} km away", nearbyMi: "{mi} miles away", nearbyUnder: "less than 1 km away", nearbyUnderMi: "less than a mile away" },
  },
};

/** La table servie au gabarit. `FICHE[lang]` remplace le littéral que chaque
 *  page portait en double. */
export const FICHE: Record<LangueFiche, typeof FR> = { fr: FR, en: EN };
