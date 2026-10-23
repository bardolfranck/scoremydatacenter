// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Danemark — 36 fiches, toutes en service. Le Danemark a une voie SPÉCIFIQUE à
// l'environnement, distincte du contentieux administratif général : la commission des
// recours environnementaux et alimentaires (Miljø- og Fødevareklagenævnet). C'est elle
// qu'un riverain saisit, et le délai est le sien.
// Texte lu sur retsinformation.dk le 2026-10-23 (consolidation servie à cet ELI).
import type { ProcedureCountry } from "./types";

export const DK: ProcedureCountry = {
  country: "DK",
  decentralised: false,
  inherits: "EU",
  national: {
    authority: {
      fr: "la commune, avec recours devant la commission des recours environnementaux (Miljø- og Fødevareklagenævnet)",
      en: "the municipality, with appeal to the Environment and Food Appeals Board (Miljø- og Fødevareklagenævnet)",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Quatre semaines pour contester la décision, à compter du jour où elle est notifiée — ou toujours de sa publication si elle a été annoncée publiquement. Un délai qui expire un samedi ou un jour férié court jusqu'au jour ouvrable suivant.",
          en: "Four weeks to contest the decision, from the day it is notified — or always from publication where it was publicly announced. A deadline falling on a Saturday or holiday runs to the next working day.",
        },
        cite: "Miljøbeskyttelsesloven § 93",
        url: "https://www.retsinformation.dk/eli/lta/2024/928",
        verified: "2026-10-23",
      },
    ],
    documents: [],
  },
};
