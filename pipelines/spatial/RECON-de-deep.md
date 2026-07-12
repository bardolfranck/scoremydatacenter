# Germany deep-adapter recon (2026-07-12) — what the 16 Länder actually expose

Live-probed source map behind a possible deep DE adapter (beyond the EU-level v0 = E1 energy-charts
+ W2 WISE + F1 Natura + F2 Corine = 4/12). **Read this before re-probing Germany** — it cost ~240k
subagent tokens across 4 parallel recon agents. Test points = our 10 DE DCs' states: Hessen
(Frankfurt), Bayern (München), NRW (Düsseldorf), Berlin, Hamburg, Niedersachsen (Hannover).

## Verdict in one line

**A deep DE adapter changes no grade in our corpus from open data.** The indicators that would make
Germany *decisional* — grid capacity E2/E3, Seveso L3 — are locked or absent; the reachable ones are
either dependency-blocked (W1), gated (W3, L1) or precision-only over already-filled F2 (ALKIS).

## Per-indicator findings (all live-probed)

| Ind | Level | Best source (verified live) | Verdict for our corpus |
|-----|-------|------------------------------|------------------------|
| **E1** carbon | national | Fraunhofer energy-charts (~381 g/kWh) — **have it** | ✅ filled |
| **W2** water status | EU | EEA WISE universal resolver — **have it** | ✅ filled |
| **F1** protected | EU | EEA Natura 2000 — **have it** | ✅ filled |
| **F2** land | national + per-Land | **CLC5** national keyless (`sgx.geodatenzentrum.de/wms_clc5_2018`, attr `clc18`) OR per-Land **ALKIS "tatsächliche Nutzung"** (all 6 states keyless, verified) | ✅ filled by Corine; ALKIS is finer (140 vs 44 classes) but returns the **same "artificialized"** for urban DC sites → **+0 grade change** |
| **E2/E3** grid capacity/queue | per-TSO | 50Hertz / Amprion / TenneT DE / TransnetBW — **no unified open feed** (unlike the Dutch capaciteitskaart) | ❌ **locked** — this is the real siting constraint, and it's the one with no open data |
| **L3** Seveso | per-Land | **No national register.** Only **Sachsen** (`luis.sachsen.de/…/betriebsbereiche_wfs`, attr `PFLICHTEN` = untere/obere Klasse, 165 sites) is clean; Hamburg partial (no tier). Hessen = anonymized **zones only** (no name/tier); RLP/BASF = nothing. EU eSPIRS register is **access-restricted**. | ❌ **dead for our states** (none in Sachsen) |
| **W1** drought | national | **UFZ Dürremonitor** — daily national netCDF SMI grid (`files.ufz.de/~drought/SM_Lall_daily_n14.nc`). Real values: Frankfurt SMI 0.17 (moderate), München 0.0096 (exceptional). | ⚠️ **works but needs `h5py`** → breaks the stdlib-pure rule for one marginal indicator (drought isn't the siting driver). Deferred. |
| **W3** withdrawals | national/Kreis | DESTATIS/regionalstatistik.de EVAS 32211 — per-Kreis exists but **login-gated**, triennial (2022), public-supply only | ❌ gated + stale → skip |
| **L1** income | national | ✅ **CLEAN keyless endpoint found**: DESTATIS Regionalatlas indicator AI1601 (disposable household income per capita per Kreis, EUR) via IT.NRW's ArcGIS `www.gis-idmz.nrw.de/arcgis/rest/services/stba/regionalatlas/MapServer/identify` + a dynamic join. Point-query, no key. Frankfurt **25 394 €**, München **35 467 €** (2022). | ✅ wireable as **raw-to-provenance** (per doctrine, German income bands are a methodology decision — same as BE/NL) → **+0 grade change** but real German income in provenance |

## Endpoints worth keeping (for a future keyed/dependency build)

- **F2 per-Land ALKIS Nutzung** (keyless, verified): NRW `wfs.nrw.de/geobasis/wfs_nw_alkis_vereinfacht`
  (`ave:Nutzung`), Hessen `gds.hessen.de/wfs2/aaa-suite/cgi-bin/alkis/vereinf/wfs`, Niedersachsen
  `opendata.lgln.niedersachsen.de/doorman/noauth/alkis_wfs_einfach`, Berlin `gdi.berlin.de/services/wfs/alkis`,
  Hamburg `geodienste.hamburg.de/HH_WFS_INSPIRE_ALKIS`, Bayern `geoservices.bayern.de/od/wms/alkis/v1/tn`
  (WMS-GFI). Per-state field schemas differ → a declarative field-map per Bundesland, not freestyle.
- **L3 Sachsen** (clean, tier-carrying): `luis.sachsen.de/arcgis/services/luft/betriebsbereiche_wfs/MapServer/WFSServer`
  — the model for what a good Seveso WFS looks like; expand as other Länder publish.
- **W1 UFZ** daily grid: `files.ufz.de/~drought/SM_Lall_daily_n14.nc` (total soil), `SM_L02_daily_n14.nc`
  (topsoil). EPSG:31468, variable `SMI` ∈ [0,1], nearest-cell sample. Needs h5py/xarray.
- **LBM-DE native** (finer than CLC5, land use + sealing %) is **key-gated** on WMS / download-only
  Open Data GeoPackage — self-host only.

## Recommendation

**What is genuinely wireable from open data, keyless, today:**
1. **L1 income** — the Regionalatlas AI1601 endpoint above (national, keyless, point-query). Wire as
   raw-to-provenance like BE/NL (German bands are a methodology decision). Real German income in the
   sidecar; no grade change until bands exist.
2. **F2 per-Land ALKIS** router (all 6 DC states keyless, verified). Finer land use than Corine, but
   returns the same "artificialized" for urban DC sites → no grade change. Build only if finer land
   use is wanted; needs a per-state field-map (declarative spec per Bundesland).

**What is NOT open:**
3. **E2/E3 grid capacity — LOCKED** (4 TSOs, no unified feed). This is the decisional indicator, and
   it has no open data. Deep DE cannot be decisional without it.
4. **L3 Seveso** — no national register; only Sachsen (none of our DC states).
5. **W1 drought** — works but needs `h5py` (breaks stdlib-pure); drought isn't a siting driver.
6. **W3 withdrawals** — login-gated, triennial.

The honest headline: **no open source changes a single grade in our corpus.** The one decisional
indicator (grid capacity) is closed; the reachable ones (L1, F2-ALKIS) are provenance/precision only.
A deep DE build wires real sources but is grade-neutral today — worth doing for the provenance depth
and to prove the 16-Länder router, not for the leaderboard. Keep DE at 4/12 for scoring; enrich the
provenance (L1) if desired.
