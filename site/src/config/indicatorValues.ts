// Libellés lisibles des valeurs catégorielles.
//
// POURQUOI CE FICHIER. Les valeurs d'un indicateur catégoriel sont des clés
// techniques — `none_within_5km`, `saturated`, `artificialized` — et la fiche les
// affichait telles quelles, en anglais, sur le site français. Une clé n'est pas une
// phrase : le lecteur doit lire ce que la donnée dit, pas le nom que le moteur lui
// donne.
//
// ET SURTOUT, POUR UNE ABSENCE : une absence est toujours « à notre connaissance »
// (Franck, 2026-10-05). On ne peut pas prouver qu'aucun établissement n'existe ; on
// peut dire qu'un registre qui les recense n'en déclare aucun. Sans cette réserve,
// aucun A ne serait jamais attribuable — et avec elle, la phrase reste vraie même si
// un site non recensé apparaît plus tard. La ligne de source, juste à côté, nomme
// l'instrument et sa limite : les deux se lisent ensemble.
//
// Les autres indicateurs catégoriels (E2, E3, E6, F1, F2, L1, W1, W2, W3…) affichent
// encore leur clé brute : leur formulation publique est une décision éditoriale, pas
// une traduction mécanique, et elle attend l'arbitrage de Franck.

type Libelle = { fr: string; en: string };

export const VALEURS: Record<string, Record<string, Libelle>> = {
  L3: {
    none_within_5km: {
      fr: "aucun site à risque technologique recensé dans un rayon de 5 km, à notre connaissance",
      en: "no technological-risk site on record within 5 km, to our knowledge",
    },
    seveso_low_within_5km: {
      fr: "un établissement Seveso recensé à moins de 5 km",
      en: "a Seveso establishment on record within 5 km",
    },
    seveso_high_within_2km: {
      fr: "un établissement Seveso seuil haut recensé à moins de 2 km",
      en: "an upper-tier Seveso establishment on record within 2 km",
    },
  },
};

/** Le libellé d'une valeur, ou la valeur brute si elle n'en a pas encore. */
export function libelleValeur(indicateur: string, valeur: unknown, lang: string): string {
  if (typeof valeur !== "string") return String(valeur);
  const l = VALEURS[indicateur]?.[valeur];
  if (!l) return valeur;
  return lang === "fr" ? l.fr : l.en;
}
