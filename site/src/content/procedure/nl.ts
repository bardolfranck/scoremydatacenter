// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Pays-Bas — 152 fiches, dont 151 en service.
// La RÈGLE est nationale et uniforme : un seul permis, l'omgevingsvergunning de l'Omgevingswet
// (entrée en vigueur le 1er janvier 2024), et un seul délai de recours, les six semaines de l'Awb.
// D'où decentralised = false (règle maison : decentralised = là où vit la RÈGLE, pas là où elle
// s'instruit). L'INSTRUCTION, elle, n'est pas communale : le hoofdstuk 4 de l'Omgevingsbesluit la
// répartit — la commune (college van B&W) par défaut, mais la province (gedeputeerde staten) pour
// les installations les plus lourdes (IPPC, Seveso) et un ministre (le Rijk) pour les projets
// d'intérêt national. Dire « instruction communale » était faux pour exactement les gros data
// centers que nous notons.
// Le délai de six semaines de l'Awb est le même pour la réclamation administrative (bezwaar) et
// pour le recours juridictionnel (beroep) : un seul nombre à retenir, ce qui en fait l'un des
// droits les plus lisibles du corpus.
// Awb art. 6:7 lu sur wetten.overheid.nl le 2026-10-23 ; répartition du bevoegd gezag
// (Omgevingswet + Omgevingsbesluit, hoofdstuk 4) vérifiée sur iplo.nl le 2026-11-02.
import type { ProcedureCountry } from "./types";

export const NL: ProcedureCountry = {
  country: "NL",
  decentralised: false,
  inherits: "EU",
  national: {
    authority: {
      fr: "la commune (college van burgemeester en wethouders) délivre l'omgevingsvergunning ; pour les installations les plus lourdes la compétence remonte à la province (gedeputeerde staten), voire à l'État (un ministre) pour les projets d'intérêt national",
      en: "the municipality (college van burgemeester en wethouders) issues the omgevingsvergunning; for the heaviest installations competence rises to the province (gedeputeerde staten), and to the State (a minister) for projects of national interest",
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
