// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La page d'accueil — la première page qu'un visiteur néerlandais verra (Franck 2026-10-29) — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
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

import type { Langue, LangueDeclaree } from "./langues";
// `nav` n'est pas de la copie : c'est la structure du menu, que le gabarit lit dans `t`. La
// source reste unique (`config/nav.ts`) ; une langue nouvelle y déclarera son menu.
import { FR_NAV, EN_NAV } from "../config/nav";
// 🔴 La table ÉTEND `config/about.ts` par un spread (`...FR_ABOUT`) : une partie de la copie
// de l'accueil vit donc là-bas, et le garde de parité ne l'a jamais vue — un spread n'a pas
// de clés à relever. C'est un second endroit à remplir pour une langue nouvelle, et il est
// désormais nommé ici.
import { FR_ABOUT, EN_ABOUT } from "../config/about";
// Les chiffres de « pourquoi maintenant » sont CALCULÉS au build : la table porte les
// gabarits de phrase, le helper plus bas les remplit.
import { STATS, statView, fmtInt, type Lang } from "../config/stats";

const FR = {
  // ── Les BANDEAUX de l'accueil. Ces quatre composants ne reçoivent que `lang` : ils
  // portaient donc chacun sa petite table en ternaire, invisible à qui cherche les textes du
  // site. Ils ne s'affichent QUE sur l'accueil, et leurs mots vivent donc ici, avec les
  // autres mots de l'accueil — un seul fichier à traduire pour toute la page.
  blocs: {
    actu: { heading: "Dernières actus du secteur", seeAll: "Voir toute l'actu →", href: "/fr/actu/", projet: "Projet", locale: "fr-FR" },
    projets: { heading: "Nouveaux projets repérés", seeAll: "Voir la veille →", href: "/fr/carte/", veille: "en veille", carte: "/fr/carte/" },
    // `{n}` et `{pays}` laissent l'ORDRE libre : une langue peut mettre le nombre après.
    pays: { label: "pays suivis", aria: "{n} pays suivis : {pays}" },
    mur: { fiche: "/fr/dc" },
  },

  // ── Ce que l'accueil choisissait encore par un test de langue, dans le gabarit.
  // Les CHEMINS d'abord : des slugs localisés, pas des mots. Ils vivent avec la copie pour
  // la même raison que les liens du pied de page (`content/chrome.ts`) — une langue nouvelle
  // déclare ses adresses, elle ne modifie pas le gabarit.
  chemins: {
    fiche: "/fr/dc",
    classement: "/fr/classement",
    carte: "/fr/carte/",
    indices: "/fr/indices/",
    indicesPays: "/fr/indices?pays=",
    methodologie: "/fr/methodologie/",
    bibliotheque: "/fr/bibliotheque/",
  },
  // Puis les FORMES : la locale des nombres et le séparateur décimal sont des propriétés de
  // la langue, comme l'espace avant le deux-points.
  formes: { locale: "fr-FR", decimale: "," },
  // Et enfin les MOTS, qui étaient en ternaire au point d'affichage — l'endroit où une
  // langue nouvelle ne va jamais les chercher.
  indices: {
    h2: "Le classement des pays",
    lead: "Cet indice agrège les notes de SITES (le contexte territorial : réseau, eau, foncier, risques). Il ne note ni les opérateurs ni la conduite des projets.",
    reserve: "A réservé · ",
    plus: "Voir la carte et les {n} pays",
  },
  powerUnknown: "puissance non communiquée",

  title: "ScoreMyDataCenter — la note publique d'acceptabilité des data centers",
  description:
    "L'acceptabilité des data centers : notée, sourcée, publique. Une note A–E par site, avec ses sources, sa confiance et une méthode ouverte.",
  altHref: "/",
  altLabel: "EN",
  tagline: "Observatoire indépendant",
  nav: FR_NAV,
  heroEyebrow: "Observatoire indépendant & public",
  heroTitle: "Un data center ne se pose plus n'importe où.<br><span class='hero-red'>Mesurons son risque.</span>",
  heroLede:
    "Les data centers transforment nos territoires. Eau, énergie, foncier, impact local, transparence : ScoreMyDataCenter évalue publiquement le score d'acceptabilité de chaque projet, selon une méthode ouverte et des faits sourcés.",
  heroStandards:
    "Nous sommes indépendants. Nous appliquons les standards de la filière — <strong>PUE</strong> (ISO/IEC&nbsp;30134), énergie, carbone — puis nous mesurons ce qu'ils ignorent : <strong>l'eau, le sol, le territoire</strong>. On obtient un nutri-score pour {n} sites réels.",
  heroChecks: [
    "La note est <strong>gratuite</strong>",
    "La méthode est <strong>publique</strong> (v0.1.0 gelée)",
    "Les sources sont <strong>vérifiables</strong>",
  ],
  corpus: {
    aria: "Le corpus en un coup d'œil",
    label: "Le corpus en un coup d'œil",
    noted: "projets notés",
    countries: "pays couverts",
    stress: "sites en zone de stress hydrique fort ou en crise d'eau",
    watch: "projets « en veille » (oppositions, moratoires)",
    scaleNote: "<strong>Une note A–E pour le site</strong> — ce que le lieu impose : eau, réseau, foncier, voisinage. Et une <strong>seconde note, projet &amp; processus</strong>, pour ce que le porteur annonce et documente : elle n'est calculable que lorsque le dossier du projet est public, ce qui reste rare. Toujours affichées avec leur confiance documentaire.",
  },
  manifesto: {
    aria: "Notre manifeste",
    line1: "Un critique note un film sans l'accord du studio. Un journaliste publie son enquête sans celui de ceux qu'elle dérange. ScoreMyDataCenter s'inscrit dans cette tradition : la liberté de critique et la contribution au débat d'intérêt général.",
    contractLead: "Notre contrat en échange :",
    contract: "une méthode publique, des faits sourcés, des mots mesurés, et un droit permanent à la correction et à la réponse.",
    link: "Lire pourquoi",
  },
  mattersTitle: "Pourquoi ça compte",
  mattersSub: "Un data center n'est pas qu'un bâtiment informatique : c'est un projet qui mobilise des ressources vitales et engage un territoire.",
  matters: [
    { icon: "water", title: "Ressource en eau", body: "<strong>{stress} sites sur {mesures}</strong> sont en zone de stress hydrique fort ou en crise d'eau. L'eau pèse lourd dans les notes du corpus.", href: "/fr/carte/", link: "Voir la carte" },
    { icon: "energy", title: "Réseau électrique", body: "La saturation des réseaux freine les raccordements et dégrade les scores. Des choix d'implantation lourds de conséquences.", href: "/fr/carte/", link: "Voir la carte" },
    { icon: "land", title: "Territoires & biodiversité", body: "Artificialisation, sols, biodiversité : des impacts locaux qui comptent autant que les mégawatts.", href: "/fr/comprendre/", link: "Comprendre les enjeux" },
    { icon: "transparency", title: "Transparence", body: "<strong>{noPower} projets sur {total}</strong> ne communiquent pas leur puissance. Nous notons sur les documents publics — l'opacité ne paie jamais.", href: "/fr/methodologie/", link: "Comprendre la méthode" },
  ],
  principlesTitle: "Notre méthode, en 4 principes",
  exploreTitle: "Explorer les scores",
  exploreSub: "Cherchez. Comparez. Comprenez.",
  exploreMapLabel: "Carte des projets",
  exploreRankLabel: "Classement — position dans la distribution",
  exploreRankMore: "Voir le classement complet",
  exploreLatestLabel: "Les plus puissants suivis",
  exploreLatestMore: "Voir tous les sites",
  searchPlaceholder: "Rechercher un site, un opérateur, un pays…",
  library: {
    title: "Intelligence Library — l'analyse par-dessus les scores",
    coverTitle: "State of Data Center Acceptability in Europe",
    lede: "Le site dit combien. Nos analyses disent où ça va, et ce que ça veut dire.",
    items: ["Tendances pays et Europe", "Risques par thème — eau, énergie, foncier, transparence", "Benchmarks opérateurs"],
    cta: "Découvrir les analyses",
  },
  whoTitle: "Pour qui ? Pour agir.",
  whoSub: "Un même accès, des usages différents — chaque profil a son point d'entrée.",
  who: [
    { name: "Citoyens", line: "Le projet près de chez vous, en clair — la carte.", href: "/fr/carte/" },
    { name: "Journalistes", line: "Des faits sourcés, citables, avec leurs archives.", href: "/fr/classement/" },
    { name: "Élus", line: "Comparer votre commune, préparer le débat.", href: "/fr/classement/" },
    { name: "ONG", line: "Oppositions et moratoires — la couche veille.", href: "/fr/carte?veille=tout" },
    { name: "Chercheurs", line: "La méthode, les données, tout se recalcule.", href: "/fr/methodologie/" },
    { name: "Opérateurs", line: "Corriger, répondre — et améliorer le projet réel.", href: "/fr/contact/" },
  ],
  heroScaleLabel: "L'échelle d'acceptabilité",
  ctaScores: "Voir les notes",
  mapOpen: "Ouvrir la carte",
  mapReserved: "· A réservé",
  viewFiche: "Voir la fiche →",
  ctaMethod: "Lire la méthode",
  panelAria: "Exemple de fiche de score",
  siteScore: "Site",
  operatorScore: "Opérateur",
  insufficient: "données insuffisantes",
  confidence: { high: "confiance : haute", medium: "confiance : moyenne", low: "confiance : faible" },
  fixtureNote:
    "Fixture de test fictive, montrée pour le format — les premières fiches réelles françaises sont en préparation.",
  whyNowAria: "Pourquoi maintenant",
  whyNow: {
    // 🔴 RÈGLE SIGNÉE PAR FRANCK (2026-10-30) : « même trio partout, périmètre = le pays de
    // la langue, Europe en repli ». Avant, les deux accueils ne disaient pas la même chose —
    // le français publiait le PUE, l'anglais le stress hydrique — et personne ne l'avait vu
    // parce que ces trois chiffres vivaient dans une const de PAGE, hors de l'objet `t`.
    //
    // LE TRIO EST CELUI QUE LA MESURE AUTORISE, pas un choix de goût. Mesuré sur stats.json :
    // `water_stress_high` existe dans TOUS les périmètres ; `grid_saturated` et
    // `pue_published` dans FR, NL et Europe seulement. Les trois sont des PARTS, donc jamais
    // un zéro trompeur.
    // 🔴 Et `pipeline` sort du trio pour cette raison exacte : aux Pays-Bas il vaut 0 MW —
    // un trou de collecte, pas une absence de projets. L'accueil néerlandais aurait publié
    // « 0 MW annoncés en pipeline », c'est-à-dire une lecture ratée présentée comme une
    // mesure. Le chiffre reste sur la page « Les chiffres du parc », où son n est visible.
    perimetre: "FR" as string,
    repli: "europe" as string | null,
    stats: [
    { genre: "vue", id: "grid_saturated", figure: "{big} sur poste électrique saturé",
      attribution: "Les chiffres du parc · {src} · n = {n}", url: "/fr/chiffres#reseau-sature" },
    { genre: "vue", id: "pue_published", figure: "{big} publient leur PUE",
      attribution: "Les chiffres du parc · déclarations opérateurs · n = {n}", url: "/fr/chiffres#pue-publie" },
    { genre: "vue", id: "water_stress_high", figure: "{big} en zone de stress hydrique fort",
      attribution: "Les chiffres du parc · {src} · n = {n}", url: "/fr/chiffres#stress-hydrique" },
    ],
  },
  whyNowPunch: "Le sujet le plus chaud de l'IA n'a aucun arbitre indépendant. <b>Nous le sommes.</b>",
  missionLine:
    "Notre mission : mesurer, sourcer et rendre publique l'acceptabilité de chaque projet de data center. Ancrer le débat dans les faits.",
  whyTitle: "Pourquoi cet observatoire",
  whyMotto: "Nous ne demandons pas la permission de publier nos notes. Nous nous imposons la méthode.",
  whyLede: "Un data center de 900 MW s'annonce près de chez vous. Où lire, clairement, ce qu'il vaut ? Son impact local ?",
  whyBody:
    "Les cartes existantes alignent des caractéristiques techniques ; les observatoires de contestation comptent les conflits. Personne ne met à plat, projet par projet, la réalité de chaque dossier : une note, des sources, une méthode que chacun peut vérifier et refaire. C'est ce vide que ScoreMyDataCenter comble : <span class='hl-red'>la première note d'acceptabilité indépendante, publique et opposable</span> — une notation factuelle, sourcée et méthodique, publiée au titre de la contribution au débat d'intérêt général. Et une échelle qui engage : <b>le <i class='gl gl-a'>A</i> se prouve en exploitation, il ne se promet pas</b> — les promesses, même excellentes, plafonnent en <i class='gl gl-b'>B</i> ; seule la preuve vérifiée fait le <i class='gl gl-a'>A</i>. Notre mission : <b>scorer tous les data centers</b> — méthodiquement, publiquement, un dossier à la fois.",
  ...FR_ABOUT,
  principlesAria: "Principes",
  principles: [
    { title: "Méthode publique", body: "Grille de notation ouverte, versionnée, citable. Quiconque peut refaire chaque note." },
    { title: "Données traçables", body: "Chaque valeur pointe vers sa source. L'annoncé n'est jamais fusionné avec le mesuré." },
    { title: "Correction et réponse de l'opérateur", body: "Une donnée semble inexacte ? Elle peut être signalée avec sa source. Après vérification, la fiche est corrigée et la modification datée. L'opérateur peut également transmettre une réponse, publiée dans un espace dédié." },
    { title: "Indépendance", body: "Les entités notées ne paient jamais leur note. Aucune influence, ni pour ni contre : la note suit la méthode." },
  ],
  scoresTitle: "Derniers projets notés",
  scoresLede:
    "Une page citable par projet : deux notes, cinq sous-scores par pilier, confiance documentaire, sources et historique complet.",
  demo: {
    kicker: "La note, en train de se faire",
    caption: "Cas réel : {name} — les cinq piliers, la note du site, puis la lettre. Méthode publique, données sourcées.",
    sr: "Animation : la fiche de {name} se note — les cinq sous-scores de pilier apparaissent, la note du site se remplit, puis la lettre s'estampille.",
    replay: "Rejouer",
    why: "Pourquoi ce site ? Sa note ({score}/100) est la plus proche de la médiane des {n} sites du corpus : c'est le site le plus ordinaire d'Europe, ni vitrine ni cas d'école. La règle de sélection est mécanique et publiée.",
  },
  status: { announced: "Annoncé", permitting: "En instruction", under_construction: "En construction", operational: "En service", unknown: "Statut non établi" },
  fixtureTag: "Fixture de test fictive",
  pillarShort: {
    energy: "Énergie",
    water: "Eau",
    land_biodiversity: "Foncier",
    local_impact: "Local",
    transparency_governance: "Transp.",
  },
  repoUrl: "https://github.com/bardolfranck/scoremydatacenter",
  methodTitle: "Une méthode, deux notes, toujours avec la confiance.",
  methodLede:
    "26 indicateurs en 5 piliers, séparés entre ce que le projet <span class='term'>subit</span> et ce que l'opérateur <span class='term'>choisit</span>. La grille, ses poids et ses seuils sont <a href='https://github.com/bardolfranck/scoremydatacenter/tree/main/data/methodology'>publics et téléchargeables</a>.",
  methodPedago: "Comprendre la note, pas à pas",
  siteScoreExplain: "Le contexte que le projet <span class='term'>subit</span> : intensité carbone du réseau électrique, stress hydrique, foncier, tissu local et économie de la commune.",
  operatorScoreExplain: "Les leviers que l'opérateur <span class='term'>choisit</span> : efficacité énergétique, refroidissement, emplois, concertation, transparence.",
  confidenceTitle: "Confiance documentaire",
  confidenceExplain:
    "Une note ne s'affiche jamais sans elle. Sous 40 % de couverture, on écrit « données insuffisantes ». On ne note pas l'inconnu.",
  weightsAria: "Poids des piliers",
  weightsCaption: "Poids du pilier dans la note globale",
  weightsNote: "Méthodologie publique, versionnée et datée — antériorité vérifiable.",
  openTitle: "On ouvre la vérité.",
  openLede: "La couche qui fabrique le jugement est ouverte : méthode, données et moteur, vérifiables par quiconque.",
  openCta: "Voir le code sur GitHub",
  openCols: [
    {
      title: "Méthode, données et moteur ouverts",
      body: "Moteur <span class='lic' tabindex='0'>AGPL<span class='info-tip'>Le code du moteur est libre : quiconque l'améliore doit repartager ses améliorations.</span></span>, données publiées <span class='lic' tabindex='0'>ODbL<span class='info-tip'>Base de données ouverte : réutilisable librement, à condition de citer la source et de partager à l'identique.</span></span>, méthodologie <span class='lic' tabindex='0'>CC BY-SA<span class='info-tip'>Contenu libre : réutilisable en citant l'auteur et en partageant aux mêmes conditions.</span></span>. Le code est <a href='https://github.com/bardolfranck/scoremydatacenter'>public sur GitHub</a> : n'importe qui peut refaire chaque note, en toute rigueur.",
    },
    {
      title: "On aide le projet, jamais la note",
      body: "Les entités notées ne paient jamais leur note publique. Un opérateur peut faire analyser son projet ; mais la note ne bouge que si le projet réel change — jamais parce qu'il a payé. « Il paie, la note monte » est structurellement exclu.",
    },
    {
      title: "Journal d'audit public",
      body: "Chaque notation, révision et correction est datée, versionnée et justifiée. Une note ne bouge jamais en silence.",
    },
    {
      title: "Contributions gouvernées",
      body: "Les corrections de données sont gratuites et relues. Pour empêcher qu'on manipule une note, nos règles de détection sont publiques dans leur principe ; leurs seuils chiffrés, eux, restent confidentiels — les afficher reviendrait à donner le mode d'emploi pour passer entre les mailles.",
    },
  ],
  redline: "Notre engagement : la note d'un projet et sa justification sont <b>publiques et gratuites, pour toujours</b>.",
  faqTitle: "Questions fréquentes",
  faq: [
    {
      // RENVOI CROISÉ, PAS DOUBLON (Franck, 2026-10-22) : la procédure est traitée en entier
      // dans « Droits et calendrier » sur /fr/comprendre. Cette entrée répond à la question
      // telle qu'elle se pose — « un projet arrive, par où commencer ? » — en trois lignes,
      // et renvoie. Le reste de cette FAQ parle de NOTRE note ; celle-ci parle de leur projet.
      q: "Un projet est annoncé près de chez moi. Par où commencer ?",
      a: "Par le calendrier, parce qu'il décide de tout : la même question posée en concertation peut changer le projet, posée après l'autorisation elle ne change plus rien. Les délais de recours sont de <b>deux mois</b> — à compter du premier jour d'affichage pour un permis de construire, de la dernière formalité accomplie pour une autorisation environnementale. Et quand le site fonctionne déjà, il reste la réclamation au préfet sur les <i>prescriptions</i> (bruit, rejets, eau). Tout le parcours, étape par étape, est dans <a href='/fr/comprendre#droits'>Droits et calendrier</a>, avec les textes.",
    },
    {
      q: "Le nutri-score des DC. Comment un data center est-il noté ?",
      a: "Chaque projet reçoit deux notes <i class='gl gl-a'>A</i>–<i class='gl gl-e'>E</i> — une pour le site, une pour l'opérateur — à partir de 26 indicateurs répartis en 5 piliers (énergie, eau, foncier, impact local, transparence). Un score chiffré est calculé puis traduit en lettre, exactement comme pour le nutri-score alimentaire que tout le monde connaît ; à côté, un niveau de confiance indique si la note repose sur des données solides ou fragiles.",
    },
    {
      q: "Qu'est-ce qui sépare un data center noté A d'un data center noté B ?",
      a: "Le nombre de piliers en tension, et leur gravité. <b>A</b> : aucune faiblesse marquée sur les piliers publiés de la fiche. <b>B</b> : solide, avec une ombre. <b>C</b> : deux tensions nettes. <b>D</b> et <b>E</b> : plusieurs piliers dans le rouge, ou une tension majeure à elle seule. Comme pour le nutri-score alimentaire, la lettre résume plusieurs critères d'un coup — et un seul critère très mauvais suffit à la tirer vers le bas. Une précision qui compte : le plafond ne se lève que sur preuve vérifiée par un tiers, et <b>aucun site d'Europe n'atteint A aujourd'hui</b>.",
    },
    {
      q: "Pourquoi ne publiez-vous pas les seuils chiffrés de la note ?",
      a: "Pour que la note ne soit pas truquable. Nous publions la grille, les poids des 5 piliers, les sources de chaque indicateur et, sur chaque fiche, le facteur qui pèse le plus sur la note — donc ce qui compte et dans quel sens. Nous ne publions pas la position exacte des seuils : avec elle, un porteur de projet pourrait viser la lettre au lieu de viser le terrain. La méthode est vérifiable, la recette n'est pas optimisable.",
    },
    {
      q: "Que veulent dire les deux notes, « site » et « opérateur » ?",
      a: "La note site évalue ce que le projet subit — territoire, eau, réseau, foncier — quel que soit celui qui le porte. La note opérateur évalue ce qu'il choisit — efficacité, concertation, transparence, engagements. On sépare le terrain des décisions.",
    },
    {
      q: "Puis-je faire noter le projet près de chez moi ?",
      a: "Oui. Suggérez-le via la <a href='#contact'>page Contact</a> : nous priorisons les dossiers les plus documentés et les plus discutés. Précision d'indépendance : nous ne notons jamais sur commande d'une partie, ni pour ni contre — la note suit la méthode, pas le demandeur.",
    },
    {
      q: "D'où viennent les données ?",
      a: "De sources publiques : réseau électrique, eau, foncier, INSEE, registres, presse locale. Chaque valeur affichée pointe vers sa source, et la méthode est ouverte : n'importe qui peut refaire le calcul.",
    },
    {
      q: "Pourquoi les projets américains n'ont-ils pas (encore) de note ?",
      a: "Parce que la profondeur suit la donnée. Une note exige des seuils calibrés pays par pays (réseau électrique, eau, foncier, registres, procédures) et un canal de correction et de réponse opérationnel — c'est le cas aujourd'hui en Europe. Aux États-Unis, nous publions d'abord la couche « en veille » : oppositions citoyennes ✋🏼 et moratoires ⏸️ — des faits sourcés, jamais une note. Les premières notes américaines viendront quand les données et la calibration seront au niveau, pas avant : nous ne notons pas l'inconnu.",
    },
    {
      q: "Un opérateur peut-il payer pour améliorer sa note ?",
      a: "Non, jamais. Les entités notées ne paient pas leur note. La note d'un projet et sa justification sont publiques et gratuites, pour toujours.",
    },
    {
      q: "Pourquoi aucun data center n'a-t-il (encore) la note <i class='gl gl-a'>A</i> ?",
      a: "Parce qu'un <i class='gl gl-a'>A</i> se prouve, il ne se promet pas : il est réservé aux valeurs vérifiées en exploitation. Un dossier entièrement déclaratif, même excellent, plafonne en <i class='gl gl-b'>B</i> — « annoncé ≠ mesuré ». Un opérateur obtient son <i class='gl gl-a'>A</i> en apportant une preuve tierce (déclaration EED au régulateur, audit ISO/IEC 30134 par un organisme accrédité — jamais une page marketing) via le canal public de correction : la donnée passe alors d'« annoncée » à « mesurée », le plafond saute, et le re-score est tracé au journal d'audit. Le <i class='gl gl-a'>A</i> ne s'achète pas et ne se déclare pas : il se démontre. Et la preuve fait monter la note projet & processus — jamais celle du site : le territoire est subi, il ne se prouve pas.",
    },
    {
      q: "Pourquoi nous publions sans demander la permission",
      a: "Un critique note un film sans l'accord du studio. Un journaliste publie son enquête sans celui de ceux qu'elle dérange. ScoreMyDataCenter s'inscrit dans cette tradition : la liberté de critique et la contribution au débat d'intérêt général. La note relève de la liberté de critique ; sa solidité dépend de la transparence de la méthode, de la qualité des sources et de la mesure des mots. Nous ne demandons pas la permission de publier une évaluation indépendante. En échange, nous nous imposons une méthode publique, des faits sourcés, des mots mesurés et un droit permanent à la correction et à la réponse.",
    },
    {
      q: "Et si une donnée est inexacte, ou si l'opérateur n'est pas d'accord ?",
      a: "Deux outils distincts : la correction factuelle — toute donnée est corrigée sur preuve, la modification est datée, et si le calcul est affecté la note est recalculée à version de méthode constante — et la réponse de l'opérateur, publiée dans un espace dédié, clairement attribuée et datée. La publication d'une réponse ne modifie pas automatiquement la note : celle-ci évolue uniquement lorsque des faits nouveaux ou corrigés changent le résultat obtenu par la méthode.",
    },
    {
      q: "Un opérateur peut-il demander le retrait de sa fiche ?",
      a: "Une donnée fausse est corrigée sur preuve, et l'opérateur peut transmettre une réponse publiée à côté de la note. Mais une note sourcée et méthodique ne se retire pas sur demande : la retirer parce qu'elle déplaît reviendrait à la vendre en creux. La note reste ; la contradiction s'ajoute.",
    },
    {
      q: "La note est-elle un verdict définitif ?",
      a: "Non : c'est une note de risque d'acceptabilité, assortie d'un niveau de confiance, et elle peut évoluer avec le projet. Le score chiffré est publié pour rendre le calcul transparent, mais c'est la lettre <i class='gl gl-a'>A</i>–<i class='gl gl-e'>E</i> qui fait foi — la note applique une grille experte, sourcée et versionnée ; elle ne prétend pas à l'exactitude d'un oracle.",
    },
    {
      q: "La note évolue-t-elle avec le progrès technique ? Un data center bien noté aujourd'hui le sera-t-il encore dans dix ans ?",
      a: "Oui, et c'est voulu. Une note change pour deux raisons : le projet évolue (nouvelles données), ou l'étalon évolue avec l'état de l'art. Nos seuils s'ancrent sur des normes qui se durcissent avec le temps (ISO, réglementation européenne) : un <i class='gl gl-a'>A</i> signifie toujours « le meilleur atteignable aujourd'hui », pas « le meilleur de 2026 ». Sans cela, tout le monde finirait <i class='gl gl-a'>A</i> à mesure que la technologie progresse — c'est précisément pourquoi l'étiquette énergie européenne a été remise à zéro en 2021, quand presque tous les appareils étaient devenus A+++. Chaque note est donc datée et rattachée à une version de méthode : un data center excellent en 2026 pourra être « moyen » aux standards de 2036 — et c'est exactement le rôle du score : récompenser le progrès, et signaler ce qui vieillit.",
    },
    {
      q: "Qui sont les acteurs de la filière data center ?",
      a: "Plusieurs familles, qui se croisent souvent sur un même projet. <b>Développeurs et aménageurs</b> : ils trouvent le terrain, obtiennent les autorisations et le raccordement, puis vendent ou louent. <b>Opérateurs de colocation</b> : ils exploitent des data centers et y louent de l'espace, de l'énergie et de la connectivité à leurs clients. <b>Hyperscalers</b> : les géants du cloud, qui construisent et exploitent leurs propres campus. <b>Néoclouds IA</b> : des fournisseurs spécialisés qui louent de la puissance de calcul pour l'intelligence artificielle. <b>Énergéticiens et gestionnaires de réseau</b> : ils produisent et fournissent l'électricité, et raccordent le site (RTE pour le transport, Enedis pour la distribution). <b>Constructeurs et équipementiers</b> : ils bâtissent et fournissent refroidissement, alimentation de secours, serveurs. <b>Collectivités et État</b> : la commune ou l'intercommunalité fixe les règles d'urbanisme et délivre en général le permis de construire ; le préfet instruit l'autorisation environnementale. <b>Investisseurs et foncières</b> : fonds et sociétés immobilières qui financent ou possèdent les murs.",
    },
    {
      q: "Comment distinguer les acteurs de la filière : développeur ou opérateur ?",
      a: "Le développeur prépare le terrain et le bâtiment (foncier, permis, raccordement) puis le vend ou le loue ; l'opérateur fait tourner les serveurs dedans et vend l'hébergement à des clients. L'analogie : le promoteur immobilier et l'hôtelier — l'un construit l'hôtel, l'autre le fait vivre. Les deux à la fois, ça existe ? Oui, et c'est même le modèle dominant des gros : Data4, Equinix, Digital Realty développent et opèrent leurs campus. Les purs développeurs sont plutôt les entrants immobiliers : H&DC, Prologis, Goodman, Segro, Altarea — ils viennent de la logistique ou de la promotion. Un site annoncé par un développeur est donc, par nature, un projet immobilier, pas un data center en service.",
    },
    {
      q: "Qui parle à la commune, et qui n'y parle jamais ?",
      a: "Cinq rôles — et surtout : qui parle au territoire, et qui ne lui parle jamais. <b>Le développeur</b> (ou aménageur) monte l'opération — foncier, permis, raccordement — construit, puis vend ou loue. C'est lui qui vient voir le maire, au début ; souvent il disparaît une fois le permis obtenu. <b>Le propriétaire</b> détient les murs (une foncière, un fonds) : il ne parle à personne localement, mais c'est lui qui encaisse. <b>L'opérateur</b> commercialise — il loue salles, énergie et connectivité à des clients : c'est le nom affiché sur la fiche, et l'interlocuteur du territoire une fois le site en service. <b>L'exploitant</b> fait tourner le bâtiment au quotidien (refroidissement, électricité, maintenance), souvent un prestataire sous-traitant invisible du public — mais c'est lui qui gère le bruit et les groupes de secours, donc ce qui gêne les riverains. <b>Le client final</b> loue les salles ou la puissance (une banque, un hyperscaler, un néocloud qui revend encore derrière) : il ne parle jamais à la commune et son nom est rarement public. Chez les gros, les trois premiers rôles sont souvent la même entreprise — Data4, Equinix, Digital Realty développent et exploitent leurs campus ; chez les entrants venus de l'immobilier, ils sont séparés. <b>Ce que ça change pour un élu :</b> celui qui promet les emplois et la chaleur récupérée n'est pas celui qui les livrera, et celui qui consomme vraiment n'est presque jamais dans la salle.",
    },
    {
      q: "Quelles sont les étapes d'un projet de data center, de l'annonce à la mise en service ?",
      a: "En France, schématiquement : 1) l'annonce et, parfois, une concertation préalable ; 2) le dépôt des demandes — permis de construire et, le plus souvent, autorisation environnementale au titre des installations classées (ICPE) ; 3) l'instruction : avis de l'autorité environnementale, puis enquête publique ; 4) la décision : permis délivré par le maire (ou par le préfet dans certains cas), autorisation environnementale par arrêté préfectoral ; 5) les délais de recours ; 6) les travaux, souvent par phases ; 7) la mise en service, puis les contrôles pendant l'exploitation. Les étapes peuvent se chevaucher, et un projet peut s'arrêter à chacune d'elles. Les droits du public à chaque étape : <a href='/fr/comprendre#droits'>Droits et calendrier</a>.",
    },
    {
      q: "Qu'est-ce qu'un « moratoire » sur les data centers ? Est-ce que ça arrête un projet ?",
      a: "Le mot recouvre des réalités très différentes. Un vœu ou une délibération politique demandant une pause n'a pas, à lui seul, d'effet juridique sur une autorisation déjà délivrée. Il existe en revanche un outil juridique : le <b>sursis à statuer</b>. Quand un plan local d'urbanisme est en cours d'élaboration ou de révision, la commune peut différer sa réponse à une demande de permis, pour deux ans au plus (code de l'urbanisme, art. L.424-1). Une pause générale à l'échelle nationale supposerait, elle, un texte de loi ou de règlement. Sur ce site, un moratoire est signalé comme un fait sourcé, jamais comme une note.",
    },
    {
      q: "Qui peut arrêter un chantier ? Que peut décider le tribunal administratif ?",
      a: "Plusieurs voies, aux effets différents. <b>Le tribunal administratif</b> : un recours contre un permis ou une autorisation n'arrête pas les travaux à lui seul. Pour les suspendre rapidement, il faut un <b>référé-suspension</b>, accordé seulement en cas d'urgence et de doute sérieux sur la légalité (code de justice administrative, art. L.521-1). Sur le fond, le juge peut annuler l'autorisation, ou laisser au porteur de projet un délai pour corriger une irrégularité qui peut l'être (code de l'urbanisme, art. L.600-5-1). Ces décisions peuvent en principe être contestées en appel, puis devant le Conseil d'État. <b>Le maire ou le préfet</b> : ils peuvent ordonner l'interruption de travaux réalisés sans autorisation ou non conformes (code de l'urbanisme, art. L.480-2) ; pour une installation classée, le préfet peut mettre en demeure l'exploitant, puis suspendre l'activité (code de l'environnement, art. L.171-8). <b>Le porteur de projet</b>, enfin, peut suspendre ou abandonner, pour des raisons financières, techniques ou commerciales.",
    },
    {
      q: "Un projet suspendu ou en moratoire peut-il redémarrer ?",
      a: "Oui, dans plusieurs cas : le sursis à statuer prend fin (à son terme, la commune doit se prononcer dans les deux mois si le demandeur confirme sa demande) ; une suspension est levée par le juge ; l'autorisation est régularisée ; une annulation est infirmée en appel ; ou le porteur dépose un nouveau dossier. À l'inverse, un permis de construire se périme : en règle générale si les travaux ne commencent pas dans les trois ans, ou s'ils sont interrompus plus d'un an ; ce délai peut être prolongé deux fois d'un an (code de l'urbanisme, art. R.424-17 et R.424-21). Un projet à l'arrêt n'est donc pas forcément un projet abandonné — c'est pourquoi nous ne le retirons jamais sans source.",
    },
    {
      q: "Que veut dire « annoncé » sur une fiche ?",
      a: "Que le data center n'est pas encore en service : projet rendu public, en cours d'autorisation ou en travaux. Tant qu'il n'est pas en service, il ne reçoit pas de note définitive mais une fourchette provisoire, calculée sur ce que le territoire subit.",
    },
    {
      q: "Qui êtes-vous, et comment restez-vous indépendants ?",
      a: "Un observatoire indépendant fondé par Franck Bardol. La méthode est ouverte, les entités notées ne paient pas, et notre fonctionnement est détaillé dans la section <a href='#open'>Modèle ouvert</a>.",
    },
  ],
  contactTitle: "Suggérer un projet, ou joindre l'observatoire.",
  contactCta: "Contact",
};

