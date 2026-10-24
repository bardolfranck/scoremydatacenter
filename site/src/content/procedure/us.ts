// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// États-Unis — 1 718 fiches, le plus gros corpus du site, sur 51 juridictions.
//
// IL N'EXISTE AUCUN PERMIS FÉDÉRAL pour un data center. C'est la commune ou le comté qui
// zone le terrain qui autorise, sous la loi d'examen environnemental de son État quand il
// en a une — et la plupart n'en ont pas. La procédure vit donc PAR ÉTAT, et un État non lu
// ne reçoit aucun bloc : servir une procédure « nationale » reviendrait à l'inventer.
//
// CE QUE CHAQUE ÉTAT PORTE ICI. La loi d'accès aux documents de l'État, et son délai de
// réponse. C'est le levier qui marche dans les deux cas de figure — avant l'autorisation
// pour obtenir le dossier, après la mise en service pour obtenir les prescriptions écrites
// et y confronter l'exploitation. New York porte en plus les trois autres axes (examen
// environnemental SEQRA, audience obligatoire de l'agence de développement, recours
// Article 78), lus au texte le 2026-10-23.
//
// 🔴 LE RÉSULTAT LE PLUS UTILE EST UN NÉGATIF. Cinq des vingt-deux juridictions lues — le
// Texas, la Floride, le Minnesota, l'Arizona et le Montana — ne fixent AUCUN délai : la loi
// dit « promptement » et s'arrête là. Un lecteur qui attend une réponse au Texas n'attend
// rien de chiffrable, et c'est exactement ce qu'il faut lui dire plutôt que de le laisser
// croire à une horloge. À l'autre bout, le Missouri et le Kansas répondent en trois jours
// ouvrés, le Maryland en trente. Un facteur dix entre deux États du même pays.
//
// ⚠️ VINGT-NEUF JURIDICTIONS MANQUENT, et pour une raison qui n'est pas juridique : leurs
// recueils officiels refusent l'accès automatisé depuis notre environnement (403, Cloudflare,
// connexion refusée). Sont concernés, par poids de corpus : Illinois (82 fiches), Géorgie
// (75), Ohio (71), Pennsylvanie (59), New Jersey (56), Caroline du Nord (42), Colorado (41),
// Massachusetts (39), Oregon (38), Michigan (36), Indiana (28), Tennessee (28), Wisconsin
// (26), Oklahoma (22), Louisiane (21), Kentucky (20), Nebraska (19), Nevada (17),
// Nouveau-Mexique (11), Wyoming (10), New Hampshire (8), Idaho (8), Alabama (8), Arkansas
// (8), Dakota du Nord (7), Hawaï (7), Mississippi (6), Alaska (4), Rhode Island (2).
// Aucune n'est un trou de doctrine : ce sont des lectures à refaire depuis un accès qui
// passe. Les hôtes officiels sont déjà déclarés dans le registre du test.
import type { ProcedureCountry } from "./types";

