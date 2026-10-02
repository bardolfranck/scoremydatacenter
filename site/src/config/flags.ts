// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Inline SVG flags for the « N pays » hero signature. Real SVG (not emoji —
// emoji flags render as letter codes on Windows/Chrome), tiny, crisp,
// theme-independent. Each entry is the INNER markup of a 30×20 viewBox; the
// component clips to rounded corners. A country the corpus reaches without a
// flag here falls back to an ISO chip (never breaks) — adding a country =
// add its flag below. The set covers the current 17 + the likely-next
// European countries so the ring grows without a code change.

export const FLAG_SVG: Record<string, string> = {
  // — current corpus (17) —
  // Hors Europe — l'international est dans la mission, pas une extension (Franck).
  IS: '<rect width="30" height="20" fill="#02529C"/><rect y="7.4" width="30" height="5.2" fill="#fff"/><rect x="9.4" width="5.2" height="20" fill="#fff"/><rect y="8.8" width="30" height="2.4" fill="#DC1E35"/><rect x="10.8" width="2.4" height="20" fill="#DC1E35"/>',
  IL: '<rect width="30" height="20" fill="#fff"/><rect y="2.4" width="30" height="2.6" fill="#0038B8"/><rect y="15" width="30" height="2.6" fill="#0038B8"/><path d="M15 6.6 12.2 11.4h5.6zM15 13.4 12.2 8.6h5.6z" fill="none" stroke="#0038B8" stroke-width="0.75"/>',
  US: '<rect width="30" height="20" fill="#B22234"/><rect y="1.54" width="30" height="1.54" fill="#fff"/><rect y="4.62" width="30" height="1.54" fill="#fff"/><rect y="7.70" width="30" height="1.54" fill="#fff"/><rect y="10.78" width="30" height="1.54" fill="#fff"/><rect y="13.86" width="30" height="1.54" fill="#fff"/><rect y="16.94" width="30" height="1.54" fill="#fff"/><rect width="12" height="10.77" fill="#3C3B6E"/><circle cx="1.4" cy="1.4" r="0.45" fill="#fff"/><circle cx="3.5" cy="1.4" r="0.45" fill="#fff"/><circle cx="5.6" cy="1.4" r="0.45" fill="#fff"/><circle cx="7.7" cy="1.4" r="0.45" fill="#fff"/><circle cx="9.8" cy="1.4" r="0.45" fill="#fff"/><circle cx="1.4" cy="3.5" r="0.45" fill="#fff"/><circle cx="3.5" cy="3.5" r="0.45" fill="#fff"/><circle cx="5.6" cy="3.5" r="0.45" fill="#fff"/><circle cx="7.7" cy="3.5" r="0.45" fill="#fff"/><circle cx="9.8" cy="3.5" r="0.45" fill="#fff"/><circle cx="1.4" cy="5.6" r="0.45" fill="#fff"/><circle cx="3.5" cy="5.6" r="0.45" fill="#fff"/><circle cx="5.6" cy="5.6" r="0.45" fill="#fff"/><circle cx="7.7" cy="5.6" r="0.45" fill="#fff"/><circle cx="9.8" cy="5.6" r="0.45" fill="#fff"/><circle cx="1.4" cy="7.7" r="0.45" fill="#fff"/><circle cx="3.5" cy="7.7" r="0.45" fill="#fff"/><circle cx="5.6" cy="7.7" r="0.45" fill="#fff"/><circle cx="7.7" cy="7.7" r="0.45" fill="#fff"/><circle cx="9.8" cy="7.7" r="0.45" fill="#fff"/>',
  MA: '<rect width="30" height="20" fill="#C1272D"/><path d="M15 6.4 16.8 11.9 12.1 8.5h5.8L13.2 11.9z" fill="none" stroke="#006233" stroke-width="0.8"/>',
  TN: '<rect width="30" height="20" fill="#E70013"/><circle cx="15" cy="10" r="6" fill="#fff"/><circle cx="15.6" cy="10" r="4.1" fill="#E70013"/><circle cx="17.2" cy="10" r="3.3" fill="#fff"/><path d="M16.2 8.2 16.9 10.3 15.1 9h2.2L15.5 10.3z" fill="#E70013"/>',
  DZ: '<rect width="30" height="20" fill="#fff"/><rect width="15" height="20" fill="#006233"/><circle cx="15" cy="10" r="5.4" fill="#D21034"/><circle cx="16.4" cy="10" r="4.4" fill="#fff"/><path d="M17.4 7.9 18.2 10.3 16.2 8.8h2.5L16.7 10.3z" fill="#D21034"/>',
  FR: '<rect width="10" height="20" fill="#002395"/><rect x="10" width="10" height="20" fill="#fff"/><rect x="20" width="10" height="20" fill="#ED2939"/>',
  DE: '<rect width="30" height="6.67" fill="#000"/><rect width="30" height="6.67" y="6.67" fill="#D00"/><rect width="30" height="6.66" y="13.33" fill="#FFCE00"/>',
  IT: '<rect width="10" height="20" fill="#009246"/><rect x="10" width="10" height="20" fill="#fff"/><rect x="20" width="10" height="20" fill="#CE2B37"/>',
  BE: '<rect width="10" height="20" fill="#000"/><rect x="10" width="10" height="20" fill="#FDDA24"/><rect x="20" width="10" height="20" fill="#EF3340"/>',
  NL: '<rect width="30" height="6.67" fill="#AE1C28"/><rect width="30" height="6.67" y="6.67" fill="#fff"/><rect width="30" height="6.66" y="13.33" fill="#21468B"/>',
  ES: '<rect width="30" height="20" fill="#AA151B"/><rect width="30" height="10" y="5" fill="#F1BF00"/>',
  PT: '<rect width="12" height="20" fill="#060"/><rect x="12" width="18" height="20" fill="#F00"/><circle cx="12" cy="10" r="3.2" fill="#FFCC4D" stroke="#fff" stroke-width=".6"/>',
  AT: '<rect width="30" height="6.67" fill="#ED2939"/><rect width="30" height="6.67" y="6.67" fill="#fff"/><rect width="30" height="6.66" y="13.33" fill="#ED2939"/>',
  PL: '<rect width="30" height="10" fill="#fff"/><rect width="30" height="10" y="10" fill="#DC143C"/>',
  LU: '<rect width="30" height="6.67" fill="#ED2939"/><rect width="30" height="6.67" y="6.67" fill="#fff"/><rect width="30" height="6.66" y="13.33" fill="#00A1DE"/>',
  IE: '<rect width="10" height="20" fill="#169B62"/><rect x="10" width="10" height="20" fill="#fff"/><rect x="20" width="10" height="20" fill="#FF883E"/>',
  CH: '<rect width="30" height="20" fill="#D52B1E"/><rect x="12.5" y="5" width="5" height="10" fill="#fff"/><rect x="10" y="7.5" width="10" height="5" fill="#fff"/>',
  DK: '<rect width="30" height="20" fill="#C60C30"/><rect x="9" width="4" height="20" fill="#fff"/><rect y="8" width="30" height="4" fill="#fff"/>',
  SE: '<rect width="30" height="20" fill="#006AA7"/><rect x="9" width="4" height="20" fill="#FECC00"/><rect y="8" width="30" height="4" fill="#FECC00"/>',
  NO: '<rect width="30" height="20" fill="#EF2B2D"/><rect x="8" width="6" height="20" fill="#fff"/><rect y="7" width="30" height="6" fill="#fff"/><rect x="9.5" width="3" height="20" fill="#002868"/><rect y="8.5" width="30" height="3" fill="#002868"/>',
  FI: '<rect width="30" height="20" fill="#fff"/><rect x="9" width="4" height="20" fill="#003580"/><rect y="8" width="30" height="4" fill="#003580"/>',
  GB: '<rect width="30" height="20" fill="#012169"/><path d="M0,0 30,20 M30,0 0,20" stroke="#fff" stroke-width="4"/><path d="M0,0 30,20 M30,0 0,20" stroke="#C8102E" stroke-width="2"/><rect x="12" width="6" height="20" fill="#fff"/><rect y="7" width="30" height="6" fill="#fff"/><rect x="13" width="4" height="20" fill="#C8102E"/><rect y="8" width="30" height="4" fill="#C8102E"/>',
  // — likely-next European countries (ring grows without a code change) —
  CZ: '<rect width="30" height="10" fill="#fff"/><rect width="30" height="10" y="10" fill="#D7141A"/><path d="M0,0 15,10 0,20Z" fill="#11457E"/>',
  SK: '<rect width="30" height="6.67" fill="#fff"/><rect width="30" height="6.67" y="6.67" fill="#0B4EA2"/><rect width="30" height="6.66" y="13.33" fill="#EE1C25"/>',
  HU: '<rect width="30" height="6.67" fill="#CD2A3E"/><rect width="30" height="6.67" y="6.67" fill="#fff"/><rect width="30" height="6.66" y="13.33" fill="#436F4D"/>',
  RO: '<rect width="10" height="20" fill="#002B7F"/><rect x="10" width="10" height="20" fill="#FCD116"/><rect x="20" width="10" height="20" fill="#CE1126"/>',
  BG: '<rect width="30" height="6.67" fill="#fff"/><rect width="30" height="6.67" y="6.67" fill="#00966E"/><rect width="30" height="6.66" y="13.33" fill="#D62612"/>',
  GR: '<rect width="30" height="20" fill="#0D5EAF"/><rect y="2.2" width="30" height="2.2" fill="#fff"/><rect y="6.6" width="30" height="2.2" fill="#fff"/><rect y="11" width="30" height="2.2" fill="#fff"/><rect y="15.4" width="30" height="2.2" fill="#fff"/><rect width="12.1" height="11" fill="#0D5EAF"/><rect x="4.4" width="3.3" height="11" fill="#fff"/><rect y="3.9" width="12.1" height="3.3" fill="#fff"/>',
  HR: '<rect width="30" height="6.67" fill="#FF0000"/><rect width="30" height="6.67" y="6.67" fill="#fff"/><rect width="30" height="6.66" y="13.33" fill="#171796"/>',
  SI: '<rect width="30" height="6.67" fill="#fff"/><rect width="30" height="6.67" y="6.67" fill="#0000A0"/><rect width="30" height="6.66" y="13.33" fill="#ED1C24"/>',
  EE: '<rect width="30" height="6.67" fill="#0072CE"/><rect width="30" height="6.67" y="6.67" fill="#000"/><rect width="30" height="6.66" y="13.33" fill="#fff"/>',
  LV: '<rect width="30" height="20" fill="#9E3039"/><rect y="8" width="30" height="4" fill="#fff"/>',
  LT: '<rect width="30" height="6.67" fill="#FDB913"/><rect width="30" height="6.67" y="6.67" fill="#006A44"/><rect width="30" height="6.66" y="13.33" fill="#C1272D"/>',
  RS: '<rect width="30" height="6.67" fill="#C6363C"/><rect width="30" height="6.67" y="6.67" fill="#0C4076"/><rect width="30" height="6.66" y="13.33" fill="#fff"/>',
  UA: '<rect width="30" height="10" fill="#0057B7"/><rect width="30" height="10" y="10" fill="#FFD700"/>',
};

