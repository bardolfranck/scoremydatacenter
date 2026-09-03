# Veille — daily detection of new data-centre projects (FR v1)

Operationalises **Flow B** of the [WORKFLOW](../WORKFLOW.md) on a **daily cadence** (Franck
2026-07-28): detect new FR DC projects → **candidate drafts (no grade)** → an HTML **digest** +
manifest deposited in the **private newsroom** → Franck's human gate in the chat.

```
GDELT-FR (announce) ─▶ [detect] ─▶ [operator tag] ─▶ [coordless dedup vs corpus] ─▶ candidate
drafts ─▶ digest.html + manifest.json ─▶ commit newsroom/veille/<date>/ ──▶ 🚦 Franck reads, replies
                                                                              "accepte <id>" in chat
```

The driver **DETECTS + ENRICHES + builds the DIGEST + commits it to the newsroom**. It **NEVER**
deploys, **NEVER** publishes a grade, **NEVER** sends mail. The send leg is CF-side (agent-codeur-site,
Resend key stays in Franck's `~/.smdc`, never crosses here).

## Run it

```bash
make veille-fr                        # daily: --timespan 1w → newsroom/veille/<date>/, commit+push
make veille-fr VEILLE_TIMESPAN=3m     # richer backfill (first digest)
```

No LLM, no API key — GDELT DOC API is keyless (throttled). Safe to run unattended.

## Doctrine held by construction (tested — `engine/tests/test_veille.py`)

- **No grade anywhere.** `digest.render_digest` REFUSES to render a candidate carrying any judgement
  key (`score`/`grade`/`confidence`/`pillar`). en-veille = sourced facts only (A-19/A-21).
- **Licence tag travels.** Every candidate carries `provenance{source, url, license, publishable}`.
  A commercial-origin lead (e.g. DCMag) is `publishable:false` → a **NON-PUBLIABLE** banner in the
  digest **and** excluded from `fr.promote_subset` (never reaches the render path).

## v1 scope

GDELT-FR only = a **press radar**. The DOC artlist gives title+url only, so candidates are
**coordless** (no geocode, no tier-1 enrichment); the digest says so honestly. **v2**: geocoding
(`geo.api.gouv`) + tier-1 enrichment + GKG V2Locations, MRAe RSS, cross-day dedup.

## Daily schedule (no LLM needed — a plain OS scheduler)

macOS launchd — `~/Library/LaunchAgents/org.scoremydatacenter.veille.plist` (adjust the repo path,
then `launchctl load` it). Runs at 07:00 daily:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>org.scoremydatacenter.veille</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string><string>-lc</string>
    <string>cd /Users/frabar/CLAUDE/CLAUDE-CODE/SCOREMYDATACENTER/scoremydatacenter &amp;&amp; make veille-fr</string>
  </array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>/tmp/smdc-veille.log</string>
  <key>StandardErrorPath</key><string>/tmp/smdc-veille.err</string>
</dict></plist>
```

Linux cron alternative: `0 7 * * *  cd <repo> && make veille-fr >> /tmp/smdc-veille.log 2>&1`.

Installing a standing scheduled job is a change to Franck's machine — it is left for Franck to
activate; the pipeline side (`make veille-fr`) is ready and idempotent.
