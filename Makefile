.PHONY: validate score rescore build test install headers headers-check onepager collect-drafts collect-governance collect-signal onboard-dc refresh-signal promote sync-api-r2 veille-fr veille-actu actu-latest

install:
	uv sync
	npm install --prefix site

validate:
	uv run python -m engine.validate

# Batch spatial collection from coordinates → sourced DRAFTS in the private newsroom.
# Proposes only; every draft is human-reviewed before it enters the circuit.
#   make collect-drafts SITES=my-sites.csv OUT=../smdc-newsroom/drafts/datacenters
SITES ?= pipelines/spatial/sample_sites.csv
OUT ?= ../smdc-newsroom/drafts/datacenters
collect-drafts:
	uv run python -m pipelines.spatial.batch $(SITES) --out $(OUT)

# Same batch, any country — the ONE way to collect a country's sites (registry-dispatched).
#   make collect-country COUNTRY=NL SITES=sites-nl.csv OUT=../smdc-newsroom/calibration/datacenters-nl
collect-country:
	uv run python -m pipelines.spatial.batch $(SITES) --country $(COUNTRY) --out $(OUT)

# Seed from DCWatch (Hubblo, ODbL) — exports a sites CSV for the batch above; never a new driver.
# Sites already in the panel (within 300 m) are set aside, not re-proposed. Output stays private
# in the newsroom (ODbL share-alike pending legal review — see JOURNAL 2026-07-13).
#   make seed-dcwatch RELEASE=2026.04.09 COUNTRY=FR SEEDS=../smdc-newsroom/seeds
RELEASE ?= 2026.04.09
SEEDS ?= ../smdc-newsroom/seeds
seed-dcwatch:
	uv run python -m pipelines.seed.dcwatch --release $(RELEASE) --country $(COUNTRY) \
	  --exclude-panel ../smdc-newsroom/calibration/datacenters \
	  --exclude-panel ../smdc-newsroom/drafts/datacenters --out $(SEEDS)

# Voie A — enrich drafts with governance sidecars (CNDP referral + judged appeals + review leads).
# Proposes only; deterministic proxies are pre-filled, the judgment ones stay review leads.
#   make collect-governance SITES=my-sites.csv OUT=../smdc-newsroom/drafts/datacenters
collect-governance:
	uv run python -m pipelines.press.batch $(SITES) --out $(OUT)

# Voie B — harvest the open contestation-signal feeds → DRAFT watchlist (facts only, no grade).
# uMap FR + US fights + US moratoria; add GDELT press detection with GDELT_QUERY=.
# SIGNAL_COUNTRIES="CA …" adds per-country GDELT specs (signal.GDELT_COUNTRY_SPECS) — the path
# for countries with no geo feed (Canada…).
#   make collect-signal SIGNAL_OUT=../smdc-newsroom/drafts/watchlist SIGNAL_COUNTRIES=CA
SIGNAL_OUT ?= ../smdc-newsroom/drafts/watchlist
SIGNAL_COUNTRY_FLAGS = $(foreach c,$(SIGNAL_COUNTRIES),--country $(c))
collect-signal:
	uv run python -m pipelines.press.collect_signal --out $(SIGNAL_OUT) $(if $(GDELT_QUERY),--gdelt-query "$(GDELT_QUERY)",) $(SIGNAL_COUNTRY_FLAGS)

# ── The orchestrated workflow (A-22) — everything auto-chains up to ONE human gate ──
# Onboard a DC: coords → spatial + governance + contestation match → bundle for review (no publish).
#   make onboard-dc LAT=48.59 LON=2.80 NAME="…" OPERATOR="…" POWER_MW=30 SIGNAL=<watchlist.draft.geojson>
onboard-dc:
	uv run python -m pipelines.orchestrate onboard --lat $(LAT) --lon $(LON) \
	  $(if $(NAME),--name "$(NAME)",) $(if $(OPERATOR),--operator "$(OPERATOR)",) \
	  $(if $(POWER_MW),--power-mw $(POWER_MW),) $(if $(PROJECT_STATUS),--project-status $(PROJECT_STATUS),) \
	  $(if $(SIGNAL),--signal $(SIGNAL),) --out $(OUT)

# Refresh the contestation signal → review queue (facts only). Add GDELT_QUERY= for press
# detection, SIGNAL_COUNTRIES="CA …" for per-country GDELT specs.
refresh-signal:
	uv run python -m pipelines.orchestrate refresh --out $(SIGNAL_OUT) $(if $(GDELT_QUERY),--gdelt-query "$(GDELT_QUERY)",) $(SIGNAL_COUNTRY_FLAGS)

