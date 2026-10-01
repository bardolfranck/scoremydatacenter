# Pipeline workflow — the orchestrated flow with one human gate (A-22)

Runbook for whoever operates or maintains the collection pipeline. The individual bricks (spatial,
governance/voie-A, signal/voie-B, reviewer) are documented in their own `RECON*.md`/`REVIEW.md`;
this file is how they **chain**. Orchestrator: `pipelines/orchestrate.py`.

**One rule above all:** everything upstream auto-chains, there is **exactly one human gate**, and
**nothing downstream publishes without it** (A-07). The gate is the legal armour, not a slowdown.

---

## 🚧 GATE GÉO — il passe AVANT tout onboarding, et il est dans la machine

**Une coordonnée fabriquée ne doit pas pouvoir entrer dans le corpus.** Ce gate n'est pas une
consigne qu'on rappelle à un agent : c'est un refus de `engine.validate`, donc il s'applique à
qui que ce soit, sans qu'on ait à y penser.

```
uv run python -m pipelines.geo_audit.centroid_check     # la MESURE (réseau, hors build)
uv run python -m engine.validate                        # le GATE (déterministe, refuse)
```

**Mesure dehors, décision dedans.** Le détecteur interroge deux géocodeurs, donc du réseau,
que le build déterministe ne fait pas ; il écrit `calibration/geo-audit/centroid-check.json`.
`engine.validate` lit ce sidecar et refuse dans deux cas : une fiche classée « géo fabriquée
probable » sans dérogation, et un sidecar qui couvre moins de fiches que le corpus — sinon il
suffirait de ne pas relancer la mesure pour passer sans être vu.

**Le critère** : proche d'un oracle géocodeur (≤ 150 m) **ET** pas sur un bâtiment. Deux
oracles obligatoires — `geo.api.gouv.fr` (INSEE) **et** Nominatim, match sur l'un ou l'autre.
Un seul oracle ne suffit pas : cinq fiches FR déclarées propres par l'INSEE seul matchaient
Nominatim à 0 m, parce que la coordonnée venait d'un géocodeur tiers et non du nôtre. Le test
bâtiment élimine le bruit (47 faux positifs sur 58 signalements).

**Les dérogations sont dans `engine/validate.py`, `GEO_WAIVERS`**, datées et motivées. Une
dérogation n'est pas une exception silencieuse : elle est écrite, elle se voit en revue, et
elle doit disparaître. Une entrée sans motif ni date est un aveu d'échec.

**Ce que ce gate a coûté avant d'exister** : 6 fiches françaises publiques et notées portaient
une coordonnée de géocodeur, dont `fr-campus-ia-fouju` — 1 400 MW, le plus gros projet du
corpus — dont la coordonnée était le centroïde EXACT de sa commune. Corrigée vers la ZAC des
Bordes, sa note est passée de E à D : on publiait qu'elle bétonnait des terres agricoles, et
c'était faux. 4 des 6 venaient de `carte.dcmag.fr`, qui géocode des noms de commune.

## Flow A — onboard a data center to score

```
coords ─▶ [1 spatial] ─▶ [2 governance/voie A] ─▶ [3 contestation match/voie B] ─▶ [4 review]
                                                                                        │
                                              ┌─────────────────────────────────────────┘
                                              ▼
                                   🚦 HUMAN GATE  ─▶ [5 promote] ─▶ (contradictoire 15 j) ─▶ publish PR
```

One command:
```
make onboard-dc LAT=48.5878 LON=2.7628 NAME="…" OPERATOR="…" POWER_MW=1400 \
     SIGNAL=../smdc-newsroom/drafts/watchlist/watchlist.draft.geojson
# → python -m pipelines.orchestrate onboard --lat … --lon … --signal …
```

