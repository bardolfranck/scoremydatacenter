# Belgium tier-1 spatial adapter (v0)

Born from the EU recon probe of 2026-07-09 (two real cases: Google Saint-Ghislain, Wallonia ·
LCL Brussels-North, Flanders). Same contract as the FR pipeline: **coordinates in, sourced draft
out, zero scores, human review mandatory.**

```
python -m pipelines.spatial.be.collect --lat 50.46767 --lon 3.86446 \
    --name "Google Data Center Saint-Ghislain" --operator "Google (Crystal Computing SRL)" \
    --project-status operational --out ../smdc-newsroom/drafts/datacenters
```

## Coverage v0

| Ind | Source | Level | Status |
|-----|--------|-------|--------|
| E1 | Elia Open Data `ods192` — **12-month mean** (BE grid swings 60–250 g/kWh intraday; snapshot would be a lottery — flagged divergence from FR) | National | ✅ |
| E2 | Elia Hosting Capacity Map (no-auth xlsx, ~385 substations, load MW, 2027/0% flex) — richer than Caparéseau; FR provisional bands reused | National | ✅ |
| E3 | — no public connection queue in BE (headroom is E2's signal) | — | ❌ `missing` |
| W1 | — no machine drought feed found (Wallonia: Aquawal/RTBF widget trace pending; Flanders KiWIS needs a token) | Regional ×3 | ❌ `not_collected` |
| W2 | SPW `EAU/MESU` (code) → EEA WISE Discodata (status; same table as FR, `wise.py` parameterized) | Wallonia only | ✅ (Flanders code layer = v1) |
| W3 | SPW `EAU/CAPTAGES` has points but volumes are mostly null | Regional | ❌ `not_collected` |
| F1 | SPW `FAUNE_FLORE/NATURA2000` (Wallonia) / EEA Natura2000Sites combined layer (elsewhere), FR distance rings | Regional + EU fallback | ✅ |
| F2 | SPW plan de secteur (legal zoning, Wallonia) with Corine cross-check / Corine alone elsewhere | Regional + EU fallback | ✅ |
| L1 | Statbel fisc2023 Table D (cached, keyed by NIS) — **raw value to provenance only**: FR bands are €/consumption-unit Filosofi, not transposable; BE bands pending methodology | National | ⚠️ provenance only |
| L3 | SPW SEVESO points (Wallonia) / Mercator `pf_seveso_con` polygons (Flanders) | Regional ×2 | ✅ (Brussels = v1) |

Identity backbone: SPW `LIMITES_ADMINISTRATIVES` (NIS in Wallonia) with Nominatim fallback for
name + region routing. Flanders NIS join = v1 backlog.

**Honest score: ~6/12 auto for a Walloon point, ~5/12 for a Flemish one** (FR: 10/12). The gaps
are carried in every provenance sidecar (`known_gaps`), not silently dropped.

## v1 backlog

- W1 Wallonia: network-trace the Aquawal/RTBF drought widget ("no API" is not "manual").
- W2/F2 Flanders: locate the VMM surface-water-body layer and the Gewestplan zoning WFS.
- Flanders NIS from Statbel statistical-sectors geojson (cache brick exists).
- Brussels: stub or probe (few DC sites).
- L1: BE income bands (methodology-lead decision — see `recon-voie-EU` note, section 3).
- Governance (T1/T2): per-region adapters — RIP/Canopea (Wallonia), omgevingsloket (Flanders),
  openpermits (Brussels), CE + DBRC case law. Iter-1 press pipeline, never auto-scored.
