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
  //   IL (8)         — hors Union, donc hors socle : tout est à lire. TROU DÉCLARÉ
  //                    (WORLD, 2026-10-27, mesuré) : le texte faisant foi est l'hébreu
  //                    (Reshumot / base Knesset), et la Knesset GÉOBLOQUE hors d'Israël
  //                    (« temporarily inaccessible from your location », vérifié au
  //                    navigateur réel depuis la France) ; gov.il refuse nos requêtes (403)
  //                    et ne sert de toute façon que des extraits en traduction « non
  //                    officielle » ; les copies anglaises complètes (Adalah, FAOLEX, NLI)
  //                    sont des recueils TIERS qui vieillissent sans le dire — pas des
  //                    sources. Aucun hôte proposable à HOTES_DE_TEXTE tant que le texte
  //                    en vigueur n'est pas LISIBLE depuis chez nous : IL reste null,
  //                    plutôt qu'un délai sourcé sur un texte qu'on n'a pas lu.
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
