# Pipeline workflow — the orchestrated flow with one human gate (A-22)

Runbook for whoever operates or maintains the collection pipeline. The individual bricks (spatial,
governance/voie-A, signal/voie-B, reviewer) are documented in their own `RECON*.md`/`REVIEW.md`;
this file is how they **chain**. Orchestrator: `pipelines/orchestrate.py`.

**One rule above all:** everything upstream auto-chains, there is **exactly one human gate**, and
**nothing downstream publishes without it** (A-07). The gate is the legal armour, not a slowdown.

---

## Flow A — onboard a data center to score

```
coords ─▶ [1 spatial] ─▶ [2 governance/voie A] ─▶ [3 contestation match/voie B] ─▶ [4 review]
                                                                                        │
                                              ┌─────────────────────────────────────────┘
                                              ▼
                                   🚦 HUMAN GATE  ─▶ [5 promote] ─▶ (contradictoire 15 j) ─▶ publish PR
```

One command:
```
make onboard-dc LAT=48.5878 LON=2.7628 NAME="…" OPERATOR="…" POWER_MW=1400 \
     SIGNAL=../smdc-newsroom/drafts/watchlist/watchlist.draft.geojson
# → python -m pipelines.orchestrate onboard --lat … --lon … --signal …
```

| Step | Module | In → Out | Guardrail at this edge |
|------|--------|----------|------------------------|
| 1 spatial | `pipelines.spatial.collect` | coords → `<id>.draft.json` (10/12 tier-1 indicators, sourced) + provenance | values only, never a score; unreachable source → `missing`, never fabricated |
| 2 governance | `pipelines.press.collect` | coords → `<id>.governance.json` (deterministic `cndp_referral` + judged `legal_appeals_count`; the 3 judgment proxies as **review leads**) | proposes; the leads need a human/LLM to read the PDF (A-07) |
| 3 contestation | `orchestrate.match_contestation` | coords + a harvested `watchlist.draft.geojson` → contestation entries within `--radius-km` (default 25) of the DC, reduced to the light shape | facts only, no grade; needs a prior `refresh` (else empty — logged, not fabricated) |
| 4 review | `pipelines.press.review` | contestation candidates → `contestation.review.jsonl` + `review.html` | `auto_published: false`; hard flags → `route: human` |
| 🚦 gate | **human** | see below | the one manual point — nothing proceeds without it |
| 5 promote | `orchestrate.promote_contestation` | approved queue → `contestation[]` entries + `archived_url` | only `decision: approve` applied; **silence ≠ consent** |

Output of steps 1–4 = a **bundle** in the private newsroom: `<newsroom>/drafts/datacenters/<id>/`
containing `<id>.draft.json`, `<id>.provenance.json`, `<id>.governance.json`,
`contestation.review.jsonl`, `review.html`.

---

## Flow B — refresh the contestation signal (periodic)

```
open feeds ─▶ [harvest] ─▶ [review] ─▶ 🚦 HUMAN GATE ─▶ [promote watchlist]
```
```
make refresh-signal SIGNAL_OUT=../smdc-newsroom/drafts/watchlist
# add GDELT_QUERY='datacenter (opposition OR moratorium)' for press detection
```
Harvests the four open feeds (uMap FR · US fights · US moratoria · GDELT), builds the review queue
(`watchlist.review.jsonl` + `watchlist.review.html`), stops at the gate. Re-runs review only the
**delta** in practice (dedupe already collapses the corpus). This is what step 3 of Flow A matches
against, so run it before onboarding a corpus.

---

## 🚦 The human gate — how to operate it

Primary mechanism = **the JSONL is the decision file**. Each line is a review item; you add a
`"decision"` field:

- `"approve"` — publish this fact as-is.
- `"edit"` then fix the `proposed` object in place (neutral `{fr,en}` label, correct `kind`,
  swap a weak source for a stronger primary one — "the press points, the registry proves"), then
  set `"approve"`.
- `"reject"` — drop it. Anything with **no `decision`** is held: silence is never consent.

Best-effort visual aid = **`review.html`** (static, no server): open it to eyeball a DC's few
contestation points — proposed label, source (live + archived) links, flags, route. It is a
**viewer**; the authoritative decision still lands in the JSONL.

For a scored DC you ALSO complete `T1` here: the governance sidecar pre-filled `cndp_referral` and
the judged appeals count; you fill the three judgment proxies (public inquiry, env-authority opinion,
council deliberations) from the sidecar's `review_leads` (open the PDF, record the enum fact — no
verdict, pre-mortem R2).

**In the same gesture, harvest the 5 project-block indicators from that dossier** (RED FLAG fix,
2026-07-09). The pipeline emits them as `not_collected` — the honest "nobody looked yet" state, which
keeps project/process at `insufficient_data` and **blocks publication** (Gate 8b). While the dossier
is open under your eyes, resolve each one:

