// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// GET /api/carte/site?t=<rang>  ou  ?id=<identifiant>  — UN site, pour l'infobulle de la
// carte (clic sur un point) et le lien profond venu du classement (?dc=<id>).
// Voir functions/_shared/carte.ts pour le pourquoi.
import { SITES, avecRang, reponse, siteParId, siteParRang } from "../../_shared/carte";

export const onRequestGet: PagesFunction = async ({ request }) => {
  const q = new URL(request.url).searchParams;
  const f = q.has("id") ? siteParId(q.get("id")) : siteParRang(q.get("t"));
  return f ? reponse(avecRang(f, SITES)) : reponse({ error: "not_found" }, 404);
};
