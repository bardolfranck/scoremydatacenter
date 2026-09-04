#!/usr/bin/env node
// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
//
// Local veille sender (agent-codeur-site leg). Reads the LATEST digest produced
// by the harvest (`make veille-fr`) in the PRIVATE newsroom, and emails it to the
// operator via Resend. The Resend key lives ONLY in ~/.smdc/resend.env, is read
// line-by-line (never sourced), and is NEVER logged. Runs locally, daily, after
// the harvest — it never deploys, never publishes, never touches R2.

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import https from "node:https";

const NEWSROOM = process.env.SMDC_NEWSROOM
  ?? "/Users/frabar/CLAUDE/CLAUDE-CODE/SCOREMYDATACENTER/smdc-newsroom";
const VEILLE_DIR = join(NEWSROOM, "veille");
const TO = process.env.VEILLE_TO ?? "bardolfranck@gmail.com";
const FROM = process.env.VEILLE_FROM ?? "SMDC Veille <no-reply@send.scoremydatacenter.org>";

// Read one KEY from an env file WITHOUT sourcing it (KEY=VALUE lines only).
function readEnvKey(file, key) {
  if (!existsSync(file)) return null;
  for (const line of readFileSync(file, "utf8").split("\n")) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
    if (m && m[1] === key) return m[2].replace(/^["']|["']$/g, "");
  }
  return null;
}

const RESEND_KEY = readEnvKey(join(homedir(), ".smdc", "resend.env"), "RESEND_API_KEY");
if (!RESEND_KEY) {
  console.error("[send-veille] RESEND_API_KEY introuvable dans ~/.smdc/resend.env"); process.exit(1);
}
if (!existsSync(VEILLE_DIR)) { console.error(`[send-veille] pas de dossier veille: ${VEILLE_DIR}`); process.exit(1); }

const dates = readdirSync(VEILLE_DIR).filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort();
if (!dates.length) { console.error("[send-veille] aucun digest trouvé"); process.exit(1); }
const latest = dates[dates.length - 1];
const dir = join(VEILLE_DIR, latest);
const manifest = JSON.parse(readFileSync(join(dir, "manifest.json"), "utf8"));
const html = readFileSync(join(dir, "digest.html"), "utf8");
const subject = manifest.subject ?? `SMDC — veille du ${latest} (${manifest.count ?? "?"} projets)`;

function postResend(payload, key) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const req = https.request(
      { hostname: "api.resend.com", path: "/emails", method: "POST",
        headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json",
                   "Content-Length": Buffer.byteLength(data) } },
      (res) => { let buf = ""; res.on("data", (c) => (buf += c));
                 res.on("end", () => { try { resolve({ status: res.statusCode, body: JSON.parse(buf || "{}") }); }
                                       catch { resolve({ status: res.statusCode, body: {} }); } }); }
    );
    req.on("error", reject); req.write(data); req.end();
  });
}

const { status, body } = await postResend({ from: FROM, to: [TO], subject, html }, RESEND_KEY);
if (status >= 200 && status < 300 && body.id) {
  console.log(`[send-veille] OK — digest ${latest} envoyé à ${TO} (Resend id ${body.id}, ${manifest.count ?? "?"} candidats)`);
} else {
  console.error(`[send-veille] ECHEC (HTTP ${status}): ${JSON.stringify(body).slice(0, 300)}`); process.exit(1);
}
