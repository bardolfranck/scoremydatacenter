// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Les chaînes servies par PLUSIEURS surfaces — et uniquement celles-là.
//
// 🔴 Ce fichier existe pour une raison précise, pas par goût du partage : la fiche et le
// portrait construisaient la MÊME phrase de lieu (« data center à {commune} »), chacun dans
// sa table, avec la même logique de repli. Deux copies d'une phrase ne restent pas longtemps
// identiques : on améliore le titre SEO de la fiche, et le portrait garde l'ancien sans que
// rien ne le dise. Une langue nouvelle aurait eu, elle, deux endroits à remplir pour une
// seule phrase.
//
// ⚠️ N'y mettre une chaîne QUE si deux surfaces la servent déjà. Un module « commun » qui
// accueille tout ce qui pourrait servir ailleurs devient un fourre-tout, et on ne sait plus
// quelle page on casse en le touchant.

import type { Langue, LangueDeclaree } from "./langues";

const FR = {
  // Le titre SERP nomme la CATÉGORIE et la COMMUNE : « data center Fouju » est la requête
  // d'un riverain ou d'un élu, c'est-à-dire exactement notre lecteur (audit SEO, 10-16).
  place: "data center à {municipality}",
  // Site hors des limites d'une ville (US : terrain non incorporé) : la juridiction réelle
  // est le comté, mais la recherche passe par la ville que citent la presse et le dossier.
  placeNear: "data center près de {reference_place} ({municipality})",
  near: "près de",
  // Le repli quand la commune manque. C'était un littéral hors de toute branche, donc le
  // même mot dans les deux langues — ce qui ne veut pas dire qu'il le restera : le
  // néerlandais écrit « datacenter » en un mot.
  placeFallback: "data center",
  // L'espace insécable avant le deux-points est une règle TYPOGRAPHIQUE du français, donc
  // une propriété de la langue — comme la virgule décimale. Elle vit ici et non en code,
  // pour qu'une langue nouvelle la déclare au lieu d'aller modifier un gabarit.
  colon: " : ",
  // Même nature que le deux-points : le français met une espace avant le point
  // d'interrogation, l'anglais et le néerlandais non. C'était écrit en dur dans la fonction
  // qui compose les questions du portrait — avec les deux langues énumérées à la main, donc
  // la troisième perdue en silence [[absence-ressemble-a-zero]].
  interrogation: " ?",
};

const EN: typeof FR = {
  place: "data center in {municipality}",
  placeNear: "data center near {reference_place} ({municipality})",
  near: "near",
  placeFallback: "data center",
  colon: ": ",
  interrogation: "?",
};


// ── NÉERLANDAIS — EN PRÉPARATION, PAS ENCORE SERVI (voir `content/langues.ts`).
// ⚠️ Les valeurs ci-dessous sont encore LE TEXTE FRANÇAIS, copié tel quel. Elles sont là
// pour qu'un traducteur natif ait la source sous les yeux, à sa place dans la structure.
// Elles NE DOIVENT PAS partir en ligne : `nl` n'est pas dans `LANGUES_VIVANTES`, et
// `test_une_langue_ne_devient_vivante_que_traduite` refuse de l'y faire entrer tant que
// ses valeurs sont celles du français.
const NL: typeof FR = {
  // Le titre SERP nomme la CATÉGORIE et la COMMUNE — en néerlandais la requête du
  // riverain est « datacenter Almere » : datacenter EN UN MOT (lexique du rapport figé).
  place: "datacenter in {municipality}",
  placeNear: "datacenter bij {reference_place} ({municipality})",
  near: "bij",
  placeFallback: "datacenter",
  // Pas d'espace avant le deux-points ni avant le point d'interrogation en néerlandais
  // (convention typographique NL, la même que l'anglais).
  colon: ": ",
  interrogation: "?",
};

/** Les chaînes partagées : `COMMUN[lang]`. */
export const COMMUN: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