| Step | Module | In → Out | Guardrail at this edge |
|------|--------|----------|------------------------|
| 1 spatial | `pipelines.spatial.collect` | coords → `<id>.draft.json` (10/12 tier-1 indicators, sourced) + provenance | values only, never a score; unreachable source → `missing`, never fabricated |
| 2 governance | `pipelines.press.collect` | coords → `<id>.governance.json` (deterministic `cndp_referral` + judged `legal_appeals_count`; the 3 judgment proxies as **review leads**) | proposes; the leads need a human/LLM to read the PDF (A-07) |
| 3 contestation | `orchestrate.match_contestation` | coords + a harvested `watchlist.draft.geojson` → contestation entries within `--radius-km` (default 25) of the DC, reduced to the light shape | facts only, no grade; needs a prior `refresh` (else empty — logged, not fabricated) |
| 4 review | `pipelines.press.review` | contestation candidates → `contestation.review.jsonl` + `review.html` | `auto_published: false`; hard flags → `route: human` |
| 🚦 gate | **human** | see below | the one manual point — nothing proceeds without it |
| 5 promote | `orchestrate.promote_contestation` | approved queue → `contestation[]` entries + `archived_url` | only `decision: approve` applied; **silence ≠ consent** |

Output of steps 1–4 = a **bundle** in the private newsroom: `<newsroom>/drafts/datacenters/<id>/`
containing `<id>.draft.json`, `<id>.provenance.json`, `<id>.governance.json`,
`contestation.review.jsonl`, `review.html`.

---

## Flow B — refresh the contestation signal (periodic)

```
open feeds ─▶ [harvest] ─▶ [review] ─▶ 🚦 HUMAN GATE ─▶ [promote watchlist]
```
```
make refresh-signal SIGNAL_OUT=../smdc-newsroom/drafts/watchlist
# add GDELT_QUERY='datacenter (opposition OR moratorium)' for press detection
```
Harvests the four open feeds (uMap FR · US fights · US moratoria · GDELT), builds the review queue
(`watchlist.review.jsonl` + `watchlist.review.html`), stops at the gate. Re-runs review only the
**delta** in practice (dedupe already collapses the corpus). This is what step 3 of Flow A matches
against, so run it before onboarding a corpus.

---

## 🚦 The human gate — how to operate it

Primary mechanism = **the JSONL is the decision file**. Each line is a review item; you add a
`"decision"` field:

- `"approve"` — publish this fact as-is.
- `"edit"` then fix the `proposed` object in place (neutral `{fr,en}` label, correct `kind`,
  swap a weak source for a stronger primary one — "the press points, the registry proves"), then
  set `"approve"`.
- `"reject"` — drop it. Anything with **no `decision`** is held: silence is never consent.

Best-effort visual aid = **`review.html`** (static, no server): open it to eyeball a DC's few
contestation points — proposed label, source (live + archived) links, flags, route. It is a
**viewer**; the authoritative decision still lands in the JSONL.

For a scored DC you ALSO complete `T1` here: the governance sidecar pre-filled `cndp_referral` and
the judged appeals count; you fill the three judgment proxies (public inquiry, env-authority opinion,
council deliberations) from the sidecar's `review_leads` (open the PDF, record the enum fact — no
verdict, pre-mortem R2).

**In the same gesture, harvest the 5 project-block indicators from that dossier** (RED FLAG fix,
2026-07-09). The pipeline emits them as `not_collected` — the honest "nobody looked yet" state, which
keeps project/process at `insufficient_data` and **blocks publication** (Gate 8b). While the dossier
is open under your eyes, resolve each one:

| Indicator | Read from the dossier | Encode as |
|---|---|---|
| **E4** PUE target · **W4** cooling / water strategy · **F5** heat recovery / ERC · **L4**, **L5** local commitments | the operator's stated commitment | `announced` + value + full source (title, URL, accessed, **`archived_url`** — official doc, régime A-20) |
| any of the above genuinely **absent** from the dossier | you searched, no commitment | `missing` + a **read-trace source** (proves you looked — Gate 8a; the 0 is now earned) |

