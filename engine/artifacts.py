# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Generated artifacts — the data contract of the site (and of the future API).

Deterministic by construction: no timestamps, no environment values. The same
repository content always produces byte-identical artifacts (this is tested).
"""

import re
from pathlib import Path

from .core import ARTIFACTS_DIR, GateError, load_watchlist, write_json

# A-28: the credit travels WITH the data — every object artifact carries it
# (scores.json/audit.json are arrays: adding a key would break consumers;
# the site footer and the fiche pages carry the credit for those).
CREDIT = "scoremydatacenter.org · data: licence by source (ODbL, Licence Ouverte…) · methodology CC BY-SA 4.0"
from .scoring import score_datacenter
from .stats import build_stats
from .indices import build_indices, update_history
from .showcase import build_showcase
# Provisional coverage band for PIPELINE fiches (product: announced/permitting/under_construction
# -> band « en veille, provisoire » ; operational -> definitive letter, no band). servable_band is
# the ONE gate (firewall test_plage_bands_firewall): operational -> None, so a band can never touch
# an operational fiche's definitive grade. Written to a SEPARATE `provisional_band` field, never grades.
from .plage_bands import build_reference_pool, servable_band, base_definitions

# Gate 7 extended to generated prose (2026-07-10): a grade must never be rendered
# outside <ScoreBadge> — including inside the LLM-written synthesis. Prose citing a
# letter duplicates computed state and is guaranteed to drift at the next methodology
# revision (seen live: an accroche pinned at "site C, piliers D" rendered next to
# recomputed badges saying D and E). The letter belongs to the badge; the prose
# carries the *why*, never the letter.
_GRADE_IN_PROSE = re.compile(
    r"(?:\bnote\b[^.!?]{0,80}?|\bnoté[e]?s?\s+|\bpilier[s]?\b[^.!?]{0,80}?|\bgrade[sd]?\b[^.!?]{0,40}?"
    r"|\brated\s+|\bpillar[s]?\b[^.!?]{0,80}?|\bscored?\s+)(?<![A-Za-zÀ-ÿ])([A-E])(?![A-Za-zÀ-ÿ0-9+])"
)


def synthesis_grade_citations(dc: dict) -> list[str]:
    """Return every grade-letter citation found in the DC's synthesis prose."""
    hits = []
    for badge, texts in (dc.get("synthesis") or {}).items():
        if not isinstance(texts, dict):
            continue
        for lang, text in texts.items():
            # `lead` is per-language now ({fr,en}); flatten one nested level so a grade letter in a
            # localized title is caught, not skipped. Body fields stay plain strings.
            fields = text.items() if isinstance(text, dict) else [(lang, text)]
            for sublang, value in fields:
                if not isinstance(value, str):
                    continue
                for m in _GRADE_IN_PROSE.finditer(value):
                    hits.append(f"{dc['id']}: synthesis.{badge}.{sublang} cites grade "
                                f"{m.group(1)!r} in prose ({m.group(0)!r})")
    return hits


def _summary(dc: dict, result: dict) -> dict:
    identity = dc["identity"]
    pub = dc.get("publication") or {}
    return {
        "id": dc["id"],
        "name": identity["name"],
        "operator": identity["operator"],
        "municipality": identity["municipality"],
        "country": identity["country"],
        "project_status": identity["project_status"],
        # First-recorded date (git first-commit of the newsroom fiche; null until backfilled).
        # Powers a « derniers scorés » banner; a date, never a grade date.
        "first_seen": identity.get("first_seen"),
        "power_mw": identity.get("power_mw"),
        # Consumer contract (agent-site): the fiche/ranking renders "~X MW · estimé" on this
        # enum (measured | announced | estimated); null = legacy fill, undisclosed provenance.
        "power_mw_status": identity.get("power_mw_status"),
        # commissioning year (identity.vintage) — the ranking sorts on it; null = not disclosed
        "expected_commissioning": (identity.get("vintage") or {}).get("expected_commissioning"),
        "grades": result["grades"],
        "confidence": result["confidence"],
        "pillars": result["pillars"],
        "citable_quote": result["citable_quote"],
        # Direct publication (2026-07-15, legal review): lifecycle is draft -> published.
        "publication_status": pub.get("status"),
    }


