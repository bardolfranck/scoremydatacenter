# Tier-2 governance pipeline — procedural source feasibility recon (2026-07-07)

**"North face", Time 1.** Before writing the `press/` pipeline, each public source behind the tier-2
governance proxies was probed live. This pipeline fills the two indicators the spatial pipeline
leaves open (`T1` consent/governance proxies, `T2` documentation transparency), from a project's
identity (name, commune, INSEE, operator) — the output of the spatial stage.

> **Principle (shared with the spatial recon): "no API" is not "manual".** A listing site always
> fetches its records from somewhere — intercept that feed (a prefecture publication section, a SPIP
> `?page=backend` RSS, an undocumented search endpoint) rather than typing. Where the exact fact
> lives only in a filed-but-unjudged case, substitute a **primary-registry proof** obtained on
> request. Manual entry is the last resort.

> **Load-bearing doctrine — "the press points, the registry proves."** Press/RSS is only a
> *detector*. A fact enters a proxy value **only after confirmation in the official primary source**
> (CNDP dataset, administrative-court open data, prefecture publication, registry certificate). This
> is the anti-defamation guarantee by construction: no operator-named judgment, only dated, sourced,
> opposable facts. The pipeline **proposes, it never publishes** — LLM extraction goes to a
> human-validation queue; no LLM field becomes `measured` without review.

## What T1/T2 require (the contract, already frozen in the schema)

`T1` is a `factualized_judgment` with a closed proxy rubric — **no `value` field**, so an opinion
cannot be recorded:

| Proxy | Type |
|-------|------|
| `public_inquiry_held` | boolean |
| `environmental_authority_opinion` | enum favorable / favorable_with_reservations / unfavorable / none |
| `cndp_referral` | boolean |
| `legal_appeals_count` | integer ≥ 0 |
| `council_deliberations` | enum favorable / mixed / unfavorable / none_recorded |

`T2` (documentation transparency): `full_dossier_online / partial / minimal / unavailable` — filled
from the same sources (the inquiry file / project record / prefecture page *is* the availability).

## Feasibility matrix

Legend — **API**: documented endpoint, key-in → value-out. **Scraped feed**: no REST but a stable
machine-readable listing (sitemap / SPIP backend / prefecture template / undocumented JSON).
**Registry proof**: primary certificate obtained on request. **Proxy**: correlated source when the
direct fact isn't published. **Manual**: resists all of the above.

