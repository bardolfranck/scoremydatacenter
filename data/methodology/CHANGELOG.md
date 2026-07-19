# Methodology changelog

Every methodology change is a version bump with a rationale and a signatory. No silent weight edits, ever. From iter-1 onward, major/minor versions require sign-off by the independent methodology council.

## ⏳ DRAFT — EN ATTENTE DE SIGNATURE (A-16) — 0.1.0 (aggregation note) — Indice SITE par pays

> **Statut : rédigé, NON signé. Prérequis de mise en prod des surfaces `/fr/indices` (brief
> 2026-07-18/19) — la PR reste non déployée tant que cette entrée n'est pas signée par Franck.**

- **Objet** : publication d'un agrégat par pays — l'« indice SITE » — calculé par le moteur au
  build (`engine/indices.py` → `indices.json` + `indices_history.json`). **Aucun changement de
  notation** : aucun poids, seuil ou indicateur ne bouge ; les notes de sites sont byte-identiques.
  L'entrée existe parce qu'un agrégat publié est un choix méthodologique opposable (A-16).
- **Règle d'agrégation** : moyenne **équipondérée** des scores SITE continus publiés du pays.
  Rationale : l'indice mesure ce que les territoires offrent ; pondérer par la puissance ferait
  parler les mégawatts (les opérateurs) et non les sites — l'agrégat pondéré MW est publié À CÔTÉ
  (`mw_weighted`) quand ≥ 5 sites du pays communiquent leur puissance, jamais à la place.
- **Périmètre énoncé** : tous les scores site publiés entrent dans la moyenne, y compris les
  sites annoncés (le score site mesure le territoire, valable à T0) ; les dénominateurs
  `n_operational` / `n_announced` sont émis et affichés en pied de carte.
- **Plancher** : n ≥ 5 sites notés, seul critère d'éligibilité (« en veille » en dessous).
  La documentation (médiane des scores doc SITE, bandes solide ≥ 0,75 / moyenne ≥ 0,5 / faible)
  accompagne toujours la lettre — règle n°1 — et ne filtre jamais.
- **Réserve A-25 héritée, dans l'agrégation** : indice ≥ 80 sans `verification_source` dans le
  pays → « B · A réservé », score réel conservé. Jamais un patch d'affichage.
- **Seuils de lettres** : la grille des fiches inchangée (A ≥ 80 · B ≥ 65 · C ≥ 50 · D ≥ 35 ·
  E < 35), désormais exposée en `grade_thresholds` au niveau racine de la méthodo.
