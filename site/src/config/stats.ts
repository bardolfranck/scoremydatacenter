// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// « Les chiffres du parc » (T0) — display model over the engine's stats.json.
// The engine computes; THIS file owns every word: section titles, punch
// phrases (neutral, no national regulatory concept), source lines (the only
// place where institutions appear, resolved per country), bonus/friction
// editorial pairing. i18n §13: FR and EN live side by side, never drift.
import statsData from "../../public/data/stats.json";

export type Lang = "fr" | "en";
export const STATS = statsData as any;

/** Perimeter slugs are URL segments: "europe" or a lowercase ISO country. */
export const perimeterKeys = (): string[] => Object.keys(STATS.perimeters);

export const COUNTRY_NAMES: Record<string, { fr: string; en: string }> = {
  AT: { fr: "Autriche", en: "Austria" }, BE: { fr: "Belgique", en: "Belgium" },
  CH: { fr: "Suisse", en: "Switzerland" }, DE: { fr: "Allemagne", en: "Germany" },
  DK: { fr: "Danemark", en: "Denmark" }, ES: { fr: "Espagne", en: "Spain" },
  FI: { fr: "Finlande", en: "Finland" }, FR: { fr: "France", en: "France" },
  GB: { fr: "Royaume-Uni", en: "United Kingdom" }, IE: { fr: "Irlande", en: "Ireland" },
  IT: { fr: "Italie", en: "Italy" }, LU: { fr: "Luxembourg", en: "Luxembourg" },
  NL: { fr: "Pays-Bas", en: "Netherlands" }, NO: { fr: "Norvège", en: "Norway" },
  PL: { fr: "Pologne", en: "Poland" }, PT: { fr: "Portugal", en: "Portugal" },
  SE: { fr: "Suède", en: "Sweden" },
};

export const REGION_NAMES: Record<string, string> = {
  "ile-de-france": "Île-de-France", "hauts-de-france": "Hauts-de-France",
  "grand-est": "Grand Est", "normandie": "Normandie", "bretagne": "Bretagne",
  "pays-de-la-loire": "Pays de la Loire", "centre-val-de-loire": "Centre-Val de Loire",
  "bourgogne-franche-comte": "Bourgogne-Franche-Comté",
  "auvergne-rhone-alpes": "Auvergne-Rhône-Alpes", "nouvelle-aquitaine": "Nouvelle-Aquitaine",
  "occitanie": "Occitanie", "provence-alpes-cote-d-azur": "Provence-Alpes-Côte d'Azur",
  "corse": "Corse", "outre-mer": "Outre-mer",
};

export function perimeterLabel(key: string, lang: Lang): string {
  if (key === "europe") return "Europe";
  return COUNTRY_NAMES[key]?.[lang] ?? key;
}

/** Number formatting — whole numbers only (Franck 2026-07-16: the decimal
 * adds nothing). Sub-1% shares render "<1 %" — rounding 0.8 up to 1 would
 * overstate by a quarter. */
export const fmtPct = (pct: number, lang: Lang): string => {
  if (pct > 0 && pct < 1) return lang === "fr" ? `<1 %` : "<1%";
  const v = Math.round(pct);
  return lang === "fr" ? `${v} %` : `${v}%`;
};
export const fmtInt = (n: number, lang: Lang): string =>
  n.toLocaleString(lang === "fr" ? "fr-FR" : "en-GB");

/** Source lines — institutions live HERE, resolved per country (cadrage §4.10:
 * regulatory concepts never reach the punch phrase). `default` covers every
 * other wired country with the neutral, truthful dataset family. */
