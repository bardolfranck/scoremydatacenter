// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// SOCLE EUROPÉEN — ce qui est vrai dans les quinze pays de l'Union que nous notons, sans
// avoir à le réécrire quinze fois.
//
// Le droit de l'environnement européen pose trois garanties minimales que chaque État doit
// transposer, et qu'aucune transposition ne peut rogner. Les écrire une fois ici, vérifiées
// sur EUR-Lex, évite le piège de la liste parallèle : un fichier national n'a plus à dire
// que ce que sa transposition AJOUTE — et c'est là que vivent les vrais délais nationaux,
// comme les deux mois français, qui ne figurent dans aucune directive.
//
// ⚠️ Un socle est un PLANCHER, jamais un plafond. Une transposition nationale plus
// protectrice prime ; un fichier national qui dit mieux doit être lu en premier.
// Textes lus sur EUR-Lex le 2026-10-23 (versions consolidées en vigueur).
import type { ProcedureJurisdiction } from "./types";

export const EU: ProcedureJurisdiction = {
  authority: {
    fr: "l'autorité compétente désignée par l'État membre",
    en: "the competent authority designated by the Member State",
  },
  windows: {
    permitting: {
      text: {
        fr: "Quand une évaluation environnementale est requise, le public concerné dispose d'au moins trente jours pour se prononcer sur le rapport d'évaluation. Ce plancher vaut dans toute l'Union.",
        en: "Where an environmental assessment is required, the public concerned has at least thirty days to comment on the assessment report. That floor applies across the Union.",
      },
      cite: "Directive 2011/92/UE, art. 6(7) (modifié par la directive 2014/52/UE)",
      url: "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02011L0092-20140515",
      verified: "2026-10-23",
    },
  },
  deadlines: [
    {
      text: {
        fr: "Une fois l'autorisation délivrée ou refusée, son contenu, ses prescriptions et les motifs qui la fondent doivent être rendus publics — y compris la façon dont les observations du public ont été prises en compte.",
        en: "Once consent is granted or refused, its content, its conditions and the reasons behind it must be made public — including how the public's comments were taken into account.",
      },
      cite: "Directive 2011/92/UE, art. 9(1)",
      url: "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02011L0092-20140515",
      verified: "2026-10-23",
    },
    {
      text: {
        fr: "Le public concerné a droit à un recours devant un tribunal pour contester la légalité de la décision, sur le fond comme sur la procédure. Le délai, lui, est fixé par chaque État — c'est la ligne nationale qu'il faut lire.",
        en: "The public concerned has a right of review before a court to challenge the decision's legality, on substance and on procedure. The deadline itself is set by each State — that is the national line to read.",
      },
      cite: "Directive 2011/92/UE, art. 11(1)",
      url: "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02011L0092-20140515",
      verified: "2026-10-23",
    },
  ],
  documents: [
    {
      text: {
        fr: "Toute information environnementale détenue par une autorité publique s'obtient sur simple demande, sans avoir à justifier d'un intérêt, et doit être fournie dans un délai d'un mois — deux si le volume le justifie, l'autorité devant alors le dire avant l'échéance.",
        en: "Any environmental information held by a public authority is available on request, without having to state an interest, and must be supplied within one month — two if the volume warrants it, the authority having to say so before the deadline.",
      },
      cite: "Directive 2003/4/CE, art. 3(1) et 3(2)",
      url: "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32003L0004",
      verified: "2026-10-23",
    },
  ],
};