# « CE QUI PÈSE LE PLUS ICI » — CALCULÉ, JAMAIS RÉDIGÉ.
#
# Le lecteur non spécialiste voit une lettre et ne sait pas ce qui la tire. On expose donc le
# HAUT du classement des contributions, en un seul indicateur, et le site en fait une phrase.
# Le moteur rend un ID et une PART, jamais des mots : la copie reste côté site, la dérivation
# reste ici.
#
# POURQUOI CALCULÉ ET NON RÉDIGÉ : c'est le quatrième dérivé du point, après la note, la carte
# et la prose. Les trois premiers ont déjà montré ce que coûte une explication STOCKÉE — 167
# synthèses servies affirmaient une absence que la valeur contredisait, parce qu'elles avaient
# été écrites puis gardées pendant que la mesure changeait sous elles. Un classement se
# recalcule à chaque build : il ne peut pas périmer, et n'a donc pas besoin d'un gate.
#
# CE QU'ON NE DIT PAS, ET C'EST LE POINT DÉLICAT : jamais la DISTANCE au seuil. Et pas
# seulement dans le texte — la SÉLECTION fuit autant. Si la phrase n'apparaissait que sur les
# fiches proches d'une bascule, sa présence serait elle-même la mesure de l'écart, et sur
# 1565 fiches elle localiserait les seuils. Elle s'affiche donc sur TOUTE fiche qui a la
# matière, indépendamment de la note et de la position dans l'échelle (arbitrage avec R&D,
# 2026-10-07).
_PART_MINIMALE_PAYS = 20  # fiches

def dominant_drag(result: dict, methodology: dict) -> str | None:
    """L'indicateur qui pèse le plus sur la note de ce site, ou None si la fiche est trop mince.

    Pèse = importance × manque, soit (poids_pilier × poids_dans_pilier × poids_tier) × (100 − score).
    C'est le même produit que celui qui construit la note : on n'invente pas une seconde
    hiérarchie à côté de l'agrégat, on en lit le premier rang.

    Rend None quand le dominant est de tier 2 ou 3. Mesuré : une seule fiche du corpus a un
    tier 2 en tête (E6, raccordabilité à un réseau de chaleur) — elle gagne faute de concurrents
    mesurés, pas parce qu'elle pèse. Publier « ce qui pèse le plus ici, c'est l'absence de réseau
    de chaleur » serait vrai arithmétiquement et faux au sens commun : une phrase pareille coûte
    plus en crédibilité qu'elle n'apporte en information. Le critère est la MATIÈRE de la fiche,
    jamais sa position dans l'échelle — sinon on retombe dans la fuite par sélection.
    """
    poids_pilier = {p["id"]: p["weight"] for p in methodology["pillars"]}
    poids_tier = {str(k): v for k, v in methodology["confidence"]["tier_weights"].items()}
    classement = []
    for d in methodology["indicators"]:
        score = result["indicators"].get(d["id"])
        if not isinstance(score, (int, float)):
            continue
        importance = (poids_pilier.get(d["pillar"], 0)
                      * d.get("weight_in_pillar", 0)
                      * poids_tier.get(str(d.get("tier", 1)), 1.0))
        if importance <= 0:
            continue
        classement.append((importance * (100 - score), d.get("tier", 1), d["id"]))
    if not classement:
        return None
    _, tier, iid = max(classement)
    return iid if tier == 1 else None


