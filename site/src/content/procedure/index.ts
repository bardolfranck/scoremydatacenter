// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Registre des procédures, une entrée par pays présent dans le corpus.
//
// Le registre est EXHAUSTIF à dessein : un pays dont la loi n'est pas lue est inscrit à
// `null`, il n'est pas omis. Un trou déclaré se compte et se rattrape ; un trou omis se
// découvre chez le lecteur. `test_le_registre_des_procedures_couvre_le_corpus` échoue dès
// qu'un pays arrive dans le corpus sans ligne ici : ajouter un pays force donc le choix —
// lire la loi, ou déclarer le trou.
import type { ProcedureCountry, ProcedureJurisdiction, ProjectStatus } from "./types";
import { EU } from "./eu";
import { FR } from "./fr";
import { US } from "./us";
import { DE } from "./de";
import { NL } from "./nl";
import { GB } from "./gb";
import { ES } from "./es";
import { CH } from "./ch";
import { SE } from "./se";
import { NO } from "./no";
import { FI } from "./fi";
import { DK } from "./dk";
import { AT } from "./at";
import { IT } from "./it";
import { BE } from "./be";
import { LU } from "./lu";
import { PL } from "./pl";
import { IE } from "./ie";

export type { ProcedureClaim, ProcedureJurisdiction, ProjectStatus } from "./types";

/** null = pays présent au corpus, procédure pas encore lue. Jamais un oubli silencieux. */
export const PROCEDURE: Record<string, ProcedureCountry | null> = {
  US,
  FR,
  DE,
  NL,
  GB,
  ES,
  CH,
  SE,
  NO,
  FI,
  DK,
  AT,
  IT,
  BE,
  LU,
  PL,
  IE,
  // Trous DÉCLARÉS. Ces pays reçoivent déjà le socle européen (consultation d'au moins
  // trente jours, publication de la décision et de ses motifs, accès au juge, information
  // environnementale sous un mois) ; ce qui leur manque est leur DÉLAI NATIONAL de recours,
  // qu'aucune directive ne fixe.
  //   PT (9)         — non lu. Au 2026-10-27, diariodarepublica.pt RÉPOND (plus de 504) mais sa
  //                    couche data est cassée : l'action du SPA `GetConsolidacaoByDiplomaFrag`
  //                    renvoie net::ERR_ABORTED, la page reste bloquée sur « A carregar alterações… »,
  //                    et data.dre.pt (export statique) redirige vers ce même SPA et bloque curl.
  //                    Le texte consolidé EN VIGUEUR n'est donc pas lisible — blocage CHEZ DRE, pas chez
  //                    nous. Substance présumée : CPTA art. 58, ~trois mois. NE PAS retenter un simple
  //                    curl (le serveur « debout » ne veut pas dire réparé) : rouvrir quand l'action
  //                    data `GetConsolidacaoByDiplomaFrag` répond et que l'art. 58 se lit au texte.
  //   IL (8)         — hors Union, donc hors socle : tout est à lire. TROU DÉCLARÉ,
  //                    instruit deux fois (WORLD, 2026-10-27, la 2e sous VPN IL) :
  //                    · LE BLOCAGE, tel qu'il est : main.knesset.gov.il et fs.knesset.gov.il
  //                      répondent HTTP/2 247 + challenge JS Reblaze depuis notre infra, et
  //                      « temporarily inaccessible from your location » au navigateur réel
  //                      depuis la France ; gov.il 403, et ne sert de toute façon que des
  //                      extraits en traduction « non officielle ». Copies anglaises complètes
  //                      (Adalah, FAOLEX, NLI) = recueils tiers — pas des sources. Le re-test
  //                      utile : ces hôtes répondent SANS VPN et SANS challenge — pas qu'un
  //                      curl passe.
  //                    · LE FAIT ARCHITECTURAL (épargne la recherche au prochain passage) :
  //                      il n'existe PAS de consolidé officiel — le bouton « לחוק המלא » du
  //                      registre officiel (apps/legislation, loi 2000613, statut תקף,
  //                      171 tiqqunim référencés ספר החוקים) pointe vers he.wikisource.org.
  //                      Wikisource lisible partout mais REFUSÉ comme hôte : la Knesset qui
  //                      pointe n'est pas une autorité qui PUBLIE (précédent Géorgie/Arkansas
  //                      = « reproduit par l'autorité qui l'applique »), un wiki vieillit sans
  //                      que `verified` le voie, et l'url publiée doit s'ouvrir CHEZ LE LECTEUR
  //                      — une Knesset géobloquée est un lien mort pour le riverain.
  //                    · LA RÉPONSE DE FOND, connue mais NON CITABLE (à confirmer le jour où
  //                      un hôte passe, jamais à servir d'ici là) : §152(a)(1) de חוק התכנון
  //                      והבנייה תשכ"ה-1965 → ערר sous 30 JOURS de la notification devant la
  //                      ועדת ערר (refus de permis ou rejet d'opposition §149(a) ; section
  //                      amendée jusqu'à תשפ"ה) ; 2e étage = עתירה מנהלית ~45 jours (תקנות
  //                      בתי משפט לעניינים מינהליים, 2000). Un trou qui sait ce qu'il cherche
  //                      se rattrape en une passe.
  PT: null,
  IL: null,  // hors Union, hors socle — trou déclaré, voir en-tête
};

