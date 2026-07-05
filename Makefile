.PHONY: validate score build test install

install:
	uv sync
	npm install --prefix site

validate:
	uv run python -m engine.validate

score: validate
	uv run python -m engine.score

build: score
	npm run build --prefix site

test:
	uv run pytest -q
