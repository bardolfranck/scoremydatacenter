// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Espagne — 68 fiches. L'évaluation environnementale relève des communautés autonomes,
// mais le DÉLAI de recours, lui, est national : la loi de 1998 sur la juridiction
// contentieuse-administrative s'applique quel que soit l'auteur de l'acte. C'est donc un
// fichier national, pas dix-sept.
// Texte lu sur boe.es le 2026-10-23.
import type { ProcedureCountry } from "./types";

export const ES: ProcedureCountry = {
  country: "ES",
  decentralised: false,
  inherits: "EU",
  frame: {
    fr: "En Espagne l'autorisation environnementale est délivrée par la communauté autonome, mais le délai pour la contester est fixé par la loi nationale.",
    en: "In Spain the environmental authorisation is issued by the autonomous community, but the deadline to challenge it is set by national law.",
  },
  national: {
    authority: {
      fr: "la communauté autonome pour l'autorisation environnementale, la commune pour la licence d'urbanisme",
      en: "the autonomous community for the environmental authorisation, the municipality for the planning licence",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Deux mois pour former un recours contentieux-administratif contre une décision expresse, à compter du lendemain de sa notification ou de sa publication. Si l'administration n'a pas répondu, le délai est de six mois.",
          en: "Two months to bring a contentious-administrative appeal against an express decision, from the day after it is notified or published. Where the authority stayed silent, the period is six months.",
        },
        cite: "Ley 29/1998, art. 46.1",
        url: "https://www.boe.es/buscar/act.php?id=BOE-A-1998-16718&tn=1&p=20210730#a46",
        verified: "2026-10-23",
      },
    ],
    documents: [],
  },
};
