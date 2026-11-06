// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Les langues vivantes du site, à UN seul endroit. Chaque table de chaînes s'y réfère, pour
// qu'ouvrir une langue soit une décision prise une fois et non une liste à rallonger partout.
//
// « Vivante » veut dire SERVIE : une langue en cours d'écriture n'entre ici qu'au moment où
// ses tables sont complètes, sinon les gardes de parité réclameraient des clés qui n'existent
// pas encore et la suite serait rouge pendant tout le temps de la rédaction.

export const LANGUES_VIVANTES = ["fr", "en"] as const;
export type Langue = (typeof LANGUES_VIVANTES)[number];

// Les langues EN PRÉPARATION : leurs tables existent, leurs clés sont gardées comme celles
// des langues vivantes, mais aucune page ne les sert. C'est l'état dans lequel une langue
// s'écrit — et il est DÉCLARÉ, pas implicite, pour qu'on sache ce qui est en cours.
//
// 🔴 Faire passer une langue d'ici à `LANGUES_VIVANTES` est la décision qui la met en ligne.
// `test_une_langue_ne_devient_vivante_que_traduite` l'empêche tant que ses valeurs sont
// encore celles du français : sans ce garde, ouvrir le néerlandais publierait 740 chaînes
// françaises sur des pages néerlandaises — exactement la façon dont l'anglais a décroché,
// mais dans l'autre sens et en une seule fois.
export const LANGUES_EN_PREPARATION = ["nl"] as const;

/** Toutes les langues qui ont une table, servies ou non. */
export const LANGUES_DECLAREES = [...LANGUES_VIVANTES, ...LANGUES_EN_PREPARATION] as const;
export type LangueDeclaree = (typeof LANGUES_DECLAREES)[number];

// 🔴 OÙ VIT CHAQUE LANGUE, déclaré une fois. Le layout disait `lang === "en" ? "/" : "/fr/"` :
// un ternaire binaire, juste tant qu'il n'y a que deux langues, et qui renvoie le lecteur
// néerlandais vers l'accueil FRANÇAIS dès qu'il y en a trois. Un ternaire ne dit pas qu'il
// ignore un cas, il en choisit un [[absence-ressemble-a-zero]].
export const RACINE: Record<LangueDeclaree, string> = { en: "/", fr: "/fr/", nl: "/nl/" };

// ──────────────────────────────────────────────────────────────────────────────────────────
// QUELLES FICHES UNE ÉDITION COUVRE — « 151 fiches NL. point final » (Franck, 2026-11-05)
// ──────────────────────────────────────────────────────────────────────────────────────────
// 🔴 TROUVÉ PAR UN PLAFOND, LE 2026-11-06. Le néerlandais bâtissait une page pour CHAQUE
// fiche du monde : 3 292 pages, dont 1 702 américaines, qui servaient de la prose anglaise
// sous une adresse néerlandaise. Personne n'y liait — mais le sitemap les déclarait toutes
// à Google, et `dist` passait de 17 445 à 24 047 fichiers : au-dessus de la limite de
// 20 000 de Cloudflare Pages, qui a refusé la publication entière.
//
// LA DOCTRINE EST ANTÉRIEURE AU PLAFOND, c'est elle qui tranche : la prose d'une langue est
// due sur les fiches de SON pays, et une fiche étrangère servie en anglais dans l'édition
// néerlandaise est VOULUE, pas une dette. Une édition de pays ne mirroite donc pas le
// corpus : elle couvre son pays.
//
// `"tous"` n'est pas un défaut, c'est une DÉCISION : le français et l'anglais sont les deux
// éditions de référence et couvrent le corpus entier. Une langue de pays liste ses préfixes
// d'identifiant — jamais déduits du code de langue, qui coïncide pour `nl` et se trompe
// pour `en`. ⚠️ La Flandre belge (42 fiches `be-`) attend l'arbitrage de Franck : le run
// suivant fait BE → NL & FR.
export const PAYS_DE_LA_LANGUE: Record<LangueDeclaree, readonly string[] | "tous"> = {
  fr: "tous",
  en: "tous",
  nl: ["nl"],
};

