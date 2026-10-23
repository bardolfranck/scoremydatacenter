// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Suisse — 54 fiches. CONSTAT, et c'est le contenu du fichier : il n'existe AUCUN délai
// fédéral applicable au permis de construire d'un data center. Le permis est cantonal,
// voire communal, et chaque canton fixe le sien.
//
// 🔴 LE PIÈGE QU'ON A ÉVITÉ. L'art. 50 de la loi fédérale sur la procédure administrative
// (PA, RS 172.021) dit « 30 jours » et se trouve en deux clics. Il ne régit QUE la
// procédure devant les autorités FÉDÉRALES : le citer pour un permis cantonal serait le
// bon texte appliqué au mauvais périmètre — une erreur qui se lit comme un délai, et qui
// ferait perdre son recours à un lecteur vaudois ou zurichois. La Suisse reste donc sans
// bloc tant qu'un canton n'est pas lu, canton par canton.
// Constat établi le 2026-10-23.
import type { ProcedureCountry } from "./types";

export const CH: ProcedureCountry = {
  country: "CH",
  decentralised: true,
  subdivisionKey: "canton (code à deux lettres) — aucun n'est encore lu",
  frame: {
    fr: "En Suisse, le permis de construire est cantonal : il n'existe pas de délai fédéral applicable. Nous ne publions pas de procédure tant que le droit du canton concerné n'a pas été lu — un délai emprunté à un autre niveau ferait perdre son recours.",
    en: "In Switzerland the building permit is cantonal: no federal deadline applies. We publish no procedure until the relevant canton's own law has been read — a deadline borrowed from another level would cost the reader their appeal.",
  },
  subdivisions: {},
};
