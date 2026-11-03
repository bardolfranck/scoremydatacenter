// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Block 1 "What is a data center?" — authored by the methodology lead
// (2026-07-06), every figure verified against its source before integration.
// Fix applied at integration: Fouju is ~90 ha per the official public
// consultation (the delivered 87 ha was not in the cited source).

export interface PowerScaleItem {
  mw: number;
  mwLabel: string;
  label: string;
}
export interface WhatIsDC {
  paragraphs: string[];
  sizesTitle: string;
  sizes: { label: string; power: string; note: string }[];
  scale: { caption: string; items: PowerScaleItem[] };
  statsParagraph: string;
  takeaway: string;
  sourcesLabel: string;
  sources: { label: string; url: string }[];
}

export const WHATIS_FR: WhatIsDC = {
  paragraphs: [
    "Un data center est un bâtiment industriel rempli de serveurs — les ordinateurs qui font fonctionner les sites web, les vidéos, les services en ligne et, de plus en plus, l'intelligence artificielle. Ces machines tournent jour et nuit, consomment de l'électricité en continu et dégagent de la chaleur qu'il faut évacuer. C'est de là que viennent leurs besoins en énergie et, selon la technique de refroidissement, en eau.",
    "Pour mesurer un data center, la bonne unité n'est pas la surface du bâtiment mais la <strong>puissance électrique, en mégawatts (MW)</strong> — le débit d'électricité que le site peut appeler à chaque instant.",
  ],
  sizesTitle: "Trois tailles très différentes portent le même nom :",
  sizes: [
    {
      label: "Data center « classique »",
      power: "quelques MW",
      note: "La grande majorité des ~300 sites français, raccordés au réseau de distribution comme une grosse usine<sup><a href='#src-quoi-1'>1</a></sup>",
    },
    {
      label: "Grand projet",
      power: "100 à 200 MW",
      note: "La consommation électrique de villes comme Le Mans ou Saint-Étienne<sup><a href='#src-quoi-1'>1</a></sup>",
    },
    {
      label: "Méga-projet",
      power: "plus de 400 MW",
      note: "Une dizaine de projets « hors normes » en France ; le Campus IA de Fouju vise 1 400 MW sur environ 90 hectares<sup><a href='#src-quoi-1'>1</a></sup><sup><a href='#src-quoi-3'>3</a></sup>",
    },
  ],
  scale: {
    caption: "Les surfaces sont proportionnelles à la puissance électrique.",
    items: [
      { mw: 3, mwLabel: "quelques MW", label: "data center classique" },
      { mw: 150, mwLabel: "150 MW", label: "grand projet ≈ Le Mans" },
      { mw: 1400, mwLabel: "1 400 MW", label: "méga-projet (Fouju)" },
    ],
  },
  statsParagraph:
    "Aujourd'hui, l'ensemble des data centers représente environ 2 % de l'électricité consommée en France ; RTE anticipe environ 4 % en 2035<sup><a href='#src-quoi-1'>1</a></sup>. À l'échelle mondiale, ils pèsent environ 1,5 % de la consommation d'électricité en 2024<sup><a href='#src-quoi-4'>4</a></sup>.",
  takeaway:
    "Le même mot désigne une salle de quelques mégawatts et un campus mille fois plus puissant. Face à un projet, la première question est toujours : combien de mégawatts ?",
  sourcesLabel: "Sources :",
  sources: [
    { label: "RTE, « Les data centers en chiffres clés », 2026", url: "https://www.rte-france.com/bases-electricite/consommation-electricite/essor-data-centers-france" },
    { label: "Journal du Grand Paris, 2025", url: "https://www.lejournaldugrandparis.fr/choose-france-un-campus-dia-geant-en-seine-et-marne/" },
    { label: "Concertation publique Campus IA", url: "https://www.concertation-campus-ia.fr/fr/comprendre-le-projet" },
    { label: "AIE, Energy and AI, 2025", url: "https://www.iea.org/reports/energy-and-ai/executive-summary" },
  ],
};

