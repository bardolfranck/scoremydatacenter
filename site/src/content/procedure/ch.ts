// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Suisse — 54 fiches sur seize cantons. Pays décentralisé : le permis de construire est
// cantonal, et CHAQUE CANTON FIXE SON PROPRE DÉLAI.
//
// 🔴 CE FICHIER EST LA DÉMONSTRATION DE CE QU'ON A ÉVITÉ. L'art. 50 de la loi fédérale sur
// la procédure administrative (PA, RS 172.021) dit « 30 jours » et se trouve en deux clics.
// Il ne régit QUE la procédure devant les autorités fédérales. Voici ce que donnent les
// treize cantons lus au texte le 2026-10-23 :
//
//     30 jours  ZH · BE · FR · GE · VS · TG
//     20 jours  ZG · LU · SH
//     14 jours  SG
//     10 jours  SO · BS · BL
//
// Publier le chiffre fédéral aurait donné raison dans six cantons et tort dans sept — à
// Soleure, Bâle-Ville et Bâle-Campagne, le lecteur aurait découvert son délai forclos avec
// vingt jours de retard. Et le fait que Zurich, le plus gros canton du corpus, tombe
// justement sur trente jours est précisément ce qui aurait empêché de s'en apercevoir.
//
// TROIS PIÈGES qu'aucun autre pays du corpus ne porte :
//   · Zoug et Schaffhouse — l'autorité peut RÉDUIRE le délai à 48 heures en cas d'urgence.
//   · Zurich — même pouvoir, jusqu'à cinq jours.
//   · Bâle-Ville — deux temps : dix jours pour ANNONCER le recours, trente pour le motiver.
//
// ⚠️ Pas de fabrique ici, bien que les treize blocs se ressemblent : une fonction qui
// estampille la date de lecture pour tout le fichier fait passer le test qui l'exige
// affirmation par affirmation, et le jour où un canton est corrigé seul, il hériterait
// en silence de la date des douze autres. Verbeux, mais chaque ligne se vérifie.
//
// Restent VD (5 fiches), JU (2) et TI (2) : leurs recueils officiels ne servent qu'une
// application monopage illisible hors navigateur (Vaud) ou des PDF de versions périmées
// (Jura, celle indexée courait jusqu'au 31 décembre 2010). Mieux vaut trois cantons
// déclarés manquants qu'un délai lu sur un texte abrogé.
import type { ProcedureCountry } from "./types";

