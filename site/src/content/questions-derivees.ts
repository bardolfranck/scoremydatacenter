// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// LES QUESTIONS DU PORTRAIT — DÉRIVÉES, JAMAIS RÉDIGÉES.
//
// 🔴 LA DISTINCTION QUI FAIT TOUT : BLOC PROJET ≠ BLOC BASE.
// Un indicateur du bloc PROJET/PROCESS non renseigné, c'est le porteur qui ne l'a pas
// documenté → une question à lui poser. Un indicateur du bloc BASE non collecté, c'est
// NOTRE trou de mesure → demander à un exploitant « quelle est l'intensité carbone du
// réseau local ? » n'a aucun sens, c'est à nous de la mesurer.
// La maquette du portrait tirait « à demander : quel poste, quelle capacité » de E2, qui
// est un indicateur de BASE. Surligné, faux, et présenté comme issu du dossier. Seul le
// bloc projet/process engendre une question ; le bloc base alimente une liste séparée, à
// notre voix (« ce que nous n'avons pas mesuré »).
//
// TROIS TABLES QUI SE MULTIPLIENT, zéro prose écrite à la main :
//   · une QUESTION par indicateur (onze) ;
//   · une AMORCE par état de l'indicateur (deux) ;
//   · un VERBE par stade de la procédure (quatre) — et ce verbe vient du dossier
//     juridique : sans lui, une question est un vœu ; avec lui, c'est une action datée.

export type EtatIndicateur = "not_collected" | "missing";
export type StadeProjet =
  | "announced"
  | "permitting"
  | "under_construction"
  | "operational"
  | "unknown";

/** Une question par indicateur du bloc projet/process. Aucune pour le bloc base. */
export const QUESTIONS: Record<string, { fr: string; en: string; nl?: string }> = {
  E4: { fr: "Quel PUE est annoncé, et calculé sur quelle base ?",
        en: "What PUE is announced, and measured how?", nl: "Welke PUE wordt aangekondigd, en op welke basis berekend?" },
  E7: { fr: "La chaleur produite sera-t-elle récupérée, par qui, et dès quelle phase ?",
        en: "Will the waste heat be recovered, by whom, and from which phase?", nl: "Wordt de restwarmte teruggewonnen, door wie, en vanaf welke fase?" },
  W4: { fr: "Quelle technologie de refroidissement, et quel volume d'eau par an ?",
        en: "Which cooling technology, and how much water a year?", nl: "Welke koeltechnologie, en welk watervolume per jaar?" },
  F4: { fr: "Quelle surface au sol, et sur quelles parcelles ?",
        en: "What ground footprint, and on which parcels?", nl: "Welk grondoppervlak, en op welke percelen?" },
  F5: { fr: "Quelles mesures d'évitement, de réduction et de compensation ?",
        en: "Which avoidance, reduction and offset measures?", nl: "Welke maatregelen om te vermijden, te verminderen en te compenseren?" },
  F6: { fr: "Le terrain est-il déjà désigné à l'urbanisation dans un document supra-communal ?",
        en: "Is the land already designated for development in a supra-municipal plan?", nl: "Is de grond al voor verstedelijking aangewezen in een bovengemeentelijk plan?" },
  F7: { fr: "Le document d'urbanisme doit-il être modifié pour ce projet ?",
        en: "Does the planning document have to be changed for this project?", nl: "Moet het ruimtelijke plan voor dit project worden gewijzigd?" },
  L4: { fr: "Combien d'emplois permanents après le chantier, et de quelle qualification ?",
        en: "How many permanent jobs after construction, and of what skill level?", nl: "Hoeveel vaste banen na de bouw, en op welk kwalificatieniveau?" },
  L5: { fr: "Quelles recettes fiscales pour la commune, sur quelle durée, avec quels abattements ?",
        en: "What tax revenue for the municipality, over what period, with what abatements?", nl: "Welke belastinginkomsten voor de gemeente, over welke periode, met welke kortingen?" },
  T1: { fr: "Quelle concertation est prévue, à quelle date, et qui y répond ?",
        en: "What consultation is planned, on what date, and who answers it?", nl: "Welk overleg is gepland, op welke datum, en wie beantwoordt het?" },
  T2: { fr: "Le dossier complet est-il consultable, où, et jusqu'à quand ?",
        en: "Is the full file open to consultation, where, and until when?", nl: "Is het volledige dossier in te zien, waar, en tot wanneer?" },
};

/**
 * L'amorce dit D'OÙ VIENT le trou, et les deux ne se lisent pas pareil : « non collecté »
 * peut être notre lecture incomplète, « absent » est un fait vérifié sur un dossier lu.
 */
export const AMORCES: Record<EtatIndicateur, { fr: string; en: string; nl?: string }> = {
  not_collected: { fr: "À demander", en: "To ask for", nl: "Te vragen" },
  missing: { fr: "Absent du dossier lu", en: "Absent from the file we read", nl: "Ontbreekt in het geraadpleegde dossier" },
};

/**
 * Le verbe dit QUAND, et c'est la fenêtre de procédure qui le donne. Il change tout : la
 * même question posée après l'autorisation ne s'obtient plus de la même façon, et parfois
 * ne s'obtient plus du tout.
 */
