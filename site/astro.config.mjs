// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://scoremydatacenter.org',
  // The dev toolbar floats over the footer and hides the legal/contact links
  // during reviews; nobody here uses it. Dev-only — production never has it.
  devToolbar: { enabled: false },
  integrations: [sitemap()],
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr'],
  },
});
