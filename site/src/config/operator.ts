// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// « L'opérateur est-il IDENTIFIÉ ? » — la question est posée à quatre endroits du site, et
// elle y était répondue par quatre listes différentes. C'est ça qui a cassé, pas une graphie
// manquante (2026-10-17) :
//
//   · related.ts        ["unknown","none","inconnu",""]  → groupait les fiches « même opérateur »
//   · DcFiche, ligne op ["unknown","none",""]            → affichait « Operator: … »
//   · DcFiche, schema   !== "unknown"                    → publiait un PropertyValue "Operator"
//   · MapIsland         `p.operator ? …`                 → rien du tout
//
// La lane américaine écrivait « opérateur non identifié » : aucune des quatre ne la connaissait.
// Servi en prod sur 162 fiches × 2 langues, dont — le pire — le balisage structuré de la page
// anglaise, qui affirmait aux machines que l'exploitant de ce data center est une société
// nommée « opérateur non identifié ».
//
// Donc UNE source, et des gardes qui la dérivent. La comparaison se fait sur une forme
// normalisée (casse, accents, espaces) : « Opérateur Non Identifié » doit mourir comme
// « operateur non identifie », sans qu'on ait à écrire les deux.
//
// ⚠️ CE FICHIER EST UN FILET, PAS LE CORRECTIF. Une liste de graphies ne peut pas connaître
// la prochaine : elle ne crie pas quand elle rate, elle laisse passer. Le correctif de fond
// est en amont — une absence d'opérateur s'écrit `null` — et il a été fait côté collecte le
// 2026-10-17 (653 fiches US, writer corrigé). Le filet reste parce qu'un vieux seed, un
// nouveau pays ou une source non encore vue peuvent rouvrir la porte.
const ABSENCE_DECLAREE = new Set([
  "", "unknown", "none", "n/a", "na", "null", "nc",
  "inconnu", "non identifie", "operateur non identifie", "operator not identified",
  "unknown — to fill", "unknown - to fill", "to fill", "a renseigner",
]);

const normalise = (o: string) =>
  o.trim().toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/\s+/g, " ");

/**
 * Vrai quand la valeur NOMME un exploitant. Faux pour une absence, quelle que soit sa forme —
 * champ vide, `null`, ou prose qui décrit le vide.
 *
 * Tout ce qui affiche, groupe ou balise un opérateur passe par ici. Un `if (dc.operator)` nu
 * est un bug en attente : il est vrai pour « opérateur non identifié ».
 */
export const operateurIdentifie = (o?: string | null): o is string =>
  typeof o === "string" && !ABSENCE_DECLAREE.has(normalise(o));
