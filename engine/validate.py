"""Build gates (ARCHITECTURE section 6.3) — every failure names its gate and its fix.

Gate 1  JSON Schema validation of all data files.
Gate 2  Announced vs measured never merged: an indicator that the methodology
        declares 'declarative' can only be measured with verification evidence.
Gate 3  Methodology coherence: threshold traceability (schema), weights sum to 1,
        unique ids, direction contract, declared-but-unenforced ethical
        constraints cannot claim 'calibrated'.
Gate 4  Contradictory review: the public repo only holds published DCs, and
        published requires operator notification >= 15 days old.
Gate 5  Methodology anteriority: exactly one active version; a real (non-zz)
        DC cannot be scored against a draft methodology; score_history entries
        must reference the current version.
Gate 6  Retrospective fixtures + transparency floor: enforced by the test
        suite (make test), which CI runs before make build.
Gate 7  No grade rendered outside <ScoreBadge>: template lint, arrives with
        the site components (plan phase 2).
Journal gate: every score_history entry after the first carries a rationale.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .core import DATA_DIR, FICTIONAL_PREFIX, GateError, load_json, load_methodology, datacenter_paths

NOTICE_DAYS = 15


def _schema_errors(instance, schema, label: str) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"GATE 1: {label}: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(instance), key=str)
    ]


def run_gates(data_dir: Path = DATA_DIR, today: date | None = None) -> list[str]:
    """Return the list of gate violations (empty = all gates pass)."""
    today = today or date.today()
    problems: list[str] = []

    dc_schema = load_json(data_dir / "schema" / "datacenter.schema.json")
    meth_schema = load_json(data_dir / "schema" / "methodology.schema.json")

    try:
        methodology = load_methodology(data_dir)
    except GateError as e:
        return [str(e)]

    problems += _schema_errors(methodology, meth_schema, "methodology")
    if problems:
        return problems  # structural failures make the rest unreliable

    # Gate 3 — cross-field methodology coherence
    indicators = methodology["indicators"]
    ids = [i["id"] for i in indicators]
    if len(ids) != len(set(ids)):
        problems.append("GATE 3: duplicate indicator ids in methodology")
    if abs(sum(p["weight"] for p in methodology["pillars"]) - 1.0) > 1e-9:
        problems.append("GATE 3: pillar weights do not sum to 1")
    for pillar in methodology["pillars"]:
        s = sum(i["weight_in_pillar"] for i in indicators if i["pillar"] == pillar["id"])
        if abs(s - 1.0) > 1e-9:
            problems.append(f"GATE 3: indicator weights in pillar {pillar['id']} sum to {s}, not 1")
    pillar_ids = {p["id"] for p in methodology["pillars"]}
    for ind in indicators:
        if ind["pillar"] not in pillar_ids:
            problems.append(f"GATE 3: indicator {ind['id']} references unknown pillar {ind['pillar']}")
        if "vulnerability_cannot_improve_score" in ind.get("constraints", []):
            # Ethical lock, executable (methodology-lead rule 2026-07-05): scores must be
            # non-increasing along the declared vulnerability order — vulnerability may
            # lower a score or dent confidence, never raise it. A corpus property test
            # (test_ethical_constraints.py) additionally checks d(site_score)/d(vulnerability) <= 0.
            order = ind.get("vulnerability_order", [])
            categories = ind.get("normalization", {}).get("categories")
            if categories is None:
                problems.append(
                    f"GATE 3: indicator {ind['id']}: vulnerability_cannot_improve_score requires a "
                    "categorical normalization"
                )
            elif sorted(order) != sorted(categories):
                problems.append(
                    f"GATE 3: indicator {ind['id']}: vulnerability_order {order} must cover exactly "
                    f"the normalization categories {sorted(categories)}"
                )
            else:
                scores = [categories[c] for c in order]
                if any(a < b for a, b in zip(scores, scores[1:])):
                    problems.append(
                        f"GATE 3: indicator {ind['id']}: ethical lock violated — scores along the "
                        f"vulnerability order {order} are {scores}, but a more vulnerable profile can "
                        "never score higher (vulnerability_cannot_improve_score, framing note section 9)"
                    )
    declarative_ids = {i["id"] for i in indicators if i["nature"] == "declarative"}

    for path in datacenter_paths(data_dir):
        dc = load_json(path)
        label = path.name
        errs = _schema_errors(dc, dc_schema, label)
        problems += errs
        if errs:
            continue

        if dc["id"] != path.stem:
            problems.append(f"GATE 1: {label}: id {dc['id']!r} does not match the filename")

        # every methodology indicator must appear exactly once (missing is declared, never implicit)
        seen = [e["id"] for e in dc["indicators"]]
        if sorted(seen) != sorted(ids):
            problems.append(
                f"GATE 1: {label}: indicator set differs from methodology "
                f"(missing={sorted(set(ids) - set(seen))}, extra={sorted(set(seen) - set(ids))}) — "
                "declare unavailable indicators explicitly with status: missing"
            )
            continue

        # Gate 2 — declarative never silently measured
        for e in dc["indicators"]:
            if e["id"] in declarative_ids and e["status"] == "measured" and "verification_source" not in e:
                problems.append(
                    f"GATE 2: {label}: {e['id']} is declarative but marked 'measured' without "
                    "verification_source — announced and measured are never merged"
                )

        # Gate 4 — contradictory review
        pub = dc["publication"]
        if pub["status"] != "published":
            problems.append(
                f"GATE 4: {label}: publication.status is {pub['status']!r} — the public repo only holds "
                "published DCs; drafts live in smdc-newsroom"
            )
        elif date.fromisoformat(pub["operator_notified_at"]) + timedelta(days=NOTICE_DAYS) > today:
            problems.append(
                f"GATE 4: {label}: operator notified on {pub['operator_notified_at']} — "
                f"{NOTICE_DAYS} days of contradictory review are not over yet"
            )

        # Gate 5 — anteriority
        if not dc["id"].startswith(FICTIONAL_PREFIX) and methodology["status"] != "published":
            problems.append(
                f"GATE 5: {label}: a real data center cannot be scored against a {methodology['status']} "
                "methodology — freeze and tag v0.1.0 first (plan phase 5)"
            )
        for n, entry in enumerate(dc["score_history"]):
            if entry["methodology_version"] != methodology["version"]:
                problems.append(
                    f"GATE 5: {label}: score_history[{n}] references methodology "
                    f"{entry['methodology_version']} but the active version is {methodology['version']} — "
                    "record a methodology_change re-score (make rescore)"
                )
            # journal gate
            if n >= 1 and not entry.get("rationale"):
                problems.append(
                    f"JOURNAL GATE: {label}: score_history[{n}] has no rationale — every revision "
                    "after the initial scoring must say why the grade moved"
                )

    return problems


def main() -> int:
    problems = run_gates()
    n_dc = len(datacenter_paths())
    if problems:
        print(f"validate: {len(problems)} gate violation(s) across {n_dc} datacenter file(s):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"validate: all gates pass ({n_dc} datacenter file(s), methodology {load_methodology()['version']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
