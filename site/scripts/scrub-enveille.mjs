#!/usr/bin/env node
// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
//
// EN-VEILLE SCRUB — leak-safety gate, runs BEFORE every `astro build`.
// A site can be shown "en veille" (visible, no published grade) only if its
// internal grade appears NOWHERE in the served output. The grade is baked into
// three consolidated artifacts (scores.json → ranking, map.geojson → map, the
// per-site dc/*.json → fiches/OG). This script blanks the PUBLIC grade of every
// en-veille site (publication_status !== "published") to the sentinel
// "en_attente" across all three, in place. Idempotent: re-running on already
// scrubbed data is a no-op. The real grade stays only in the pipeline's private
// newsroom — never in what we ship.

import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = join(HERE, "..", "public", "data");
const DC_DIR = join(DATA, "dc");
const SENTINEL = "en_attente";

// En-veille = sites shown WITHOUT a published grade (visible, "note en attente").
// NOTE: publication_status is "draft" for the WHOLE corpus (the site never used
// it) — it is NOT the discriminant. Until the pipeline emits a dedicated flag,
// en-veille = a whitelisted country (Israel now; Gulf next). Prefer an explicit
// per-site flag when the pipeline provides one.
// Single source of truth: data/veille.json (also read by engine/stats.py for the
// named counts). Fallback to the historical constant if the file is absent.
let veilleCountries = ["IL"];
try {
  const veilleCfg = JSON.parse(readFileSync(join(HERE, "..", "..", "data", "veille.json"), "utf8"));
  if (Array.isArray(veilleCfg.countries)) veilleCountries = veilleCfg.countries;
} catch { /* keep fallback */ }
const EN_VEILLE_COUNTRIES = new Set(veilleCountries);
const isEnVeille = (o) =>
  o?.en_veille === true ||
  o?.publication_status === "en_veille" ||
  EN_VEILLE_COUNTRIES.has(o?.country);

let scrubbedIds = new Set();
let counts = { dc: 0, scores: 0, geojson: 0, indices: 0 };

// Pillar sub-grades are notes too — a lone "land: B" on an en-veille fiche leaks
// the assessment we withhold. Blank every A–E pillar letter + its score.
function scrubPillars(obj) {
  const p = obj?.pillars;
  if (!p || typeof p !== "object") return false;
  let changed = false;
  for (const k of Object.keys(p)) {
    const v = p[k];
    if (v && /^[A-E]$/.test(v.grade ?? "")) { v.grade = SENTINEL; delete v.score; changed = true; }
  }
  return changed;
}

// 1) Per-site fiches — source of truth for who is en-veille.
if (existsSync(DC_DIR)) {
  for (const f of readdirSync(DC_DIR)) {
    if (!f.endsWith(".json")) continue;
    const p = join(DC_DIR, f);
    let dc;
    try { dc = JSON.parse(readFileSync(p, "utf8")); } catch { continue; }
    if (!isEnVeille(dc)) continue;
    scrubbedIds.add(dc.id);
    let changed = false;
    if (dc.grades?.site && dc.grades.site.grade !== SENTINEL) {
      dc.grades.site.grade = SENTINEL;
      delete dc.grades.site.score;
      changed = true;
    }
    if (dc.grades?.project_process && dc.grades.project_process.grade && dc.grades.project_process.grade !== SENTINEL) {
      // keep insufficient_data as-is (already non-committal); only strip a real letter
      if (/^[A-E]$/.test(dc.grades.project_process.grade)) {
        dc.grades.project_process.grade = SENTINEL;
        delete dc.grades.project_process.score;
        changed = true;
      }
    }
    // grade history could re-expose the letter — blank letters there too
    if (Array.isArray(dc.score_history)) {
      for (const h of dc.score_history) {
        if (h?.grades) {
          if (/^[A-E]$/.test(h.grades.site ?? "")) { h.grades.site = SENTINEL; changed = true; }
          if (/^[A-E]$/.test(h.grades.project_process ?? "")) { h.grades.project_process = SENTINEL; changed = true; }
        }
      }
    }
    if (scrubPillars(dc)) changed = true;
    if (changed) { writeFileSync(p, JSON.stringify(dc, null, 2)); counts.dc++; }
  }
}

// 2) scores.json (ranking) — list of site rows.
const scoresPath = join(DATA, "scores.json");
if (existsSync(scoresPath)) {
  const rows = JSON.parse(readFileSync(scoresPath, "utf8"));
  let changed = false;
  for (const r of rows) {
    if (!scrubbedIds.has(r.id) && !isEnVeille(r)) continue;
    if (r.grades?.site && r.grades.site.grade !== SENTINEL) {
      r.grades.site.grade = SENTINEL; delete r.grades.site.score; changed = true; counts.scores++;
    }
    if (/^[A-E]$/.test(r.grades?.project_process?.grade ?? "")) {
      r.grades.project_process.grade = SENTINEL; delete r.grades.project_process.score; changed = true;
    }
    if (scrubPillars(r)) changed = true;
  }
  if (changed) writeFileSync(scoresPath, JSON.stringify(rows));
}

// 3) map.geojson (map pins + donut).
const geoPath = join(DATA, "map.geojson");
if (existsSync(geoPath)) {
  const geo = JSON.parse(readFileSync(geoPath, "utf8"));
  let changed = false;
  for (const feat of geo.features ?? []) {
    const pr = feat.properties ?? {};
    if (!scrubbedIds.has(pr.id) && !isEnVeille(pr)) continue;
    if (pr.grade_site && pr.grade_site !== SENTINEL) { pr.grade_site = SENTINEL; changed = true; counts.geojson++; }
    pr.en_veille = true;
  }
  if (changed) writeFileSync(geoPath, JSON.stringify(geo));
}

// 4) indices.json (country index) — defensive: never publish an aggregate grade
// for a country that is entirely en-veille.
const idxPath = join(DATA, "indices.json");
if (existsSync(idxPath)) {
  const idx = JSON.parse(readFileSync(idxPath, "utf8"));
  const countries = idx.countries ?? {};
  // a country whose every scored site is en-veille shouldn't surface a letter
  if (countries.IL && scrubbedIds.size) {
    // conservative: if IL appears and all our IL sites are en-veille, blank its grade
    if (countries.IL.grade && /^[A-E]$/.test(countries.IL.grade)) {
      countries.IL.grade = SENTINEL; delete countries.IL.score; countries.IL.en_veille = true; counts.indices++;
      writeFileSync(idxPath, JSON.stringify(idx));
    }
  }
}

// 5) stats.json — the per-country figures page (/figures/<cc>) is built around
// GRADES (exemplars labelled by grade, "most frequent grade", distribution).
// For an en-veille country we cannot show that. Drop the whole perimeter → no
// /figures/<cc> page is generated, and no exemplar/point grade can leak.
const statsPath = join(DATA, "stats.json");
if (existsSync(statsPath)) {
  const stats = JSON.parse(readFileSync(statsPath, "utf8"));
  const per = stats.perimeters ?? {};
  let changed = false;
  for (const cc of Array.from(EN_VEILLE_COUNTRIES)) {
    if (per[cc]) { delete per[cc]; changed = true; counts.stats = (counts.stats || 0) + 1; }
  }
  if (changed) writeFileSync(statsPath, JSON.stringify(stats));
}

console.log(
  `[scrub-enveille] en-veille sites: ${scrubbedIds.size} | scrubbed → dc:${counts.dc} scores:${counts.scores} geojson:${counts.geojson} indices:${counts.indices} stats-perimeters:${counts.stats || 0}`
);
