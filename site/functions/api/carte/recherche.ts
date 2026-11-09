// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// GET /api/carte/recherche?q=<texte>  — la recherche de projets posée sur la carte.
// Elle filtrait le corpus entier DANS le navigateur, ce qui exigeait de l'y avoir
// téléchargé. Même règle de correspondance qu'avant (nom, commune, opérateur, sans
// accents), même plafond de quatre réponses : une requête rend au plus quatre sites.
import { SITES, avecRang, norm, reponse } from "../../_shared/carte";

const PLAFOND = 4;

export const onRequestGet: PagesFunction = async ({ request }) => {
  const q = norm(new URL(request.url).searchParams.get("q") ?? "");
  if (q.length < 2) return reponse({ type: "FeatureCollection", features: [] });
  const trouves = [];
  for (const f of SITES) {
    const p = f.properties;
    if (norm([p.name, p.municipality, p.operator].filter(Boolean).join(" ")).includes(q)) {
      trouves.push(avecRang(f, SITES));
      if (trouves.length >= PLAFOND) break;
    }
  }
  return reponse({ type: "FeatureCollection", features: trouves });
};
