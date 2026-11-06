// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// 🔴 UNE RÉGION NE S'AFFICHE QUE SI ELLE SE LIT. Trouvé le 2026-11-06 en vérifiant les
// pages belges : la fiche d'Anvers disait « datacenter in Antwerpen (VAN) ». `VAN` est un
// code de zone administrative, pas un mot — et ce n'était pas isolé : 1 368 fiches sur
// 3 292 portent un `admin_area` qui est un code, et 679 descriptions servies l'affichaient.
// Dans les trois langues, et dans la balise que Google montre.
//
// LE CHAMP EST HÉTÉROGÈNE PAR CONSTRUCTION, et c'est la vraie cause : selon la source, il
// porte un NOM COMPLET (« New York » pour les États-Unis — c'est même écrit dans
// `content/procedure/us.ts`), un NUMÉRO DE DÉPARTEMENT français (« 91 ») ou un CODE de
// subdivision (`ENG`, `NW`, `HE`, `BY`, `MD`, `VAN`). Le réparer dans la donnée voudrait
// dire traduire une centaine de noms de régions en trois langues : un chantier, pas un
// correctif. L'affichage, lui, peut trancher tout de suite — et le faire sans jamais rien
// inventer.
//
// LA RÈGLE : on montre ce qu'un lecteur peut lire, on cache le reste.
// · un numéro — « 91 », « 59 » : c'est la convention française, tout lecteur français la
//   lit, et c'est une requête (« data center 91 »). On garde.
// · un nom — « New York », « Nordrhein-Westfalen » : c'est un mot. On garde.
// · un code en capitales — `ENG`, `VAN` : ce n'est une convention nulle part, et la commune
//   est déjà nommée juste avant. On cache : « in Slough » plutôt que « in Slough (ENG) ».
//   Rien n'est perdu, puisque le pays est dit par ailleurs.
//
// ⚠️ Ce qui NE change pas : `addressRegion` du balisage Schema.org garde la valeur brute.
// Une donnée structurée est lue par une machine, qui attend un code de subdivision ; le
// masquage est une règle d'AFFICHAGE, pas une correction de la donnée.

/** Une zone administrative lisible par un humain — ou rien. */
export function regionLisible(admin: unknown): string {
  const v = String(admin ?? "").trim();
  if (!v) return "";
  // Un code : deux à quatre caractères, aucune minuscule, aucun chiffre.
  const estUnCode = v.length <= 4 && !/[a-z0-9]/.test(v);
  return estUnCode ? "" : v;
}

/** « Commune (Région) » quand la région se lit, « Commune » sinon. */
export function communeEtRegion(municipality: unknown, admin: unknown): string {
  const ville = String(municipality ?? "").trim();
  const region = regionLisible(admin);
  if (!ville) return region;
  return region ? `${ville} (${region})` : ville;
}
