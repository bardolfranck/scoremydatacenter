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

/** « Ce que cela signifie » — one fixed meaning line per stat (mockup v3):
 * the consequence, never a judgment. Written once, like the punch phrases. */
export const MEANINGS: Record<string, { fr: string; en: string }> = {
  grid_saturated: {
    fr: "Les nouveaux raccordements peuvent devenir plus longs, plus coûteux ou plus incertains.",
    en: "New grid connections can become longer, costlier or more uncertain.",
  },
  grid_queue_critical: {
    fr: "La file d'attente devient un paramètre de calendrier à part entière.",
    en: "The connection queue becomes a schedule parameter in its own right.",
  },
  water_stress_high: {
    fr: "Le choix du refroidissement devient une question territoriale, pas seulement technique.",
    en: "Cooling choices become a territorial question, not only a technical one.",
  },
  water_no_stress: {
    fr: "Là où l'eau ne manque pas, le débat se déplace vers le réseau et les sols.",
    en: "Where water is not scarce, the debate shifts to grid and land.",
  },
  soil_artificialized: {
    fr: "Le parc se développe surtout sur des espaces déjà transformés — tous les nouveaux projets ne suivent pas cette logique.",
    en: "The fleet grows mostly on already-transformed land — not every new project follows that logic.",
  },
  protected_area_close: {
    fr: "La proximité d'un espace protégé pèse sur l'instruction et sur l'acceptation locale.",
    en: "Proximity to a protected area weighs on permitting and local acceptance.",
  },
  seveso_high_2km: {
    fr: "Le voisinage industriel s'ajoute au dossier — rarement en sa faveur.",
    en: "Industrial neighbours add to the file — rarely in its favour.",
  },
  power_disclosed: {
    fr: "La donnée de base du débat public est le plus souvent disponible.",
    en: "The basic figure of any public debate is usually available.",
  },
  pue_published: {
    fr: "L'efficacité annoncée ne vaut jamais preuve — publier est le premier pas.",
    en: "Claimed efficiency is never proof — publishing is the first step.",
  },
  heat_reuse: {
    fr: "Entre intention et mise en œuvre, l'écart reste immense.",
    en: "Between intention and implementation, the gap remains huge.",
  },
  operational_share: {
    fr: "Nous mesurons d'abord l'existant, pas seulement les promesses.",
    en: "We measure what exists first, not only what is promised.",
  },
  pipeline: {
    fr: "", en: "",
  },
  oppositions: {
    fr: "Des faits sourcés, jamais une note — un contexte.",
    en: "Sourced facts, never a grade — context.",
  },
};

/** Hero meaning — the one-line reading under the edition figure. */
export const HERO_MEANING: Record<string, { fr: string; en: string }> = {
  grid_saturated: {
    fr: "Le parc existe. Le réseau, lui, manque déjà de marge.",
    en: "The fleet is here. The grid already lacks headroom.",
  },
  water_stress_high: {
    fr: "Le parc existe. L'eau, elle, est déjà sous tension.",
    en: "The fleet is here. The water is already under stress.",
  },
  soil_artificialized: {
    fr: "Le parc s'est construit sur des espaces déjà transformés.",
    en: "The fleet was built on already-transformed land.",
  },
  power_disclosed: {
    fr: "La donnée de base du débat est le plus souvent disponible.",
    en: "The basic figure of the debate is usually available.",
  },
};

/** Card icons — Phosphor name + tint family (mockup v3.1: the tint follows
 * the SUBJECT family; bonus/friction stays on the bar). */
export const STAT_ICON: Record<string, { icon: string; tint: string }> = {
  grid_saturated: { icon: "lightning", tint: "blue" },
  grid_queue_critical: { icon: "hourglass", tint: "blue" },
  water_stress_high: { icon: "drop", tint: "cyan" },
  water_no_stress: { icon: "drop", tint: "cyan" },
  soil_artificialized: { icon: "leaf", tint: "green" },
  protected_area_close: { icon: "plant", tint: "green" },
  seveso_high_2km: { icon: "warning", tint: "orange" },
  power_disclosed: { icon: "file-text", tint: "blue" },
  pue_published: { icon: "gauge", tint: "orange" },
  heat_reuse: { icon: "flame", tint: "purple" },
  operational_share: { icon: "hard-drives", tint: "green" },
  pipeline: { icon: "chart-bar", tint: "blue" },
  oppositions: { icon: "warning", tint: "orange" },
};

/** Act 4 — descriptive constraint ranking: share of sites concerned,
 * recomputed per perimeter (`invert` reads the friction as 100−pct). */
