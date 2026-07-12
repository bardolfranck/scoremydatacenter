# Multi-country spatial pipeline — architecture, status, gotchas, per-country TODO

The reference for scaling `pipelines/spatial` across countries **without re-hitting the same
walls**. Read this before adding a country. Companion to [`README.md`](./README.md) (the original
FR pipeline) and [`RECON.md`](./RECON.md) (the FR source feasibility study).

**One rule above all (Franck, 2026-07-11): think COMMON.** What is shared lives once; a country
contributes a *declarative spec* plus only its genuine national quirks. No per-country copy of the
skeleton, no `compute-fr.py` / `compute-de.py` drift. And there is **one way to run** — the wrong
ways fail loudly (see [`../WORKFLOW.md`](../WORKFLOW.md)).

---

## 1. The layers (what is common, once)

| File | Role — shared by every country |
|------|-------------------------------|
| `country.py` | **THE skeleton** — `build_draft(spec, …)`: collector loop, block-aware padding, fragment + provenance assembly, the CLI (`run_cli`). One copy, no drift. |
| `bands.py` | **Canonical value→category mappings** — E2/E3 MW & fill bands, WFD status classes, F1 distance rings, Corine→soil, Seveso `l3_value`. Cross-country comparability *by construction*; national modules import these, never redefine them. |
| `geo.py` | **Generic access** — ArcGIS REST (point query / identify), OGC WFS + OGC API Features (pygeoapi), `laea3035` (pan-EU INSPIRE grid projection, stdlib), `min_vertex_km` (axis-order-tolerant). |
| `eu.py` | **EU-level collectors any country gets free** — `collect_e1_energy_charts` (Fraunhofer energy-charts, all ENTSO-E), `collect_w2_universal` (EEA WISE spatial resolver + status join), `natura_rings` (EEA Natura 2000), `corine_at_point` (Corine CLC2018). |
| `eu_member.py` | **The anti-clone factory** — `make_eu_member_spec(iso, e1=, natura=)`. A full EU/EEA member with no national quirk IS this spec + its ISO code. |
| `registry.py` | **ONE ISO→spec map.** `batch.py` and the orchestrator resolve a country here. Adding a country = add one line here (+ its spec file). |

A **spec** is a plain dict (see `country.py` docstring): `iso`, `generator`, `summary`,
`fetch_commune`, `identity_fields`, `collectors` (list of `((ids…), fn)`), `collectable_gaps`,
`provenance_commune`, `provenance_extra`, `manual_still_required`.

---

## 2. How to add a country (the decision tree)

```
Is it in the EU/EEA data commons (WISE + Natura + Corine + ENTSO-E)?
│
├─ YES, no national quirk ─────────▶ eu_member.py factory, ONE line:
│                                     XX_SPEC = make_eu_member_spec("XX")
│                                     (PL, SE, FI — 4/12: E1+W2+F1+F2)
│
├─ YES, but one deviation ─────────▶ factory with a flag:
│    • energy-charts 500s on it      make_eu_member_spec("IE", e1=False)   → 3/12
│    • outside Natura 2000           make_eu_member_spec("NO", natura=False) → 3/12
│
├─ Has RICHER national sources ────▶ hand-written spec (own file), reuse eu.py where a national
│    (worth wiring)                   source is missing:
│                                     • FR collect.py (10/12), BE be/ (regional ×3), NL nl.py,
│                                       LU lu.py, DE de.py (EU-level v0), GB gb.py (Brexit)
│
└─ NOT in the commons (US, …) ─────▶ WATCHLIST, not a score (cadrage A-19): sourced facts, no
                                      grade. See ../press + calibration/watchlist/. Deep scoring
                                      only if a federal adapter is explicitly commissioned.
```

Then, **always the same three steps** (one way to run):

```bash
# 1. collect (registry-dispatched batch — the ONE path)
make collect-country COUNTRY=XX SITES=sites-xx.csv OUT=../smdc-newsroom/calibration/datacenters-xx

# 2. promote the reviewed drafts to scored records (loader ignores .draft.json)
for f in ../smdc-newsroom/calibration/datacenters-xx/*.draft.json; do
  cp "$f" "${f%.draft.json}.json"; done
rm ../smdc-newsroom/calibration/datacenters-xx/*.draft.json

# 3. rebuild the served artifacts (NEVER `make score` when the newsroom is next door — it refuses)
make prod-artifacts
```

`load_datacenters` globs `datacenters*` panels automatically — a new `datacenters-xx/` folder is
picked up with **zero code change** to the build path.

