#!/usr/bin/env node
// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
//
// GRADE-WITHHELD SCRUB — leak-safety gate, runs BEFORE every `astro build`.
// A site shown WITHOUT a published grade is only truly withheld if its internal
// grade appears NOWHERE in the served output. The grade is baked into three
// consolidated artifacts (scores.json → ranking, map.geojson → map, the per-site
// dc/*.json → fiches/OG). This script blanks it to the sentinel "en_attente"
// across all three, in place. Idempotent. The real grade stays only in the
// pipeline's private newsroom — never in what we ship.
//
// 🔴 DEUX POPULATIONS, UNE SEULE RÈGLE (Franck, 2026-10-16 : « la fiche a raison »).
// Ce script ne couvrait que la première, et la seconde fuyait en production :
//   (1) EN VEILLE — un pays de data/veille.json (Israël). Décision de publication.
//   (2) NOTE EN ATTENTE — la fiche affiche « note en attente » parce que sa bande
//       de couverture est plus large que le plancher irréductible (servable_band →
//       provisional_band.kind === "en_attente"). La fiche retirait la lettre ; le
//       CLASSEMENT et la CARTE la publiaient quand même. Mesuré le 2026-10-16 :
//       18 fiches, dont Google Bissen affiché « note en attente » sur sa page et
//       « Site D · dans les 3 % les moins bien notés » au classement. Même site,
//       deux affirmations publiques contradictoires, sur un opérateur nommé.
// La règle tranchée : une lettre qu'on refuse de montrer sur la fiche n'apparaît
// NULLE PART. La fiche est l'affichage vetté ; les agrégats la suivent.
//
// ⚠️ Et la lettre n'est pas seule : le SCORE la redonne. Les seuils de notation
// sont publics, donc servir 38,7 en retirant le « D » ne retire rien du tout.
// Chaque blanchiment retire la lettre ET son score — c'est déjà ce que faisait ce
// script pour la veille, c'est pour ça qu'on élargit son déclencheur au lieu
// d'écrire un second mécanisme à côté.

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

// Déclencheur (2) : la fiche elle-même dit « note en attente ». Lu sur l'artefact
// servi, pas recalculé ici — le moteur est seul juge de la bande (servable_band),
// ce script ne fait que propager SA décision aux agrégats.
const isBandWithheld = (o) => o?.provisional_band?.kind === SENTINEL;
const isWithheld = (o) => isEnVeille(o) || isBandWithheld(o);

let scrubbedIds = new Set();
let bandIds = new Set();        // population (2), pour un log qui distingue les deux
let counts = { dc: 0, scores: 0, geojson: 0, indices: 0, bands: 0 };

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
    if (!isWithheld(dc)) continue;
    scrubbedIds.add(dc.id);
    if (!isEnVeille(dc)) bandIds.add(dc.id);
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
    // 🔴 HIÉRARCHIE : PUBLICATION > AFFICHAGE. Une fiche EN VEILLE perd aussi sa bande.
    // Le champ `provisional_band` ne portait rien de lisible tant que la fenêtre large était
    // muette, donc personne ne le blanchissait. La règle C-bis lui fait porter la note
    // PROBABLE — et une règle d'affichage n'a jamais eu mandat de rouvrir une décision de
    // publication signée (data/veille.json : « editing this file is a publication decision —
    // Franck signs »). Sans cette ligne, la fiche israélienne de Kfar Yona (pipeline, donc
    // elle a une bande) ressortirait sa lettre au premier build après C-bis.
    // Retiré en entier, pas rogné : la fiche retombe sur la puce neutre, qui est l'état voulu.
    // ⚠️ NE S'APPLIQUE QU'À LA POPULATION (1). Une fiche « note en attente » hors veille garde
    // sa bande : ce qu'elle a le droit d'y montrer est un arbitrage d'affichage, pas de
    // publication — et il est ouvert.
    if (isEnVeille(dc) && dc.provisional_band) { delete dc.provisional_band; changed = true; counts.bands++; }
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
    // `en_veille` reste réservé à la population (1) : une fiche « note en attente »
    // n'est PAS en veille, et poser le drapeau sur elle écrirait un fait faux dans
    // un fichier public. La lettre blanchie suffit à dire ce qu'il y a à dire.
    if (isEnVeille(pr) || !bandIds.has(pr.id)) pr.en_veille = true;
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
  `[scrub-grades] retenues: ${scrubbedIds.size} (veille ${scrubbedIds.size - bandIds.size} + note-en-attente ${bandIds.size})`
  + ` | blanchi → dc:${counts.dc} scores:${counts.scores} geojson:${counts.geojson} bandes-veille:${counts.bands} indices:${counts.indices} stats-perimeters:${counts.stats || 0}`
);

