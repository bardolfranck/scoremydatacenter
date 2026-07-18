.PHONY: validate score rescore build test install headers headers-check onepager collect-drafts collect-governance collect-signal onboard-dc refresh-signal promote

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
	-@if [ -f $$HOME/.smdc/media.env ]; then 	  set -a; . $$HOME/.smdc/media.env; set +a; 	  if [ -n "$$SMDC_MEDIA_BASE" ]; then 	    uv run python -m pipelines.media.satellite --upload || echo "media-sat: non-fatal failure (voir logs)"; 	  else echo "media-sat: SMDC_MEDIA_BASE vide (activer R2 puis renseigner ~/.smdc/media.env)"; fi; 	else echo "media-sat: ~/.smdc/media.env absent — photos sat non générées"; fi

# Génération/upload manuel des photos satellite (mêmes règles, à la demande).
media-sat:
	@set -a; . $$HOME/.smdc/media.env; set +a; 	uv run python -m pipelines.media.satellite --upload

# Deploy the built site to Cloudflare Pages (direct upload — the prod build needs
# the private newsroom, so it happens HERE, never in a public-repo CI).
# One-time setup: `cd site && npx wrangler login` (Franck's Cloudflare account).
# Indexing open since 2026-07-16 (noindex lifted on Franck's call; robots.txt + sitemap served).
deploy: build
	cd site && npx wrangler pages deploy dist --project-name=scoremydatacenter --commit-dirty=true

# Regenerate the downloadable one-pager PDFs from the built pages.
# Run after ANY change to site/src/content/questions.ts, then commit the PDFs.
onepager:
	npm run build --prefix site
	(cd site && npx astro preview --port 4399 > /dev/null 2>&1 & echo $$! > /tmp/smdc-preview.pid) && sleep 3
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="site/public/downloads/questions-data-center-fr.pdf" "http://localhost:4399/fr/comprendre/one-pager"
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="site/public/downloads/questions-data-center-en.pdf" "http://localhost:4399/understand/one-pager"
	lsof -ti :4399 | xargs kill 2>/dev/null || true