---

## 3. Country status matrix (2026-07-12)

Coverage = tier-1 indicators auto-filled (of 12). All spatial-only → project/process is
`insufficient_data`; no grade shows A without operational proof (A-25 reservation).

| ISO | Kind | Cov. | E1 (carbon) | W2 (water) | F1 (nature) | F2 (land) | Other national | Notes |
|-----|------|------|-------------|-----------|-------------|-----------|----------------|-------|
| **FR** | national (own) | **10/12** | RTE eCO2mix | Sandre+WISE | API Carto INPN | PLU/RPG+Corine | E2/E3 Caparéseau, W1 VigiEau, W3 BNPE, L1 Filosofi, L3 Géorisques | the reference build |
| **BE** | regional ×3 (own) | ~8/12 | Elia ods192 | SPW MESU+WISE | SPW/EEA | plan de secteur/Corine | L3 SPW+Mercator Seveso | Wallonia proven; Flanders W2/zoning partial; Brussels stub |
| **NL** | national (own) | ~6/12 | energy-charts | PDOK KRW+WISE (fallback) | EEA | Corine | **E2+E3 capaciteitskaart** (richer than Caparéseau), L3 PDOK Seveso, L1 CBS (raw) | |
| **LU** | national (own) | ~4/12 | energy-charts | geoportail+WISE | EEA | PAG national | L3 INSPIRE GML | one keyless OGC-API endpoint serves W2+F2 |
| **DE** | EU-level v0 (own) | **4/12** | energy-charts (~381) | WISE universal | EEA | Corine | — | the 16-Länder deep build is the TODO |
| **PL** | factory | 4/12 | energy-charts (**~652**) | WISE universal | EEA | Corine | — | energy angle (dirtiest EU grid) |
| **IE** | factory `e1=False` | 3/12 | — (energy-charts 500) | WISE universal | EEA | Corine | — | grid CAPACITY is the story (EirGrid, deep) |
| **GB** | national (own) | 2/12 | **carbonintensity.org.uk** (~106) | — (Brexit) | — (Brexit) | Corine (pre-Brexit) | — | Brexit ejected UK from the EU commons |
| **SE** | factory | 4/12 | energy-charts (**~23**) | WISE universal | EEA | Corine | — | clean-grid end (hydro+nuclear) |
| **FI** | factory | ~3/12 | energy-charts (~64) | WISE universal (patchy) | EEA | Corine | — | lake-dense → W2 buffer misses |
| **NO** | factory `natura=False` | 3/12 | energy-charts (~30) | WISE universal | — (Emerald) | Corine | — | EEA-not-EU: Emerald Network ≠ Natura |
| **US** | **watchlist only** | — | — | — | — | — | — | A-19: presence + Data Center Watch partnership, no score |

---

## 4. Gotchas — the walls we already hit (don't hit them again)

1. **Grid carbon is volatile → 12-month MEAN, never a snapshot.** BE swings 60–250 gCO2/kWh
   intraday; a snapshot is a lottery. `collect_e1_energy_charts` averages a year.
2. **Memoize E1 per country.** National carbon is identical for every DC in a country; the
   year-long fetch (~35k points) is cached per `(country, window)` — else a batch rate-limits
   itself (was silently dropping E1 on ~30% of sites before the memo).
3. **energy-charts does not serve every zone.** Ireland returns HTTP 500 (`ie`); the US is not in
   it at all. Use `e1=False` (factory) or a national feed (GB carbonintensity.org.uk).
4. **`collect_w2_universal` is nearest-within-buffer** (rivers are lines). It misses points on a
   polder or dense-urban block off any water body (NL Middenmeer, several FI/SE points). A national
   **point-in-polygon** source is preferable where one exists; wire it first and keep the universal
   resolver as the fallback (pattern in `nl.py`/`lu.py`: `national() or eu.collect_w2_universal()`).
5. **Brexit removed the UK from the EU commons.** WISE has ZERO GB water bodies for the 2022 WFD
   cycle; Natura is EU-only (UK = national site network). Only Corine survives (CLC2018 predates
   Brexit). A UK deep build is *national* (EA/SEPA/NRW, JNCC, HSE) — like DE's Länder but whole-country.
6. **WFS axis order bites.** Flanders serves EPSG:4326 as (lat,lon) or Lambert 72; some services
   emit [lon,lat] vs [lat,lon]. `geo.min_vertex_km` tries both against a Europe plausibility window.