export const CH: ProcedureCountry = {
  country: "CH",
  decentralised: true,
  subdivisionKey: "admin_area = sigle du canton (ZH, VD, GE…)",
  frame: {
    fr: "En Suisse, le permis de construire est cantonal et chaque canton fixe son propre délai de recours : de dix jours à Soleure et dans les deux Bâle à trente à Zurich et Genève. Il n'existe aucun délai fédéral applicable, et nous ne publions rien pour un canton dont le droit n'a pas été lu.",
    en: "In Switzerland the building permit is cantonal and each canton sets its own appeal deadline: from ten days in Solothurn and the two Basels to thirty in Zurich and Geneva. No federal deadline applies, and we publish nothing for a canton whose own law we have not read.",
  },
  subdivisions: {
    ZH: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance de recours cantonale",
        en: "the municipality for the building permit, then the cantonal appeals body",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Trente jours pour déposer un recours écrit, à compter du lendemain de la notification — du lendemain de la publication officielle si la décision n'a pas été notifiée.",
            en: "Thirty days to file a written appeal, from the day after notification — from the day after official publication where the decision was not notified.",
          },
          cite: "Verwaltungsrechtspflegegesetz (VRG, LS 175.2), § 22 Abs. 1 et 2",
          url: "https://www2.zhlex.zh.ch/appl/zhlex_r.nsf/WebView/1F43F59724E5F9EEC12588C300332E2C/$File/175.2_24.5.59_118.pdf",
          verified: "2026-10-23",
        },
        {
          text: {
            fr: "En cas d'urgence particulière, l'autorité peut réduire ce délai à cinq jours.",
            en: "In cases of particular urgency the authority may cut that period to five days.",
          },
          cite: "VRG (LS 175.2), § 22 Abs. 3",
          url: "https://www2.zhlex.zh.ch/appl/zhlex_r.nsf/WebView/1F43F59724E5F9EEC12588C300332E2C/$File/175.2_24.5.59_118.pdf",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    BE: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance de recours cantonale",
        en: "the municipality for the building permit, then the cantonal appeals body",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Trente jours pour former recours, à compter de la notification ou de la publication de la décision.",
            en: "Thirty days to lodge an appeal, from the notification or publication of the decision.",
          },
          cite: "Gesetz über die Verwaltungsrechtspflege (VRPG, BSG 155.21), Art. 67 Abs. 1",
          url: "https://www.belex.sites.be.ch/app/de/texts_of_law/155.21",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    ZG: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance de recours cantonale",
        en: "the municipality for the building permit, then the cantonal appeals body",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Vingt jours pour déposer un recours écrit après la communication de la décision — et non trente.",
            en: "Twenty days to file a written appeal after the decision is communicated — not thirty.",
          },
          cite: "Gesetz über den Rechtsschutz in Verwaltungssachen (BGS 162.1), § 43 Abs. 1",
          url: "https://bgs.zg.ch/app/de/texts_of_law/162.1",
          verified: "2026-10-23",
        },
        {
          text: {
            fr: "En cas d'urgence particulière, l'autorité peut ramener ce délai à quarante-huit heures.",
            en: "In cases of particular urgency the authority may cut that period to forty-eight hours.",
          },
          cite: "BGS 162.1, § 43 Abs. 2",
          url: "https://bgs.zg.ch/app/de/texts_of_law/162.1",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    FR: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance de recours cantonale",
        en: "the municipality for the building permit, then the cantonal appeals body",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Trente jours pour recourir — dix seulement contre une décision incidente.",
            en: "Thirty days to appeal — only ten against an incidental decision.",
          },
          cite: "Code de procédure et de juridiction administrative (CPJA, RSF 150.1), art. 79",
          url: "https://bdlf.fr.ch/app/fr/texts_of_law/150.1",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    GE: {
      authority: {
        fr: "le département cantonal pour l'autorisation de construire, puis la chambre administrative",
        en: "the cantonal department for the building permit, then the administrative chamber",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Trente jours contre une décision finale, dix contre les autres décisions. Le délai court dès le lendemain de la notification.",
            en: "Thirty days against a final decision, ten against other decisions. The period runs from the day after notification.",
          },
          cite: "Loi sur la procédure administrative (LPA, E 5 10), art. 62",
          url: "https://silgeneve.ch/legis/data/rsg_e5_10.htm",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    LU: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance de recours cantonale",
        en: "the municipality for the building permit, then the cantonal appeals body",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Vingt jours pour former opposition contre une décision finale, dix contre une décision incidente. L'opposition suspend la décision.",
            en: "Twenty days to object to a final decision, ten against an interim one. The objection suspends the decision.",
          },
          cite: "Gesetz über die Verwaltungsrechtspflege (SRL Nr. 40), § 119 Abs. 1",
          url: "https://srl.lu.ch/app/de/texts_of_law/40",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    VS: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis le Conseil d'État ou le tribunal cantonal",
        en: "the municipality for the building permit, then the Council of State or the cantonal court",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Trente jours pour déposer le recours — dix s'il s'agit d'une décision incidente.",
            en: "Thirty days to file the appeal — ten if it is an incidental decision.",
          },
          cite: "Loi sur la procédure et la juridiction administratives (LPJA, RS/VS 172.6), art. 46 al. 1",
          url: "https://lex.vs.ch/app/fr/texts_of_law/172.6",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    SG: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance de recours cantonale",
        en: "the municipality for the building permit, then the cantonal appeals body",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Quatorze jours seulement pour déposer le recours après la notification — cinq contre des mesures provisionnelles ou d'exécution.",
            en: "Fourteen days only to file the appeal after notification — five against provisional or enforcement measures.",
          },
          cite: "Gesetz über die Verwaltungsrechtspflege (sGS 951.1), Art. 47",
          url: "https://www.gesetzessammlung.sg.ch/app/de/texts_of_law/951.1",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    BS: {
      authority: {
        fr: "le département cantonal pour l'autorisation de construire, puis le tribunal administratif",
        en: "the cantonal department for the building permit, then the administrative court",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Dix jours pour ANNONCER le recours par écrit au tribunal administratif, puis trente jours au plus pour en déposer les motifs. Manquer le premier délai ferme le second.",
            en: "Ten days to DECLARE the appeal in writing to the administrative court, then at most thirty days to file its grounds. Missing the first closes the second.",
          },
          cite: "Gesetz über die Verfassungs- und Verwaltungsrechtspflege (SG 270.100), § 16",
          url: "https://www.gesetzessammlung.bs.ch/app/de/texts_of_law/270.100",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    SO: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance supérieure",
        en: "the municipality for the building permit, then the higher authority",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Dix jours — le délai le plus court du corpus suisse — à compter de la remise de la décision.",
            en: "Ten days — the shortest in the Swiss corpus — from service of the decision.",
          },
          cite: "Gesetz über den Rechtsschutz in Verwaltungssachen (BGS 124.11), § 32 Abs. 1",
          url: "https://bgs.so.ch/app/de/texts_of_law/124.11",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    TG: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance de recours cantonale",
        en: "the municipality for the building permit, then the cantonal appeals body",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Trente jours pour déposer le mémoire de recours, qui doit porter des conclusions, des motifs et les moyens de preuve.",
            en: "Thirty days to file the appeal, which must carry its claims, its grounds and its evidence.",
          },
          cite: "Gesetz über die Verwaltungsrechtspflege (RB 170.1), § 45 Abs. 1",
          url: "https://www.rechtsbuch.tg.ch/app/de/texts_of_law/170.1",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    SH: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance de recours cantonale",
        en: "the municipality for the building permit, then the cantonal appeals body",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Vingt jours après la communication de la décision — ou, à défaut, après en avoir eu connaissance.",
            en: "Twenty days after the decision is communicated — or, failing that, after learning of it.",
          },
          cite: "Gesetz über den Rechtsschutz in Verwaltungssachen (SHR 172.200), Art. 20 Abs. 1",
          url: "https://www.rechtsbuch.sh.ch/app/de/texts_of_law/172.200",
          verified: "2026-10-23",
        },
        {
          text: {
            fr: "En cas d'urgence particulière, l'autorité peut ramener ce délai à quarante-huit heures.",
            en: "In cases of particular urgency the authority may cut that period to forty-eight hours.",
          },
          cite: "SHR 172.200, Art. 20 Abs. 2",
          url: "https://www.rechtsbuch.sh.ch/app/de/texts_of_law/172.200",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
    BL: {
      authority: {
        fr: "la commune pour l'autorisation de construire, puis l'instance de recours cantonale",
        en: "the municipality for the building permit, then the cantonal appeals body",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Dix jours à compter de la notification. Un tiers que l'autorité ne connaissait pas dispose de dix jours à compter du moment où il a connaissance de la décision.",
            en: "Ten days from notification. A third party unknown to the authority has ten days from the moment they learn of the decision.",
          },
          cite: "Verwaltungsverfahrensgesetz (SGS 175), § 33 Abs. 1 et 2",
          url: "https://bl.clex.ch/app/de/texts_of_law/175",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
  },
};
