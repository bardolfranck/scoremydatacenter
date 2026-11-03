// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// LES MÊMES PAGES, DANS CHAQUE LANGUE — déclarées une fois, ici.
//
// Avant cette table, chaque page portait un `altHref` : l'adresse de sa jumelle dans
// « l'autre langue ». Au singulier. Tout le site supposait donc DEUX langues, et le sélecteur
// comme le cluster hreflang se construisaient sur cette paire. À trois langues, « l'autre »
// devient « les autres » : ce n'est plus un lien, c'est un sélecteur — et un hreflang bâti
// sur une paire déclare à un moteur qu'une page néerlandaise est la version anglaise d'une
// page française.
//
// La règle de structure : une page n'a plus à savoir où vivent ses sœurs. Elle dit QUI elle
// est (`page="glossaire"`), et `Base.astro` dérive le reste de cette table. Une langue de
// plus est alors une COLONNE à remplir, pas 81 fichiers à rouvrir.
//
// `:id` dans un chemin est un segment variable (l'identifiant d'un site, le périmètre d'une
// page de chiffres). Il se reporte tel quel d'une langue à l'autre : c'est une clé de donnée,
// pas un mot — le traduire casserait l'adresse.
//
// 🔴 CE QUI MANQUE SE DÉCLARE, ET NE S'INVENTE PAS. Une famille sans colonne néerlandaise
// n'est pas un oubli : c'est une page dont la prose n'est pas écrite en néerlandais. Le
// sélecteur n'offre alors pas cette langue sur cette page — mieux qu'un lien vers une page
// française déguisée en néerlandais [[absence-ressemble-a-zero]].
import { LANGUES_VIVANTES, type LangueDeclaree } from "../content/langues";

export interface FamilleDeRoutes {
  /** Ce que la page EST, indépendamment de la langue. Passé par la page à `Base`. */
  id: string;
  /** Son adresse par langue. Une langue absente = pas de version dans cette langue. */
  chemins: Partial<Record<LangueDeclaree, string>>;
}

// Les slugs néerlandais ne sont pas inventés ici : ce sont ceux que `NL_NAV` et le pied de
// page de `chrome.ts` promettent déjà au lecteur. Une liste à deux endroits finit par mentir,
// donc `test_la_table_de_routes_et_le_menu_disent_la_meme_chose` les confronte.
export const FAMILLES: FamilleDeRoutes[] = [
  { id: "accueil", chemins: { en: "/", fr: "/fr/", nl: "/nl/" } },
  { id: "carte", chemins: { en: "/map/", fr: "/fr/carte/", nl: "/nl/kaart/" } },
  { id: "classement", chemins: { en: "/ranking/", fr: "/fr/classement/", nl: "/nl/ranglijst/" } },
  { id: "comparer", chemins: { en: "/compare/", fr: "/fr/comparer/", nl: "/nl/vergelijken/" } },
  { id: "indices", chemins: { en: "/indices/", fr: "/fr/indices/", nl: "/nl/indices/" } },
  // 🔴 LES PAGES DE CHIFFRES SONT HORS TABLE, ET C'EST UN FAIT, PAS UN OUBLI. La même
  // adresse n'y porte pas le même contenu : le périmètre par défaut est la FRANCE en
  // français et l'EUROPE en anglais (cadrage §4.10). `/fr/chiffres/` a donc pour jumelle
  // `/figures/fr/`, et `/figures/` a pour jumelle `/fr/chiffres/europe/` — un croisement
  // qu'une table d'adresses ne sait pas dire. Elles gardent leur paire déclarée page par
  // page, et le néerlandais ne les offrira que le jour où on tranchera SON défaut.
  //
  // Découvert en comparant les deux rendus octet à octet : la table « corrigeait » ces
  // quatre pages vers index↔index, ce qui aurait déclaré à Google que les chiffres
  // européens sont la version anglaise des chiffres français.
  { id: "fiche", chemins: { en: "/dc/:id/", fr: "/fr/dc/:id/", nl: "/nl/dc/:id/" } },
  { id: "portrait", chemins: {
    en: "/dc/:id/portrait/", fr: "/fr/dc/:id/portrait/", nl: "/nl/dc/:id/portret/" } },
  { id: "portrait-explainer", chemins: {
    en: "/site-portrait/", fr: "/fr/portrait-du-site/", nl: "/nl/portret-van-de-site/" } },
  { id: "acceptabilite", chemins: {
    en: "/acceptability-of-data-centers/",
    fr: "/fr/acceptabilite-data-center/",
    nl: "/nl/acceptatie-datacenter/" } },
  { id: "notation", chemins: {
    en: "/data-center-rating/", fr: "/fr/notation-data-center/", nl: "/nl/beoordeling-datacenter/" } },
  { id: "nuisances", chemins: {
    en: "/data-center-nuisances/", fr: "/fr/nuisances-data-center/", nl: "/nl/hinder-datacenter/" } },
  { id: "comprendre", chemins: {
    en: "/understand/", fr: "/fr/comprendre/", nl: "/nl/datacenters-begrijpen/" } },
  { id: "one-pager", chemins: {
    en: "/understand/one-pager/",
    fr: "/fr/comprendre/one-pager/",
    nl: "/nl/datacenters-begrijpen/one-pager/" } },
  { id: "normes", chemins: { en: "/standards/", fr: "/fr/normes/", nl: "/nl/normen/" } },
  { id: "methodologie", chemins: {
    en: "/methodology/", fr: "/fr/methodologie/", nl: "/nl/methodologie/" } },
  { id: "note-pas-a-pas", chemins: {
    en: "/the-grade-step-by-step/",
    fr: "/fr/la-note-pas-a-pas/",
    nl: "/nl/het-cijfer-stap-voor-stap/" } },
  { id: "sources", chemins: { en: "/sources/", fr: "/fr/sources/", nl: "/nl/bronnen/" } },
  { id: "glossaire", chemins: { en: "/glossary/", fr: "/fr/glossaire/", nl: "/nl/glossarium/" } },
  { id: "actu", chemins: { en: "/news/", fr: "/fr/actu/", nl: "/nl/nieuws/" } },
  { id: "bibliotheque", chemins: {
    en: "/intelligence/", fr: "/fr/bibliotheque/", nl: "/nl/bibliotheek/" } },
  { id: "bibliotheque-tous", chemins: {
    en: "/intelligence/all/", fr: "/fr/bibliotheque/tous/", nl: "/nl/bibliotheek/alles/" } },
  { id: "developpeurs", chemins: {
    en: "/developers/", fr: "/fr/developpeurs/", nl: "/nl/ontwikkelaars/" } },
  { id: "cle", chemins: {
    en: "/developers/key/", fr: "/fr/developpeurs/cle/", nl: "/nl/ontwikkelaars/sleutel/" } },
  { id: "qui-sommes-nous", chemins: {
    en: "/who-we-are/", fr: "/fr/qui-sommes-nous/", nl: "/nl/over-ons/" } },
  { id: "presse", chemins: { en: "/press/", fr: "/fr/presse/", nl: "/nl/pers/" } },
  { id: "contact", chemins: { en: "/contact/", fr: "/fr/contact/", nl: "/nl/contact/" } },
  { id: "mentions", chemins: { en: "/legal/", fr: "/fr/mentions-legales/", nl: "/nl/juridisch/" } },

  // Les rapports restent à DEUX langues, et c'est une décision : un rapport pays se publie
  // dans la langue du pays et en anglais, jamais en trois exemplaires du site.
  { id: "rapport-france", chemins: { en: "/reports/france/", fr: "/fr/rapports/france/" } },
  { id: "rapport-banques", chemins: { en: "/reports/banks/", fr: "/fr/rapports/banques/" } },
  { id: "rapport-big-tech", chemins: { en: "/reports/big-tech/", fr: "/fr/rapports/big-tech/" } },
  { id: "rapport-nederland", chemins: {
    en: "/reports/nederland/", fr: "/fr/rapports/nederland/" } },

  // Pages d'une seule langue, déclarées comme telles : l'aperçu partagé est un outil interne
  // et la page 404 n'a pas de jumelle (le serveur la sert telle quelle, hors de toute route).
  { id: "apercu-partage", chemins: { fr: "/fr/apercu-partage/" } },
];

