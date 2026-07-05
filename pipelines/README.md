# Pipelines

Reserved for the open data parsers (iter-0.5+), AGPL-3.0 — the Electricity Maps model.

- `spatial/` (iter-0.5): tier-1 spatial queries against public APIs (RTE, Hub'Eau/BNPE, INPN, Cerema, INSEE, Géorisques) from a project's coordinates alone.
- `press/` (iter-1): LLM extraction from press / permitting files / council deliberations (tier 2), with a mandatory human-validation queue.

Contract: a pipeline writes partial `data/datacenters/*.json` files (values + sources) — **never scores**. Manual entry and automated collection produce the same object.
