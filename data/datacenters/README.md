# Published data centers

One JSON file per **published** data center (`{iso2}-{slug}.json`), ODbL-licensed.

- Files contain raw sourced indicator values only — computed scores never live here (the engine produces them at build time).
- A file enters this directory **only** at `publication.status: published`, i.e. after the contradictory-review period (operator notified ≥ 15 days, response published alongside).
- Development fixtures use the fictional `zz-` prefix.

Schema: `../schema/datacenter.schema.json` (phase 1).

> **Note for other sessions — "only `zz-` here" is the publication gate, not the pipeline's maturity.**
> The collection pipeline (spatial + governance/voie A + contestation/voie B + orchestrator + reviewer)
> has been validated end-to-end on **~30 real French data centers** as a **local dev panel** — source
> drafts in scratch, artifacts in the git-ignored `site/public/data/`, **never committed, never
> deployed**. This directory stays `zz-`-only by design (A-11): a real nominative DC enters only at
> `publication.status: published`, after the contradictory-review period. So don't re-run the `zz-`
> exploration or the voie-A/B build — they exist and are tested. Full chronology: cadrage
> `PLAN.md` (top) + `JOURNAL.md`.