- **Historique** : append-only, événements uniquement (changement de lettre, bascule de réserve,
  bascule d'éligibilité, nouveau pays) ; le score continu dérive dans `indices.json`, pas dans
  l'historique. Gate d'idempotence : corpus inchangé ⇒ historique byte-identique.
- Signataire : _(à signer — Franck Bardol)_.

## 0.1.0 (policy note) — 2026-07-19 — L2 power provenance: an aggregator MW is a claim, not a fact

- **Rule (memo signed Franck Bardol, 2026-07-19)**: L2 ("monster ratio", MW per 1000 inhabitants) may
  only carry `status: measured` when its power figure comes from a **regulatory register** (EED —
  e.g. the Dutch RVO disclosure, which states the INSTALLED/RATED basis). A power figure from an
  aggregator, the press or the operator itself is an unverified third-party claim whose basis
  (IT load? grid feed? full-build?) is undeclared — measured wrong 2x-13x against the RVO register
  (DCWatch's own CSV column is `power_total_mw`). Such L2 entries carry `status: announced`:
  the existing declarative cap + confidence penalty apply. No weight, threshold or indicator
  change — existing engine semantics only; version stays 0.1.0.
- **Enforcement**: Gate 9 (`engine/validate.py`) blocks a 'measured' L2 on a positively-identified
  non-regulatory figure; lenient on unattributed prose (never promoted NOR accused). Canonical tier
  definition: `pipelines/labels/power_tier.py` (adds an `operator` tier); migration:
  `scripts/migrate_l2_prudence.py`.
- **Effect on the corpus (479 DC)**: 214 L2 entries flipped to announced; **43 site letters move
  down one grade** (B 110→83, C 170→181, D 30→46) — every move recorded in the DC's public
  score_history with this rationale. The 13 letter-fragile DCs were hand-checked first: 3 sourced
  corrections applied (Colt campus 24 MW IT official — aggregator overstated 2.5x; DataOne 400 MW
  announced per primary press), 10 marked "verification attempted, no better source".
- Signatory: decision Franck Bardol (memo 2026-07-19), implemented in working session (Claude).

## 0.1.0 (metadata note) — 2026-07-15 — fill `published_at` (zero scoring change)

- `published_at: null → "2026-07-14"` — the freeze date. The git tag `v0.1.0` remains the primary
  timestamped proof of anteriority (as stated in the FREEZE entry); this fills the schema field so
  the published grid carries its own date, matching the site's "public, versioned and dated" claim.
  No weight, threshold, indicator or version change; grades are byte-identical.
- Signatory: metadata completion on Franck Bardol's instruction (2026-07-15), working session (Claude).

## 0.1.0 — 2026-07-14 — FREEZE

The grid is frozen exactly as calibrated through draft revisions (a)-(i) — **zero scoring change in this entry**: every grade in the corpus is byte-identical before and after the freeze (only version strings move). What the freeze changes is the standing of the grid:

- **`version` drops the `-draft` suffix**; the file becomes `v0.1.0.json` (Gate 5 anteriority: one active version, tagged in git — the tag is the timestamped proof of anteriority).
- **`calibration_status` flips to `calibrated` on 23/24 indicators**, retro-validated against the 311-DC corpus (FR 257, CH 54, BE 2) with the 4 CI anchors green (E-anchor and D-anchor hard assertions among them). **L1 stays `provisional` by construction**: `direction: non_monotonic` cannot claim `calibrated` (schema rule) — its sense is deliberately carried by the ethical lock (`vulnerability_cannot_improve_score`), not by curve fitting; this is a feature of the freeze, not an omission.
- **`parameters.provisional` -> `false`.** Placeholder rationales ("PROVISIONAL — to be calibrated…") are re-stamped "Calibrated at the v0.1.0 freeze"; nuanced calibration notes (WRI severity note, Uptime ranges pending citable reference, tier-3 out-of-MVP rows E5/W5) are kept verbatim as history — they document known limits, and honest limits are part of an opposable method.
- **Known reconciliations carried into v0.1.x**: the 22/24-vs-21 MVP legend discrepancy (initial draft note) reads 22 in MVP since F5 entered (f); beta's rounding-boundary pin (30.0 = E) holds and is re-pinned by the golden snapshot at this freeze.
- **Effect on gates**: the A-27 nominative-ranking gate's freeze condition is now met (its second condition, the D/E contradictoire, is wired since A-26); Gate 5 stops treating the corpus as scored against a draft.
- Signatory: **frozen on Franck Bardol's instruction (« gèle v0.1.0 », 2026-07-14)**; prepared in working session (Claude).

## 0.1.0-draft (i) — 2026-07-11 — the A is reserved: it is proven, never granted by data (A-25)

Surfaced by the EU expansion: very favorable foreign sites (clean-ish grid, no water stress, artificialized land, no Seveso, far from Natura) crossed the site A threshold (≥80) — the FR corpus had only ever reached B, so the "no A" property held by accident, not by construction. An A on the badge that a journalist screenshots reads as "proven excellent", which A-25 forbids: **A = exploitation vérifiée seulement**.

- **New parameter `reserve_A_for_verified: true`** + engine rule (`_reserve_top_grade`): a grade (site OR project/process) that scores A is published one rung down at **B** with `reserved_from: "A"`, UNLESS the DC carries third-party operational verification (any indicator with `verification_source` — the same A-25 unlock signal that flips `announced → measured`). The real score is kept intact; the badge is meant to read "B · A réservé — se prouve en exploitation" (a stated published rule, not a hidden number/letter contradiction). The day an operator proves its operations, the A unlocks by itself.
- **Effect**: no DC in the current corpus (all spatial base facts, zero operator verification) can show A. The one residual site A (nl-northc-rotterdam-zestienhoven, 89.2) becomes B·réservé.
- Sanity: FR corpus unchanged (never reached A), calibration anchors (E/D) untouched, golden zz fixtures unchanged (alpha B, beta E), all gates green.
- ⚠️ **Front-end follow-up (Franck to sign off the wording)**: the badge/fiche must render the `reserved_from` reason ("A réservé, se prouve en exploitation") next to the B so the kept score and the letter never read as a contradiction.
- Signatory: prepared in working session (Claude, for review by Franck Bardol), applying the already-validated A-25 doctrine.

## 0.1.0-draft (h) — 2026-07-09 — calibration iter-2: base thresholds learn to say E

Applied against the pinned 32-DC French corpus (`score_corpus.py`); every move justified, all still `calibration_status: provisional` pending the freeze. Corpus site distribution moves from **6 B / 26 C** (compressed, unable to express A/D/E) to **7 B / 17 C / 7 D / 1 E**; the E-anchor (farmland hyperscaler) reaches its retrospective target and its CI anchor is promoted from `xfail` to a hard assertion.

- **F2 `agricultural` 25 → 0 — a category fix, not tuning**: agricultural land IS part of ENAF (Espaces Naturels, Agricoles et Forestiers); scoring it above `natural_or_enaf` (0) contradicted the ZAN referential this basis cites.
- **F1 .30 → .20 / F2 .25 → .35** — REX 2026-07-07 lesson 5: F1 only sees *designated* zones (Natura 2000/ZNIEFF) and is blind to ordinary plain biodiversity; F2 carries ordinary-habitat destruction. Land pillar still sums to 1.0.
- **E1 .30 → .15 / E2 .25 → .35 / E3 .20 → .25** — E1 (grid carbon) has zero intra-FR variance (one national RTE figure): at .30 it granted every French DC 7.5 free points and masked local grid saturation, the actual siting constraint (Caparéseau S3REnR). E1 regains prominence with per-country bases at internationalization.
- **W1 `high` 30 → 20** — WRI Aqueduct "high" (40–80% baseline withdrawal) is a severe class; 30/100 was generous for siting new load there.
- **Data, not methodology**: L2 (MW per 1000 inhabitants — the cadrage's "monster ratio", base tier-1) computed for the two known-power corpus DCs from INSEE population; it was `missing` corpus-wide despite being deterministic. The corpus fill lives in the private newsroom.
- Sanity held: transparency-floor property test, ethical lock (gate 3) and all gates green; fictional fixtures re-pinned (alpha B 77.7; beta E 30.0 — the rounding-boundary case to be re-pinned at freeze) and golden snapshot regenerated.
- Signatory: calibration iter-2, prepared in working session (Claude, for review by Franck Bardol); to be confirmed or amended by the corpus-order review before the v0.1.0 freeze.

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
