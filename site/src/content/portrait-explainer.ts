// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La page « Portrait du site », qui EXPLIQUE le portrait (le portrait lui-même est dans portrait.ts) — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
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
  title: "Le portrait du site — ScoreMyDataCenter",
  metaDescription: "Chaque data center a deux pages chez nous : la fiche technique et le portrait du site. Mêmes faits, deux lecteurs — l'analyste et le riverain.",
  tagline: "Observatoire indépendant",
  h1: "Le portrait du site",
  lead: "Chaque site noté a <strong>deux pages</strong> chez nous. Les mêmes faits, les mêmes sources, pas une donnée de plus — mais deux lecteurs qui n'ont ni le même temps, ni la même question. Confondre les deux, c'est en perdre un.",

  twoTitle: "Deux pages, deux lecteurs",
  portraitFor: "Le portrait du site",
  portraitWho: "Pour qui habite à côté, siège au conseil municipal, ou couvre le sujet.",
  portraitBullets: [
    "Ce qui <strong>pèse le plus</strong> sur la note, en trois points",
    "Où en est la procédure, et <strong>jusqu'à quand</strong> on peut encore agir",
    "Ce qu'il reste à demander, <strong>et à qui</strong>",
    "Fait pour être imprimé et posé sur une table",
  ],
  sheetFor: "La fiche technique",
  sheetWho: "Pour qui lit des indicateurs : exploitant, analyste, assureur, bureau d'études.",
  sheetBullets: [
    "Les <strong>vingt-six indicateurs</strong>, un par un",
    "Chaque valeur avec <strong>sa source et sa date</strong>",
    "L'état de chaque mesure : mesurée, annoncée, absente du dossier",
    "Les sites comparables, notés sur la même grille",
  ],
  demoPortraitHref: "/fr/dc/fr-campus-ia-fouju/portrait/",
  demoPortraitLabel: "Voir un portrait : Campus IA Fouju →",
  demoSheetHref: "/fr/dc/fr-campus-ia-fouju/",
  demoSheetLabel: "La fiche du même site →",
  notSimplified: "Le portrait n'est pas une version simplifiée de la fiche. Il ne retire rien : il range autrement, et il va jusqu'à la question que la fiche ne pose pas — « et maintenant, qu'est-ce que je fais ? ».",

  addsTitle: "Ce que le portrait ajoute",
  adds: [
    {
      icon: "measure",
      title: "Les points qui décideront",
      body: "Trois, pas vingt-six. Choisis par le calcul, pas par nous : le facteur que le moteur désigne comme dominant d'abord, puis ce que le <strong>territoire impose</strong> avant ce que le <strong>porteur annonce</strong>. La distinction compte : l'un ne se négocie pas, l'autre si.",
    },
    {
      icon: "transparency",
      title: "Où en est la procédure, et jusqu'à quand",
      body: "Le délai de recours, la fenêtre d'observation, la voie de réclamation une fois le site en service — lus <strong>dans le texte de loi du pays ou de l'État concerné</strong>, jamais dans un commentaire. Quand nous ne l'avons pas lu, nous le disons et nous indiquons quoi demander à sa place.",
    },
    {
      icon: "local",
      title: "Ce qu'il reste à demander",
      body: "Chaque question sort d'un indicateur que le dossier ne renseigne pas, et elle se conjugue au temps de la procédure : « à demander avant le dépôt », « à verser à l'enquête », « à faire inscrire dans l'autorisation », « à réclamer au titre des prescriptions ». Une question sans son verbe est un vœu.",
    },
  ],

  refuseTitle: "Ce qu'il ne fait pas",
  refuse: [
    "<strong>Aucune affirmation sur la santé.</strong> Nous ne mesurons pas d'effet sanitaire et nous ne prétendons pas le faire. Nous publions ce qui figure au dossier, et ce qui n'y figure pas.",
    "<strong>Aucune phrase écrite à la main.</strong> Tout ce que vous lisez sur un portrait est dérivé des mêmes données que la fiche. Une phrase rédigée au cas par cas serait une affirmation que personne ne pourrait vérifier — et elle serait surlignée, donc crue.",
    "<strong>Aucune lettre que la fiche retient.</strong> Quand la note d'un site ou d'un pilier n'est pas publiable, elle n'apparaît pas davantage ici. Les deux pages disent la même chose, ou elles ne disent rien.",
  ],

  madeTitle: "Comment il est fabriqué",
  madeBody: "Le portrait et la fiche lisent <strong>le même artefact</strong>, produit par le même calcul. Rien n'est saisi deux fois, donc rien ne peut diverger. Les questions viennent d'une table « indicateur × état × stade » ; la procédure d'un dossier où chaque affirmation porte son article de loi, un lien vers le texte et la date à laquelle nous l'avons lu. Quand une juridiction n'est pas lue, le portrait ne l'invente pas : il dit ce qui reste vrai sans elle. <a href=\"/fr/methodologie/\">La méthode</a> et <a href=\"/fr/la-note-pas-a-pas/\">la note pas à pas</a> détaillent le calcul.",

  findTitle: "Trouver le portrait d'un site",
  findBody: "Il n'y a pas de liste des portraits : il y en a un par site noté, et on l'atteint par le site. Partez du lieu, ou de la note.",
  mapHref: "/fr/carte/",
  mapLabel: "Chercher sur la carte →",
  rankHref: "/fr/classement/",
  rankLabel: "Parcourir le classement →",
  examplesIntro: "Trois exemples, trois situations différentes :",
  examples: [
    { href: "/fr/dc/fr-campus-ia-fouju/portrait/", name: "Campus IA Fouju", why: "projet en instruction en Seine-et-Marne : la fenêtre d'observation est ouverte, et la procédure française est lue en entier." },
    { href: "/dc/us-stamp-data-center/portrait/", name: "STAMP Data Center (New York)", why: "projet annoncé aux États-Unis : audience obligatoire de l'agence de développement, examen SEQRA, recours à quatre mois." },
    { href: "/dc/us-microsoft-hoffman-estates-chi05-data-center/portrait/", name: "Hoffman Estates (Illinois)", why: "un État dont nous n'avons pas encore lu la loi : le portrait dit ce qui reste vrai, et quoi demander à la place." },
  ],
};

