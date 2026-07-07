# Tier-1 spatial pipeline — source feasibility recon (2026-07-07)

**Phase 4 bis, Temps 1.** Before writing the pipeline, each public source behind the 12
tier-1 indicators was probed live from a real GPS point (rural Seine-et-Marne,
`48.5990, 2.8060`, commune Champeaux `77082`).

> **Principle (revised after review): "no API" is not "manual".** A source without a REST API
> almost always still exposes its data — a web map *has* to fetch its markers from somewhere, so
> we intercept the same feed it loads (Caparéseau, below, was cracked exactly this way). And where
> the exact indicator genuinely isn't published, we substitute a **correlated proxy** (the way one
> reads the S&P 500 off the Dow when the direct print is unavailable) rather than sending a human
> to type it. Manual entry is the last resort, not the default. The three tiers below are now
> **API / scraped-feed / proxy**, and only what resists all three stays manual.

**Backbone that makes everything else cheap:** `geo.api.gouv.fr/communes?lat&lon` reverse-geocodes
coordinates alone into `{commune, INSEE code, population, surface, département, région}` in one
call. Every collector below keys off it. Probed ✅.

## Feasibility matrix

Legend — **Clean**: one documented API, coords in → value out, no key.
**Partial**: API exists but the value needs derivation/aggregation that is editorial or multi-call.
**Manual**: no usable API; interactive map or file downloads only.

| Ind | Indicator | Source(s) | Probe result | Verdict |
|-----|-----------|-----------|--------------|---------|
| **E1** | Grid carbon intensity | RTE eCO2mix (ODRÉ `eco2mix-national-tr`, field `taux_co2`) | ✅ real-time g/kWh returned | **Clean** — national value (France grid is national); caveat recorded in provenance |
| **E2** | Grid connection capacity | RTE Caparéseau / S3REnR | ✅ **cracked** — the Leaflet map loads a per-region substation JSON (`/medias/{uuid}`) with WGS84 coords + `values.RTE_CDR` (available MW). Discover the rotating UUID from the region page, take the nearest poste | **Scraped feed** |
| **E3** | Grid congestion / queue | RTE Caparéseau / S3REnR | ✅ **cracked** — same feed, `values.INFO_TX` (reserved-capacity fill rate %). No API, but a clean file, not manual | **Scraped feed** |
| **W1** | Local water stress | VigiEau `api/zones?lat&lon` (Propluvia restrictions) | ✅ `niveauGravite` (e.g. `alerte_renforcee`) + arrêté PDF | **Clean** |
| **W2** | Water body status | Sandre WFS + EEA WISE | ✅ **automated** — Sandre WFS (2022 layer VRAP2022) resolves the water-body code at the point; EEA **WISE** Discodata SQL API returns all ~11 400 French water bodies' WFD ecological status (2022 cycle) in one cached query, joined by code. Bypasses the slow per-agence ArcGIS servers entirely: every country reports the same figures to the EEA, exposed via one national API | **API + cached reference** |
| **W3** | Basin withdrawal pressure | BNPE / Hub'Eau `prelevements/chroniques` | ✅ **automated** — commune annual withdrawal volume summed by `code_commune_insee`; provisional pressure band, raw Mm³ kept in the source | **Computed proxy** |
| **F1** | Protected-area overlap / distance | API Carto IGN `nature` (Natura 2000 habitat+oiseaux, ZNIEFF 1/2) | ✅ point & buffered-polygon queries work; empty = no overlap | **Clean** (buffer rings for distance) |
| **F2** | Soil status | API Carto IGN (PLU/RPG) + Corine Land Cover | ✅ PLU zoning / RPG parcel as primary; **Corine Land Cover 2018** (wall-to-wall, IGN Géoplateforme WFS, point-in-polygon) as no-gap fallback where PLU/RPG are silent **and** as an independent cross-check — observed cover vs. legal zoning; any disagreement is flagged in provenance (`f2_crosscheck`) | **Clean + cross-checked** |
| **F3** | Ecological corridors (TVB) | SRADDET / INPN | ⚠️ TVB is per-region SRADDET layers, no unified national API | **Partial → deferred** |
| **L1** | Municipality socio-economic profile | INSEE Filosofi (cached) | ✅ **automated** — median disposable income per commune, from the open Filosofi CSV cached once and joined by INSEE code (with Paris/Lyon/Marseille arrondissement back-fill). Provisional income bands, raw €/UC in the source | **Cached reference** |
| **L2** | Absorption capacity | INSEE (via `geo.api.gouv.fr`) | ⚠️ municipality side (population, surface) automated; the ratio needs the **project's** size (power/footprint) as input, and the ratio definition is still `PROVISIONAL` | **Partial** |
| **L3** | Technological hazard / Seveso | Géorisques `api/v1/installations_classees?latlon&rayon` | ✅ `statutSeveso` + per-site coords → distance bands, fully deterministic | **Clean** |