Never leave a project indicator `not_collected` on a DC you intend to publish, and never mark one
`missing` (an opacity accusation) without the read-trace: **an E of non-extraction is as false as an A
of complacency.** (A stage-2 LLM extractor will pre-fill this table from the dossier later; for now it
is the gate's checklist.)

Then:
```
make promote REVIEW=<newsroom>/drafts/datacenters/<id>/contestation.review.jsonl
```
`promote` applies only the `approve` rows, strips internal flags, and adds `archived_url` to each
source (best-effort Internet Archive capture — if a source is a raw API/JSON endpoint the snapshot
may be declined; swap to a press/registry URL, which archives cleanly). **This is still not a public
publish** — the public repo only receives a DC by the contradictoire PR at `status: published` (A-11).

---

## Stage 3 — synthesis redaction (post-scoring, automated, orthogonal to country)

The one narrative on each fiche (`synthesis`: two sides, `site` and `project_process`) is **not written
by hand** — it is a batch phase that runs **after the engine scores**, reads each DC's own measured
indicators + normalised scores, and delegates only the prose to the model. Built to scale to 10k DCs.

```
make score                                            # engine produces grades + normalised scores
python -m pipelines.synthesize --source <newsroom>/calibration/datacenters --artifacts site/public/data
# repeat --source per country panel (datacenters-be, …) — nothing here is country-specific
```

| In → Out | Guardrail at this edge |
|----------|------------------------|
| scored artifact `dc/<id>.json` + source DC → `synthesis` written back onto the **source** | model call is a **seam** (`llm=`); never hard-wires a vendor |
| deterministic prompt from measured `base`/`process` signals only | describes the **real value/score**, never a per-country assumption (grid at 9 vs 147 gCO₂/kWh) |
| every draft validated **before** it lands | **Gate 7** (no A–E letter in prose, reuses `engine.artifacts.synthesis_grade_citations`) + editorial bans; invalid → retried, then refused |
| `project_process == insufficient_data` → fixed honest block | no model call; "données insuffisantes", coherent with the withheld grade |
| already-synthesised DC skipped unless `--force` | idempotent — safe to re-run over the whole corpus |

The rules (grounding, two-axis, Gate 7, bans, fixed insufficient block) are one document:
`<newsroom>/calibration/SYNTHESIS-GENERATION.md`. `pipelines/synthesize.py` is its executable form.
The letter stays in the badge; the prose carries the *why*, for every country panel opened next.

---

## Guardrails carried end to end

- **No score anywhere in the pipeline.** Only the engine, at build, from the reviewed DC file.
- **Facts only in the signal** (A-21); a test fails the build if `grade`/`letter`/`score`/`confidence`
  appears in a signal/queue artifact.
- **Propose, never publish** (A-07): every artifact is a draft in the private newsroom; the public
  repo is untouched until the human PR.
- **Press is linked, never reproduced; evidence is archived** (A-20).
- **Nominative output stays private**; the orchestrator code is de-nominalized (public data-source
  endpoints only — no operator/project/collective names).

## Stage 4 — la carte de contexte (photo satellite ANNOTÉE) — NATIVE depuis 2026-09-29

**Toute fiche nouvelle naît avec sa carte de contexte.** Ce n'est plus un enrichissement
optionnel : c'est la photo par défaut de la fiche. Arbitrage Franck du 2026-09-29.

**Deux versions de la photo satellite coexistent, et c'est voulu — ne pas « harmoniser ».**
La version ANNOTÉE (`context_map`) est pour la FICHE, où elle remplace la vignette à
l'affichage. La version BRUTE non annotée (`satellite_image`) reste servie : elle alimente
le bandeau défilant de la home et les listes, et sert de repli sur les fiches sans carte.
Le bandeau garde les vignettes brutes **tant que le rendu de vignette annotée n'existe pas**
— à 400 px, un texte gravé à 20 px tombe à 7 px, donc une simple réduction serait illisible.
Une vignette annotée demanderait un rendu DISTINCT portant une seule annotation en gros ;
chantier non ouvert (Franck : « on ne fait pas les chantiers en même temps »).

```
uv run python -m pipelines.media.context_map_batch --scope fr  --upload
uv run python -m pipelines.media.context_map_batch --scope non-fr --upload
```

Le rendu est dans `pipelines/media/context_map.py`, le pilote dans `context_map_batch.py`.
Sortie R2 sous `ctx/{id}-{hmac8}.webp`, clé non énumérable comme `sat/` (A-28). Le build ne
publie l'URL **que si la clé est au manifeste** : pas de manifeste, pas de carte, jamais
d'URL devinée — toutes les fiches n'ont pas de carte, contrairement à la vignette.

**Qui y a droit.** Coordonnée vérifiée — sur un bâtiment ou à ≤ 25 m d'après
`calibration/geo-audit/on-building.json` — **plus toute fiche de projet** quel que soit son
verdict : sur un site non construit, le test bâtiment ne dit rien de la coordonnée. Les
fiches écartées gardent leur vignette brute.

**Les cinq annotations, et leurs règles.** Chacune porte le quoi, le combien et le
qualificatif, et **écrit son absence** au lieu de disparaître.

1. **Emprise** — le bâtiment apparié, tracé. Sur une fiche PROJET, aucun tracé sauf si OSM
   tague l'objet `data_center` : le bâtiment le plus proche d'un site non construit est
   celui d'un TIERS, et le cerner en le légendant « emprise » serait faux et dommageable.
2. **Cours d'eau NOMMÉ** le plus proche + l'état de sa masse d'eau (directive-cadre). Les
   cours d'eau sans nom sont du bruit — Étrechet en a 42 dans 1,5 km.
3. **Poste de RACCORDEMENT**, depuis la MÊME source que la note : Caparéseau en France, avec
   capacité d'accueil et taux de réservation. **Jamais le transformateur de rue le plus
   proche** — il contredirait la fiche (défaut du 2026-09-29 : carte « poste 20 kV à 334 m »
   contre fiche « poste à 1,1 km, 7,9 MW, réservé à 80 % »). Il est presque toujours hors
   cadre (1,3 à 4 km) : on l'écrit sans pastille. Hors FR, uniquement un poste de transport
   ≥ 63 kV, sinon « non déterminé ».
4. **Zone des logements** les plus proches + nombre de bâtiments dans 750 m. Zone, pas
   objet : le tagging résidentiel d'OSM est trop inégal pour désigner UN logement.
5. **Puissance contre taille de la commune** — « 1 400 MW déclarés — commune de 655
   habitants ». Par défaut sur toutes les fiches. Sans puissance, la ligne reste et dit
   « puissance déclarée inconnue ». Le qualificatif suit `power_mw_status` : jamais
   « déclarés » sur une estimation maison.

**L'image doit être auto-suffisante**, parce qu'elle voyage seule : nom du site, commune,
**pays**, note **telle qu'on la publie** (« note provisoire E–D », « note en attente » —
jamais une lettre ferme là où on publie une fourchette), date des annotations, crédits, et
la mention « les anneaux sont des tampons de distance, non un zonage réglementaire ». Cette
mention est **gravée dans l'image et nulle part ailleurs** : la répéter sous l'image sur la
fiche est une redondance qui trahit le principe.