// ── GARDE DE SORTIE ───────────────────────────────────────────────────────────
// Le scrub ci-dessus écrit ; ce bloc RELIT ce qui vient d'être écrit et refuse le
// build si une lettre a survécu quelque part. Sans lui, la prochaine clé ajoutée à
// un artefact (un `grade` dans un champ neuf, un historique, un résumé) rouvrirait
// la fuite en silence — exactement ce qui vient de se produire : le mécanisme de
// bande est arrivé APRÈS ce script, et personne n'a vérifié que les deux
// s'accordaient. Un garde qui ne relit pas sa propre sortie ne garde rien.
const LETTER = /^[A-E]$/;
const leaks = [];
const seenLetter = (where, id, val) => { if (LETTER.test(val ?? "")) leaks.push(`${where} ${id} = ${val}`); };

if (existsSync(scoresPath)) {
  for (const r of JSON.parse(readFileSync(scoresPath, "utf8"))) {
    if (!scrubbedIds.has(r.id)) continue;
    seenLetter("scores.json/site", r.id, r.grades?.site?.grade);
    seenLetter("scores.json/projet", r.id, r.grades?.project_process?.grade);
    if (typeof r.grades?.site?.score === "number") leaks.push(`scores.json/score ${r.id} = ${r.grades.site.score}`);
    for (const [k, v] of Object.entries(r.pillars ?? {})) seenLetter(`scores.json/pilier:${k}`, r.id, v?.grade);
  }
}
if (existsSync(geoPath)) {
  for (const f of JSON.parse(readFileSync(geoPath, "utf8")).features ?? []) {
    if (scrubbedIds.has(f.properties?.id)) seenLetter("map.geojson", f.properties.id, f.properties.grade_site);
  }
}
if (existsSync(DC_DIR)) {
  for (const f of readdirSync(DC_DIR)) {
    if (!f.endsWith(".json")) continue;
    let dc; try { dc = JSON.parse(readFileSync(join(DC_DIR, f), "utf8")); } catch { continue; }
    if (!scrubbedIds.has(dc.id)) continue;
    seenLetter("dc/site", dc.id, dc.grades?.site?.grade);
    seenLetter("dc/projet", dc.id, dc.grades?.project_process?.grade);
    if (typeof dc.grades?.site?.score === "number") leaks.push(`dc/score ${dc.id} = ${dc.grades.site.score}`);
    for (const [k, v] of Object.entries(dc.pillars ?? {})) seenLetter(`dc/pilier:${k}`, dc.id, v?.grade);
    for (const h of dc.score_history ?? []) seenLetter("dc/historique", dc.id, h?.grades?.site);
    // Population (1) seulement : une fiche en veille ne garde AUCUNE bande, puisque la bande
    // porte des lettres depuis C-bis. Une fiche « note en attente » hors veille en garde une —
    // ce qu'elle a le droit d'y afficher ne se tranche pas ici.
    if (isEnVeille(dc) && dc.provisional_band) leaks.push(`dc/bande ${dc.id} = ${JSON.stringify(dc.provisional_band).slice(0, 60)}`);
  }
}
if (leaks.length) {
  console.error(
    `[scrub-grades] FUITE — ${leaks.length} note(s) retenue(s) encore servie(s). Le build est refusé :\n  - `
    + leaks.slice(0, 20).join("\n  - ") + (leaks.length > 20 ? `\n  … et ${leaks.length - 20} autres` : "")
  );
  process.exit(1);
}
console.log(`[scrub-grades] garde OK — aucune lettre servie pour les ${scrubbedIds.size} fiches retenues.`);
