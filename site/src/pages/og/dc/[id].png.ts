// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Per-DC Open Graph card (1200×630) — a faithful build-time render of the
// validated R4 design (draft-4 screen 3d): dark navy, Chivo, "My" grey, pillar
// strip with icons, dual 118px badge, citable quote. Hand-built SVG → resvg (no
// headless browser); Chivo TTF vendored for text.
import type { APIRoute } from "astro";
import { Resvg } from "@resvg/resvg-js";
import { join } from "node:path";

// resvg-js 2.x honours `fontFiles` (paths), NOT `fontBuffers` — passing buffers
// silently falls back to a system sans, which renders every weight at ~regular
// (the "pas la même police / pas assez gras" bug). Paths load the real Chivo.
const fontDir = join(process.cwd(), "src/og/fonts");
const FONT_FILES = ["chivo-900.ttf", "chivo-700.ttf", "chivo-mono-400.ttf", "chivo-mono-600.ttf"].map((f) => join(fontDir, f));

const GRADE: Record<string, { bg: string; fg: string }> = {
  a: { bg: "#0B7A4B", fg: "#ffffff" }, b: { bg: "#6FA032", fg: "#ffffff" },
  c: { bg: "#DFA918", fg: "#ffffff" }, d: { bg: "#CF6A1C", fg: "#ffffff" },
  e: { bg: "#BF3B21", fg: "#ffffff" }, na: { bg: "#20344c", fg: "#8fa6c2" },
};
const gr = (g: string) => GRADE[g === "insufficient_data" ? "na" : g.toLowerCase()] ?? GRADE.na;
const lt = (g: string) => (g === "insufficient_data" ? "–" : g);
const esc = (s: any) => String(s ?? "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]!));
const clip = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + "…" : s);
const twoLines = (s: string) => { const i = s.indexOf(" "); return i < 0 ? [s, ""] : [s.slice(0, i), s.slice(i + 1)]; };

const ICON: Record<string, string> = {
  energy: '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
  water: '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
  land: '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6"/>',
  local: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  transparency: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
};
const pIcon = (k: string, x: number, y: number) =>
  `<g transform="translate(${x},${y}) scale(0.75)" fill="none" stroke="#8fa6c2" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICON[k]}</g>`;
const PILLARS: [string, string, string][] = [
  ["energy", "Énergie", "energy"], ["water", "Eau", "water"], ["land_biodiversity", "Foncier", "land"],
  ["local_impact", "Impact", "local"], ["transparency_governance", "Transp.", "transparency"],
];
const STATUS: Record<string, string> = { announced: "Annoncé", permitting: "En instruction", under_construction: "En construction", operational: "En service" };

// Brand icon (smdc-icon.svg inlined), scaled to 46px on the navy card.
const BRAND_ICON = `<g transform="translate(64,56) scale(0.71875)">
  <rect width="64" height="64" rx="14" fill="#102A43"/>
  <rect x="10" y="20" width="10" height="26" rx="2.5" fill="#fff" opacity="0.85"/>
  <rect x="44" y="20" width="10" height="26" rx="2.5" fill="#fff" opacity="0.85"/>
  <rect x="23" y="12" width="18" height="34" rx="3" fill="#fff"/>
  <rect x="27" y="18" width="10" height="2.5" rx="1.25" fill="#102A43"/><rect x="27" y="25" width="10" height="2.5" rx="1.25" fill="#102A43"/>
  <rect x="27" y="32" width="10" height="2.5" rx="1.25" fill="#102A43"/><rect x="27" y="39" width="10" height="2.5" rx="1.25" fill="#102A43"/>
  <rect x="11" y="50" width="7.2" height="5" rx="1.8" fill="#0B7A4B"/><rect x="19.7" y="50" width="7.2" height="5" rx="1.8" fill="#6FA032"/>
  <rect x="28.4" y="50" width="7.2" height="5" rx="1.8" fill="#DFA918"/><rect x="37.1" y="50" width="7.2" height="5" rx="1.8" fill="#CF6A1C"/>
  <rect x="45.8" y="50" width="7.2" height="5" rx="1.8" fill="#BF3B21"/>
</g>`;

// The project name never gets truncated: it fits on one line if it can, else
// shrinks, else wraps to two balanced lines. cap ≈ 26 chars × 58px, the widest
// that fits the left column before the badges (x=800).
function nameBlock(raw: string): string {
  const cap = 1508;
  const T = (y: number, size: number, s: string) =>
    `<text x="62" y="${y}" font-family="Chivo" font-weight="900" font-size="${size}" letter-spacing="-1" fill="#fff">${esc(s)}</text>`;
  const len = raw.length;
  let size = Math.min(58, Math.floor(cap / Math.max(len, 1)));
  if (size >= 38) return T(242, size, raw);
  const mid = Math.floor(len / 2);
  const before = raw.lastIndexOf(" ", mid);
  const after = raw.indexOf(" ", mid);
  let split = before;
  if (after > 0 && (before < 0 || after - mid < mid - before)) split = after;
  if (split < 0) return T(242, Math.max(size, 30), raw); // no break point
  const l1 = raw.slice(0, split), l2 = raw.slice(split + 1);
  size = Math.min(48, Math.floor(cap / Math.max(l1.length, l2.length, 1)));
  const lh = Math.round(size * 1.02);
  return T(226, size, l1) + T(226 + lh, size, l2);
}

