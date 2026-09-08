# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Review + demo surface for the INTERNAL validation cohort (T0b) — no scoring.

The scoring/collection rail is EU's `build_validation_cohort.py` (canonical, single source
of truth). This companion sits ON TOP of its output and owns two things:

  (a) DEMO SURFACE — a readable, non-circular readout of the sealed cohort: count, announced
      share, structural-grade distribution, firewall status. It NEVER reveals a per-project
      grade in a way that could leak; it summarises the internal exposure variable.
  (b) DEDUP AGAINST THE SERVED CORPUS — the study frame must be pipeline projects that are
      NOT already publicly graded (« en veille », A-19). EU stamps ids `study-` so id-dedup
      is moot; the real test is spatial: same ~1 km cell + same operator as a SERVED site =
      the same data center → it must not sit in the sealed cohort. Source of truth for the
      served frame is `map.geojson` (the only served surface carrying coordinates — rounded
      to 2 dp by design, so 2 dp is the honest match resolution).

    python scripts/study_review.py                       # dedup + demo on the armed cohort
    python scripts/study_review.py --snapshot <T0b.json> # explicit snapshot path
    python scripts/study_review.py --self-test           # synthetic fixture, no files needed

This REPLACES the retired `study_cohort.py` (which re-scored — redundant with EU's engine).
Non-circularity is preserved: we read EU's structural grades, we never join contestation.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root → `engine` importable

from engine.core import ARTIFACTS_DIR, DATA_DIR

# Served frame carrying coordinates. Fiches (dc/*.json) deliberately omit coords (privacy);
# map.geojson is the only served surface with geometry — and it is rounded to 2 dp.
SERVED_MAP = ARTIFACTS_DIR / "map.geojson"
MANIFEST = DATA_DIR / "validation_study_ids.json"
_DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "smdc-newsroom" / "validation"
CELL_DP = 2  # served coords are 2 dp (~1.1 km lat) — match at the served resolution, not finer
_UNKNOWN = "unknown"


# Legal-form tokens dropped before comparison so 'TelemaxX … GmbH' == 'TelemaxX …' and
# 'Acme Oy' == 'Acme'. Legal forms ONLY — no descriptor stripping (that would cause false
# positives). NB: this catches suffix variants; it does NOT catch two different DESCRIPTORS on
# the same brand (e.g. 'Hetzner Finland Oy' vs 'Hetzner Online') — that coincidence is still
# surfaced by the cell match as a SOFT flag for human review.
_LEGAL = {"gmbh", "oy", "oyj", "ab", "ltd", "limited", "sa", "sas", "sarl", "bv", "ag",
          "plc", "llc", "inc", "srl", "spa", "as", "nv", "kg", "kgaa", "se", "corp", "co"}


def _norm_op(op) -> str:
    """Operator → comparison key: lowercased, legal-form tokens dropped, alnum-joined.
    'TelemaxX Telekommunikation GmbH' == 'TelemaxX Telekommunikation'. OSM's placeholder
    ('UNKNOWN — to fill') collapses to a sentinel that never hard-matches."""
    toks = [t for t in re.split(r"[^a-z0-9]+", (op or "").lower()) if t and t not in _LEGAL]
    s = "".join(toks)
    return s if s and not s.startswith("unknown") else _UNKNOWN


def _cell(lat, lon):
    try:
        return (round(float(lat), CELL_DP), round(float(lon), CELL_DP))
    except (TypeError, ValueError):
        return None


def _served_index(map_path: Path):
    """From map.geojson → {cell: set(operator_keys)} and set(all cells). geometry = [lon, lat]."""
    by_cell: dict = {}
    cells: set = set()
    if not map_path.exists():
        return by_cell, cells
    gj = json.loads(map_path.read_text())
    for f in gj.get("features", []):
        lon, lat = (f.get("geometry", {}).get("coordinates") or [None, None])[:2]
        c = _cell(lat, lon)
        if not c:
            continue
        cells.add(c)
        by_cell.setdefault(c, set()).add(_norm_op(f.get("properties", {}).get("operator")))
    return by_cell, cells


def dedup_against_served(items: list, map_path: Path = SERVED_MAP):
    """Split study items into (clean, hard_clash, soft_flag).

    hard_clash = same 2 dp cell AND same operator as a served DC → certainly already public →
                 must leave the sealed cohort (breaks the « en veille » promise otherwise).
    soft_flag  = same cell but operator UNKNOWN on our side → probably the same site, cannot
                 confirm → surfaced for a human, NOT auto-dropped (avoid false positives in a
                 dense cluster like Frankfurt where distinct DCs share a 1 km cell)."""
    by_cell, _ = _served_index(map_path)
    clean, hard, soft = [], [], []
    for it in items:
        c = _cell(it.get("lat"), it.get("lon"))
        op = _norm_op(it.get("operator"))
        served_ops = by_cell.get(c)
        if served_ops is None:
            clean.append(it)
        elif op != _UNKNOWN and op in served_ops:
            hard.append(it)
        else:
            soft.append(it)
    return clean, hard, soft


def _real_grade_leaks(study_ids: set):
    """Mirror the CI tripwire (#187) as a demo readout: any study id served with a real grade.

    EXACT-id match only (never a bare `study-` prefix grep — watchlist.geojson carries unrelated
    `study-appealed`/`study-commission` status enums that a prefix scan would false-positive on).
    Scans the per-fiche file + the two consolidated served surfaces the tripwire watches
    (scores.json, map.geojson); watchlist.geojson is intentionally NOT scanned."""
    if not study_ids or not ARTIFACTS_DIR.exists():
        return []
    real = {"A", "B", "C", "D", "E"}
    leaks = []
    # (a) per-fiche served file
    for sid in study_ids:
        fiche = ARTIFACTS_DIR / "dc" / f"{sid}.json"
        if fiche.exists():
            g = json.loads(fiche.read_text()).get("grades", {}).get("site", {}).get("grade")
            if g in real:
                leaks.append(f"{sid}:dc.json={g}")
    # (b) scores.json — {id: {...grade...}} leaderboard rows, exact id
    sp = ARTIFACTS_DIR / "scores.json"
    if sp.exists():
        scores = json.loads(sp.read_text())
        rows = scores.values() if isinstance(scores, dict) else scores
        for row in rows:
            if isinstance(row, dict) and row.get("id") in study_ids:
                g = (row.get("grades", {}).get("site", {}) or {}).get("grade") or row.get("grade_site")
                if g in real:
                    leaks.append(f"{row['id']}:scores.json={g}")
    # (c) map.geojson — features carrying grade_site on an exact study id
    mp = ARTIFACTS_DIR / "map.geojson"
    if mp.exists():
        for f in json.loads(mp.read_text()).get("features", []):
            props = f.get("properties", {})
            if props.get("id") in study_ids and props.get("grade_site") in real:
                leaks.append(f"{props['id']}:map.geojson={props['grade_site']}")
    return leaks


def _load_snapshot(path: Path) -> dict:
    data = json.loads(path.read_text())
    # EU writes {id: item}; tolerate a bare list too.
    return data if isinstance(data, dict) else {it["id"]: it for it in data}


def apply_exclusions(exclude_ids, snapshot_path: Path, manifest_path: Path) -> None:
    """Remove an EXPLICIT, EU/R&D-validated list of true-duplicate ids from BOTH the T0b
    snapshot AND the manifest, kept in sync (desync would make the firewall see a manifest id
    with no T0b entry — so the two edits are one operation). Acts ONLY on the ids passed in —
    never on the whole `hard` bucket (a hard coincidence may be a legitimate campus expansion
    to KEEP, not a duplicate). Snapshot is a dict keyed by id; manifest keeps its `note`, ids
    stay sorted+unique."""
    ex = set(exclude_ids)
    if not ex:
        return
    snap = _load_snapshot(snapshot_path)
    snap = {k: v for k, v in snap.items() if k not in ex}
    snapshot_path.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n")
    if manifest_path.exists():
        man = json.loads(manifest_path.read_text())
        man["ids"] = sorted(set(man.get("ids", [])) - ex)
        manifest_path.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")
    print(f"  ↳ EXCLUS : {len(ex)} doublon(s) retiré(s) de T0b ET du manifeste (synchro) : {sorted(ex)}")


def apply_campus_flags(flag_ids, snapshot_path: Path) -> None:
    """Set `campus_expansion: true` on an EXPLICIT list of T0b items (a new hall on a campus
    already served publicly). These are KEPT in the cohort — the flag lets R&D run the analysis
    WITH and WITHOUT them (robustness), never an exclusion. Touches T0b only (not the manifest:
    the id stays under study)."""
    fl = set(flag_ids)
    if not fl:
        return
    snap = _load_snapshot(snapshot_path)
    n = 0
    for i in fl:
        if i in snap:
            snap[i]["campus_expansion"] = True
            n += 1
    snapshot_path.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n")
    print(f"  ↳ FLAGGÉ campus_expansion=true : {n} fiche(s) (retenues) : {sorted(fl)}")


def report(snapshot: dict, study_ids: set, map_path: Path = SERVED_MAP) -> dict:
    items = list(snapshot.values())
    # Cohorte FIGÉE = tout le T0b (rien n'est retiré au stade démo — les vrais doublons ont
    # déjà été sortis par EU en amont). Les extensions de campus sont GARDÉES + flaggées.
    campus = [it for it in items if it.get("campus_expansion")]
    greenfield = [it for it in items if not it.get("campus_expansion")]  # vue d'analyse primaire R&D
    announced = sum(1 for it in items if it.get("project_status") == "announced")
    dist: dict = {}
    for it in items:  # distribution sur la cohorte COMPLÈTE (35)
        dist[it.get("grade_site")] = dist.get(it.get("grade_site"), 0) + 1
    leaks = _real_grade_leaks(study_ids)
    # Contrôle de cohérence : la dédup ne doit plus voir de doublon NON flaggé (tous traités).
    _clean, hard, soft = dedup_against_served(items, map_path)
    unflagged_hard = [it.get("id") for it in hard if not it.get("campus_expansion")]

    bar = "─" * 62
    print(bar)
    print(" COHORTE DE VALIDATION « note = indicateur avancé » — INTERNE (T0b)")
    print(bar)
    print(f"  COHORTE (figée)                : {len(items)}   (dont annoncés : {announced})")
    print(f"    ├─ vue greenfield-primary (hors extensions campus) : {len(greenfield)}")
    print(f"    └─ vue sensibilité (toutes)                        : {len(items)}")
    print(f"  extensions de campus (gardées, campus_expansion=true) : {len(campus)}"
          + (f"  {[it.get('id') for it in campus]}" if campus else ""))
    print(f"  distribution note structurelle (cohorte complète) : "
          + ("  ".join(f"{g}:{dist[g]}" for g in 'ABCDE' if dist.get(g)) or "—"))
    print(f"  ── contrôles ({'source : map.geojson @ ' + str(CELL_DP) + ' dp'}) ──")
    print(f"  doublon SERVI non flaggé (doit être 0) : {len(unflagged_hard)}"
          + (f"  ⚠️ {unflagged_hard}" if unflagged_hard else "  ✅"))
    print(f"  à revoir (même cellule, opérateur ≠/inconnu) : {len(soft)}"
          + (f"  {[it.get('id') for it in soft]}" if soft else "   (aucun)"))
    print(f"  PARE-FEU A-19 (ids étude servis gradés) : "
          + ("⚠️  FUITE " + str(leaks[:5]) if leaks else "✅ aucun — étude hors served"))
    print(bar)
    return {"total": len(items), "campus": len(campus), "greenfield": len(greenfield),
            "soft": len(soft), "leaks": leaks, "unflagged_hard": unflagged_hard,
            "hard_ids": [it.get("id") for it in hard],
            "soft_ids": [it.get("id") for it in soft]}


def _self_test() -> int:
    """Synthetic T0b + served frame — proves dedup logic without any real file (runnable tonight)."""
    served = {"type": "FeatureCollection", "features": [
        {"geometry": {"coordinates": [8.58, 47.69]}, "properties": {"operator": "Stack Infrastructure"}},
        {"geometry": {"coordinates": [16.35, 48.19]}, "properties": {"operator": "DATASIX"}},
        {"geometry": {"coordinates": [7.60, 47.55]}, "properties": {"operator": "TelemaxX Telekommunikation"}},
    ]}
    snap = {
        "study-a": {"id": "study-a", "operator": "Stack Infrastructure", "lat": 47.693, "lon": 8.5845,
                    "project_status": "under_construction", "grade_site": "C"},   # HARD: cell+op = served
        "study-b": {"id": "study-b", "operator": "UNKNOWN — to fill", "lat": 16.353, "lon": 16.35,
                    "project_status": "announced", "grade_site": "D"},            # clean (no cell match)
        "study-c": {"id": "study-c", "operator": "UNKNOWN — to fill", "lat": 48.19, "lon": 16.35,
                    "project_status": "announced", "grade_site": "B"},            # SOFT: cell match, op unknown
        "study-d": {"id": "study-d", "operator": "GreenScale", "lat": 50.11, "lon": 8.68,
                    "project_status": "announced", "grade_site": "A"},            # clean
        "study-e": {"id": "study-e", "operator": "TelemaxX Telekommunikation GmbH", "lat": 47.553, "lon": 7.601,
                    "project_status": "under_construction", "grade_site": "C"},   # HARD via legal-suffix drop (GmbH)
    }
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".geojson", delete=False) as fh:
        json.dump(served, fh); mp = Path(fh.name)
    clean, hard, soft = dedup_against_served(list(snap.values()), mp)
    ok = True
    ok &= sorted(it["id"] for it in hard) == ["study-a", "study-e"]   # study-e = suffixe légal rattrapé
    ok &= [it["id"] for it in soft] == ["study-c"]
    ok &= sorted(it["id"] for it in clean) == ["study-b", "study-d"]
    print("self-test dédup:", "✅ PASS" if ok else "❌ FAIL",
          f"(clean={[i['id'] for i in clean]} hard={[i['id'] for i in hard]} soft={[i['id'] for i in soft]})")

    # apply_exclusions (doublon vrai study-a) : retrait synchro T0b + manifeste
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as sf:
        json.dump(snap, sf); snap_p = Path(sf.name)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as mf:
        json.dump({"note": "test", "ids": sorted(snap)}, mf)
        man_p = Path(mf.name)
    apply_exclusions(["study-a"], snap_p, man_p)
    apply_campus_flags(["study-e"], snap_p)  # extension campus : gardée + flaggée, PAS retirée du manifeste
    snap_after = json.loads(snap_p.read_text())
    man_after = json.loads(man_p.read_text())
    ok2 = ("study-a" not in snap_after and "study-a" not in man_after["ids"]  # exclu des deux
           and snap_after.get("study-e", {}).get("campus_expansion") is True   # flaggé
           and "study-e" in man_after["ids"]                                    # mais gardé au manifeste
           and man_after.get("note") == "test"                                  # champs préservés
           and set(snap_after) == {"study-b", "study-c", "study-d", "study-e"}
           and man_after["ids"] == ["study-b", "study-c", "study-d", "study-e"])
    print("self-test apply :", "✅ PASS" if ok2 else "❌ FAIL",
          f"(T0b={sorted(snap_after)} manifeste={man_after['ids']} campus_e={snap_after.get('study-e',{}).get('campus_expansion')})")
    for p in (mp, snap_p, man_p):
        p.unlink(missing_ok=True)
    return 0 if (ok and ok2) else 1


