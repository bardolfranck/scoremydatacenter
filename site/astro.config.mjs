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
      const m = item.url.match(/\/dc\/([^/]+)\/?$/);
      const when = m && lastmodById[m[1]];
      if (when) item.lastmod = new Date(`${when}T00:00:00Z`).toISOString();
      return item;
    },
  })],
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr'],
  },
});
