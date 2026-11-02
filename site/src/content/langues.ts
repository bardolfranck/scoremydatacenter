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

// Les langues EN PRÉPARATION : leurs tables existent, leurs clés sont gardées comme celles
// des langues vivantes, mais aucune page ne les sert. C'est l'état dans lequel une langue
// s'écrit — et il est DÉCLARÉ, pas implicite, pour qu'on sache ce qui est en cours.
//
// 🔴 Faire passer une langue d'ici à `LANGUES_VIVANTES` est la décision qui la met en ligne.
// `test_une_langue_ne_devient_vivante_que_traduite` l'empêche tant que ses valeurs sont
// encore celles du français : sans ce garde, ouvrir le néerlandais publierait 740 chaînes
// françaises sur des pages néerlandaises — exactement la façon dont l'anglais a décroché,
// mais dans l'autre sens et en une seule fois.
export const LANGUES_EN_PREPARATION = ["nl"] as const;

/** Toutes les langues qui ont une table, servies ou non. */
export const LANGUES_DECLAREES = [...LANGUES_VIVANTES, ...LANGUES_EN_PREPARATION] as const;
export type LangueDeclaree = (typeof LANGUES_DECLAREES)[number];
