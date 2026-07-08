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
  { href: "/fr/comprendre", label: "Comprendre les data centers" },
  { href: "/fr/#method", label: "Méthode" },
  { href: "/fr/#open", label: "Modèle ouvert" },
  { href: "/fr/#contact", label: "Contact" },
  { href: "/fr/#faq", label: "FAQ" },
];

export const EN_NAV: NavItem[] = [
  { href: "/fr/carte", label: "Map" },
  { href: "/#scores", label: "Scores" },
  { href: "/understand", label: "Understanding data centers" },
  { href: "/#method", label: "Method" },
  { href: "/#open", label: "Open model" },
  { href: "/#contact", label: "Contact" },
  { href: "/#faq", label: "FAQ" },
];
