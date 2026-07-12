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
| **L1** income | national | DESTATIS Regionalatlas ArcGIS hosts don't resolve; GENESIS REST API needs a **free registration key**; BBSR INKAR = downloadable CSV (cache-brick candidate, if the export URL is pinned) | ⚠️ gated/keyed; INKAR is the open path if wanted |

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

1. **Keep DE at the EU-level 4/12.** No open source moves a grade in our corpus; the grid data (the
   value) simply isn't public.
2. **The per-Land router is proven buildable** (F2 ALKIS keyless in all 6 states) — build it only if
   finer land use is wanted later; it won't change urban-DC grades.
3. **W1 is available if the project accepts an `h5py` dependency** (a deliberate break of the
   stdlib-pure rule) — worth it only when drought becomes a scored pillar input.
4. **L1 via INKAR CSV** (cache-brick) is the one clean-ish coverage gain, pending the pinned export URL.

The honest headline: **Germany's open geodata caps deep scoring; its decisional indicator (grid
capacity) is closed.** A deep DE build is a keyed/dependency/self-host project, not an open-data ride.
