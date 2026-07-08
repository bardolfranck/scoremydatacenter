// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Per-DC Open Graph card (1200×630) rendered at build: the score card a
// journalist shares. Hand-built SVG → PNG via resvg (no headless browser). A
// grade only ever appears here as the dual badge + the pillar strip; the card is
// the offline twin of the fiche's screenshot zone.
import type { APIRoute } from "astro";
import { Resvg } from "@resvg/resvg-js";
import { readFileSync } from "node:fs";
import { join } from "node:path";

// Build-time only (astro build cwd = the site root); fonts are not served.
const font = (f: string) => readFileSync(join(process.cwd(), "src/og/fonts", f));
const FONTS = [font("chivo-900.ttf"), font("chivo-700.ttf"), font("chivo-mono-400.ttf"), font("chivo-mono-600.ttf")];

const GRADE = {
  a: { bg: "#0B7A4B", fg: "#ffffff" }, b: { bg: "#6FA032", fg: "#102A43" },
  c: { bg: "#DFA918", fg: "#102A43" }, d: { bg: "#CF6A1C", fg: "#102A43" },
  e: { bg: "#BF3B21", fg: "#ffffff" }, na: { bg: "#20344c", fg: "#8fa6c2" },
} as const;
const g = (grade: string) => GRADE[(grade === "insufficient_data" ? "na" : grade.toLowerCase()) as keyof typeof GRADE] ?? GRADE.na;
const letter = (grade: string) => (grade === "insufficient_data" ? "–" : grade);
const PILLARS = [["energy", "Énergie"], ["water", "Eau"], ["land_biodiversity", "Foncier"], ["local_impact", "Local"], ["transparency_governance", "Transp."]];
const STATUS: Record<string, string> = { announced: "Annoncé", permitting: "En instruction", under_construction: "En construction", operational: "En service" };
const esc = (s: string) => String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]!));
const clip = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

function chip(x: number, y: number, s: number, grade: string, fs: number, r = 12) {
  const c = g(grade);
  return `<rect x="${x}" y="${y}" width="${s}" height="${s}" rx="${r}" fill="${c.bg}"/>` +
    `<text x="${x + s / 2}" y="${y + s / 2}" font-family="Chivo" font-weight="900" font-size="${fs}" fill="${c.fg}" text-anchor="middle" dominant-baseline="central">${letter(grade)}</text>`;
}

function card(dc: any): string {
  const place = [dc.municipality, dc.admin_area ? `(${dc.admin_area})` : "", dc.country].filter(Boolean).join(" ");
  const meta = [STATUS[dc.project_status] ?? dc.project_status, dc.power_mw ? `${dc.power_mw} MW` : ""].filter(Boolean).join(" · ");
  const pill = PILLARS.map(([id, label], i) => {
    const x = 64 + i * 120, gr = dc.pillars?.[id]?.grade ?? "insufficient_data";
    return `<text x="${x + 28}" y="466" font-family="Chivo Mono" font-size="16" fill="#8fa6c2" text-anchor="middle">${esc(label)}</text>` + chip(x, 476, 56, gr, 30, 8);
  }).join("");
  const site = dc.grades.site, pp = dc.grades.project_process;
  const siteDoc = site.documentation?.label?.fr ?? "";
  const ppDoc = pp.grade === "insufficient_data" ? "données insuffisantes" : (pp.documentation?.label?.fr ?? "");
  return `<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <rect width="1200" height="630" fill="#102A43"/>
  <text x="64" y="92" font-family="Chivo" font-weight="900" font-size="30" fill="#ffffff">Score<tspan fill="#8FA6C2">My</tspan>DataCenter</text>
  <text x="1136" y="90" font-family="Chivo Mono" font-size="20" fill="#8fa6c2" text-anchor="end">scoremydatacenter.org</text>
  <text x="64" y="188" font-family="Chivo Mono" font-weight="600" font-size="20" fill="#8fa6c2" letter-spacing="2">FICHE PROJET · ${esc(clip(place, 40)).toUpperCase()}</text>
  <text x="62" y="252" font-family="Chivo" font-weight="900" font-size="58" fill="#ffffff">${esc(clip(dc.name, 26))}</text>
  <text x="64" y="300" font-family="Chivo Mono" font-size="22" fill="#c6d3e2">${esc(meta)}</text>
  ${pill}
  <rect x="64" y="556" width="1072" height="1" fill="#20344c"/>
  <text x="64" y="590" font-family="Chivo" font-weight="700" font-size="26" fill="#ffffff">« ${esc(clip(dc.citable_quote?.fr ?? "", 78))} »</text>
  <g transform="translate(772,150)">
    ${chip(0, 0, 112, site.grade, 64)}
    <text x="130" y="40" font-family="Chivo Mono" font-weight="600" font-size="17" fill="#8fa6c2">NOTE DU SITE</text>
    <text x="130" y="72" font-family="Chivo" font-weight="700" font-size="23" fill="#ffffff">${esc(clip(siteDoc, 24))}</text>
    ${chip(0, 152, 112, pp.grade, 64)}
    <text x="130" y="192" font-family="Chivo Mono" font-weight="600" font-size="17" fill="#8fa6c2">NOTE PROJET &amp; PROCESSUS</text>
    <text x="130" y="224" font-family="Chivo" font-weight="700" font-size="23" fill="#ffffff">${esc(clip(ppDoc, 24))}</text>
  </g>
</svg>`;
}

export function getStaticPaths() {
  const modules = import.meta.glob("../../../../public/data/dc/*.json", { eager: true });
  return Object.values(modules).map((m: any) => ({ params: { id: m.default.id }, props: { dc: m.default } }));
}

export const GET: APIRoute = ({ props }) => {
  const dc = (props as any).dc;
  dc._scored = dc.score_history?.[dc.score_history.length - 1]?.date ?? "";
  const png = new Resvg(card(dc), {
    fitTo: { mode: "width", value: 1200 },
    font: { fontBuffers: FONTS, loadSystemFonts: false, defaultFontFamily: "Chivo" },
  }).render().asPng();
  return new Response(png, { headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=3600" } });
};
