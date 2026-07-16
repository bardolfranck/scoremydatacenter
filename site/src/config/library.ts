// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Intelligence Library — MOCKUP data (brief COWORK 2026-07-14).
// Every entry is deliberately FICTIONAL: titles and hooks are lorem-Latin so the
// placeholder nature is visible at a glance. Nothing here is written content —
// the mockup freezes the FORM only. No real brief exists yet (library gate:
// no storefront ships until a real brief + free digest stand behind it).

export type BriefFamily = "flagship" | "country" | "theme";
export type BriefTheme = "water" | "energy" | "land" | "impact" | "transparency";
export type BriefTeaser = "trend" | "bars" | "dots" | "scatter";

export interface LibraryBrief {
  id: string;
  family: BriefFamily;
  theme: BriefTheme | null; // themed briefs only — null for flagship/country
  /** ISO country code — country briefs only, drives the native-language rule. */
  country?: string;
  /** Cover chip — short label printed on the cover field. */
  cover: string;
  /** {fr,en} only for the flagship (real product name = structure, not content);
   *  every other title is placeholder Latin, identical in both languages. */
  title: { fr: string; en: string };
  hook: string | { fr: string; en: string }; // standfirst — per-language when real copy exists
  date: string; // fictional ISO date, drives the Index sort
  priceFromEur: number | null; // fictional; null = bespoke, on request only
  teaser: BriefTeaser;
}

// Cover fields (draft-5 micro-tokens 1h): derived from pillar accents, darkened
// for print. NEVER a grade colour — A–E only ever appears as a real score badge.
export const COVER_FIELDS: Record<string, string> = {
  flagship: "#102a43",
  country: "#33465f",
  water: "#1a5e77",
  energy: "#8a5a12",
  land: "#35692f",
  impact: "#6e4636",
  transparency: "#3e4c6b",
};

export const coverField = (b: LibraryBrief): string =>
  COVER_FIELDS[b.theme ?? b.family];

// Language rule (intelligence-library.md §5): EN is systematic (the sector's
// working language); a country brief ships NATIVE + EN (localisation is an
// acquisition investment, not a traction reward); FR is home market + the
// pan-EU flagship only — never bolted onto every country edition.
const COUNTRY_NATIVE_LANGS: Record<string, string[]> = {
  fr: ["fr"],
  be: ["fr", "nl"],
  nl: ["nl"],
  lu: ["fr", "de"],
  de: ["de"],
  pl: ["pl"],
  ie: ["en"], // native English — the edge case: a single-language edition
  gb: ["en"],
  se: ["sv"],
  fi: ["fi"],
  no: ["no"],
  es: ["es"],
  it: ["it"],
};

/** Language code → flag emoji (same register as the header's 🇬🇧/🇫🇷 switch). */
export const LANG_FLAGS: Record<string, string> = {
  fr: "🇫🇷",
  en: "🇬🇧",
  nl: "🇳🇱",
  de: "🇩🇪",
  pl: "🇵🇱",
  sv: "🇸🇪",
  fi: "🇫🇮",
  no: "🇳🇴",
  es: "🇪🇸",
  it: "🇮🇹",
};

/** Publication languages of a brief, native first, EN always present. */
export const briefLanguages = (b: LibraryBrief): string[] => {
  if (b.family === "flagship") return ["en", "fr"];
  if (b.family === "country" && b.country) {
    const native = COUNTRY_NATIVE_LANGS[b.country] ?? [];
    return [...new Set([...native, "en"])];
  }
  return ["en"];
};

export const hookText = (hook: LibraryBrief["hook"], lang: "fr" | "en"): string =>
  typeof hook === "string" ? hook : hook[lang];

export const FLAGSHIP: LibraryBrief = {
  id: "flagship-inaugural",
  family: "flagship",
  theme: null,
  cover: "Nº I",
  title: {
    fr: "État de l'acceptabilité des data centers en Europe",
    en: "State of Data Center Acceptability in Europe",
  },
  hook: {
    fr: "Où l'acceptabilité monte, où elle se dégrade — et pourquoi. La lecture de référence avant d'implanter, d'investir ou de débattre.",
    en: "Where acceptability rises, where it erodes — and why. The reference read before you site, invest or debate.",
  },
  date: "2026-06-01",
  priceFromEur: null, // price to be set later (Franck, 2026-07-16)
  teaser: "bars",
};