export const RANK_SPEC: { id: string; invert?: boolean; label: { fr: string; en: string }; phrase: { fr: string; en: string } }[] = [
  { id: "pue_published", invert: true, label: { fr: "Transparence", en: "Transparency" },
    phrase: { fr: "des sites ne publient pas leur efficacité réelle.", en: "of sites do not publish their real efficiency." } },
  { id: "grid_saturated", label: { fr: "Réseau électrique", en: "Power grid" },
    phrase: { fr: "des sites proches d'un poste saturé.", en: "of sites near a saturated substation." } },
  { id: "water_stress_high", label: { fr: "Eau", en: "Water" },
    phrase: { fr: "des sites en zone de stress hydrique fort.", en: "of sites in high water-stress areas." } },
  { id: "protected_area_close", label: { fr: "Zones protégées", en: "Protected areas" },
    phrase: { fr: "des sites à moins d'1 km d'un espace naturel protégé.", en: "of sites within 1 km of a protected natural area." } },
  { id: "seveso_high_2km", label: { fr: "Sites à risque", en: "High-hazard sites" },
    phrase: { fr: "des sites à moins de 2 km d'un site industriel à haut risque.", en: "of sites within 2 km of a high-hazard industrial site." } },
];

export function rankConstraints(peri: any, lang: Lang) {
  return RANK_SPEC
    .map((spec) => {
      const st = peri.stats?.[spec.id];
      if (!st || st.kind !== "share") return null;
      const share = spec.invert ? Math.round(10 * (100 - st.pct)) / 10 : st.pct;
      return { id: spec.id, label: spec.label[lang], phrase: spec.phrase[lang], share, n: st.n };
    })
    .filter(Boolean)
    .sort((a: any, b: any) => b.share - a.share);
}

