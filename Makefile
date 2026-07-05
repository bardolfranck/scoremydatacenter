.PHONY: validate score rescore build test install

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

test:
	uv run pytest -q
