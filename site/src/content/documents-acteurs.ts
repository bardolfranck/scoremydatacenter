// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Le bloc « Documents des acteurs du projet » de la fiche (Franck 2026-11-21), un bloc par
// langue (i18n §13). Ce sont les DÉCLARATIONS de l'exploitant, du porteur, de l'architecte,
// du bureau d'études ou de l'entreprise : elles documentent le projet tel que ses auteurs le
// présentent. Servies À PART des actes officiels, jamais dans la note.
//
// 🔴 `roles`, `types` et `supports` couvrent EXACTEMENT les énumérations de
// `identity.project_party_documents` (data/schema/datacenter.schema.json). Garde :
// engine/tests/test_dictionnaire_documents.py.

import type { LangueDeclaree } from "./langues";

const FR = {
  titre: "Documents des acteurs du projet",
  intro: "Publiés par l'exploitant, le porteur du projet ou leurs prestataires. Ce sont leurs déclarations, reliées à leur source.",
  sansDate: "non daté",
  documente: "documente :",
  verifie: "lien vérifié le {date}",
  indisponible: "lien indisponible depuis le {date}",
  accessibleDepuis: "accessible depuis {pays}",
  roles: {
    operator: "exploitant",
    developer: "porteur du projet",
    architect: "architecte",
    engineering_firm: "bureau d'études",
    contractor: "entreprise de construction",
  },
  types: {
    project_page: "Page du projet",
    press_release: "Communiqué",
    report: "Rapport",
    presentation: "Présentation",
    case_study: "Étude de cas",
  },
  supports: {
    project_status: "le statut du projet",
    developer: "le porteur du projet",
    existence: "l'existence du site",
    operator: "l'exploitant",
  },
  datePattern: "{j}/{m}/{a}",
};

const EN: typeof FR = {
  titre: "Documents from the project's parties",
  intro: "Published by the operator, the project applicant or their contractors. These are their own statements, linked to their source.",
  sansDate: "undated",
  documente: "documents:",
  verifie: "link checked on {date}",
  indisponible: "link unavailable since {date}",
  accessibleDepuis: "accessible from {pays}",
  roles: {
    operator: "operator",
    developer: "project applicant",
    architect: "architect",
    engineering_firm: "engineering firm",
    contractor: "construction contractor",
  },
  types: {
    project_page: "Project page",
    press_release: "Press release",
    report: "Report",
    presentation: "Presentation",
    case_study: "Case study",
  },
  supports: {
    project_status: "the project status",
    developer: "the project applicant",
    existence: "that the site exists",
    operator: "the operator",
  },
  datePattern: "{a}-{m}-{j}",
};

const NL: typeof FR = {
  titre: "Documenten van projectbetrokkenen",
  intro: "Gepubliceerd door de exploitant, de initiatiefnemer of hun opdrachtnemers. Het zijn hun eigen verklaringen, gekoppeld aan hun bron.",
  sansDate: "ongedateerd",
  documente: "documenteert:",
  verifie: "link gecontroleerd op {date}",
  indisponible: "link niet beschikbaar sinds {date}",
  accessibleDepuis: "alleen toegankelijk vanuit {pays}",
  roles: {
    operator: "exploitant",
    developer: "initiatiefnemer",
    architect: "architect",
    engineering_firm: "ingenieursbureau",
    contractor: "bouwbedrijf",
  },
  types: {
    project_page: "Projectpagina",
    press_release: "Persbericht",
    report: "Rapport",
    presentation: "Presentatie",
    case_study: "Casestudy",
  },
  supports: {
    project_status: "de projectstatus",
    developer: "de initiatiefnemer",
    existence: "het bestaan van de site",
    operator: "de exploitant",
  },
  datePattern: "{j}-{m}-{a}",
};

/** La copie du bloc « Documents des acteurs du projet » : `DOCUMENTS_ACTEURS[lang]`. */
export const DOCUMENTS_ACTEURS: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
