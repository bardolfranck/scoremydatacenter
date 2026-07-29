// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Shared types + helpers for the report email-gate Functions.

export interface Env {
  // D1 database holding the subscribers table (Franck's own exportable store).
  DB: D1Database;
  // R2 bucket holding the report PDFs (keys per reports.ts).
  REPORTS_BUCKET: R2Bucket;
  // Resend API key — set as an ENCRYPTED secret, never committed.
  RESEND_API_KEY: string;
}

export type Lang = "fr" | "en";

export function normLang(v: unknown): Lang {
  return v === "fr" ? "fr" : "en";
}

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

// A minimal HTML page for the confirm / error / unsubscribe screens the user
// lands on. Kept inline (no template engine) and self-contained.
export function htmlPage(opts: { lang: Lang; title: string; body: string; status?: number }): Response {
  const home = opts.lang === "fr" ? "/fr/" : "/";
  const back = opts.lang === "fr" ? "Retour à l'accueil" : "Back to home";
  const doc = `<!doctype html><html lang="${opts.lang}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(opts.title)} — ScoreMyDataCenter</title>
<style>
  :root{color-scheme:light dark}
  body{margin:0;min-height:100dvh;display:grid;place-items:center;background:#f6f8fb;
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#16233a}
  @media(prefers-color-scheme:dark){body{background:#0e1626;color:#e8edf5}}
  .card{max-width:30rem;margin:1.5rem;padding:2rem;border-radius:16px;background:#fff;
        box-shadow:0 20px 50px -28px rgba(14,22,38,.5);text-align:center}
  @media(prefers-color-scheme:dark){.card{background:#141a24}}
  h1{font-size:1.5rem;margin:.2rem 0 .6rem}
  p{line-height:1.5;margin:.4rem 0;color:#4a5568}
  @media(prefers-color-scheme:dark){p{color:#a8b3c4}}
  a.btn{display:inline-block;margin-top:1.1rem;padding:.6rem 1.1rem;border-radius:10px;
        background:#16233a;color:#fff;text-decoration:none;font-weight:600}
</style></head><body><div class="card">${opts.body}
<p><a class="btn" href="${home}">${back}</a></p></div></body></html>`;
  return new Response(doc, {
    status: opts.status ?? 200,
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
  });
}

export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c] as string));
}

// Email validation: RFC-pragmatic format, then a DNS check that the domain can
// actually receive mail (MX, or A/AAAA fallback). Catches "vatefairecuire@unoeuf.fr"
// style junk domains up front — the double opt-in catches the rest (a fake
// mailbox on a real domain simply never confirms). DNS failure never blocks
// (fail-open): a transient DoH hiccup must not reject a legitimate signup.
export function normalizeEmail(v: unknown): string {
  return String(v ?? "").trim().toLowerCase();
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function isValidEmailFormat(email: string): boolean {
  return EMAIL_RE.test(email) && email.length <= 254;
}

export async function domainCanReceive(email: string): Promise<boolean> {
  const domain = email.split("@")[1];
  if (!domain) return false;
  const q = async (type: "MX" | "A" | "AAAA") => {
    const r = await fetch(
      `https://cloudflare-dns.com/dns-query?name=${encodeURIComponent(domain)}&type=${type}`,
      { headers: { accept: "application/dns-json" } },
    );
    if (!r.ok) throw new Error("doh");
    return (await r.json()) as { Answer?: Array<{ type: number }> };
  };
  try {
    const mx = await q("MX");
    if (mx.Answer?.some((a) => a.type === 15)) return true; // 15 = MX
    const a = await q("A");
    if (a.Answer?.length) return true;
    const aaaa = await q("AAAA");
    return !!aaaa.Answer?.length;
  } catch {
    return true; // fail-open on DNS trouble
  }
}

// Long, URL-safe, unguessable token for confirm / download / unsubscribe.
export function newToken(): string {
  const b = new Uint8Array(32);
  crypto.getRandomValues(b);
  return [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
}

export function nowIso(): string {
  return new Date().toISOString();
}
