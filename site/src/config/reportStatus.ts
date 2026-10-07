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
        "et aucun site du corpus n'atteint A aujourd'hui. Ces deux notes portaient deux pages " +
        "entières du rapport : un errata n'y suffisait pas. " +
        "La correction vient de notre propre méthode : une source qui recense les établissements " +
        "remplace une couche qui ne pouvait pas établir une absence.",
      en:
        "Report withdrawn from download on 7 October 2026, pending rewrite. " +
        "Two Dutch sites carry an A grade in it: Eurofiber Alblasserdam and KPN Rotterdam. " +
        "The national Seveso register (BRZO) has since established that a classified establishment " +
        "sits within 2 km of each — 1.86 km and 1.94 km. Their site grade is B (65.1 out of 100), " +
        "and no site in the corpus reaches A today. Those two grades carried two full pages of the " +
        "report, so an erratum would not have been enough. " +
        "The correction comes from our own method: a source that enumerates establishments replaces " +
        "a layer that could never establish an absence.",
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