const EN: typeof FR = {
  blocs: {
    actu: { heading: "Latest sector news", seeAll: "See all news →", href: "/news/", projet: "Project", locale: "en-GB" },
    projets: { heading: "Newly flagged projects", seeAll: "See the watch →", href: "/map/", veille: "watching", carte: "/map/" },
    pays: { label: "countries tracked", aria: "{n} countries tracked: {pays}" },
    mur: { fiche: "/dc" },
  },

  chemins: {
    fiche: "/dc",
    classement: "/ranking",
    carte: "/map/",
    indices: "/indices/",
    indicesPays: "/indices?pays=",
    methodologie: "/methodology/",
    bibliotheque: "/intelligence/",
  },
  formes: { locale: "en-US", decimale: "." },
  indices: {
    h2: "The country ranking",
    lead: "This index aggregates SITE grades (the territorial context: grid, water, land, hazards). It grades neither operators nor how projects are run.",
    reserve: "A reserved · ",
    plus: "See the map and all {n} countries",
  },
  powerUnknown: "power not disclosed",

  title: "ScoreMyDataCenter — the public score for data center acceptability",
  description:
    "Data center acceptability: graded, sourced, public. An A–E grade per site, with its sources, its confidence and an open method.",
  altHref: "/fr/",
  altLabel: "FR",
  tagline: "Independent observatory",
  nav: EN_NAV,
  heroEyebrow: "Independent, public observatory",
  heroTitle: "A data center can no longer be built just anywhere.<br><span class='hero-red'>Let's measure its risk.</span>",
  heroLede:
    "Data centers are transforming our territories. Water, energy, land, local impact, transparency: ScoreMyDataCenter publicly assesses the acceptability score of every project, with an open method and sourced facts.",
  heroStandards:
    "We are independent. We apply the industry's own standards — <strong>PUE</strong> (ISO/IEC&nbsp;30134), energy, carbon — then we measure what they leave out: <strong>water, land, territory</strong>. The result is a Nutri-Score for {n} real sites.",
  heroChecks: [
    "The grade is <strong>free</strong>",
    "The method is <strong>public</strong> (v0.1.0 frozen)",
    "The sources are <strong>verifiable</strong>",
  ],
  corpus: {
    aria: "The corpus at a glance",
    label: "The corpus at a glance",
    noted: "scored projects",
    countries: "countries covered",
    stress: "sites in a high water-stress or water-crisis basin",
    watch: "projects on watch (oppositions, moratoria)",
    scaleNote: "<strong>An A–E grade for the site</strong> — what the location imposes: water, grid, land, neighbours. And a <strong>second grade, project &amp; process</strong>, for what the developer announces and documents: it can only be computed when the project's dossier is public, which remains rare. Always shown with their documentary confidence.",
  },
  manifesto: {
    aria: "Our manifesto",
    line1: "A critic reviews a film without the studio's approval. A journalist publishes an investigation without the consent of those it disturbs. ScoreMyDataCenter belongs to that tradition: freedom of criticism and contribution to the public-interest debate.",
    contractLead: "Our contract in return:",
    contract: "a public method, sourced facts, measured words, and a permanent right to correction and response.",
    link: "Read why",
  },
  mattersTitle: "Why it matters",
  mattersSub: "A data center is not just an IT building: it is a project that mobilises vital resources and commits a territory.",
  matters: [
    { icon: "water", title: "Water resource", body: "<strong>{stress} sites out of {mesures}</strong> sit in a high water-stress or water-crisis basin. Water weighs heavily in the corpus grades.", href: "/map/", link: "See the map" },
    { icon: "energy", title: "Power grid", body: "Grid saturation slows connections and degrades scores. Siting choices with heavy consequences.", href: "/map/", link: "See the map" },
    { icon: "land", title: "Land & biodiversity", body: "Artificialisation, soils, biodiversity: local impacts that matter as much as megawatts.", href: "/understand/", link: "Understand the stakes" },
    { icon: "transparency", title: "Transparency", body: "<strong>{noPower} projects out of {total}</strong> do not disclose their power. We grade on public documents — opacity never pays.", href: "/methodology/", link: "Understand the method" },
  ],
  principlesTitle: "Our method, in 4 principles",
  exploreTitle: "Explore the scores",
  exploreSub: "Search. Compare. Understand.",
  exploreMapLabel: "Map of the projects",
  exploreRankLabel: "Ranking — position in the distribution",
  exploreRankMore: "See the full ranking",
  exploreLatestLabel: "Highest-power tracked",
  exploreLatestMore: "See every site",
  searchPlaceholder: "Search a site, an operator, a country…",
  library: {
    title: "Intelligence Library — the analysis above the scores",
    coverTitle: "State of Data Center Acceptability in Europe",
    lede: "The site says how much. Our analyses say where it's heading, and what it means.",
    items: ["Country and Europe trends", "Risks by theme — water, energy, land, transparency", "Operator benchmarks"],
    cta: "Discover the analyses",
  },
  whoTitle: "For whom? To act.",
  whoSub: "One access, different uses — every profile has its entry point.",
  who: [
    { name: "Citizens", line: "The project near you, in plain terms — the map.", href: "/map/" },
    { name: "Journalists", line: "Sourced, quotable facts, with their archives.", href: "/ranking/" },
    { name: "Elected officials", line: "Compare your municipality, prepare the debate.", href: "/ranking/" },
    { name: "NGOs", line: "Oppositions and moratoria — the watch layer.", href: "/map?veille=tout" },
    { name: "Researchers", line: "The method, the data — everything recomputes.", href: "/methodology/" },
    { name: "Operators", line: "Correct, respond — and improve the real project.", href: "/contact/" },
  ],
  heroScaleLabel: "The acceptability scale",
  ctaScores: "See the scores",
  mapOpen: "Open the map",
  mapReserved: "· A reserved",
  viewFiche: "View the fiche →",
  ctaMethod: "Read the method",
  panelAria: "Example scorecard",
  siteScore: "Site",
  operatorScore: "Operator",
  insufficient: "insufficient data",
  confidence: { high: "confidence: high", medium: "confidence: medium", low: "confidence: low" },
  fixtureNote:
    "Fictional test fixture, shown for format only — the first real French scorecards are in preparation.",
  whyNowAria: "Why now",
  whyNow: {
    // L'anglais n'est le pays de personne : son périmètre est l'Europe, qui est aussi le
    // repli des autres langues (règle Franck, 2026-10-30).
    perimetre: "europe",
    repli: null,
    stats: [
    { genre: "vue", id: "grid_saturated", figure: "{big} on already-saturated substations",
      attribution: "Fleet figures · {src} · n = {n}", url: "/figures#reseau-sature" },
    { genre: "vue", id: "pue_published", figure: "{big} publish their PUE",
      attribution: "Fleet figures · operators' declarations · n = {n}", url: "/figures#pue-publie" },
    { genre: "vue", id: "water_stress_high", figure: "{big} under high water stress",
      attribution: "Fleet figures · WRI Aqueduct · n = {n}", url: "/figures#stress-hydrique" },
    ],
  },
  whyNowPunch: "The hottest issue in AI infrastructure has no independent referee. <b>Now it does.</b>",
  missionLine:
    "Our mission: measure, source and make public the acceptability of every data center project — grounding the debate in facts.",
  whyTitle: "Why this observatory",
  whyMotto: "We don't ask permission to publish our scores. We hold ourselves to the method.",
  whyLede: "A 900 MW data center is announced near you. Where do you read, clearly, what it's worth? Its local impact?",
  whyBody:
    "Existing maps list technical specifications; conflict trackers count disputes. No one lays out, project by project, the reality of each case: a grade, sources, a method anyone can verify and recompute. That is the gap ScoreMyDataCenter fills: <span class='hl-red'>the first independent acceptability grade, public and contestable</span> — factual, sourced and methodical ratings, published as a contribution to the public-interest debate. And a scale with teeth: <b>an <i class='gl gl-a'>A</i> is proven in operation, never promised</b> — even excellent promises cap at <i class='gl gl-b'>B</i>; only verified proof earns the <i class='gl gl-a'>A</i>. Our mission: <b>score every data center</b> — methodically, publicly, one file at a time.",
  ...EN_ABOUT,
  principlesAria: "Core principles",
  principles: [
    { title: "Public method", body: "Open scoring grid, versioned and citable. Anyone can re-run every grade." },
    { title: "Traceable data", body: "Every value links to its source. Announced claims are never merged with measured facts." },
    { title: "Correction and operator response", body: "A data point seems inaccurate? It can be reported with its source. After verification, the datasheet is corrected and the change dated. The operator can also send a response, published in a dedicated space." },
    { title: "Independence", body: "Scored entities never pay for their grade. No influence, for or against: the grade follows the method." },
  ],
  scoresTitle: "Latest scored projects",
  scoresLede:
    "A citable page per project: two grades, five pillar sub-scores, documentation confidence, sources and full history.",
  demo: {
    kicker: "A grade, being made",
    caption: "Real case: {name} — five pillars, the site score, then the letter. Public method, sourced data.",
    sr: "Animation: {name}'s fiche gets graded — the five pillar sub-scores appear, the site score fills, then the letter stamps in.",
    replay: "Replay",
    why: "Why this site? Its score ({score}/100) sits closest to the median of the {n} sites in the corpus: the most ordinary site in Europe, neither showcase nor cautionary tale. The selection rule is mechanical and published.",
  },
  status: { announced: "Announced", permitting: "Permitting", under_construction: "Under construction", operational: "Operational", unknown: "Status not established" },
  fixtureTag: "Fictional test fixture",
  pillarShort: {
    energy: "Energy",
    water: "Water",
    land_biodiversity: "Land",
    local_impact: "Local",
    transparency_governance: "Transp.",
  },
  repoUrl: "https://github.com/bardolfranck/scoremydatacenter",
  methodTitle: "One method, two grades, always with confidence.",
  methodLede:
    "26 indicators across 5 pillars, split between what a project <span class='term'>endures</span> and what its operator <span class='term'>chooses</span>. The grid, its weights and its thresholds are <a href='https://github.com/bardolfranck/scoremydatacenter/tree/main/data/methodology'>public and downloadable</a>.",
  methodPedago: "Understand the grade, step by step",
  siteScoreExplain: "The context the project <span class='term'>endures</span>: the electricity grid's carbon intensity, water stress, land, local fabric and the town's economy.",
  operatorScoreExplain: "The levers the operator <span class='term'>chooses</span>: energy efficiency, cooling, jobs, consultation, transparency.",
  confidenceTitle: "Documentation confidence",
  confidenceExplain:
    "A grade never appears without it. Below 40% coverage we say “insufficient data”. We do not grade the unknown.",
  weightsAria: "Pillar weights",
  weightsCaption: "Pillar weight in the global grade",
  weightsNote: "Public, versioned and dated methodology — verifiable anteriority.",
  openTitle: "We open the truth.",
  openLede: "The layer that produces the judgment is open: method, data and engine, verifiable by anyone.",
  openCta: "See the code on GitHub",
  openCols: [
    {
      title: "Open method, data and engine",
      body: "<span class='lic' tabindex='0'>AGPL<span class='info-tip'>The engine code is free: anyone who improves it must share those improvements back.</span></span> engine, <span class='lic' tabindex='0'>ODbL<span class='info-tip'>Open database: freely reusable, provided you credit the source and share alike.</span></span> published data, <span class='lic' tabindex='0'>CC BY-SA<span class='info-tip'>Free content: reusable if you credit the author and share under the same terms.</span></span> methodology. The code is <a href='https://github.com/bardolfranck/scoremydatacenter'>public on GitHub</a>: anyone can recompute every grade, with full rigor.",
    },
    {
      title: "We help the project, never the grade",
      body: "Scored entities never pay for their public grade. An operator may have its project analysed; but the grade moves only when the real project changes — never because it paid. \"Pay to raise the grade\" is structurally impossible.",
    },
    {
      title: "Public audit log",
      body: "Every scoring, revision and correction is dated, versioned and justified. Grades cannot move silently.",
    },
    {
      title: "Governed contributions",
      body: "Data corrections are free and reviewed. To stop anyone from gaming a grade, our detection rules are public in principle; their numeric thresholds stay confidential — publishing them would hand out the manual for slipping through.",
    },
  ],
  redline: "Our commitment: a project's grade and its justification are <b>public and free, forever</b>.",
  faqTitle: "Frequently asked questions",
  faq: [
    {
      q: "A project has been announced near me. Where do I start?",
      a: "With the calendar, because it decides everything: the same question asked during consultation can still change the project; asked after the authorisation, it changes nothing. Appeal windows are <b>two months</b> — from the first day of posting for a building permit, from the last formality completed for an environmental authorisation. And once the site is running, what remains is a claim to the prefect about its <i>prescriptions</i> (noise, discharges, water). The whole path, step by step, is in <a href='/fr/comprendre#droits'>Rights and calendar</a> (in French), with the legal texts.",
    },
    {
      q: "The Nutri-Score of data centers. How is a data center graded?",
      a: "Each project receives two <i class='gl gl-a'>A</i>–<i class='gl gl-e'>E</i> grades — one for the site, one for the operator — from 26 indicators across 5 pillars (energy, water, land, local impact, transparency). A numeric score is computed, then translated into a letter, exactly like the food Nutri-Score everyone knows; next to it, a confidence level says whether the grade rests on solid or fragile data.",
    },
    {
      q: "What separates a data center graded A from one graded B?",
      a: "The number of pillars under tension, and how severe they are. <b>A</b>: no marked weakness on the pillars published on the fiche. <b>B</b>: solid, with one shadow. <b>C</b>: two clear tensions. <b>D</b> and <b>E</b>: several pillars in the red, or one major tension on its own. As with the food Nutri-Score, the letter sums up several criteria at once — and a single very poor criterion is enough to pull it down. One thing worth knowing: the cap only lifts on third-party verified proof, and <b>no site in Europe reaches A today</b>.",
    },
    {
      q: "Why don't you publish the numeric thresholds behind the grade?",
      a: "So the grade cannot be gamed. We publish the grid, the weights of the 5 pillars, the sources behind every indicator and, on each fiche, the factor that weighs most on the grade — so what counts, and in which direction. We do not publish where the thresholds sit: with that, a developer could aim at the letter instead of aiming at the ground. The method is verifiable; the recipe is not optimisable.",
    },
    {
      q: "What do the two grades, “site” and “operator”, mean?",
      a: "The site grade assesses what the project endures — territory, water, grid, land — whoever carries it. The operator grade assesses what the operator chooses — efficiency, consultation, transparency, commitments. We separate the terrain from the decisions.",
    },
    {
      q: "Can I get the project near me graded?",
      a: "Yes. Suggest it through the <a href='#contact'>Contact section</a>: we prioritize the best-documented and most-debated cases. One independence note: we never grade on behalf of a party, for or against — the grade follows the method, not the requester.",
    },
    {
      q: "Where does the data come from?",
      a: "Public sources: power grid, water, land registries, census data, official records, local press. Every displayed value links to its source, and the method is open: anyone can redo the computation.",
    },
    {
      q: "Why don't US projects have a grade (yet)?",
      a: "Because depth follows the data. A grade requires thresholds calibrated country by country (grid, water, land, registries, procedures) and a working correction-and-response channel — which is the case in Europe today. In the United States we first publish the 'on watch' layer: citizen oppositions ✋🏼 and moratoria ⏸️ — sourced facts, never a grade. The first US grades will come when the data and the calibration are ready, not before: we do not grade the unknown.",
    },
    {
      q: "Can an operator pay to improve its grade?",
      a: "No, never. Scored entities do not pay for their grade. A project's grade and its justification are public and free, forever.",
    },
    {
      q: "Why does no data center have an <i class='gl gl-a'>A</i> (yet)?",
      a: "Because an <i class='gl gl-a'>A</i> is proven, never promised: it is reserved for values verified in operation. A fully declarative file, however excellent, caps at <i class='gl gl-b'>B</i> — “announced ≠ measured”. An operator earns its <i class='gl gl-a'>A</i> by bringing third-party proof (its EED filing to the regulator, an ISO/IEC 30134 audit by an accredited body — never a marketing page) through our public correction channel: the data flips from “announced” to “measured”, the cap lifts, and the re-score is traced in the public audit log. An <i class='gl gl-a'>A</i> cannot be bought or declared: it is demonstrated. And proof lifts the project & process grade — never the site grade: the territory is endured, it cannot be proven away.",
    },
    {
      q: "Why we publish without asking permission",
      a: "A critic reviews a film without the studio's approval. A journalist publishes an investigation without the consent of those it disturbs. ScoreMyDataCenter belongs to that tradition: freedom of criticism and contribution to the public-interest debate. The grade is an exercise of the freedom of criticism; its strength rests on the transparency of the method, the quality of the sources and the restraint of the words. We do not ask permission to publish an independent assessment. In return, we hold ourselves to a public method, sourced facts, measured words, and a permanent right to correction and response.",
    },
    {
      q: "What if a data point is wrong, or the operator disagrees?",
      a: "Two distinct tools: factual correction — any data point is corrected on evidence, the change is dated, and when the calculation is affected the grade is recomputed under the same method version — and the operator's response, published in a dedicated space, clearly attributed and dated. Publishing a response never changes the grade automatically: it only moves when new or corrected facts change the result produced by the method.",
    },
    {
      q: "Can an operator request removal of its fiche?",
      a: "A wrong data point is corrected on evidence, and the operator can send a response published alongside the grade. But a sourced, methodical grade is not removed on request: pulling it because it displeases would be selling it in reverse. The grade stays; the counter-argument is added.",
    },
    {
      q: "Is the grade a final verdict?",
      a: "No: it is an acceptability-risk grade, coupled with a confidence level, and it can evolve with the project. The numeric score is published to make the computation transparent, but the <i class='gl gl-a'>A</i>–<i class='gl gl-e'>E</i> letter is what counts — the grade applies an expert, sourced, versioned grid; it does not claim the precision of an oracle.",
    },
    {
      q: "Does the grade evolve with technical progress? Will a well-graded data center still be well-graded in ten years?",
      a: "Yes, by design. A grade changes for two reasons: the project evolves (new data), or the yardstick evolves with the state of the art. Our thresholds anchor on standards that tighten over time (ISO, European regulation): an <i class='gl gl-a'>A</i> always means “the best achievable today”, not “the best of 2026”. Without that, everyone would end up <i class='gl gl-a'>A</i> as technology progresses — which is exactly why the EU energy label was reset in 2021, when nearly every appliance had become A+++. Each grade is therefore dated and tied to a methodology version: a data center excellent in 2026 may be “average” by 2036 standards — and that is precisely the score's job: reward progress, and flag what ages.",
    },
    {
      q: "Who are the players in the data center industry?",
      a: "Several families, which often meet on the same project. <b>Developers</b>: they find the land, obtain permits and grid connection, then sell or lease. <b>Colocation operators</b>: they run data centers and rent out space, power and connectivity to their customers. <b>Hyperscalers</b>: the cloud giants, which build and run their own campuses. <b>AI neoclouds</b>: specialized providers renting out computing power for artificial intelligence. <b>Energy companies and grid operators</b>: they produce and supply electricity and connect the site (in France, RTE for transmission, Enedis for distribution). <b>Builders and equipment makers</b>: they construct the building and supply cooling, backup power, servers. <b>Local authorities and the State</b>: in France, the municipality or inter-municipal body sets planning rules and usually grants the building permit; the préfet reviews the environmental authorization. <b>Investors and property companies</b>: funds and real-estate firms that finance or own the buildings.",
    },
    {
      q: "How to tell the players apart: developer or operator?",
      a: "The developer prepares the land and the building (plot, permits, grid connection), then sells or leases it; the operator runs the servers inside and sells hosting to customers. The analogy: the property developer and the hotelier — one builds the hotel, the other brings it to life. Can one company do both? Yes, and it is even the dominant model among the big players: Data4, Equinix, Digital Realty develop and operate their campuses. Pure developers tend to be newcomers from real estate: H&DC, Prologis, Goodman, Segro, Altarea — they come from logistics or property development. A site announced by a developer is therefore, by nature, a real-estate project, not a data center in service.",
    },
    {
      q: "Who talks to the town, and who never does?",
      a: "Five roles — and above all: who talks to the territory, and who never does. <b>The developer</b> assembles the deal — land, permits, grid connection — builds, then sells or leases. It's the developer who meets the mayor, early on; often they vanish once the permit is granted. <b>The owner</b> holds the walls (a property fund, a REIT): they talk to no one locally, but they collect the rent. <b>The operator</b> sells the service — leasing rooms, power and connectivity to clients: it's the name on the scorecard, and the territory's contact once the site is live. <b>The facility manager</b> runs the building day to day (cooling, power, maintenance), often an invisible subcontractor — but it's who handles the noise and the backup generators, i.e. what disturbs neighbours. <b>The end customer</b> leases the rooms or the compute (a bank, a hyperscaler, a neocloud reselling further on): it never talks to the town and its name is rarely public. At the big players, the first three roles are often the same company — Data4, Equinix, Digital Realty develop and operate their campuses; among real-estate newcomers they're separate. <b>What it changes for an elected official:</b> the one promising jobs and recovered heat is not the one who will deliver them, and the one truly consuming is almost never in the room.",
    },
    {
      q: "What are the stages of a data center project, from announcement to operation?",
      a: "In France, broadly: 1) announcement and, sometimes, a prior public consultation; 2) filing — building permit and, most often, an environmental authorization under the classified-installations regime (ICPE); 3) review: opinion of the environmental authority, then public inquiry; 4) decision: permit granted by the mayor (or by the préfet in some cases), environmental authorization by prefectoral order; 5) appeal periods; 6) construction, often in phases; 7) commissioning, then inspections during operation. Stages can overlap, and a project can stop at any of them. The public's rights at each stage: <a href='/understand#rights'>Rights and timeline</a>.",
    },
    {
      q: "What is a “moratorium” on data centers? Does it stop a project?",
      a: "The word covers very different things. A political motion or council resolution calling for a pause has, on its own, no legal effect on an authorization already granted. There is, however, a legal tool: the <b>sursis à statuer</b> (deferral of decision). When a local urban plan is being drawn up or revised, the municipality can postpone its answer to a permit application, for two years at most (French planning code, art. L.424-1). A general nationwide pause would require a law or regulation. On this site, a moratorium is reported as a sourced fact, never as a score.",
    },
    {
      q: "Who can stop a construction site? What can the administrative court decide?",
      a: "Several routes, with different effects. <b>The administrative court</b>: an appeal against a permit or authorization does not, by itself, stop the works. To suspend them quickly, a <b>référé-suspension</b> (interim suspension) is needed, granted only when there is urgency and serious doubt about legality (administrative justice code, art. L.521-1). On the merits, the judge can annul the authorization, or give the project owner time to correct a defect that can be fixed (planning code, art. L.600-5-1). These rulings can in principle be appealed, then taken to the Conseil d'État. <b>The mayor or the préfet</b>: they can order works carried out without authorization, or not in compliance, to be halted (planning code, art. L.480-2); for a classified installation, the préfet can serve formal notice on the operator, then suspend the activity (environment code, art. L.171-8). <b>The project owner</b>, finally, can suspend or abandon for financial, technical or commercial reasons.",
    },
    {
      q: "Can a suspended project, or one under moratorium, restart?",
      a: "Yes, in several cases: the deferral of decision ends (at its term, the municipality must decide within two months if the applicant confirms the application); a suspension is lifted by the judge; the authorization is regularized; an annulment is overturned on appeal; or the owner files a new application. Conversely, a building permit expires: as a general rule if works do not start within three years, or are interrupted for more than a year; this period can be extended twice by one year (planning code, art. R.424-17 and R.424-21). A stalled project is therefore not necessarily an abandoned one — which is why we never remove it without a source.",
    },
    {
      q: "What does “announced” mean on a page?",
      a: "That the data center is not in service yet: a project made public, under permitting or under construction. Until it is in service, it gets no final score but a provisional range, computed on what the territory bears.",
    },
    {
      q: "Who are you, and how do you stay independent?",
      a: "An independent observatory founded by Franck Bardol. The method is open, scored entities do not pay, and how we operate is detailed in the <a href='#open'>Open model section</a>.",
    },
  ],
  contactTitle: "Suggest a project, or reach the observatory.",
  contactCta: "Contact",
};