type SrcMap = { FR?: { fr: string; en: string }; default: { fr: string; en: string } };
const SOURCES: Record<string, SrcMap> = {
  grid_saturated: {
    FR: { fr: "Capacités d'accueil réseau — Caparéseau (RTE)", en: "Grid hosting capacity — Caparéseau (RTE)" },
    default: { fr: "Capacités d'accueil des gestionnaires de réseau", en: "Grid operators' hosting-capacity registers" },
  },
  grid_queue_critical: {
    FR: { fr: "Files d'attente de raccordement — Caparéseau (RTE)", en: "Connection queues — Caparéseau (RTE)" },
    default: { fr: "Files d'attente des gestionnaires de réseau", en: "Grid operators' connection queues" },
  },
  water_stress_high: {
    FR: { fr: "WRI Aqueduct 4.0 · VigiEau", en: "WRI Aqueduct 4.0 · VigiEau" },
    default: { fr: "WRI Aqueduct 4.0", en: "WRI Aqueduct 4.0" },
  },
  water_no_stress: {
    FR: { fr: "WRI Aqueduct 4.0 · VigiEau", en: "WRI Aqueduct 4.0 · VigiEau" },
    default: { fr: "WRI Aqueduct 4.0", en: "WRI Aqueduct 4.0" },
  },
  soil_artificialized: {
    FR: { fr: "Occupation des sols — IGN API Carto", en: "Land use — IGN API Carto" },
    default: { fr: "Corine Land Cover (EEA)", en: "Corine Land Cover (EEA)" },
  },
  protected_area_close: {
    FR: { fr: "Natura 2000 & ZNIEFF — INPN / IGN", en: "Natura 2000 & ZNIEFF — INPN / IGN" },
    default: { fr: "Zones protégées — EEA CDDA / Natura 2000", en: "Protected areas — EEA CDDA / Natura 2000" },
  },
  seveso_high_2km: {
    FR: { fr: "Installations classées — Géorisques", en: "Classified installations — Géorisques" },
    default: { fr: "Registres nationaux des sites industriels à risque", en: "National registers of high-hazard industrial sites" },
  },
  pue_published: { default: { fr: "Déclarations publiques des opérateurs", en: "Operators' public disclosures" } },
  heat_reuse: { default: { fr: "Déclarations publiques des opérateurs", en: "Operators' public disclosures" } },
  power_disclosed: { default: { fr: "Déclarations publiques des opérateurs", en: "Operators' public disclosures" } },
  operational_share: { default: { fr: "Corpus ScoreMyDataCenter — statut des projets", en: "ScoreMyDataCenter corpus — project status" } },
  pipeline: { default: { fr: "Corpus ScoreMyDataCenter — projets annoncés & en instruction", en: "ScoreMyDataCenter corpus — announced & permitting projects" } },
  oppositions: { default: { fr: "Couche veille — faits sourcés, jamais une note", en: "Watch layer — sourced facts, never a grade" } },
};

export function sourceLine(statId: string, countries: string[], lang: Lang): string {
  const map = SOURCES[statId];
  if (!map) return "";
  if (map.FR && countries.length === 1 && countries[0] === "FR") return map.FR[lang];
  if (map.FR && countries.includes("FR")) {
    return lang === "fr" ? `${map.default[lang]} · ${map.FR.fr} (France)` : `${map.default[lang]} · ${map.FR.en} (France)`;
  }
  return map.default[lang];
}

/** Punch phrases — {pct}/{num}/{n}/{mw}/{projects}… get substituted. Neutral
 * wording only: the constraint speaks, never a national regulatory concept. */