/** Pays dont le bloc national complète le socle européen plutôt que de s'y substituer. */
export const SOCLE_EUROPEEN = EU;

export interface ResolvedProcedure {
  country: ProcedureCountry;
  jurisdiction: ProcedureJurisdiction;
  /** Le socle hérité, à lire AVANT le bloc national — ou null. */
  socle: ProcedureJurisdiction | null;
  /** Le nom de la subdivision quand la procédure en vient, sinon null. */
  subdivision: string | null;
}

/**
 * La procédure qui s'applique réellement à un site — ou null, que la page doit rendre
 * comme un « nous n'avons pas lu cette juridiction » explicite, jamais comme un silence
 * et jamais en retombant sur les règles d'une autre juridiction.
 *
 * Un pays décentralisé ne retombe JAMAIS sur son bloc national : aux États-Unis aucun
 * permis fédéral ne porte sur un data center, et en Suisse aucun délai fédéral ne porte
 * sur un permis de construire. Servir un bloc « national » pour un État ou un canton non
 * lu reviendrait à en inventer un.
 */
export function resolveProcedure(
  country: string | null | undefined,
  adminArea: string | null | undefined,
): ResolvedProcedure | null {
  if (!country) return null;
  const entry = PROCEDURE[country];
  if (!entry) return null;
  const socle = entry.inherits === "EU" ? EU : null;

  if (entry.decentralised) {
    const sub = adminArea ? entry.subdivisions?.[adminArea] : undefined;
    return sub
      ? { country: entry, jurisdiction: sub, socle, subdivision: adminArea! }
      : null;
  }
  return entry.national
    ? { country: entry, jurisdiction: entry.national, socle, subdivision: null }
    : null;
}

/**
 * La fenêtre ouverte à ce stade. Le bloc national prime sur le socle : une transposition
 * plus précise que la directive doit être celle qu'on lit.
 */
export function windowFor(
  resolved: ResolvedProcedure,
  status: ProjectStatus | string | null | undefined,
) {
  if (!status) return null;
  const s = status as ProjectStatus;
  return resolved.jurisdiction.windows[s] ?? resolved.socle?.windows[s] ?? null;
}

/** Tous les délais applicables, socle d'abord puis national. */
export function deadlinesFor(resolved: ResolvedProcedure) {
  return [...(resolved.socle?.deadlines ?? []), ...resolved.jurisdiction.deadlines];
}

/** Comment obtenir le dossier, socle d'abord puis national. */
export function documentsFor(resolved: ResolvedProcedure) {
  return [...(resolved.socle?.documents ?? []), ...resolved.jurisdiction.documents];
}
