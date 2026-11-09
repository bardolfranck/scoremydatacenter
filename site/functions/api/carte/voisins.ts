// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// GET /api/carte/voisins?id=<identifiant>  — la mini-carte d'une fiche : le site et ses
// voisins. Elle chargeait les 3 339 fiches pour en afficher une poignée autour d'un
// point au zoom 8. Elle reçoit maintenant le site et ses voisins dans un rayon qui couvre
// ce zoom, plafonnés : ce qu'elle montrait, sans le reste du monde.
import { SITES, km, reponse, siteParId } from "../../_shared/carte";

const RAYON_KM = 250;
const PLAFOND = 80;

export const onRequestGet: PagesFunction = async ({ request }) => {
  const centre = siteParId(new URL(request.url).searchParams.get("id"));
  if (!centre) return reponse({ error: "not_found" }, 404);
  const [lon, lat] = centre.geometry.coordinates;
  const voisins = SITES
    .filter((f) => f !== centre)
    .map((f) => ({ f, d: km(lon, lat, f.geometry.coordinates[0], f.geometry.coordinates[1]) }))
    .filter((x) => x.d <= RAYON_KM)
    .sort((a, b) => a.d - b.d)
    .slice(0, PLAFOND)
    .map(({ f }) => ({ type: "Feature", geometry: f.geometry,
                       properties: { id: f.properties.id, name: f.properties.name, grade_site: f.properties.grade_site } }));
  return reponse({ centre: centre.geometry.coordinates, voisins });
};
