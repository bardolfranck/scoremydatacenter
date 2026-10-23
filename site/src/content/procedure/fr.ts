// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// France — the authorisation is national in substance (code de l'environnement),
// instructed by the préfet de département. Not decentralised: the same articles
// apply in the Ain and in the Nord, so one national block covers all 70
// départements of the corpus. The régional agrément (Île-de-France, over
// 5 000 m²) is a filter ON TOP, not a different procedure.
//
// Every claim below was read on Légifrance in the version in force (2026-10-22)
// and is already served on /fr/comprendre — same text, one source.
import type { ProcedureCountry } from "./types";

export const FR: ProcedureCountry = {
  country: "FR",
  decentralised: false,
  national: {
    authority: {
      fr: "le préfet de département, après enquête publique",
      en: "the département préfet, after a public inquiry",
    },
    windows: {
      announced: {
        text: {
          fr: "Rien n'est encore déposé : la délibération du conseil municipal sur le terrain et sur l'urbanisme se prend maintenant, avant tout dossier.",
          en: "Nothing is filed yet: the municipal council's votes on the land and on planning happen now, before any application.",
        },
        cite: "Code de l'environnement, art. L. 123-9",
        url: "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033038541",
        verified: "2026-10-22",
      },
      permitting: {
        text: {
          fr: "C'est la fenêtre utile : une observation écrite pendant l'enquête publique entre au dossier et appelle une réponse du commissaire enquêteur.",
          en: "This is the useful window: a written observation during the public inquiry enters the file and requires an answer from the inquiry commissioner.",
        },
        cite: "Code de l'environnement, art. L. 123-9",
        url: "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033038541",
        verified: "2026-10-22",
      },
      operational: {
        text: {
          fr: "Le site fonctionne : reste la réclamation au préfet sur l'insuffisance des prescriptions — bruit, rejets, eau.",
          en: "The site is running: what remains is a claim to the préfet that the operating conditions are insufficient — noise, discharges, water.",
        },
        cite: "Code de l'environnement, art. R. 181-52",
        url: "https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006074220/LEGISCTA000033929087",
        verified: "2026-10-22",
      },
    },
    deadlines: [
      {
        text: {
          fr: "Après l'autorisation, le recours des tiers est de deux mois à compter de l'affichage et de la publication — et il ne se rattrape pas.",
          en: "Once authorised, third parties have two months from the posting and publication to appeal — and it does not come back.",
        },
        cite: "Code de l'environnement, art. R. 181-50 (décret n° 2024-423 du 10 mai 2024)",
        url: "https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006074220/LEGISCTA000033929087",
        verified: "2026-10-22",
      },
      {
        text: {
          fr: "Le recours doit être notifié à l'auteur de la décision et au bénéficiaire dans les quinze jours, sous peine d'irrecevabilité.",
          en: "The appeal must be notified to the issuing authority and to the beneficiary within fifteen days, or it is inadmissible.",
        },
        cite: "Code de l'environnement, art. R. 181-51",
        url: "https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006074220/LEGISCTA000033929087",
        verified: "2026-10-22",
      },
      {
        text: {
          fr: "Qui achète ou loue après l'affichage de l'autorisation ne peut plus contester les inconvénients qu'elle autorise.",
          en: "Anyone who buys or rents after the authorisation is posted can no longer challenge the nuisances it allows.",
        },
        cite: "Code de l'environnement, art. L. 514-6, III",
        url: "https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006074220/LEGISCTA000006176598",
        verified: "2026-10-22",
      },
    ],
    documents: [
      {
        text: {
          fr: "Le dossier d'enquête — étude d'impact, étude acoustique, avis de l'autorité environnementale — est consultable en mairie et en ligne pendant toute l'enquête.",
          en: "The inquiry file — impact assessment, acoustic study, environmental authority opinion — is open at the town hall and online for the whole inquiry.",
        },
        cite: "Code de l'environnement, art. L. 123-9",
        url: "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033038541",
        verified: "2026-10-22",
      },
    ],
  },
};