export const US: ProcedureCountry = {
  country: "US",
  decentralised: true,
  subdivisionKey: "admin_area = nom complet de l'État, p. ex. \"New York\"",
  frame: {
    fr: "Aux États-Unis, aucun permis fédéral ne porte sur un data center : c'est la commune ou le comté qui autorise, sous la loi de son État. Et chaque État a sa propre loi d'accès aux documents — de trois jours ouvrés au Missouri à trente au Maryland, et aucun délai du tout au Texas.",
    en: "In the United States no federal permit covers a data centre: the town or county authorises it, under its own state's law. And every state has its own public-records law — from three business days in Missouri to thirty in Maryland, and no deadline at all in Texas.",
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
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide, étude acoustique — s'obtient par une demande écrite FOIL : l'administration doit agir dans les cinq jours ouvrés.",
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
    "Arizona": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État. Le délai : « promptement » — AUCUN nombre de jours. Un défaut de réponse prompte vaut refus, ce qui ouvre le recours.",
            en: "Any record held by the town, the county or the development agency is obtained by a written request under the state's public-records law. The deadline: “promptly” — NO number of days. A failure to respond promptly counts as a denial, which opens the appeal.",
          },
          cite: "A.R.S. § 39-121.01(D)(1)",
          url: "https://www.azleg.gov/ars/39/00121-01.htm",
          verified: "2026-10-24",
        },
      ],
    },
    "California": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de dix jours.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within ten days.",
          },
          cite: "Cal. Gov. Code § 7922.535(a)",
          url: "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=GOV&sectionNum=7922.535",
          verified: "2026-10-24",
        },
      ],
    },
    "Connecticut": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État. Un refus doit être notifié PAR ÉCRIT dans les quatre jours ouvrés — dix lorsque la demande porte sur des données nominatives de personnels. Un silence au-delà vaut refus et ouvre le recours.",
            en: "Any record held by the town, the county or the development agency is obtained by a written request under the state's public-records law. A denial must be given IN WRITING within four business days — ten where the request covers personnel data. Silence beyond that counts as a denial and opens the appeal.",
          },
          cite: "Conn. Gen. Stat. § 1-206(a)",
          url: "https://www.cga.ct.gov/current/pub/chap_014.htm",
          verified: "2026-10-24",
        },
      ],
    },
    "Delaware": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de quinze jours ouvrés.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within fifteen business days.",
          },
          cite: "29 Del. C. § 10003(h)(1)",
          url: "https://delcode.delaware.gov/title29/c100/index.html",
          verified: "2026-10-24",
        },
      ],
    },
    "District of Columbia": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de quinze jours, samedis, dimanches et jours fériés non comptés.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within fifteen days, excluding Saturdays, Sundays and legal holidays.",
          },
          cite: "D.C. Code § 2-532(c)(1)",
          url: "https://code.dccouncil.gov/us/dc/council/code/sections/2-532",
          verified: "2026-10-24",
        },
      ],
    },
    "Florida": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État. Le délai : « promptement » et « de bonne foi » — AUCUN nombre de jours. Il n'y a pas d'horloge : seule la relance datée fait courir la preuve.",
            en: "Any record held by the town, the county or the development agency is obtained by a written request under the state's public-records law. The deadline: “promptly” and “in good faith” — NO number of days. There is no clock: only a dated follow-up builds the record.",
          },
          cite: "Fla. Stat. § 119.07(1)(c)",
          url: "https://m.flsenate.gov/Statutes/119.07",
          verified: "2026-10-24",
        },
      ],
    },
    "Iowa": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de vingt jours calendaires au maximum, dix jours ouvrés ordinairement.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within twenty calendar days at most, ten business days ordinarily.",
          },
          cite: "Iowa Code § 22.8(4)(d)",
          url: "https://www.legis.iowa.gov/docs/code/22.8.pdf",
          verified: "2026-10-24",
        },
      ],
    },
    "Kansas": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de trois jours ouvrés.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within three business days.",
          },
          cite: "K.S.A. § 45-218(d)",
          url: "https://ksrevisor.gov/statutes/chapters/ch45/045_002_0018.html",
          verified: "2026-10-24",
        },
      ],
    },
    "Maine": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État. L'administration doit ACCUSER RÉCEPTION de la demande dans les cinq jours ouvrés. L'accusé n'est pas la communication : c'est le point de départ, pas l'arrivée.",
            en: "Any record held by the town, the county or the development agency is obtained by a written request under the state's public-records law. The agency must ACKNOWLEDGE the request within five working days. The acknowledgement is not the disclosure: it is the start, not the finish.",
          },
          cite: "1 M.R.S. § 408-A(3)",
          url: "https://legislature.maine.gov/statutes/1/title1sec408-A.html",
          verified: "2026-10-24",
        },
      ],
    },
    "Maryland": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de trente jours.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within thirty days.",
          },
          cite: "Md. Code, Gen. Prov. § 4-203(a)(1)",
          url: "https://mgaleg.maryland.gov/mgawebsite/Laws/StatuteText?article=ggp&section=4-203&enactments=false",
          verified: "2026-10-24",
        },
      ],
    },
    "Minnesota": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État. Le délai : « dès que raisonnablement possible » — AUCUN nombre de jours. Il n'y a pas d'horloge : seule la relance datée fait courir la preuve.",
            en: "Any record held by the town, the county or the development agency is obtained by a written request under the state's public-records law. The deadline: “as soon as reasonably possible” — NO number of days. There is no clock: only a dated follow-up builds the record.",
          },
          cite: "Minn. Stat. § 13.03, subd. 3",
          url: "https://www.revisor.mn.gov/statutes/cite/13.03",
          verified: "2026-10-24",
        },
      ],
    },
    "Missouri": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de trois jours ouvrés.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within three business days.",
          },
          cite: "Mo. Rev. Stat. § 610.023.3",
          url: "https://revisor.mo.gov/main/OneSection.aspx?section=610.023",
          verified: "2026-10-24",
        },
      ],
    },
    "Montana": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État. Le délai : le droit d'examiner et de copier toute information publique est posé, mais AUCUN délai de réponse n'est fixé par la loi.",
            en: "Any record held by the town, the county or the development agency is obtained by a written request under the state's public-records law. The deadline: the right to examine and copy any public information is stated, but the statute sets NO response deadline.",
          },
          cite: "MCA § 2-6-1003",
          url: "https://mca.legmt.gov/bills/mca/title_0020/chapter_0060/part_0100/section_0030/0020-0060-0100-0030.html",
          verified: "2026-10-24",
        },
      ],
    },
    "South Carolina": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de dix jours, samedis, dimanches et jours fériés non comptés — vingt pour un document de plus de vingt-quatre mois.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within ten days, excluding Saturdays, Sundays and legal holidays — twenty for a record older than twenty-four months.",
          },
          cite: "S.C. Code § 30-4-30(C)",
          url: "https://www.scstatehouse.gov/code/t30c004.php",
          verified: "2026-10-24",
        },
      ],
    },
    "South Dakota": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de dix jours ouvrés.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within ten business days.",
          },
          cite: "SDCL § 1-27-37(1)",
          url: "https://sdlegislature.gov/Statutes/1-27-37",
          verified: "2026-10-24",
        },
      ],
    },
    "Texas": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État. Le délai : « promptement », c'est-à-dire « aussi vite que possible selon les circonstances, dans un délai raisonnable, sans retard » — AUCUN nombre de jours. Il n'y a pas d'horloge : seule la relance datée fait courir la preuve.",
            en: "Any record held by the town, the county or the development agency is obtained by a written request under the state's public-records law. The deadline: “promptly”, meaning “as soon as possible under the circumstances, that is, within a reasonable time, without delay” — NO number of days. There is no clock: only a dated follow-up builds the record.",
          },
          cite: "Tex. Gov't Code § 552.221(a)",
          url: "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
          verified: "2026-10-24",
        },
      ],
    },
    "Utah": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de dix jours ouvrés — cinq si la demande sert le public plutôt que le demandeur.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within ten business days — five where the request benefits the public rather than the requester.",
          },
          cite: "Utah Code § 63G-2-204(4)(b)",
          url: "https://le.utah.gov/xcode/Title63G/Chapter2/63G-2-S204.html",
          verified: "2026-10-24",
        },
      ],
    },
    "Vermont": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de trois jours ouvrés.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within three business days.",
          },
          cite: "1 V.S.A. § 318(a)(1)",
          url: "https://legislature.vermont.gov/statutes/section/01/005/00318",
          verified: "2026-10-24",
        },
      ],
    },
    "Virginia": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de cinq jours ouvrés.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within five working days.",
          },
          cite: "Va. Code § 2.2-3704(B)",
          url: "https://law.lis.virginia.gov/vacode/title2.2/chapter37/section2.2-3704/",
          verified: "2026-10-24",
        },
      ],
    },
    "Washington": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de cinq jours ouvrés.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within five business days.",
          },
          cite: "RCW 42.56.520(1)",
          url: "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56.520",
          verified: "2026-10-24",
        },
      ],
    },
    "West Virginia": {
      authority: {
        fr: "la commune ou le comté qui zone le terrain",
        en: "the town or county that zones the land",
      },
      windows: {},
      deadlines: [],
      documents: [
        {
          text: {
            fr: "Toute pièce détenue par la commune, le comté ou l'agence de développement — étude d'impact, demande d'aide fiscale, étude acoustique — s'obtient par une demande écrite au titre de la loi d'accès aux documents de l'État : l'administration doit répondre dans un délai de cinq jours, samedis, dimanches et jours fériés non comptés.",
            en: "Any record held by the town, the county or the development agency — impact study, tax-assistance application, acoustic study — is obtained by a written request under the state's public-records law: the agency must respond within five days, excluding Saturdays, Sundays and legal holidays.",
          },
          cite: "W. Va. Code § 29B-1-3(d)",
          url: "https://code.wvlegislature.gov/29B-1-3/",
          verified: "2026-10-24",
        },
      ],
    },
  },
};
