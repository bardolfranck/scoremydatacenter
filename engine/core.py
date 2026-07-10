# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Shared paths, loading and deterministic serialization.

Everything the engine writes must be byte-for-byte reproducible from the
repository content alone (external reproducibility promise): no timestamps,
no environment-dependent values in artifacts.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
ARTIFACTS_DIR = REPO_ROOT / "site" / "public" / "data"

FICTIONAL_PREFIX = "zz-"


class GateError(Exception):
    """A blocking build-gate violation. The message must say which gate and how to fix."""


def load_json(path: Path):
    return json.loads(Path(path).read_text())


def dump_json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(data))


def methodology_path(data_dir: Path = DATA_DIR) -> Path:
    files = sorted((data_dir / "methodology").glob("v*.json"))
    if len(files) != 1:
        raise GateError(
            f"GATE 5: expected exactly one active methodology file in data/methodology/, found {len(files)}: "
            f"{[f.name for f in files]}. Archive superseded versions outside the glob or keep one."
        )
    return files[0]


def load_methodology(data_dir: Path = DATA_DIR) -> dict:
    return load_json(methodology_path(data_dir))


# Every country panel is scored, not just the default one: source DCs live in
# `datacenters/` plus any per-country sibling (`datacenters-be/`, …). Reading a
# single dir silently dropped whole countries from map.geojson/scores.json on
# every rebuild. Auxiliary drafting files (.provenance/.draft/.governance) sit
# next to the DCs in some panels and are not scored.
_AUX_SUFFIXES = (".provenance.json", ".draft.json", ".governance.json")


def datacenter_paths(data_dir: Path = DATA_DIR) -> list[Path]:
    paths = [
        p
        for d in sorted(data_dir.glob("datacenters*")) if d.is_dir()
        for p in d.glob("*.json")
        if not p.name.endswith(_AUX_SUFFIXES)
    ]
    return sorted(paths, key=lambda p: p.stem)


def load_datacenters(data_dir: Path = DATA_DIR) -> dict[str, dict]:
    return {p.stem: load_json(p) for p in datacenter_paths(data_dir)}


def watchlist_paths(data_dir: Path = DATA_DIR) -> list[Path]:
    return sorted((data_dir / "watchlist").glob("*.json"))


def load_watchlist(data_dir: Path = DATA_DIR) -> list[dict]:
    """Flatten every watchlist file (each file is an array of 'En veille' entries, A-19)."""
    entries: list[dict] = []
    for p in watchlist_paths(data_dir):
        entries.extend(load_json(p))
    return entries
