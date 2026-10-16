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
    // Pages de CONCEPT (une page = un concept), placées avant la pédagogie longue : elles
    // définissent les mots que le reste du site emploie.
    { href: "/fr/acceptabilite-data-center", label: "L'acceptabilité" },
    { href: "/fr/notation-data-center", label: "La notation" },
    { href: "/fr/nuisances-data-center", label: "Les nuisances" },
    { href: "/fr/comprendre", label: "Comprendre les data centers" },
    { href: "/fr/normes", label: "Les normes · où on se situe" },
    { href: "/fr/methodologie", label: "Méthode" },
    { href: "/fr/la-note-pas-a-pas", label: "La note, pas à pas" },
    { href: "/fr/sources", label: "Sources & licences" },
    { href: "/fr/glossaire", label: "Glossaire" },
    { href: "/fr/#faq", label: "FAQ" },
  ]},
  // « Comparer » RETIRÉ DU MENU (Franck 2026-10-02) — la page, le moteur, les artefacts par
  // pays et la projection restent en place et continuent d'être construits à chaque build :
  // /fr/comparer et /compare répondent toujours. Seule l'entrée de menu disparaît. Pour la
  // remettre, décommenter la ligne ci-dessous (et son équivalent anglais) ; rien d'autre.
  // ⭐ REMIS AU MENU LE 2026-10-16, le jour où le comparateur est revenu en production sur
  // puissance × typologie. Il avait été retiré le 2026-10-02 parce qu'il comparait des
  // territoires ; il compare désormais des objets de même taille et de même métier.
  // ⚠️ Sans cette ligne la page répondait mais n'était atteignable que par son URL — une
  // page en production que personne ne peut trouver est une page qui n'existe pas.
  { href: "/fr/comparer", label: "Comparer" },
  { href: "/fr/actu", label: "Actu" },
  { label: "Bibliothèque", children: [
    { href: "/fr/rapports/france", label: "Rapport — La France" },
    { href: "/fr/rapports/nederland", label: "Rapport — Les Pays-Bas" },
    { href: "/fr/rapports/big-tech", label: "Rapport Big Tech-AI" },
    { href: "/fr/rapports/banques", label: "Rapport — Les banques" },
    { href: "/fr/bibliotheque", label: "Toute la bibliothèque" },
  ]},
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
    { href: "/acceptability-of-data-centers", label: "Acceptability" },
    { href: "/data-center-rating", label: "Rating" },
    { href: "/data-center-nuisances", label: "Nuisances" },
    { href: "/understand", label: "Understanding data centers" },
    { href: "/standards", label: "The standards · where we sit" },
    { href: "/methodology", label: "Method" },
    { href: "/the-grade-step-by-step", label: "A grade, step by step" },
    { href: "/sources", label: "Sources & licenses" },
    { href: "/glossary", label: "Glossary" },
    { href: "/#faq", label: "FAQ" },
  ]},
  // Remise au menu le 2026-10-16 avec le retour du comparateur en production — voir FR.
  { href: "/compare", label: "Compare" },
  { href: "/news", label: "News" },
  { label: "Library", children: [
    { href: "/reports/france", label: "France report" },
    { href: "/reports/nederland", label: "Netherlands report" },
    { href: "/reports/big-tech", label: "Big Tech-AI report" },
    { href: "/reports/banks", label: "The banks report" },
    { href: "/intelligence", label: "The whole library" },
  ]},
  { label: "Observatory", children: [
    { href: "/who-we-are", label: "Who we are" },
    { href: "/#open", label: "Open model" },
    { href: "/developers", label: "Developer API" },
    { href: "/#contact", label: "Contact" },
  ]},
];
