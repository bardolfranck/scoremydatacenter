// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Pologne — 70 fiches, le plus gros des cinq trous. Le permis (pozwolenie na budowę) est délivré
// par le starosta (niveau powiat / district), mais le délai pour faire appel est NATIONAL et
// uniforme — quatorze jours, Code de procédure administrative (KPA). Comme NL/LU, l'autorité nomme
// le décideur local, la loi fixe le délai (decentralised: false).
//
// RÉSERVE DE L'ART. 129 § 3 VÉRIFIÉE : le § 3 réserve le cas où « des dispositions particulières
// prévoient d'autres délais ». Le droit de la construction (Prawo budowlane) n'en fixe aucun pour
// l'odwołanie : l'appel contre un pozwolenie na budowę suit le délai général de quatorze jours du KPA
// (pratique constante et concordante des services d'architecture des voïvodies). La réserve n'est donc
// pas déclenchée. L'odwołanie (appel administratif au voïvode) est la PREMIÈRE échéance ; une skarga
// ultérieure au tribunal administratif de voïvodie existe mais n'est pas le délai qui tombe en premier.
//
// Texte lu dans le texte unifié EN VIGUEUR (Dz.U. 2025 poz. 1691, publié le 3 décembre 2025),
// obtenu en PDF sur dziennikustaw.gov.pl, le 2026-10-27. ISAP ne sert que des PDF et bloque la lecture
// automatisée ; dziennikustaw.gov.pl sert le même texte officiel, lisible.
import type { ProcedureCountry } from "./types";

export const PL: ProcedureCountry = {
  country: "PL",
  decentralised: false,
  inherits: "EU",
  national: {
    authority: {
      fr: "le starosta, ou le président d'une ville à statut de powiat ; l'appel monte au voïvode (wojewoda)",
      en: "the starosta (district head), or the mayor of a city with powiat status; the appeal goes up to the voivode (wojewoda)",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Quatorze jours pour faire appel de la décision (odwołanie), par l'intermédiaire de l'autorité qui l'a rendue, à compter de sa notification. Passé ce délai, la décision devient définitive.",
          en: "Fourteen days to appeal the decision (odwołanie), through the authority that issued it, from the day it is served. After that, the decision becomes final.",
        },
        cite: "Ustawa z dnia 14 czerwca 1960 r. — Kodeks postępowania administracyjnego, art. 129 § 2",
        url: "https://dziennikustaw.gov.pl/D2025000169101.pdf",
        verified: "2026-10-27",
      },
      {
        text: {
          fr: "Faire appel dans le délai SUSPEND l'exécution de la décision : les travaux ne peuvent pas démarrer tant que l'appel est pendant, sauf si la décision a reçu la force exécutoire immédiate.",
          en: "Filing the appeal in time SUSPENDS the decision: works cannot start while the appeal is pending, unless the decision was given immediate enforceability.",
        },
        cite: "Ustawa z dnia 14 czerwca 1960 r. — Kodeks postępowania administracyjnego, art. 130 § 2 (exception : § 3)",
        url: "https://dziennikustaw.gov.pl/D2025000169101.pdf",
        verified: "2026-10-27",
      },
    ],
    documents: [],
  },
};