**On POINTE, on ne repeint pas.** La photo montre déjà la rivière, le poste et les maisons.
Pastilles numérotées, distances mesurées, anneaux 100/300 m, échelle, nord. Pas de cercle de
zone autour d'une pastille : les anneaux font les zones. Azimuts réels — un schéma aux
directions inventées serait de la géo fabriquée.

**Données** : `api.openstreetmap.org` `map.json?bbox=` d'abord, **Overpass filtré en repli sur
le HTTP 400** (plafond de 50 000 objets en zone dense). Population : geo.api.gouv.fr en
France, Nominatim puis Wikidata P1082 ailleurs, **cache par commune** (Nominatim est à
1 req/s). WebP qualité 82 — un PNG pèse neuf fois plus pour la même image.

**Avant de rendre, la géo doit être propre.** Deux contrôles, tous deux nés du cas Fouju :
`pipelines/geo_audit/probe.py` (la coordonnée tombe-t-elle sur un bâtiment) et le détecteur
de centroïde (la coordonnée est-elle le centre administratif de sa commune). Le second doit
passer au **gate d'ingestion** : Fouju était publié, noté et faux, et ni l'audit bâtiment ni
le registre de provenance ne le voyaient. Critère fiable = **près d'un oracle géocodeur ET
pas sur un bâtiment** ; le seuil seul sur-signale.

## Stage 5 — les REGISTRES d'autorité environnementale (avis MRAe) — depuis 2026-10-01

Chaîne : **REGISTRE (index) → LIEN PDF → AVIS → JSON d'extraction → RATTACHEMENT**. Quatre
modules dans `pipelines/registers/`, un par maillon, et un seul chemin pour les lancer :

```
python -m pipelines.registers.run      --out ../smdc-newsroom/registres --national   # récolte : index → PDF → extraction
python -m pipelines.registers.match_run --out ../smdc-newsroom/registres              # rattachement + 3 sorties dérivées
```

