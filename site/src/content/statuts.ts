// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// LE VOCABULAIRE DES STATUTS DE PROJET — déclaré UNE fois.
//
// 🔴 Il vivait dans SEIZE tables, dans seize fichiers (la fiche, le portrait, la carte, le
// classement, l'accueil, les chiffres, la carte OG…), et rien ne les comparait. Ajouter une
// valeur voulait donc dire la retrouver seize fois, et en oublier une ne cassait rien : la
// rubrique affichait la valeur BRUTE, en anglais, au milieu d'une page française.
// `engine/tests/test_i18n_parity.py` recense maintenant ces tables en les CHERCHANT dans le
// code, et exige que chacune libelle chaque statut.
//
// 🔴 LE CINQUIÈME EST ARRIVÉ LE 2026-10-29, et il dit l'inverse des quatre autres.
// « operational repasse en non-mesuré » (Franck) : il n'existait aucune façon de NE PAS
// affirmer. Les quatre valeurs sont des affirmations ; `unknown` est leur absence assumée —
// « rien de public ne dit où en est ce site ». Ce n'est pas un trou de collecte à combler
// par défaut : c'est le refus d'affirmer un stade qu'aucune source ne porte.
//
// ⚠️ ET « PAS operational » N'EST PAS « EST UN PROJET ». Deux endroits confondaient les deux
// (le verbe des questions dérivées, la note sous l'image satellite) et faisaient donc parler
// `unknown` comme un chantier. Pour « est un projet », tester l'appartenance à `PIPELINE`.

/** Les stades qu'une source publique peut établir, dans l'ordre du cycle de vie. */
export const PIPELINE = ["announced", "permitting", "under_construction"] as const;

/** Tout le vocabulaire servi, `unknown` compris. */
export const STATUTS = [...PIPELINE, "operational", "unknown"] as const;

export type Statut = (typeof STATUTS)[number];

/** Vrai pour un site dont une source publique dit qu'il est EN PROJET. */
export function enProjet(statut: string | null | undefined): boolean {
  return (PIPELINE as readonly string[]).includes(statut ?? "");
}
