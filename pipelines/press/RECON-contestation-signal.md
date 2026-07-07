# Contestation-signal recon (voie B) — press detection + structured opposition (2026-07-07)

**"North face", Time 1 — the second half.** Where voie A (`RECON.md`) collects the procedural *facts*
of contestation that **score** (T1: appeals, environmental-authority opinion, CNDP referral, public
inquiry, deliberations), voie B collects the contestation *signal* — press coverage, curated
oppositions, moratoria, petitions — that **feeds a published signal layer, never the grade**.

> **Governing decision — A-21 (see ARCHITECTURE.md).** Contestation enters the system on two strictly
> separated tracks:
> 1. **As a procedural FACT** → it scores, via T1 (voie A). Dated, opposable, un-gameable.
> 2. **As a SIGNAL** (curated oppositions, named collectives, articles, petitions) → a **published,
>    sourced layer beside the score, never a slider on the letter.** It powers the "watchlist" /
>    *En veille* layer (A-19) and annotates scored fiches with sourced facts — no grade attached.
>
> **What must NEVER score:** press volume/tone and self-reported signature counts. They are gameable
> in both directions (astroturfing for/against, suppression); letting them move the grade would break
> `vulnerability_cannot_improve_score` in reverse (an organized commune would drag its own letter down,
> an apathetic one would not) and invite defamation exposure. They drive **detection and triage only**,
> shown at most as "self-reported, unverified", never weighted. Same load-bearing rule as voie A:
> **"the press points, the registry proves."**

## Evidence tiers (what a source is allowed to do)

| Tier | Sources | Allowed use |
|------|---------|-------------|
| **Hard fact** | procedural (voie A) + **official inquiry-register observation counts** + moratoria | scores (T1) / hard context |
| **Sourced curated fact** | curated opposition maps, named collectives, moratorium datasets, matched articles | **published signal layer** (facts + coords + source), annotates fiches & watchlist — no grade |
| **Gameable / detection-only** | self-reported petition counts, raw press volume & tone | detection + triage; shown "self-reported, unverified"; **never weighted** |

## Feasibility matrix (probed live)

Legend — **API**: documented endpoint. **Scraped feed**: no REST but a stable machine-readable feed
(a map's GeoJSON layer, a page's embedded JSON). **Headless**: only a JS-executing browser reaches it.
**Partnership/PDF**: no feed; curated behind PDFs or a data agreement.

| Source | Signal | Scope | Access | Licence | Verdict |
|--------|--------|-------|--------|---------|---------|
| **GDELT DOC 2.0** (`api.gdeltproject.org/api/v2/doc/doc`) | news articles (title, url, domain, date, language, country) + intensity time series | global (EN+FR) | **API**, `artlist` confirmed 200 | free incl. **commercial** + attribution | **primary press backbone** |
| **Community uMap** (`umap.openstreetmap.fr/fr/datalayer/{mapId}/{uuid}/`) | opposition + project points, named collectives, source links | FR | **scraped feed** (GeoJSON per layer) — verified live | ⚠️ map-level licence unset / source article NC — resolve before commercial reuse | **FR opposition feed** |
| **Community fights dataset** (`datacentertracker.org/data/fights.json`, from its `app.js`) | ~1.3k US cases: project, company, status, opposition groups, outcome, sources | US | **scraped feed** (JSON) | **CC BY 4.0** | **US contestation feed** |
| **Community moratorium dataset** (public GitHub CSV) | ~220 moratoria, geocoded, legal basis, status | US | **open file** (CSV) | **CC BY 4.0** | **US moratorium feed** |
| **OSM Overpass** | data-center inventory (`man_made`/`telecom=data_center`) | global | **API** | ODbL | inventory backbone |
| **National assembly petitions** (data.gouv CSV) | official petitions + vote counts | FR | **open file** (CSV) | Open Licence 2.0 | official petition signal |
| **Senate petitions** (Decidim GraphQL) | official petitions + endorsement counts | FR | **API** (POST blocked from this egress; real) | open | official petition signal |
| **Inquiry-register observation counts** | mobilization count on a formal inquiry (hardest to fake) | FR | **headless** (Cloudflare-walled to curl) | — | strongest FR mobilization — worth a browser fetcher |
| Self-reported petition platform | signature count in page JSON (robots-permitted) | global | scraped feed | UGC | **weak/gameable — flag only** |
| National news RSS aggregator | freshest, most precise per-project articles | FR+EN | RSS | ⚠️ **non-commercial ToS** | **recon-only, never ship** |
| Boutique US research (blocked $ / group counts) | curated US flagship figures | US | **partnership / PDF** | — | data agreement, not a feed |

## Recommended v1 perimeter

**Stand up the signal layer on the open, pure-HTTP feeds (no partnership, no headless):**
- **GDELT DOC `artlist`** — the global press-detection backbone (raises a project's watchlist flag →
  human triage; never a score input). Add its intensity time series after one clean 200 confirms the
  schema on a dedicated IP.
- **Community uMap GeoJSON** (FR oppositions/projects), **fights.json** (US), **moratorium CSV** (US),
  **Overpass** (global inventory) — sourced facts into the *En veille* watchlist + fiche annotations.
- **National assembly petitions CSV** (+ Senate API) — official, attributable petition counts.

**Reserve for later:** a **headless (Playwright) fetcher** for the one hard signal curl can't reach —
official inquiry-register observation counts (the least-gameable mobilization number); and
**partnership outreach** for the boutique US research and the FR map's editor (which also resolves the
map's non-commercial licence at the source).

## Operational notes (learned in recon)

- **GDELT**: throttled ("one request / 5 s"); a shared egress IP earns a sustained 429. Production needs
  a **dedicated IP + ≥5 s pacing + exponential backoff**; for backfill use the ngrams/BigQuery datasets.
- **Query precision (project binding)**: anchor on `near20:"<operator> <commune>"` (far more
  discriminating than commune alone), scope with `sourcecountry`/`sourcelang`, add a contestation
  lexicon and negative-tone/`theme:` filters to drop tech-launch noise, then post-filter `domain`
  against a local-press allowlist and dedupe by resolved URL.
- **National news RSS** returns 0 items silently unless terms are `+`-joined with a full `hl=xx-YY`;
  usable for manual discovery only (non-commercial ToS), never as a production feed.
- **Boundary with the score**: a matched article/opposition entry raises a **flag** and creates a
  **sourced fact**, feeding the signal layer. The letter still moves only on voie-A procedural facts.

## Guardrail (unchanged, load-bearing)

The signal layer **publishes facts, it does not grade** (A-19/A-21). Every entry carries its source and
the A-20 evidence discipline (archive the page; copyrighted press is linked, never reproduced). No
press volume, tone, or self-reported count is ever weighted into a letter — that boundary is what keeps
the score un-gameable and the observatory citable. Detection is a means; the fact is the deliverable.
