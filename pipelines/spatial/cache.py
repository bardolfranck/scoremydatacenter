# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Cached reference files — the brick behind the "download once, join by code" collectors.

Some tier-1 signals aren't point-APIs but national reference tables (INSEE Filosofi income,
DCE ecological status). We fetch each once into a local cache and join it to the point by its
key (INSEE commune code, water-body code). The cache is content that could be rebuilt from public
sources at any time, so it is git-ignored, not committed.
"""

import urllib.request
from pathlib import Path

from .http import SourceUnavailable, USER_AGENT

CACHE_DIR = Path(__file__).resolve().parent / ".cache"


def cached_path(url: str, name: str, refresh: bool = False) -> Path:
    """Return a local path to `url`'s content, downloading it once into the cache.

    `name` is the stable filename in the cache (e.g. 'filosofi_communes.csv'). Pass refresh=True
    to force a re-download. Raises SourceUnavailable if the file is absent and cannot be fetched.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / name
    if dest.exists() and dest.stat().st_size > 0 and not refresh:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except Exception as exc:
        if dest.exists():  # keep a stale copy rather than lose the reference entirely
            return dest
        raise SourceUnavailable(f"cache fetch failed for {name}: {exc}") from exc
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return dest