7. **Seveso tier is often absent in INSPIRE-thin exports.** `bands.l3_value` returns **None** for
   an unknown-tier site *inside 2 km* (band undecidable) — we never guess a hazard class. Beyond
   2 km the tier can't change the band, so unknown is safe.
8. **L1 income never transposes.** FR bands are Filosofi €/consumption-unit; every country's income
   definition differs (Statbel per-declaration, CBS per-household, LUSTAT salaries…). Raw value
   goes to provenance only; the **bands are a methodology-lead decision**, not a code default.
9. **One way to rebuild.** `make score` / `engine.score` **refuses** when the newsroom is checked
   out next door (it would wipe the served corpus + watchlist to the zz fixtures). Use
   `make prod-artifacts`. `SMDC_PUBLIC_FIXTURES=1` is the explicit override. (See `../WORKFLOW.md`.)
10. **Promotion step.** The loader ignores `*.draft.json` (they're proposals). A collected draft
    must be copied to `<id>.json` to be scored — the human-review gate, materialized.
11. **Methodology schema is `additionalProperties:false`.** A new parameter (e.g. the A-reservation
    flag) must be added to `data/schema/methodology.schema.json` too, or every gate fails.
12. **Golden snapshot** covers the public zz fixtures only. A methodology/artifact-shape change
    regenerates it (`SMDC_PUBLIC_FIXTURES=1 … build_artifacts(out_dir='engine/tests/golden')`);
    zz has no A, so the A-reservation left it byte-stable.
13. **US federal endpoints are flaky.** NLCD (land cover) responds; eGRID and PAD-US ArcGIS
    services 404/500 on the obvious URLs — a US scored adapter is real work, not a cheap ride.

---

## 5. Per-country TODO to deepen (v1 national adapters)

Ordered roughly by value. Each lifts a country from presence toward decisional scoring.

- **DE — the big one.** 16 Länder for W2 (per-Land WFS water-body code), F2 (Gewestplan/zoning),
  L3 (Land Seveso registers), W1, W3, L1 (DESTATIS/Regionalatlas per Kreis); E2/E3 per-TSO
  (50Hertz/Amprion/TenneT/TransnetBW). E1 already done. Biggest market, biggest build.
- **IE — grid capacity is THE story.** Wire EirGrid/SEMO for E1 + **E2/E3** (the Dublin moratorium
  = halted connections). CSO income, COMAH Seveso. This is where Ireland becomes decisional.
- **GB — national build (Brexit tax).** EA/SEPA/NRW catchment data for W2, JNCC SAC/SPA for F1,
  NGED/UKPN capacity for E2/E3, HSE COMAH for L3, ONS income for L1.
- **BE — finish the regions.** W1 (network-trace the Aquawal/RTBF drought widget), W2 Flanders
  (VMM/DOV code layer), F2 Flanders (Gewestplan), Flanders NIS join, Brussels stub, governance ×3.
- **NL — keyed sources.** Legal zoning (ruimtelijke plannen API, needs a free key), W1 (KNMI
  neerslagtekort, keyed), W3 abstraction volumes, L1 bands.
- **PL — the energy angle is enough for v0.** To deepen: PSE grid capacity, GUS income, national
  Seveso (ZDR/ZZR), W1.
- **LU — small gaps.** W1 (Aquawal), W3 volumes, L1 (LUSTAT salaries → bands).
- **SE / FI / NO — national capacity + income + Seveso.** For NO specifically: the **Emerald
  Network** protected-areas layer (Bern Convention) to replace the missing Natura F1.
- **US — decision pending.** Either a federal adapter (eGRID E1 → point-in-subregion, NLCD F2,
  PAD-US F1) *if* deep US scoring is commissioned, or stay watchlist + a Data Center Watch data
  partnership (A-19, the cadrage default).

## 6. Cross-cutting TODO (not per-country)

- **L1 income bands** per country — a methodology-lead arbitrage (raw values already in provenance).
- **E2/E3 grid-capacity bands** calibration — currently the FR provisional cutoffs reused
  everywhere; NL uses an availability *class* (1–3) mapped onto them, a documented approximation.
- **Governance (T1/T2)** per country — the deepest layer (per-region legal systems). BE recon
  mapped it (CNDP→RIP/openbaar onderzoek, CE vs RvVb…); never auto-scored (A-19 doctrine).
- **Front — map default view fits the scored corpus (Europe)**, so the US watchlist markers sit
  off-screen west; and the map popup still shows `null MW` when power isn't disclosed (should read
  "puissance non communiquée", as the leaderboard already does).
