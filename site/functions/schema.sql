-- SPDX-License-Identifier: AGPL-3.0-or-later
-- Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
-- D1 schema for the report email-gate. Franck's own, exportable store.
-- Apply:  npx wrangler d1 execute smdc-leads --file=functions/schema.sql --remote
--
-- CNIL-minimal: we keep only what the purpose needs — the address, which report
-- it was for, the language, the consent flag, and the lifecycle timestamps.
-- No raw IP, no tracking, no profile. One row per (email, report).

CREATE TABLE IF NOT EXISTS subscribers (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  email           TEXT    NOT NULL,
  report          TEXT    NOT NULL,
  lang            TEXT    NOT NULL DEFAULT 'fr',
  status          TEXT    NOT NULL DEFAULT 'pending',   -- pending | confirmed | unsubscribed
  token           TEXT    NOT NULL,                     -- confirm / download / unsubscribe token
  consent         INTEGER NOT NULL DEFAULT 0,           -- 1 = explicit checkbox ticked
  created_at      TEXT    NOT NULL,
  confirmed_at    TEXT,
  unsubscribed_at TEXT
);

-- One subscription per person per report (upsert target in subscribe.ts).
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_email_report ON subscribers (email, report);
-- Token lookups drive confirm / download / unsubscribe.
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_token ON subscribers (token);
-- Handy for exports / dashboards.
CREATE INDEX IF NOT EXISTS idx_subscribers_report_status ON subscribers (report, status);
