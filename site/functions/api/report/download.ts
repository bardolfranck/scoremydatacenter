// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// GET /api/report/download?token=…  — the gated delivery.
// Only a CONFIRMED token gets the PDF. The file is streamed from R2 (never a
// public/guessable URL), so a paid tier later can reuse the exact same gate.
// The link is stable (bookmarkable) but tied to one confirmed subscriber.
import type { Env } from "../../_shared/util";
import { htmlPage, normLang } from "../../_shared/util";
import { getReport, pdfKey, pdfFilename } from "../../_shared/reports";

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const token = new URL(request.url).searchParams.get("token") ?? "";

  const row = token
    ? await env.DB.prepare(`SELECT report, lang, status FROM subscribers WHERE token = ?1`)
        .bind(token).first<{ report: string; lang: string; status: string }>()
    : null;

  if (!row || row.status !== "confirmed") {
    return htmlPage({
      lang: "fr",
      status: 403,
      title: "Accès non confirmé",
      body: `<h1>Lien non confirmé</h1>
<p>Ce lien de téléchargement n'est pas (ou plus) valide. Vérifiez que vous avez bien cliqué sur le lien de confirmation reçu par email.</p>
<p style="color:#8a97a8">This download link isn't confirmed — check the confirmation email we sent you.</p>`,
    });
  }

  const def = getReport(row.report);
  const lang = normLang(row.lang);
  if (!def) return htmlPage({ lang, status: 404, title: "Rapport introuvable", body: `<h1>Rapport introuvable</h1>` });

  const key = pdfKey(def, lang);
  const object = await env.REPORTS_BUCKET.get(key);
  if (!object) {
    return htmlPage({
      lang, status: 404, title: "Fichier indisponible",
      body: `<h1>Fichier momentanément indisponible</h1>
<p>Le rapport n'a pas pu être servi. Réessaie plus tard, ou écris-nous : contact@scoremydatacenter.org.</p>`,
    });
  }

  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("content-type", "application/pdf");
  headers.set("content-disposition", `attachment; filename="${pdfFilename(def, lang)}"`);
  headers.set("cache-control", "private, no-store");
  return new Response(object.body, { headers });
};
