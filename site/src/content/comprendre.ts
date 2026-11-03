// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La page « Comprendre les data centers » — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
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
// 🔴 `nav` n'est PAS de la copie : c'est la structure du menu, et la table la porte parce
// que le gabarit `Understand.astro` la lit dans `t`. Elle vivait dans la page, où le menu
// de la bonne langue était à portée ; ici il faut l'importer — mais la source reste unique
// (`config/nav.ts`), et une langue nouvelle déclarera son menu au même endroit que les
// autres. Déplacer `nav` hors de `t` demanderait de retoucher le gabarit : pas dans ce lot,
// qui ne doit rien changer à ce qui est rendu.
import { FR_NAV, EN_NAV, NL_NAV } from "../config/nav";

const FR = {
  title: "Comprendre les data centers, sans jargon — ScoreMyDataCenter",
  description:
    "Ce qu'un data center change vraiment près de chez vous : ordres de grandeur, impact local, les bonnes questions à poser, vos droits, le calendrier. En clair, sans jargon.",
  tagline: "Observatoire indépendant",
  altHref: "/understand/",
  altLabel: "EN",
  nav: FR_NAV,
  pageTitle: "Comprendre les data centers",
  lede:
    "Pour l'élu qui reçoit l'appel d'un cabinet, le riverain qui découvre un panneau d'enquête publique, le journaliste qui débute sur le sujet : l'essentiel, sans jargon. Ce qui se cache derrière les chiffres.",
  pendingLabel: "Texte en préparation",
  whyLabel: "Pourquoi :",
  takeawayLabel: "À retenir —",
  sourcesLabel: "Sources :",
  seeMore: "Voir plus…",
  seeLess: "Réduire",
  tocAria: "Sommaire",
  blocks: [
    {
      id: "what-is", anchor: "quoi",
      title: "C'est quoi, un data center ?",
      slot: "whatis",
    },
    {
      id: "why-local", anchor: "commune",
      title: "Pourquoi ça concerne ma commune",
      slot: "rich",
    },
    {
      id: "questions-to-ask", anchor: "questions",
      title: "Les bonnes questions à poser",
      body: "La checklist qui épouse nos piliers de notation : énergie, eau, foncier, impact local, transparence.",
      featured: true,
      slot: "checklist",
    },
    {
      id: "what-makes-good", anchor: "bon-projet",
      title: "C'est quoi, un « bon » projet ?",
      slot: "rich",
    },
    {
      id: "your-rights", anchor: "droits",
      title: "Droits et calendrier",
      slot: "rich",
    },
    {
      id: "faq-block", anchor: "faq",
      title: "Questions pratiques",
      slot: "rich",
    },
    {
      id: "read-more", anchor: "aller-plus-loin",
      title: "Aller plus loin",
      slot: "rich",
    },
  ],
};

// 🔴 ASYMÉTRIE VOULUE, pas un oubli : EN porte en plus contextNotice, inFranceLabel, tag. L'anglais
// s'adresse à un lecteur qui n'est pas en France et a besoin qu'on le lui dise ;
// le gabarit teste ces clés (`t.x && …`), donc leur absence ne rend rien côté FR.
// Ces feuilles sont déclarées dans `ASYMETRIES_MODULES` du garde de parité : une
// asymétrie non déclarée reste une dérive.
const EN = {
  title: "Data centers, explained without jargon — ScoreMyDataCenter",
  description:
    "What a data center really means for your area: orders of magnitude, local impact, the right questions to ask, your rights and the timeline. Plain language, no jargon.",
  tagline: "Independent observatory",
  altHref: "/fr/comprendre/",
  altLabel: "FR",
  nav: EN_NAV,
  pageTitle: "Understanding data centers",
  lede:
    "For the local official getting the developer's call, the resident discovering a public-inquiry notice, the journalist new to the beat: the essentials, without jargon. What hides behind the numbers.",
  pendingLabel: "Text in preparation",
  whyLabel: "Why:",
  takeawayLabel: "Takeaway —",
  sourcesLabel: "Sources:",
  seeMore: "See more…",
  seeLess: "Collapse",
  tocAria: "Contents",
  inFranceLabel: "In France —",
  contextNotice:
    "This guide is written from the <strong>French</strong> regulatory and market context — the observatory's first scored country. The questions in block 3 travel anywhere; figures, rights and timelines are France-specific. Country-specific versions will follow the observatory's expansion.",
  blocks: [
    {
      id: "what-is", anchor: "what",
      title: "What is a data center?",
      slot: "whatis",
      tag: "France",
    },
    {
      id: "why-local", anchor: "municipality",
      title: "Why it concerns my municipality",
      slot: "rich",
      tag: "France",
    },
    {
      id: "questions-to-ask", anchor: "questions",
      title: "The right questions to ask",
      body: "The checklist that mirrors our scoring pillars: energy, water, land, local impact, transparency.",
      featured: true,
      slot: "checklist",
    },
    {
      id: "what-makes-good", anchor: "good-project",
      title: "What makes a “good” project?",
      slot: "rich",
    },
    {
      id: "your-rights", anchor: "rights",
      title: "Rights and timeline",
      slot: "rich",
      tag: "France",
    },
    {
      id: "faq-block", anchor: "faq",
      title: "Practical questions",
      slot: "rich",
    },
    {
      id: "read-more", anchor: "further",
      title: "Going further",
      slot: "rich",
    },
  ],
};


