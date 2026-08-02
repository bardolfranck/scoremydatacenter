# RECON — Israel (IL): tier-1 source feasibility (probed live 2026-07-27)

**Question (Franck):** "no commons → watchlist" was shorthand — does Israel actually lack data?
**Answer: no.** Israel has some of the best open data outside the EU commons — but behind ONE
structural gotcha, and with real gaps on the spatial layers. A national adapter is plausible at
**~4-5/12 cheap, ~6-8/12 with a deeper dig** — better than the US (flaky endpoints), comparable
or better than post-Brexit GB. Doctrine unchanged: watchlist (A-19) until a scored IL adapter is
commissioned or a hot case justifies it; this recon de-risks that day.

## The structural gotcha (hit live, twice)

**data.gov.il is a real CKAN and its API answers cleanly — but the direct file downloads are
behind a JS anti-bot challenge** (obfuscated script wall; same class as the inquiry-register
Cloudflare wall in the FR recon). The bypass is standard and clean: **the CKAN DataStore API**
(`/api/3/action/datastore_search?resource_id=…`) serves the same rows as JSON, keyless. Rule for
any future IL collector: *always the DataStore API, never the download URL.* Noga (the grid
operator) 403s plain HTTP too — its data path likely needs a headless fetcher or a key.

## Feasibility matrix (every verdict = a live probe, not a doc promise)

| Ind. | Source probed | Verdict |
|------|---------------|---------|
| **E1** (grid carbon) | Ember yearly dataset — keyless public CSV (HTTP 200); Electricity Maps `IL` (401 keyed); Noga real-time (403) | **OPEN (yearly national)** via Ember — same "global keyless brick" class as W1; real-time needs a key/headless → not needed for a base score |
| **E2/E3** (grid capacity) | Noga ISO site | **WALL** (403 anti-bot). No open hosting-capacity feed found. Like IE/DE: the capacity story exists (state just doubled power-plant targets) but the feed is closed — deep probe or manual |
| **W1** (water stress) | WRI Aqueduct at Modi'in (31.90, 35.01) | **OPEN** — `zre_or_crisis` ('Extremely High >80%'). ⚠️ Publish with the honest caveat: Israel is the world leader in desalination — the raw basin referential overstates the *effective* constraint; state the referential, note the limit (the §7.3 discipline) |
| **W2/W3** (status / abstraction) | Water Authority datasets not found as API on CKAN | **MANUAL/DEEP** — likely portal+PDF territory |
| **F1** (protected areas) | CKAN "שמורות טבע" dataset — DataStore OK but **geometry stripped** (5 rows, Shape_Area only); govmap ArcGIS REST not found at the obvious endpoints (404) | **EXISTS, NOT YET SPATIAL** — the INPA layers live in govmap; a deeper probe of govmap's real ArcGIS/API is the single highest-value next step |
| **F2** (land cover) | no Corine (IL outside EEA39) | gap — a GLOBAL fallback brick (ESA WorldCover) would serve IL *and* every future non-EU country; methodology-lead call |
| **L1** (socio-eco) | CKAN DataStore `אשכול כלכלי חברתי` | **OPEN, EXCELLENT** — official CBS socio-economic cluster (ESHKOL 1–10) for **995 localities**, with CBS locality code + English names, keyless JSON. Better structured than several EU members. Bands = methodology-lead (never code) |
| **L2** (MW/pop) | CKAN locality datasets (9 hits incl. monthly locality-level population) | **LIKELY OPEN** (DataStore) — join on the same locality code as L1 |
| **L3** (hazard sites) | CKAN "חומרים מסוכנים" → 0 datasets | **GAP on CKAN** — Ministry of Env. Protection runs a separate portal; probe or manual |
| **T1/T2** | — | never auto-scored (A-19 doctrine); note the contestation profile is atypical: labor/international (Nimbus employee protests) more than local-siting |

## What this changes

- **Nothing today** (doctrine holds): watchlist. The 2026 IL wave (Nvidia mega-campus north,
  ~$1.5bn Ashdod, Nebius national supercomputer) belongs on the watchlist like the Maghreb lot —
  with the W1-desalination caveat wording and (context) the state's doubled power-plant targets.
- **The day an IL adapter is commissioned**: it is a RIDE, not a wall — E1 (Ember) + W1 + L1 + L2
  by pure keyless HTTP (~4-5/12), then govmap/INPA spatial dig for F1 (+L3, W2) toward 6-8/12.
  Estimated at days, not the 20-40-day worst case — the CKAN DataStore does the heavy lifting.
- **One reusable idea beyond IL**: Ember yearly carbon + ESA WorldCover land cover are *global
  keyless bricks* (the W1-Aqueduct class) — each one added to `eu.py`-equivalent-for-world would
  lift EVERY non-EU watchlist country at once. Methodology-lead arbitrage before wiring.

