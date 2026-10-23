// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Allemagne — 313 fiches, dont 309 EN SERVICE. C'est donc la voie de réclamation qui
// compte ici, pas la fenêtre de consultation.
//
// La loi est FÉDÉRALE (BImSchG, VwGO) ; seul l'organe qui l'applique est régional — le
// Regierungspräsidium du Land. Pas de fichier par Land, donc : la même loi s'applique en
// Bavière et en Rhénanie, et dupliquer seize fois le même article produirait seize copies
// qui divergeraient. Textes lus sur gesetze-im-internet.de le 2026-10-23.
//
// ⚠️ PÉRIMÈTRE : un data center n'est pas en soi une installation soumise à autorisation
// BImSchG. Ce qui l'y fait entrer, ce sont ses GROUPES ÉLECTROGÈNES de secours — et c'est
// précisément par là que le dossier devient public. Voir notre registre de projets DE.
import type { ProcedureCountry } from "./types";

export const DE: ProcedureCountry = {
  country: "DE",
  decentralised: false,
  inherits: "EU",
  frame: {
    fr: "En Allemagne la loi est fédérale et l'instruction régionale : c'est le Regierungspräsidium du Land qui délivre l'autorisation. Un data center y entre généralement par ses groupes électrogènes de secours, soumis à la loi sur les immissions.",
    en: "In Germany the law is federal and the review regional: the Land's Regierungspräsidium issues the permit. A data centre usually enters that regime through its standby generators, caught by the immission-control act.",
  },
  national: {
    authority: {
      fr: "le Regierungspräsidium du Land (autorisation d'immissions), la commune pour le permis de construire",
      en: "the Land's Regierungspräsidium (immission-control permit), the municipality for the building permit",
    },
    windows: {
      permitting: {
        text: {
          fr: "Le dossier est mis à disposition du public pendant un mois après l'annonce, et les objections peuvent être déposées jusqu'à deux semaines après la fin de cette mise à disposition — un mois pour les installations relevant de la directive sur les émissions industrielles.",
          en: "The file is made available to the public for one month after the announcement, and objections can be raised until two weeks after that display period ends — one month for installations under the industrial-emissions directive.",
        },
        cite: "BImSchG § 10 Abs. 3",
        url: "https://www.gesetze-im-internet.de/bimschg/__10.html",
        verified: "2026-10-23",
      },
    },
    deadlines: [
      {
        text: {
          fr: "Le recours contre l'autorisation doit être introduit dans le mois qui suit sa notification. Passé ce délai, elle devient définitive.",
          en: "An action against the permit must be brought within one month of its notification. After that it becomes final.",
        },
        cite: "VwGO § 74 Abs. 1",
        url: "https://www.gesetze-im-internet.de/vwgo/__74.html",
        verified: "2026-10-23",
      },
    ],
    documents: [],
  },
};
