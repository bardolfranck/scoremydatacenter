// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Resend transactional send + the double-opt-in confirmation email (FR/EN).
// From no-reply@send.scoremydatacenter.org, Reply-To contact@scoremydatacenter.org
// (which Cloudflare Email Routing forwards to Franck's inbox).
import type { Env, Lang } from "./util";
import { escapeHtml } from "./util";
import type { ReportDef } from "./reports";
import { reportTitle } from "./reports";

const FROM = "ScoreMyDataCenter <no-reply@send.scoremydatacenter.org>";
const REPLY_TO = "contact@scoremydatacenter.org";

export async function sendConfirmationEmail(
  env: Env,
  opts: { to: string; lang: Lang; report: ReportDef; confirmUrl: string; unsubscribeUrl: string },
): Promise<void> {
  const title = reportTitle(opts.report, opts.lang);
  const { subject, html, text } = opts.lang === "fr"
    ? buildFr(title, opts.confirmUrl, opts.unsubscribeUrl)
    : buildEn(title, opts.confirmUrl, opts.unsubscribeUrl);

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: FROM,
      to: [opts.to],
      reply_to: REPLY_TO,
      subject,
      html,
      text,
    }),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`resend ${res.status}: ${detail.slice(0, 300)}`);
  }
}

function shell(bodyHtml: string): string {
  return `<!doctype html><html><body style="margin:0;background:#f6f8fb;padding:24px;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#16233a">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table role="presentation" width="480" cellpadding="0" cellspacing="0"
 style="max-width:480px;background:#fff;border-radius:14px;padding:32px;box-shadow:0 14px 40px -24px rgba(14,22,38,.4)">
${bodyHtml}
</table></td></tr></table></body></html>`;
}

function button(url: string, label: string): string {
  return `<tr><td style="padding:22px 0"><a href="${escapeHtml(url)}"
 style="display:inline-block;background:#16233a;color:#fff;text-decoration:none;
 padding:12px 22px;border-radius:10px;font-weight:600">${escapeHtml(label)}</a></td></tr>`;
}

function buildFr(title: string, confirmUrl: string, unsubUrl: string) {
  return {
    subject: `Confirme ton email pour recevoir « ${title} »`,
    text:
      `Bonjour,\n\nVous avez demandé « ${title} » sur ScoreMyDataCenter.\n` +
      `Confirmez votre email en ouvrant ce lien — le rapport se télécharge aussitôt :\n${confirmUrl}\n\n` +
      `Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.\n` +
      `Se désinscrire : ${unsubUrl}\n\n— ScoreMyDataCenter, observatoire indépendant`,
    html: shell(
      `<tr><td style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#8a97a8">ScoreMyDataCenter</td></tr>
<tr><td style="font-size:20px;font-weight:700;padding:6px 0 2px">Plus qu'un clic 📄</td></tr>
<tr><td style="line-height:1.55;color:#4a5568;padding-top:8px">
Vous avez demandé <strong>« ${escapeHtml(title)} »</strong>. Confirmez votre email et le rapport se télécharge aussitôt.</td></tr>
${button(confirmUrl, "Confirmer et télécharger")}
<tr><td style="line-height:1.5;color:#8a97a8;font-size:13px">
Si vous n'êtes pas à l'origine de cette demande, ignorez simplement ce message — rien ne sera envoyé.</td></tr>
<tr><td style="padding-top:18px;border-top:1px solid #eef1f5;color:#8a97a8;font-size:12px;line-height:1.5">
Tu reçois cet email car ton adresse a été saisie sur scoremydatacenter.org.
<a href="${escapeHtml(unsubUrl)}" style="color:#8a97a8">Se désinscrire</a>.</td></tr>`,
    ),
  };
}

function buildEn(title: string, confirmUrl: string, unsubUrl: string) {
  return {
    subject: `Confirm your email to get "${title}"`,
    text:
      `Hello,\n\nYou requested "${title}" on ScoreMyDataCenter.\n` +
      `Confirm your email by opening this link — the report downloads right away:\n${confirmUrl}\n\n` +
      `If you didn't request this, just ignore this message.\n` +
      `Unsubscribe: ${unsubUrl}\n\n— ScoreMyDataCenter, independent observatory`,
    html: shell(
      `<tr><td style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#8a97a8">ScoreMyDataCenter</td></tr>
<tr><td style="font-size:20px;font-weight:700;padding:6px 0 2px">One click away 📄</td></tr>
<tr><td style="line-height:1.55;color:#4a5568;padding-top:8px">
You requested <strong>"${escapeHtml(title)}"</strong>. Confirm your email and the report downloads right away.</td></tr>
${button(confirmUrl, "Confirm and download")}
<tr><td style="line-height:1.5;color:#8a97a8;font-size:13px">
If you didn't request this, just ignore this message — nothing will be sent.</td></tr>
<tr><td style="padding-top:18px;border-top:1px solid #eef1f5;color:#8a97a8;font-size:12px;line-height:1.5">
You received this because your address was entered on scoremydatacenter.org.
<a href="${escapeHtml(unsubUrl)}" style="color:#8a97a8">Unsubscribe</a>.</td></tr>`,
    ),
  };
}
