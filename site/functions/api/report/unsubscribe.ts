// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// GET /api/report/unsubscribe?token=…  — one-click opt-out (CNIL).
// Flips the row to `unsubscribed`; the address stays in the table (so we honour
// the opt-out and don't re-mail) but is excluded from any future send.
import type { Env } from "../../_shared/util";
import { htmlPage, normLang, nowIso } from "../../_shared/util";

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const token = new URL(request.url).searchParams.get("token") ?? "";

  const row = token
    ? await env.DB.prepare(`SELECT lang FROM subscribers WHERE token = ?1`).bind(token).first<{ lang: string }>()
    : null;

  const lang = normLang(row?.lang);
  if (row) {
    await env.DB.prepare(
      `UPDATE subscribers SET status = 'unsubscribed', unsubscribed_at = ?2 WHERE token = ?1`,
    ).bind(token, nowIso()).run();
  }

  return htmlPage({
    lang,
    title: lang === "fr" ? "Désinscription" : "Unsubscribed",
    body: lang === "fr"
      ? `<h1>C'est fait ✔</h1><p>Votre adresse ne recevra plus nos publications. Vous pouvez revenir quand vous voulez.</p>`
      : `<h1>Done ✔</h1><p>Your address won't receive our publications anymore. You're welcome back anytime.</p>`,
  });
};