export const PHRASES: Record<string, { fr: string; en: string }> = {
  grid_saturated: {
    fr: "du parc est raccordé à un poste électrique déjà saturé.",
    en: "of the fleet is connected to an already-saturated substation.",
  },
  grid_queue_critical: {
    fr: "des sites font face à une file d'attente de raccordement élevée ou critique.",
    en: "of sites face a high or critical grid-connection queue.",
  },
  water_stress_high: {
    fr: "des sites sont implantés dans un bassin en stress hydrique fort ou en crise d'eau.",
    en: "of sites sit in a basin under high water stress or water crisis.",
  },
  water_no_stress: {
    fr: "des sites sont dans un bassin sans stress hydrique.",
    en: "of sites sit in a basin with no water stress.",
  },
  soil_artificialized: {
    fr: "du parc est bâti sur des sols déjà artificialisés — pas sur des terres agricoles ou naturelles.",
    en: "of the fleet is built on already-artificialized soil — not on farmland or natural land.",
  },
  protected_area_close: {
    fr: "des sites jouxtent une zone naturelle protégée, à moins d'un kilomètre.",
    en: "of sites border a protected natural area, within one kilometre.",
  },
  seveso_high_2km: {
    fr: "des sites voisinent un site industriel à haut risque, à moins de 2 km.",
    en: "of sites neighbour a high-hazard industrial site, within 2 km.",
  },
  pue_published: {
    fr: "des sites publient leur efficacité énergétique (PUE) réelle. L'efficacité annoncée ne vaut jamais preuve — publier est le premier pas.",
    en: "of sites publish their real energy efficiency (PUE). Claimed efficiency is never proof — publishing is the first step.",
  },
  heat_reuse: {
    fr: "des sites déclarent valoriser leur chaleur fatale (réseau de chaleur, équipements voisins) — le premier levier d'un bon projet.",
    en: "of sites declare recovering their waste heat (heat networks, nearby facilities) — the first lever of a good project.",
  },
  power_disclosed: {
    fr: "des sites communiquent leur puissance électrique — la donnée de base du débat public.",
    en: "of sites disclose their electrical capacity — the basic figure of any public debate.",
  },
  operational_share: {
    fr: "du parc suivi est déjà en service — nous mesurons l'existant, pas seulement les promesses.",
    en: "of the tracked fleet is already operating — we measure what exists, not only what is promised.",
  },
  pipeline: {
    fr: "annoncés dans les projets pas encore en service ({projects} projets — {undisclosed} ne communiquent pas leur puissance).",
    en: "announced across projects not yet in service ({projects} projects — {undisclosed} do not disclose their capacity).",
  },
  oppositions: {
    fr: "projets sous opposition citoyenne ou moratoire — recensés et sourcés, jamais notés sur cette base.",
    en: "projects under citizen opposition or moratorium — recorded and sourced, never graded on that basis.",
  },
};

/** Page structure — four question-sections, each pairing at least one
 * flattering stat with one uncomfortable one (the neutrality signature). */
export const SECTIONS: { id: string; lead: string; stats: string[] }[] = [
  { id: "territoire", lead: "grid_saturated", stats: ["grid_saturated", "soil_artificialized", "water_stress_high", "grid_queue_critical", "protected_area_close", "seveso_high_2km"] },
  { id: "transparence", lead: "pue_published", stats: ["pue_published", "power_disclosed", "heat_reuse"] },
  { id: "dynamique", lead: "pipeline", stats: ["pipeline", "operational_share", "oppositions"] },
];

/** Editorial tone — the colour of the proportion bar (green/orange/blue),
 * never a label: the neutrality signature stays visual (Franck 2026-07-16).
 * `inverse` marks shares whose NUMERATOR is the virtue: their friction
 * intensity is 100−pct (0.8 % publishing PUE = a 99.2-strong friction). */
export const STAT_TONE: Record<string, { tone: "good" | "bad" | "neutral"; inverse?: boolean }> = {
  soil_artificialized: { tone: "good" }, water_no_stress: { tone: "good" },
  power_disclosed: { tone: "good" }, operational_share: { tone: "good" },
  grid_saturated: { tone: "bad" }, grid_queue_critical: { tone: "bad" },
  water_stress_high: { tone: "bad" }, protected_area_close: { tone: "bad" },
  seveso_high_2km: { tone: "bad" },
  pue_published: { tone: "bad", inverse: true }, heat_reuse: { tone: "bad", inverse: true },
  pipeline: { tone: "neutral" }, oppositions: { tone: "neutral" },
};

