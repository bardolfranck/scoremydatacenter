// Libellés lisibles des valeurs catégorielles et des unités.
//
// POURQUOI. La fiche affichait la clé technique du moteur — `saturated`,
// `artificialized`, `no_stress` — en anglais, sur le site français. Une clé n'est pas
// une phrase : le lecteur doit lire ce que la donnée dit. La raison est la LISIBILITÉ,
// rien d'autre ; les clés quittent le HTML au passage, mais ce n'est pas un motif
// (le barème n'est pas publié, et « réseau saturé » se remappe aussi bien que
// `saturated`).
//
// DEUX RÈGLES D'ÉCRITURE.
// 1. Décrire le FAIT, jamais le juger — la note porte déjà le jugement (G6).
// 2. Une absence se dit « à notre connaissance » (Franck, 2026-10-05). On ne peut
//    pas prouver qu'aucun site n'existe ; on peut dire qu'un registre qui les
//    recense n'en déclare aucun. Sans cette réserve aucun A ne serait attribuable,
//    et avec elle la phrase reste vraie si un site non recensé apparaît plus tard.
//    Elle ne va QUE sur une absence : `none_within_5km`, `distant_over_5km`.
//
// Formulations validées par Franck le 2026-10-05, y compris les trois cas qu'il a
// tranchés lui-même : le profil social d'une commune (favorable / intermédiaire /
// fragile), le dossier de l'opérateur, et les retombées annoncées.

type Libelle = { fr: string; en: string };

const L = (fr: string, en: string): Libelle => ({ fr, en });