# Apply a human-approved contestation review queue (only decision:approve; adds archived_url).
# Pass INTO=<dc.json> to WRITE the approved facts into the DC file (the last mile → re-score to render).
#   make promote REVIEW=<id>/contestation.review.jsonl INTO=<id>/<id>.draft.json
promote:
	uv run python -m pipelines.orchestrate promote $(REVIEW) $(if $(INTO),--into $(INTO),)

# Promote an approved review queue into the standalone "En veille" watchlist layer (A-19).
# Then `make build` regenerates watchlist.geojson → the map's distinct markers.
#   make promote-watchlist REVIEW=<queue>.jsonl WATCHLIST=../smdc-newsroom/drafts/watchlist/fr.json
promote-watchlist:
	uv run python -m pipelines.orchestrate promote $(REVIEW) --watchlist $(WATCHLIST)

score: validate
	uv run python -m engine.score

# Record a justified grade change in the audit journal, e.g.:
#   make rescore EVENT=data_correction RATIONALE="operator provided the measured PUE"
rescore:
	uv run python -m engine.score --record --event $(EVENT) --rationale "$(RATIONALE)"

# With the private newsroom checked out next door (Franck's machine, local agents),
# `make build` rebuilds the served data from the REAL corpus — running the public-only
# `score` here wiped the map down to the 2 zz fixtures three times. Without the
# newsroom (CI, external cloners), it falls back to `score` as before.
build:
	@if [ -d ../smdc-newsroom/calibration ]; then $(MAKE) prod-artifacts; else $(MAKE) score; fi
	npm run build --prefix site
	$(MAKE) prune-public-json

# Anti-pillage (Franck 2026-07-22, corrigé 2026-07-23): the deployed site serves
# HTML, never the raw data. The build INLINES every JSON it needs into the HTML;
# Astro also mirrors public/data/*.json into dist/ — those are the bulk-scrape
# hole (one curl on scores.json = the whole corpus).
# We do NOT delete them: a DELETED asset leaves Cloudflare's edge serving a STALE
# cached copy for days — a 404 origin can't evict it (the cache saga of 07-22:
# scores.json still 200/2.7 MB 20 h after the prune). Instead we OVERWRITE each
# with a tiny no-store STUB, so the asset still EXISTS in the deployment:
# Cloudflare then has something authoritative to serve and replaces the stale
# corpus. Only the two geojson the map fetches at runtime keep real (Seau-A) data.
prune-public-json:
	@find site/dist/data -name '*.json' ! -name '*.geojson' -type f -exec sh -c 'printf "%s" "{\"gone\":true,\"note\":\"Bulk data endpoints are retired - structured access is available via the API.\"}" > "$$1"' _ {} \;
	@echo "prune: $$(find site/dist/data -name '*.json' ! -name '*.geojson' | wc -l | tr -d ' ') data JSON replaced by no-store stub; geojson kept → $$(ls site/dist/data/*.geojson 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' ')"

test: headers-check
	uv run pytest -q

headers:
	uv run python scripts/check_headers.py --fix

headers-check:
	uv run python scripts/check_headers.py

# Regenerate the citable methodology doc from methodology.json (no divergence).
methodology-doc:
	uv run python scripts/gen_methodology_doc.py

# Rebuild the SERVED artifacts from the private newsroom (real DCs + watchlist),
# NOT the public zz- fixtures. Use this — never `make score` — to refresh the site
# data; `make score` reads the public repo and would wipe the corpus to 2 test DCs.
# WORKFLOW (brief 9-img-sat, A-28) : toute nouvelle fiche reçoit sa photo
# satellite AUTOMATIQUEMENT au build de prod — génération idempotente (skip si
# déjà sur R2), non fatale (le build n'échoue jamais pour une image), politesse
# réseau. Secret HMAC + base URL : ~/.smdc/media.env (hors repos).
prod-artifacts:
	uv run python scripts/build_prod_artifacts.py
	-@if [ -f $$HOME/.smdc/media.env ]; then 	  while IFS= read -r kv; do case "$$kv" in ''|\#*) ;; *=*) export "$$kv" ;; esac; done < $$HOME/.smdc/media.env; 	  if [ -n "$$SMDC_MEDIA_BASE" ]; then 	    uv run python -m pipelines.media.satellite --upload || echo "media-sat: non-fatal failure (voir logs)"; 	  else echo "media-sat: SMDC_MEDIA_BASE vide (activer R2 puis renseigner ~/.smdc/media.env)"; fi; 	else echo "media-sat: ~/.smdc/media.env absent — photos sat non générées"; fi
	$(MAKE) sync-api-r2

