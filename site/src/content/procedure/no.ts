// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Norvège — 45 fiches, toutes en service. Hors Union européenne, donc SANS socle : la
// Norvège applique une partie du droit européen par l'accord EEE, mais nous ne publions
// que ce que nous avons lu. Ici, la loi générale de procédure administrative.
// Texte lu sur lovdata.no le 2026-10-23.
import type { ProcedureCountry } from "./types";

export const NO: ProcedureCountry = {
  country: "NO",
  decentralised: false,
  national: {
    authority: {
      fr: "la commune, le préfet de comté (statsforvalteren) en appel",
      en: "the municipality, with the county governor (statsforvalteren) on appeal",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Trois semaines pour former une réclamation contre la décision, à compter du moment où elle parvient à la partie concernée — à compter de la publication si elle a été annoncée publiquement.",
          en: "Three weeks to lodge a complaint against the decision, from the moment notice reaches the party concerned — from publication if it was announced publicly.",
        },
        cite: "Forvaltningsloven § 29",
        url: "https://lovdata.no/dokument/NL/lov/1967-02-10/KAPITTEL_6",
        verified: "2026-10-23",
      },
    ],
    documents: [],
  },
};