/** Story fragments — written ONCE per stat (like the punch phrases), then the
 * section phrase is COMPOSED at build: strongest published bonus + strongest
 * friction, "X — mais Y." Deterministic, per perimeter, per language. */
export const FRAGMENTS: Record<string, { up?: { fr: string; en: string }; down?: { fr: string; en: string } }> = {
  soil_artificialized: { up: { fr: "le parc s'est construit sur des sols déjà pris", en: "the fleet was built on land already taken" } },
  water_no_stress: { up: { fr: "la plupart des sites échappent au stress hydrique", en: "most sites escape water stress" } },
  power_disclosed: { up: { fr: "les opérateurs disent leur puissance", en: "operators disclose their capacity" } },
  operational_share: { up: { fr: "le parc suivi tourne déjà", en: "the tracked fleet is already running" } },
  grid_saturated: { down: { fr: "il s'est branché sur un réseau qui n'a plus de place", en: "it plugged into a grid with no room left" } },
  grid_queue_critical: { down: { fr: "les files d'attente de raccordement s'allongent", en: "connection queues keep growing" } },
  water_stress_high: { down: { fr: "une partie du parc puise dans des bassins déjà sous tension", en: "part of the fleet draws from basins already under stress" } },
  protected_area_close: { down: { fr: "beaucoup jouxtent des espaces naturels protégés", en: "many border protected natural areas" } },
  seveso_high_2km: { down: { fr: "certains voisinent des sites industriels à haut risque", en: "some neighbour high-hazard industrial sites" } },
  pue_published: { down: { fr: "presque aucun ne prouve ses performances", en: "almost none proves its performance" } },
  heat_reuse: { down: { fr: "la chaleur part en l'air presque partout", en: "the heat is wasted almost everywhere" } },
  pipeline: { down: { fr: "ce qui s'annonce ne dit pas toujours sa puissance", en: "what's coming doesn't always state its capacity" } },
};

const _esc = (x: string) => x.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/** Composed section phrase — HTML with .up/.down spans, or null when the
 * perimeter publishes neither side. Rule: among the section's published
 * stats, strongest bonus (max pct) + strongest friction (max pct, or
 * 100−pct for `inverse` shares; a pipeline with silent projects counts). */
export function composeStory(peri: any, sectionId: string, lang: Lang): string | null {
  const sec = SECTIONS.find((s) => s.id === sectionId);
  if (!sec) return null;
  let bonus: { id: string; score: number } | null = null;
  let friction: { id: string; score: number } | null = null;
  for (const id of sec.stats) {
    const view = statView(peri, id, lang);
    if (!view) continue;
    const meta = STAT_TONE[id];
    if (meta.tone === "good" && FRAGMENTS[id]?.up) {
      const score = view.pct ?? 0;
      if (!bonus || score > bonus.score) bonus = { id, score };
    } else if (meta.tone === "bad" && FRAGMENTS[id]?.down) {
      const score = meta.inverse ? 100 - (view.pct ?? 0) : (view.pct ?? 0);
      if (!friction || score > friction.score) friction = { id, score };
    } else if (id === "pipeline" && FRAGMENTS.pipeline?.down) {
      const p = peri.stats?.pipeline;
      if (p && p.mw_undisclosed_n > 0 && !friction) friction = { id, score: 0 };
    }
  }
  const up = bonus ? _esc(FRAGMENTS[bonus.id].up![lang]) : null;
  const down = friction ? _esc(FRAGMENTS[friction.id].down![lang]) : null;
  const cap = (x: string) => x.charAt(0).toUpperCase() + x.slice(1);
  const joiner = lang === "fr" ? " — mais " : " — but ";
  if (up && down) return `<span class="up">${cap(up)}</span>${joiner}<span class="down">${down}</span>.`;
  if (up) return `<span class="up">${cap(up)}</span>.`;
  if (down) return `<span class="down">${cap(down)}</span>.`;
  return null;
}

