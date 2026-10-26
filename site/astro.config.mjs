// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import fs from 'node:fs';

// lastmod par fiche : la date du dernier build où le CONTENU de la fiche a bougé, pas la
// date du build. Un lastmod qui change à chaque build annoncerait 1 438 pages modifiées
// tous les jours — Google finit par l'ignorer, et on perdrait exactement ce qu'on cherche :
// déclencher un recrawl quand une note bouge vraiment (cas vécu : Fouju E→D).
// Date de MISE EN LIGNE des portraits. Ce n'est pas une date de contenu : c'est le jour où
// ces 6 566 URL ont commencé à exister. Constante, donc stable d'un build à l'autre.
const PORTRAITS_PUBLIES = "2026-10-25";

const lastmodById = Object.fromEntries(
  fs.readdirSync('public/data/dc')
    .filter((f) => f.endsWith('.json'))
    .map((f) => {
      const d = JSON.parse(fs.readFileSync(`public/data/dc/${f}`, 'utf-8'));
      return [d.id, d.content_changed_at ?? d.updated_at];
    })
    .filter(([, when]) => when),
);

export default defineConfig({
  site: 'https://scoremydatacenter.org',
  // The dev toolbar floats over the footer and hides the legal/contact links
  // during reviews; nobody here uses it. Dev-only — production never has it.
  devToolbar: { enabled: false },
  integrations: [sitemap({
    serialize(item) {
      // Le portrait lit le MÊME artefact que la fiche : il bouge quand elle bouge, donc il
      // porte la même date. Sans ce `(?:portrait\/)?`, les 6 566 portraits partaient sans
      // lastmod — soit la moitié du site, et justement la moitié toute neuve, celle qu'on a
      // le plus besoin de faire explorer.
      const m = item.url.match(/\/dc\/([^/]+)\/(?:portrait\/)?$/) ?? item.url.match(/\/dc\/([^/]+)$/);
      let when = m && lastmodById[m[1]];
      // 🔴 UNE PAGE NEUVE NE PEUT PAS PORTER UNE VIEILLE DATE. Un portrait hérite de la date
      // de CONTENU de sa fiche — c'est juste pour ses données, et faux pour son existence :
      // les 6 566 portraits sont nés le 25 octobre et annonçaient « modifié le 17 ». Pire,
      // l'index de sitemap prend le MAXIMUM de ces dates : il déclarait « rien n'a bougé
      // depuis le 20 octobre » le jour où le site doublait de taille. Un explorateur qui fait
      // confiance à cette date ne redemande jamais le sitemap, et les pages neuves attendent.
      // La borne s'efface d'elle-même : dès qu'une fiche bouge après cette date, c'est sa
      // date de contenu qui reprend la main.
      if (m && item.url.includes("/portrait/") && (!when || when < PORTRAITS_PUBLIES)) {
        when = PORTRAITS_PUBLIES;
      }
      if (when) item.lastmod = new Date(`${when}T00:00:00Z`).toISOString();
      return item;
    },
  })],
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr'],
  },
});
