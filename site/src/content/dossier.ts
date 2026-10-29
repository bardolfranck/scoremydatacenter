// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Le bloc « ce que déclare le dossier environnemental », servi sur la fiche — un bloc par
// langue (i18n §13).
//
// 🔴 Cette copie vivait dans un TERNAIRE du composant (`lang === "fr" ? {…} : {…}`) : deux
// langues en dur dans l'expression, donc une troisième à insérer dans une expression plutôt
// qu'à déclarer dans une table. C'est la forme qui a laissé l'anglais décrocher deux fois.
//
// ⚠️ L'ATTRIBUTION EST LE BOUCLIER, et elle est dans ces mots : les rubriques DÉCRIVENT
// (« Groupes électrogènes et fioul »), elles ne qualifient pas (« nuisances » serait notre
// verdict). Traduire ce bloc, c'est garder cette règle : l'autorité écrit, nous rapportons.
//
// 🔴 Le type ne garde RIEN au build (`astro build` sans `astro check`) : une clé absente
// rend `undefined` en silence. Le garde qui mord est `engine/tests/test_i18n_parity.py`.

import type { Langue } from "./langues";

const FR = {
  kicker: "Ce que déclare le dossier environnemental",
  lire: "lire l'avis (PDF)", pages: "p.", petitionnaire: "pétitionnaire",
  // Les rubriques DÉCRIVENT, elles ne qualifient pas. « Groupes électrogènes et fioul »
  // plutôt que « nuisances » : nommer une nuisance serait notre verdict, et c'est exactement
  // ce que ce bloc s'interdit. Le lecteur conclut, l'autorité écrit, nous rapportons.
  secours: "Groupes électrogènes et fioul", bruit: "Bruit relevé", voisinage: "Voisinage",
  energie: "Énergie et chaleur", eau: "Eau et refroidissement", emissions: "Émissions",
  emploi: "Emploi", emprise: "Emprise et bâti", icpe: "Classement ICPE",
  reserves: "Réserves de l'autorité", autresNiv: "Autres niveaux cités dans l'avis",
  periode: "", jour: "Jour", nuit: "Nuit", mesure: "Mesure", autres: "Les autres dans l'avis",
  caveatGroupes: "puissance de secours — ce n'est pas la puissance consommée par le site",
  bruitNote: "État relevé dans l'étude d'impact, avant exploitation.",
  pasUneNote: "Ces chiffres ne sont pas une note.",
  pasUneNoteSuite: " Ils proviennent du dossier déposé par le pétitionnaire et de l'avis de l'autorité environnementale ; nous les rapportons avec leur phrase et leur page, nous ne les évaluons pas.",
  bloc: "Ce bloc n'existe que pour les projets soumis à évaluation environnementale — une minorité des sites.",
  absence: "Son absence ne signifie pas l'absence d'impact",
  absenceSuite: " : elle indique qu'aucun document public exploitable n'a été identifié dans notre corpus à ce jour.",
  niveauxLabel: "Niveaux relevés", emergenceLabel: "Émergence",
  avisPluriel: "avis d'autorité environnementale rendus sur ce site",
  sansDate: "date non confirmée",
  explication: "Explication",
  differe: "diffère d'un dossier à l'autre",
  differeNote: "Ce site a fait l'objet de plusieurs dossiers. Les valeurs qui ne sont pas les mêmes de l'un à l'autre sont signalées, et affichées côte à côte avec leur date. Un écart peut venir d'un projet redimensionné, d'une tranche différente, ou d'une donnée corrigée : l'avis ne dit pas laquelle, et nous ne le devinons pas.",
  icpeTip: "Installation classée pour la protection de l'environnement : le régime qui encadre, autorise et contrôle une activité pouvant présenter un risque ou une gêne. Chaque numéro désigne l'activité visée dans la nomenclature nationale. Être classé ne veut pas dire être dangereux : cela veut dire être encadré, et donc contrôlé.",
  // Le mot est dans la table comme les autres : il était en ternaire au point d'affichage,
  // là où on le lit — l'endroit où une langue nouvelle ne le trouve jamais.
  valeursMultiples: "{n} valeurs",
  // 🔴 LE FORMAT EST UNE PROPRIÉTÉ DE LA LANGUE, pas une branche de code. Les deux sources
  // ne datent pas pareil (le registre régional donne « 30/03/2022 », l'index national
  // « 2022-04-01 ») : la date est donc toujours recomposée dans le motif de la langue.
  // Un néerlandais écrira `{j}-{m}-{a}` sans toucher au composant.
  datePattern: "{j}/{m}/{a}",
  locale: "fr-FR",
};

const EN: typeof FR = {
  kicker: "What the environmental case file states",
  lire: "read the opinion (PDF)", pages: "p.", petitionnaire: "applicant",
  secours: "Generators and fuel", bruit: "Measured noise", voisinage: "Neighbourhood",
  energie: "Energy and heat", eau: "Water and cooling", emissions: "Emissions",
  emploi: "Employment", emprise: "Footprint and buildings", icpe: "ICPE classification",
  reserves: "Authority's reservations", autresNiv: "Other levels cited in the opinion",
  periode: "", jour: "Day", nuit: "Night", mesure: "Measure", autres: "The others in the opinion",
  caveatGroupes: "backup power — this is not the power the site draws",
  bruitNote: "State recorded in the impact assessment, before operation.",
  pasUneNote: "These figures are not a grade.",
  pasUneNoteSuite: " They come from the file submitted by the applicant and from the environmental authority's opinion; we report them with their sentence and page, we do not assess them.",
  bloc: "This block exists only for projects subject to environmental assessment — a minority of sites.",
  absence: "Its absence does not mean an absence of impact",
  absenceSuite: ": it means no usable public document has been identified in our corpus to date.",
  niveauxLabel: "Recorded levels", emergenceLabel: "Emergence",
  avisPluriel: "environmental authority opinions issued on this site",
  sansDate: "date not confirmed",
  explication: "Explanation",
  differe: "differs between filings",
  differeNote: "This site has been the subject of several filings. Values that are not the same from one to the next are flagged, and shown side by side with their date. A gap may come from a resized project, a different phase, or a corrected figure: the opinion does not say which, and we do not guess.",
  icpeTip: "ICPE — the French regime that authorises, frames and inspects an activity liable to create a risk or a nuisance. Each number designates the activity concerned in the national nomenclature. Being classified does not mean being dangerous: it means being regulated, and therefore inspected.",
  valeursMultiples: "{n} values",
  datePattern: "{a}-{m}-{j}",
  locale: "en-GB",
};

/** La copie du bloc dossier : `DOSSIER[lang]`. */
export const DOSSIER: Record<Langue, typeof FR> = { fr: FR, en: EN };
