// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// One OG card PER STAT (T0, cadrage §4.10): every figure is shareable alone.
// Navy field, huge tabular number with the gold underline, neutral phrase,
// VISIBLE perimeter badge, n + corpus date + methodology version. Same
// resvg/Chivo chain as the per-DC cards (fontFiles, never fontBuffers).
import type { APIRoute } from "astro";
import { Resvg } from "@resvg/resvg-js";
import { join } from "node:path";
import {
  STATS, T, perimeterLabel, statView, displayableStats, fmtInt,
  type Lang,
} from "../../../config/stats";

const fontDir = join(process.cwd(), "src/og/fonts");
const FONT_FILES = ["chivo-900.ttf", "chivo-700.ttf", "chivo-mono-400.ttf", "chivo-mono-600.ttf"].map((f) => join(fontDir, f));

const esc = (s: any) => String(s ?? "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]!));

const BRAND_ICON = `<g transform="translate(64,56) scale(0.71875)">
  <rect width="64" height="64" rx="14" fill="#1b3a5c"/>
  <rect x="10" y="20" width="10" height="26" rx="2.5" fill="#fff" opacity="0.85"/>
  <rect x="44" y="20" width="10" height="26" rx="2.5" fill="#fff" opacity="0.85"/>
  <rect x="23" y="12" width="18" height="34" rx="3" fill="#fff"/>
  <rect x="27" y="18" width="10" height="2.5" rx="1.25" fill="#102A43"/><rect x="27" y="25" width="10" height="2.5" rx="1.25" fill="#102A43"/>
  <rect x="27" y="32" width="10" height="2.5" rx="1.25" fill="#102A43"/><rect x="27" y="39" width="10" height="2.5" rx="1.25" fill="#102A43"/>
  <rect x="11" y="50" width="7.2" height="5" rx="1.8" fill="#0B7A4B"/><rect x="19.7" y="50" width="7.2" height="5" rx="1.8" fill="#6FA032"/>
  <rect x="28.4" y="50" width="7.2" height="5" rx="1.8" fill="#DFA918"/><rect x="37.1" y="50" width="7.2" height="5" rx="1.8" fill="#CF6A1C"/>
  <rect x="45.8" y="50" width="7.2" height="5" rx="1.8" fill="#BF3B21"/>
</g>`;

function wrap(text: string, max: number, maxLines: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let cur = "";
  for (const w of words) {
    if ((cur + " " + w).trim().length > max && cur) {
      lines.push(cur);
      cur = w;
      if (lines.length === maxLines - 1) break;
    } else cur = (cur + " " + w).trim();
  }
  const used = lines.join(" ").split(" ").filter(Boolean).length;
  const rest = words.slice(used).join(" ");
  lines.push(rest.length > max ? rest.slice(0, max - 1) + "…" : rest);
  return lines.filter(Boolean);
}

function card(lang: Lang, perimeter: string, statId: string): string {
  const t = T[lang];
  const peri = STATS.perimeters[perimeter];
  const view = statView(peri, statId, lang)!;
  const badgeText = perimeter === "europe"
    ? (view.countries.length === 1 && view.countries[0] === "FR"
        ? t.franceOnly
        : t.countriesOn(view.countries.length, peri.countries.length))
    : perimeterLabel(perimeter, lang);
  const phrase = wrap(view.phrase, 44, 3);
  const big = view.big;
  const bigSize = big.length <= 5 ? 190 : big.length <= 8 ? 150 : 110;
  const meta = [
    `n = ${fmtInt(view.n, lang)}`,
    STATS.corpus_date ?? "",
    `${t.methodo} v${STATS.methodology_version}`,
  ].filter(Boolean).join(" · ");
  const badgeW = 24 + badgeText.length * 12;
  return `<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <rect width="1200" height="630" fill="#102A43"/>
  ${BRAND_ICON}
  <text x="124" y="78" font-family="Chivo" font-weight="700" font-size="24" fill="#fff">Score<tspan fill="#8FA6C2">My</tspan>DataCenter</text>
  <text x="124" y="98" font-family="Chivo Mono" font-size="13" fill="#8fa6c2">${lang === "fr" ? "les chiffres du parc" : "fleet figures"}</text>
  <rect x="${1136 - badgeW}" y="52" width="${badgeW}" height="42" rx="21" fill="#1b3a5c" stroke="#3a5474"/>
  <text x="${1136 - badgeW / 2}" y="79" font-family="Chivo Mono" font-weight="600" font-size="18" fill="#c6d3e2" text-anchor="middle">${esc(badgeText)}</text>

  <text x="64" y="${170 + bigSize}" font-family="Chivo" font-weight="900" font-size="${bigSize}" letter-spacing="-4" fill="#ffffff">${esc(big)}</text>
  <rect x="66" y="${186 + bigSize}" width="${Math.min(big.length * bigSize * 0.52, 1000)}" height="14" rx="4" fill="#DFA918" opacity="0.75"/>

  ${phrase.map((line, i) =>
    `<text x="64" y="${262 + bigSize + i * 42}" font-family="Chivo" font-weight="700" font-size="31" fill="#e7edf5">${esc(line)}</text>`).join("\n  ")}

  <line x1="64" y1="546" x2="1136" y2="546" stroke="#ffffff" stroke-opacity="0.14"/>
  <text x="64" y="580" font-family="Chivo Mono" font-size="15" fill="#8fa6c2">${esc(meta)}</text>
  <text x="1136" y="580" font-family="Chivo Mono" font-size="15" fill="#8fa6c2" text-anchor="end">scoremydatacenter.org</text>
</svg>`;
}

export function getStaticPaths() {
  const paths: { params: { key: string }; props: { lang: Lang; perimeter: string; statId: string } }[] = [];
  for (const lang of ["fr", "en"] as Lang[]) {
    for (const perimeter of Object.keys(STATS.perimeters)) {
      const peri = STATS.perimeters[perimeter];
      for (const statId of displayableStats(peri)) {
        paths.push({
          params: { key: `${lang}-${perimeter.toLowerCase()}-${statId}` },
          props: { lang, perimeter, statId },
        });
      }
    }
  }
  return paths;
}

export const GET: APIRoute = ({ props }) => {
  const { lang, perimeter, statId } = props as { lang: Lang; perimeter: string; statId: string };
  const png = new Resvg(card(lang, perimeter, statId), {
    fitTo: { mode: "width", value: 1200 },
    font: { fontFiles: FONT_FILES, loadSystemFonts: false, defaultFontFamily: "Chivo" },
  }).render().asPng();
  return new Response(png, { headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=3600" } });
};
