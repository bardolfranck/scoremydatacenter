// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Finlande — 37 fiches, toutes en service.
// Texte lu sur finlex.fi le 2026-10-23.
import type { ProcedureCountry } from "./types";

export const FI: ProcedureCountry = {
  country: "FI",
  decentralised: false,
  inherits: "EU",
  national: {
    authority: {
      fr: "la commune pour le permis de construire, l'agence régionale (aluehallintovirasto) pour l'autorisation environnementale",
      en: "the municipality for the building permit, the regional agency (aluehallintovirasto) for the environmental permit",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Trente jours pour former un recours écrit contre la décision, à compter de sa notification. Le recours ne peut se fonder que sur l'illégalité de la décision.",
          en: "Thirty days to lodge a written appeal against the decision, from its notification. The appeal may only be founded on the decision being unlawful.",
        },
        cite: "Laki oikeudenkäynnistä hallintoasioissa (808/2019), 13 §",
        url: "https://finlex.fi/fi/lainsaadanto/2019/808",
        verified: "2026-10-23",
      },
    ],
    documents: [],
  },
};
