# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root → `engine`/`pipelines` importable

from engine.core import ARTIFACTS_DIR, DATA_DIR
from pipelines.veille import dedup  # util PARTAGÉ (UNE seule vérité de dédup study_review × onboard)

# Served frame carrying coordinates. Fiches (dc/*.json) deliberately omit coords (privacy);
# map.geojson is the only served surface with geometry — and it is rounded to 2 dp.
SERVED_MAP = ARTIFACTS_DIR / "map.geojson"
MANIFEST = DATA_DIR / "validation_study_ids.json"
_DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "smdc-newsroom" / "validation"
def dedup_against_served(items: list, map_path: Path = SERVED_MAP):
    """Délègue à l'util PARTAGÉ `pipelines.veille.dedup` (UNE seule vérité study_review × onboard) :
    charge map.geojson → `served_index` → `dedup_vs_served` → (clean, hard, soft).

    Règle partagée (calée agent-API × EU) : HARD = même cellule 2 dp ET (opérateur exact post-`norm_op`
    OU 1er token de marque identique) → doublon servi certain, sort de la cohorte scellée. SOFT =
    chevauchement de marque NON-primaire → à revoir humain, jamais d'auto-drop. CLEAN = greenfield.
    ⚠️ Reclassement voulu de l'unification : « Hetzner Finland Oy » vs servi « Hetzner Online »
    (descripteur ≠, ex-SOFT en local) est désormais HARD via le 1er-token identique 'hetzner'."""
    features = json.loads(map_path.read_text()).get("features", []) if map_path.exists() else []
    return dedup.dedup_vs_served(items, dedup.served_index(features))


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
    print(f"  ── contrôles (source : map.geojson @ {dedup.CELL_DP} dp, dédup partagée) ──")
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
    """Fixture synthétique — prouve la DÉLÉGATION à l'util partagé + sa règle (sans fichier réel).
    (La règle elle-même est testée dans pipelines/veille/tests du dedup ; ici on vérifie que
    study_review batche/apply correctement via dedup.dedup_vs_served.)"""
    served = {"type": "FeatureCollection", "features": [
        {"geometry": {"coordinates": [8.58, 47.69]}, "properties": {"operator": "Stack Infrastructure"}},
        {"geometry": {"coordinates": [25.03, 60.34]}, "properties": {"operator": "Hetzner Online"}},
        {"geometry": {"coordinates": [8.68, 50.11]}, "properties": {"operator": "Digital Realty"}},
    ]}
    snap = {
        "study-exact":   {"id": "study-exact", "operator": "Stack Infrastructure", "lat": 47.693, "lon": 8.5845,
                          "project_status": "under_construction", "grade_site": "C"},  # HARD : opérateur exact
        "study-hetzner": {"id": "study-hetzner", "operator": "Hetzner Finland Oy", "lat": 60.341, "lon": 25.031,
                          "project_status": "under_construction", "grade_site": "C"},  # HARD : 1er token 'hetzner' (ex-SOFT → unifié)
        "study-soft":    {"id": "study-soft", "operator": "Global Realty", "lat": 50.111, "lon": 8.681,
                          "project_status": "announced", "grade_site": "B"},           # SOFT : overlap 'realty' non-1er
        "study-clean":   {"id": "study-clean", "operator": "GreenScale", "lat": 12.0, "lon": 12.0,
                          "project_status": "announced", "grade_site": "A"},           # CLEAN : aucune cellule servie
    }
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".geojson", delete=False) as fh:
        json.dump(served, fh); mp = Path(fh.name)
    clean, hard, soft = dedup_against_served(list(snap.values()), mp)
    ok = True
    ok &= sorted(it["id"] for it in hard) == ["study-exact", "study-hetzner"]  # Hetzner rattrapé HARD (unification)
    ok &= [it["id"] for it in soft] == ["study-soft"]
    ok &= [it["id"] for it in clean] == ["study-clean"]
    print("self-test dédup (util partagé):", "✅ PASS" if ok else "❌ FAIL",
          f"(clean={[i['id'] for i in clean]} hard={[i['id'] for i in hard]} soft={[i['id'] for i in soft]})")

    # apply_exclusions (doublon vrai) + apply_campus_flags (extension gardée + flaggée, PAS retirée du manifeste)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as sf:
        json.dump(snap, sf); snap_p = Path(sf.name)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as mf:
        json.dump({"note": "test", "ids": sorted(snap)}, mf)
        man_p = Path(mf.name)
    apply_exclusions(["study-exact"], snap_p, man_p)
    apply_campus_flags(["study-hetzner"], snap_p)
    snap_after = json.loads(snap_p.read_text())
    man_after = json.loads(man_p.read_text())
    ok2 = ("study-exact" not in snap_after and "study-exact" not in man_after["ids"]  # exclu des deux
           and snap_after.get("study-hetzner", {}).get("campus_expansion") is True    # flaggé
           and "study-hetzner" in man_after["ids"]                                     # mais gardé au manifeste
           and man_after.get("note") == "test"                                         # champs préservés
           and set(snap_after) == {"study-hetzner", "study-soft", "study-clean"}
           and man_after["ids"] == ["study-clean", "study-hetzner", "study-soft"])
    print("self-test apply :", "✅ PASS" if ok2 else "❌ FAIL",
          f"(T0b={sorted(snap_after)} manifeste={man_after['ids']} campus_e={snap_after.get('study-hetzner',{}).get('campus_expansion')})")
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
