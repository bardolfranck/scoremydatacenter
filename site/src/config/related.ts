// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
//
// Internal-linking helper: for a given fiche, pick a handful of "related" sites
// so every fiche links to its neighbours. These are STATIC, crawlable <a> links —
// unlike the mini-map's client-side pins — which weave the 1,400+ fiches into a
// topical mesh (crawl paths + contextual relevance + real UX). Deterministic.
//
// Order of relevance (Franck 2026-09-22): same operator → same region (same country,
// see below) → CLOSEST BY DISTANCE. « Same country » was dropped as a relation: with
// ~1,300 French fiches it says nothing to a reader ("en quoi sont-elles voisines ?").
// Every item now carries the REASON it is there — the operator's name, the region, or
// the actual distance in km.

export interface DcLite {
  id: string;
  name: string;
  operator?: string;
  country?: string;
  admin_area?: string;
  municipality?: string;
  grade?: string;
  lat?: number;
  lon?: number;
}

export type Relation = "operator" | "region" | "nearby";
export interface Related extends DcLite {
  relation: Relation;
  /** Distance in km, present on the "nearby" relation only. */
  km?: number;
}

export function toLite(dc: any, coords?: Record<string, [number, number]>): DcLite {
  const c = coords?.[dc.id];
  return {
    id: dc.id,
    name: dc.name,
    operator: dc.operator ?? undefined,
    country: dc.country ?? undefined,
    admin_area: dc.admin_area ?? undefined,
    municipality: dc.municipality ?? undefined,
    grade: dc.grades?.site?.grade ?? undefined,
    lat: c?.[1],
    lon: c?.[0],
  };
}

/** Coordinates come from the served map.geojson (already public, rounded to ~1 km). */
export function coordsFromGeojson(geojson: any): Record<string, [number, number]> {
  const out: Record<string, [number, number]> = {};
  for (const f of geojson?.features ?? []) {
    const id = f?.properties?.id;
    const c = f?.geometry?.coordinates;
    if (id && Array.isArray(c) && c.length === 2) out[id] = [c[0], c[1]];
  }
  return out;
}

const byName = (a: DcLite, b: DcLite) => (a.name || "").localeCompare(b.name || "");

function km(a: DcLite, b: DcLite): number | undefined {
  if (a.lat == null || a.lon == null || b.lat == null || b.lon == null) return undefined;
  const R = 6371, rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad, dLon = (b.lon - a.lon) * rad;
  const h = Math.sin(dLat / 2) ** 2
    + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

// An "unknown" operator is a placeholder, not an identity: it must never group fiches together.
const namedOperator = (o?: string) =>
  !!o && !["unknown", "none", "inconnu", ""].includes(o.trim().toLowerCase());

export function buildRelated(all: DcLite[], current: DcLite, max = 6): Related[] {
  const out: Related[] = [];
  const seen = new Set<string>([current.id]);
  const others = all.filter((d) => d.id !== current.id);

  const take = (pool: DcLite[], relation: Relation, cap: number) => {
    let n = 0;
    for (const d of pool) {
      if (out.length >= max || n >= cap) break;
      if (seen.has(d.id)) continue;
      seen.add(d.id);
      out.push({ ...d, relation, ...(relation === "nearby" ? { km: km(current, d) } : {}) });
      n++;
    }
  };

  if (namedOperator(current.operator))
    take([...others.filter((d) => namedOperator(d.operator) && d.operator === current.operator)]
      .sort(byName), "operator", 3);

  // « Same region » is ALWAYS compared within the same country: administrative codes collide
  // across borders (2026-09-22 bug — the Indre « 36 » paired Châteauroux with Italian sites
  // whose province carries the same code).
  if (current.admin_area && current.country)
    take([...others.filter((d) => d.admin_area === current.admin_area && d.country === current.country)]
      .sort(byName), "region", 3);

  // Fill with the genuinely CLOSEST sites — a real answer to « why is this one a neighbour ? ».
  const measured = others
    .map((d) => ({ d, k: km(current, d) }))
    .filter((x): x is { d: DcLite; k: number } => x.k !== undefined)
    .sort((a, b) => a.k - b.k)
    .map((x) => x.d);
  take(measured, "nearby", max);

  return out.slice(0, max);
}
