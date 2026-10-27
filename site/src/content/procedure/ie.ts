// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Irlande — 12 fiches. Le permis d'urbanisme est décidé par l'autorité locale (local planning
// authority), An Coimisiún Pleanála (ex-An Bord Pleanála) statuant en appel ; le délai du recours
// JURIDICTIONNEL (judicial review) devant la High Court est national et uniforme — huit semaines.
// decentralised: false, comme NL/LU/PL : l'autorité nomme le décideur, la loi fixe le délai.
//
// PIÈGE DE LA VERSION ÉVITÉ : l'art. 50 du Planning and Development Act 2000 (le texte « as enacted »
// que sert irishstatutebook pour les lois primaires) est PÉRIMÉ — le Planning and Development Act 2024
// (loi n° 34 de 2024) a refondu le contentieux. Les articles 278 à 290 (dont l'art. 281) sont EN VIGUEUR
// depuis le 1er août 2025, commencés par le Planning and Development Act 2024 (Commencement) (No. 3)
// Order 2025 (S.I. No. 379 of 2025), art. 2(b) — établi par la TABLE DE COMMENCEMENT officielle de l'ISBC
// (irishstatutebook.ie/eli/isbc/2024_34.html), vérifiée au texte (le S.I. 662/2024 ne commence, lui, que
// les art. 1 à 5 et la Partie 26 — il NE porte PAS la Partie 9). La Partie 9 supprime l'étape du leave et
// porte le délai à l'art. 281. On cite donc le texte en vigueur (art. 281 PDA 2024), pas l'art. 50 de 2000.
// Le texte de l'art. 281 « as enacted » EST le texte en vigueur : loi récente, art. 281 non amendé
// depuis (consolidation revisedacts.lawreform.ie identique). Lu sur irishstatutebook.ie le 2026-10-27.
//
// NON TRAITÉ ICI : l'appel de première instance devant An Coimisiún Pleanála est une voie DISTINCTE et
// plus courte ; son délai sous le régime 2024 n'est pas vérifié dans ce bloc, qui s'en tient au recours
// juridictionnel. Mieux vaut une affirmation tenue qu'un second délai approximatif.
import type { ProcedureCountry } from "./types";

export const IE: ProcedureCountry = {
  country: "IE",
  decentralised: false,
  inherits: "EU",
  national: {
    authority: {
      fr: "l'autorité locale d'urbanisme ; en appel, An Coimisiún Pleanála (ex-An Bord Pleanála). Le recours juridictionnel se porte devant la High Court.",
      en: "the local planning authority; on appeal, An Coimisiún Pleanála (formerly An Bord Pleanála). Judicial review goes to the High Court.",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Huit semaines pour engager un recours juridictionnel (judicial review) devant la High Court, à compter de la décision. La High Court peut accorder une prolongation pour un motif valable et suffisant.",
          en: "Eight weeks to bring a judicial review before the High Court, from the date of the decision. The High Court may grant an extension for good and sufficient reason.",
        },
        cite: "Planning and Development Act 2024 (No. 34 of 2024), s. 281(1)",
        url: "https://www.irishstatutebook.ie/eli/2024/act/34/section/281/enacted/en/html",
        verified: "2026-10-27",
      },
    ],
    documents: [],
  },
};