# Go-live paid-API hook (Franck 2026-07-23): push the freshly built artifacts to
# the PRIVATE API bucket (paid Seau B) via the API repo's own sync script. It is
# GARDÉ + NON FATAL + INERTE — it does NOTHING until BOTH exist: the committed
# script AND its dedicated R2 creds. So a site deploy can never touch the API
# bucket by accident, and never before the API's test key is killed + auth locked
# (P6: the paywall must be shut before the real corpus lands in R2).
# Contract for agent-codeur-API (the Worker lives in the PRIVATE sibling repo
# ../smdc-api — option A, Franck 2026-07-23 — NOT inside this public repo):
#   - script:  ../smdc-api/scripts/sync-r2.sh  (committed there; runs
#              `aws s3 sync … --delete`, excludes zz-*, targets smdc-api-data)
#   - creds:   ~/.smdc/r2-api.env  (KEY=VALUE — AWS_ACCESS_KEY_ID / _SECRET_ACCESS_KEY
#              / endpoint), an S3 R2 token scoped to smdc-api-data ONLY. NOT the
#              média-sat HMAC token (different mechanism + least privilege).
# The script's DATA_DIR defaults to site/public/data, resolved from the make cwd
# (this repo root), so the sibling location does not change what gets synced.
# Env is parsed line-by-line (KEY=VALUE only) — a malformed line is skipped, never
# executed, so a secret can never leak into the build log (cf. the cloudflare.env
# lesson).
SYNC_R2 ?= ../smdc-api/scripts/sync-r2.sh
sync-api-r2:
	-@if [ -f "$(SYNC_R2)" ] && [ -f "$$HOME/.smdc/r2-api.env" ]; then \
	  while IFS= read -r kv; do case "$$kv" in ''|\#*) ;; *=*) export "$$kv" ;; esac; done < "$$HOME/.smdc/r2-api.env"; \
	  echo "sync-api-r2: pushing published artifacts → smdc-api-data (R2)"; \
	  sh "$(SYNC_R2)" || echo "sync-api-r2: non-fatal failure (see logs)"; \
	else \
	  echo "sync-api-r2: inert — needs $(SYNC_R2) (committed) + ~/.smdc/r2-api.env; API bucket untouched"; \
	fi

# Génération/upload manuel des photos satellite (mêmes règles, à la demande).
media-sat:
	@while IFS= read -r kv; do case "$$kv" in ''|\#*) ;; *=*) export "$$kv" ;; esac; done < $$HOME/.smdc/media.env; 	uv run python -m pipelines.media.satellite --upload

# Deploy the built site to Cloudflare Pages (direct upload — the prod build needs
# the private newsroom, so it happens HERE, never in a public-repo CI).
# One-time setup: `cd site && npx wrangler login` (Franck's Cloudflare account).
# Indexing open since 2026-07-16 (noindex lifted on Franck's call; robots.txt + sitemap served).
deploy: build
	cd site && npx wrangler pages deploy dist --project-name=scoremydatacenter --commit-dirty=true
	$(MAKE) purge-cache

# Post-deploy cache purge (Franck 2026-07-22, durci 2026-07-28): a Pages deploy
# does NOT evict the zone edge cache. Enumerating URLs (the old approach) was
# fragile — it only covered /data/*.json + geojson, so any HTML page whose
# bundle hash changed kept serving stale (the map/watchlist rendered from an old
# JS chunk), and every NEW file was missed until someone added it to the list.
# The durable fix is a single "purge_everything": one complete flush of the zone
# after each deploy, immune to whatever files appeared or vanished. It is rate-
# limited to ~1/second per zone (a non-issue for deploys) and needs the SAME
# token as before (Zone > Cache Purge:Edit) + the zone id, in
# ~/.smdc/cloudflare.env (CF_PURGE_TOKEN=... / CF_ZONE_ID=...). Without it:
# skipped with a loud notice (the whole edge stays cached until a dashboard purge).
# The env file is parsed line-by-line (KEY=VALUE only), NEVER sourced/executed —
# a malformed or bare line is skipped, so a secret can never leak into the log
# (2026-07-27 incident: a bare token line was echoed as "command not found").
# Values are then whitespace-stripped: a stray trailing char on CF_ZONE_ID (a
# CRLF file) had been silently malforming the purge URL, so EVERY make purge
# quietly failed — the old target never checked "success", so it went unnoticed
# and looked like recurring "stale edge cache" (root-caused 2026-07-28).
purge-cache:
	@if [ -f $$HOME/.smdc/cloudflare.env ]; then \
	  while IFS= read -r kv; do case "$$kv" in ''|\#*) ;; *=*) export "$$kv" ;; esac; done < $$HOME/.smdc/cloudflare.env; \
	  CF_ZONE_ID=$$(printf '%s' "$$CF_ZONE_ID" | tr -d '[:space:]'); \
	  CF_PURGE_TOKEN=$$(printf '%s' "$$CF_PURGE_TOKEN" | tr -d '[:space:]'); \
	  ok=""; \
	  for try in 1 2; do \
	    ok=$$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$$CF_ZONE_ID/purge_cache" \
	      -H "Authorization: Bearer $$CF_PURGE_TOKEN" -H "Content-Type: application/json" \
	      --data '{"purge_everything":true}' | grep -o '"success":[a-z]*' | head -1); \
	    [ "$$ok" = '"success":true' ] && break; \
	    sleep 2; \
	  done; \
	  if [ "$$ok" = '"success":true' ]; then \
	    echo "purge-cache: purge_everything OK — whole edge (HTML + assets + /data) flushed"; \
	  else \
	    echo "purge-cache: purge_everything FAILED after retry — check the token (Zone>Cache Purge:Edit) or purge from the dashboard"; \
	  fi; \
	else \
	  echo "purge-cache: ~/.smdc/cloudflare.env absent — cache NOT purged (create a Zone>Cache Purge:Edit token, else Purge Everything in the dashboard)"; \
	fi

