// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Suède — 52 fiches, toutes en service. Loi nationale, délai court.
// Texte lu sur riksdagen.se le 2026-10-23.
import type { ProcedureCountry } from "./types";

export const SE: ProcedureCountry = {
  country: "SE",
  decentralised: false,
  inherits: "EU",
  national: {
    authority: {
      fr: "la commune pour le permis de construire, le conseil régional (länsstyrelsen) pour l'autorisation environnementale",
      en: "the municipality for the building permit, the county board (länsstyrelsen) for the environmental permit",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Trois semaines pour contester la décision, à compter du jour où elle vous a été communiquée. C'est l'un des délais les plus courts du corpus.",
          en: "Three weeks to contest the decision, from the day it reached you. One of the shortest deadlines in the corpus.",
        },
        cite: "Förvaltningslag (2017:900), 44 §",
        url: "https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/forvaltningslag-2017900_sfs-2017-900/",
        verified: "2026-10-23",
      },
    ],
    documents: [],
  },
};