| Indicator | Read from the dossier | Encode as |
|---|---|---|
| **E4** PUE target · **W4** cooling / water strategy · **F5** heat recovery / ERC · **L4**, **L5** local commitments | the operator's stated commitment | `announced` + value + full source (title, URL, accessed, **`archived_url`** — official doc, régime A-20) |
| any of the above genuinely **absent** from the dossier | you searched, no commitment | `missing` + a **read-trace source** (proves you looked — Gate 8a; the 0 is now earned) |

Never leave a project indicator `not_collected` on a DC you intend to publish, and never mark one
`missing` (an opacity accusation) without the read-trace: **an E of non-extraction is as false as an A
of complacency.** (A stage-2 LLM extractor will pre-fill this table from the dossier later; for now it
is the gate's checklist.)

Then:
```
make promote REVIEW=<newsroom>/drafts/datacenters/<id>/contestation.review.jsonl
```
`promote` applies only the `approve` rows, strips internal flags, and adds `archived_url` to each
source (best-effort Internet Archive capture — if a source is a raw API/JSON endpoint the snapshot
may be declined; swap to a press/registry URL, which archives cleanly). **This is still not a public
publish** — the public repo only receives a DC by the contradictoire PR at `status: published` (A-11).

---

## Stage 3 — synthesis redaction (post-scoring, automated, orthogonal to country)

The one narrative on each fiche (`synthesis`: two sides, `site` and `project_process`) is **not written
by hand** — it is a batch phase that runs **after the engine scores**, reads each DC's own measured
indicators + normalised scores, and delegates only the prose to the model. Built to scale to 10k DCs.

```
make score                                            # engine produces grades + normalised scores
python -m pipelines.synthesize --source <newsroom>/calibration/datacenters --artifacts site/public/data
# repeat --source per country panel (datacenters-be, …) — nothing here is country-specific
```

| In → Out | Guardrail at this edge |
|----------|------------------------|
| scored artifact `dc/<id>.json` + source DC → `synthesis` written back onto the **source** | model call is a **seam** (`llm=`); never hard-wires a vendor |
| deterministic prompt from measured `base`/`process` signals only | describes the **real value/score**, never a per-country assumption (grid at 9 vs 147 gCO₂/kWh) |
| every draft validated **before** it lands | **Gate 7** (no A–E letter in prose, reuses `engine.artifacts.synthesis_grade_citations`) + editorial bans; invalid → retried, then refused |
| `project_process == insufficient_data` → fixed honest block | no model call; "données insuffisantes", coherent with the withheld grade |
| already-synthesised DC skipped unless `--force` | idempotent — safe to re-run over the whole corpus |

The rules (grounding, two-axis, Gate 7, bans, fixed insufficient block) are one document:
`<newsroom>/calibration/SYNTHESIS-GENERATION.md`. `pipelines/synthesize.py` is its executable form.
The letter stays in the badge; the prose carries the *why*, for every country panel opened next.

---

## Guardrails carried end to end

- **No score anywhere in the pipeline.** Only the engine, at build, from the reviewed DC file.
- **Facts only in the signal** (A-21); a test fails the build if `grade`/`letter`/`score`/`confidence`
  appears in a signal/queue artifact.
- **Propose, never publish** (A-07): every artifact is a draft in the private newsroom; the public
  repo is untouched until the human PR.
- **Press is linked, never reproduced; evidence is archived** (A-20).
- **Nominative output stays private**; the orchestrator code is de-nominalized (public data-source
  endpoints only — no operator/project/collective names).

## Run it end to end on a fictional DC (recipe for a successor)

```
# 1. seed a signal to match against (or point --signal at an existing harvest)
python -m pipelines.orchestrate refresh --out /tmp/wl
# 2. onboard a fictional zz- DC (real coords, TEST identity)
python -m pipelines.orchestrate onboard --lat 48.59 --lon 2.80 --name "zz Test" \
    --operator TEST --power-mw 30 --signal /tmp/wl/watchlist.review.jsonl --out /tmp/onb
#    (note: onboard matches a *.geojson; use a harvested watchlist.draft.geojson as --signal)
# 3. edit /tmp/onb/<id>/contestation.review.jsonl — set "decision":"approve" on the good ones
# 4. python -m pipelines.orchestrate promote /tmp/onb/<id>/contestation.review.jsonl
```
Verified live: onboarding real coordinates produced a full bundle (tier-1 + governance + contestation
candidates matched within 25 km + `review.html`); `promote` applied only the approved entry and held
the rest. Offline tests: `engine/tests/test_orchestrate.py`.

## Reusability

The same orchestrator serves the initial backfill, the recurring signal delta, and each new scored
DC's `contestation[]`. Adding a DC is one command to the gate, then one `promote` — never a manual
step-by-step.