| Proxy | Source(s) | Probe result | Verdict |
|-------|-----------|--------------|---------|
| **`cndp_referral`** | data.gouv "Saisines de la CNDP" CSV + national débat-public site | ✅ CSV (Open Licence 2.0, 927 rows 1997→2026-03, `;`/cp1252) carries project name + **decision type** (public debate / prior consultation L.121-8 or L.121-17 / advisory / referral rejected / no procedure) + state. Site (Drupal): `sitemap.xml` (3,284 URLs w/ `lastmod`) + paginated project listing + `?keys=` search overlay catches what the ~2×/yr CSV misses | **API + scraped feed** |
| **`environmental_authority_opinion`** | Regional environmental-authority site (SPIP) + prefecture | ✅ `spip.php?page=backend` = RSS; per-region annual "avis rendus" pages list every opinion as a direct PDF (a data-center opinion was found live in one region's 2025 list). National authority = same SPIP pattern. PDF tenor is LLM-extractable | **Scraped feed** |
| **`public_inquiry_held`** (+ inquiry conclusion enum) | Prefecture publication sections `{dept}.gouv.fr/Publications/*` | ✅ shared state template across prefectures (verified on 3 départements), identical URL grammar; detail page + `RAPPORT-ET-CONCLUSIONS` sub-article carry the commissaire-enquêteur's **formal conclusion** (favorable / with reservations / unfavorable) as a downloadable PDF. No RSS/sitemap → per-département HTML sweep (the per-region sweep pattern) | **Scraped feed** |
| **`legal_appeals_count`** — judged | Administrative-court open data (TA/CAA/CE) | ✅ exhaustive since 2021–2022 (TA from 2022-06-30). Monthly zips `/DTA/{YYYY}/{MM}` (~85 MB) = durable channel; undocumented JSON search API (`/recherche/api/model_search_juri/openData/{JURI}/{term}/200`) verified returning per-court dossiers. Companies/communes/lawyers named (only natural persons pseudonymized) → project matching works. Terms are OR-matched → phrase logic client-side on the zips | **Scraped feed + monthly dump** |
| **`legal_appeals_count`** — pending | Registry certificate (art. R.600-7 code de l'urbanisme) | ✅ *anyone* may request from the court registry a certificate attesting no appeal **or giving the filing date** of one. Free, per-decision, mail form per court. Open data holds **judged cases only** — a filed-but-unjudged appeal (what the press reports) is invisible for 1–3 yrs. Detect in press/RSS → prove by certificate | **Detection → registry proof (semi-auto)** |
| **`council_deliberations`** | Town-hall site (via public directory API) + press | ⚠️ national open standard covers ≪1% of communes (≈41 datasets) → unusable as primary. Chain verified: commune → INSEE (`geo.api.gouv.fr`) → town-hall website (`api-lannuaire.service-public.fr`) → scrape deliberation PDFs + LLM; small communes that publish nothing fall back to press + human confirmation of the actual minutes | **Proxy (semi-auto), per-commune availability flag** |
| **T2** documentation online | e-inquiry registry providers + prefecture + impact-study aggregator | ✅ registry providers expose current-inquiry listings (one enumerable by sequential ID, ~1–7100; one Webflow collection); one is Cloudflare-challenged (needs a headless pass). Presence/completeness maps to the enum | **Scraped feed** |

## Recommended v1 perimeter

**Automated now (input = the identity the spatial stage already produces):**
- `cndp_referral` — data.gouv CSV + débat-public site overlay. *Clean.*
- `environmental_authority_opinion` — SPIP RSS/pages + prefecture PDF, LLM tenor extraction **with a
  recalibrated enum** (see caveat).
- `public_inquiry_held` (+ inquiry-conclusion enum) — per-département prefecture sweep, **all**
  participation section types (post-2023 "green industry" law scatters authorizations across sibling
  sections, not just "enquêtes publiques").
- `legal_appeals_count` (judged) — monthly admin-court zips + local index + phrase-match.
- `T2` — documentation presence from the same sources.

**Semi-automated (detect → human confirmation, feeding the A-07 validation queue):**
- `legal_appeals_count` (pending) — press/court-RSS detection → R.600-7 registry certificate.
- `council_deliberations` — directory → town-hall site → LLM, else press + minutes confirmation.

**Deferred / secondary:** the national impact-study aggregator has no simple REST (JS-only search) —
a secondary net when a region is missing; one Cloudflare-challenged registry provider needs a
headless-browser pass.

## Calibration notes to carry into the methodology freeze (plan phase 5)

1. **Recalibrate `environmental_authority_opinion`.** A regional environmental authority does **not**
   issue a favorable/unfavorable opinion — it issues observations and recommendations. The
   favorable / with-reservations / unfavorable shape belongs to the **inquiry commissioner's
   conclusion**, not the environmental-authority opinion. Recommendation: decouple the two — a factual
   environmental-authority enum (opinion issued + recommendation count / no observations) distinct
   from the inquiry-conclusion enum — rather than forcing a verdict the authority never renders.
2. **Define appeal direction in `legal_appeals_count`.** A single project generates appeals in both
   directions (developer vs. commune preemption ≠ opponents vs. project authorizations). Decide
   whether the proxy counts all appeals or tags direction — the pillar's "contestation" meaning
   suggests distinguishing.
3. **Interpretability of a missing CNDP referral** depends on the R.121-2 industrial-equipment cost
   thresholds; a pending decree may remove industrial equipment from mandatory referral — track it in
   provenance so "no referral" stays interpretable.
4. **Press/publication coverage bias is a confidence counter, never a zero.** A commune with no local
   press or portal is not a commune "without contestation" — feed this into the two-cause confidence
   (`missing_data` ≠ `unverifiable_declarative`), never into a low proxy value.
5. **T1×CNDP / L6 collinearity** (already flagged, A-18): re-check double-counting in phase 5.

## v1 build (Time 2) — what ships

`pipelines/press/` mirrors the spatial pipeline (stdlib only, each collector returns a sourced dict
or `None`, never a score). One command per site or per corpus:

```
python -m pipelines.press.collect --lat .. --lon .. --name ".." --out <newsroom>/drafts/datacenters
make collect-governance SITES=sites.csv OUT=<newsroom>/drafts/datacenters
```

Output = **`<id>.governance.json` sidecar** next to the spatial draft — never written into the scored
record, because a valid `T1` needs all five proxies and three need a human/LLM to read a PDF. The
sidecar carries:

- **`proposed_t1_proxies`** — the two deterministic proxies pre-filled and sourced:
  `cndp_referral` (from the CNDP register, with decision type + fiche URL) and `legal_appeals_count`
  (judged, a **provisional upper bound** with the full dossier list — the metadata-only court API
  can't tighten it, and appeal direction needs human triage). The three judgment proxies stay
  `null`.
- **`review_leads`** — the exact documents to open for the null proxies and T2 (MRAe search,
  prefecture publications, town-hall site, impact-study aggregator, the R.600-7 note for pending
  appeals).
- **`caveats`** — appeal direction, CNDP-absence-is-not-proof, MRAe-tenor-recalibration, coverage
  bias is a confidence signal not a zero.

Verified live end-to-end on a real contested case: deterministic `cndp_referral: true` (decision
type + fiche resolved from the register) and a non-zero judged-appeals bound with dossier numbers +
dates, the three judgment proxies handed over as leads. A point that reverse-geocodes to the wrong
commune yields no fabricated referral — the real project surfaces only as a `other_dept_candidates`
lead, exactly the anti-fabrication contract.

**Known v1 limitations (documented, not silently capped):** the TA code is guessed as `TA{dept}`
(right when the competent court sits in the department — the common case; the search URL is always
emitted as a lead for the exceptions); the judged-appeals count is a provisional upper bound;
`environmental_authority_opinion` / `public_inquiry_held` / `council_deliberations` are leads, not
values, until the iter-1 LLM stage + human queue reads the PDFs.

## Guardrail (unchanged, load-bearing)

The pipeline **proposes, it never publishes.** Output = sourced draft fragments in `smdc-newsroom`
(private), every value carrying its primary source, **zero notes/scores**. Press is a detector; the
registry proves. No LLM-extracted field reaches `status: measured` without human validation. Tested
only against fictional `zz-` fixtures in the public repo; nothing operator-named enters here.
