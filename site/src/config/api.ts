// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// The ONE place the developer page reads its moving targets (brief §6): the API
// base URL, the site origin, the Lemon Squeezy checkout link. Staging → prod is
// a single edit here — no rewrite across the page's curl examples or the
// reveal-key button. The paid endpoints live in a PRIVATE Worker repo; this file
// only names its public URL.

// Prod: the custom domain is live (CF route + DNS) and serves every endpoint
// (verified /v1/datacenters → 200). Never show the personal workers.dev host on
// a paid product page. Flip back only if the custom route breaks.
export const API_BASE = "https://api.scoremydatacenter.org";
// Staging fallback (personal): https://smdc-api.bardolfranck.workers.dev

export const SITE = "https://scoremydatacenter.org";

// Lemon Squeezy checkout for the "Data DC" plan — placeholder until the LS
// product exists (setup = Franck). Empty string → the CTA points at the passive
// contact mailto instead of a dead checkout link.
export const LEMONSQUEEZY_CHECKOUT_URL_DATA_DC = "";

export const CONTACT_EMAIL = "contact@scoremydatacenter.org";
