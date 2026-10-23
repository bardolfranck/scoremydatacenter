// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Italie — 92 fiches, toutes en service. L'évaluation environnementale est régionale, mais
// le délai pour attaquer l'acte est national : le code du procès administratif s'applique
// quel que soit l'auteur de la décision. Un fichier national, donc, pas vingt.
// Texte lu sur normattiva.it le 2026-10-23 (en vigueur depuis le 16-9-2010).
import type { ProcedureCountry } from "./types";

export const IT: ProcedureCountry = {
  country: "IT",
  decentralised: false,
  inherits: "EU",
  frame: {
    fr: "En Italie l'évaluation environnementale est conduite par la région, mais le délai pour contester la décision devant le tribunal administratif est fixé par la loi nationale.",
    en: "In Italy the environmental assessment is run by the region, but the deadline to challenge the decision before the administrative court is set by national law.",
  },
  national: {
    authority: {
      fr: "la commune pour le permis de construire, la région pour l'évaluation environnementale ; recours devant le tribunal administratif régional (TAR)",
      en: "the municipality for the building permit, the region for the environmental assessment; appeal to the regional administrative court (TAR)",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Soixante jours, à peine de forclusion, pour demander l'annulation de la décision — pour violation de la loi, incompétence ou excès de pouvoir.",
          en: "Sixty days, on pain of forfeiture, to seek annulment of the decision — for breach of law, lack of competence or misuse of power.",
        },
        cite: "Codice del processo amministrativo (d.lgs. 104/2010, allegato 1), art. 29",
        url: "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2010-07-02;104",
        verified: "2026-10-23",
      },
    ],
    documents: [],
  },
};
