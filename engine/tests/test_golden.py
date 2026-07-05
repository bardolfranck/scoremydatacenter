"""Golden files: the artifacts generated from the committed data must be
byte-identical to the committed snapshot. This is both the non-regression net
(any scoring drift shows up as a reviewable diff) and the external
reproducibility promise ('git clone && make score' gives exactly what the site
serves) — tested on every build, in every clean CI clone."""

from pathlib import Path

from engine.artifacts import build_artifacts
from engine.core import load_datacenters, load_methodology

GOLDEN = Path(__file__).parent / "golden"


def test_artifacts_match_golden_snapshot(tmp_path):
    build_artifacts(load_datacenters(), load_methodology(), out_dir=tmp_path)

    generated = {p.relative_to(tmp_path).as_posix(): p for p in tmp_path.rglob("*.json")}
    generated |= {p.relative_to(tmp_path).as_posix(): p for p in tmp_path.rglob("*.geojson")}
    golden = {p.relative_to(GOLDEN).as_posix(): p for p in GOLDEN.rglob("*.json")}
    golden |= {p.relative_to(GOLDEN).as_posix(): p for p in GOLDEN.rglob("*.geojson")}

    assert sorted(generated) == sorted(golden), "artifact file set changed — regenerate the golden snapshot deliberately"
    for rel, path in sorted(generated.items()):
        assert path.read_bytes() == golden[rel].read_bytes(), (
            f"{rel} drifted from the golden snapshot — if intentional, regenerate golden and review the diff"
        )


def test_build_is_deterministic(tmp_path):
    build_artifacts(load_datacenters(), load_methodology(), out_dir=tmp_path / "a")
    build_artifacts(load_datacenters(), load_methodology(), out_dir=tmp_path / "b")
    for pa in sorted((tmp_path / "a").rglob("*")):
        if pa.is_file():
            pb = tmp_path / "b" / pa.relative_to(tmp_path / "a")
            assert pa.read_bytes() == pb.read_bytes()