// ── NÉERLANDAIS — EN PRÉPARATION, PAS ENCORE SERVI (voir `content/langues.ts`).
// ⚠️ Les valeurs ci-dessous sont encore LE TEXTE FRANÇAIS, copié tel quel. Elles sont là
// pour qu'un traducteur natif ait la source sous les yeux, à sa place dans la structure.
// Elles NE DOIVENT PAS partir en ligne : `nl` n'est pas dans `LANGUES_VIVANTES`, et
// `test_une_langue_ne_devient_vivante_que_traduite` refuse de l'y faire entrer tant que
// ses valeurs sont celles du français.
const NL: typeof FR = {
  blocs: {
    actu: { heading: "Laatste sectornieuws", seeAll: "Al het nieuws →", href: "/nl/nieuws/", projet: "Project", locale: "nl-NL" },
    projets: { heading: "Nieuw gesignaleerde projecten", seeAll: "Bekijk de monitoring →", href: "/nl/kaart/", veille: "gevolgd", carte: "/nl/kaart/" },
    pays: { label: "landen gevolgd", aria: "{n} landen gevolgd: {pays}" },
    mur: { fiche: "/nl/dc" },
  },

  chemins: {
    fiche: "/nl/dc",
    classement: "/nl/ranglijst",
    carte: "/nl/kaart/",
    indices: "/nl/indices/",
    indicesPays: "/nl/indices?pays=",
    methodologie: "/nl/methodologie/",
    bibliotheque: "/nl/bibliotheek/",
  },
  formes: { locale: "nl-NL", decimale: "," },
  indices: {
    h2: "De ranglijst van de landen",
    lead: "Deze index aggregeert de cijfers van SITES (de territoriale context: net, water, bodem, risico's). Hij beoordeelt geen exploitanten en niet het gedrag van projecten.",
    reserve: "A alleen op bewijs · ",
    plus: "Bekijk de kaart en de {n} landen",
  },
  powerUnknown: "vermogen niet meegedeeld",

  title: "ScoreMyDataCenter — het publieke acceptatiecijfer van datacenters",
  description:
    "De maatschappelijke acceptatie van datacenters: beoordeeld, gedocumenteerd, openbaar. Een cijfer A–E per site, met bronnen, vertrouwensniveau en een open methode.",
  altHref: "/",
  altLabel: "EN",
  tagline: "Onafhankelijk observatorium",
  nav: FR_NAV,
  heroEyebrow: "Onafhankelijk & publiek observatorium",
  heroTitle: "Een datacenter komt niet langer zomaar ergens te staan.<br><span class='hero-red'>Wij meten het risico.</span>",
  heroLede:
    "Datacenters veranderen onze leefomgeving. Water, energie, grond, lokale impact, transparantie: ScoreMyDataCenter beoordeelt publiekelijk de acceptatiescore van elk project, volgens een open methode en gedocumenteerde feiten.",
  heroStandards:
    "We zijn onafhankelijk. We passen de standaarden van de sector toe — <strong>PUE</strong> (ISO/IEC&nbsp;30134), energie, koolstof — en meten vervolgens wat zij negeren: <strong>het water, de bodem, het gebied</strong>. Het resultaat is een Nutri-Score voor {n} echte sites.",
  heroChecks: [
    "Het cijfer is <strong>gratis</strong>",
    "De methode is <strong>openbaar</strong> (v0.1.0 bevroren)",
    "De bronnen zijn <strong>verifieerbaar</strong>",
  ],
  corpus: {
    aria: "Het corpus in één oogopslag",
    label: "Het corpus in één oogopslag",
    noted: "beoordeelde projecten",
    countries: "landen gedekt",
    stress: "sites in een zone met hoge waterstress of in watercrisis",
    watch: "projecten gevolgd, nog niet beoordeeld (verzet, moratoria)",
    scaleNote: "<strong>Eén cijfer A–E voor de site</strong> — wat de plek oplegt: water, net, grond, omwonenden. En een <strong>tweede cijfer, project &amp; proces</strong>, voor wat de initiatiefnemer aankondigt en documenteert: het is alleen te berekenen wanneer het projectdossier openbaar is, en dat blijft zeldzaam. Altijd getoond mét hun documentair vertrouwen.",
  },
  manifesto: {
    aria: "Ons manifest",
    line1: "Een criticus beoordeelt een film zonder toestemming van de studio. Een journalist publiceert zijn onderzoek zonder die van wie het stoort. ScoreMyDataCenter staat in die traditie: de vrijheid van kritiek en de bijdrage aan het publieke debat.",
    contractLead: "Ons contract in ruil:",
    contract: "een openbare methode, gedocumenteerde feiten, afgewogen woorden, en een permanent recht op correctie en weerwoord.",
    link: "Lees waarom",
  },
  mattersTitle: "Waarom het telt",
  mattersSub: "Een datacenter is niet zomaar een IT-gebouw: het is een project dat vitale hulpbronnen mobiliseert en een gebied voor lange tijd vastlegt.",
  matters: [
    { icon: "water", title: "Watervoorraad", body: "<strong>{stress} van de {mesures} sites</strong> staan in een zone met hoge waterstress of in watercrisis. Water weegt zwaar in de cijfers van het corpus.", href: "/nl/kaart/", link: "Bekijk de kaart" },
    { icon: "energy", title: "Elektriciteitsnet", body: "Verzadigde netten remmen aansluitingen en drukken de scores. Locatiekeuzes met zware gevolgen.", href: "/nl/kaart/", link: "Bekijk de kaart" },
    { icon: "land", title: "Gebied & biodiversiteit", body: "Verharding, bodem, biodiversiteit: lokale effecten die even zwaar tellen als de megawatts.", href: "/nl/datacenters-begrijpen/", link: "Begrijp wat er speelt" },
    { icon: "transparency", title: "Transparantie", body: "<strong>{noPower} van de {total} projecten</strong> maken hun vermogen niet bekend. Wij beoordelen op publieke documenten — ondoorzichtigheid loont nooit.", href: "/nl/methodologie/", link: "Begrijp de methode" },
  ],
  principlesTitle: "Onze methode, in 4 principes",
  exploreTitle: "Verken de scores",
  exploreSub: "Zoek. Vergelijk. Begrijp.",
  exploreMapLabel: "Kaart van de projecten",
  exploreRankLabel: "Ranglijst — positie in de verdeling",
  exploreRankMore: "Bekijk de volledige ranglijst",
  exploreLatestLabel: "De krachtigste gevolgde sites",
  exploreLatestMore: "Bekijk alle sites",
  searchPlaceholder: "Zoek een site, een exploitant, een land…",
  library: {
    title: "Intelligence Library — de analyse bovenop de scores",
    coverTitle: "State of Data Center Acceptability in Europe",
    lede: "De site zegt hoeveel. Onze analyses zeggen waar het heen gaat, en wat het betekent.",
    items: ["Trends per land en voor Europa", "Risico's per thema — water, energie, grond, transparantie", "Benchmarks van exploitanten"],
    cta: "Ontdek de analyses",
  },
  whoTitle: "Voor wie? Om te handelen.",
  whoSub: "Dezelfde toegang, verschillende toepassingen — elk profiel heeft zijn eigen ingang.",
  who: [
    { name: "Burgers", line: "Het project bij u in de buurt, in klare taal — de kaart.", href: "/nl/kaart/" },
    { name: "Journalisten", line: "Gedocumenteerde, citeerbare feiten, met hun archieven.", href: "/nl/ranglijst" },
    { name: "Bestuurders", line: "Vergelijk uw gemeente, bereid het debat voor.", href: "/nl/ranglijst" },
    { name: "Ngo's", line: "Verzet en moratoria — de monitoringlaag.", href: "/nl/kaart?veille=tout" },
    { name: "Onderzoekers", line: "De methode, de data — alles is na te rekenen.", href: "/nl/methodologie/" },
    { name: "Exploitanten", line: "Corrigeer, reageer — en verbeter het echte project.", href: "/nl/contact/" },
  ],
  heroScaleLabel: "De acceptatieschaal",
  ctaScores: "Bekijk de cijfers",
  mapOpen: "Open de kaart",
  mapReserved: "· A alleen op bewijs",
  viewFiche: "Bekijk de fiche →",
  ctaMethod: "Lees de methode",
  panelAria: "Voorbeeld van een scorefiche",
  siteScore: "Site",
  operatorScore: "Exploitant",
  insufficient: "onvoldoende gegevens",
  confidence: { high: "vertrouwen: hoog", medium: "vertrouwen: gemiddeld", low: "vertrouwen: laag" },
  fixtureNote:
    "Fictieve testfixture, getoond voor het formaat — de eerste echte fiches zijn in voorbereiding.",
  whyNowAria: "Waarom nu",
  whyNow: {
    // Règle signée Franck (2026-10-30) : même trio partout, périmètre = le pays de la
    // langue, Europe en repli. Les trois ids existent dans le périmètre NL (stats.json).
    perimetre: "NL" as string,
    repli: "europe" as string | null,
    stats: [
    { genre: "vue", id: "grid_saturated", figure: "{big} op een vol onderstation",
      attribution: "Kerncijfers van het datacenterpark · {src} · n = {n}", url: "/nl/kerncijfers#vol-station" },
    { genre: "vue", id: "pue_published", figure: "{big} publiceren hun PUE",
      attribution: "Kerncijfers van het datacenterpark · opgaven van exploitanten · n = {n}", url: "/nl/kerncijfers#pue-gepubliceerd" },
    { genre: "vue", id: "water_stress_high", figure: "{big} in een zone met hoge waterstress",
      attribution: "Kerncijfers van het datacenterpark · {src} · n = {n}", url: "/nl/kerncijfers#waterstress" },
    ],
  },
  whyNowPunch: "Het heetste onderwerp van AI heeft geen enkele onafhankelijke scheidsrechter. <b>Die scheidsrechter zijn wij.</b>",
  missionLine:
    "Onze missie: de maatschappelijke acceptatie van elk datacenterproject meten, documenteren en openbaar maken. Het debat verankeren in de feiten.",
  whyTitle: "Waarom dit observatorium",
  whyMotto: "We vragen geen toestemming om onze cijfers te publiceren. We leggen onszelf de methode op.",
  whyLede: "Een datacenter van 900 MW wordt aangekondigd bij u in de buurt. Waar leest u, helder, wat het waard is — en wat de lokale impact is?",
  whyBody:
    "De bestaande kaarten zetten technische kenmerken op een rij; de observatoria van het verzet tellen conflicten. Niemand legt, project per project, de werkelijkheid van elk dossier op tafel: een cijfer, bronnen, een methode die iedereen kan controleren en overdoen. Dát gat vult ScoreMyDataCenter: <span class='hl-red'>het eerste onafhankelijke en publieke acceptatiecijfer, waarop iedereen zich kan beroepen</span> — een feitelijke, gedocumenteerde en methodische beoordeling, gepubliceerd als bijdrage aan het publieke debat. En een schaal die bindt: <b>de <i class='gl gl-a'>A</i> bewijs je in exploitatie, je belooft hem niet</b> — beloften, hoe uitstekend ook, komen niet boven een <i class='gl gl-b'>B</i> uit; alleen geverifieerd bewijs maakt de <i class='gl gl-a'>A</i>. Onze missie: <b>alle datacenters scoren</b> — methodisch, openbaar, dossier voor dossier.",
  ...FR_ABOUT,
  principlesAria: "Principes",
  principles: [
    { title: "Openbare methode", body: "Open, geversioneerde, citeerbare meetlat. Iedereen kan elk cijfer overdoen." },
    { title: "Traceerbare gegevens", body: "Elke waarde verwijst naar haar bron. Het aangekondigde wordt nooit vermengd met het gemetene." },
    { title: "Correctie en weerwoord van de exploitant", body: "Lijkt een gegeven onjuist? Het kan met zijn bron worden gemeld. Na verificatie wordt de fiche gecorrigeerd en de wijziging gedateerd. De exploitant kan ook een weerwoord insturen, gepubliceerd in een eigen ruimte." },
    { title: "Onafhankelijkheid", body: "Beoordeelde partijen betalen nooit voor hun cijfer. Geen invloed, vóór noch tegen: het cijfer volgt de methode." },
  ],
  scoresTitle: "Laatst beoordeelde projecten",
  scoresLede:
    "Eén citeerbare pagina per project: twee cijfers, vijf subscores per pijler, documentair vertrouwen, bronnen en volledige historiek.",
  demo: {
    kicker: "Het cijfer, terwijl het ontstaat",
    caption: "Echt geval: {name} — de vijf pijlers, het cijfer van de site, dan de letter. Openbare methode, gedocumenteerde gegevens.",
    sr: "Animatie: de fiche van {name} wordt beoordeeld — de vijf pijler-subscores verschijnen, het cijfer van de site vult zich, dan wordt de letter gestempeld.",
    replay: "Opnieuw afspelen",
    why: "Waarom deze site? Zijn score ({score}/100) ligt het dichtst bij de mediaan van de {n} sites van het corpus: de gewoonste site van Europa, geen etalage en geen schoolvoorbeeld. De selectieregel is mechanisch en gepubliceerd.",
  },
  status: { announced: "Aangekondigd", permitting: "In behandeling", under_construction: "In aanbouw", operational: "In bedrijf", unknown: "Status niet vastgesteld" },
  fixtureTag: "Fictieve testfixture",
  pillarShort: {
    energy: "Energie",
    water: "Water",
    land_biodiversity: "Bodem",
    local_impact: "Lokaal",
    transparency_governance: "Transp.",
  },
  repoUrl: "https://github.com/bardolfranck/scoremydatacenter",
  methodTitle: "Eén methode, twee cijfers, altijd met het vertrouwen erbij.",
  methodLede:
    "26 indicatoren in 5 pijlers, verdeeld naar wat het project <span class='term'>ondergaat</span> en wat de exploitant <span class='term'>kiest</span>. De meetlat, haar gewichten en drempels zijn <a href='https://github.com/bardolfranck/scoremydatacenter/tree/main/data/methodology'>openbaar en downloadbaar</a>.",
  methodPedago: "Begrijp het cijfer, stap voor stap",
  siteScoreExplain: "De context die het project <span class='term'>ondergaat</span>: koolstofintensiteit van het elektriciteitsnet, waterstress, bodem, lokaal weefsel en economie van de gemeente.",
  operatorScoreExplain: "De hefbomen die de exploitant <span class='term'>kiest</span>: energie-efficiëntie, koeling, banen, inspraak, transparantie.",
  confidenceTitle: "Documentair vertrouwen",
  confidenceExplain:
    "Een cijfer verschijnt er nooit zonder. Onder 40% dekking schrijven we ‘onvoldoende gegevens’. Het onbekende beoordelen we niet.",
  weightsAria: "Gewichten van de pijlers",
  weightsCaption: "Gewicht van de pijler in het totaalcijfer",
  weightsNote: "Openbare, geversioneerde en gedateerde methodologie — zo is controleerbaar wat er het eerst was.",
  openTitle: "Wij spelen open kaart.",
  openLede: "De laag die het oordeel maakt, is open: methode, data en rekenmotor, door iedereen te verifiëren.",
  openCta: "Bekijk de code op GitHub",
  openCols: [
    {
      title: "Open methode, data en rekenmotor",
      body: "Motor <span class='lic' tabindex='0'>AGPL<span class='info-tip'>De code van de rekenmotor is vrij: wie hem verbetert, moet de verbeteringen opnieuw delen.</span></span>, gepubliceerde data <span class='lic' tabindex='0'>ODbL<span class='info-tip'>Open databank: vrij herbruikbaar, op voorwaarde van bronvermelding en delen onder gelijke voorwaarden.</span></span>, methodologie <span class='lic' tabindex='0'>CC BY-SA<span class='info-tip'>Vrije inhoud: herbruikbaar met naamsvermelding en delen onder dezelfde voorwaarden.</span></span>. De code is <a href='https://github.com/bardolfranck/scoremydatacenter'>publiek op GitHub</a>: iedereen kan elk cijfer nauwgezet overdoen.",
    },
    {
      title: "We helpen het project, nooit het cijfer",
      body: "Beoordeelde partijen betalen nooit voor hun publieke cijfer. Een exploitant kan zijn project laten analyseren; maar het cijfer beweegt alleen als het echte project verandert — nooit omdat er betaald is. ‘Hij betaalt, het cijfer stijgt’ is structureel uitgesloten.",
    },
    {
      title: "Publiek auditlogboek",
      body: "Elke beoordeling, herziening en correctie is gedateerd, geversioneerd en gemotiveerd. Een cijfer beweegt nooit in stilte.",
    },
    {
      title: "Begeleide bijdragen",
      body: "Correcties van gegevens zijn gratis en worden nagelezen. Om manipulatie van een cijfer te verhinderen zijn de principes van onze detectieregels openbaar; hun exacte drempelwaarden blijven vertrouwelijk — ze tonen zou de handleiding geven om door de mazen van het net te glippen.",
    },
  ],
  redline: "Onze belofte: het cijfer van een project en zijn motivering zijn <b>openbaar en gratis, voor altijd</b>.",
  faqTitle: "Veelgestelde vragen",
  faq: [
    {
      q: "Er is een project aangekondigd bij mij in de buurt. Waar begin ik?",
      a: "Bij het tijdpad, want dat beslist alles: dezelfde vraag gesteld tijdens de inspraak kan het project veranderen; gesteld na de vergunning verandert ze niets meer. In Frankrijk zijn de beroepstermijnen <b>twee maanden</b> — vanaf de eerste dag van aanplakking voor een bouwvergunning, vanaf de laatste vervulde formaliteit voor een milieuvergunning. En als de site al draait, rest nog de klacht bij de prefect over de <i>voorschriften</i> (geluid, lozingen, water). Het hele parcours, stap voor stap, staat in <a href='/nl/datacenters-begrijpen#rechten'>Rechten en tijdpad</a>, met de teksten.",
    },
    {
      q: "De nutri-score van datacenters. Hoe wordt een datacenter beoordeeld?",
      a: "Elk project krijgt twee cijfers <i class='gl gl-a'>A</i>–<i class='gl gl-e'>E</i> — één voor de site, één voor de exploitant — op basis van 26 indicatoren in 5 pijlers (energie, water, bodem, lokale impact, transparantie). Een getalscore wordt berekend en vertaald naar een letter, precies zoals bij de Nutri-Score op voedsel die iedereen kent; daarnaast zegt een vertrouwensniveau of het cijfer op stevige of op fragiele gegevens steunt.",
    },
    {
      q: "Wat scheidt een datacenter met een A van een datacenter met een B?",
      a: "Het aantal pijlers onder spanning, en hun ernst. <b>A</b>: geen uitgesproken zwakte op de gepubliceerde pijlers van de fiche. <b>B</b>: stevig, met één schaduwzijde. <b>C</b>: twee duidelijke spanningen. <b>D</b> en <b>E</b>: meerdere pijlers in het rood, of één grote spanning op zichzelf. Zoals bij de Nutri-Score op voedsel vat de letter meerdere criteria in één keer samen — en één heel slecht criterium volstaat om haar omlaag te trekken. Eén kanttekening die telt: het plafond gaat alleen omhoog op bewijs dat door een derde is geverifieerd, en <b>geen enkele site in Europa haalt vandaag een A</b>.",
    },
    {
      q: "Waarom publiceren jullie de exacte drempelwaarden niet?",
      a: "Opdat het cijfer niet te manipuleren valt. We publiceren de meetlat, de gewichten van de 5 pijlers, de bronnen van elke indicator en, op elke fiche, de factor die het zwaarst weegt — dus wat telt en in welke richting. We publiceren de exacte positie van de drempels niet: daarmee zou een initiatiefnemer op de letter kunnen mikken in plaats van op het terrein. De methode is verifieerbaar, het recept is niet te optimaliseren.",
    },
    {
      q: "Wat betekenen de twee cijfers, ‘site’ en ‘exploitant’?",
      a: "Het sitecijfer beoordeelt wat het project ondergaat — gebied, water, net, grond — wie er ook achter zit. Het exploitantcijfer beoordeelt wat hij kiest — efficiëntie, inspraak, transparantie, toezeggingen. We scheiden het terrein van de beslissingen.",
    },
    {
      q: "Kan ik het project bij mij in de buurt laten beoordelen?",
      a: "Ja. Stel het voor via de <a href='#contact'>contactpagina</a>: we geven voorrang aan de best gedocumenteerde en meest besproken dossiers. Eén kanttekening over onafhankelijkheid: we beoordelen nooit in opdracht van een partij, vóór noch tegen — het cijfer volgt de methode, niet de aanvrager.",
    },
    {
      q: "Waar komen de gegevens vandaan?",
      a: "Uit publieke bronnen: elektriciteitsnet, water, bodem, INSEE, registers, lokale pers. Elke getoonde waarde verwijst naar haar bron, en de methode is open: iedereen kan de berekening overdoen.",
    },
    {
      q: "Waarom hebben de Amerikaanse projecten (nog) geen cijfer?",
      a: "Omdat we pas diep gaan waar de data het toelaten. Een cijfer vraagt per land gekalibreerde drempels (elektriciteitsnet, water, bodem, registers, procedures) en een werkend kanaal voor correctie en weerwoord — dat is vandaag het geval in Europa. In de Verenigde Staten publiceren we eerst de monitoringlaag: burgerverzet ✋🏼 en moratoria ⏸️ — gedocumenteerde feiten, nooit een cijfer. De eerste Amerikaanse cijfers komen wanneer de data en de kalibratie op niveau zijn, niet eerder: het onbekende beoordelen we niet.",
    },
    {
      q: "Kan een exploitant betalen om zijn cijfer te verbeteren?",
      a: "Nee, nooit. Beoordeelde partijen betalen niet voor hun cijfer. Het cijfer van een project en zijn motivering zijn openbaar en gratis, voor altijd.",
    },
    {
      q: "Waarom heeft nog geen enkel datacenter het cijfer <i class='gl gl-a'>A</i>?",
      a: "Omdat een <i class='gl gl-a'>A</i> bewezen wordt, niet beloofd: hij is voorbehouden aan waarden die in exploitatie zijn geverifieerd. Een volledig declaratief dossier, hoe uitstekend ook, komt niet boven een <i class='gl gl-b'>B</i> uit — ‘aangekondigd ≠ gemeten’. Een exploitant behaalt zijn <i class='gl gl-a'>A</i> door bewijs van een derde aan te leveren (EED-rapportage aan de toezichthouder, ISO/IEC 30134-audit door een geaccrediteerde instelling — nooit een marketingpagina) via het publieke correctiekanaal: de waarde gaat dan van ‘aangekondigd’ naar ‘gemeten’, het plafond vervalt, en de herberekening wordt vastgelegd in het auditlogboek. De <i class='gl gl-a'>A</i> is niet te koop en niet op eigen verklaring te krijgen: hij wordt aangetoond. En bewijs verhoogt het cijfer project &amp; proces — nooit dat van de site: het gebied is een gegeven: daar valt niets te bewijzen.",
    },
    {
      q: "Waarom we publiceren zonder toestemming te vragen",
      a: "Een criticus beoordeelt een film zonder akkoord van de studio. Een journalist publiceert zijn onderzoek zonder dat van wie het stoort. ScoreMyDataCenter staat in die traditie: de vrijheid van kritiek en de bijdrage aan het publieke debat. Het cijfer valt onder de vrijheid van kritiek; zijn soliditeit hangt af van de transparantie van de methode, de kwaliteit van de bronnen en de afgewogenheid van de woorden. We vragen geen toestemming om een onafhankelijke beoordeling te publiceren. In ruil leggen we onszelf een openbare methode op, gedocumenteerde feiten, afgewogen woorden en een permanent recht op correctie en weerwoord.",
    },
    {
      q: "En als een gegeven onjuist is, of de exploitant het er niet mee eens is?",
      a: "Twee aparte instrumenten: de feitelijke correctie — elk gegeven wordt op bewijs gecorrigeerd, de wijziging wordt gedateerd, en als de berekening wordt geraakt, wordt het cijfer herberekend bij gelijke methodeversie — en het weerwoord van de exploitant, gepubliceerd in een eigen ruimte, met duidelijke naamsvermelding en datum. De publicatie van een weerwoord wijzigt het cijfer niet automatisch: dat beweegt alleen wanneer nieuwe of gecorrigeerde feiten de uitkomst van de methode veranderen.",
    },
    {
      q: "Kan een exploitant de verwijdering van zijn fiche vragen?",
      a: "Een onjuist gegeven wordt op bewijs gecorrigeerd, en de exploitant kan een weerwoord insturen dat naast het cijfer wordt gepubliceerd. Maar een gedocumenteerd en methodisch cijfer wordt niet op verzoek ingetrokken: intrekken omdat het niet bevalt, zou het langs de achterdeur verkopen zijn. Het cijfer blijft; de tegenspraak komt erbij.",
    },
    {
      q: "Is het cijfer een definitief oordeel?",
      a: "Nee: het is een cijfer voor acceptatierisico, met een vertrouwensniveau, en het kan meebewegen met het project. De getalscore wordt gepubliceerd om de berekening transparant te maken, maar de letter <i class='gl gl-a'>A</i>–<i class='gl gl-e'>E</i> is maatgevend — het cijfer past een meetlat van experts toe, gedocumenteerd en geversioneerd; het pretendeert geen orakelnauwkeurigheid.",
    },
    {
      q: "Beweegt het cijfer mee met de technische vooruitgang? Is een goed beoordeeld datacenter dat over tien jaar nog?",
      a: "Ja, en dat is gewild. Een cijfer verandert om twee redenen: het project evolueert (nieuwe gegevens), of de maatstaf evolueert met de stand van de techniek. Onze drempels zijn verankerd in normen die mettertijd strenger worden (ISO, Europese regelgeving): een <i class='gl gl-a'>A</i> betekent altijd ‘het beste dat vandaag haalbaar is’, niet ‘het beste van 2026’. Anders zou iedereen op den duur een <i class='gl gl-a'>A</i> halen naarmate de technologie vordert — precies daarom is het Europese energielabel in 2021 herschaald, toen bijna alle apparaten A+++ waren geworden. Elk cijfer is dus gedateerd en gekoppeld aan een methodeversie: een datacenter dat in 2026 uitstekend is, kan naar de normen van 2036 ‘middelmatig’ zijn — en dat is exact de rol van de score: vooruitgang belonen, en signaleren wat veroudert.",
    },
    {
      q: "Wie zijn de spelers in de datacentersector?",
      a: "Meerdere families, die elkaar op één project vaak kruisen. <b>Ontwikkelaars en gebiedsontwikkelaars</b>: zij vinden de grond, halen de vergunningen en de netaansluiting binnen, en verkopen of verhuren daarna. <b>Colocatie-exploitanten</b>: zij exploiteren datacenters en verhuren er ruimte, energie en connectiviteit aan hun klanten. <b>Hyperscalers</b>: de cloudreuzen, die hun eigen campussen bouwen en exploiteren. <b>AI-neoclouds</b>: gespecialiseerde aanbieders die rekenkracht voor kunstmatige intelligentie verhuren. <b>Energiebedrijven en netbeheerders</b>: zij produceren en leveren de elektriciteit en sluiten de site aan (in Frankrijk RTE voor het transport, Enedis voor de distributie). <b>Bouwers en toeleveranciers</b>: zij bouwen en leveren koeling, noodstroom, servers. <b>Overheden</b>: de gemeente of het samenwerkingsverband stelt de stedenbouwkundige regels vast en verleent doorgaans de bouwvergunning; in Frankrijk behandelt de prefect de milieuvergunning. <b>Investeerders en vastgoedfondsen</b>: fondsen en vastgoedmaatschappijen die de panden financieren of bezitten.",
    },
    {
      q: "Hoe onderscheid je de spelers: ontwikkelaar of exploitant?",
      a: "De ontwikkelaar maakt het terrein en het gebouw klaar (grond, vergunningen, aansluiting) en verkoopt of verhuurt het daarna; de exploitant laat er de servers draaien en verkoopt de hosting aan klanten. De analogie: de projectontwikkelaar en de hotelier — de een bouwt het hotel, de ander brengt het tot leven. Allebei tegelijk, bestaat dat? Ja, het is zelfs het dominante model bij de groten: Data4, Equinix en Digital Realty ontwikkelen én exploiteren hun campussen. De zuivere ontwikkelaars zijn eerder de nieuwkomers uit het vastgoed: H&DC, Prologis, Goodman, Segro, Altarea — ze komen uit de logistiek of de projectontwikkeling. Een site die door een ontwikkelaar wordt aangekondigd, is dus van nature een vastgoedproject, geen datacenter in bedrijf.",
    },
    {
      q: "Wie praat met de gemeente, en wie praat er nooit mee?",
      a: "Vijf rollen — en vooral: wie praat met het gebied, en wie nooit. <b>De ontwikkelaar</b> zet de operatie op — grond, vergunningen, aansluiting — bouwt, en verkoopt of verhuurt dan. Hij is het die in het begin bij de burgemeester langsgaat; vaak verdwijnt hij zodra de vergunning binnen is. <b>De eigenaar</b> bezit het pand (een vastgoedfonds): hij praat lokaal met niemand, maar hij is het die incasseert. <b>De exploitant</b> verkoopt — hij verhuurt zalen, energie en connectiviteit aan klanten: zijn naam staat op de fiche, en hij is het aanspreekpunt van het gebied zodra de site in bedrijf is. <b>De technisch beheerder</b> laat het gebouw dagelijks draaien (koeling, elektriciteit, onderhoud), vaak een onderaannemer die het publiek nooit ziet — maar hij beheert het geluid en de noodaggregaten, dus wat de omwonenden hindert. <b>De eindklant</b> huurt de zalen of het vermogen (een bank, een hyperscaler, een neocloud die verder doorverkoopt): hij praat nooit met de gemeente en zijn naam is zelden publiek. Bij de groten zijn de eerste drie rollen vaak hetzelfde bedrijf — Data4, Equinix, Digital Realty ontwikkelen en exploiteren hun campussen; bij de nieuwkomers uit het vastgoed zijn ze gescheiden. <b>Wat dit verandert voor een bestuurder:</b> wie de banen en de restwarmte belooft, is niet wie ze zal leveren, en wie werkelijk verbruikt, zit bijna nooit aan tafel.",
    },
    {
      q: "Wat zijn de stappen van een datacenterproject, van aankondiging tot ingebruikname?",
      a: "In Frankrijk, schematisch: 1) de aankondiging en soms een voorafgaande inspraak; 2) de indiening van de aanvragen — bouwvergunning en meestal een milieuvergunning onder het regime van de geklasseerde installaties (ICPE); 3) de behandeling: advies van de milieuautoriteit, dan openbare raadpleging; 4) de beslissing: vergunning verleend door de burgemeester (of in bepaalde gevallen de prefect), milieuvergunning bij prefectoraal besluit; 5) de beroepstermijnen; 6) de bouw, vaak in fasen; 7) de ingebruikname, en daarna de controles tijdens de exploitatie. Stappen kunnen elkaar overlappen, en een project kan bij elk ervan stoppen. De rechten van het publiek bij elke stap: <a href='/nl/datacenters-begrijpen#rechten'>Rechten en tijdpad</a>.",
    },
    {
      q: "Wat is een ‘moratorium’ op datacenters? Stopt dat een project?",
      a: "Het woord dekt heel verschillende ladingen. Een politieke motie of raadsbeslissing die om een pauze vraagt, heeft op zichzelf geen juridisch effect op een al verleende vergunning. Er bestaat in Frankrijk wél een juridisch instrument: het <b>sursis à statuer</b> (aanhouden van de beslissing). Wanneer een lokaal stedenbouwkundig plan wordt opgesteld of herzien, kan de gemeente haar antwoord op een vergunningsaanvraag uitstellen, voor ten hoogste twee jaar (Franse stedenbouwwet, art. L.424-1). Een algemene pauze op nationale schaal zou een wet of een besluit vergen. Op deze site wordt een moratorium gemeld als een gedocumenteerd feit, nooit als een cijfer.",
    },
    {
      q: "Wie kan een bouwplaats stilleggen? Wat kan de bestuursrechter beslissen?",
      a: "Meerdere wegen, met verschillende effecten. <b>De bestuursrechter</b>: een beroep tegen een vergunning legt de bouw niet uit zichzelf stil. Om die snel te schorsen is een <b>référé-suspension</b> (kort geding tot schorsing) nodig, alleen toegekend bij spoed en ernstige twijfel over de rechtmatigheid (Franse code van bestuursrechtspraak, art. L.521-1). In de bodemprocedure kan de rechter de vergunning vernietigen, of de initiatiefnemer tijd geven om een herstelbaar gebrek te corrigeren (stedenbouwwet, art. L.600-5-1). Tegen die uitspraken staat in beginsel hoger beroep open, daarna de Conseil d'État. <b>De burgemeester of de prefect</b>: zij kunnen bouwwerkzaamheden die zonder vergunning of in strijd ermee worden uitgevoerd, laten stilleggen (stedenbouwwet, art. L.480-2); voor een geklasseerde installatie kan de prefect de exploitant in gebreke stellen en daarna de activiteit schorsen (milieuwet, art. L.171-8). <b>De initiatiefnemer</b>, ten slotte, kan zelf opschorten of afzien, om financiële, technische of commerciële redenen.",
    },
    {
      q: "Kan een geschorst project, of een project onder moratorium, herstarten?",
      a: "Ja, in meerdere gevallen: het aanhouden van de beslissing loopt af (aan het einde moet de gemeente binnen twee maanden beslissen als de aanvrager zijn aanvraag bevestigt); een schorsing wordt door de rechter opgeheven; de vergunning wordt geregulariseerd; een vernietiging wordt in hoger beroep tenietgedaan; of de initiatiefnemer dient een nieuw dossier in. Omgekeerd verloopt een bouwvergunning: in de regel als de bouw niet binnen drie jaar begint, of langer dan een jaar stilligt; die termijn kan twee keer met een jaar worden verlengd (Franse stedenbouwwet, art. R.424-17 en R.424-21). Een stilgevallen project is dus niet noodzakelijk een opgegeven project — daarom halen we het nooit weg zonder bron.",
    },
    {
      q: "Wat betekent ‘aangekondigd’ op een fiche?",
      a: "Dat het datacenter nog niet in bedrijf is: project publiek gemaakt, in vergunningsprocedure of in aanbouw. Zolang het niet in bedrijf is, krijgt het geen definitief cijfer maar een voorlopige bandbreedte, berekend op wat het gebied ondergaat.",
    },
    {
      q: "Wie zijn jullie, en hoe blijven jullie onafhankelijk?",
      a: "Een onafhankelijk observatorium, opgericht door Franck Bardol. De methode is open, beoordeelde partijen betalen niet, en onze werking staat beschreven in de sectie <a href='#open'>Open model</a>.",
    },
  ],
  contactTitle: "Stel een project voor, of bereik het observatorium.",
  contactCta: "Contact",
};

