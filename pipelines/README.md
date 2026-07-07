# Pipelines

Reserved for the open data parsers (iter-0.5+), AGPL-3.0 — the Electricity Maps model.

- `spatial/` (iter-0.5, **v1 built**): tier-1 collection from a project's coordinates alone. v1 auto-fills **10 of 12** indicators + identity — E1/W1/W3/F1/F2/L3 via public APIs, E2/E3 by reading Caparéseau's map data feed directly (no REST API, but the data is there), L1 via a cached INSEE Filosofi join, and W2 via the EEA WISE national WFD-status table joined by water-body code. Only L2 (needs the project's power) and F3/T1/T2 (later stages) remain. A batch runner scales it to a whole corpus in one command. See `spatial/RECON.md` for the feasibility matrix and `spatial/README.md` to run it.
- `press/` (**voie A v1 built**; LLM stage iter-1): tier-2 governance collection from official documents. v1 fills the deterministic proxies — `cndp_referral` (national CNDP saisines register) and judged `legal_appeals_count` (administrative-court open data, a provisional upper bound) — and hands the judgment proxies (`environmental_authority_opinion` / `public_inquiry_held` / `council_deliberations`) + T2 to a reviewer as sourced leads. Output is an `<id>.governance.json` sidecar, never injected into the scored record. The iter-1 stage adds LLM extraction from the linked PDFs (avis, inquiry conclusions) with a mandatory human-validation queue. See `press/RECON.md`.

Contract: a pipeline writes partial `data/datacenters/*.json` files (values + sources) — **never scores**. Manual entry and automated collection produce the same object.
