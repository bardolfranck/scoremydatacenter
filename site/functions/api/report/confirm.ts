// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// GET /api/report/confirm?token=…  — step 2 of the double opt-in.
// The link mailed to the subscriber. Marks the row `confirmed` (this is the
// proof the address is real and theirs), then 302-redirects straight to the
// gated download so the PDF starts immediately.
import type { Env } from "../../_shared/util";
import { htmlPage, normLang, nowIso } from "../../_shared/util";

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const token = new URL(request.url).searchParams.get("token") ?? "";
  const origin = new URL(request.url).origin;

  const row = token
    ? await env.DB.prepare(`SELECT status, lang FROM subscribers WHERE token = ?1`).bind(token).first<{ status: string; lang: string }>()
    : null;

  if (!row) {
    return htmlPage({
      lang: "fr",
      status: 404,
      title: "Lien invalide",
      body: `<h1>Lien invalide ou expiré</h1>
<p>Ce lien de confirmation n'est plus valide. Reprenez le téléchargement depuis la page du rapport.</p>
<p style="color:#8a97a8">This confirmation link is no longer valid — please request the report again.</p>`,
    });
  }

  const lang = normLang(row.lang);
  if (row.status !== "confirmed") {
    await env.DB.prepare(
      `UPDATE subscribers SET status = 'confirmed', confirmed_at = ?2 WHERE token = ?1`,
    ).bind(token, nowIso()).run();
  }

  // Straight to the gated stream — the download starts without another click.
  return Response.redirect(`${origin}/api/report/download?token=${encodeURIComponent(token)}`, 302);
};
