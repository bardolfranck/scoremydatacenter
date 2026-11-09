// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Les chaînes du CHROME : ce que `Base.astro` met autour de chaque page — accroche, boîte de
// recherche, menu de pied de page, bandeau de consentement. Elles sont sur les 13 168 pages,
// donc sur chaque page d'une langue nouvelle : un lecteur néerlandais verrait sinon « Refuser »
// et « Accepter » en français sous une fiche néerlandaise.
//
// 🔴 Les SLUGS du pied de page vivent ici, avec leurs libellés. Ce n'est pas un relâchement de
// la règle « les chemins restent en code » : un chemin CALCULÉ (`/fr` contre rien) reste en
// code, mais un slug de menu est une décision de langue — c'est celle que Franck a prise le
// 2026-10-29 en validant `maatschappelijke acceptatie`, où le mot choisi commande l'URL. Les
// demander ensemble évite qu'une langue nouvelle ait des libellés traduits pointant vers des
// URL françaises.
//
// Comme pour `fiche.ts` : le type ne garde rien au build (`astro build` tourne sans
// `astro check`), c'est `engine/tests/test_i18n_parity.py` qui mord.

import type { Langue, LangueDeclaree } from "./langues";

const FR = {
  // 🔴 L'ATTRIBUTION ODbL EST UN TEXTE, DONC ELLE EST ICI (B-1, avis cabinet
  // 2026-07-27 : « contient des informations de », jamais « basé sur »). Elle se
  // décidait dans DEUX scripts client, chacun par un test sur la langue — et
  // `MapIsland` la déduisait d'un `base.startsWith("/fr")`, c'est-à-dire d'un
  // préfixe d'URL. Une mention légale choisie par la forme d'une adresse.
  dcwatch: 'Contient des informations de <a href="https://dcwatch.hubblo.org" target="_blank" rel="noopener">DCWatch (Hubblo)</a>, ODbL',
  // La même phrase sert la description schema.org de l'organisation ET l'accroche du pied de
  // page. Elle était écrite deux fois dans Base.astro, à 130 lignes d'écart.
  baseline: "Observatoire indépendant du risque d'acceptabilité des data centers.",
  ogLocale: "fr_FR",
  search: {
    action: "/fr/classement/",
    placeholder: "Rechercher une commune, un site, un opérateur…",
    aria: "Rechercher une commune ou un projet noté",
  },
  footer: [
    { heading: "Explorer", links: [
      { label: "Carte", href: "/fr/carte/" },
      { label: "Classement", href: "/fr/classement/" },
      { label: "Indices pays", href: "/fr/indices/" },
      { label: "Les chiffres du parc", href: "/fr/chiffres/" },
      { label: "Comprendre les data centers", href: "/fr/comprendre/" },
    ] },
    { heading: "Ressources", links: [
      { label: "Méthodologie", href: "/fr/methodologie/" },
      { label: "Modèle ouvert", href: "/fr/#open" },
      { label: "Bibliothèque", href: "/fr/bibliotheque/" },
      { label: "API développeurs", href: "/fr/developpeurs/" },
      { label: "FAQ", href: "/fr/#faq" },
    ] },
    { heading: "À propos", links: [
      { label: "Qui sommes-nous ?", href: "/fr/qui-sommes-nous/" },
      { label: "Presse", href: "/fr/presse/" },
      { label: "Contact", href: "/fr/contact/" },
      { label: "Mentions légales", href: "/fr/mentions-legales/" },
    ] },
  ],
  // 🔴 CE QUE LE SÉLECTEUR DE LANGUE NE DISAIT PAS. Depuis le 2026-11-06, une édition de
  // pays ne couvre QUE ses pays (`PAYS_DE_LA_LANGUE`) : l'édition néerlandaise publie les
  // fiches néerlandaises et belges, et sert les autres en anglais. C'était vrai, voulu,
  // documenté — et invisible. Un lecteur qui cliquait « NL » ne pouvait pas distinguer un
  // choix éditorial d'une traduction en retard.
  //
  // Le trou `{pays}` est rempli par le gabarit avec les pays que la DÉCLARATION donne, dans
  // la langue de qui lit : la phrase ne nomme donc aucun pays en dur, et l'édition suivante
  // sera décrite juste sans qu'on rouvre cette table. La phrase est servie dans la langue de
  // la PAGE, pas dans celle de l'édition visée — un francophone qui hésite doit comprendre
  // l'avertissement avant de changer de langue, pas après.
  //
  // 🔴 ET LA LISTE VIENT APRÈS UN DEUX-POINTS, PAS EN COMPLÉMENT. Première version :
  // « les fiches de {pays} » — rendu « les fiches de Pays-Bas et Belgique » dans le
  // navigateur. L'article contracté devant un nom de pays (« des Pays-Bas », « de la
  // Belgique ») est une règle du français, et une liste DÉRIVÉE ne peut pas la porter :
  // il faudrait déclarer le genre et l'article de chaque pays, dans chaque langue, pour
  // une phrase de huit mots. Mettre la liste après un deux-points supprime le besoin — et
  // vaut pour un pays comme pour cinq. Trouvé en REGARDANT la page, pas par un test.
  apercuEdition: "Fiches et pages d'explication\u202f: {pays}. Ailleurs, l'anglais.",
  consent: {
    aria: "Consentement à la mesure d'audience",
    text: "Mesure d'audience : nous utilisons Google Analytics pour compter les visites et comprendre ce qui est lu. Aucun cookie n'est déposé sans votre accord.",
    moreHref: "/fr/mentions-legales",
    more: "En savoir plus",
    decline: "Refuser",
    accept: "Accepter",
  },
};

