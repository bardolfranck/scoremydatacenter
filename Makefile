.PHONY: validate score rescore build test install headers headers-check onepager

install:
	uv sync
	npm install --prefix site

validate:
	uv run python -m engine.validate

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