export const BRIEFS: LibraryBrief[] = [
  FLAGSHIP,
  {
    id: "theme-water",
    family: "theme",
    theme: "water",
    cover: "H₂O",
    title: {
      fr: "Eau — la ressource qui fait ou défait un projet",
      en: "Water — the resource that makes or breaks a project",
    },
    hook: {
      fr: "Refroidissement, prélèvements, bassins déjà sous tension : les questions à poser avant qu'un data center n'ouvre le robinet.",
      en: "Cooling, withdrawals, basins already under stress: the questions to ask before a data center turns on the tap.",
    },
    date: "2026-05-12",
    priceFromEur: 500,
    teaser: "trend",
  },
  {
    id: "country-nl",
    family: "country",
    theme: null,
    country: "nl",
    cover: "NL",
    title: {
      fr: "Data centers in Batavia — lorem ipsum retis",
      en: "Data centers in Batavia — lorem ipsum retis",
    },
    hook: "Consectetur retis capacitas, ager rusticus, moratoria: lorem ipsum sub tensione.",
    date: "2026-04-20",
    priceFromEur: 900,
    teaser: "scatter",
  },
  {
    id: "country-de",
    family: "country",
    theme: null,
    country: "de",
    cover: "DE",
    title: {
      fr: "Data centers in Germania — lorem ipsum industria",
      en: "Data centers in Germania — lorem ipsum industria",
    },
    hook: "Lorem ipsum industria et retis onus, sed do eiusmod tempor incididunt ut labore.",
    date: "2026-03-30",
    priceFromEur: 900,
    teaser: "bars",
  },
  {
    id: "country-fr",
    family: "country",
    theme: null,
    country: "fr",
    cover: "FR",
    title: {
      fr: "Data centers in Gallia — lorem ipsum patria",
      en: "Data centers in Gallia — lorem ipsum patria",
    },
    hook: "Lorem ipsum patria, retis nuclearis et arva magna, sed ut perspiciatis unde omnis.",
    date: "2026-05-28",
    priceFromEur: 900,
    teaser: "bars",
  },
  {
    id: "country-ie",
    family: "country",
    theme: null,
    country: "ie",
    cover: "IE",
    title: {
      fr: "Data centers in Hibernia — lorem ipsum insula",
      en: "Data centers in Hibernia — lorem ipsum insula",
    },
    hook: "Lorem ipsum insula, retis saturatio et quaestio publica, ut enim ad minim veniam.",
    date: "2026-04-05",
    priceFromEur: 900,
    teaser: "trend",
  },
  {
    id: "theme-energy",
    family: "theme",
    theme: "energy",
    cover: "CO₂",
    title: {
      fr: "Énergie — ce que le réseau peut encore absorber",
      en: "Energy — what the grid can still absorb",
    },
    hook: {
      fr: "Raccordements sous tension, mix carboné, promesses d'énergie verte : comment lire la crédibilité énergétique d'un projet avant qu'il ne se branche.",
      en: "Strained grid connections, carbon in the mix, green-power promises: how to read a project's energy credibility before it plugs in.",
    },
    date: "2026-03-18",
    priceFromEur: 500,
    teaser: "bars",
  },
  {
    id: "theme-transparency",
    family: "theme",
    theme: "transparency",
    cover: "Doc.",
    title: {
      fr: "Transparence — qui publie, qui se tait",
      en: "Transparency — who publishes, who stays silent",
    },
    hook: {
      fr: "Dossiers accessibles ou opacité organisée : la transparence d'un opérateur s'observe pièce par pièce — et elle en dit long sur le reste.",
      en: "Accessible files or organised opacity: an operator's transparency shows document by document — and it says a lot about everything else.",
    },
    date: "2026-02-25",
    priceFromEur: 500,
    teaser: "dots",
  },
  {
    id: "theme-land",
    family: "theme",
    theme: "land",
    cover: "Ha",
    title: {
      fr: "Foncier & biodiversité — bâtir sans artificialiser",
      en: "Land & biodiversity — building without sealing soil",
    },
    hook: {
      fr: "Friche industrielle ou terre vivante ? Ce que l'emprise au sol d'un projet révèle de son acceptabilité — bien avant l'enquête publique.",
      en: "Brownfield or living land? What a project's ground footprint reveals about its acceptability — long before the public inquiry.",
    },
    date: "2026-02-02",
    priceFromEur: 500,
    teaser: "scatter",
  },
  {
    id: "theme-impact",
    family: "theme",
    theme: "impact",
    cover: "Local",
    title: {
      fr: "Impact local — voisins, emplois, contreparties",
      en: "Local impact — neighbours, jobs, trade-offs",
    },
    hook: {
      fr: "Chaleur récupérée, retombées locales, nuisances : ce qu'un territoire gagne — ou subit — quand un data center s'installe.",
      en: "Recovered heat, local benefits, nuisance: what a territory gains — or endures — when a data center moves in.",
    },
    date: "2026-01-15",
    priceFromEur: 500,
    teaser: "trend",
  },
];

/** Index view: newest first (the archive is a catalogue, date is the order). */
export const BRIEFS_BY_DATE: LibraryBrief[] = [...BRIEFS].sort((a, b) =>
  b.date.localeCompare(a.date),
);

/** Revue summary — theme cards in the site's pillar order (fiche DC order). */
export const THEME_ORDER: BriefTheme[] = ["energy", "water", "land", "impact", "transparency"];
export const THEME_BRIEFS: LibraryBrief[] = THEME_ORDER
  .map((th) => BRIEFS.find((b) => b.theme === th))
  .filter((b): b is LibraryBrief => Boolean(b));
/** Country cards — home market first, then the sector's main markets. */
const COUNTRY_ORDER = ["fr", "nl", "de", "ie"];
export const COUNTRY_BRIEFS: LibraryBrief[] = COUNTRY_ORDER
  .map((c) => BRIEFS.find((b) => b.family === "country" && b.country === c))
  .filter((b): b is LibraryBrief => Boolean(b));

/** Country flags (not language flags — 🇮🇪 vs the 🇬🇧 of English). */
export const COUNTRY_FLAGS: Record<string, string> = {
  fr: "🇫🇷", be: "🇧🇪", nl: "🇳🇱", lu: "🇱🇺", de: "🇩🇪", pl: "🇵🇱", ie: "🇮🇪",
  gb: "🇬🇧", se: "🇸🇪", fi: "🇫🇮", no: "🇳🇴", es: "🇪🇸", it: "🇮🇹",
};

/** Corpus countries with no dedicated brief yet — shown as a "coming soon" flag strip. */
export const COMING_SOON_COUNTRIES: string[] = ["pl", "be", "lu", "gb", "es", "it", "se", "fi", "no"];