def drag_fields(results: dict[str, dict], datacenters: dict[str, dict],
                methodology: dict) -> dict[str, dict]:
    """Par fiche : {indicator, country, country_share?}. Un pays mince n'a PAS de part.

    La part dit « comme pour 83 % des sites français ». Elle retourne une limite en
    information : le facteur dominant est quasi constant à l'intérieur d'un pays (mesuré :
    FR 83 % sur E2, IE 92 %, IL 100 % ; DE et GB les plus variés à 39 % et 45 %), donc l'élu
    qui lit SA fiche lirait la même phrase que ses voisins. Le dire explicitement transforme
    la redondance en la chose la plus utile pour lui : la contrainte est SYSTÉMIQUE, elle
    n'est pas le fait de ce projet-là. Elle ne révèle rien des seuils — c'est la distribution
    des faiblesses par pays, pas la position des bascules.

    Sous `_PART_MINIMALE_PAYS` fiches, on sert le facteur SANS la part : « comme pour 89 % des
    sites portugais » reposerait sur huit fiches, soit le même voisinage fabriqué par la
    minceur que le comparateur signale déjà. (J'avais d'abord voulu réutiliser le seuil du
    comparateur ; il dérive d'un tout autre raisonnement — deux voisins minimum sous 15 % du
    pays — et partager une constante parce que sa valeur coïncide aurait créé une dépendance
    fausse.)
    """
    dominants = {dc_id: dominant_drag(r, methodology) for dc_id, r in results.items()}
    pays = {dc_id: datacenters[dc_id]["identity"].get("country") for dc_id in results}
    total, par_facteur = {}, {}
    for dc_id, iid in dominants.items():
        cc = pays[dc_id]
        total[cc] = total.get(cc, 0) + 1
        if iid:
            par_facteur[(cc, iid)] = par_facteur.get((cc, iid), 0) + 1
    out = {}
    for dc_id, iid in dominants.items():
        if not iid:
            continue
        cc = pays[dc_id]
        champ = {"indicator": iid, "country": cc}
        if total.get(cc, 0) >= _PART_MINIMALE_PAYS:
            champ["country_share"] = round(par_facteur[(cc, iid)] / total[cc], 3)
        out[dc_id] = champ
    return out


def _watchlist_kind(entry: dict) -> str:
    """Feature-level marker kind, derived from the entry's facts (facts stay untouched).

    moratorium (official act) > opposition (citizen/legal contestation) > announced_project
    (bare listing). A legal `appeal` is a contestation signal — it maps to the opposition
    marker, not to the neutral "just announced" pin.
    """
    kinds = {f.get("kind") for f in (entry.get("facts") or [])}
    if "moratorium" in kinds:
        return "moratorium"
    if kinds & {"opposition", "appeal", "petition"}:
        return "opposition"
    return "announced_project"