def _resolve_snapshot(arg: str | None) -> Path | None:
    if arg:
        return Path(arg)
    hits = sorted(_DEFAULT_SNAPSHOT_DIR.glob("*/baseline-scores-T0b.json"))
    return hits[-1] if hits else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Revue + démo de la cohorte de validation (T0b).")
    ap.add_argument("--snapshot", help="chemin du baseline-scores-T0b.json (sinon : dernier trouvé)")
    ap.add_argument("--manifest", help="manifeste à SYNCHRONISER avec --exclude (défaut : data/ du repo). "
                    "EU l'arme dans son worktree tant que rien n'est mergé — pointe-le là.")
    ap.add_argument("--exclude", default="", help="ids (virgule) = doublons VRAIS validés à retirer de T0b+manifeste")
    ap.add_argument("--flag-campus", dest="flag_campus", default="",
                    help="ids (virgule) = extensions de campus à marquer campus_expansion=true (retenues)")
    ap.add_argument("--apply", action="store_true",
                    help="ÉCRIT réellement --exclude / --flag-campus (sinon : dry-run, ne touche rien)")
    ap.add_argument("--self-test", action="store_true", help="fixture synthétique, sans fichier réel")
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(_self_test())
    snap_path = _resolve_snapshot(args.snapshot)
    if not snap_path or not snap_path.exists():
        raise SystemExit(f"snapshot T0b introuvable ({snap_path}) — EU le produit via build_validation_cohort.py ; "
                         "sinon : python scripts/study_review.py --self-test")
    snapshot = _load_snapshot(snap_path)
    # Les ids sous étude = les clés du T0b (source EXACTE, indépendante de l'emplacement du manifeste).
    report(snapshot, set(snapshot.keys()))

    excl = [s for s in args.exclude.split(",") if s.strip()]
    flag = [s for s in args.flag_campus.split(",") if s.strip()]
    if excl or flag:
        man_path = Path(args.manifest) if args.manifest else MANIFEST
        if args.apply:
            apply_exclusions(excl, snap_path, man_path)
            apply_campus_flags(flag, snap_path)
        else:
            if excl:
                print(f"  (dry-run) --exclude retirerait {len(excl)} fiche(s) de T0b+manifeste : {excl}")
            if flag:
                print(f"  (dry-run) --flag-campus marquerait {len(flag)} fiche(s) campus_expansion : {flag}")
            print("  → ajoute --apply pour écrire (T0b partagé + manifeste worktree EU).")
