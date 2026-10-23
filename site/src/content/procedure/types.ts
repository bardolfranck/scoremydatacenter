// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Procedure files — "what can still be done, where, and until when".
//
// These blocks are the only place on the site where we tell a reader what to DO.
// They are therefore held to the strictest rule we have: a claim exists only if
// it carries the statute that says it, a link to the TEXT (never a commentary,
// never a law-firm digest), and the date we read that text in its version in
// force. No source, no claim — `resolveProcedure` returns null and the page says
// so rather than inventing a procedure that does not exist in that jurisdiction.

/** One actionable statement, traceable to the text that creates it. */
export interface ProcedureClaim {
  /** What the reader can do, or what runs out. Written for a non-lawyer. */
  text: { fr: string; en: string };
  /** The article, cited the way the jurisdiction cites it. */
  cite: string;
  /** Primary source: the text itself. */
  url: string;
  /** Date we read that text, in the version then in force (YYYY-MM-DD). */
  verified: string;
}

export type ProjectStatus = "announced" | "permitting" | "under_construction" | "operational";

/** The level that actually decides, and what is open at each stage. */
export interface ProcedureJurisdiction {
  /** Who decides. Named as locals name it. */
  authority: { fr: string; en: string };
  /** The window open at a given stage — the one sentence that matters most. */
  windows: Partial<Record<ProjectStatus, ProcedureClaim>>;
  /** Deadlines that do not come back once missed. */
  deadlines: ProcedureClaim[];
  /** How to obtain the file itself. */
  documents: ProcedureClaim[];
}

export interface ProcedureCountry {
  /** ISO 3166-1 alpha-2, as the corpus spells `country`. */
  country: string;
  /**
   * True when the permit is decided below the national level. A decentralised
   * country NEVER falls back on its national block for a site: `national` then
   * only frames what is common, and a site whose subdivision is absent gets no
   * procedure block at all.
   */
  decentralised: boolean;
  /**
   * How `subdivisions` is keyed — the corpus spells `admin_area` differently per
   * country (US: full state name; DE: two-letter Land; FR: département code;
   * GB: ISO nation). Stated here so a mismatch is a bug, not a silent miss.
   */
  subdivisionKey?: string;
  /**
   * One sentence on how the country is built, for a reader who assumes every
   * country works like theirs. No claim, no deadline — the frame only.
   */
  frame?: { fr: string; en: string };
  /**
   * Socle supranational dont ce pays hérite. "EU" = les garanties minimales des
   * directives 2011/92 et 2003/4, écrites une seule fois dans eu.ts. Un socle est un
   * PLANCHER : le bloc national le complète, il ne le remplace jamais.
   */
  inherits?: "EU";
  national?: ProcedureJurisdiction;
  subdivisions?: Record<string, ProcedureJurisdiction>;
}