/** LE chiffre — the single huge number on top; first available wins. */
export const HERO_PRIORITY = ["grid_saturated", "water_stress_high", "soil_artificialized", "power_disclosed"];

export const T = {
  fr: {
    pageTitle: "Les chiffres du parc — ScoreMyDataCenter",
    metaDescription:
      "Ce que disent les données publiques des data centers, agrégées site par site : réseau, eau, sols, transparence, dynamique. Chaque chiffre est daté, sourcé et recalculable.",
    tagline: "Observatoire indépendant",
    h1: "Les chiffres du parc",
    lede: "Ce que disent les données publiques des data centers, agrégées site par site. Chaque chiffre est daté, sourcé et recalculable.",
    editionOf: "Édition du",
    perimeter: "Périmètre",
    perimeterSelectAria: "Changer de périmètre",
    dcWord: "data centers",
    countriesWord: (n: number) => (n > 1 ? `${n} pays` : "1 pays"),
    methodo: "méthodologie",
    heroKicker: "Le chiffre de l'édition",
    copyLink: "Copier le lien",
    copied: "Lien copié ✓",
    sections: {
      territoire: { title: "Le territoire", sub: "là où les data centers s'installent" },
      transparence: { title: "La transparence", sub: "ce que les opérateurs rendent public — ou pas" },
      dynamique: { title: "La dynamique", sub: "ce qui arrive : projets, puissances, oppositions" },
      methode: { title: "La méthode, en chiffres", sub: "d'où viennent ces nombres" },
    },
    regionAll: "France entière",
    moreLabel: (n: number) => `Tous les chiffres (${n} de plus)`,
    methodStory: '<span class="up">Aucun chiffre de cette page n\'est déclaratif : tout est recalculé site par site</span> — et quand la donnée manque, <span class="down">le chiffre le dit</span>.',
    regionAria: "Filtrer le territoire par région",
    regionGated: (n: number) => `n insuffisant dans ce périmètre (n=${n}) — pas de pourcentage sur si peu de sites`,
    franceOnly: "France seulement",
    countriesOn: (agg: number, total: number) => (agg < total ? `${agg} pays sur ${total}` : `${agg} pays`),
    nLabel: "n =",
    excludedNote: (n: number) => `${n} site${n > 1 ? "s" : ""} sans donnée publiée — exclu${n > 1 ? "s" : ""} et comptés à part`,
    method: {
      corpus: (n: number, c: number) => `data centers analysés un par un, dans ${c} pays. Aucun échantillonnage : le corpus entier, site par site.`,
      coverage: "de couverture moyenne des indicateurs — quand la donnée manque, le chiffre le dit au lieu de l'inventer.",
      open: "recalculable : données, grille et moteur sont ouverts. Chacun peut refaire chaque chiffre.",
      openSrc: "Moteur AGPL · méthode CC BY-SA · git clone && make score",
      corpusSrc: (v: string, d: string) => `Corpus v${v}${d ? ` · données au ${d}` : ""}`,
      coverageSrc: "Bases publiques croisées site par site",
    },
    ogAlt: "Le chiffre, en carte partageable",
  },
  en: {
    pageTitle: "Fleet figures — ScoreMyDataCenter",
    metaDescription:
      "What public data says about data centers, aggregated site by site: grid, water, soil, transparency, momentum. Every figure is dated, sourced and recomputable.",
    tagline: "Independent observatory",
    h1: "Fleet figures",
    lede: "What public data says about data centers, aggregated site by site. Every figure is dated, sourced and recomputable.",
    editionOf: "Edition of",
    perimeter: "Perimeter",
    perimeterSelectAria: "Change perimeter",
    dcWord: "data centers",
    countriesWord: (n: number) => (n > 1 ? `${n} countries` : "1 country"),
    methodo: "methodology",
    heroKicker: "The figure of this edition",
    copyLink: "Copy link",
    copied: "Link copied ✓",
    sections: {
      territoire: { title: "The territory", sub: "where data centers settle" },
      transparence: { title: "Transparency", sub: "what operators make public — or don't" },
      dynamique: { title: "Momentum", sub: "what's coming: projects, capacity, opposition" },
      methode: { title: "The method, in figures", sub: "where these numbers come from" },
    },
    regionAll: "All of France",
    moreLabel: (n: number) => `All the figures (${n} more)`,
    methodStory: '<span class="up">Nothing on this page is declarative: everything is recomputed site by site</span> — and when data is missing, <span class="down">the figure says so</span>.',
    regionAria: "Filter the territory by region",
    regionGated: (n: number) => `not enough sites in this perimeter (n=${n}) — no percentage on so few sites`,
    franceOnly: "France only",
    countriesOn: (agg: number, total: number) => (agg < total ? `${agg} of ${total} countries` : `${agg} countries`),
    nLabel: "n =",
    excludedNote: (n: number) => `${n} site${n > 1 ? "s" : ""} with no published value — excluded and counted apart`,
    method: {
      corpus: (n: number, c: number) => `data centers analysed one by one, across ${c} countries. No sampling: the whole corpus, site by site.`,
      coverage: "average indicator coverage — when data is missing, the figure says so instead of inventing it.",
      open: "recomputable: data, grid and engine are open. Anyone can redo every figure.",
      openSrc: "AGPL engine · CC BY-SA method · git clone && make score",
      corpusSrc: (v: string, d: string) => `Corpus v${v}${d ? ` · data as of ${d}` : ""}`,
      coverageSrc: "Public datasets crossed site by site",
    },
    ogAlt: "This figure as a shareable card",
  },
};

