# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Provenance headers: insert (--fix) and verify (CI) the SPDX header on all
code files. Machine-readable, project-level copyright (never per-file
authorship — see AUTHORS), no keyword stuffing."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

HEADER = [
    "SPDX-License-Identifier: AGPL-3.0-or-later",
    "Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter",
    "https://scoremydatacenter.org · independent data center acceptability-risk score",
]

TARGETS = {
    "#": ["engine/**/*.py", "scripts/**/*.py"],
    "//": ["site/*.mjs", "site/src/**/*.astro"],
}
EXCLUDED_PARTS = {".venv", "node_modules", "dist", ".astro"}


def _files() -> list[tuple[Path, str]]:
    out = []
    for prefix, globs in TARGETS.items():
        for pattern in globs:
            for path in sorted(REPO_ROOT.glob(pattern)):
                if not EXCLUDED_PARTS.intersection(path.parts):
                    out.append((path, prefix))
    return out


def _header_block(prefix: str) -> str:
    return "".join(f"{prefix} {line}\n" for line in HEADER)


def _has_header(text: str, prefix: str) -> bool:
    return _header_block(prefix) in text[:600]


def _insert(path: Path, prefix: str) -> None:
    text = path.read_text()
    block = _header_block(prefix)
    if path.suffix == ".astro" and text.startswith("---\n"):
        text = "---\n" + block + text[len("---\n"):]
    else:
        text = block + text
    path.write_text(text)


def main() -> int:
    fix = "--fix" in sys.argv
    missing = []
    for path, prefix in _files():
        if not _has_header(path.read_text(), prefix):
            if fix:
                _insert(path, prefix)
                print(f"headers: added to {path.relative_to(REPO_ROOT)}")
            else:
                missing.append(path.relative_to(REPO_ROOT))
    if missing:
        print("headers: missing SPDX provenance header (run `make headers`):", file=sys.stderr)
        for p in missing:
            print(f"  - {p}", file=sys.stderr)
        return 1
    if not fix:
        print(f"headers: {len(_files())} file(s) carry the provenance header")
    return 0


if __name__ == "__main__":
    sys.exit(main())
