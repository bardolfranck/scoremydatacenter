// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Luxembourg — 10 fiches. Pays unitaire : le permis (autorisation de construire) est délivré
// par le bourgmestre de la commune, mais le délai pour attaquer la décision est NATIONAL et
// uniforme — trois mois pour saisir le tribunal administratif, loi du 21 juin 1999. Comme aux
// Pays-Bas, un seul nombre à retenir ; l'autorité nomme le décideur communal, la loi fixe le délai.
//
// RÉSERVE DE L'ART. 13(1) VÉRIFIÉE : l'art. 13 s'ouvre sur « sauf dans les cas où les lois ou les
// règlements fixent un délai plus long ou plus court », donc trois mois est le délai de DROIT COMMUN.
// Il n'est écarté par aucun délai spécial pour le permis de construire : la jurisprudence constante du
// tribunal administratif applique le délai de recours contentieux de trois mois à l'autorisation de
// construire (pas de recours de pleine juridiction en la matière). Les plans PAG/PAP (actes
// réglementaires de la loi du 19 juillet 2004) relèvent d'un régime de recours distinct, non traité ici.
//
// Texte lu sur legilux.public.lu (version consolidée EN VIGUEUR, applicable au 16/09/2023) le 2026-10-27.
// Legilux signale lui-même « la version consolidée est un texte documentaire sans valeur juridique » :
// c'est le journal officiel qui reproduit son propre texte coordonné — choix assumé, même doctrine que
// les recueils cités par l'autorité qui les applique.
import type { ProcedureCountry } from "./types";

export const LU: ProcedureCountry = {
  country: "LU",
  decentralised: false,
  inherits: "EU",
  national: {
    authority: {
      fr: "le bourgmestre de la commune ; le recours se porte ensuite devant le tribunal administratif",
      en: "the municipal mayor (bourgmestre); the appeal then goes to the administrative tribunal",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Trois mois pour attaquer la décision devant le tribunal administratif — à compter de sa notification, ou du jour où vous avez pu en prendre connaissance. Un recours gracieux adressé à l'autorité avant ce délai le suspend et fait courir un nouveau délai de trois mois.",
          en: "Three months to challenge the decision before the administrative tribunal — from the day it is notified, or from the day you could become aware of it. A prior request for reconsideration (recours gracieux) sent before that deadline suspends it and starts a fresh three-month period.",
        },
        cite: "Loi du 21 juin 1999 portant règlement de procédure devant les juridictions administratives, art. 13",
        url: "https://legilux.public.lu/eli/etat/leg/loi/1999/06/21/n2/consolide/20230916",
        verified: "2026-10-27",
      },
    ],
    documents: [],
  },
};
