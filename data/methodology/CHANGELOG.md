# Methodology changelog

Every methodology change is a version bump with a rationale and a signatory. No silent weight edits, ever. From iter-1 onward, major/minor versions require sign-off by the independent methodology council.

## 0.1.0-draft (g) — 2026-07-09 — `not_collected` vs `missing`: an E of non-extraction is as false as an A of complacency (RED FLAG fix)

- **New indicator status `not_collected`** (schema + engine), distinct from `missing`. `missing` = we READ the public dossier and the commitment is absent → on project/process it scores a hard **0** (verified opacity; hiding never beats disclosing). `not_collected` = **nobody has looked yet** → it is **excluded** from the substantive score (never a 0) and instead **lowers coverage**, pushing project/process toward `insufficient_data`. Root cause fixed: the old single `missing` conflated "not looked" with "verified absent", so an un-harvested project block was branded operator opacity (Fouju came out `E` on project/process with its ICPE dossier fully online but unread by us).
- **Engine — new "did we even look?" guard**: a project/process grade may not rest on governance alone. If no project-block indicator has been looked at (all `not_collected`), the operator has not been examined → `insufficient_data`, never a transparency-floor letter drawn from indicators nobody read. Confidence counts `not_collected` as a data gap (cause `missing_data`), like `missing`.
- **Pipelines** now emit `not_collected` by default for uncovered project/process indicators (base stays `missing` — a base gap is our collection gap, excluded & renormalized, unchanged).
- **Gate 8 (CI)** makes the incoherent state impossible by construction (philosophy A-18): (a) once **T2 attests a public dossier**, a project indicator may be `missing` (an opacity accusation) only with a **read-trace source** — otherwise mark it `not_collected` until harvested; (b) `not_collected` is a draft-only state and **blocks publication**. Schema updated: `missing` may now carry a read-trace source; `not_collected` carries no value/proxies/source.
- No weight, threshold or pillar change — scoring *semantics* only. The zz corpus grades are byte-identical (alpha's F5 gains a read-trace source; its grade is unchanged); the frozen calibration corpus had 315 un-harvested project/process indicators re-labelled `missing → not_collected`, sending Fouju back to `insufficient_data` until its dossier is extracted.
- Rationale & signatory: **decision Franck Bardol, 2026-07-09** — « un E de non-extraction est aussi faux qu'un A de complaisance ». Implemented in working session (Claude Code).

## 0.1.0-draft (f) — 2026-07-09 — F5 (heat recovery / ERC) enters the MVP (calibration iter-1)

- **F5 `mvp: false → true`.** Heat recovery / avoid-reduce-offset measures now score inside the `land_biodiversity` pillar (project block). Trigger: the calibration sprint needs a high anchor, and heat recovery is the single most decisive positive an operator can disclose — keeping it out of MVP made an "A" structurally unreachable. Direction (`encoded_in_scoring`) and normalization (categorical: `heat_recovery_and_erc` 100 / `partial` 50 / `none` 0) are unchanged; the pillar's MVP weights still sum to 1.0 (F1 .30 / F2 .25 / F3 .20 / F4 .15 / F5 .10), so the engine's renormalize-on-present rule needs no edit.
- **`threshold_basis` promoted from `editorial_choice` (PROVISIONAL) to `reference`: ISO/IEC 30134-6 — Energy Reuse Factor (ERF)**, the international standard for data-center waste-heat reuse. The category cut-offs stay `calibration_status: provisional` (to be tuned in phase 5), but the *sense* of the axis is now anchored to a real referential, not to an editorial choice.
- **E5 and W5 unchanged** (still `mvp: false`, tier 3) — this reconciles one of the three out-of-MVP rows flagged at the initial draft (F5 in, E5/W5 deferred), not all three.
- Retrospective calibration anchors posed in CI (`engine/tests/test_calibration_anchors.py`, `xfail(strict=True)`): E-anchor site=E and A-anchor project_process∈{A,B} — both UNMET today (site grid collapses onto B/C; retrospective governance unsourceable), tracked as targets that flip CI red the day calibration reaches them. Live nominative sources pinned in the private newsroom corpus (A-11).
- Version string stays `0.1.0-draft` (draft revisions are tracked as lettered entries here, per this changelog's convention); no weight was silently edited.
- Signatory: calibration sprint iter-1, prepared in working session (Claude Code) for Franck Bardol; category thresholds to be signed at the v0.1.0 freeze.

## 0.1.0-draft (e) — 2026-07-09 — W5 label disambiguation (no scoring change)

- **W5 label renamed**: « WUE mesuré / source d'eau réelle » → « WUE constaté / source d'eau (auto-déclarés) » (en: "Observed WUE / water source (self-reported)"). The old label conflated two independent axes of the schema: `status` (measured vs announced — is the figure actual or promised?) and `nature` (public_fact vs declarative — who produces it?). An operator's observed WUE is *actual* yet *self-reported*: real, but unverifiable without a third party. The new label carries both. Description updated accordingly.
- No weight, threshold, direction or MVP change — labels only.
- Signatory: decision Franck Bardol (working session 2026-07-09, calibration sprint prep), implemented by Claude.

## 0.1.0-draft (d) — 2026-07-05 — methodology-lead review verdicts (COWORK)

- **Points 1-3 validated as-is** (base/pp transparency-floor asymmetry, pillar-weight renormalization, provisional parameters). Noted: the declarative cap and the confidence penalty are NOT a double count — the cap acts on the substantive score, the penalty on the confidence: the two axes of the dual display.
- **New invariant (schema-enforced)**: a `base` indicator can never be declarative (`block: base` ⇒ `nature: public_fact`) — otherwise the renormalize-on-missing rule would become a loophole in the transparency floor.
- **`close_to` removed** (was: asymmetric "close to better grade" gloss). Systematically flattering the operator dents perceived independence; the one-decimal published score already shows boundary proximity. The letter and the number, no editorial gloss. Parameter `borderline_margin` dropped.
- **`insufficient_data` cascades to pillar sub-scores**: a pillar below the coverage floor is never given a punitive letter drawn from unknowns (displaying "local impact: E" while saying "not enough data to grade the operator" was contradictory and attackable). Parameter renamed `min_coverage_project_process` → `min_coverage` (applies to the global project/process grade and to every pillar display sub-score; each graded pillar now publishes its coverage).
- **Ethical lock made executable**: constrained indicators declare a `vulnerability_order` (least → most vulnerable); gate 3 rejects any grid where a more vulnerable category scores higher, and a corpus property test enforces d(site_score)/d(vulnerability) ≤ 0 (same pattern as the transparency floor). L1: `["strong_fit", "neutral", "sensitive"]`.
- Confidence raw score clamped at 0 (defensive).
- Signatory: methodology-lead review (COWORK) relayed by Franck Bardol, implemented in working session (Claude Code).

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
