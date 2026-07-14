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
  hook: string; // one-line standfirst — lorem Latin, clearly fictional
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

export const FLAGSHIP: LibraryBrief = {
  id: "flagship-inaugural",
  family: "flagship",
  theme: null,
  cover: "Nº I",
  title: {
    fr: "État de l'acceptabilité des data centers en Europe",
    en: "State of Data Center Acceptability in Europe",
  },
  hook: "Lorem ipsum dolor sit amet, corpus integrum legitur — ubi notae crescunt, ubi decrescunt, pilari singuli.",
  date: "2026-06-01",
  priceFromEur: 1900,
  teaser: "bars",
};

export const BRIEFS: LibraryBrief[] = [
  FLAGSHIP,
  {
    id: "theme-water",
    family: "theme",
    theme: "water",
    cover: "Aqua",
    title: {
      fr: "Aqua sub pressione — lorem ipsum meridiana",
      en: "Aqua sub pressione — lorem ipsum meridiana",
    },
    hook: "Lorem ipsum dolor sit amet, aqua consectetur adipiscing elit, sed do eiusmod tempor.",
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
    id: "country-pl",
    family: "country",
    theme: null,
    country: "pl",
    cover: "PL",
    title: {
      fr: "Data centers in Polonia — lorem ipsum carbo",
      en: "Data centers in Polonia — lorem ipsum carbo",
    },
    hook: "Lorem ipsum carbo et transitio, quis nostrud exercitation ullamco laboris nisi.",
    date: "2026-02-14",
    priceFromEur: 900,
    teaser: "dots",
  },
  {
    id: "theme-energy",
    family: "theme",
    theme: "energy",
    cover: "CO₂",
    title: {
      fr: "Energia et carbo — lorem ortus et occasus",
      en: "Energia et carbo — lorem ortus et occasus",
    },
    hook: "Lorem ipsum inter orientem et occidentem discrimen carbonis dilatatur, sed do eiusmod.",
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
      fr: "Quis publicat, quis tacet — lorem ipsum",
      en: "Quis publicat, quis tacet — lorem ipsum",
    },
    hook: "Tertia pars operatorum lorem ipsum documentorum publicorum concentrat, ut labore et dolore.",
    date: "2026-02-25",
    priceFromEur: 500,
    teaser: "dots",
  },
  {
    id: "theme-land",
    family: "theme",
    theme: "land",
    cover: "Ager",
    title: {
      fr: "Ager et biodiversitas — lorem ipsum arvum",
      en: "Ager et biodiversitas — lorem ipsum arvum",
    },
    hook: "Lorem ipsum arva artificialia et solum vivum, quis nostrud exercitation ullamco.",
    date: "2026-02-02",
    priceFromEur: 500,
    teaser: "scatter",
  },
  {
    id: "theme-impact",
    family: "theme",
    theme: "impact",
    cover: "Vic.",
    title: {
      fr: "Vicinia et labor — lorem ipsum localis",
      en: "Vicinia et labor — lorem ipsum localis",
    },
    hook: "Lorem ipsum vicinia, opera localia et onera communia, duis aute irure dolor.",
    date: "2026-01-15",
    priceFromEur: 500,
    teaser: "trend",
  },
];

/** Index view: newest first (the archive is a catalogue, date is the order). */
export const BRIEFS_BY_DATE: LibraryBrief[] = [...BRIEFS].sort((a, b) =>
  b.date.localeCompare(a.date),
);