export const VERBES: Record<StadeProjet, { fr: string; en: string; nl?: string }> = {
  announced: {
    fr: "à demander maintenant, avant le dépôt du dossier",
    en: "to ask now, before the application is filed",
    nl: "nu te vragen, vóór de indiening van het dossier",
  },
  permitting: {
    fr: "à verser à l'enquête — une observation écrite entre au dossier et appelle une réponse",
    en: "to put to the inquiry — a written observation enters the file and requires an answer",
    nl: "in te brengen tijdens de inspraak — een schriftelijke opmerking komt in het dossier en vraagt om een antwoord",
  },
  under_construction: {
    fr: "à exiger au titre des prescriptions : l'autorisation est délivrée, le chantier a commencé",
    en: "to demand under the operating conditions: the permit is granted, work has begun",
    nl: "te eisen via de voorschriften: de vergunning is verleend, de bouw is begonnen",
  },
  operational: {
    fr: "à réclamer auprès de l'autorité — le site fonctionne, seules les prescriptions sont encore opposables",
    en: "to claim from the authority — the site is running, only its operating conditions still bite",
    nl: "op te eisen bij de autoriteit — de site draait, alleen de voorschriften zijn nog afdwingbaar",
  },
  // 🔴 Le stade n'est pas établi : on ne dit donc NI « le site fonctionne » NI « le chantier
  // a commencé ». On dit à qui demander, et quoi.
  unknown: {
    fr: "à demander à l'autorité — rien de public ne dit où en est ce site, et c'est la première chose à faire établir",
    en: "to ask the authority — no public source says where this site stands, and that is the first thing to have established",
    nl: "te vragen aan de autoriteit — geen publieke bron zegt waar deze site staat, en dat is het eerste om te laten vaststellen",
  },
};

/**
 * AFFÛTAGE PAR COMBINAISON. Une question ne dit pas la même chose selon ce que mesure un
 * AUTRE indicateur : « quel volume d'eau par an ? » pèse autrement dans un bassin déjà en
 * tension. Dérivé de deux indicateurs, donc toujours vérifiable — pas une appréciation.
 */
const AFFUTAGE: Array<{
  question: string;
  quand: (v: Record<string, unknown>) => boolean;
  ajout: { fr: string; en: string; nl?: string };
}> = [
  {
    question: "W4",
    quand: (v) => v.W1 === "high" || v.W1 === "extremely_high",
    ajout: { fr: "dans un bassin déjà en tension", en: "in a basin already under stress", nl: "in een stroomgebied dat al onder druk staat", },
  },
  {
    question: "W4",
    quand: (v) => v.W2 === "bad" || v.W2 === "poor",
    ajout: { fr: "vers un cours d'eau déjà dégradé", en: "into an already impaired watercourse", nl: "naar een al aangetaste waterloop", },
  },
  {
    question: "F4",
    quand: (v) => v.F2 === "agricultural" || v.F2 === "natural",
    ajout: { fr: "sur un sol qui n'est pas artificialisé", en: "on land that is not already developed", nl: "op grond die nog niet verhard is", },
  },
  {
    question: "L5",
    quand: (v) => typeof v.L2 === "number" && (v.L2 as number) >= 5,
    ajout: { fr: "pour une commune que le projet dépasse largement",
             en: "for a municipality the project dwarfs", nl: "voor een gemeente waar het project veel te groot voor is", },
  },
];

export interface QuestionDerivee {
  id: string;
  amorce: { fr: string; en: string; nl?: string };
  texte: { fr: string; en: string; nl?: string };
  verbe: { fr: string; en: string; nl?: string };
}

/**
 * Les questions d'une fiche, dans l'ordre de priorité : le pilier qui tire la note d'abord
 * (`dominant_drag`), puis l'ordre des indicateurs. Rien n'est choisi à la main.
 */
export function questionsPour(
  indicateurs: Array<{ id: string; block: string; status: string; pillar: string; value?: unknown }>,
  stade: string | null | undefined,
  pilierDominant?: string | null,
): QuestionDerivee[] {
  const valeurs: Record<string, unknown> = {};
  for (const i of indicateurs) if (i.value != null) valeurs[i.id] = i.value;

  // 🔴 LE REPLI ÉTAIT `operational`, et il affirmait donc « le site fonctionne » pour un
  // stade qu'aucune source ne porte — l'absence qui se lit comme la valeur la plus engageante.
  // Le repli est désormais `unknown`, qui n'affirme rien.
  const verbe = VERBES[(stade as StadeProjet) ?? "unknown"] ?? VERBES.unknown;

  const retenues = indicateurs.filter(
    (i) => (i.block === "project" || i.block === "process")
        && (i.status === "not_collected" || i.status === "missing")
        && QUESTIONS[i.id],
  );

  const poids = (i: { pillar: string }) => (pilierDominant && i.pillar === pilierDominant ? 0 : 1);
  retenues.sort((a, b) => poids(a) - poids(b));

  return retenues.map((i) => {
    const base = QUESTIONS[i.id];
    const ajouts = AFFUTAGE.filter((r) => r.question === i.id && r.quand(valeurs));
    const suffixe = (l: "fr" | "en") =>
      ajouts.length ? " — " + ajouts.map((r) => r.ajout[l]).join(", ") : "";
    return {
      id: i.id,
      amorce: AMORCES[i.status as EtatIndicateur],
      texte: {
        fr: base.fr.replace(/\s*\?$/, "") + suffixe("fr") + " ?",
        en: base.en.replace(/\s*\?$/, "") + suffixe("en") + "?",
      },
      verbe,
    };
  });
}