## Probe log (2026-07-27)

CKAN `package_search` 200 (44+ datasets on generic query) · direct resource download → JS
challenge wall (twice) · `datastore_search` → clean JSON (L1 995 rows sampled; F1 5 rows,
no geometry) · Electricity Maps IL → 401 keyed · Ember API → keyed, but public CSV bucket → 200 ·
Noga → 403 · govmap `ags.govmap.gov.il`/`open.govmap.gov.il` guesses → 404/HTML · Aqueduct
Modi'in → Extremely High.


## Addendum — deep dig + adapter build (2026-08-02, GO Franck « je veux voir des notes »)

The sub-agent dig resolved what the first recon left open; `il.py` is LIVE (registry `IL`):

- **Backbone (FR-grade)**: local-authority jurisdiction polygons on AGOL
  (`GvulotShputRashuyotVaadim`, point-in-polygon, `CR_LAMAS` = CBS symbol) + CKAN population
  join; nearest CBS settlement point only as a FLAGGED fallback. Gotcha caught live: the
  nearest-point heuristic picked Bareqet (2 154 hab.) for a DC administratively in Shoham
  (24 996) — nearest-point is NOT an administrative fact, hence polygon-first.
- **F1**: INPA reserves/parks national layer via a public AGOL mirror (1 427 polygons; every
  official state GIS backend is WAF/geo-fenced) — documented secondary provenance, Natura-ring
  logic reused as-is.
- **L1**: the CBS 2021 socio-economic index is SPATIALLY PUBLISHED (`SOEC_Rashut_2021`:
  CLUSTER_2021/2019 + INDEX_VALUE + RANK, keyed by the same CBS symbol) — raw to provenance.
  Gotcha: the welfare-ministry aschkol dataset uses a DIFFERENT authority numbering (Shoham
  379 vs CBS 1304) — never join across those registries.
- **L3 path confirmed open** (MoEP CKAN registry, 25 758 geolocated sites, ITM/EPSG:2039 —
  needs reprojection, next iteration). **Noga wall re-confirmed** (WAF + geo-fence, no
  data.gov.il fallback; Electricity Maps dropped its IL parser too).
- **Pilot run (7 sites, seeds/sites-il.csv)**: E1/W1/F1/F2 auto-filled 7/7 from GPS alone +
  L2 deterministic where MW+population known. Site grades: 4×D (35.1), 3×E (27.4/22.9),
  documentation "low" (missing_data ≈ 0.74) — the honest picture of a gas-heavy grid
  (E1 492.69 → 0 pts) in extreme baseline water stress (W1 → 0), stated with the desalination
  caveat on every fiche. Publication remains gated by the normal machinery (A-26 contradictoire).


## Addendum 2 — panel hardening (2026-08-02, GO relayé « DÉCISIONS FRANCK 2026-08-01 »)

- **W1 × water regime, EXPORTABLE (presentation level)**: `world.apply_w1_regime` — the
  jurisdiction declares `water_supply_regime` (IL: `desal_dominant`, sourced Israel Water
  Authority / FAO AQUASTAT) and the site carries `water_source` (evidence only, default
  `undisclosed`). desal_dominant + undisclosed → the basin reading is explicitly NOT asserted
  as a site fact (caveat in the W1 source title) + a PRE-DECLARED contradictoire lever in
  provenance. **Score untouched** — moving W1=0 to "unknown" is a calibration decision
  (Franck, v0.1.0 freeze). The Gulf inherits by declaring its own regime value.
- **ITM (EPSG:2039) wired**: stdlib Transverse Mercator + an EMPIRICAL Israel-1993 datum
  correction derived against 40 CBS settlement pairs (mean offset −65.86/−40.33 m, stdev
  0.12/0.36 m, residual <1 m). Never trust "GRS80 params" alone for ITM — the datum shift is
  ~77 m.
- **L3 finding (methodology-grade)**: the MoEP toxics-permit class (רעלים, 3 947 geolocated
  sites via the validated Mifal_Key↔Mispar_Mezahe join) is FAR broader than Seveso — labs,
  cosmetics plants — and publishes NO severity tier. EVERY pilot DC has a permitted site
  within 300 m; the band-safe rule correctly refuses to guess → L3 stays `not_collected`,
  and the honest deliverable is the CONTEXT COUNT in provenance (`l3_moep_context`:
  sites within 2/5 km, stated as counts, never a hazard verdict). No Seveso-tier analogue
  exists on data.gov.il (probed). The collector lights up by itself the day a tier is published.
- **Panel: 8 sites** (+ MedOne Kfar Yona, OSM-exact building). Grades unchanged: 4×D, 4×E.
  Publication: HELD — « en veille / note en attente » (doctrine 2026-08-01), no letters, no
  contradictoire mailing until Franck's go.
