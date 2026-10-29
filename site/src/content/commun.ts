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

import type { Langue } from "./langues";

const FR = {
  // Le titre SERP nomme la CATÉGORIE et la COMMUNE : « data center Fouju » est la requête
  // d'un riverain ou d'un élu, c'est-à-dire exactement notre lecteur (audit SEO, 10-16).
  place: "data center à {municipality}",
  // Le repli quand la commune manque. C'était un littéral hors de toute branche, donc le
  // même mot dans les deux langues — ce qui ne veut pas dire qu'il le restera : le
  // néerlandais écrit « datacenter » en un mot.
  placeFallback: "data center",
  // L'espace insécable avant le deux-points est une règle TYPOGRAPHIQUE du français, donc
  // une propriété de la langue — comme la virgule décimale. Elle vit ici et non en code,
  // pour qu'une langue nouvelle la déclare au lieu d'aller modifier un gabarit.
  colon: " : ",
};

const EN: typeof FR = {
  place: "data center in {municipality}",
  placeFallback: "data center",
  colon: ": ",
};

/** Les chaînes partagées : `COMMUN[lang]`. */
export const COMMUN: Record<Langue, typeof FR> = { fr: FR, en: EN };
