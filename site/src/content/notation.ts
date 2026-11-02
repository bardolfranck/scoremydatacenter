// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La page de concept « La notation » — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
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

const FR = {
  title: "Noter un data center — la méthode Nutri-Score de l'acceptabilité | ScoreMyDataCenter",
  metaDescription: "Comment note-t-on un data center ? Deux notes de A à E — site et projet — avec niveau de confiance et méthode ouverte. Le « Nutri-Score » de l'acceptabilité, projet par projet.",
  tagline: "Observatoire indépendant",
  h1: "La notation des data centers",
  lead: "Noter un data center, c'est résumer en une lettre de <strong><span class='note-inline n-a'>A</span> à <span class='note-inline n-e'>E</span></strong> ce que des dizaines d'indicateurs sourcés disent de son empreinte et de sa conduite — comme un <strong>Nutri-Score</strong>, mais pour un projet d'infrastructure. Nous attribuons <strong>deux notes</strong> par projet, toujours assorties d'un niveau de confiance.",
  sections: [
    { h2: "L'idée du Nutri-Score",
      corps: "<p>Une étiquette lisible par tous devant une réalité technique complexe. Une lettre ne remplace pas le dossier : elle y donne accès et le rend comparable d'un site à l'autre.</p>" },
    { h2: "Deux notes, pas une",
      corps: "<p>Une pour le <strong>site</strong> — le contexte que le projet subit, qu'il n'a pas choisi — et une pour le <strong>projet et le processus</strong> — ce que l'opérateur décide. Les séparer évite qu'un bon dossier rachète un mauvais terrain, ou l'inverse. Une note n'est <strong>pas</strong> la moyenne des piliers : voir <a href=\"/fr/methodologie\">la méthode</a>.</p>" },
    { h2: "Cinq piliers, des poids explicites",
      corps: "<p>Énergie 25 %, Eau 20 %, Foncier et biodiversité 20 %, Impact local 20 %, Transparence et gouvernance 15 %. Ces poids sont publics et ne changent pas d'un site à l'autre.</p>" },
    { h2: "La confiance ne se sépare jamais de la note",
      corps: "<p>Sous 40 % de couverture documentaire, nous écrivons « données insuffisantes » au lieu d'une lettre. <strong>Le <span class='note-inline n-a'>A</span> se prouve, il ne se promet pas</strong> : une absence de donnée ne vaut jamais une bonne note — sans quoi le site le moins transparent serait le mieux noté.</p>" },
    { h2: "Une méthode reproductible",
      corps: "<p>Le calcul ne repose que sur les valeurs sourcées du fichier de chaque projet, et la méthode est ouverte. Pour la voir s'appliquer pas à pas : <a href=\"/fr/la-note-pas-a-pas\">la note, pas à pas</a>, <a href=\"/fr/classement\">le classement</a>, <a href=\"/fr/carte\">la carte</a>.</p>" },
  ],
};

const EN: typeof FR = {
  title: 'Rating a data center — the Nutri-Score method for acceptability | ScoreMyDataCenter',
  metaDescription: 'How is a data center rated? Two grades from A to E — site and project — each with a confidence level and an open method. The “Nutri-Score” of acceptability, project by project.',
  tagline: "Independent observatory",
  h1: 'Data center rating',
  lead: 'Rating a data center means summarising, in a single letter from <strong><span class="note-inline n-a">A</span> to <span class="note-inline n-e">E</span></strong>, what dozens of sourced indicators say about its footprint and its conduct — like a <strong>Nutri-Score</strong>, but for an infrastructure project. We assign <strong>two grades</strong> per project, always paired with a confidence level.',
  sections: [
    { h2: 'The Nutri-Score idea', corps: '<p>A label anyone can read in front of a complex technical reality. A letter does not replace the file: it opens it, and makes it comparable from one site to the next.</p>' },
    { h2: 'Two grades, not one', corps: '<p>One for the <strong>site</strong> — the context the project endures and did not choose — and one for the <strong>project and process</strong> — what the operator decides. Keeping them apart stops a good file from buying off a bad location, or the reverse. A grade is <strong>not</strong> the average of the pillars: see <a href="/methodology/">the method</a>.</p>' },
    { h2: 'Five pillars, explicit weights', corps: '<p>Energy 25%, Water 20%, Land and biodiversity 20%, Local impact 20%, Transparency and governance 15%. These weights are public and do not vary from one site to another.</p>' },
    { h2: 'Confidence is never detached from the grade', corps: '<p>Below 40% documentary coverage we write “insufficient data” instead of a letter. <strong>An <span class="note-inline n-a">A</span> is proven, never promised</strong>: missing data never earns a good grade — otherwise the least transparent site would be the best rated.</p>' },
    { h2: 'A reproducible method', corps: '<p>The calculation rests only on the sourced values in each project\'s file, and the method is open. To see it applied step by step: <a href="/the-grade-step-by-step/">the grade, step by step</a>, <a href="/ranking/">the ranking</a>, <a href="/map/">the map</a>.</p>' },
  ],
};