/** L'édition de cette langue publie-t-elle la fiche `id` ? */
export function langueCouvreLaFiche(lang: LangueDeclaree, id: string): boolean {
  const pays = PAYS_DE_LA_LANGUE[lang];
  if (pays === "tous") return true;
  return pays.includes(String(id).split("-", 1)[0]);
}

/** Les fiches que l'édition d'une langue publie. Le tri d'origine est conservé. */
export function fichesDeLaLangue<T extends { id: string }>(
  lang: LangueDeclaree,
  fiches: readonly T[],
): T[] {
  if (PAYS_DE_LA_LANGUE[lang] === "tous") return [...fiches];
  return fiches.filter((f) => langueCouvreLaFiche(lang, f.id));
}

// 🔴 CE QUI RESTE À TRANCHER AVANT QUE LE NÉERLANDAIS SOIT SERVI : `altHref`/`altLabel`.
// Tout le site suppose DEUX langues — « l'autre langue », au singulier. Chaque page passe un
// `altHref` unique, et `Base.astro` construit son cluster hreflang sur cette paire. À trois
// langues, « l'autre » devient « les autres » : c'est un sélecteur, pas un lien, et le
// hreflang doit lister les trois. Ce n'est pas un détail d'affichage — un hreflang qui ment
// déclare à Google qu'une page néerlandaise est la version anglaise d'une page française.
// Décision de structure : elle appartient à Franck, pas au harnais de préviz.

// ──────────────────────────────────────────────────────────────────────────────────────────
// LE PLURIEL EST UNE RÈGLE DE LANGUE, PAS UN `s` À COLLER
// ──────────────────────────────────────────────────────────────────────────────────────────
// Le français met zéro au SINGULIER (« 0 site »), l'anglais et le néerlandais au PLURIEL
// (« 0 sites », « 0 sites »). Un `n > 1 ? "sites" : "site"` dans un gabarit n'est donc pas
// une commodité : c'est la règle du français, appliquée au néerlandais, en silence. La règle
// se déclare par langue ; les FORMES vivent dans la table de chaînes, avec le reste de la
// prose, parce que ce sont des mots.
// ──────────────────────────────────────────────────────────────────────────────────────────
// LES FORMATS SONT UNE PROPRIÉTÉ DE LA LANGUE, PAS UN `lang === "fr"`
// ──────────────────────────────────────────────────────────────────────────────────────────
// 🔴 Trouvé le 2026-11-05, et c'est la troisième langue qui l'a révélé : la virgule décimale
// s'écrivait `lang === "fr" ? String(s).replace(".", ",") : String(s)` — dans la carte des
// indices, dans la page des indices, et le `fr-FR`/`en-GB` du comparateur. Or le NÉERLANDAIS
// MET AUSSI LA VIRGULE. Le ternaire ne dit pas qu'il ignore un cas : il en choisit un
// [[absence-ressemble-a-zero]]. Un indice à 80,5 se serait affiché « 80.5 » à un lecteur
// néerlandais — pas une erreur, pas un blanc, juste faux.
//
// Déclarer le format PAR LANGUE le rend vrai pour la langue suivante sans qu'on y pense, et
// c'est ce que le ternaire ne peut pas faire. `test_langues_ts_declare_chaque_langue` refuse
// une table de cette section qui oublierait une langue déclarée.
export const LOCALE: Record<LangueDeclaree, string> = {
  fr: "fr-FR",
  en: "en-GB",
  nl: "nl-NL",
};

export const SEPARATEUR_DECIMAL: Record<LangueDeclaree, string> = {
  fr: ",",
  en: ".",
  nl: ",",
};

/** `s` écrit avec la virgule (ou le point) de `lang`. */
export function nombreDecimal(lang: LangueDeclaree, s: number | string): string {
  return String(s).replace(".", SEPARATEUR_DECIMAL[lang]);
}

export type FormePluriel = "un" | "autres";

export const REGLE_PLURIEL: Record<LangueDeclaree, (n: number) => FormePluriel> = {
  fr: (n) => (Math.abs(n) < 2 ? "un" : "autres"),
  en: (n) => (Math.abs(n) === 1 ? "un" : "autres"),
  nl: (n) => (Math.abs(n) === 1 ? "un" : "autres"),
};

