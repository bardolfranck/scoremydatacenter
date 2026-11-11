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

// 🔴 LE SIXIÈME EST ARRIVÉ LE 2026-11-07, et il regarde en arrière.
// Huit fiches servies disaient « (closed) » ou « ** INACTIVE ** » dans leur nom, portaient une
// note, et déclaraient `operational` : nous affirmions que des sites fermés étaient en
// exploitation. Décision de Franck : on ne retire pas la page — « fermé mais a existé, donc on
// garde la note » — on ANNONCE la fermeture, dans la fiche et dans le statut.
// `decommissioned` n'est donc ni un stade du pipeline (il ne mène à rien) ni `unknown` (on sait,
// justement) : c'est une FIN ÉTABLIE. Sa note devient une note d'ARCHIVE, et une archive sans
// date se lit comme le présent — d'où `identity.vintage.decommissioned_year`, exigé par
// `hors_service_gate`. Les calculs qui parlent du parc en activité (vitrine, médiane,
// classement) exigent déjà `operational` : ils l'excluent par construction, pas par une liste.

/** Tout le vocabulaire servi, `unknown` et `decommissioned` compris. */
// 🔴 LE SEPTIÈME, 2026-11-11 : `withdrawn` = projet REFUSÉ ou RETIRÉ. Jamais construit, donc
// ni `decommissioned` (fermeture d'un site qui a existé) ni un stade du pipeline (il ne mène
// plus à rien). Même traitement : la note est une archive datée, la fiche l'annonce.
export const STATUTS = [...PIPELINE, "operational", "decommissioned", "withdrawn", "unknown"] as const;

export type Statut = (typeof STATUTS)[number];

/** Vrai pour un site dont une source publique dit qu'il est EN PROJET. */
export function enProjet(statut: string | null | undefined): boolean {
  return (PIPELINE as readonly string[]).includes(statut ?? "");
}

/** Vrai pour un site MIS HORS SERVICE : sa note est une archive, pas un état présent. */
export function horsService(statut: string | null | undefined): boolean {
  return statut === "decommissioned";
}

/** Vrai pour un PROJET REFUSÉ OU RETIRÉ : jamais construit, sa note est une archive. */
export function projetRetire(statut: string | null | undefined): boolean {
  return statut === "withdrawn";
}
