// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// LA CARTE NE TÉLÉCHARGE PLUS LE CORPUS (Franck 2026-11-09 : « compiler côté serveur et
// exposer le moins possible en un coup »).
//
// Jusqu'ici /data/map.geojson livrait en UN fichier les 3 339 fiches avec nom, opérateur,
// commune et lettre : un `curl` suffisait à emporter le plancher gratuit entier. Le
// fichier public ne porte plus que des POINTS ANONYMES (position à ~1 km, couleur, taille,
// pays) et un numéro d'ordre `t`. Tout ce qui nomme un site — nom, opérateur, commune,
// identifiant, lien — passe par ces fonctions, UN SITE PAR REQUÊTE (ou une poignée pour la
// recherche et les voisins). Tout emporter redevient des milliers de requêtes : ce qu'un
// limiteur de débit sait arrêter, et ce que le plan de site permet déjà, ni plus ni moins.
//
// Les données viennent de `functions/_data/`, écrit par scripts/prune_public_json.py au
// build à partir des geojson COMPLETS, AVANT qu'ils soient anonymisés dans dist/. Elles
// sont empaquetées dans la fonction, jamais servies comme fichier.
// `t` = rang de l'entité dans ce fichier. Les deux côtés dérivent du même fichier, dans
// le même ordre, au même build : ils ne peuvent pas se décaler.
import carte from "../_data/carte.json";
import veille from "../_data/veille.json";

type Feature = { type: "Feature"; geometry: { type: "Point"; coordinates: [number, number] }; properties: Record<string, any> };

export const SITES: Feature[] = (carte as any).features;
export const VEILLE: Feature[] = (veille as any).features;

const PAR_ID = new Map<string, Feature>(SITES.map((f) => [String(f.properties.id), f]));

export function siteParRang(t: string | null): Feature | null {
  if (t === null || !/^\d{1,6}$/.test(t)) return null;
  return SITES[Number(t)] ?? null;
}
export function siteParId(id: string | null): Feature | null {
  return id ? PAR_ID.get(id) ?? null : null;
}
export function veilleParRang(t: string | null): Feature | null {
  if (t === null || !/^\d{1,6}$/.test(t)) return null;
  return VEILLE[Number(t)] ?? null;
}

// Une entité renvoyée garde son rang : le navigateur s'en sert pour retrouver le point.
export const avecRang = (f: Feature, liste: Feature[]) => ({ ...f, properties: { ...f.properties, t: liste.indexOf(f) } });

export function reponse(corps: unknown, status = 200): Response {
  return new Response(JSON.stringify(corps), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      // Cache court au bord : la réponse est la même pour tout le monde, et un
      // déploiement purge tout le cache de la zone.
      "cache-control": status === 200 ? "public, max-age=300" : "no-store",
      "x-robots-tag": "noindex, nofollow",
    },
  });
}

export const norm = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "")
  .toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

export function km(aLon: number, aLat: number, bLon: number, bLat: number): number {
  const r = Math.PI / 180;
  const dLat = (bLat - aLat) * r, dLon = (bLon - aLon) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(aLat * r) * Math.cos(bLat * r) * Math.sin(dLon / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}