// ── NÉERLANDAIS — EN PRÉPARATION, PAS ENCORE SERVI (voir `content/langues.ts`).
// ⚠️ Les valeurs ci-dessous sont encore LE TEXTE FRANÇAIS, copié tel quel. Elles sont là
// pour qu'un traducteur natif ait la source sous les yeux, à sa place dans la structure.
// Elles NE DOIVENT PAS partir en ligne : `nl` n'est pas dans `LANGUES_VIVANTES`, et
// `test_une_langue_ne_devient_vivante_que_traduite` refuse de l'y faire entrer tant que
// ses valeurs sont celles du français.
const NL: typeof FR = {
  title: "Een datacenter beoordelen — de Nutri-Score-methode voor maatschappelijke acceptatie | ScoreMyDataCenter",
  metaDescription: "Hoe wordt een datacenter beoordeeld? Twee cijfers van A tot E — site en project — met een vertrouwensniveau en een open methode. De ‘Nutri-Score’ van de maatschappelijke acceptatie, project per project.",
  tagline: "Onafhankelijk observatorium",
  h1: "De beoordeling van datacenters",
  lead: "Een datacenter beoordelen is in één letter van <strong><span class='note-inline n-a'>A</span> tot <span class='note-inline n-e'>E</span></strong> samenvatten wat tientallen gedocumenteerde indicatoren zeggen over zijn voetafdruk en zijn gedrag — als een <strong>Nutri-Score</strong>, maar voor een infrastructuurproject. We kennen per project <strong>twee cijfers</strong> toe, altijd samen met een vertrouwensniveau.",
  sections: [
    { h2: "Het idee van de Nutri-Score",
      corps: "<p>Een etiket dat iedereen kan lezen, vóór een complexe technische werkelijkheid. Een letter vervangt het dossier niet: ze opent het, en maakt het vergelijkbaar van site tot site.</p>" },
    { h2: "Twee cijfers, niet één",
      corps: "<p>Eén voor de <strong>site</strong> — de context die het project ondergaat en niet heeft gekozen — en één voor <strong>project en proces</strong> — wat de exploitant beslist. Ze scheiden voorkomt dat een goed dossier een slechte plek afkoopt, of omgekeerd. Een cijfer is <strong>niet</strong> het gemiddelde van de pijlers: zie <a href=\"/fr/methodologie\">de methode</a>.</p>" },
    { h2: "Vijf pijlers, expliciete gewichten",
      corps: "<p>Energie 25 %, Water 20 %, Bodem en biodiversiteit 20 %, Lokale impact 20 %, Transparantie en governance 15 %. Deze gewichten zijn openbaar en verschillen niet van site tot site.</p>" },
    { h2: "Het vertrouwen laat zich nooit van het cijfer scheiden",
      corps: "<p>Onder 40 % documentaire dekking schrijven we ‘onvoldoende gegevens’ in plaats van een letter. <strong>Een <span class='note-inline n-a'>A</span> bewijs je, een A beloof je niet</strong>: ontbrekende gegevens leveren nooit een goed cijfer op — anders zou de minst transparante site het best beoordeeld zijn.</p>" },
    { h2: "Een reproduceerbare methode",
      corps: "<p>De berekening steunt uitsluitend op de waarden mét bron in het dossier van elk project, en de methode is open. Om de methode stap voor stap toegepast te zien: <a href=\"/fr/la-note-pas-a-pas\">het cijfer, stap voor stap</a>, <a href=\"/fr/classement\">de ranglijst</a>, <a href=\"/fr/carte\">de kaart</a>.</p>" },
  ],
};

/** La table servie au gabarit : `NOTATION[lang]`. */
export const NOTATION: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
