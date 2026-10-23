// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Registry of procedure files, one entry per country present in the corpus.
//
// The registry is EXHAUSTIVE on purpose: a country we have not read is listed
// with `null`, not left out. A gap we declare is countable and testable; a gap
// we leave out is a gap nobody sees. `test_le_registre_des_procedures_couvre_le
// _corpus` fails when a new country lands in the corpus without a line here, so
// adding a country forces the choice — read the law, or declare the hole.
import type { ProcedureCountry, ProcedureJurisdiction, ProjectStatus } from "./types";
import { FR } from "./fr";
import { US } from "./us";

export type { ProcedureClaim, ProcedureJurisdiction, ProjectStatus } from "./types";

/** null = country in the corpus, procedure not read yet. Never a silent miss. */
export const PROCEDURE: Record<string, ProcedureCountry | null> = {
  FR,
  US,
  // Declared gaps, in corpus order. Each one needs its own statutes read at
  // source before it earns a file — the German draft (BImSchG + Landesrecht)
  // and the Dutch one (Omgevingswet) are the two next in line.
  DE: null,
  NL: null,
  GB: null,
  IT: null,
  PL: null,
  ES: null,
  CH: null,
  SE: null,
  NO: null,
  BE: null,
  FI: null,
  DK: null,
  IE: null,
  LU: null,
  PT: null,
  AT: null,
  IL: null,
};

export interface ResolvedProcedure {
  country: ProcedureCountry;
  jurisdiction: ProcedureJurisdiction;
  /** The subdivision name when the procedure came from one, else null. */
  subdivision: string | null;
}

/**
 * The procedure that actually applies to one site — or null, which the page
 * must render as an explicit "we have not read this jurisdiction", never as
 * silence and never by falling back on another jurisdiction's rules.
 *
 * A decentralised country NEVER falls back on its national block: in the United
 * States there is no federal data-center permit, so serving a "national"
 * procedure for an unread state would be inventing one.
 */
export function resolveProcedure(
  country: string | null | undefined,
  adminArea: string | null | undefined,
): ResolvedProcedure | null {
  if (!country) return null;
  const entry = PROCEDURE[country];
  if (!entry) return null;

  if (entry.decentralised) {
    const sub = adminArea ? entry.subdivisions?.[adminArea] : undefined;
    return sub ? { country: entry, jurisdiction: sub, subdivision: adminArea! } : null;
  }
  return entry.national
    ? { country: entry, jurisdiction: entry.national, subdivision: null }
    : null;
}

/** The one window open at this stage, or null when the stage has none written. */
export function windowFor(
  resolved: ResolvedProcedure,
  status: ProjectStatus | string | null | undefined,
) {
  if (!status) return null;
  return resolved.jurisdiction.windows[status as ProjectStatus] ?? null;
}
