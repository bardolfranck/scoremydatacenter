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

import type { Langue } from "./langues";
// 🔴 `nav` n'est PAS de la copie : c'est la structure du menu, et la table la porte parce
// que le gabarit `Understand.astro` la lit dans `t`. Elle vivait dans la page, où le menu
// de la bonne langue était à portée ; ici il faut l'importer — mais la source reste unique
// (`config/nav.ts`), et une langue nouvelle déclarera son menu au même endroit que les
// autres. Déplacer `nav` hors de `t` demanderait de retoucher le gabarit : pas dans ce lot,
// qui ne doit rien changer à ce qui est rendu.
import { FR_NAV, EN_NAV } from "../config/nav";

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
      anchor: "quoi",
      title: "C'est quoi, un data center ?",
      slot: "whatis",
    },
    {
      anchor: "commune",
      title: "Pourquoi ça concerne ma commune",
      slot: "rich",
    },
    {
      anchor: "questions",
      title: "Les bonnes questions à poser",
      body: "La checklist qui épouse nos piliers de notation : énergie, eau, foncier, impact local, transparence.",
      featured: true,
      slot: "checklist",
    },
    {
      anchor: "bon-projet",
      title: "C'est quoi, un « bon » projet ?",
      slot: "rich",
    },
    {
      anchor: "droits",
      title: "Droits et calendrier",
      slot: "rich",
    },
    {
      anchor: "faq",
      title: "Questions pratiques",
      slot: "rich",
    },
    {
      anchor: "aller-plus-loin",
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
      anchor: "what",
      title: "What is a data center?",
      slot: "whatis",
      tag: "France",
    },
    {
      anchor: "municipality",
      title: "Why it concerns my municipality",
      slot: "rich",
      tag: "France",
    },
    {
      anchor: "questions",
      title: "The right questions to ask",
      body: "The checklist that mirrors our scoring pillars: energy, water, land, local impact, transparency.",
      featured: true,
      slot: "checklist",
    },
    {
      anchor: "good-project",
      title: "What makes a “good” project?",
      slot: "rich",
    },
    {
      anchor: "rights",
      title: "Rights and timeline",
      slot: "rich",
      tag: "France",
    },
    {
      anchor: "faq",
      title: "Practical questions",
      slot: "rich",
    },
    {
      anchor: "further",
      title: "Going further",
      slot: "rich",
    },
  ],
};

/** La table servie au gabarit : `COMPRENDRE[lang]`. */
export const COMPRENDRE = { fr: FR, en: EN } satisfies Record<Langue, unknown>;
