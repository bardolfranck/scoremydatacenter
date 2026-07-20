# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""The pipeline's one delegated step, wired — a `Callable[[str], str]` for `pipelines.synthesize`.

The synthesis phase (A-22 stage 3) deliberately left the model call as a SEAM so no vendor is
hard-wired into the pipeline. This module is one implementation of that seam, nothing more: it takes
a prompt, returns raw text, and knows nothing about data centres, scoring or prose rules — those all
live in `synthesize.py`, which validates every output against Gate 7 before it can land.

Credentials come from `~/.smdc/llm.env` (chmod 600), never from the repo and never from a CLI flag:
same convention as `~/.smdc/media.env` for the satellite pipeline. The key is read at call time and
never logged.

    from pipelines.llm_client import anthropic_llm
    synthesize_panel(src, artifacts, llm=anthropic_llm())

Model choice: Sonnet by default. The fiche is a public, citable, shareable artefact — the cost gap
against a cheaper tier is a few euros once, against prose that is permanent. Override per call site
if a batch genuinely does not warrant it.

stdlib only (urllib), consistent with the rest of the pipeline: no SDK dependency for one POST.
"""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5"
ENV_FILE = Path.home() / ".smdc" / "llm.env"


def _api_key() -> str:
    """ANTHROPIC_API_KEY from the environment, else from ~/.smdc/llm.env."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            name, _, value = line.strip().partition("=")
            if name == "ANTHROPIC_API_KEY" and value:
                return value.strip().strip("'\"")
    raise SystemExit(
        f"No ANTHROPIC_API_KEY. Put it in {ENV_FILE} (chmod 600) or export it.\n"
        "The synthesis phase is the pipeline's one delegated step; it needs a model."
    )


def anthropic_llm(model: str = DEFAULT_MODEL, *, max_tokens: int = 3000,
                  timeout: int = 90, retries: int = 3):
    """Return the `llm` callable `synthesize.redact()` expects: prompt in, raw text out.

    Retries only on transport/5xx/429 — a 4xx is a bug in the request, not bad luck, so it surfaces
    immediately rather than being burned through the retry budget.

    `max_tokens` has to clear the WORST case, not the median: a DC whose project & process grade is
    withheld needs one block, but a fully documented one needs two (site + project), each carrying
    lead/fr/en — six text fields. At 1200 the reply truncated mid-sentence and came back as invalid
    JSON, which `redact()` can only report as a parse error, not diagnose. Since output tokens are
    billed as generated, a generous ceiling costs nothing on the short replies.
    """
    key = _api_key()

    def call(prompt: str) -> str:
        body = json.dumps({
            "model": model, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(API_URL, data=body, headers={
            "x-api-key": key, "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        })
        last = None
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    payload = json.loads(resp.read().decode())
                return "".join(b.get("text", "") for b in payload.get("content", []))
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 529):
                    raise SystemExit(f"Anthropic API {exc.code}: {exc.read().decode()[:300]}")
                last = exc
            except Exception as exc:  # transport
                last = exc
            time.sleep(2 * (attempt + 1))
        raise SystemExit(f"Anthropic API unreachable after {retries} attempts: {last}")

    return call
