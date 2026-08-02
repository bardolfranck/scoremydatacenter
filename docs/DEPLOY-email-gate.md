<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Deploy runbook — report email-gate (Big Tech / Banks / …)

The lead-magnet download: visitor gives an email → double opt-in → gated PDF.
Front page = `src/components/ReportDownload.astro` (thin pages under
`src/pages/reports/…` + `src/pages/fr/rapports/…`). Backend = Pages Functions in
`site/functions/api/report/` (`subscribe`, `confirm`, `download`, `unsubscribe`)
reading the registry `site/functions/_shared/reports.ts`.

## Bindings the Functions expect
| Binding            | Type   | Purpose                                   |
|--------------------|--------|-------------------------------------------|
| `DB`               | D1     | `subscribers` table (the email store)     |
| `REPORTS_BUCKET`   | R2     | the report PDFs                           |
| `RESEND_API_KEY`   | Secret | Resend sending key (already set by Franck)|

## One-time setup (run from `site/`)

1. **Create the D1 database** and note the `database_id` it prints:
   ```bash
   npx wrangler d1 create smdc-leads
   ```
2. **Apply the schema** (remote = the real prod DB):
   ```bash
   npx wrangler d1 execute smdc-leads --file=functions/schema.sql --remote
   ```
3. **Create the R2 bucket** (or reuse an existing one; then set `REPORTS_BUCKET` to it):
   ```bash
   npx wrangler r2 bucket create smdc-reports
   ```
4. **Upload the PDFs** under the exact keys in `reports.ts`
   (source: `8-library-docs-a-produire/`):
   ```bash
   npx wrangler r2 object put smdc-reports/reports/big-tech/ScoreMyDataCenter-BigTech-2026-FR-FIGE.pdf \
     --file="<path>/ScoreMyDataCenter-BigTech-2026-FR-FIGE.pdf"
   npx wrangler r2 object put smdc-reports/reports/big-tech/ScoreMyDataCenter-BigTech-2026-EN-V1.pdf \
     --file="<path>/ScoreMyDataCenter-BigTech-2026-EN-V1.pdf"
   # …and the Banks pair when that report goes live.
   ```
5. **Bind them to the Pages project** — dashboard → Workers & Pages →
   `scoremydatacenter` → **Settings → Functions → Bindings** (Production):
   - D1 database binding: variable `DB` → database `smdc-leads`
   - R2 bucket binding: variable `REPORTS_BUCKET` → bucket `smdc-reports`
   - Confirm the **`RESEND_API_KEY`** secret is present on **Production**.

## Deploy
`make deploy` (local, as always). Confirm wrangler reports the compiled
Functions (`Compiled Worker … /functions`). Functions are picked up from
`site/functions/` (CWD = `site`).

## Smoke test (prod)
1. Open `/fr/rapports/big-tech`, submit a real address → "vérifie ta boîte mail".
2. Inbox: confirmation mail from `no-reply@send.scoremydatacenter.org`.
3. Click → PDF downloads. Re-open the same link → still downloads (confirmed).
4. `npx wrangler d1 execute smdc-leads --command="SELECT email,report,status,created_at FROM subscribers ORDER BY id DESC LIMIT 5" --remote`
5. Unsubscribe link → row flips to `unsubscribed`.

## Export the list (Franck, anytime)
```bash
npx wrangler d1 execute smdc-leads --remote \
  --command="SELECT email,report,lang,status,created_at,confirmed_at FROM subscribers WHERE status='confirmed'" --json > leads.json
```
(or the D1 console in the Cloudflare dashboard — the store is yours, fully readable/exportable.)

## Add a new report later
1. Add an entry to `reports.ts` (slug, titles, R2 keys, filenames, `gated`).
2. Add thin pages `src/pages/reports/<slug>.astro` + `src/pages/fr/rapports/<slug>.astro`.
3. Upload its PDFs to R2 under the keys named in the entry. Done — same gate.
