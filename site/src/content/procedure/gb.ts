// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Royaume-Uni — 148 fiches. Le droit de l'urbanisme n'est PAS britannique : l'Angleterre
// et le pays de Galles relèvent du Town and Country Planning Act 1990, l'Écosse de sa
// propre loi de 1997, l'Irlande du Nord de la sienne de 2011. Pays décentralisé, donc, et
// une nation non lue ne reçoit aucun bloc — c'est la même règle que pour les États-Unis.
//
// Clé de subdivision : `admin_area` tel que le corpus l'écrit — ENG, WLS, SCT, NIR.
// Textes lus sur legislation.gov.uk le 2026-10-23.
import type { ProcedureCountry } from "./types";

const ANGLETERRE_PAYS_DE_GALLES = {
  authority: {
    fr: "l'autorité locale d'urbanisme (local planning authority)",
    en: "the local planning authority",
  },
  windows: {},
  deadlines: [
    {
      text: {
        fr: "Six semaines pour saisir la High Court d'une contestation de la décision d'urbanisme, à compter du lendemain du jour où elle est prise — et il faut d'abord en obtenir l'autorisation du juge.",
        en: "Six weeks to bring a challenge to the planning decision before the High Court, running from the day after it is taken — and leave of the court is needed first.",
      },
      cite: "Town and Country Planning Act 1990, s. 288(4A)-(4B)",
      url: "https://www.legislation.gov.uk/ukpga/1990/8/section/288",
      verified: "2026-10-23",
    },
  ],
  documents: [
    {
      text: {
        fr: "Toute information environnementale détenue par une autorité publique se demande par écrit : la réponse est due dans les vingt jours ouvrables.",
        en: "Any environmental information held by a public authority can be requested in writing: the answer is due within twenty working days.",
      },
      cite: "Environmental Information Regulations 2004, reg. 5(1)-(2)",
      url: "https://www.legislation.gov.uk/uksi/2004/3391/regulation/5",
      verified: "2026-10-23",
    },
  ],
};

export const GB: ProcedureCountry = {
  country: "GB",
  decentralised: true,
  subdivisionKey: "admin_area = ENG | WLS | SCT | NIR",
  frame: {
    fr: "Le Royaume-Uni n'a pas un droit de l'urbanisme mais trois : l'Angleterre et le pays de Galles partagent la loi de 1990, l'Écosse a la sienne depuis 1997, l'Irlande du Nord depuis 2011. La procédure ci-dessous est celle de la nation concernée.",
    en: "The United Kingdom has not one planning law but three: England and Wales share the 1990 Act, Scotland has had its own since 1997, Northern Ireland since 2011. The procedure below is that nation's.",
  },
  subdivisions: {
    ENG: ANGLETERRE_PAYS_DE_GALLES,
    WLS: ANGLETERRE_PAYS_DE_GALLES,
  },
};