const EN: typeof FR = {
  title: "The site portrait — ScoreMyDataCenter",
  metaDescription: "Every data centre has two pages here: the technical sheet and the site portrait. Same facts, two readers — the analyst and the neighbour.",
  tagline: "Independent observatory",
  h1: "The site portrait",
  lead: "Every graded site has <strong>two pages</strong> here. The same facts, the same sources, not one datum more — but two readers who share neither the time nor the question. Confuse them and you lose one.",

  twoTitle: "Two pages, two readers",
  portraitFor: "The site portrait",
  portraitWho: "For whoever lives next to it, sits on the council, or covers the story.",
  portraitBullets: [
    "What <strong>weighs most</strong> on the grade, in three points",
    "Where the procedure stands, and <strong>until when</strong> anything can still be done",
    "What is still worth asking for, <strong>and of whom</strong>",
    "Built to be printed and put on a table",
  ],
  sheetFor: "The technical sheet",
  sheetWho: "For whoever reads indicators: operator, analyst, insurer, consultancy.",
  sheetBullets: [
    "The <strong>twenty-six indicators</strong>, one by one",
    "Every value with <strong>its source and its date</strong>",
    "The state of each measure: measured, announced, absent from the file",
    "Comparable sites, graded on the same grid",
  ],
  demoPortraitHref: "/dc/us-stamp-data-center/portrait/",
  demoPortraitLabel: "See a portrait: STAMP Data Center →",
  demoSheetHref: "/dc/us-stamp-data-center/",
  demoSheetLabel: "The same site's technical sheet →",
  notSimplified: "The portrait is not a simplified sheet. It removes nothing: it orders differently, and it goes as far as the question the sheet does not ask — “and now, what do I do?”.",

  addsTitle: "What the portrait adds",
  adds: [
    {
      icon: "measure",
      title: "The points that will decide",
      body: "Three, not twenty-six. Chosen by the calculation, not by us: the factor the engine names as dominant first, then what the <strong>territory imposes</strong> before what the <strong>developer announces</strong>. The distinction matters: one is not negotiable, the other is.",
    },
    {
      icon: "transparency",
      title: "Where the procedure stands, and until when",
      body: "The appeal deadline, the comment window, the complaint route once the site is running — read <strong>in the statute of the country or state concerned</strong>, never in a commentary. Where we have not read it, we say so and say what to ask for instead.",
    },
    {
      icon: "local",
      title: "What is still worth asking for",
      body: "Each question comes from a measure the file leaves blank, and it is conjugated to the stage of the procedure: “to ask before the application is filed”, “to put to the inquiry”, “to get written into the approval”, “to claim under the operating conditions”. A question without its verb is a wish.",
    },
  ],

  refuseTitle: "What it does not do",
  refuse: [
    "<strong>No claim about health.</strong> We measure no health effect and we do not claim to. We publish what is in the file, and what is not.",
    "<strong>No sentence written by hand.</strong> Everything on a portrait is derived from the same data as the sheet. A sentence written case by case would be a claim nobody could check — and it would be highlighted, therefore believed.",
    "<strong>No letter the sheet withholds.</strong> Where a site's or a pillar's grade is not publishable, it does not appear here either. The two pages say the same thing, or they say nothing.",
  ],

  madeTitle: "How it is built",
  madeBody: "The portrait and the sheet read <strong>the same artefact</strong>, produced by the same calculation. Nothing is entered twice, so nothing can diverge. The questions come from an “indicator × state × stage” table; the procedure from a registry where every claim carries its article, a link to the text, and the date we read it. Where a jurisdiction is unread, the portrait does not invent it: it says what remains true without it. <a href=\"/methodology/\">The method</a> and <a href=\"/the-grade-step-by-step/\">the grade step by step</a> set out the calculation.",

  findTitle: "Finding a site's portrait",
  findBody: "There is no list of portraits: there is one per graded site, and you reach it through the site. Start from the place, or from the grade.",
  mapHref: "/map/",
  mapLabel: "Search the map →",
  rankHref: "/ranking/",
  rankLabel: "Browse the ranking →",
  examplesIntro: "Three examples, three different situations:",
  examples: [
    { href: "/fr/dc/fr-campus-ia-fouju/portrait/", name: "Campus IA Fouju (France)", why: "a project under review: the comment window is open, and the French procedure is read in full." },
    { href: "/dc/us-stamp-data-center/portrait/", name: "STAMP Data Center (New York)", why: "an announced US project: a mandatory development-agency hearing, SEQRA review, a four-month challenge window." },
    { href: "/dc/us-microsoft-hoffman-estates-chi05-data-center/portrait/", name: "Hoffman Estates (Illinois)", why: "a state whose law we have not read yet: the portrait says what remains true, and what to ask for instead." },
  ],
};

/** La table servie au gabarit : `PORTRAIT_EXPLAINER[lang]`. */
export const PORTRAIT_EXPLAINER: Record<Langue, typeof FR> = { fr: FR, en: EN };