export const VALEURS: Record<string, Record<string, Libelle>> = {
  // ——— Énergie ———
  E2: {
    ample: L("capacité de raccordement largement disponible", "ample connection capacity"),
    adequate: L("capacité de raccordement suffisante", "adequate connection capacity"),
    constrained: L("capacité de raccordement contrainte", "constrained connection capacity"),
    saturated: L("réseau saturé au point de raccordement", "grid saturated at the connection point"),
  },
  E3: {
    low: L("réseau local peu encombré", "little local grid congestion"),
    moderate: L("réseau local moyennement encombré", "moderate local grid congestion"),
    high: L("réseau local très encombré", "heavy local grid congestion"),
    critical: L("réseau local en congestion critique", "critical local grid congestion"),
  },
  E6: {
    raccordable: L("raccordable à un réseau de chaleur existant", "connectable to an existing heat network"),
    proche: L("réseau de chaleur à proximité", "heat network nearby"),
    eloigne: L("aucun réseau de chaleur à proximité", "no heat network nearby"),
  },
  E7: {
    realise: L("récupération de chaleur réalisée", "heat recovery in operation"),
    contrat_signe: L("contrat de récupération de chaleur signé", "heat-recovery contract signed"),
    etude: L("récupération de chaleur à l'étude", "heat recovery under study"),
    intention: L("intention annoncée, sans engagement", "stated intention, no commitment"),
    aucun: L("aucune récupération de chaleur annoncée", "no heat recovery announced"),
  },

  // ——— Eau ———
  W1: {
    no_stress: L("zone sans stress hydrique mesuré", "no measured water stress in the area"),
    moderate: L("stress hydrique modéré", "moderate water stress"),
    high: L("stress hydrique élevé", "high water stress"),
    zre_or_crisis: L("zone de répartition des eaux ou arrêté de crise", "water-allocation zone or drought order"),
  },
  W2: {
    very_good: L("masse d'eau en très bon état", "water body in very good status"),
    good: L("masse d'eau en bon état", "water body in good status"),
    moderate: L("masse d'eau en état moyen", "water body in moderate status"),
    poor: L("masse d'eau en état médiocre", "water body in poor status"),
    bad: L("masse d'eau en mauvais état", "water body in bad status"),
  },
  W3: {
    low: L("prélèvements faibles sur le bassin", "low abstraction in the basin"),
    moderate: L("prélèvements modérés sur le bassin", "moderate abstraction in the basin"),
    high: L("prélèvements élevés sur le bassin", "high abstraction in the basin"),
    very_high: L("prélèvements très élevés sur le bassin", "very high abstraction in the basin"),
  },
  W4: {
    closed_loop_dry: L("refroidissement en circuit fermé, sans eau", "dry closed-loop cooling"),
    hybrid_adiabatic: L("refroidissement hybride adiabatique", "hybrid adiabatic cooling"),
    evaporative_open: L("refroidissement évaporatif en circuit ouvert", "open-circuit evaporative cooling"),
    unknown: L("technologie de refroidissement non communiquée", "cooling technology not disclosed"),
  },

  // ——— Foncier & biodiversité ———
  F1: {
    overlap: L("recoupe une zone naturelle protégée", "overlaps a protected natural area"),
    adjacent_under_1km: L("zone naturelle protégée à moins de 1 km", "protected natural area within 1 km"),
    near_1_to_5km: L("zone naturelle protégée entre 1 et 5 km", "protected natural area 1–5 km away"),
    distant_over_5km: L(
      "aucune zone naturelle protégée recensée à moins de 5 km, à notre connaissance",
      "no protected natural area on record within 5 km, to our knowledge",
    ),
  },
  F2: {
    artificialized: L("terrain déjà artificialisé", "previously developed land"),
    transitional: L("terrain en transition", "transitional land"),
    agricultural: L("terre agricole", "farmland"),
    natural_or_enaf: L("espace naturel, agricole ou forestier", "natural, agricultural or forest land"),
  },
  F5: {
    erc_complet: L("mesures éviter-réduire-compenser complètes", "full avoid-reduce-offset measures"),
    partiel: L("mesures éviter-réduire-compenser partielles", "partial avoid-reduce-offset measures"),
    aucun: L("aucune mesure éviter-réduire-compenser", "no avoid-reduce-offset measures"),
  },

  // ——— Impact local ———
  L1: {
    strong_fit: L("profil social de la commune : favorable", "municipality's social profile: favourable"),
    neutral: L("profil social de la commune : intermédiaire", "municipality's social profile: intermediate"),
    sensitive: L("profil social de la commune : fragile", "municipality's social profile: fragile"),
  },
  L3: {
    none_within_5km: L(
      "aucun site à risque technologique recensé dans un rayon de 5 km, à notre connaissance",
      "no technological-risk site on record within 5 km, to our knowledge",
    ),
    seveso_low_within_5km: L("un établissement Seveso recensé à moins de 5 km", "a Seveso establishment on record within 5 km"),
    seveso_high_within_2km: L(
      "un établissement Seveso seuil haut recensé à moins de 2 km",
      "an upper-tier Seveso establishment on record within 2 km",
    ),
  },
  L5: {
    documented_significant: L("retombées fiscales documentées", "documented tax revenue"),
    announced_unquantified: L("retombées annoncées sans chiffrage", "revenue announced without figures"),
    none: L("aucune retombée fiscale annoncée", "no tax revenue announced"),
  },

  // ——— Transparence & gouvernance ———
  T2: {
    full_dossier_online: L("dossier complet publié en ligne", "full dossier published online"),
    partial: L("dossier partiellement publié", "dossier partially published"),
    minimal: L("dossier minimal", "minimal dossier"),
    unavailable: L("dossier non accessible", "dossier not accessible"),
  },
};

// Unités : on traduit ce qui est une phrase, on garde ce qui est une notation
// standard (gCO2e/kWh, PUE, L/kWh se lisent pareil dans les deux langues).
const UNITES: Record<string, string> = {
  hectares: "hectares",
  "% renewable": "% renouvelable",
  "MW per 1000 inhabitants": "MW pour 1000 habitants",
  "permanent jobs per 100 MW": "emplois permanents pour 100 MW",
};

/** Le libellé d'une valeur, ou la valeur brute si elle n'en a pas encore. */
export function libelleValeur(indicateur: string, valeur: unknown, lang: string): string {
  if (typeof valeur !== "string") return String(valeur);
  const l = VALEURS[indicateur]?.[valeur];
  if (!l) return valeur;
  return lang === "fr" ? l.fr : l.en;
}

/** L'unité dans la langue de la page ; inchangée si c'est une notation. */
export function libelleUnite(unite: string, lang: string): string {
  if (lang !== "fr") return unite;
  return UNITES[unite] ?? unite;
}
