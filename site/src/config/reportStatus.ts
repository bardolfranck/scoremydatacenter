// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// L'ÉTAT ÉDITORIAL D'UN RAPPORT PUBLIÉ, EN UN SEUL ENDROIT.
//
// Un rapport figé est un PDF : il ne se corrige pas en place, et une copie
// téléchargée circule indéfiniment. Quand une mesure change ce qu'il affirme, il
// n'y a donc que deux gestes honnêtes, et le choix entre les deux dépend de ce que
// l'affirmation PORTE dans le document :
//
//   · `erratum`  — l'affirmation est un passage. Le reste du rapport tient, on
//                  publie la correction datée à côté du téléchargement.
//   · `withdrawn` — l'affirmation structure le document (ici deux planches entières).
//                  Une note de bas de page ne porterait pas ça : on retire le
//                  téléchargement, on dit pourquoi, et le rapport revient réécrit.
//
// 🔴 `withdrawn` VEUT DIRE « PLUS SERVI », PAS « PLUS TÉLÉCHARGEABLE » (Franck, 2026-11-05).
// Du 7 octobre au 5 novembre 2026, le fichier était bien retiré — 410 à la livraison, aperçu
// remplacé par la note, `subscribe` qui refuse — et la page CONTINUAIT de vendre le document :
// pastille « gratuit », titre d'accroche, sommaire, maquette de couverture ; et le menu
// l'annonçait sur chaque page du site. Présenter un rapport, c'est le servir. Toute surface
// qui lit cette table doit donc tirer la conséquence ENTIÈRE, dans toutes les langues :
//   · la page du rapport devient la RÉTRACTATION (titre, description, h1 portent le nom du
//     document et la note datée ; ni sommaire, ni couverture, ni chiffre d'accroche) ;
//   · le menu ne l'annonce plus — on ne met pas en vitrine ce qu'on ne sert pas ;
//   · la vitrine de la bibliothèque n'y promet ni rapport ni aperçu, seulement la note.
// Ce que le retrait ne touche PAS : l'adresse, qui répond toujours (marque-page, indexée) et
// qui est ce qui adresse les copies déjà sorties. Un 404 ne rétracte rien.
//
// Retirer ne « dé-distribue » pas : ça protège les téléchargements futurs, pas les
// passés. Ce qui adresse les copies déjà sorties, c'est la note publique et datée —
// d'où le refus de répondre par un 404, qui n'explique rien (et laisserait en plus
// le bord de Cloudflare servir une copie périmée, cf. `prune-public-json`).
//
// Les deux surfaces lisent CETTE table : la page du rapport (Astro) et la fonction
// de livraison (Cloudflare). Deux tables auraient divergé — une page annonçant le
// retrait pendant que la fonction sert encore le fichier.

export interface ReportNotice {
  /** Date ISO de la note, affichée telle quelle : une correction non datée ne vaut rien. */
  since: string;
  fr: string;
  en: string;
}

export interface ReportStatus {
  withdrawn?: ReportNotice;
  erratum?: ReportNotice;
}

// Le fait commun aux deux notes ci-dessous, pour mémoire : jusqu'au 2026-10-06, L3
// (voisinage de site à risque technologique) était renseigné hors de France depuis une
// couche de PRÉSENCE industrielle, qui peut dire « j'en ai trouvé un » mais dont le
// silence n'établit aucune absence. Les registres Seveso NATIONAUX (BRZO aux Pays-Bas)
// énumèrent les établissements : ils peuvent, eux, établir l'absence — et ils ont établi
// une présence à moins de 2 km des deux sites néerlandais notés A.
export const REPORT_STATUS: Record<string, ReportStatus> = {
  nederland: {
    withdrawn: {
      since: "2026-10-07",
      fr:
        "Rapport retiré du téléchargement le 7 octobre 2026, le temps de sa réécriture. " +
        "Deux sites néerlandais y portent la note A : Eurofiber Alblasserdam et KPN Rotterdam. " +
        "Le registre Seveso national (BRZO) établit depuis qu'un établissement classé se trouve " +
        "à moins de 2 km de chacun — 1,86 km et 1,94 km. Leur note de site est B (65,1 sur 100), " +
        "et aucun site du corpus n'atteint A aujourd'hui.",
      en:
        "Report withdrawn from download on 7 October 2026, pending rewrite. " +
        "Two Dutch sites carry an A grade in it: Eurofiber Alblasserdam and KPN Rotterdam. " +
        "The national Seveso register (BRZO) has since established that a classified establishment " +
        "sits within 2 km of each — 1.86 km and 1.94 km. Their site grade is B (65.1 out of 100), " +
        "and no site in the corpus reaches A today.",
    },
  },
  "big-tech": {
    erratum: {
      since: "2026-10-07",
      fr:
        "Errata du 7 octobre 2026 — le passage sur les deux premiers A du corpus. " +
        "Eurofiber Alblasserdam et KPN Rotterdam n'y sont plus notés A : le registre Seveso " +
        "national (BRZO) place un établissement classé à moins de 2 km de chacun, ce qui porte " +
        "leur note de site à B — 65,1 sur 100, contre 84,5 au gel du rapport. " +
        "Aucun site du corpus n'atteint A aujourd'hui. Le reste du rapport est inchangé.",
      en:
        "Erratum, 7 October 2026 — the passage on the corpus's first two A grades. " +
        "Eurofiber Alblasserdam and KPN Rotterdam no longer hold an A: the national Seveso " +
        "register (BRZO) places a classified establishment within 2 km of each, which brings " +
        "their site grade to B — 65.1 out of 100, against 84.5 when the report was frozen. " +
        "No site in the corpus reaches A today. The rest of the report is unchanged.",
    },
  },
};