/** La table servie au gabarit : `ACCUEIL[lang]`. */
export const ACCUEIL: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };

/**
 * Les trois chiffres de « pourquoi maintenant », remplis — `chiffresAccueil(lang)`.
 *
 * Ils sont calculés au build depuis `stats.json` : la table porte les PHRASES, ce helper
 * porte le remplissage. Les deux pages composaient la même chose, chacune chez elle, avec
 * son propre périmètre et son propre `fmtInt` — donc une langue de plus aurait recopié la
 * composition une troisième fois.
 *
 * Une entrée dont le chiffre manque DISPARAÎT (le `.filter(Boolean)` d'avant) : on n'affiche
 * pas une phrase à trou, et surtout pas un zéro de repli.
 */
export function chiffresAccueil(lang: Langue) {
  const t = ACCUEIL[lang] as typeof FR;
  const peri = (STATS as any).perimeters[t.whyNow.perimetre]
    ?? (t.whyNow.repli ? (STATS as any).perimeters[t.whyNow.repli] : null);
  if (!peri) return [];
  const sortie: Array<{ figure: string; attribution: string; url: string }> = [];
  for (const e of t.whyNow.stats as any[]) {
    if (e.genre === "pipeline") {
      const p = peri?.stats?.pipeline;
      if (!p) continue;
      sortie.push({
        figure: e.figure.replace("{mw}", fmtInt(p.mw_announced, lang as Lang)),
        attribution: e.attribution.replace("{projects}", String(p.projects)),
        url: e.url,
      });
      continue;
    }
    // 🔴 Un `genre` inconnu ARRÊTE le build au lieu de faire disparaître un chiffre en
    // silence. Sans ça, une faute de frappe dans la table retirerait une des trois cases de
    // l'accueil sans rien casser — l'absence qui ressemble à un choix.
    if (e.genre !== "vue") {
      throw new Error(`accueil: genre de chiffre inconnu « ${e.genre} » (id ${e.id ?? "?"})`);
    }
    const v = statView(peri, e.id, lang as Lang);
    if (!v) continue;
    const remplir = (s: string) => s
      .replace("{big}", String(v.big))
      .replace("{src}", String((v as any).src ?? ""))
      .replace("{n}", String(v.n));
    sortie.push({ figure: remplir(e.figure), attribution: remplir(e.attribution), url: e.url });
  }
  return sortie;
}
