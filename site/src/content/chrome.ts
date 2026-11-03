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
  consent: {
    aria: "Audience-measurement consent",
    text: "Audience measurement: we use Google Analytics to count visits and understand what gets read. No cookie is set without your consent.",
    moreHref: "/legal",
    more: "Learn more",
    decline: "Decline",
    accept: "Accept",
  },
};


// ── NÉERLANDAIS — EN PRÉPARATION, PAS ENCORE SERVI (voir `content/langues.ts`).
// ⚠️ Les valeurs ci-dessous sont encore LE TEXTE FRANÇAIS, copié tel quel. Elles sont là
// pour qu'un traducteur natif ait la source sous les yeux, à sa place dans la structure.
// Elles NE DOIVENT PAS partir en ligne : `nl` n'est pas dans `LANGUES_VIVANTES`, et
// `test_une_langue_ne_devient_vivante_que_traduite` refuse de l'y faire entrer tant que
// ses valeurs sont celles du français.
const NL: typeof FR = {
  // Baseline = description schema.org ET accroche du pied de page (une seule phrase).
  baseline: "Onafhankelijk observatorium van het acceptatierisico van datacenters.",
  ogLocale: "nl_NL",
  search: {
    action: "/nl/ranglijst",
    placeholder: "Zoek een gemeente, een site, een exploitant…",
    aria: "Zoek een gemeente of een beoordeeld project",
  },
  // Slugs NL choisis AVEC les libellés (règle du fichier : le mot commande l'URL).
  footer: [
    { heading: "Verkennen", links: [
      { label: "Kaart", href: "/nl/kaart/" },
      { label: "Ranglijst", href: "/nl/ranglijst/" },
      { label: "Landenindex", href: "/nl/indices/" },
      { label: "Kerncijfers van het datacenterpark", href: "/nl/kerncijfers/" },
      { label: "Datacenters begrijpen", href: "/nl/datacenters-begrijpen/" },
    ] },
    { heading: "Hulpmiddelen", links: [
      { label: "Methodologie", href: "/nl/methodologie/" },
      { label: "Open model", href: "/nl/#open" },
      { label: "Bibliotheek", href: "/nl/bibliotheek/" },
      { label: "API voor ontwikkelaars", href: "/nl/ontwikkelaars/" },
      { label: "FAQ", href: "/nl/#faq" },
    ] },
    { heading: "Over", links: [
      { label: "Over ons", href: "/nl/over-ons/" },
      { label: "Pers", href: "/nl/pers/" },
      { label: "Contact", href: "/nl/contact/" },
      { label: "Juridische informatie", href: "/nl/juridisch/" },
    ] },
  ],
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
