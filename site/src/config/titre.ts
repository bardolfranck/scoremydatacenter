// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// 🔴 « LE LIEU NE PART JAMAIS » ÉTAIT VRAI DU TITRE, ET FAUX DE CE QUE GOOGLE MONTRE.
// Les deux cascades de titre (fiche et portrait) dégradent déjà dans l'ordre du moins
// coûteux — la région entre parenthèses, puis l'angle — en se fiant à un budget de
// 65 caractères, et leur commentaire dit, à raison, que 65 est une limite d'AFFICHAGE et pas
// d'indexation. Il leur manquait une marche : quand le NOM à lui seul mange le budget, le
// lieu est bien dans la balise, et il tombe hors de la partie VISIBLE.
//
// Mesuré sur les 3 292 fiches servies le 2026-11-07 : **14 fiches** ont un lieu qui commence
// après le 57ᵉ caractère, sur la fiche ET sur le portrait — même cohorte des deux côtés.
// Le lecteur voit « AMAZON DATA SERVICES INC. IAD 50 IAD 60 IAD-71 IAD-78 IAD-79 … » et
// jamais la commune. Les 1 332 autres titres longs gardent un lieu visible : ils ne sont pas
// concernés, et on ne les touche pas.
//
// ⚠️ CE QU'ON PAIE, nommément. Raccourcir le nom le sort du titre, donc de ce que Google
// indexe DANS le titre (le nom complet reste en H1 et dans le corps, donc indexé par la
// page). On échange la queue d'un nom contre une commune visible. L'arbitrage suit la seule
// intention mesurée : huit des dix suggestions de Google sur « data center » sont des
// communes à projet, et personne ne cherche « IAD-79 ». Pour les 14, la commune vaut plus
// que la fin de l'énumération.
//
// ⚠️ ET LA COUPE SE VOIT. Une troncature qui tombe sur une frontière de mot se lit comme un
// nom entier — c'est exactement l'erreur qui a coûté une demi-journée le 2026-11-06, quand
// « … HOSPITALS - MEAD » (60 caractères pile) a été pris pour un nom complet alors qu'il
// manquait « OWMONT BUILD B » [[noms-tronques-par-la-collecte]]. L'ellipsis n'est donc pas
// de la décoration : c'est elle qui empêche le titre d'AFFIRMER un nom qui n'existe pas.

/** La largeur que Google affiche, en caractères. C'est un PROXY : la coupure réelle se fait
 *  en pixels (~600), donc entre 55 et 62 caractères selon les lettres. On prend une valeur
 *  prudente, et c'est le même nombre qui sert à compter la cohorte dans le test. */
export const VISIBLE_SERP = 57;

/** Le budget des cascades existantes — une limite d'affichage, pas d'indexation. */
export const BUDGET_SERP = 65;

/** En dessous, un nom raccourci ne nomme plus rien : « AMAZON DATA… » vaut mieux que
 *  « AMA… », et à ce stade mieux vaut garder le nom entier et perdre le lieu. */
export const PLANCHER_NOM = 24;

/**
 * Le nom tel qu'il doit entrer dans un titre pour que ce qui le SUIT reste visible.
 *
 * `reserve` = les caractères posés entre le nom et le lieu (« — » et ses espaces, soit 3).
 * Rend le nom inchangé quand il tient déjà, ou quand le raccourcir descendrait sous le
 * plancher : dans ce cas aucune version courte ne nomme le site, et on ne dégrade pas pour
 * dégrader.
 */
export function nomVisible(nom: string, reserve: number): string {
  const n = String(nom ?? "");
  const budget = VISIBLE_SERP - reserve - 1; // -1 pour l'ellipsis
  if (n.length <= VISIBLE_SERP - reserve) return n;
  if (budget < PLANCHER_NOM) return n;
  // Couper sur une frontière de MOT : une coupe au milieu d'un mot se voit, mais elle
  // abîme la lecture, et on cherche un nom qui reste prononçable.
  const brut = n.slice(0, budget);
  const espace = brut.lastIndexOf(" ");
  const coupe = espace >= PLANCHER_NOM ? brut.slice(0, espace) : brut;
  // On retire une ponctuation de fin pour ne pas écrire « Crédit Mutuel /… ».
  return `${coupe.replace(/[\s/,;:·\-–—(]+$/, "")}…`;
}

/** Vrai quand tout ce qui SUIT le nom commence au-delà de la largeur visible — donc quand
 *  le lecteur ne voit qu'un nom tronqué par Google, sans note ni commune.
 *
 *  ⚠️ Le nom dit « après le nom », pas « le lieu » : sur la fiche, ce qui suit le nom est la
 *  note PUIS le lieu (ordre décidé le 2026-10-23 : la note est ce qui nous distingue). Un
 *  prédicat qui prétendrait mesurer le lieu mentirait sur une des deux surfaces. */
export function apresLeNomCache(titre: string, separateur = " — "): boolean {
  const i = String(titre ?? "").indexOf(separateur);
  return i > VISIBLE_SERP;
}
