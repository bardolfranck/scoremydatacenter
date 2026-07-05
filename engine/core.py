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


def datacenter_paths(data_dir: Path = DATA_DIR) -> list[Path]:
    return sorted((data_dir / "datacenters").glob("*.json"))


def load_datacenters(data_dir: Path = DATA_DIR) -> dict[str, dict]:
    return {p.stem: load_json(p) for p in datacenter_paths(data_dir)}