export function reportStatus(slug: unknown): ReportStatus {
  return (typeof slug === "string" ? REPORT_STATUS[slug] : undefined) ?? {};
}

export function isWithdrawn(slug: unknown): boolean {
  return Boolean(reportStatus(slug).withdrawn);
}

/** La note dans la langue de la surface, `nl` repliant sur l'anglais comme les PDF. */
export function noticeText(n: ReportNotice, lang: "fr" | "en" | "nl"): string {
  return lang === "fr" ? n.fr : n.en;
}

// ─── L'ÉDITION : DE QUAND DATE CE QUE LE RAPPORT AFFIRME (Franck, 2026-11-27) ───
//
// Un rapport est une photo, le site est le film. Ses chiffres sont ceux du jour où on l'a
// gelé ; la fiche, elle, se recalcule à chaque versement. Un rapport qui ne dit pas sa date
// laisse croire qu'il parle d'aujourd'hui — et un lecteur qui trouve une note différente sur
// la fiche conclut que l'un des deux est faux. Chaque rapport porte donc sa date de gel et la
// taille du corpus qu'il a mesuré, à côté de la taille d'aujourd'hui.
//
// 🔴 LA FIN DE VIE EST UNE RÈGLE, PAS UN JUGEMENT AU CAS PAR CAS. Une édition est ARCHIVÉE dès
// que l'une des deux conditions tombe (Franck, 2026-11-27) :
//   · six mois se sont écoulés depuis le gel ;
//   · le corpus comparable a doublé depuis le gel.
// « Comparable » = l'Europe : les rapports ont été gelés avant l'entrée des sites américains.
// Comparer au total mondial ferait doubler le corpus par un périmètre que le rapport ne
// couvre pas. Archivée ne veut pas dire fausse (ça, c'est `erratum` / `withdrawn` plus
// haut) : le rapport reste téléchargeable, il dit seulement qu'il est d'une autre époque.
// La règle se calcule au build : aucun drapeau à poser à la main, donc aucun oubli possible.

export interface ReportEdition {
  /** Date ISO du gel des chiffres (source : `gel` dans smdc-library/syntheses). */
  frozen: string;
  /** Nombre de sites européens du corpus mesuré au gel (`corpus_n`). */
  corpus: number;
}

export const REPORT_EDITIONS: Record<string, ReportEdition> = {
  "big-tech": { frozen: "2026-07-22", corpus: 1269 },
  banques: { frozen: "2026-07-22", corpus: 1269 },
  france: { frozen: "2026-07-30", corpus: 1405 },
  nederland: { frozen: "2026-07-30", corpus: 1405 },
};

export const EDITION_MAX_MONTHS = 6;
export const EDITION_MAX_GROWTH = 2;

export interface EditionState extends ReportEdition {
  archived: boolean;
  /** Date ISO où la règle des six mois archive l'édition. */
  expires: string;
}

/** L'état d'une édition à une date donnée, contre le corpus européen du moment.
 *  `corpusNow` absent (build sans corpus) : seule la règle des six mois s'applique —
 *  une absence ne se lit jamais comme un doublement. */
export function editionState(slug: unknown, today: Date, corpusNow: number | null): EditionState | null {
  const e = typeof slug === "string" ? REPORT_EDITIONS[slug] : undefined;
  if (!e) return null;
  const exp = new Date(`${e.frozen}T00:00:00Z`);
  exp.setUTCMonth(exp.getUTCMonth() + EDITION_MAX_MONTHS);
  const expires = exp.toISOString().slice(0, 10);
  const grown = corpusNow !== null && corpusNow >= EDITION_MAX_GROWTH * e.corpus;
  return { ...e, expires, archived: today.toISOString().slice(0, 10) >= expires || grown };
}
