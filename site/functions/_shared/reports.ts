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
  "france": {
    slug: "france",
    gated: true,
    titleFr: "La France, vue de ses data centers",
    titleEn: "France, seen through its data centers",
    pdfFr: "reports/france/ScoreMyDataCenter-France-2026-FR-FIGE.pdf",
    pdfEn: "reports/france/ScoreMyDataCenter-France-2026-EN-FIGE.pdf",
    filenameFr: "ScoreMyDataCenter-France-2026-FR.pdf",
    filenameEn: "ScoreMyDataCenter-France-2026-EN.pdf",
  },
  // Country reports ship in the country's language + EN, never FR (policy Franck
  // 2026-07-30: the national language reaches the LOCAL elected official who isn't
  // at ease in English — and it avoids "1 report = 3 versions"). France is the sole
  // FR edition (the country IS francophone). Nederland: NL + EN. The NL edition is
  // HELD pending a native-Dutch review (agent-codeur-rapports) — a translated-from-
  // English text would ring false to the very reader it exists for. So for now BOTH
  // site languages serve the EN PDF: a FR visitor reads the English edition (the
  // report page says so). When the NL edition passes native review, it becomes a
  // third language here.
  "nederland": {
    slug: "nederland",
    gated: true,
    titleFr: "Les Pays-Bas, vus de leurs data centers",
    titleEn: "The Netherlands, seen through its data centers",
    pdfFr: "reports/nederland/ScoreMyDataCenter-Nederland-2026-EN-FIGE.pdf",
    pdfEn: "reports/nederland/ScoreMyDataCenter-Nederland-2026-EN-FIGE.pdf",
    filenameFr: "ScoreMyDataCenter-Nederland-2026-EN.pdf",
    filenameEn: "ScoreMyDataCenter-Nederland-2026-EN.pdf",
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