## Recommended v1 perimeter

**Automated now (10 indicators + identity backbone), all from coordinates alone:**
- API: `E1` (eCO2mix), `W1` (VigiEau), `W3` (BNPE), `F1` (API Carto nature),
  `F2` (API Carto GPU/RPG), `L3` (Géorisques).
- Scraped feed: `E2`, `E3` (Caparéseau substation JSON — see `capareseau.py`).
- Cached reference: `L1` (INSEE Filosofi commune income; `cache.py`), `W2` (EEA WISE WFD status
  joined by water-body code; `wise.py`).
- Identity: `geo.api.gouv.fr` (municipality, INSEE, département, region, population, surface).

All map directly onto the methodology's units/categories, so the pipeline emits a *sourced value*,
not a guess. The E2/E3/W3/L1 category thresholds are provisional (methodology owns final
calibration); the raw MW / fill-% / Mm³ / €/UC / WFD-class is carried in each source title so the
mapping stays auditable.

**The two that remain — and why they aren't sourcing:**
- `L2` absorption capacity — municipality side already automated; needs the project's own
  power/footprint as input (which the operator/press announces) — a form field, not sourcing.
- `F3` corridors (TVB) — per-region SRADDET layers; a per-region stitch like Caparéseau.
- `T1`/`T2` — governance proxies for the iter-1 `press/` LLM pipeline, not this one.

**Note on W2** — the lesson of "no clean national API" was itself wrong: France's per-agence
ArcGIS servers are slow/unreliable, but every country reports the same DCE figures to the **EEA**,
whose WISE database exposes them through one public SQL API (Discodata). Going up a level to the
European aggregator beat stitching six national platforms. The `cache.py` brick (download-once,
join-by-code) powers both `L1` and `W2`.

**Genuinely manual (for now):** the two **judgment** proxies `T1`/`T2` (consultation, appeals,
env-authority opinion) — these live in permitting files and council deliberations, and are the
job of the iter-1 `press/` LLM pipeline with a human-validation queue, not the spatial one.

**Honest headline:** **10 of 12** tier-1 indicators auto-fill from coordinates today (5 → 8 with
Caparéseau/E2/E3/W3, → 9 with L1's cached Filosofi join, → 10 with W2 via EEA WISE). Only `L2`
(needs one project input) and `F3` + the governance proxies `T1`/`T2` (iter-1 LLM stage) remain.
The 30-minute manual KPI is beaten — cold run ≈ a few seconds, and the batch runner scales it to a
whole corpus in one command.

## Guardrail (unchanged, load-bearing)

The pipeline **proposes, it never publishes.** Output = draft fragments in `smdc-newsroom`
(private), every value carrying its source, **zero notes/scores**. An out-of-range API value read
wrong is exactly as dangerous as a hallucination — human review before a fragment enters the
circuit is mandatory. The engine still computes all scores from the reviewed file at build time.
