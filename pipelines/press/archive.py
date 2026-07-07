# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Durable third-party snapshots via the Internet Archive (A-20).

`archive_url(url)` triggers an Internet Archive "Save Page Now" capture and returns the resulting
snapshot URL — or, if the capture can't be made, the closest existing snapshot — or None. It is
**best-effort**: it never raises and never blocks a draft. An archived copy is *evidence for a
human reader*, not a scoring input (the engine scores from the value alone, so the public repo
stays reproducible — A-20 / P6). We let a neutral third party host the bytes and only keep the
pointer, which is exactly what keeps copyrighted press linkable without redistributing it.

Only specific, rot-prone public *pages* are worth pinning here (a CNDP debate fiche, an official
avis PDF). Open-data point-APIs are NOT archived — they are re-fetchable and time-varying, so a
snapshot of "the current value" would be meaningless (A-20: link, don't copy).
"""

import json
import urllib.parse
import urllib.request

from pipelines.spatial.http import USER_AGENT

_SAVE = "https://web.archive.org/save/"
_AVAILABLE = "https://archive.org/wayback/available"
_TIMEOUT = 30


def _open(url: str, timeout: int):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=timeout)


def _https(url: str) -> str:
    return url.replace("http://", "https://", 1) if url.startswith("http://") else url


def _save_now(url: str, timeout: int) -> str | None:
    """Trigger a fresh capture; return the new snapshot URL from the response, or None."""
    try:
        with _open(_SAVE + url, timeout) as resp:
            location = resp.headers.get("Content-Location") or ""
            if "/web/" in location:
                return "https://web.archive.org" + location
            final = resp.geturl() or ""
            if "/web/" in final:
                return _https(final)
    except Exception:
        return None
    return None


def _closest_snapshot(url: str, timeout: int) -> str | None:
    """Fallback: the newest snapshot the Wayback availability API already knows, or None."""
    try:
        query = _AVAILABLE + "?" + urllib.parse.urlencode({"url": url})
        with _open(query, timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
    except Exception:
        return None
    closest = ((data.get("archived_snapshots") or {}).get("closest")) or {}
    snap = closest.get("url")
    return _https(snap) if snap and closest.get("available") else None


def archive_url(url: str | None, *, timeout: int = _TIMEOUT) -> str | None:
    """Best-effort durable snapshot URL for `url`: fresh capture, else existing, else None."""
    if not url:
        return None
    return _save_now(url, timeout) or _closest_snapshot(url, timeout)
