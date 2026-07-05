# Schemas

JSON Schema contracts for all data files (phase 1):

- `datacenter.schema.json` — identity, indicators (raw sourced values only), publication workflow, score history. Encodes the pre-mortem rules structurally (no `value` field on judgment indicators, mandatory sources, announced ≠ measured).
- `methodology.schema.json` — pillars, indicators, normalization, threshold traceability (`threshold_basis` mandatory), confidence rules.

All keys and enums are English-only; French survives only inside `{ "fr": …, "en": … }` editorial values.
