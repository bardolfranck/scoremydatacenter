// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Pays-Bas — 152 fiches, dont 151 en service. Loi nationale, instruction communale.
// Le délai de six semaines de l'Awb est le même pour la réclamation administrative
// (bezwaar) et pour le recours juridictionnel (beroep) : un seul nombre à retenir, ce qui
// en fait l'un des droits les plus lisibles du corpus.
// Texte lu sur wetten.overheid.nl le 2026-10-23.
import type { ProcedureCountry } from "./types";

export const NL: ProcedureCountry = {
  country: "NL",
  decentralised: false,
  inherits: "EU",
  national: {
    authority: {
      fr: "la commune, ou la province pour les installations les plus lourdes",
      en: "the municipality, or the province for the heaviest installations",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Six semaines pour contester la décision — le même délai vaut pour la réclamation administrative et pour le recours devant le juge.",
          en: "Six weeks to contest the decision — the same period applies to the administrative objection and to the court appeal.",
        },
        cite: "Algemene wet bestuursrecht, art. 6:7",
        url: "https://wetten.overheid.nl/BWBR0005537/2026-08-15/#Hoofdstuk6_Afdeling6.2_Artikel6:7",
        verified: "2026-10-23",
      },
    ],
    documents: [],
  },
};
