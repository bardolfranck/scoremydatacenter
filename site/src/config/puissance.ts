// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// 🔴 UNE PUISSANCE NUE SE LIT COMME UNE MESURE. Trouvé le 2026-11-07 en vérifiant les
// 6 000 MW du projet Matador avant de les écrire dans un titre : le chiffre n'a aucune
// source, et la fiche l'affichait quand même comme un fait. Mesuré ensuite sur le corpus
// servi — 3 292 fiches, accesseur :
//
//   · 349 fiches portent une puissance ;
//   · **aucune n'est mesurée** — 133 « annoncé », 92 « estimé », 124 sans rien ;
//   · l'affichage ne distinguait QUE « estimé » (DcFiche.astro, Ranking.astro) ;
//   · les quatre plus gros chiffres de la page d'accueil (10 000, 10 000, 9 000, 6 000 MW)
//     sont précisément dans le lot SANS qualificatif.
//
// Donc 257 fiches sur 349 servaient un chiffre de presse avec l'autorité d'une mesure, dont
// les quatre que la page d'accueil met en vitrine. Le commentaire de `DcFiche.astro` énonçait
// pourtant déjà la règle — « un chiffre non mesuré n'est jamais servi comme un fait nu » —
// et sa mise en œuvre ne couvrait qu'un cas sur trois.
//
// POURQUOI LE TROU EXISTAIT : il est PAR PAYS, pas par fait. La France qualifie 218 de ses
// 221 puissances, Israël 7 sur 7 ; les États-Unis 0 sur 85, les Pays-Bas 0 sur 36. Le champ
// n'est pas optionnel par nature, il est oublié par deux sondes — et un oubli ressemble à
// une mesure ([[absence-ressemble-a-zero]]). Combler la donnée est le travail des filières ;
// l'affichage, lui, peut cesser de mentir tout de suite, sans rien inventer.
//
// ⚠️ LE QUATRIÈME ÉTAT A DÉJÀ UN NOM, et on ne lui en donne pas un second : `engine/
// puissance.py` écrit `"origine": power_mw_status or "non_documente"`. On réutilise ce mot.
// Deux vocabulaires pour un même état, c'est une liste à deux endroits
// ([[liste-a-deux-endroits-ment]]).
//
// CE QUI N'EST PAS DE L'AFFICHAGE : le comparateur. Il ne lit JAMAIS `power_mw` mais un
// GROUPE (`engine/puissance.py`), précisément pour que la provenance n'ait aucun effet sur
// une comparaison. Rien ici ne le concerne.

import { fmtInt, fmtDec, type Lang } from "./stats";

/** Les quatre états possibles de la provenance d'une puissance. `non_documente` inclus :
 *  c'est le mot qu'écrit déjà `engine/puissance.py` quand le champ est absent. */
export type OriginePuissance = "measured" | "announced" | "estimated" | "non_documente";

type Libelle = { fr: string; en: string; nl?: string };

// Le libellé dit la PROVENANCE, jamais un jugement sur le chiffre : « annoncé » est un fait
// vérifiable (quelqu'un l'a annoncé), « non documenté » est l'aveu d'un trou chez nous.
// `measured` n'a pas de libellé : une mesure est le cas normal, et le signaler suggérerait
// que les autres sont normales aussi.
const LIBELLES: Record<Exclude<OriginePuissance, "measured">, Libelle> = {
  announced: { fr: "annoncé", en: "announced", nl: "aangekondigd" },
  estimated: { fr: "estimé", en: "estimated", nl: "geschat" },
  // ⚠️ COURT, parce que le même mot va dans six endroits dont deux sont étroits (les
  // vignettes d'accueil, la carte sociale). Un libellé long y aurait appelé une version
  // abrégée, donc deux vocabulaires pour un état [[liste-a-deux-endroits-ment]]. Et il dit
  // ce qui est vrai de NOUS — aucune source enregistrée — pas de l'exploitant, qui n'a
  // peut-être rien caché.
  non_documente: { fr: "non sourcé", en: "unsourced", nl: "bron onbekend" },
};

/** La provenance d'une puissance SERVIE — jamais `undefined`, parce qu'un champ absent est
 *  un état, pas une absence d'état. */
export function originePuissance(statut: unknown): OriginePuissance {
  const v = String(statut ?? "").trim();
  return v === "measured" || v === "announced" || v === "estimated" ? v : "non_documente";
}

/** Le mot à afficher à côté du chiffre, « » pour une mesure. Repli sur la valeur BRUTE
 *  tant qu'une langue manque — comme `libelleFait` : une langue à moitié remplie se lirait
 *  sinon comme une langue complète. */
export function libelleOrigine(origine: OriginePuissance, lang: string): string {
  if (origine === "measured") return "";
  const l = LIBELLES[origine];
  return l[lang as keyof Libelle] ?? origine;
}

// Une estimation est un flottant de modèle (0,518008551…) : on l'arrondit pour que le
// chiffre SE LISE comme approximatif — la perte de précision est le message. Deux chiffres
// significatifs, alignés sur l'arrondi de la source (idempotent : source ≈ affichage).
const arrondirEstimation = (v: number) => Number(v.toPrecision(2));

// ⚠️ ET LE NOMBRE S'ÉCRIT DANS LA LANGUE QUI LE LIT. Les surfaces ne s'accordaient pas :
// la page chiffres passait par `fmtInt` (« 6 000 »), la fiche et le classement
// interpolaient la valeur brute (« 6000 »), et `Math.round` sur l'accueil rendait « 1 MW »
// pour une estimation de 0,518. Une seule écriture ici — c'est la même leçon que
// [[prose-unite-reecrite-fait-faux]] vue par l'autre bout : on ne réécrit pas l'unité, mais
// on écrit le nombre comme la langue l'écrit (virgule ≠ point, relevé en néerlandais).
const ecrire = (v: number, lang: Lang | string): string => {
  const l = lang as Lang;
  return v % 1 === 0 ? fmtInt(v, l) : fmtDec(v, l, 2);
};

/** Ce qu'une surface affiche pour une puissance : le chiffre, et le mot de sa provenance.
 *  UNE seule dérivation pour les six surfaces qui servaient leur propre version. */
export function puissanceServie(
  powerMw: unknown,
  statut: unknown,
  lang: Lang | string,
): { valeur: string; origine: OriginePuissance; libelle: string } | null {
  // `isFinite` global plutôt que `Number.isFinite` : la cible TS du site ne garantit pas ES2015.
  const n = typeof powerMw === "number" && isFinite(powerMw) && powerMw > 0 ? powerMw : null;
  if (n === null) return null;
  const origine = originePuissance(statut);
  const brut = origine === "estimated" ? arrondirEstimation(n) : n;
  const valeur = `${origine === "estimated" ? "~" : ""}${ecrire(brut, lang)} MW`;
  return { valeur, origine, libelle: libelleOrigine(origine, String(lang)) };
}
