// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// POST /api/report/subscribe  — step 1 of the double opt-in.
// Body: { email, consent, report, lang, company? }
//   1. honeypot (`company`) tripped → pretend success, drop silently (bot).
//   2. consent must be true; email must be valid format AND a receiving domain.
//   3. upsert the row as `pending` with a fresh token (existing confirmed rows
//      stay confirmed — a re-request just refreshes the token & re-mails).
//   4. mail the confirmation link. The PDF is NEVER handed out here.
import type { Env } from "../../_shared/util";
import {
  json, normalizeEmail, isValidEmailFormat, domainCanReceive,
  normLang, newToken, nowIso,
} from "../../_shared/util";
import { getReport } from "../../_shared/reports";
import { sendConfirmationEmail } from "../../_shared/email";

interface Body {
  email?: unknown; consent?: unknown; report?: unknown; lang?: unknown; company?: unknown;
}

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  let body: Body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "bad_request" }, 400);
  }

  // 1. Honeypot: a real visitor never fills `company`. Answer 200 so the bot
  // sees "success" and nothing is stored or sent.
  if (typeof body.company === "string" && body.company.trim() !== "") {
    return json({ ok: true });
  }

  // 2. Validation.
  if (body.consent !== true) return json({ ok: false, error: "consent" }, 400);
  const def = getReport(body.report);
  if (!def) return json({ ok: false, error: "report" }, 400);
  const lang = normLang(body.lang);
  const email = normalizeEmail(body.email);
  if (!isValidEmailFormat(email)) return json({ ok: false, error: "email" }, 400);
  if (!(await domainCanReceive(email))) return json({ ok: false, error: "email" }, 400);

  // 3. Upsert. UNIQUE(email, report) keeps one row per (person, report).
  const token = newToken();
  const now = nowIso();
  try {
    await env.DB.prepare(
      `INSERT INTO subscribers (email, report, lang, status, token, consent, created_at)
       VALUES (?1, ?2, ?3, 'pending', ?4, 1, ?5)
       ON CONFLICT(email, report) DO UPDATE SET
         token = ?4,
         lang = ?3,
         consent = 1,
         created_at = ?5,
         status = CASE WHEN subscribers.status = 'unsubscribed' THEN 'pending' ELSE subscribers.status END`,
    ).bind(email, def.slug, lang, token, now).run();
  } catch (e) {
    return json({ ok: false, error: "store" }, 500);
  }

  // 4. Send the confirmation email. If it fails, surface a retryable error.
  const origin = new URL(request.url).origin;
  const confirmUrl = `${origin}/api/report/confirm?token=${token}`;
  const unsubscribeUrl = `${origin}/api/report/unsubscribe?token=${token}`;
  try {
    await sendConfirmationEmail(env, { to: email, lang, report: def, confirmUrl, unsubscribeUrl });
  } catch {
    return json({ ok: false, error: "send" }, 502);
  }

  return json({ ok: true });
};
