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

# Voie A — enrich drafts with governance sidecars (CNDP referral + judged appeals + review leads).
# Proposes only; deterministic proxies are pre-filled, the judgment ones stay review leads.
#   make collect-governance SITES=my-sites.csv OUT=../smdc-newsroom/drafts/datacenters
collect-governance:
	uv run python -m pipelines.press.batch $(SITES) --out $(OUT)

# Voie B — harvest the open contestation-signal feeds → DRAFT watchlist (facts only, no grade).
# uMap FR + US fights + US moratoria; add GDELT press detection with GDELT_QUERY=.
#   make collect-signal SIGNAL_OUT=../smdc-newsroom/drafts/watchlist
SIGNAL_OUT ?= ../smdc-newsroom/drafts/watchlist
collect-signal:
	uv run python -m pipelines.press.collect_signal --out $(SIGNAL_OUT) $(if $(GDELT_QUERY),--gdelt-query "$(GDELT_QUERY)",)

# ── The orchestrated workflow (A-22) — everything auto-chains up to ONE human gate ──
# Onboard a DC: coords → spatial + governance + contestation match → bundle for review (no publish).
#   make onboard-dc LAT=48.59 LON=2.80 NAME="…" OPERATOR="…" POWER_MW=30 SIGNAL=<watchlist.draft.geojson>
onboard-dc:
	uv run python -m pipelines.orchestrate onboard --lat $(LAT) --lon $(LON) \
	  $(if $(NAME),--name "$(NAME)",) $(if $(OPERATOR),--operator "$(OPERATOR)",) \
	  $(if $(POWER_MW),--power-mw $(POWER_MW),) $(if $(PROJECT_STATUS),--project-status $(PROJECT_STATUS),) \
	  $(if $(SIGNAL),--signal $(SIGNAL),) --out $(OUT)

# Refresh the contestation signal → review queue (facts only). Add GDELT_QUERY= for press detection.
refresh-signal:
	uv run python -m pipelines.orchestrate refresh --out $(SIGNAL_OUT) $(if $(GDELT_QUERY),--gdelt-query "$(GDELT_QUERY)",)

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

build: score
	npm run build --prefix site

test: headers-check
	uv run pytest -q

headers:
	uv run python scripts/check_headers.py --fix

headers-check:
	uv run python scripts/check_headers.py

# Regenerate the downloadable one-pager PDFs from the built pages.
# Run after ANY change to site/src/content/questions.ts, then commit the PDFs.
onepager:
	npm run build --prefix site
	(cd site && npx astro preview --port 4399 > /dev/null 2>&1 & echo $$! > /tmp/smdc-preview.pid) && sleep 3
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="site/public/downloads/questions-data-center-fr.pdf" "http://localhost:4399/fr/comprendre/one-pager"
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="site/public/downloads/questions-data-center-en.pdf" "http://localhost:4399/understand/one-pager"
	lsof -ti :4399 | xargs kill 2>/dev/null || true
