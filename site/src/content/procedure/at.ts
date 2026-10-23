// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Autriche — 9 fiches, toutes en service. État fédéral : le droit de la construction
// appartient aux Länder, et il n'y a donc PAS de délai fédéral pour le permis lui-même.
// Mais le délai de recours devant le tribunal administratif, lui, est fédéral et vaut
// contre les décisions des autorités des Länder : c'est ce qu'on publie, et rien de plus.
// Texte lu sur ris.bka.gv.at le 2026-10-23.
import type { ProcedureCountry } from "./types";

export const AT: ProcedureCountry = {
  country: "AT",
  decentralised: false,
  inherits: "EU",
  frame: {
    fr: "En Autriche, le droit de la construction appartient aux Länder : le permis et ses conditions se lisent dans le Baurecht du Land. Le délai de recours devant le tribunal administratif, lui, est fédéral.",
    en: "In Austria building law belongs to the Länder: the permit and its conditions are read in that Land's Baurecht. The deadline to appeal to the administrative court, however, is federal.",
  },
  national: {
    authority: {
      fr: "l'autorité du Land ou la commune selon le Baurecht applicable, puis le tribunal administratif du Land",
      en: "the Land authority or the municipality under the applicable Baurecht, then the Land's administrative court",
    },
    windows: {},
    deadlines: [
      {
        text: {
          fr: "Quatre semaines pour former un recours contre la décision d'une autorité devant le tribunal administratif.",
          en: "Four weeks to bring an appeal against an authority's decision before the administrative court.",
        },
        cite: "VwGVG § 7 Abs. 4",
        url: "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20008255&Paragraf=7",
        verified: "2026-10-23",
      },
    ],
    documents: [],
  },
};
