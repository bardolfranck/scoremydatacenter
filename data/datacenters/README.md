# Published data centers

One JSON file per **published** data center (`{iso2}-{slug}.json`), ODbL-licensed.

- Files contain raw sourced indicator values only — computed scores never live here (the engine produces them at build time).
- A file enters this directory **only** at `publication.status: published`, i.e. after the contradictory-review period (operator notified ≥ 15 days, response published alongside).
- Development fixtures use the fictional `zz-` prefix.

Schema: `../schema/datacenter.schema.json` (phase 1).
