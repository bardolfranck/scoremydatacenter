// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Country SITE index — shared display constants.
import { COUNTRY_NAMES as NOMS_UE } from "./stats";
import { COUNTRY_NAME as NOMS_MONDE } from "./flags";

// Les noms de pays vivaient dans DEUX recensements : 17 pays dans stats.ts (l'Europe du
// corpus) et 51 dans flags.ts (l'anneau de la page d'accueil). Un pays suivi hors des 17
// s'affichait donc en CODE ISO sur cette page et sur le bloc indice de l'accueil — constaté
// sur Israël le 2026-10-02. On fusionne, stats.ts gardant la main sur ses 17 libellés.
export const COUNTRY_NAMES: Record<string, { fr: string; en: string }> = {
  ...NOMS_MONDE, ...NOMS_UE,
};

// 🔴 ICI et pas dans `stats.ts` : c'est ce fichier qui porte la table FUSIONNÉE (les
// 23 pays, Europe du corpus + anneau mondial). Posée à côté des 19, l'aide serait
// retombée sur le code ISO pour les quatre autres — une régression invisible tant
// qu'aucune fiche n'en vient.
// 🔴 LE MÊME NOM NE SE DIT PAS PAREIL SEUL ET DANS UNE PHRASE. « 🇺🇸 Verenigde Staten » dans
// une liste à côté du drapeau, mais « deze site ligt in DE Verenigde Staten » : le
// néerlandais met l'article aux noms de pays PLURIELS et à ceux en « Koninkrijk/Republiek ».
// Stocker la forme avec article partout écorcherait la liste ; la forme nue partout écrirait
// une faute dans la phrase. On garde donc les deux, pour les seuls pays qui le demandent.
// (Règle de rapports-SMDC, 2026-11-03. Le français et l'anglais n'en ont pas besoin ici :
// « se trouve en France », « located in the United States » — l'article y est dans le
// gabarit ou pas du tout.)
const NOM_EN_PHRASE: Record<string, Partial<Record<string, string>>> = {
  US: { nl: "de Verenigde Staten" },
  GB: { nl: "het Verenigd Koninkrijk" },
};

/** Le nom d'un pays tel qu'il s'écrit DANS une phrase — sa forme nue si rien ne diffère. */
export function nomDePaysEnPhrase(iso: string, lang: string): string {
  return NOM_EN_PHRASE[iso]?.[lang] ?? (COUNTRY_NAMES as any)[iso]?.[lang] ?? iso;
}

// Un drapeau emoji N'EST PAS une liste à tenir à jour : c'est le code ISO écrit avec les
// deux indicateurs régionaux correspondants. Le recensement manuel a laissé passer un pays
// suivi, qui est sorti en lettres. On dérive — et l'oubli n'est plus possible.
//
// SAUF pour les territoires dont l'État n'est pas reconnu, où le drapeau serait une prise de
// position. Règle Franck (2026-10-02) : drapeau si l'État est reconnu par l'ONU, ou par la
// France. Le Sahara occidental est un territoire non autonome au sens de l'ONU, qui n'y
// reconnaît aucun État ; la France a reconnu la souveraineté marocaine en juillet 2024.
const SANS_DRAPEAU: Record<string, string> = {
  EH: "territoire non autonome au sens de l'ONU — aucun État reconnu, ni par l'ONU ni par la France",
};

export function countryFlag(iso: string): string {
  if (!/^[A-Z]{2}$/.test(iso) || iso in SANS_DRAPEAU) return "";
  return String.fromCodePoint(...[...iso].map((c) => 0x1f1e6 + c.charCodeAt(0) - 65));
}
