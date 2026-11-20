// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Le bloc « Documents officiels » de la fiche (2026-11-20), un bloc par langue (i18n §13).
//
// RÈGLE « on ouvre la vérité, on vend le temps » (Franck 2026-11-20) : la fiche sert, pour
// chaque fait, le LIEN vers l'autorité qui l'a publié et sa DATE. La copie archivée,
// l'extraction et la chronologie restent privées. Ce bloc ne nomme donc que des actes et des
// autorités : il ne résume pas leur contenu, et il ne pèse pas sur la note.
//
// 🔴 `types` doit couvrir EXACTEMENT l'énumération `identity.official_documents[].type` du
// schéma (data/schema/datacenter.schema.json), et `supports` celle de `supports`. Une liste à
// deux endroits ment : le garde est engine/tests/test_official_documents.py, qui compare
// les deux. Un type sans libellé rendrait `undefined` en silence (astro build sans check).

import type { LangueDeclaree } from "./langues";

const FR = {
  titre: "Documents officiels",
  intro: "Les actes publiés par les autorités sur ce site, chacun daté et relié à l'autorité qui l'a publié. Ils documentent des faits ; ils n'entrent pas dans la note.",
  reference: "réf.",
  atteste: "atteste :",
  verifie: "lien vérifié le {date}",
  supports: {
    project_status: "le statut du projet",
    developer: "le porteur du projet",
    existence: "l'existence du site",
  },
  types: {
    planning_decision: "Décision d'urbanisme",
    appeal_decision: "Décision en appel",
    licence: "Licence environnementale",
    annual_environmental_report: "Rapport environnemental annuel",
    gazette_notice: "Avis au journal officiel",
    air_permit: "Permis d'émissions atmosphériques",
    construction_registration: "Enregistrement de chantier",
    environmental_notice: "Avis environnemental",
    environmental_record: "Inscription au registre environnemental",
    facility_registry: "Inscription au registre des installations",
    regulatory_filing: "Déclaration réglementaire",
    county_record: "Acte du comté",
    municipal_record: "Acte municipal",
    state_record: "Acte de l'État fédéré",
    parcel_record: "Fiche cadastrale",
    public_report: "Rapport public",
    public_statement: "Communiqué officiel",
  },
  datePattern: "{j}/{m}/{a}",
};

const EN: typeof FR = {
  titre: "Official documents",
  intro: "Acts published by public authorities about this site, each dated and linked to the authority that published it. They document facts; they are not part of the score.",
  reference: "ref.",
  atteste: "attests:",
  verifie: "link checked on {date}",
  supports: {
    project_status: "the project status",
    developer: "the project applicant",
    existence: "that the site exists",
  },
  types: {
    planning_decision: "Planning decision",
    appeal_decision: "Appeal decision",
    licence: "Environmental licence",
    annual_environmental_report: "Annual environmental report",
    gazette_notice: "Official gazette notice",
    air_permit: "Air permit",
    construction_registration: "Construction registration",
    environmental_notice: "Environmental notice",
    environmental_record: "Environmental registry record",
    facility_registry: "Facility registry entry",
    regulatory_filing: "Regulatory filing",
    county_record: "County record",
    municipal_record: "Municipal record",
    state_record: "State record",
    parcel_record: "Parcel record",
    public_report: "Public report",
    public_statement: "Official statement",
  },
  datePattern: "{a}-{m}-{j}",
};

const NL: typeof FR = {
  titre: "Officiële documenten",
  intro: "Door overheden gepubliceerde stukken over deze site, elk gedateerd en gekoppeld aan de instantie die het publiceerde. Ze documenteren feiten; ze tellen niet mee in het cijfer.",
  reference: "kenmerk",
  atteste: "staaft:",
  verifie: "link gecontroleerd op {date}",
  supports: {
    project_status: "de projectstatus",
    developer: "de initiatiefnemer",
    existence: "het bestaan van de site",
  },
  types: {
    planning_decision: "Besluit over de bouwaanvraag",
    appeal_decision: "Uitspraak in beroep",
    licence: "Milieuvergunning",
    annual_environmental_report: "Jaarlijks milieuverslag",
    gazette_notice: "Officiële bekendmaking",
    air_permit: "Vergunning voor luchtemissies",
    construction_registration: "Registratie van bouwwerken",
    environmental_notice: "Milieukennisgeving",
    environmental_record: "Vermelding in het milieuregister",
    facility_registry: "Vermelding in het inrichtingenregister",
    regulatory_filing: "Verplichte deponering bij de toezichthouder",
    county_record: "Stuk van de county",
    municipal_record: "Gemeentelijk stuk",
    state_record: "Stuk van de deelstaat",
    parcel_record: "Kadastrale gegevens",
    public_report: "Openbaar rapport",
    public_statement: "Officiële verklaring",
  },
  datePattern: "{j}-{m}-{a}",
};

/** La copie du bloc « Documents officiels » : `DOCUMENTS_OFFICIELS[lang]`. */
export const DOCUMENTS_OFFICIELS: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