# Regenerate the downloadable one-pager PDFs from the built pages.
# Run after ANY change to site/src/content/questions.ts, then commit the PDFs.
onepager:
	npm run build --prefix site
	(cd site && npx astro preview --port 4399 > /dev/null 2>&1 & echo $$! > /tmp/smdc-preview.pid) && sleep 3
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="site/public/downloads/questions-data-center-fr.pdf" "http://localhost:4399/fr/comprendre/one-pager"
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="site/public/downloads/questions-data-center-en.pdf" "http://localhost:4399/understand/one-pager"
	lsof -ti :4399 | xargs kill 2>/dev/null || true

# Daily veille — detect new FR data-center projects → candidate drafts → digest in the PRIVATE
# newsroom (veille/<date>/). NEVER deploys, NEVER publishes a grade, NEVER sends mail (the send
# leg is CF-side, agent-codeur-site). No LLM needed → a plain daily scheduler runs this directly
# (see pipelines/veille/README.md for the launchd/cron snippet). Commits only the veille/ tree.
VEILLE_OUT ?= ../smdc-newsroom/veille
VEILLE_TIMESPAN ?= 1w
veille-fr:
	uv run python -m pipelines.veille.fr --out $(VEILLE_OUT) --timespan $(VEILLE_TIMESPAN)
	@cd $(VEILLE_OUT)/.. && git add veille && \
	  if git diff --cached --quiet; then echo "veille-fr: rien de neuf"; \
	  else git commit -q -m "veille: digest $$(date +%F)" && (git push -q 2>/dev/null && echo "veille-fr: digest poussé au newsroom" || echo "veille-fr: commit local (push différé — offline?)"); fi

# Daily ACTU — GDELT harvest → Sonnet classifier (news/projet/bruit) → actu.json. Writes the PRIVATE
# archive (newsroom/actu/<date>/, ALL items) + refreshes the DEPLOYED site/public/data/actu/latest.json
# (approved-only — today's items start UNAPPROVED, so nothing new goes public until Franck approves via
# `promote`). Needs the Sonnet key (~/.smdc/llm.env). NEVER deploys/publishes/sends. Commits actu/ only.
NEWSROOM ?= ../smdc-newsroom
ACTU_TIMESPAN ?= 1w
veille-actu:
	uv run python -m pipelines.veille.actu --newsroom $(NEWSROOM) --public-data site/public/data --timespan $(ACTU_TIMESPAN)
	@cd $(NEWSROOM) && git add actu && \
	  if git diff --cached --quiet; then echo "veille-actu: rien de neuf"; \
	  else git commit -q -m "actu: archive $$(date +%F)" && (git push -q 2>/dev/null && echo "veille-actu: archive poussée au newsroom" || echo "veille-actu: commit local (push différé — offline?)"); fi

# DEPLOY side: regenerate the deployed site/public/data/actu/latest.json from the COMMITTED newsroom
# archives (approved-only, windowed, transient _gate stripped). The CI run's public/data is
# ephemeral → the newsroom is the source of truth. Call this in the site build BEFORE astro build.
# No network, no LLM key. (agent-codeur-site 2026-09-04)
actu-latest:
	uv run python -m pipelines.veille.actu --regen-latest --newsroom $(NEWSROOM) --public-data site/public/data