def build_artifacts(datacenters: dict[str, dict], methodology: dict,
                    out_dir: Path = ARTIFACTS_DIR, watchlist: list[dict] | None = None) -> dict[str, dict]:
    """Score every DC and write all artifacts. Returns the per-DC results."""
    if watchlist is None:
        watchlist = load_watchlist()
    # Gate 7 (prose): refuse to emit an artifact whose synthesis cites grade letters —
    # the incoherent "stale letter next to a recomputed badge" state is impossible.
    prose_violations = [v for dc in datacenters.values() for v in synthesis_grade_citations(dc)]
    if prose_violations:
        raise GateError(
            "GATE 7 (prose): a grade letter is never rendered outside <ScoreBadge> — strip it "
            "from the synthesis (the badge carries the letter, the prose carries the why):\n  - "
            + "\n  - ".join(prose_violations)
        )
    results = {dc_id: score_datacenter(dc, methodology) for dc_id, dc in sorted(datacenters.items())}

    # Provisional coverage bands (deterministic): reference pool = every scored fiche's present
    # BASE sub-scores; the band tightens against it. servable_band gates it to pipeline fiches only.
    base_ids = [d["id"] for d in base_definitions(methodology)]
    drags = drag_fields(results, datacenters, methodology)

    def _present(dc_id: str) -> dict:
        ind = results[dc_id]["indicators"]
        return {i: ind[i] for i in base_ids if ind.get(i) is not None}

    band_pool = build_reference_pool(
        {"country": dc["identity"]["country"], "present": _present(dc_id)}
        for dc_id, dc in sorted(datacenters.items())
    )

    def _provisional_band(dc_id: str, dc: dict):
        return servable_band(
            dc["identity"]["project_status"], _present(dc_id), dc["identity"]["country"],
            methodology, band_pool, confidence=results[dc_id]["confidence"]["level"],
        )

    labels = {i["id"]: i["label"] for i in methodology["indicators"]}
    scores, features, audit = [], [], []

    for dc_id, dc in sorted(datacenters.items()):
        result = results[dc_id]
        band = _provisional_band(dc_id, dc)  # None for operational fiches (never a band)
        band_field = {"provisional_band": band} if band else {}
        # scores.json is a leaderboard array consumed by strict readers — the band lives on
        # the per-fiche dc/{id}.json (the loupe's source), not here, until asked otherwise.
        scores.append(_summary(dc, result))

        # ── Anti-pillage (Franck 2026-07-22): map.geojson is the ONE data file
        # the site MUST serve publicly (the map fetches it client-side), so it
        # is the paywall's real frontier. It carries ONLY the free "Seau A"
        # floor — the identity + the site LETTER — and NOTHING sellable. Dropped
        # here (premium, Seau B, sold via the API): operator grade, per-pillar
        # scores, exact power_mw, the citable quote, confidence, precise GPS.
        # Coordinates are rounded to ~1 km (2 decimals); a coarse size_tier
        # keeps the map's dot-sizing without disclosing the MW figure.
        coords = dc["identity"]["coordinates"]
        mw = dc["identity"].get("power_mw")
        size_tier = 0 if not isinstance(mw, (int, float)) else (1 if mw < 10 else 2 if mw < 50 else 3)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(coords["lon"], 2), round(coords["lat"], 2)],
            },
            "properties": {
                "id": dc_id,
                "name": dc["identity"]["name"],
                "operator": dc["identity"]["operator"],
                "municipality": dc["identity"]["municipality"],
                "country": dc["identity"]["country"],
                "grade_site": result["grades"]["site"]["grade"],
                # A-25 reserve is part of the public letter's presentation, not a sold field.
                **({"reserved_site": True} if result["grades"]["site"].get("reserved_from") == "A" else {}),
                "project_status": dc["identity"]["project_status"],
                "size_tier": size_tier,
                # First-recorded date (identity.first_seen) so a « derniers SCORÉS » banner can sort
                # by recency (Phase-1). A DATE, never a grade date; null until backfilled (git first-
                # commit of the newsroom fiche — see scripts/backfill_first_seen.py, gated on Franck).
                "first_seen": dc["identity"].get("first_seen"),
            },
        })

        indicator_detail = []
        entries = {e["id"]: e for e in dc["indicators"]}
        for ind in methodology["indicators"]:
            if not ind["mvp"]:
                continue
            entry = entries[ind["id"]]
            indicator_detail.append({
                "id": ind["id"],
                "label": labels[ind["id"]],
                "pillar": ind["pillar"],
                "block": ind["block"],
                "status": entry["status"],
                "value": entry.get("value"),
                "proxies": entry.get("proxies"),
                "score": result["indicators"][ind["id"]],
                "source": entry.get("source"),
                "verification_source": entry.get("verification_source"),
            })

        write_json(out_dir / "dc" / f"{dc_id}.json", {
            "credit": CREDIT,
            **_summary(dc, result),
            # Provisional coverage band — present ONLY on pipeline fiches, in its own field,
            # never inside `grades`. Its `central`/`adjacent` letters are a provisional RANGE,
            # not a definitive grade (loupe display contract; ScoreBadge reads this).
            **band_field,
            "summary": dc["identity"]["summary"],
            "vintage": dc["identity"].get("vintage"),
            "admin_area": dc["identity"].get("admin_area"),
            "indicators": indicator_detail,
            # « Ce qui pèse le plus ici » : l'id du facteur dominant + sa part dans le pays.
            # Calculé à chaque build depuis le classement des contributions — jamais stocké,
            # donc jamais périmé. Absent quand la fiche est trop mince (voir dominant_drag).
            **({"dominant_drag": drags[dc_id]} if dc_id in drags else {}),
            "publication": dc["publication"],
            "score_history": dc["score_history"],
            # Contestation signal (A-21): sourced facts published next to the note,
            # never an input to the grade. Passed through untouched.
            "contestation": dc.get("contestation"),
            # Narrative synthesis: written by the WORKFLOW's LLM redaction phase
            # AFTER scoring, then stored on the source DC. The engine only passes
            # it through — never computed at render, never re-derived here.
            "synthesis": dc.get("synthesis"),
        })

        audit += [{"dc_id": dc_id, "dc_name": dc["identity"]["name"], **event} for event in dc["score_history"]]

    # Watchlist (A-19): world "En veille" projects — sourced facts, NO grade.
    # The engine never scores these; it only passes the facts through to the map.
    # Un fait suivi n'a pas toujours un LIEU. Cas fondateur : le cloud fédéré de Cannes —
    # capacité répartie, aucune installation à pointer. Lui inventer un point l'aurait
    # épinglé sur la carte à un endroit qui n'existe pas, soit exactement le défaut qu'on
    # corrige ailleurs. Une entrée sans coordonnées reste donc suivie, mais n'entre pas
    # dans la couche cartographique.
    watch_features = [{
        "type": "Feature",
        # Coords rounded to ~1 km like the graded layer (no precise GPS in a public file).
        "geometry": {"type": "Point", "coordinates": [round(e["coordinates"]["lon"], 2), round(e["coordinates"]["lat"], 2)]},
        "properties": {
            "id": e["id"],
            "name": e["name"],
            "operator": e.get("operator"),
            "municipality": e.get("municipality"),
            "country": e["country"],
            "project_status": e.get("project_status"),
            "watchlist_status": "en_veille",
            # Detection date = when the project was first sourced/listed (entry-level source).
            # Powers the « derniers projets repérés » banner (Phase-1 site vivant): the served
            # projection had no date, so sorting « latest » was impossible. This is a FACT date,
            # never a grade date (A-19: an en-veille entry is never graded).
            "detected_at": (e.get("source") or {}).get("accessed"),
            # Derived marker kind so the map can style flat (styling on the nested facts[]
            # array is impractical in MapLibre expressions). A moratorium is an OFFICIAL act —
            # it outranks an opposition signal when an entry carries both. Never a grade.
            "kind": _watchlist_kind(e),
            "source": e["source"],
            "facts": e.get("facts") or [],
        },
    } for e in watchlist if e.get("coordinates")]

    write_json(out_dir / "scores.json", scores)
    # T0 « Les chiffres du parc » — corpus aggregates, one file per build
    # (cadrage §4.10). Data only: labels and editorial framing live site-side.
    write_json(out_dir / "stats.json", build_stats(datacenters, methodology, watchlist, results))
    # Country SITE index (brief 2026-07-18/19): artifact + append-only history.
    indices = build_indices(datacenters, methodology, results)
    write_json(out_dir / "indices.json", indices)
    write_json(out_dir / "indices_history.json", update_history(indices, out_dir / "indices_history.json"))
    # Home showcase (2026-07-20): who appears on the front page is a RULE,
    # not an accident of filtering — the engine ranks, the site renders.
    write_json(out_dir / "home_showcase.json", build_showcase(datacenters, results, watchlist))
    write_json(out_dir / "map.geojson", {"type": "FeatureCollection", "credit": CREDIT, "features": features})
    write_json(out_dir / "watchlist.geojson", {"type": "FeatureCollection", "credit": CREDIT, "features": watch_features})
    write_json(out_dir / "audit.json", sorted(audit, key=lambda e: (e["date"], e["dc_id"])))
    write_json(out_dir / "methodology.json", methodology)
    return results
