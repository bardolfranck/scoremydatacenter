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
      nl: "de prefect van het departement, na de inspraak",
    },
    windows: {
      announced: {
        text: {
          fr: "Rien n'est encore déposé : la délibération du conseil municipal sur le terrain et sur l'urbanisme se prend maintenant, avant tout dossier.",
          en: "Nothing is filed yet: the municipal council's votes on the land and on planning happen now, before any application.",
          nl: "Er is nog niets ingediend: het raadsbesluit van de gemeenteraad over de grond en over de ruimtelijke ordening valt nú, vóór enig dossier.",
        },
        cite: "Code de l'environnement, art. L. 123-9",
        url: "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033038541",
        verified: "2026-10-22",
      },
      permitting: {
        text: {
          fr: "C'est la fenêtre utile : une observation écrite pendant l'enquête publique entre au dossier et appelle une réponse du commissaire enquêteur.",
          en: "This is the useful window: a written observation during the public inquiry enters the file and requires an answer from the inquiry commissioner.",
          nl: "Dit is het nuttige venster: een schriftelijke opmerking tijdens de inspraak komt in het dossier en vraagt om een antwoord van de onderzoekscommissaris.",
        },
        cite: "Code de l'environnement, art. L. 123-9",
        url: "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033038541",
        verified: "2026-10-22",
      },
      operational: {
        text: {
          fr: "Le site fonctionne : reste la réclamation au préfet sur l'insuffisance des prescriptions — bruit, rejets, eau.",
          en: "The site is running: what remains is a claim to the préfet that the operating conditions are insufficient — noise, discharges, water.",
          nl: "De site draait: wat rest is de klacht bij de prefect over ontoereikende voorschriften — geluid, lozingen, water.",
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
          nl: "Na de vergunning hebben derden twee maanden om in beroep te gaan, te rekenen vanaf de aanplakking en de publicatie — en die termijn is fataal.",
        },
        cite: "Code de l'environnement, art. R. 181-50 (décret n° 2024-423 du 10 mai 2024)",
        url: "https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006074220/LEGISCTA000033929087",
        verified: "2026-10-22",
      },
      {
        text: {
          fr: "Le recours doit être notifié à l'auteur de la décision et au bénéficiaire dans les quinze jours, sous peine d'irrecevabilité.",
          en: "The appeal must be notified to the issuing authority and to the beneficiary within fifteen days, or it is inadmissible.",
          nl: "Het beroep moet binnen vijftien dagen worden gemeld aan de autoriteit die het besluit nam en aan de begunstigde, op straffe van niet-ontvankelijkheid.",
        },
        cite: "Code de l'environnement, art. R. 181-51",
        url: "https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006074220/LEGISCTA000033929087",
        verified: "2026-10-22",
      },
      {
        text: {
          fr: "Qui achète ou loue après l'affichage de l'autorisation ne peut plus contester les inconvénients qu'elle autorise.",
          en: "Anyone who buys or rents after the authorisation is posted can no longer challenge the nuisances it allows.",
          nl: "Wie koopt of huurt nadat de vergunning is aangeplakt, kan de hinder die ze toestaat niet meer aanvechten.",
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
          nl: "Het inspraakdossier — milieueffectrapport, akoestisch onderzoek, advies van de milieuautoriteit — is in het gemeentehuis en online in te zien zolang de inspraak loopt.",
        },
        cite: "Code de l'environnement, art. L. 123-9",
        url: "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033038541",
        verified: "2026-10-22",
      },
    ],
  },
};