const EN: typeof FR = {
  dcwatch: 'Contains information from <a href="https://dcwatch.hubblo.org" target="_blank" rel="noopener">DCWatch (Hubblo)</a>, ODbL',
  baseline: "Independent observatory of data-center acceptability risk.",
  ogLocale: "en_GB",
  search: {
    action: "/ranking/",
    placeholder: "Search a town, a site, an operator…",
    aria: "Search a town or a scored project",
  },
  footer: [
    { heading: "Explore", links: [
      { label: "Map", href: "/map/" },
      { label: "Ranking", href: "/ranking/" },
      { label: "Country index", href: "/indices/" },
      { label: "Fleet figures", href: "/figures/" },
      { label: "Understanding data centers", href: "/understand/" },
    ] },
    { heading: "Resources", links: [
      { label: "Methodology", href: "/methodology/" },
      { label: "Open model", href: "/#open" },
      { label: "Library", href: "/intelligence/" },
      { label: "Developer API", href: "/developers/" },
      { label: "FAQ", href: "/#faq" },
    ] },
    { heading: "About", links: [
      { label: "Who we are", href: "/who-we-are/" },
      { label: "Press", href: "/press/" },
      { label: "Contact", href: "/contact/" },
      { label: "Legal notices", href: "/legal/" },
    ] },
  ],
  apercuEdition: "Sites and explainer pages: {pays}. Elsewhere, English.",
  consent: {
    aria: "Audience-measurement consent",
    text: "Audience measurement: we use Google Analytics to count visits and understand what gets read. No cookie is set without your consent.",
    moreHref: "/legal",
    more: "Learn more",
    decline: "Decline",
    accept: "Accept",
  },
};


// ── NÉERLANDAIS — SERVI DEPUIS LE 2026-11-06 (voir `content/langues.ts`).
// ⚠️ Ce commentaire disait encore « EN PRÉPARATION, PAS ENCORE SERVI » et « les valeurs
// ci-dessous sont encore LE TEXTE FRANÇAIS » : les deux étaient faux depuis le 2026-11-06.
// Un commentaire périmé sur un bloc SERVI est pire qu'une absence de commentaire — il
// autorise à traiter ces chaînes comme un brouillon alors qu'elles sont sur chaque page
// néerlandaise. Corrigé le 2026-11-08, en ajoutant `apercuEdition`.
const NL: typeof FR = {
  dcwatch: 'Bevat informatie van <a href="https://dcwatch.hubblo.org" target="_blank" rel="noopener">DCWatch (Hubblo)</a>, ODbL',
  // Baseline = description schema.org ET accroche du pied de page (une seule phrase).
  baseline: "Onafhankelijk observatorium van het acceptatierisico van datacenters.",
  ogLocale: "nl_NL",
  search: {
    action: "/nl/ranglijst/",
    placeholder: "Zoek een gemeente, een site, een exploitant…",
    aria: "Zoek een gemeente of een beoordeeld project",
  },
  // Slugs NL choisis AVEC les libellés (règle du fichier : le mot commande l'URL).
  footer: [
    { heading: "Verkennen", links: [
      { label: "Kaart", href: "/nl/kaart/" },
      { label: "Ranglijst", href: "/nl/ranglijst/" },
      { label: "Landenindex", href: "/nl/indices/" },
      { label: "Datacenters begrijpen", href: "/nl/datacenters-begrijpen/" },
    ] },
    { heading: "Hulpmiddelen", links: [
      { label: "Methodologie", href: "/nl/methodologie/" },
      { label: "Open model", href: "/nl/#open" },
      { label: "Bibliotheek", href: "/nl/bibliotheek/" },
      { label: "FAQ", href: "/nl/#faq" },
    ] },
    { heading: "Over", links: [
      { label: "Over ons", href: "/nl/over-ons/" },
      { label: "Contact", href: "/nl/contact/" },
      { label: "Juridische informatie", href: "/nl/juridisch/" },
    ] },
  ],
  apercuEdition: "Datacenters en uitlegpagina's: {pays}. Elders Engels.",
  consent: {
    aria: "Toestemming voor bezoekersstatistieken",
    text: "Bezoekersstatistieken: we gebruiken Google Analytics om bezoeken te tellen en te begrijpen wat er wordt gelezen. Zonder uw toestemming wordt geen cookie geplaatst.",
    moreHref: "/nl/juridisch",
    more: "Meer informatie",
    decline: "Weigeren",
    accept: "Accepteren",
  },
};

/** Le chrome servi au gabarit : `CHROME[lang]`. */
export const CHROME: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