/**
 * La forme à servir pour `n`, choisie par la règle de la langue.
 *
 * La table écrit `{ un: "…{n} site…", autres: "…{n} sites…" }` — DEUX phrases entières, pas
 * un radical et une terminaison : une langue a le droit de tourner sa phrase autrement au
 * singulier, et « 1 site » n'est pas partout « {n} site ». Le trou `{n}` reste dans les deux
 * formes, et c'est l'appelant qui le remplit avec SON format de nombre (l'espace fine
 * insécable du français n'est pas celle du néerlandais).
 */
export function pluriel(
  lang: LangueDeclaree,
  n: number,
  formes: Record<FormePluriel, string>,
): string {
  return formes[REGLE_PLURIEL[lang](n)];
}

/**
 * La copie d'un composant pour `lang`, avec repli DÉCLARÉ sur l'anglais.
 *
 * 🔴 Huit composants portent encore leur copie EN DUR, par langue, dans le composant —
 * ~301 chaînes hors des tables gardées. Tant qu'elles y sont, `T[lang]` rend `undefined`
 * pour toute langue nouvelle, et la page ne s'affiche pas mal : **elle ne se construit
 * pas**. L'accueil néerlandais est tombé exactement là (`Cannot read properties of
 * undefined (reading 'eyebrow')`), et aucun garde de parité ne pouvait le voir : ils
 * lisent `content/`, pas les composants.
 *
 * Ce repli n'est pas la réparation — la réparation est de sortir ces chaînes dans un
 * module de `TABLES_MODULES`, où la parité se vérifie. Il évite qu'un bloc manquant
 * EMPÊCHE la page d'exister, et le bandeau de préviz dit lesquels sont encore en anglais.
 */
export function copie<T>(table: Record<string, T>, lang: string): T {
  return table[lang] ?? table.en;
}

/**
 * La valeur d'un champ de DONNÉE pour `lang`, avec repli DÉCLARÉ : langue → anglais → français.
 *
 * 🔴 POURQUOI CETTE FONCTION EXISTE, ET POURQUOI L'ORDRE N'EST PAS UN DÉTAIL. Cinq composants
 * portaient chacun leur propre version de ce repli, et tous les cinq terminaient sur le
 * FRANÇAIS : `obj?.[lang] ?? obj?.fr ?? ""`. Avec deux langues, cette seconde branche n'est
 * JAMAIS prise — `lang` vaut `fr` ou `en`, et les deux clés existent. C'était donc du code
 * mort depuis le premier jour, qui s'exécute pour la première fois le jour où une troisième
 * langue arrive. Et ce jour-là il sert du **français** à un lecteur néerlandais : sans erreur,
 * sans blanc, sans que rien ne crie [[absence-ressemble-a-zero]].
 *
 * L'anglais d'abord, donc, parce que c'est la traduction fidèle de référence et la langue que
 * ce lecteur a le plus de chances de lire. Le français n'est PAS une langue de secours
 * universelle : c'est la langue d'un des pays du corpus. Il reste en dernier ressort pour les
 * enregistrements anciens qui ne portent que `fr`, pas comme un choix éditorial.
 *
 * Ce repli vaut aussi pour ce qui n'est pas de la prose : l'URL d'une **carte de contexte
 * annotée** est un champ par langue comme un autre, et une fiche néerlandaise montrant une
 * photo satellite annotée en français est le même défaut, en image.
 *
 * ⚠️ Il ne répare QUE le repli qui mente. Deux autres familles cassent sur une langue neuve et
 * ne se réparent pas par une chaîne : le repli qui EFFACE (`?? ""`, un libellé ICPE qui devient
 * muet) et l'absence de tout repli (`undefined` rendu, ou la page qui ne se construit pas).
 * Celles-là réclament la colonne de la langue, pas un ordre de secours.
 */
export function donnee<T>(objet: Record<string, T> | null | undefined, lang: string): T | "" {
  if (!objet) return "";
  return objet[lang] ?? objet.en ?? objet.fr ?? "";
}
