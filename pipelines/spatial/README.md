# `pipelines/spatial` — tier-1 collection from coordinates (iter-0.5, v1)

Coordinates in → a **sourced draft** datacenter fragment out. The pipeline **proposes, it does
not publish**: output goes to `smdc-newsroom` (private) as a draft, every value carries its
source, and no score or note is ever written. A human reviews before anything enters the circuit.

> **Multi-country (11 countries + US watchlist).** This file documents the original FR pipeline.
> For the country architecture (shared skeleton + `eu_member` factory + national specs), the
> **how-to-add-a-country decision tree**, the status matrix and the gotchas/TODO per country, see
> **[`COUNTRIES.md`](./COUNTRIES.md)** — read it before adding a country.

See [`RECON.md`](./RECON.md) for the source-by-source feasibility study behind the v1 perimeter.

## What it fills (v1)

Ten tier-1 indicators map onto public sources with no editorial step, so the pipeline emits a
*sourced value* for each — plus the whole identity block:

| Indicator | Source | How | Output |
|-----------|--------|-----|--------|
| **E1** grid carbon intensity | RTE eCO2mix (ODRÉ) | API | gCO2/kWh (national) |
| **W1** water stress | VigiEau / Propluvia | API | restriction category |
| **W2** water body status | Sandre WFS + EEA WISE | API + cached | WFD status class |
| **W3** withdrawal pressure | Hub'Eau BNPE | API | pressure band (Mm³/yr) |
| **F1** protected areas | INPN via IGN API Carto | API | overlap / distance ring |
| **F2** soil status | IGN API Carto (PLU/RPG) + Corine Land Cover | API + cross-check | soil category |
| **L3** technological hazard | Géorisques | API | Seveso distance category |
| **E2** grid connection capacity | RTE Caparéseau | scraped feed | available-MW category |
| **E3** grid congestion | RTE Caparéseau | scraped feed | fill-rate category |
| **L1** socio-economic profile | INSEE Filosofi | cached reference | income band (€/UC) |

Caparéseau has no REST API, but its map loads a per-region substation JSON — the collector reads
that same feed (`capareseau.py`), discovering the rotating media UUID from the region page. "No
API" was never "no data".

`F2` uses two independent sources: the PLU zoning / RPG parcel (legal vocation) as primary, and
**Corine Land Cover 2018** (observed, wall-to-wall) as both a no-gap fallback where PLU/RPG are
silent and a cross-check. When both are present they're compared: agreement raises confidence, and
a disagreement (e.g. an "agricultural" zone already built over) is flagged in the provenance
side-car (`f2_crosscheck`) for the reviewer — not hidden.

Two indicators use the **cache brick** (`cache.py`, download-once + join-by-code):
- `L1` — the INSEE Filosofi commune income CSV, joined by INSEE code (Paris/Lyon/Marseille
  arrondissement back-fill).
- `W2` — France's per-agence DCE servers are slow/unreliable, so the collector goes up a level to
  the **EEA WISE** database (`wise.py`): one Discodata SQL query returns every French water body's
  WFD ecological status (2022 cycle), joined by the code Sandre's WFS resolves at the point.

Cached files live in `.cache/` (git-ignored). The remaining `F3`, `L2`, `T1`, `T2` are padded as
`status: "missing"`: `L2` needs the project's own power as an input, and `T1`/`T2` are governance
proxies for the iter-1 LLM pipeline, not this one.

## Run

```bash
python -m pipelines.spatial.collect --lat 48.599 --lon 2.806 \
    --name "Project name" --operator "Operator" --power-mw 30 \
    --out ../smdc-newsroom/drafts/datacenters
```

Writes two files: `<id>.draft.json` (schema-valid, engine-scoreable) and
`<id>.provenance.json` (a side-car listing what ran, what was skipped, the commune facts —
population/surface — and the resolved DCE water body for W2). Omit `--out` to print to stdout.

### Batch (automate future runs)

Process a whole corpus in one command — the shape the phase-5 calibration sprint needs:

```bash
make collect-drafts SITES=my-sites.csv OUT=../smdc-newsroom/drafts/datacenters
# or directly:
python -m pipelines.spatial.batch my-sites.csv --out <newsroom>/drafts/datacenters
```

Input is CSV (`name,operator,lat,lon[,power_mw,project_status]`) or a JSON array of the same
fields (see `sample_sites.csv`). One draft+provenance pair per row, filenames keyed by id so
re-runs **refresh in place** (idempotent). A bad row or a source outage is reported and skipped —
never aborts the batch. It prints a **coverage matrix** (per indicator, how many sites filled) so
you can see corpus completeness at a glance.

Stdlib only, no API key. A source that is unreachable degrades that one indicator to `missing`;
the run never crashes (except when the point is outside France — the backbone geocoder can't place
it, and that is a hard error).

## The contract (why review is mandatory)

An out-of-range API value read wrong is exactly as dangerous as a hallucination. The draft is a
proposal; the engine still computes every score at build time from the **reviewed** file.