const SEGMENTS = (chemin: string) => chemin.split("/").filter(Boolean);

/** La famille qui rend ce chemin, et les segments variables qu'il porte. */
export function famillePour(
  chemin: string,
): { famille: FamilleDeRoutes; langue: LangueDeclaree; params: string[] } | null {
  const vus = SEGMENTS(chemin);
  for (const famille of FAMILLES) {
    for (const [langue, motif] of Object.entries(famille.chemins)) {
      const attendus = SEGMENTS(motif);
      if (attendus.length !== vus.length) continue;
      const params: string[] = [];
      let ok = true;
      for (let i = 0; i < attendus.length; i++) {
        if (attendus[i] === ":id") params.push(vus[i]);
        else if (attendus[i] !== vus[i]) { ok = false; break; }
      }
      if (ok) return { famille, langue: langue as LangueDeclaree, params };
    }
  }
  return null;
}

/** Le chemin de CE contenu dans une autre langue — ou null s'il n'y est pas écrit. */
export function cheminDansLaLangue(
  famille: FamilleDeRoutes,
  langue: LangueDeclaree,
  params: string[],
): string | null {
  const motif = famille.chemins[langue];
  if (!motif) return null;
  let i = 0;
  const segments = SEGMENTS(motif).map((s) => (s === ":id" ? params[i++] : s));
  // 🔴 L'accueil n'a PAS de segment : « / » + "" + « / » donnait « // », que `new URL` lit
  // comme une adresse relative au protocole et refuse. Le build est tombé exactement là,
  // sur `/fr/` — le cas vide d'une construction par concaténation, celui qu'on ne teste pas.
  return segments.length ? "/" + segments.join("/") + "/" : "/";
}

/**
 * Les versions de cette page dans les autres langues SERVIES.
 *
 * Une langue en préparation n'y figure pas : elle a des tables, pas de lecteurs. Et une page
 * dont la langue n'est pas écrite n'y figure pas non plus — le sélecteur doit refléter ce qui
 * existe, pas ce qu'on voudrait avoir.
 */
export function autresLangues(
  chemin: string,
  servies: readonly string[] = LANGUES_VIVANTES,
): { langue: LangueDeclaree; href: string }[] {
  const trouve = famillePour(chemin);
  if (!trouve) return [];
  return servies
    .filter((lg) => lg !== trouve.langue)
    .map((lg) => ({
      langue: lg as LangueDeclaree,
      href: cheminDansLaLangue(trouve.famille, lg as LangueDeclaree, trouve.params),
    }))
    .filter((a): a is { langue: LangueDeclaree; href: string } => a.href !== null);
}
