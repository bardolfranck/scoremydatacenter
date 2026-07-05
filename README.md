# ScoreMyDataCenter

**Independent observatory scoring the social acceptability of data center projects — public A–E grades, Nutri-Score style, France first.**

Every published score is reproducible from this repository:

```
git clone <this repo>
make score
```

The engine, the methodology, the published data and the audit log are open. What we sell is convenience (simulation, monitoring, API at scale) — **the paywall never falls on the truth**: a project's grade and its justification are always public and free.

## Repository layout

| Path | Contents | License |
|---|---|---|
| `engine/` | Scoring engine (validation, normalization, dual grading, confidence, audit artifacts) | AGPL-3.0 |
| `pipelines/` | Open data parsers (tier-1 spatial queries, from iter-0.5) | AGPL-3.0 |
| `data/datacenters/` | One JSON file per **published** data center | ODbL |
| `data/methodology/` | Versioned, tagged scoring grid (weights, thresholds, references) | CC BY-SA 4.0 |
| `data/schema/` | JSON Schema contracts for all data files | AGPL-3.0 |
| `site/` | Static site (Astro, EN + FR) — scoremydatacenter.org | code AGPL-3.0, content CC BY-SA 4.0 |

## How scoring works

- 24 indicators, 5 pillars (energy, water, land & biodiversity, local impact, transparency & governance).
- Dual grade: **site score** (context the project endures) and **project/process score** (choices the operator makes).
- A grade is never displayed without its **documentation confidence** level.
- `announced` data is never merged with `measured` data; opacity can never improve a grade.
- Every score revision carries a public rationale (see the audit log).

Scores are computed **at build time** by `engine/` from the JSON files in `data/` and the pinned methodology version. Nothing is computed at runtime; hand-editing a score is structurally impossible.

## Publication workflow

Named data centers enter this repository **only after** a contradictory-review period (operator notified ≥ 15 days before publication, response published alongside the score). Drafts live in a separate private repository until then. CI gates block any file that violates these rules.

## Contributing

Data corrections are welcome and always free (issues/PRs with a mandatory source and a declaration of interest). Contribution templates and full guidelines arrive before the repository goes public. Validation is governed: maintainer review is mandatory, and anti-poisoning checks apply — their principle is public, their exact thresholds are not.

## Status

Pre-launch scaffold (iter-0, phase 0). No real data center is scored yet; development uses fictional `zz-*` fixtures only.

## Licensing

- Code (`engine/`, `pipelines/`, `site/` code, schemas): [AGPL-3.0](LICENSE)
- Published data (`data/datacenters/`): [ODbL 1.0](data/LICENSE)
- Methodology and editorial content (`data/methodology/`, site content): [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

Founded by Franck Bardol · [scoremydatacenter.org](https://scoremydatacenter.org)
