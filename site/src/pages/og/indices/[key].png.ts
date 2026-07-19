// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// One OG card PER COUNTRY (« La France note C — indice site », brief §2.1).
// Byte-stable between index events (§1 bis): every figure on the card comes
// from the country's LAST EVENT in indices_history.json (grade, score, n,
// date) — never from the continuous score that drifts at every build. The
// reading insert is part of the card (non-detachable, amendement 2026-07-19):
// « notes de SITES » ships on every rendering surface, OG included.
import type { APIRoute } from "astro";
import { Resvg } from "@resvg/resvg-js";
import { join } from "node:path";
import indicesData from "../../../../public/data/indices.json";
import historyData from "../../../../public/data/indices_history.json";
import { COUNTRY_NAMES } from "../../../config/indices";

type Lang = "fr" | "en";
const INDICES = indicesData as any;
const HISTORY = historyData as any[];

const fontDir = join(process.cwd(), "src/og/fonts");
const FONT_FILES = ["chivo-900.ttf", "chivo-700.ttf", "chivo-mono-400.ttf", "chivo-mono-600.ttf"].map((f) => join(fontDir, f));

const esc = (s: any) => String(s ?? "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]!));

const GRADE_FILL: Record<string, string> = {
  A: "#0B7A4B", B: "#6FA032", C: "#DFA918", D: "#CF6A1C", E: "#BF3B21",
};

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

const T = {
  fr: {
    kicker: "indice site par pays",
    notes: (name: string, grade: string) => `${name} note ${grade} — indice site`,
    reserved: "A réservé — sans exploitation vérifiée dans le pays (A-25)",
    veille: (name: string) => `${name} — en veille`,
    veilleSub: (n: number) => `n = ${n} < 5 sites notés : moyenne non calculée`,
    insert: ["Cet indice agrège les notes de SITES (réseau, eau, foncier, risques).",
             "Il ne note ni les opérateurs ni la conduite des projets."],
    doc: { solide: "doc solide", moyenne: "doc moyenne", faible: "doc faible" },
    asOf: "indice au",
  },
  en: {
    kicker: "country site index",
    notes: (name: string, grade: string) => `${name} grades ${grade} — site index`,
    reserved: "A reserved — no verified operations in the country (A-25)",
    veille: (name: string) => `${name} — on watch`,
    veilleSub: (n: number) => `n = ${n} < 5 scored sites: no mean computed`,
    insert: ["This index aggregates SITE grades (grid, water, land, hazards).",
             "It grades neither operators nor how projects are run."],
    doc: { solide: "solid doc", moyenne: "medium doc", faible: "weak doc" },
    asOf: "index as of",
  },
};

function lastEvent(iso: string) {
  let ev = null;
  for (const e of HISTORY) if (e.country === iso) ev = e;
  return ev;
}

function card(lang: Lang, iso: string): string {
  const t = T[lang];
  const entry = INDICES.countries[iso];
  const ev = lastEvent(iso);
  const name = (COUNTRY_NAMES as any)[iso]?.[lang] ?? iso;
  const dfmt = (d: string) => (lang === "fr" ? d.split("-").reverse().join("/") : d);
  // §1 bis: figures FROM THE EVENT — the card only changes when the country moves.
  const evDate = ev ? dfmt(ev.date) : "";
  const grade = ev?.to?.grade ?? null;
  const score = ev?.to?.score ?? null;
  const n = ev?.to?.n ?? entry?.n ?? 0;
  const scoreTxt = score === null ? "" : (lang === "fr" ? String(score).replace(".", ",") : String(score));
  const reserved = entry?.reserved_from === "A";
  const doc = entry?.documentation;

  const title = grade ? t.notes(name, grade) : t.veille(name);
  const docTxt = doc ? ` · ${(t.doc as any)[doc.band]}` : "";
  const sub = grade
    ? (reserved ? t.reserved : `${scoreTxt} / 100 · n = ${n}${docTxt}`)
    : t.veilleSub(n);
  const sub2 = grade && reserved ? `${scoreTxt} / 100 · n = ${n}${docTxt}` : null;
  const fill = grade ? GRADE_FILL[grade] : "#3a5474";
  const letter = grade ?? "–";

  const meta = [`${t.asOf} ${evDate}`, `${lang === "fr" ? "méthodo" : "methodology"} v${INDICES.methodology_version}`]
    .filter(Boolean).join(" · ");

  return `<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <rect width="1200" height="630" fill="#102A43"/>
  ${BRAND_ICON}
  <text x="124" y="78" font-family="Chivo" font-weight="700" font-size="24" fill="#fff">Score<tspan fill="#8FA6C2">My</tspan>DataCenter</text>
  <text x="124" y="98" font-family="Chivo Mono" font-size="13" fill="#8fa6c2">${esc(t.kicker)}</text>

  <rect x="64" y="170" width="240" height="240" rx="36" fill="${fill}"/>
  <text x="184" y="352" font-family="Chivo" font-weight="900" font-size="180" fill="#ffffff" text-anchor="middle">${esc(letter)}</text>
  ${reserved ? `<rect x="64" y="418" width="240" height="34" rx="17" fill="#1b3a5c" stroke="#3a5474"/>
  <text x="184" y="441" font-family="Chivo Mono" font-weight="600" font-size="16" fill="#c6d3e2" text-anchor="middle">${lang === "fr" ? "B · A réservé" : "B · A reserved"}</text>` : ""}

  <text x="352" y="252" font-family="Chivo" font-weight="900" font-size="52" fill="#ffffff">${esc(title)}</text>
  <text x="352" y="308" font-family="Chivo" font-weight="700" font-size="28" fill="#e7edf5">${esc(sub)}</text>
  ${sub2 ? `<text x="352" y="350" font-family="Chivo" font-weight="700" font-size="24" fill="#c6d3e2">${esc(sub2)}</text>` : ""}

  <text x="352" y="430" font-family="Chivo" font-size="21" fill="#8fa6c2">${esc(t.insert[0])}</text>
  <text x="352" y="460" font-family="Chivo" font-size="21" fill="#8fa6c2">${esc(t.insert[1])}</text>

  <line x1="64" y1="546" x2="1136" y2="546" stroke="#ffffff" stroke-opacity="0.14"/>
  <text x="64" y="580" font-family="Chivo Mono" font-size="15" fill="#8fa6c2">${esc(meta)}</text>
  <text x="1136" y="580" font-family="Chivo Mono" font-size="15" fill="#8fa6c2" text-anchor="end">scoremydatacenter.org</text>
</svg>`;
}

export function getStaticPaths() {
  const paths: { params: { key: string }; props: { lang: Lang; iso: string } }[] = [];
  for (const lang of ["fr", "en"] as Lang[]) {
    for (const iso of Object.keys(INDICES.countries)) {
      paths.push({ params: { key: `${lang}-${iso.toLowerCase()}` }, props: { lang, iso } });
    }
  }
  return paths;
}

export const GET: APIRoute = ({ props }) => {
  const { lang, iso } = props as { lang: Lang; iso: string };
  const png = new Resvg(card(lang, iso), {
    fitTo: { mode: "width", value: 1200 },
    font: { fontFiles: FONT_FILES, loadSystemFonts: false, defaultFontFamily: "Chivo" },
  }).render().asPng();
  return new Response(png, { headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=3600" } });
};