`match_run` prend le **même `--out`** (le dossier du registre) ; le corpus noté est lu à côté,
dans `<out>/../calibration` (ou `$NEWSROOM_CAL`). Il ne touche AUCUN réseau, il est idempotent
(deux passages donnent le même octet), il ne modifie JAMAIS le corpus, et il s'arrête en erreur
si le corpus est absent ou tronqué — un `--out` qui pointe à côté ne doit pas produire un
rattachement vide qui aurait l'air valide.

Ce que chaque passage produit, **systématiquement et sans intervention** (la GÉNÉRATION est
automatique ; ce qu'on en fait ensuite ne l'est jamais — voir plus bas) :

| fichier | contenu | ce qu'un humain en fait |
|---|---|---|
| `registres/<avis>.json` | un JSON d'extraction par avis — chaque fait avec sa phrase et sa page | rien : donnée brute, sourcée |
| `registres/index.json` | ce qui a été traité, et **pourquoi** un document ne l'a pas été | rien |
| `registres/couverture.json` | champ × avis, région × avis, motif de rejet × document, **centroïdes partagés** | lit la comptabilité ; décide quoi collecter/corriger |
| `registres/rattachement.json` | quel avis parle de quelle fiche — **propositions, jamais confirmées** | **confirme** (`confirme: true`) avant tout service |
| `registres/rattachement.json` → `projets_a_collecter` | **les projets que l'État documente et que le corpus ignore** | **collecte** (nouvelle fiche, ou veille si non localisable) |
| `registres/rattachement-a-arbitrer.json` | les cas **ambigus** : par avis, le triplet `fiche (opérateur, commune)` de chaque candidat | **tranche** quelle fiche, sans ouvrir le corpus |
| `registres/operateurs-a-renseigner.json` | fiches rattachées à **opérateur inconnu** + le pétitionnaire de l'avis | **écrit** l'opérateur (l'avis est la provenance), ou laisse si le pétitionnaire manque |

### Le détecteur de projets est DANS la machine, pas dans la tête de l'opérateur

Le premier passage a trouvé cinq projets absents du corpus — DIGITAL MRS5 et SEGRO Urban
Logistics à Marseille, le Village Delage à Courbevoie, un programme mixte à Vélizy — **en
lisant les PDF un par un, à la main**. Un détecteur qui ne vit que dans le compte rendu d'un
run ne détecte rien au run suivant.

Il est donc une SORTIE NOMMÉE du rattachement (`projets_a_collecter`), écrite à chaque
passage, et il couvre deux cas :

- `non_rattache` — aucun candidat dans le rayon ni dans la commune ;
- `projet_absent_du_corpus` — des candidats existaient, mais **l'exploitant nommé par le
  document** ne correspond à aucun d'eux. C'est le cas des cinq : bonne commune, fiches
  voisines plausibles, et pourtant un autre site.

Le second cas suppose de lire l'exploitant DANS le PDF : 23 avis sur 39 viennent de l'index
national, qui ne publie pas le pétitionnaire. Sans cette lecture, le détecteur est aveugle
précisément là où il sert.

### Ce qui n'est JAMAIS automatique

**Un rattachement faux ferait apparaître sur une fiche les chiffres d'un autre projet — des
faits justes, sur la mauvaise fiche, et rien ne trahirait l'erreur.** C'est l'erreur la plus
grave que ce chantier puisse produire, parce qu'elle serait invisible. D'où la règle : la
machine PROPOSE, elle n'APPLIQUE jamais.

Les quatre sorties ne sont pas de même nature, et chacune attend un acte humain différent —
aucune ne se sert ni ne s'applique seule :

- `rattachement.json` **propose** un lien avis → fiche. Rien n'est servi tant qu'un humain
  n'a pas passé `confirme` à `true` (`confirme: false` partout à la sortie de la machine).
- `projets_a_collecter` **signale** un projet que le corpus ignore. Un humain décide d'en
  faire une fiche notée (localisation réelle établie) ou une entrée en veille, jamais sur une
  coordonnée de registre fabriquée.
- `rattachement-a-arbitrer.json` **demande un arbitrage** : plusieurs fiches à score égal,
  indiscernables par la machine. Un humain tranche en lisant le triplet, jamais la machine.
- `operateurs-a-renseigner.json` **demande une écriture** : l'opérateur manquant qu'un avis
  peut combler. Un humain l'écrit avec l'avis pour provenance — et s'abstient quand le
  pétitionnaire manque (une fiche signalée n'est pas une fiche à renseigner).

## Run it end to end on a fictional DC (recipe for a successor)

```
# 1. seed a signal to match against (or point --signal at an existing harvest)
python -m pipelines.orchestrate refresh --out /tmp/wl
# 2. onboard a fictional zz- DC (real coords, TEST identity)
python -m pipelines.orchestrate onboard --lat 48.59 --lon 2.80 --name "zz Test" \
    --operator TEST --power-mw 30 --signal /tmp/wl/watchlist.review.jsonl --out /tmp/onb
#    (note: onboard matches a *.geojson; use a harvested watchlist.draft.geojson as --signal)
# 3. edit /tmp/onb/<id>/contestation.review.jsonl — set "decision":"approve" on the good ones
# 4. python -m pipelines.orchestrate promote /tmp/onb/<id>/contestation.review.jsonl
```
Verified live: onboarding real coordinates produced a full bundle (tier-1 + governance + contestation
candidates matched within 25 km + `review.html`); `promote` applied only the approved entry and held
the rest. Offline tests: `engine/tests/test_orchestrate.py`.

## Reusability

The same orchestrator serves the initial backfill, the recurring signal delta, and each new scored
DC's `contestation[]`. Adding a DC is one command to the gate, then one `promote` — never a manual
step-by-step.

---

## Multi-country collection (11 countries + US watchlist)

The spatial pipeline is country-generic: one skeleton, a declarative spec per country resolved
through `pipelines/spatial/registry.py`. Full details, decision tree, status matrix and per-country
gotchas/TODO are in **[`spatial/COUNTRIES.md`](spatial/COUNTRIES.md)**. The operating flow — **one
way to run**, same three steps for every country:

```bash
# 1. COLLECT — registry-dispatched batch (the ONE path; --country selects the adapter)
make collect-country COUNTRY=BE SITES=sites-be.csv OUT=../smdc-newsroom/calibration/datacenters-be
#    Belgium routes by region (Wallonia/Flanders/Brussels) automatically; PL/SE/FI/NO/IE ride the
#    EU-member factory; DE/GB/NL/LU have national specs. US is NOT scored → watchlist (A-19).

# 2. PROMOTE — reviewed drafts become scored records (the loader ignores *.draft.json)
for f in ../smdc-newsroom/calibration/datacenters-be/*.draft.json; do cp "$f" "${f%.draft.json}.json"; done
rm ../smdc-newsroom/calibration/datacenters-be/*.draft.json

# 3. REBUILD the served artifacts — NEVER `make score` next to the newsroom (it refuses, would wipe
#    the corpus + watchlist to the zz fixtures). This is the single rebuild path.
make prod-artifacts
```

`load_datacenters` globs every `datacenters*` panel, so a new `datacenters-xx/` folder is scored
with zero build-path change. The A-25 reservation caps any A without operational proof to B, so a
thin foreign corpus never shows a false A.

**US and any non-EU-commons country → the watchlist, not a score** (cadrage A-19). Sourced facts,
no letter, no contradictoire: drop a `calibration/watchlist/<country>.json` array (same shape as
`fr-oppositions.json`); `make prod-artifacts` renders the "En veille" markers.

---

## État des lieux collecte → notation → affichage (2026-09-06) — la rationalisation

*Gravé sur demande directe de Franck : rationaliser la stack de collecte/notation/insertion site.
Décidé côté idées, pas encore côté code. Vision + estimation, pour caler l'équipe.*

### Le constat : 4 familles de collecte, une seule arrive jusqu'au site

| Famille | Ce qu'elle récolte | Où ça atterrit aujourd'hui |
|---|---|---|
| **① `spatial/`** (~30 fichiers, par pays) | structurel + coordonnées | **moteur → 1412 scorés → SITE** ✅ (la seule boucle complète) |
| **② `press/`** (GDELT signal) | ~4000 détections presse | **cul-de-sac** : niveau *article* (titre, pas de coords, pas d'entité projet) → non rattachable ✗ |
| **③ `veille/`** (radar quotidien) | ~10 candidats / passage | **fil Actu** = rappel visuel, puis meurt ✗ |
| **④ proposeurs** (`dcwatch/`, `eed/`, `seed/`) | candidats de sources ciblées | triage manuel → s'évapore ✗ |

**Chiffres clés** : sur 1404 sites notés, **1355 sont opérationnels** (96 %) ; seulement **57 sont
pipeline** (announced 49 / permitting 6 / construction 2). La contestation, elle, vit sur les
**annoncés** — qu'on ne score quasiment pas. D'où le double symptôme : un instantané figé
d'opérationnels + un ticker d'actu qui **ne renourrit jamais les scores**.

**Pourquoi ②③④ meurent** : le moteur a été bâti pour des sites opérationnels avec data spatiale
complète. Les signaux presse/veille sont au niveau article → **il manque un maillon
« signal → projet géolocalisé + dédupliqué » avant le moteur.** Preuve que c'est faisable : le
collecteur d'étude `press/osm_projects.py` (nuit 2026-09-06) a géolocalisé + scoré 34 projets
annoncés (cohorte T0b). C'est le **premier morceau** du maillon manquant.

### La cible : UN tapis roulant

```
DÉTECTER              RELIER + NETTOYER          SCORER            PUBLIER
②③④ + OSM        →   signal → projet         →  moteur        →  bandeau home
(presse/GDELT/OSM)    géolocalisé, dédupliqué,    existant          « derniers projets
                      entité + niveau opposition  (inchangé)         scorés » + flux API
                      ▲ LE CHAÎNON MANQUANT
```

Effet : le site passe de **« one-shot best-effort qui meurt lentement »** à **observatoire vivant**
(nouveaux scorés en tête de home chaque semaine, sans intervention) ; la **data fraîche devient un
vecteur d'appétence API** ; le même tapis fait grossir la **cohorte de validation** (N↑ → le pari
« précurseur » devient testable) et peut alimenter la **watchlist publique** en auto.

### Estimation du chantier (effort / difficulté, phasé)

| Phase | Contenu | Difficulté | Durée indicative | Risque principal |
|---|---|---|---|---|
| **1 — Quick win visible** | promouvoir `osm_projects.py` (déjà écrit) d'étude→onboarding PUBLIC des projets annoncés EU (gate voie-verte/voie-rouge) + bandeau home « derniers projets scorés » (comme le strip Actu déjà bâti) | **Faible-Moyenne** | **~1 semaine** | faux projets auto-onboardés → le gate humain existe déjà (A-22) |
| **2 — Le vrai maillon** | extracteur **presse → projet** : titre GDELT → géocode + entité + niveau opposition + dédup ; débloque les ~4000 détections ET la quantification de contestation (PQR/moratoire) | **Moyenne-Haute** | **~2-4 semaines** | qualité/coût LLM d'extraction ; géocodage titre→lieu ; dédup |
| **3 — Unifier + continu** | tout faire déboucher sur `orchestrate.py` (un seul run), cron continu, surface « flux frais » pour l'API | **Moyenne** | **~1 semaine** | câblage de pièces existantes, peu de risque neuf |

**Total ≈ 5-7 semaines** pour l'« observatoire vivant » complet, **mais un premier résultat visible
en ~1 semaine** (phase 1, sur l'acquis de la nuit). **Difficulté globale : MOYENNE** — ce n'est pas
de la recherche : moteur + affichage existent déjà, un seul composant est réellement délicat
(l'extracteur presse, phase 2). Le gros du reste = du **câblage** de briques qui existent.

**Principe directeur** (même doctrine que « one way to run », cf. `spatial/COUNTRIES.md`) : UN seul
chemin de run, pas de driver maison par source ; chaque famille de collecte se branche sur le
**même** maillon « relier+nettoyer » puis le **même** moteur. On ne multiplie pas les tapis, on en
fait converger un.

> **Le « PUBLIER » du tapis (où sort le score : public vs API payante) est une décision PRODUIT, pas
> dev.** Cadrage + pre-mortem = `1-cadrage`/`11-API/cadrage-API.md` §2bis (paywall par cycle de vie :
> note provisoire en plage → API, note définitive → public à la livraison). Ne pas dupliquer ici.
