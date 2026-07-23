// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Single source of truth for the site navigation — pages must not hand-roll
// their own copy (four pages diverging silently is how menus rot).
//
// The header groups the sections (Franck 2026-07-22): 11 flat entries were too
// many to sit in one row. Four heads follow the visitor's path — Explore (show
// me the data) → Understand (can I trust it?) → Library (go deeper) → the
// Observatory (who are you?). A node with `children` renders as a dropdown;
// a bare link (Bibliothèque) stays flat. Order the children by importance.

export interface NavLink {
  href: string;
  label: string;
}
export interface NavGroup {
  label: string;
  children: NavLink[];
}
export type NavNode = NavLink | NavGroup;

export function isGroup(n: NavNode): n is NavGroup {
  return (n as NavGroup).children !== undefined;
}

export const FR_NAV: NavNode[] = [
  { label: "Explorer", children: [
    { href: "/fr/carte", label: "Carte" },
    { href: "/fr/classement", label: "Classement" },
    { href: "/fr/indices", label: "Indices pays" },
    { href: "/fr/chiffres", label: "Les chiffres" },
  ]},
  { label: "Comprendre", children: [
    { href: "/fr/comprendre", label: "Comprendre les data centers" },
    { href: "/fr/methodologie", label: "Méthode" },
    { href: "/fr/#faq", label: "FAQ" },
  ]},
  { href: "/fr/bibliotheque", label: "Bibliothèque" },
  { label: "L'observatoire", children: [
    { href: "/fr/qui-sommes-nous", label: "Qui sommes-nous ?" },
    { href: "/fr/#open", label: "Modèle ouvert" },
    { href: "/fr/developpeurs", label: "API développeurs" },
    { href: "/fr/#contact", label: "Contact" },
  ]},
];

// Same action → same destination as FR (i18n §13): Map and Ranking are real EN
// pages, not homepage anchors or FR fallbacks.
export const EN_NAV: NavNode[] = [
  { label: "Explore", children: [
    { href: "/map", label: "Map" },
    { href: "/ranking", label: "Ranking" },
    { href: "/indices", label: "Country index" },
    { href: "/figures", label: "Figures" },
  ]},
  { label: "Understand", children: [
    { href: "/understand", label: "Understanding data centers" },
    { href: "/methodology", label: "Method" },
    { href: "/#faq", label: "FAQ" },
  ]},
  { href: "/intelligence", label: "Intelligence Library" },
  { label: "Observatory", children: [
    { href: "/who-we-are", label: "Who we are" },
    { href: "/#open", label: "Open model" },
    { href: "/developers", label: "Developer API" },
    { href: "/#contact", label: "Contact" },
  ]},
];