function dualBadge(x: number, y: number, grade: string, label: string, doc: string): string {
  const c = gr(grade);
  const [l1, l2] = twoLines(doc);
  return `<rect x="${x}" y="${y}" width="118" height="118" rx="18" fill="${c.bg}"/>` +
    `<text x="${x + 59}" y="${y + 59}" font-family="Chivo" font-weight="900" font-size="72" fill="${c.fg}" text-anchor="middle" dominant-baseline="central">${lt(grade)}</text>` +
    `<text x="${x + 134}" y="${y + 42}" font-family="Chivo Mono" font-weight="600" font-size="13" letter-spacing="1" fill="#8fa6c2">${esc(label)}</text>` +
    `<text x="${x + 134}" y="${y + 70}" font-family="Chivo" font-weight="700" font-size="19" fill="#fff">${esc(l1)}</text>` +
    (l2 ? `<text x="${x + 134}" y="${y + 92}" font-family="Chivo" font-weight="700" font-size="19" fill="#fff">${esc(l2)}</text>` : "");
}

function card(dc: any): string {
  const d = dc.score_history?.[dc.score_history.length - 1]?.date;
  const dateFr = d ? d.split("-").reverse().join("/") : "";
  const place = [dc.municipality, dc.admin_area ? `(${dc.admin_area})` : "", dc.country].filter(Boolean).join(" ");
  const kicker = ["Fiche projet", place, dc.power_mw ? `${dc.power_mw} MW` : ""].filter(Boolean).join(" · ");
  const strip = PILLARS.map(([id, label, ic], i) => {
    const x = 64 + i * 60, g = dc.pillars?.[id]?.grade ?? "insufficient_data", c = gr(g);
    return pIcon(ic, x + 17, 300) +
      `<text x="${x + 26}" y="333" font-family="Chivo Mono" font-weight="600" font-size="11" fill="#8fa6c2" text-anchor="middle" letter-spacing="0.5">${esc(label).toUpperCase()}</text>` +
      `<rect x="${x}" y="340" width="52" height="46" rx="8" fill="${c.bg}"/>` +
      `<text x="${x + 26}" y="363" font-family="Chivo" font-weight="900" font-size="26" fill="${c.fg}" text-anchor="middle" dominant-baseline="central">${lt(g)}</text>`;
  }).join("");
  const site = dc.grades.site, pp = dc.grades.project_process;
  const siteDoc = site.documentation?.label?.fr ?? "";
  const ppDoc = pp.grade === "insufficient_data" ? "données insuffisantes" : (pp.documentation?.label?.fr ?? "");
  return `<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <rect width="1200" height="630" fill="#102A43"/>
  ${BRAND_ICON}
  <text x="124" y="78" font-family="Chivo" font-weight="700" font-size="24" fill="#fff">Score<tspan fill="#8FA6C2">My</tspan>DataCenter</text>
  <text x="124" y="98" font-family="Chivo Mono" font-size="13" fill="#8fa6c2">observatoire indépendant</text>
  ${dateFr ? `<text x="1136" y="86" font-family="Chivo Mono" font-size="15" fill="#c6d3e2" text-anchor="end">Scoré le ${esc(dateFr)}</text>` : ""}

  <text x="64" y="182" font-family="Chivo Mono" font-weight="600" font-size="15" letter-spacing="1.8" fill="#8fa6c2">${esc(clip(kicker, 48)).toUpperCase()}</text>
  ${nameBlock(dc.name)}
  ${strip}
  <text x="64" y="410" font-family="Chivo Mono" font-size="11" fill="#8fa6c2"><tspan fill="#c6d3e2">●●●○</tspan> = documentation disponible par pilier</text>

  ${dualBadge(800, 180, site.grade, "NOTE DU SITE", siteDoc)}
  ${dualBadge(800, 314, pp.grade, "NOTE PROJET & PROCESSUS", ppDoc)}

  <line x1="64" y1="536" x2="1136" y2="536" stroke="#ffffff" stroke-opacity="0.14"/>
  <text x="64" y="572" font-family="Chivo" font-weight="500" font-size="18" fill="#c6d3e2">« ${esc(clip(dc.citable_quote?.fr ?? "", 62))} »</text>
  <text x="1136" y="572" font-family="Chivo Mono" font-size="14" fill="#8fa6c2" text-anchor="end">scoremydatacenter.org</text>
</svg>`;
}

export function getStaticPaths() {
  const modules = import.meta.glob("../../../../public/data/dc/*.json", { eager: true });
  return Object.values(modules).map((m: any) => ({ params: { id: m.default.id }, props: { dc: m.default } }));
}

export const GET: APIRoute = ({ props }) => {
  const png = new Resvg(card((props as any).dc), {
    fitTo: { mode: "width", value: 1200 },
    font: { fontFiles: FONT_FILES, loadSystemFonts: false, defaultFontFamily: "Chivo" },
  }).render().asPng();
  return new Response(png, { headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=3600" } });
};