/** The stat ids a perimeter can actually display (post-gate), in page order. */
export function displayableStats(peri: any): string[] {
  const out: string[] = [];
  for (const sec of SECTIONS) for (const id of sec.stats) {
    if (id === "operational_share") { if (peri.n_sites >= 10) out.push(id); }
    else if (peri.stats[id]) out.push(id);
  }
  return out;
}

/** Resolve one stat to its display payload (big number + phrase pieces). */
export function statView(peri: any, id: string, lang: Lang) {
  const t = T[lang];
  if (id === "operational_share") {
    const op = peri.by_status?.operational ?? 0;
    const pct = peri.n_sites ? Math.round((1000 * op) / peri.n_sites) / 10 : 0;
    return {
      big: fmtPct(pct, lang), pct, phrase: PHRASES[id][lang],
      n: peri.n_sites, countries: peri.countries, excluded: 0,
      src: sourceLine(id, peri.countries, lang),
    };
  }
  const s = peri.stats[id];
  if (!s) return null;
  if (s.kind === "share") {
    const excluded = Object.values(s.excluded as Record<string, number>).reduce((a: number, b: number) => a + b, 0);
    return {
      big: fmtPct(s.pct, lang), pct: s.pct, phrase: PHRASES[id][lang],
      n: s.n, countries: s.countries, excluded,
      src: sourceLine(id, s.countries, lang),
    };
  }
  if (s.kind === "pipeline") {
    return {
      big: `${fmtInt(s.mw_announced, lang)} MW`,
      phrase: PHRASES[id][lang]
        .replace("{projects}", String(s.projects))
        .replace("{undisclosed}", String(s.mw_undisclosed_n)),
      n: s.projects, pct: undefined, countries: s.countries, excluded: 0,
      src: sourceLine(id, s.countries, lang),
    };
  }
  if (s.kind === "watchlist") {
    return {
      big: fmtInt(s.entries, lang), pct: undefined, phrase: PHRASES[id][lang],
      n: s.entries, countries: s.countries, excluded: 0,
      src: sourceLine(id, s.countries, lang),
    };
  }
  return null;
}
