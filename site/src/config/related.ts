// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
//
// Internal-linking helper: for a given fiche, pick a handful of "related" sites
// so every fiche links to its neighbours (same operator → same region → same
// country). These are STATIC, crawlable <a> links — unlike the mini-map's
// client-side pins — which weave the 1,400+ fiches into a topical mesh (crawl
// paths + contextual relevance + real UX). Deterministic: candidates are sorted
// by name so the build output is stable.

export interface DcLite {
  id: string;
  name: string;
  operator?: string;
  country?: string;
  admin_area?: string;
  municipality?: string;
  grade?: string;
}

export type Relation = "operator" | "region" | "country";
export interface Related extends DcLite {
  relation: Relation;
}

export function toLite(dc: any): DcLite {
  return {
    id: dc.id,
    name: dc.name,
    operator: dc.operator ?? undefined,
    country: dc.country ?? undefined,
    admin_area: dc.admin_area ?? undefined,
    municipality: dc.municipality ?? undefined,
    grade: dc.grades?.site?.grade ?? undefined,
  };
}

const byName = (a: DcLite, b: DcLite) => (a.name || "").localeCompare(b.name || "");

// max total links, and how many each category may contribute before the next
// category fills the rest (so a 50-site operator can't monopolise the block).
export function buildRelated(all: DcLite[], current: DcLite, max = 6): Related[] {
  const out: Related[] = [];
  const seen = new Set<string>([current.id]);
  const others = all.filter((d) => d.id !== current.id);

  const take = (pool: DcLite[], relation: Relation, cap: number) => {
    let n = 0;
    for (const d of [...pool].sort(byName)) {
      if (out.length >= max || n >= cap) break;
      if (seen.has(d.id)) continue;
      seen.add(d.id);
      out.push({ ...d, relation });
      n++;
    }
  };

  if (current.operator)
    take(others.filter((d) => d.operator && d.operator === current.operator), "operator", 3);
  if (current.admin_area)
    take(others.filter((d) => d.admin_area && d.admin_area === current.admin_area), "region", 3);
  if (current.country)
    take(others.filter((d) => d.country && d.country === current.country), "country", max);

  return out.slice(0, max);
}
