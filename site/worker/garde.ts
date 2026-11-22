// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// GARDE ANTI-ASPIRATION (décision Franck 2026-11-22). Mesuré ce jour-là : la seule limite
// était celle de la zone Cloudflare, environ 5 pages par 10 s, blocage de 10 s. Une IP
// patiente aspirait les 3 516 fiches en 2 h. Franck : « rends ça prohibitif en temps », sans
// gêner un lecteur ; l'usage en volume est un usage PRO, par l'API payante.
//
// Règle, PAR IP :
//  - fiches (page, portrait, dans les 3 langues) : 20 par heure, 50 par jour ;
//  - détail d'un site via l'API de la carte (/api/carte/site, /api/veille/site) : budget À
//    PART, 60 par heure, 150 par jour — sinon un visiteur qui clique sur la carte serait
//    bloqué au 21e clic ; et sans le compter, `?t=1,2,3…` énumérait tout le corpus ;
//  - au dépassement, blocage qui DOUBLE à chaque récidive : 30 min, 1 h, 2 h, 4 h… plafond
//    7 jours ; 7 jours sans récidive remettent le compteur à zéro (une IP partagée n'est pas
//    punie à vie).
//
// Ce fichier est PUR (aucune API Cloudflare) : il se teste avec `node --test`.

export type Budget = { parHeure: number; parJour: number };
export const BUDGETS: Record<"fiche" | "carte", Budget> = {
  fiche: { parHeure: 20, parJour: 50 },
  carte: { parHeure: 60, parJour: 150 },
};

export const MINUTE = 60_000;
export const HEURE = 60 * MINUTE;
export const JOUR = 24 * HEURE;
export const BLOCAGE_INITIAL = 30 * MINUTE;
export const BLOCAGE_MAX = 7 * JOUR;
export const AMNISTIE = 7 * JOUR;

export type Etat = {
  hits: Record<string, number[]>; // horodatages des 24 dernières heures, par budget
  recidives: number;
  derniereRecidive: number;
  bloqueJusqua: number;
};

export const ETAT_VIDE: Etat = { hits: {}, recidives: 0, derniereRecidive: 0, bloqueJusqua: 0 };

export type Verdict = { ok: true; etat: Etat } | { ok: false; etat: Etat; reessayerDans: number };

/** La durée du blocage pour la n-ième récidive (n ≥ 1) : 30 min × 2^(n-1), plafonnée. */
export function dureeBlocage(n: number): number {
  return Math.min(BLOCAGE_INITIAL * 2 ** Math.max(0, n - 1), BLOCAGE_MAX);
}

/** Décide pour UNE requête comptée. Rend le nouvel état à enregistrer. */
export function decider(etat: Etat, budget: "fiche" | "carte", maintenant: number): Verdict {
  const e: Etat = {
    hits: Object.fromEntries(
      Object.entries(etat.hits || {}).map(([k, v]) => [k, v.filter((t) => maintenant - t < JOUR)]),
    ),
    recidives: etat.recidives || 0,
    derniereRecidive: etat.derniereRecidive || 0,
    bloqueJusqua: etat.bloqueJusqua || 0,
  };
  if (e.bloqueJusqua > maintenant) {
    return { ok: false, etat: e, reessayerDans: e.bloqueJusqua - maintenant };
  }
  if (e.recidives && maintenant - e.derniereRecidive > AMNISTIE) e.recidives = 0;
  const b = BUDGETS[budget];
  const jour = e.hits[budget] || [];
  const heure = jour.filter((t) => maintenant - t < HEURE).length;
  if (heure >= b.parHeure || jour.length >= b.parJour) {
    e.recidives += 1;
    e.derniereRecidive = maintenant;
    const d = dureeBlocage(e.recidives);
    e.bloqueJusqua = maintenant + d;
    return { ok: false, etat: e, reessayerDans: d };
  }
  e.hits[budget] = [...jour, maintenant];
  return { ok: true, etat: e };
}

/** Quel budget consomme cette requête (GET seulement), ou null si elle n'est pas comptée. */
export function budgetDe(method: string, pathname: string): "fiche" | "carte" | null {
  if (method !== "GET") return null;
  const p = pathname.toLowerCase();
  if (/^\/(?:fr\/|nl\/)?dc\/[^/]+\/(?:portrait\/)?$/.test(p)) return "fiche";
  if (/^\/api\/(?:carte|veille)\/site\/?$/.test(p)) return "carte";
  return null;
}

// Moteurs de recherche exemptés — le référencement en dépend. On ne croit PAS l'agent
// utilisateur seul (n'importe qui écrit « Googlebot ») : il faut soit la catégorie de robot
// vérifié de Cloudflare, soit l'agent ET le réseau (ASN) du moteur.
const MOTEURS: Array<{ ua: RegExp; asn: number[] }> = [
  { ua: /Googlebot|Google-InspectionTool|GoogleOther/i, asn: [15169, 396982] },
  { ua: /bingbot|BingPreview|msnbot/i, asn: [8075] },
];

export function moteurVerifie(ua: string, cf: { verifiedBotCategory?: string; asn?: number } | undefined): boolean {
  const cat = cf?.verifiedBotCategory || "";
  if (/search engine/i.test(cat)) return true;
  return MOTEURS.some((m) => m.ua.test(ua) && m.asn.includes(Number(cf?.asn)));
}

const MESSAGES: Record<"fr" | "en" | "nl", { titre: string; corps: string }> = {
  fr: {
    titre: "Limite de consultation atteinte",
    corps: "Vous avez consulté beaucoup de fiches en peu de temps. Pour un usage en volume (analyse de portefeuille, intégration), ScoreMyDataCenter propose un accès professionnel par API.",
  },
  en: {
    titre: "Browsing limit reached",
    corps: "You have viewed many site pages in a short time. For volume use (portfolio analysis, integration), ScoreMyDataCenter offers professional API access.",
  },
  nl: {
    titre: "Raadpleeglimiet bereikt",
    corps: "U hebt in korte tijd veel sitepagina's bekeken. Voor gebruik op grote schaal (portefeuilleanalyse, integratie) biedt ScoreMyDataCenter professionele API-toegang.",
  },
};

export function pageLimite(pathname: string, reessayerDans: number): Response {
  const lang = pathname.startsWith("/fr/") ? "fr" : pathname.startsWith("/nl/") ? "nl" : "en";
  const m = MESSAGES[lang];
  const minutes = Math.ceil(reessayerDans / MINUTE);
  const apres = { fr: `Réessayez dans ${minutes} min.`, en: `Try again in ${minutes} min.`, nl: `Probeer het over ${minutes} min opnieuw.` }[lang];
  const html = `<!doctype html><html lang="${lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${m.titre} — ScoreMyDataCenter</title><style>body{font-family:system-ui,sans-serif;max-width:560px;margin:12vh auto;padding:0 16px;color:#1b2430;line-height:1.5}a{color:#1d5fa8}</style></head><body><h1>${m.titre}</h1><p>${m.corps}</p><p><a href="mailto:contact@scoremydatacenter.org">contact@scoremydatacenter.org</a></p><p>${apres}</p></body></html>`;
  return new Response(html, {
    status: 429,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "retry-after": String(Math.ceil(reessayerDans / 1000)),
      "cache-control": "no-store",
      "x-robots-tag": "noindex",
    },
  });
}
