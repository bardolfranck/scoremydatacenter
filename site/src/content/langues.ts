// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Les langues vivantes du site, à UN seul endroit. Chaque table de chaînes s'y réfère, pour
// qu'ouvrir une langue soit une décision prise une fois et non une liste à rallonger partout.
//
// « Vivante » veut dire SERVIE : une langue en cours d'écriture n'entre ici qu'au moment où
// ses tables sont complètes, sinon les gardes de parité réclameraient des clés qui n'existent
// pas encore et la suite serait rouge pendant tout le temps de la rédaction.

export const LANGUES_VIVANTES = ["fr", "en"] as const;
export type Langue = (typeof LANGUES_VIVANTES)[number];
