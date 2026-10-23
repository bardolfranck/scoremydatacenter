// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// United States — there is NO federal data-center permit. A data center is
// permitted by the town or county that zones the land, under whatever
// environmental-review statute its state imposes. The procedure therefore lives
// per state, and a state we have not read gets no block at all.
//
// New York read at source on 2026-10-23: 6 NYCRR 617 (SEQRA), General Municipal
// Law art. 18-A (industrial development agencies), Public Officers Law art. 6
// (FOIL), CPLR 217.
import type { ProcedureCountry } from "./types";

export const US: ProcedureCountry = {
  country: "US",
  decentralised: true,
  subdivisionKey: "admin_area = full state name, e.g. \"New York\"",
  frame: {
    fr: "Aux États-Unis, aucun permis fédéral ne porte sur un data center : c'est la commune ou le comté qui autorise, sous la loi d'examen environnemental de son État. La procédure ci-dessous est celle de cet État, pas une procédure nationale.",
    en: "In the United States no federal permit covers a data center: the town or county authorises it, under its own state's environmental-review statute. The procedure below is that state's, not a national one.",
  },
  subdivisions: {
    "New York": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain (agence chef de file au titre du SEQRA)",
        en: "the town or county that zones the land (lead agency under SEQRA)",
      },
      windows: {
        announced: {
          text: {
            fr: "Avant tout dossier : l'aide financière d'une agence de développement industriel (abattement de taxe foncière, PILOT) au-delà de 100 000 $ impose une audience publique — souvent le premier rendez-vous public du projet, et le plus tôt.",
            en: "Before any filing: financial assistance from an industrial development agency (property-tax abatement, PILOT) above $100,000 requires a public hearing — often the project's first public meeting, and the earliest.",
          },
          cite: "N.Y. General Municipal Law § 859-a(2)",
          url: "https://www.nysenate.gov/legislation/laws/GMU/859-A",
          verified: "2026-10-23",
        },
        permitting: {
          text: {
            fr: "L'examen SEQRA est ouvert : les commentaires sur l'étude d'impact (draft EIS) sont reçus pendant trente jours au moins, à compter du dépôt et de la diffusion de l'avis d'achèvement.",
            en: "SEQRA review is open: comments on the draft EIS are accepted for a minimum of thirty days from the first filing and circulation of the notice of completion.",
          },
          cite: "6 NYCRR 617.9(a)(3)",
          url: "https://www.law.cornell.edu/regulations/new-york/6-NYCRR-617.9",
          verified: "2026-10-23",
        },
        operational: {
          text: {
            fr: "Le site fonctionne : les conditions opposables sont celles écrites dans l'autorisation locale. Les obtenir, puis les confronter à l'exploitation, passe par une demande FOIL.",
            en: "The site is running: the enforceable conditions are the ones written into the local approval. Getting them, then holding the operation to them, goes through a FOIL request.",
          },
          cite: "N.Y. Public Officers Law § 89(3)(a)",
          url: "https://www.nysenate.gov/legislation/laws/PBO/89",
          verified: "2026-10-23",
        },
      },
      deadlines: [
        {
          text: {
            fr: "Si une audience publique est tenue sur l'étude d'impact, elle s'ouvre entre quinze et soixante jours calendaires après le dépôt de l'avis d'achèvement : la date se surveille, elle ne se demande pas.",
            en: "If a public hearing is held on the draft EIS, it opens no less than 15 and no more than 60 calendar days after the notice of completion is filed: the date is watched for, not requested.",
          },
          cite: "6 NYCRR 617.9(a)(4)(ii)",
          url: "https://www.law.cornell.edu/regulations/new-york/6-NYCRR-617.9",
          verified: "2026-10-23",
        },
        {
          text: {
            fr: "L'audience de l'agence de développement industriel doit être annoncée au moins dix jours à l'avance : c'est le préavis minimal pour s'organiser.",
            en: "The industrial development agency's hearing must be noticed at least ten days ahead: that is the minimum warning you get.",
          },
          cite: "N.Y. General Municipal Law § 859-a(3)",
          url: "https://www.nysenate.gov/legislation/laws/GMU/859-A",
          verified: "2026-10-23",
        },
        {
          text: {
            fr: "Contester la décision devant le juge (procédure dite Article 78) : quatre mois à compter du jour où elle devient définitive. Ce délai ne se rattrape pas.",
            en: "Challenging the decision in court (an Article 78 proceeding): four months from the day it becomes final and binding. This one does not come back.",
          },
          cite: "N.Y. CPLR 217(1)",
          url: "https://www.nysenate.gov/legislation/laws/CVP/217",
          verified: "2026-10-23",
        },
      ],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide, étude acoustique — s'obtient par une demande écrite FOIL : l'administration doit répondre dans les cinq jours ouvrés.",
            en: "Any record held by the town, the county or the development agency — impact study, assistance application, acoustic study — is obtained by a written FOIL request: the agency must act within five business days.",
          },
          cite: "N.Y. Public Officers Law § 89(3)(a)",
          url: "https://www.nysenate.gov/legislation/laws/PBO/89",
          verified: "2026-10-23",
        },
        {
          text: {
            fr: "Un refus se conteste : trente jours pour faire appel par écrit auprès du responsable désigné de l'administration.",
            en: "A denial can be contested: thirty days to appeal in writing to the agency's designated appeals officer.",
          },
          cite: "N.Y. Public Officers Law § 89(4)(a)",
          url: "https://www.nysenate.gov/legislation/laws/PBO/89",
          verified: "2026-10-23",
        },
      ],
    },
  },
};
