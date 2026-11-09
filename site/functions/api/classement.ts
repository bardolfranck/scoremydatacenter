// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// GET /api/classement?src=/fr/classement/&tri=site&ordre=desc&statut=all&q=…&page=1
//   → { total, page, par, lignes: [html…] }   — un paquet de lignes du classement
// GET /api/classement?src=/fr/classement/&lieu=<lat>,<lon>
//   → { lignes: [html…], km: [d…] }           — les cinq lignes les plus proches d'un lieu
//
// La page Classement publiait ses 3 339 lignes en un HTML de 10 Mo (Franck 2026-11-09).
// Elle n'en garde plus que les premières ; le reste se demande ici, par paquets. Les
// lignes sont celles qu'Astro a rendues — découpées après le build par
// scripts/prune_public_json.py, jamais re-dessinées ici. Le tri et le filtre reprennent
// À L'IDENTIQUE ce que faisait le navigateur (Ranking.astro, ancienne fonction apply).
import { km, reponse } from "../_shared/carte";
import donnees from "../_data/classement.json";

type Meta = [string, string, string, number | null, number | null, Record<string, number>];
type Page = { meta: Meta[]; z: string; off: number[]; par: number };
const PAGES = donnees as unknown as Record<string, Page>;

// Le HTML d'une langue arrive compressé (deflate brut, base64) : on ne le décompresse
// qu'à la première demande de cette langue, puis il reste en mémoire de l'instance.
const enClair = new Map<string, Promise<string>>();
function html(src: string): Promise<string> {
  let p = enClair.get(src);
  if (!p) {
    const octets = Uint8Array.from(atob(PAGES[src].z), (c) => c.charCodeAt(0));
    p = new Response(new Blob([octets]).stream().pipeThrough(new DecompressionStream("deflate-raw"))).text();
    enClair.set(src, p);
  }
  return p;
}
const ligne = (texte: string, p: Page, i: number) => texte.slice(p.off[i], p.off[i + 1]);
// Même normalisation que la botte de foin rendue au build (data-search).
const norm = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

export const onRequestGet: PagesFunction = async ({ request }) => {
  const q = new URL(request.url).searchParams;
  const src = q.get("src") ?? "";
  const page = Object.hasOwn(PAGES, src) ? PAGES[src] : undefined;
  if (!page) return reponse({ error: "not_found" }, 404);
  const texte = await html(src);
  const n = page.meta.length;

  const lieu = q.get("lieu");
  if (lieu) {
    const [lat, lon] = lieu.split(",").map(Number);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) {
      return reponse({ error: "bad_request" }, 400);
    }
    const proches = page.meta
      .map((m, i) => (m[3] === null || m[4] === null ? null : { i, d: km(lon, lat, m[4], m[3]) }))
      .filter((x): x is { i: number; d: number } => x !== null)
      .sort((a, b) => a.d - b.d)
      .slice(0, 5);
    return reponse({ lignes: proches.map((x) => ligne(texte, page, x.i)), km: proches.map((x) => x.d) });
  }

  const tri = q.get("tri") ?? "site";
  const asc = q.get("ordre") === "asc";
  const statut = q.get("statut") ?? "all";
  const cherche = norm((q.get("q") ?? "").trim().slice(0, 100));
  // La taille de page vient du build (RANG_PAR_PAGE), la même que celle de la page servie.
  const PAR = page.par;
  const numero = Math.max(1, Math.min(1000, parseInt(q.get("page") ?? "1", 10) || 1));

  let idx = Array.from({ length: n }, (_, i) => i);
  if (statut !== "all") idx = idx.filter((i) => page.meta[i][0] === statut);
  if (cherche) idx = idx.filter((i) => page.meta[i][2].includes(cherche));
  idx.sort((a, b) => {
    if (tri === "country") {
      const diff = page.meta[a][1].localeCompare(page.meta[b][1]);
      return asc ? -diff : diff;
    }
    const va = page.meta[a][5][tri] ?? -1;
    const vb = page.meta[b][5][tri] ?? -1;
    // Une absence n'est pas une valeur extrême : sans donnée, en fin dans les deux sens.
    if ((va < 0) !== (vb < 0)) return va < 0 ? 1 : -1;
    return asc ? va - vb : vb - va;
  });

  const debut = (numero - 1) * PAR;
  return reponse({
    total: idx.length,
    page: numero,
    par: PAR,
    lignes: idx.slice(debut, debut + PAR).map((i) => ligne(texte, page, i)),
  });
};
