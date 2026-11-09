// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// GET /api/veille/site?t=<rang>  — UNE entrée de la veille (opposition, moratoire,
// projet annoncé), pour son infobulle. Le fichier public ne porte que la position et la
// nature de chaque entrée ; les faits et les sources de presse arrivent ici, une à la
// fois. Voir functions/_shared/carte.ts.
import { VEILLE, avecRang, reponse, veilleParRang } from "../../_shared/carte";

export const onRequestGet: PagesFunction = async ({ request }) => {
  const f = veilleParRang(new URL(request.url).searchParams.get("t"));
  return f ? reponse(avecRang(f, VEILLE)) : reponse({ error: "not_found" }, 404);
};
