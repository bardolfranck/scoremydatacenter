import json
import shutil
from pathlib import Path

import pytest

from engine.core import DATA_DIR, load_json, load_methodology


@pytest.fixture(scope="session")
def methodology():
    return load_methodology()


@pytest.fixture(scope="session")
def parameters(methodology):
    return methodology["parameters"]


@pytest.fixture()
def alpha():
    return load_json(DATA_DIR / "datacenters" / "zz-test-alpha.json")


@pytest.fixture()
def beta():
    return load_json(DATA_DIR / "datacenters" / "zz-test-beta.json")


@pytest.fixture()
def data_copy(tmp_path):
    """Mutable copy of data/ for gate tests. Returns (dir, edit) where edit(relpath, fn)
    loads a JSON file, applies fn, and writes it back."""
    target = tmp_path / "data"
    shutil.copytree(DATA_DIR, target)

    def edit(relpath: str, fn):
        p = target / relpath
        doc = json.loads(p.read_text())
        fn(doc)
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    return target, edit


def indicator(dc: dict, indicator_id: str) -> dict:
    return next(e for e in dc["indicators"] if e["id"] == indicator_id)
