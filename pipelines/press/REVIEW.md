# watchlist-reviewer — turning 965 raw drafts into a validated publish queue

The review of harvested contestation drafts (voie B) is a **procedure**, so it is automated in two
layers with a human as the last gate. It never publishes on its own (A-07 / A-15).

## Layer 1 — deterministic scaffold (`review.py`)

Reads `watchlist.draft.geojson` and, per entry, does the mechanical steps:

1. **Reduce** the rich harvester record to the **light published shape** (A-19 refinement): identity
   + entry-level `source` + `facts[]` (contestation shape, empty for a bare announced project).
2. **Flag** mechanically: `missing_coords`, `geoloc_out_of_country` (national bbox), `no_name`,
   `no_source_url`, `license_nc_umap` (NC upstream), `self_reported_count` (weak/gameable — kept as a
   flagged fact, never a score).
3. **Route**: a hard flag → `human`; otherwise → `agent` (needs source-verification + a neutral
   `{fr, en}` label). Every row carries `auto_published: false`.

Output: `watchlist.review.jsonl` (one proposal/line) + `_review_flags.md`. Stdlib only.

```
python -m pipelines.press.review <newsroom>/drafts/watchlist/watchlist.draft.geojson
```

Observed on a 965-entry corpus: **962 → agent, 3 → human** (hard geoloc flags); flags surfaced 122 NC
licences (all FR uMap) and 231 self-reported counts to tag. So the human's immediate hand-work is the
3 hard cases, not 965.

## Layer 2 — LLM reviewer (the sub-agent that verifies)

For each `agent`-routed proposal, an LLM reviewer with web access does the judgment steps a script
cannot:

- **Verify the source** — open the URL, confirm it supports the claim; report
  `source_supports: yes|partial|no|unreachable` with a one-line evidence quote.
- **Write the neutral label** `{fr, en}` — state the fact, never a verdict (pre-mortem R2). No
  adjectives of approval/disapproval.
- **"The press points, the registry proves"** — if the source is a community map, an activist
  aggregator, or the raw dataset itself, flag it and name a **stronger primary source** to fetch
  (local press, prefecture/city ordinance, court record).
- Keep `kind`/`self_reported` accurate; a self-reported count stays flagged, never hard evidence.

Its output is a reviewed proposal (`route: ready_for_human | needs_more_work`, `auto_published:
false`). It writes nothing and publishes nothing.

## Layer 3 — human validation (the last gate, non-negotiable)

A person approves/edits/rejects the queue — heavily on `human`-routed and `needs_more_work` items, a
spot-check on the rest — then promotes accepted entries (adding `archived_url` at publish, A-20). This
is the A-07 mandatory human-validation gate: nominative facts about real projects never reach the
public layer on a machine's say-so.

## Reusability

The same pipeline serves all three cases: the initial **965 backfill**, the recurring **delta** of new
harvest, and the **per-DC** contestation facts folded into a scored fiche's `contestation[]`.
