// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// PRÉVIZ DES LANGUES EN PRÉPARATION — un harnais de relecture, jamais une page servie.
//
// Un traducteur natif relit le RENDU, pas le fichier : c'est la leçon du rapport néerlandais
// figé, 62 corrections pour avoir cru qu'un fichier de clés se relisait. Mais une langue en
// préparation n'a pas de pages, par construction (`LANGUES_EN_PREPARATION`) — il faut donc
// un rendu qui existe en local et PAS en production.
//
// 🔴 LE PORTILLON EST DANS `getStaticPaths`, pas dans un `if` de gabarit. Une page Astro sans
// `getStaticPaths` est TOUJOURS construite ; un `if` qui ne rend rien laisse quand même un
// fichier HTML dans `dist/`. Rendre `[]` est la seule forme qui ne produit aucun octet.
// `test_la_previz_ne_sort_rien_en_production` le vérifie sur le code, et le diff d'octets du
// site rendu le vérifie sur le résultat.
import { LANGUES_EN_PREPARATION } from "../content/langues";

export const PREVIZ = process.env.SMDC_PREVIZ === "1";

// La langue relue n'est pas écrite ici : c'est celle qui est EN PRÉPARATION. Quand le
// néerlandais passera vivant et qu'une autre langue entrera en préparation, la préviz la
// suivra sans qu'on y pense — une langue nommée en dur ici serait une liste de plus.
// 🔴 Et elle vit dans ce module parce qu'Astro ISOLE `getStaticPaths` : il ne voit pas les
// constantes du frontmatter de la page, seulement les imports. Première version : `LANGUE`
// déclarée dans la page → `LANGUE is not defined` au rendu, pas à la compilation.
export const LANGUE_PREVIZ = LANGUES_EN_PREPARATION[0];

// 🔴 LE PORTILLON PREND UNE FABRIQUE, PAS UNE LISTE. Première version : il filtrait le
// RÉSULTAT, donc `getStaticPaths` faisait tout son travail — lire les 3 267 artefacts, le
// geojson, choisir la fiche — avant qu'on jette la liste. Conséquence vue tout de suite : un
// gabarit de préviz qui lève une exception a CASSÉ le build de production, alors qu'il n'y
// produit pas une page. Un portillon fermé ne doit rien exécuter derrière lui.
/** Les chemins de préviz, ou AUCUN — et aucun travail — si le portillon est fermé. */
export function cheminsPreviz<T>(fabrique: () => T[]): T[] {
  return PREVIZ ? fabrique() : [];
}

/** Les gabarits relus en préviz — le périmètre signé : fiche, portrait, Comprendre, accueil. */
export const GABARITS = ["accueil", "fiche", "portrait", "comprendre", "methodologie"] as const;
export type Gabarit = (typeof GABARITS)[number];

/** Le FR de référence pour le côte-à-côte, par gabarit. `{id}` = la fiche choisie au build. */
export const JUMEAU_FR: Record<Gabarit, string> = {
  accueil: "/fr/",
  fiche: "/fr/dc/{id}/",
  portrait: "/fr/dc/{id}/portrait/",
  comprendre: "/fr/comprendre/",
  methodologie: "/fr/methodologie/",
};

/** La fiche de démonstration, choisie UNE fois : les deux pages de préviz doivent montrer la
 *  même, sinon le côte-à-côte compare deux sites différents. Déterministe à garniture égale. */
export function choisirDemo(dcs: any[], pays: string): any {
  const notee = (d: any) => /^[A-E]$/.test(d?.grades?.site?.grade ?? "") && !d?.grade_withheld;
  const garniture = (d: any) => JSON.stringify(d).length;
  const locales = dcs.filter((d: any) => d.country === pays && notee(d));
  const pool = locales.length ? locales : dcs.filter(notee);
  return pool.sort(
    (a: any, b: any) => garniture(b) - garniture(a) || String(a.id).localeCompare(String(b.id)),
  )[0];
}
