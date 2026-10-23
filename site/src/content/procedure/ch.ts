// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Suisse — 54 fiches, réparties sur seize cantons. Pays décentralisé : le permis de
// construire est cantonal, et chaque canton fixe son propre délai de recours.
//
// 🔴 LE PIÈGE QU'ON A ÉVITÉ. L'art. 50 de la loi fédérale sur la procédure administrative
// (PA, RS 172.021) dit « 30 jours » et se trouve en deux clics. Il ne régit QUE la
// procédure devant les autorités FÉDÉRALES : le citer pour un permis cantonal serait le
// bon texte appliqué au mauvais périmètre — une erreur qui se lit comme un délai, et qui
// ferait perdre son recours à un lecteur vaudois. Le fait que Zurich aboutisse au même
// nombre de jours ne valide rien : c'est une coïncidence de son droit cantonal, pas une
// règle fédérale qui descendrait.
//
// Zurich lu au texte le 2026-10-23 sur le recueil officiel du canton (zhlex, état du
// 1.10.22). Restent quinze cantons, soit 39 des 54 fiches :
//   VD 5 · BE 5 · ZG 4 · FR 4 · GE 4 · LU 3 · JU 2 · VS 2 · TI 2 · SG 2 · BS 2
//   SO 1 · TG 1 · SH 1 · BL 1
import type { ProcedureCountry } from "./types";

export const CH: ProcedureCountry = {
  country: "CH",
  decentralised: true,
  subdivisionKey: "admin_area = sigle du canton (ZH, VD, GE…)",
  frame: {
    fr: "En Suisse, le permis de construire est cantonal : il n'existe pas de délai fédéral applicable. Nous ne publions pas de procédure pour un canton dont le droit n'a pas été lu — un délai emprunté à un autre niveau ferait perdre son recours.",
    en: "In Switzerland the building permit is cantonal: no federal deadline applies. We publish no procedure for a canton whose own law we have not read — a deadline borrowed from another level would cost the reader their appeal.",
  },
  subdivisions: {
    ZH: {
      authority: {
        fr: "la commune pour l'autorisation de construire ; recours devant l'instance de recours cantonale, puis le tribunal administratif",
        en: "the municipality for the building permit; appeal to the cantonal appeals body, then the administrative court",
      },
      windows: {},
      deadlines: [
        {
          text: {
            fr: "Trente jours pour déposer un recours écrit, à compter du lendemain de la notification de la décision — du lendemain de sa publication officielle si elle n'a pas été notifiée.",
            en: "Thirty days to file a written appeal, from the day after the decision is notified — from the day after its official publication where it was not notified.",
          },
          cite: "Verwaltungsrechtspflegegesetz (VRG, LS 175.2), § 22 Abs. 1 et 2",
          url: "https://www2.zhlex.zh.ch/appl/zhlex_r.nsf/WebView/1F43F59724E5F9EEC12588C300332E2C/$File/175.2_24.5.59_118.pdf",
          verified: "2026-10-23",
        },
        {
          text: {
            fr: "En cas d'urgence particulière, l'autorité peut réduire ce délai à cinq jours. Un délai qui expire un samedi ou un jour férié court jusqu'au jour ouvrable suivant.",
            en: "In cases of particular urgency the authority may cut that period to five days. A deadline ending on a Saturday or public holiday runs to the next working day.",
          },
          cite: "VRG § 22 Abs. 3 et § 11 Abs. 1",
          url: "https://www2.zhlex.zh.ch/appl/zhlex_r.nsf/WebView/1F43F59724E5F9EEC12588C300332E2C/$File/175.2_24.5.59_118.pdf",
          verified: "2026-10-23",
        },
      ],
      documents: [],
    },
  },
};