export const COUNTRY_NAME: Record<string, { fr: string; en: string }> = {
  IS: { fr: "Islande", en: "Iceland" },
  IL: { fr: "Israël", en: "Israel" },
  US: { fr: "États-Unis", en: "United States" },
  MA: { fr: "Maroc", en: "Morocco" },
  TN: { fr: "Tunisie", en: "Tunisia" },
  DZ: { fr: "Algérie", en: "Algeria" },
  FR: { fr: "France", en: "France" }, DE: { fr: "Allemagne", en: "Germany" },
  IT: { fr: "Italie", en: "Italy" }, BE: { fr: "Belgique", en: "Belgium" },
  NL: { fr: "Pays-Bas", en: "Netherlands" }, ES: { fr: "Espagne", en: "Spain" },
  PT: { fr: "Portugal", en: "Portugal" }, AT: { fr: "Autriche", en: "Austria" },
  PL: { fr: "Pologne", en: "Poland" }, LU: { fr: "Luxembourg", en: "Luxembourg" },
  IE: { fr: "Irlande", en: "Ireland" }, CH: { fr: "Suisse", en: "Switzerland" },
  DK: { fr: "Danemark", en: "Denmark" }, SE: { fr: "Suède", en: "Sweden" },
  NO: { fr: "Norvège", en: "Norway" }, FI: { fr: "Finlande", en: "Finland" },
  GB: { fr: "Royaume-Uni", en: "United Kingdom" },
};

/** A 30×20 rounded flag, or null when the country has no flag yet (→ ISO chip fallback). */
export function flagInner(iso: string): string | null {
  return FLAG_SVG[iso.toUpperCase()] ?? null;
}
