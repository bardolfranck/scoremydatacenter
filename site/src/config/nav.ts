// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Single source of truth for the site navigation — pages must not hand-roll
// their own copy (four pages diverging silently is how menus rot).

export interface NavItem {
  href: string;
  label: string;
}

export const FR_NAV: NavItem[] = [
  { href: "/fr/carte", label: "Carte" },
  { href: "/fr/classement", label: "Classement" },
  { href: "/fr/indices", label: "Indices pays" },
  { href: "/fr/chiffres", label: "Les chiffres" },
  { href: "/fr/bibliotheque", label: "Bibliothèque" },
  { href: "/fr/comprendre", label: "Comprendre les data centers" },
  { href: "/fr/methodologie", label: "Méthode" },
  { href: "/fr/#open", label: "Modèle ouvert" },
  { href: "/fr/qui-sommes-nous", label: "Qui sommes-nous ?" },
  { href: "/fr/#contact", label: "Contact" },
  { href: "/fr/#faq", label: "FAQ" },
];

// Same action → same destination as FR (i18n §13): Map and Ranking are real EN
// pages, not homepage anchors or FR fallbacks.
export const EN_NAV: NavItem[] = [
  { href: "/map", label: "Map" },
  { href: "/ranking", label: "Ranking" },
  { href: "/indices", label: "Country index" },
  { href: "/figures", label: "Figures" },
  { href: "/intelligence", label: "Intelligence Library" },
  { href: "/understand", label: "Understanding data centers" },
  { href: "/methodology", label: "Method" },
  { href: "/#open", label: "Open model" },
  { href: "/who-we-are", label: "Who we are" },
  { href: "/#contact", label: "Contact" },
  { href: "/#faq", label: "FAQ" },
];
