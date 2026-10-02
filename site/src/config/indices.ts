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