export const WHATIS_EN: WhatIsDC = {
  paragraphs: [
    "A data center is an industrial building full of servers — the computers that run websites, videos, online services and, increasingly, artificial intelligence. These machines run day and night, draw electricity continuously and give off heat that must be removed. That is where their energy needs come from — and, depending on the cooling technique, their water needs.",
    "To size a data center, the right unit is not the building's footprint but its <strong>electrical power, in megawatts (MW)</strong> — the flow of electricity the site can draw at any moment.",
  ],
  sizesTitle: "Three very different sizes share the same name:",
  sizes: [
    {
      label: "“Classic” data center",
      power: "a few MW",
      note: "The vast majority of France's ~300 sites, connected to the distribution grid like a large factory<sup><a href='#src-what-1'>1</a></sup>",
    },
    {
      label: "Large project",
      power: "100 to 200 MW",
      note: "The electricity consumption of cities like Le Mans or Saint-Étienne<sup><a href='#src-what-1'>1</a></sup>",
    },
    {
      label: "Mega-project",
      power: "above 400 MW",
      note: "About a dozen “out of the ordinary” projects in France; the Fouju AI Campus targets 1,400 MW on about 90 hectares<sup><a href='#src-what-1'>1</a></sup><sup><a href='#src-what-3'>3</a></sup>",
    },
  ],
  scale: {
    caption: "Areas are proportional to electrical power.",
    items: [
      { mw: 3, mwLabel: "a few MW", label: "classic data center" },
      { mw: 150, mwLabel: "150 MW", label: "large project ≈ Le Mans" },
      { mw: 1400, mwLabel: "1,400 MW", label: "mega-project (Fouju)" },
    ],
  },
  statsParagraph:
    "Today, data centers account for about 2% of the electricity consumed in France; RTE expects about 4% by 2035<sup><a href='#src-what-1'>1</a></sup>. Worldwide, they used about 1.5% of electricity in 2024<sup><a href='#src-what-4'>4</a></sup>.",
  takeaway:
    "The same word covers a room of a few megawatts and a campus a thousand times more powerful. Facing a project, the first question is always: how many megawatts?",
  sourcesLabel: "Sources:",
  sources: [
    { label: "RTE, “Data centers in key figures”, 2026", url: "https://www.rte-france.com/bases-electricite/consommation-electricite/essor-data-centers-france" },
    { label: "Journal du Grand Paris, 2025", url: "https://www.lejournaldugrandparis.fr/choose-france-un-campus-dia-geant-en-seine-et-marne/" },
    { label: "Campus IA public consultation", url: "https://www.concertation-campus-ia.fr/fr/comprendre-le-projet" },
    { label: "IEA, Energy and AI, 2025", url: "https://www.iea.org/reports/energy-and-ai/executive-summary" },
  ],
};

// ── NÉERLANDAIS — rédigé après la passe native ; chiffres identiques au FR vérifié.
// Ancres de sources sur l'ancre NL du bloc (#src-wat-N).
export const WHATIS_NL: WhatIsDC = {
  paragraphs: [
    "Een datacenter is een industrieel gebouw vol servers — de computers die websites, video's, onlinediensten en, steeds vaker, kunstmatige intelligentie laten draaien. Die machines draaien dag en nacht, verbruiken continu elektriciteit en geven warmte af die moet worden afgevoerd. Daar komt hun energiebehoefte vandaan — en, afhankelijk van de koeltechniek, hun waterbehoefte.",
    "Om een datacenter te meten is de juiste eenheid niet de oppervlakte van het gebouw maar het <strong>elektrische vermogen, in megawatt (MW)</strong> — de stroom die de site op elk moment kan afnemen.",
  ],
  sizesTitle: "Drie heel verschillende maten dragen dezelfde naam:",
  sizes: [
    {
      label: "‘Klassiek’ datacenter",
      power: "enkele MW",
      note: "De grote meerderheid van de ~300 Franse sites, aangesloten op het distributienet zoals een grote fabriek<sup><a href='#src-wat-1'>1</a></sup>",
    },
    {
      label: "Groot project",
      power: "100 tot 200 MW",
      note: "Het elektriciteitsverbruik van steden als Le Mans of Saint-Étienne<sup><a href='#src-wat-1'>1</a></sup>",
    },
    {
      label: "Megaproject",
      power: "meer dan 400 MW",
      note: "Een tiental ‘buitenmaatse’ projecten in Frankrijk; de Campus IA in Fouju mikt op 1.400 MW op ongeveer 90 hectare<sup><a href='#src-wat-1'>1</a></sup><sup><a href='#src-wat-3'>3</a></sup>",
    },
  ],
  scale: {
    caption: "De oppervlakten zijn evenredig met het elektrische vermogen.",
    items: [
      { mw: 3, mwLabel: "enkele MW", label: "klassiek datacenter" },
      { mw: 150, mwLabel: "150 MW", label: "groot project ≈ Le Mans" },
      { mw: 1400, mwLabel: "1.400 MW", label: "megaproject (Fouju)" },
    ],
  },
  statsParagraph:
    "Vandaag nemen de datacenters samen ongeveer 2% van het in Frankrijk verbruikte stroomvolume voor hun rekening; RTE verwacht ongeveer 4% in 2035<sup><a href='#src-wat-1'>1</a></sup>. Wereldwijd gebruikten ze in 2024 ongeveer 1,5% van de elektriciteit<sup><a href='#src-wat-4'>4</a></sup>.",
  takeaway:
    "Hetzelfde woord dekt een zaal van enkele megawatt en een campus die duizend keer krachtiger is. Tegenover een project is de eerste vraag altijd: hoeveel megawatt?",
  sourcesLabel: "Bronnen:",
  sources: [
    { label: "RTE, « Les data centers en chiffres clés », 2026", url: "https://www.rte-france.com/bases-electricite/consommation-electricite/essor-data-centers-france" },
    { label: "Journal du Grand Paris, 2025", url: "https://www.lejournaldugrandparis.fr/choose-france-un-campus-dia-geant-en-seine-et-marne/" },
    { label: "Publiek overleg Campus IA", url: "https://www.concertation-campus-ia.fr/fr/comprendre-le-projet" },
    { label: "IEA, Energy and AI, 2025", url: "https://www.iea.org/reports/energy-and-ai/executive-summary" },
  ],
};
