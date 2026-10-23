// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Belgique — 42 fiches, toutes en service. CONSTAT, comme la Suisse : le permis
// d'environnement est RÉGIONAL. La Flandre a son omgevingsvergunning, la Wallonie son
// permis unique, Bruxelles le sien. Il n'existe pas de procédure belge à publier.
//
// ⚠️ PIÈGE DE CLÉ. Le corpus écrit `admin_area` au niveau de la PROVINCE (VBR, VAN, WLG…)
// alors que le droit se décide au niveau de la RÉGION. Un fichier régional devra donc
// passer par la correspondance ci-dessous, sans quoi il ne trouvera jamais sa subdivision.
// Correspondance établie sur le corpus le 2026-10-23 :
//   Flandre  : VBR (17) · VAN (6) · VOV (5) · VLI (2) · VWV (2)   = 32 fiches
//   Wallonie : WLG (3) · WHT (1) · WNA (1)                        =  5 fiches
//   Non renseigné : 5 fiches
// Bruxelles n'apparaît pas encore au corpus.
import type { ProcedureCountry } from "./types";

export const BE: ProcedureCountry = {
  country: "BE",
  decentralised: true,
  subdivisionKey: "région (dérivée de admin_area, qui est une PROVINCE) — aucune n'est encore lue",
  frame: {
    fr: "En Belgique, le permis d'environnement est régional : la Flandre, la Wallonie et Bruxelles ont chacune le leur, avec leurs propres délais. Nous ne publions pas de procédure tant que le droit de la région concernée n'a pas été lu.",
    en: "In Belgium the environmental permit is regional: Flanders, Wallonia and Brussels each have their own, with their own deadlines. We publish no procedure until the relevant region's law has been read.",
  },
  subdivisions: {},
};