// ── NÉERLANDAIS — EN PRÉPARATION, PAS ENCORE SERVI (voir `content/langues.ts`).
// ⚠️ Les valeurs ci-dessous sont encore LE TEXTE FRANÇAIS, copié tel quel. Elles sont là
// pour qu'un traducteur natif ait la source sous les yeux, à sa place dans la structure.
// Elles NE DOIVENT PAS partir en ligne : `nl` n'est pas dans `LANGUES_VIVANTES`, et
// `test_une_langue_ne_devient_vivante_que_traduite` refuse de l'y faire entrer tant que
// ses valeurs sont celles du français.
// Comme EN, le bloc NL est non typé : il porte les clés d'avertissement de contexte
// (contextNotice/inFranceLabel/tag) que `typeof FR` ne connaît pas — le lecteur NL
// n'est pas en France, le garde `test_une_langue_servie_hors_france_porte_son_
// avertissement_de_contexte` les exige à la mise en vie.
const NL = {
  title: "Datacenters begrijpen, zonder jargon — ScoreMyDataCenter",
  description:
    "Wat een datacenter echt verandert in uw buurt: ordes van grootte, lokale impact, de juiste vragen om te stellen, uw rechten, het tijdpad. In klare taal, zonder jargon.",
  tagline: "Onafhankelijk observatorium",
  altHref: "/understand/",
  altLabel: "EN",
  nav: NL_NAV,
  pageTitle: "Datacenters begrijpen",
  lede:
    "Voor de bestuurder die een adviesbureau aan de lijn krijgt, de omwonende die een bekendmaking van een inspraakprocedure ontdekt, de journalist die net op het onderwerp begint: de essentie, zonder jargon. Wat er achter de getallen schuilgaat.",
  pendingLabel: "Tekst in voorbereiding",
  whyLabel: "Waarom:",
  takeawayLabel: "Onthoud —",
  sourcesLabel: "Bronnen:",
  seeMore: "Meer tonen…",
  seeLess: "Inklappen",
  tocAria: "Inhoud",
  inFranceLabel: "In Frankrijk —",
  contextNotice:
    "Deze gids is geschreven vanuit de <strong>Franse</strong> regelgeving en markt — het eerste land dat het observatorium volledig beoordeelt. De vragen in blok 3 gelden overal; bedragen, rechten en termijnen zijn Frans. Landspecifieke versies volgen met de uitbreiding van het observatorium.",
  blocks: [
    {
      id: "what-is", anchor: "wat",
      title: "Wat is een datacenter?",
      slot: "whatis",
      tag: "Frankrijk",
    },
    {
      id: "why-local", anchor: "gemeente",
      title: "Waarom dit mijn gemeente aangaat",
      slot: "rich",
      tag: "Frankrijk",
    },
    {
      id: "questions-to-ask", anchor: "vragen",
      title: "De juiste vragen om te stellen",
      body: "De checklist die onze beoordelingspijlers volgt: energie, water, bodem, lokale impact, transparantie.",
      featured: true,
      slot: "checklist",
    },
    {
      id: "what-makes-good", anchor: "goed-project",
      title: "Wat is een ‘goed’ project?",
      slot: "rich",
    },
    {
      id: "your-rights", anchor: "rechten",
      title: "Rechten en tijdpad",
      slot: "rich",
      tag: "Frankrijk",
    },
    {
      id: "faq-block", anchor: "faq",
      title: "Praktische vragen",
      slot: "rich",
    },
    {
      id: "read-more", anchor: "verder",
      title: "Verder lezen",
      slot: "rich",
    },
  ],
};

/** La table servie au gabarit : `COMPRENDRE[lang]`. */
export const COMPRENDRE = { fr: FR, en: EN, nl: NL } satisfies Record<LangueDeclaree, unknown>;
