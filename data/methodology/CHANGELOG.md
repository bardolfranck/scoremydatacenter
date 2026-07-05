# Methodology changelog

Every methodology change is a version bump with a rationale and a signatory. No silent weight edits, ever. From iter-1 onward, major/minor versions require sign-off by the independent methodology council.

## 0.1.0-draft (c) — 2026-07-05 — scoring parameters + engine semantics

- New PROVISIONAL parameters (engine bring-up, phase 1b): `declarative_confidence_penalty` 0.5, `confidence_thresholds` {high 0.75, medium 0.45}, `borderline_margin` 3 points.
- Missing-data semantics fixed by the transparency floor: a missing **base** datum (public fact — our collection gap) is excluded and renormalized, reported through confidence (cause `missing_data`); a missing **project/process** datum (operator disclosure) **counts as 0** — hiding can never beat disclosing. `insufficient_data` replaces the project/process letter below 40% weighted coverage; a pillar with zero known indicators is not graded.
- Letters are graded on the **rounded published score** (one decimal): the public number and the public letter can never contradict each other.
- Signatory: draft amendment prepared in working session (Claude Code); all values to be calibrated in phase 5.

## 0.1.0-draft (b) — 2026-07-05 — direction contract (blind-spot fix)

- `direction` is now a mandatory, schema-enforced declaration of each indicator's scoring sense: `lower_is_better` / `higher_is_better` / `encoded_in_scoring` (ordering fully carried by category/rubric scores) / `non_monotonic` (sense unsettled — requires a `calibration_note` and cannot claim `calibrated`). The old `not_applicable` escape hatch is removed.
- `calibration_status` (`provisional` | `calibrated`) replaces the `provisional` boolean on every indicator; the v0.1.0 freeze = flipping all to `calibrated`.
- `constraints` (closed enum — an unknown constraint fails validation instead of silently no-oping).
- **L1 (socio-economic profile)**: `non_monotonic` + constraint `vulnerability_cannot_improve_score` — partly an ethical choice, not empirical: retrospective calibration must never learn "fragile municipality = better grade" (ethical lock, framing note §9). Retro-validation does not settle this alone; the constraint caps it.
- **T1 / CNDP referral**: settled by definition, not by tuning — a CNDP referral is a process signal (neutral-to-positive, never a red flag); controversy is already captured by L6, so scoring it negatively would double-count. Phase-5 calibration must include a T1×L6 collinearity check.
- Working rule: an ambiguous indicator is never a question to the founder — it is `direction: non_monotonic` + `calibration_note` in this file. A missing field IS the blind spot: add the field, don't ask.
- Signatory: draft amendment prepared in working session (Claude Code) upon methodology-lead review (COWORK, 2026-07-05).

## 0.1.0-draft — 2026-07-05

- Initial draft: 24 indicators across 5 pillars (energy 25%, water 20%, land & biodiversity 20%, local impact 20%, transparency & governance 15%), per the v2 indicator grid.
- Dual-score structure: `base` block (site score) vs `project`/`process` blocks (project/process score).
- T1 (consent/governance) is a factualized judgment: procedural proxy rubric only, no verdict — relocated tier 3 → 2.
- E5, W5, F5 marked out of MVP scope (tier 3). Note: the v2 grid legend says 22/24 in MVP but marks these 3 rows out (→ 21) — discrepancy to be reconciled at the v0.1.0 freeze.
- **All weights, thresholds, category scores and parameters are PROVISIONAL** (marked `provisional: true` / `PROVISIONAL` rationales): structural placeholders so the engine can be built. They will be calibrated during the retrospective validation sprint (plan phase 5, ~5 known-outcome cases) and purged before the v0.1.0 freeze.
- Signatory: draft prepared in working session (Claude Code); to be signed by Franck Bardol at the v0.1.0 freeze.
