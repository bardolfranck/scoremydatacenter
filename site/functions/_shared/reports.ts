// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// The ONE registry of downloadable reports. Adding a report = one entry here +
// one thin page (src/pages/.../<slug>.astro) + the PDF(s) uploaded to R2 under
// the keys named below. The email gate, D1 store, confirmation mail and gated
// delivery are all report-agnostic — they read this table.
//
// `gated`: false = the whole PDF is a free lead-magnet (Big Tech). true = only
// the full edition is gated; a free teaser (page 1) lives elsewhere (Banks).
// Delivery is identical either way (email → confirm → download); `gated` is a
// flag the surfaces can read, not a different backend path. A future PAID tier
// is a separate decision (Franck) — NOT wired here; keep this free-only.

export interface ReportDef {
  slug: string;
  gated: boolean;
  titleFr: string;
  titleEn: string;
  // R2 object keys for the FULL edition, per language.
  pdfFr: string;
  pdfEn: string;
  // Filename presented to the browser on download, per language.
  filenameFr: string;
  filenameEn: string;
}

export const REPORTS: Record<string, ReportDef> = {
  "big-tech": {
    slug: "big-tech",
    gated: false,
    // Display name = "Big Tech-AI" (report carries the AI-proxy angle). The R2
    // keys below keep the file's own "BigTech" name — renaming the object would
    // mean re-forging the PDF; only the shown title/filename change.
    titleFr: "Rapport Big Tech-AI 2026",
    titleEn: "Big Tech-AI Report 2026",
    pdfFr: "reports/big-tech/ScoreMyDataCenter-BigTech-2026-FR-FIGE.pdf",
    pdfEn: "reports/big-tech/ScoreMyDataCenter-BigTech-2026-EN-FIGE.pdf",
    filenameFr: "ScoreMyDataCenter-BigTech-AI-2026-FR.pdf",
    filenameEn: "ScoreMyDataCenter-BigTech-AI-2026-EN.pdf",
  },
  "banques": {
    slug: "banques",
    gated: true,
    titleFr: "Les noms de chez vous — Les banques",
    titleEn: "Household names — The banks",
    pdfFr: "reports/banques/ScoreMyDataCenter-Banques-2026-FR-FIGE.pdf",
    pdfEn: "reports/banques/ScoreMyDataCenter-Banques-2026-EN-FIGE.pdf",
    filenameFr: "ScoreMyDataCenter-Banques-2026-FR.pdf",
    filenameEn: "ScoreMyDataCenter-Banques-2026-EN.pdf",
  },
};

export function getReport(slug: unknown): ReportDef | null {
  if (typeof slug !== "string") return null;
  return REPORTS[slug] ?? null;
}

export function pdfKey(def: ReportDef, lang: "fr" | "en"): string {
  return lang === "fr" ? def.pdfFr : def.pdfEn;
}
export function pdfFilename(def: ReportDef, lang: "fr" | "en"): string {
  return lang === "fr" ? def.filenameFr : def.filenameEn;
}
export function reportTitle(def: ReportDef, lang: "fr" | "en"): string {
  return lang === "fr" ? def.titleFr : def.titleEn;
}