/** Act 5 — exemplar cards: fixed copy + data-driven bullets. */
export const EXEMPLAR_COPY = {
  fr: {
    title: "Trois projets qui racontent ce territoire",
    sub: "Sélection mécanique et publiée — le profil le plus courant, le plus contraint, le mieux documenté. Des situations réelles derrière les agrégats.",
    why: { representative: "Le profil le plus courant", constrained: "Le plus contraint", documented: "Le mieux documenté" },
    crit: {
      representative: "critère : profil modal du territoire (statut, réseau, sols, note la plus fréquente)",
      constrained: "critère : plus grand cumul de frictions territoriales du périmètre",
      documented: "critère : score de confiance documentaire maximal",
    },
    fiche: "Voir la fiche →",
    status: { announced: "Annoncé", permitting: "En instruction", under_construction: "En construction", operational: "En service" },
    mwUnknown: "puissance non communiquée",
    frictionsLine: (n: number) => `${n} contrainte${n > 1 ? "s" : ""} territoriale${n > 1 ? "s" : ""} cumulée${n > 1 ? "s" : ""}`,
    confLine: { high: "Confiance documentaire : haute", medium: "Confiance documentaire : moyenne", low: "Confiance documentaire : faible" },
    facts: {
      e2: "Raccordé à un poste déjà saturé", w1: "En zone de stress hydrique fort",
      f2: "Sur des sols déjà artificialisés", f1: "À moins d'1 km d'un espace protégé", l3: "Site à haut risque à moins de 2 km",
    },
  },
  en: {
    title: "Three projects that tell this territory",
    sub: "A mechanical, published selection — the most common profile, the most constrained, the best documented. Real situations behind the aggregates.",
    why: { representative: "The most common profile", constrained: "The most constrained", documented: "The best documented" },
    crit: {
      representative: "criterion: the territory's modal profile (status, grid, soil, most frequent grade)",
      constrained: "criterion: highest cumulated territorial frictions in the perimeter",
      documented: "criterion: highest documentary-confidence score",
    },
    fiche: "View the fiche →",
    status: { announced: "Announced", permitting: "Permitting", under_construction: "Under construction", operational: "Operational" },
    mwUnknown: "capacity not disclosed",
    frictionsLine: (n: number) => `${n} cumulated territorial constraint${n > 1 ? "s" : ""}`,
    confLine: { high: "Documentary confidence: high", medium: "Documentary confidence: medium", low: "Documentary confidence: low" },
    facts: {
      e2: "Connected to an already-saturated substation", w1: "In a high water-stress area",
      f2: "On already-artificialized soil", f1: "Within 1 km of a protected area", l3: "High-hazard site within 2 km",
    },
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
    v3: {
      q: {
        territoire: "Peut-on encore construire ici ?",
        transparence: "Que sait-on vraiment des projets ?",
        dynamique: "Où va le parc ?",
        tension: "Qu'est-ce qui pèse le plus ici ?",
        methode: "Comment lire ces chiffres ?",
      },
      looking: "Vous regardez",
      allRegions: "Toutes les régions",
      seeSelection: "Voir cette sélection",
      heroKicker: "Le chiffre de l'édition — sur le territoire sélectionné",
      disclaim: "Ce n'est pas un classement. C'est la photographie d'un territoire : ce qu'il accueille déjà, ce qu'il peut encore absorber, et ce que les dossiers publics permettent réellement de savoir.",
      copyView: "⧉ Copier le lien de cette vue",
      meaningLabel: "Ce que cela signifie",
      mapCap: "Sites du corpus — en orange, ceux raccordés à un poste saturé. Calculé depuis les coordonnées, jamais une illustration.",
      mapCta: "Explorer la carte →",
      projWord: (n: number) => `${n} projet${n > 1 ? "s" : ""} à venir`,
      editionShort: "édition du",
      compare: {
        title: "Annoncer n'est pas mesurer.",
        colPub: "Ce qui est souvent publié", colMiss: "Ce qui manque encore",
        rows: [["Puissance prévue", "Consommation réelle"], ["PUE annoncé", "PUE mesuré"], ["Chaleur récupérable", "Chaleur effectivement utilisée"]],
        close: "Quand la donnée manque, ScoreMyDataCenter ne l'invente pas. L'absence d'information reste visible.",
        cta: "Comprendre notre approche →",
      },
      t1: {
        title: "📈 L'historique commence ici.",
        p1: (d: string) => `Ceci est la première édition (corpus au ${d}). Les évolutions — nouveaux projets, puissances, oppositions — apparaîtront ici d'édition en édition, à méthode et périmètre constants.`,
        p2: "Nous n'affichons aucune tendance que nos propres données ne portent pas encore.",
        cta: "Voir les projets à venir →",
      },
      rankSub: "Les contraintes du territoire, classées par part des sites concernés — un classement descriptif, jamais une note.",
      rankNote: "classement recalculé par périmètre : part des sites concernés par chaque contrainte",
      guarantee: {
        title: "Aucun chiffre de cette page n'est écrit à la main.",
        chips: (n: string, cov: string) => [
          [n, "sites analysés un par un"],
          [cov, "de couverture moyenne — le manque est affiché"],
          ["100 %", "recalculable (données, grille, moteur ouverts)"],
          ["1", "même méthode pour tous les territoires"],
          ["100 %", "des chiffres reliés à leurs sources"],
        ],
        line: "Les chiffres changent quand les faits changent — jamais pour arranger le récit.",
        cta: "Voir la méthode complète →",
      },
      indband: "ScoreMyDataCenter est un observatoire indépendant. Aucun financement d'opérateur. Aucune donnée propriétaire. Aucune complaisance.",
    },
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
    v3: {
      q: {
        territoire: "Can you still build here?",
        transparence: "What do we really know about the projects?",
        dynamique: "Where is the fleet heading?",
        tension: "What weighs most here?",
        methode: "How to read these figures?",
      },
      looking: "You are looking at",
      allRegions: "All regions",
      seeSelection: "View this selection",
      heroKicker: "The figure of this edition — on the selected territory",
      disclaim: "This is not a ranking. It is the photograph of a territory: what it already hosts, what it can still absorb, and what public files actually allow to know.",
      copyView: "⧉ Copy the link to this view",
      meaningLabel: "What it means",
      mapCap: "Corpus sites — in orange, those connected to a saturated substation. Computed from coordinates, never an illustration.",
      mapCta: "Explore the map →",
      projWord: (n: number) => `${n} upcoming project${n > 1 ? "s" : ""}`,
      editionShort: "edition of",
      compare: {
        title: "Announcing is not measuring.",
        colPub: "What is often published", colMiss: "What is still missing",
        rows: [["Planned capacity", "Actual consumption"], ["Announced PUE", "Measured PUE"], ["Recoverable heat", "Heat actually used"]],
        close: "When data is missing, ScoreMyDataCenter does not invent it. The absence of information stays visible.",
        cta: "Understand our approach →",
      },
      t1: {
        title: "📈 The history starts here.",
        p1: (d: string) => `This is the first edition (corpus as of ${d}). Changes — new projects, capacity, opposition — will appear here edition after edition, with constant method and perimeter.`,
        p2: "We display no trend our own data does not yet carry.",
        cta: "See upcoming projects →",
      },
      rankSub: "The territory's constraints, ranked by the share of sites concerned — a descriptive ranking, never a grade.",
      rankNote: "recomputed per perimeter: share of sites concerned by each constraint",
      guarantee: {
        title: "No figure on this page is written by hand.",
        chips: (n: string, cov: string) => [
          [n, "sites analysed one by one"],
          [cov, "average coverage — the gap is displayed"],
          ["100%", "recomputable (open data, grid and engine)"],
          ["1", "same method for every territory"],
          ["100%", "of figures linked to their sources"],
        ],
        line: "Figures change when facts change — never to fit the story.",
        cta: "See the full method →",
      },
      indband: "ScoreMyDataCenter is an independent observatory. No operator funding. No proprietary data. No complacency.",
    },
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
