# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Détecteur de géo FABRIQUÉE : la coordonnée d'une fiche = un géocodage de NOM de commune ?

Ce qu'on traque n'est pas « la coordonnée est-elle au barycentre géométrique de la commune »,
c'est « quelqu'un a-t-il géocodé un nom de commune au lieu de localiser un site ». L'outil qui
produit ce genre de coordonnée est un GÉOCODEUR. On teste donc la coordonnée contre la réponse
des géocodeurs eux-mêmes — plus proche du défaut réel qu'un centroïde théorique jamais calculé.

DEUX ORACLES, un match sur l'un OU l'autre lève le drapeau :
  · geo.api.gouv.fr — le `centre` INSEE de la commune (France ; c'est ce que notre pipeline FR
    utilise, donc une géo fabriquée par notre pipeline y matche : cas Fouju) ;
  · Nominatim — géocodeur le plus courant ; une fiche importée d'un annuaire aura matché LUI,
    pas l'INSEE. Vaut partout dans le monde.

CRITÈRE COMBINÉ (le vrai livrable, pas le seuil brut) : près d'un oracle (< 150 m) ET la
coordonnée n'est PAS sur un bâtiment réel (off_building / no_building dans on-building.json).
Le test bâtiment élimine le bruit — un vrai DC dans une petite commune dense tombe près du
centroïde mais SUR un bâtiment (cas des faux positifs FR : Marcq-en-Barœul 19,7 m, etc.).

    python -m pipelines.geo_audit.centroid_check            # France (2 oracles)
    python -m pipelines.geo_audit.centroid_check --world    # monde entier

MESURE DEHORS, DÉCISION DEDANS : ce module fait la MESURE (réseau) et écrit le sidecar
`centroid-check.json` ; le GATE (engine.validate._geo_gate) LIT le sidecar et refuse, sans
réseau. Interne newsroom — jamais dans le build public.

RECONSTRUIT le 2026-10-02 à partir du bytecode orphelin (source perdue, sidecar du 2026-09-29
produit par un script non commité) : même méthode, même schéma de sortie, rendu REJOUABLE —
cf. [[figer-par-test-revele-les-fantomes]], c'était la 4ᵉ commande fantôme du chantier.
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]                 # …/scoremydatacenter
NEWSROOM = REPO.parent / "smdc-newsroom" / "calibration"   # dépôt privé voisin
OUT = NEWSROOM / "geo-audit" / "centroid-check.json"
ONBUILDING = NEWSROOM / "geo-audit" / "on-building.json"
CACHE = REPO / ".media-sat" / "centroid-cache.json"        # gitignored, politesse réseau

UA = "ScoreMyDataCenter/geo-audit (+https://scoremydatacenter.org)"
THRESHOLD_M = 150.0
# Un verdict de test bâtiment qui N'EST PAS sur/près d'un bâtiment : c'est seulement combiné à la
# proximité d'un oracle qu'il devient une géo fabriquée probable. near_building (≤25 m) ne compte
# PAS ici — un point près d'un vrai bâtiment n'est pas un géocodage de commune.
NOT_ON_BUILDING = {"off_building", "no_building"}


def classer(closest_m: float | None, verdict: str | None) -> str | None:
    """Le critère COMBINÉ, isolé pour être testable sans réseau. Près d'un oracle (< seuil) :
    pas sur un bâtiment → géo fabriquée ; sur un bâtiment → faux positif (vrai DC d'une commune
    dense) ; **statut bâtiment INCONNU → `non_evalue`, surtout PAS faux positif** — une fiche
    jamais mesurée ne doit jamais ressembler à une fiche mesurée et saine (sinon le détecteur
    a l'air d'autant plus propre qu'on lui ajoute des fiches non testées : fail-open). Loin de
    tout oracle → rien à signaler."""
    if closest_m is None or closest_m > THRESHOLD_M:
        return None
    if verdict is None:
        return "non_evalue"
    return "fabriquee" if verdict in NOT_ON_BUILDING else "faux_positif"


def metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Haversine, points en (lat, lon). Même formule que audit.py."""
    r = 6_371_000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except Exception:  # noqa: BLE001
        return {}


def _save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False))


def insee_oracle(lat: float, lon: float, cache: dict) -> tuple[float | None, str | None]:
    """Distance au `centre` INSEE de la commune (France seulement)."""
    key = f"INSEE:{round(lat, 3)},{round(lon, 3)}"
    if key not in cache:
        url = "https://geo.api.gouv.fr/communes?" + urllib.parse.urlencode(
            {"lat": lat, "lon": lon, "fields": "centre,nom,code"})
        try:
            data = _get(url)
            communes = data if isinstance(data, list) else []
            if communes:
                lon0, lat0 = communes[0]["centre"]["coordinates"]
                cache[key] = [round(metres((lat, lon), (lat0, lon0)), 1), communes[0].get("nom")]
            else:
                cache[key] = [None, None]
        except Exception:  # noqa: BLE001
            cache[key] = [None, None]
    return tuple(cache[key])


def nominatim_oracle(lat: float, lon: float, cache: dict) -> tuple[float | None, str | None]:
    """Distance au point que Nominatim rend pour la commune (géocodeur — l'oracle du défaut)."""
    key = f"NOM:{round(lat, 3)},{round(lon, 3)}"
    if key not in cache:
        url = "https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode(
            {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10})
        try:
            data = _get(url)
            lat0, lon0 = float(data["lat"]), float(data["lon"])
            addr = data.get("address") or {}
            nom = (addr.get("city") or addr.get("town") or addr.get("municipality")
                   or addr.get("village") or data.get("name"))
            cache[key] = [round(metres((lat, lon), (lat0, lon0)), 1), nom]
        except Exception:  # noqa: BLE001
            cache[key] = [None, None]
        time.sleep(1.1)   # politique d'usage Nominatim : ≤ 1 req/s
    return tuple(cache[key])


def corpus() -> list[tuple[str, float, float, str]]:
    """(id, lat, lon, country) pour chaque fiche notée qui porte une coordonnée."""
    out: list[tuple[str, float, float, str]] = []
    for p in sorted(NEWSROOM.glob("datacenters*/*.json")):
        if p.name.endswith("provenance.json"):
            continue
        try:
            idn = (json.loads(p.read_text()).get("identity") or {})
        except Exception:  # noqa: BLE001
            continue
        c = idn.get("coordinates") or {}
        if c.get("lat") is None or c.get("lon") is None:
            continue
        out.append((p.stem, float(c["lat"]), float(c["lon"]), idn.get("country") or ""))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pipelines.geo_audit.centroid_check",
                                 description="Détecter les coordonnées de géocodeur (géo fabriquée).")
    ap.add_argument("--world", action="store_true", help="tout le corpus (sinon France seule)")
    a = ap.parse_args(argv)

    cache = _load_cache()
    verdicts = json.loads(ONBUILDING.read_text()).get("fiches", {})
    fiches = [f for f in corpus() if a.world or f[0].startswith("fr-")]

    fabriquees: list[dict] = []
    faux_positifs: list[dict] = []
    non_evalues: list[dict] = []
    erreurs = 0
    for i, (cid, lat, lon, country) in enumerate(fiches):
        try:
            d_insee, nom_insee = insee_oracle(lat, lon, cache) if country == "FR" else (None, None)
            d_nom, nom_nom = nominatim_oracle(lat, lon, cache)
            dists = {k: v for k, v in (("insee", d_insee), ("nominatim", d_nom)) if v is not None}
            if not dists:
                erreurs += 1
                continue
            closest_oracle = min(dists, key=dists.get)
            closest_m = dists[closest_oracle]
            verdict = (verdicts.get(cid) or {}).get("verdict")
            rec = {
                "id": cid, "commune": nom_insee or nom_nom, "country": country,
                "oracle_dist_m": {"insee": d_insee, "nominatim": d_nom},
                "closest_oracle": closest_oracle, "closest_m": closest_m,
                "audit_verdict": verdict,
            }
            verdict_classe = classer(closest_m, verdict)
            if verdict_classe == "fabriquee":
                rec["flag"] = "GÉO FABRIQUÉE PROBABLE"
                fabriquees.append(rec)
            elif verdict_classe == "faux_positif":
                rec["flag"] = "faux positif — sur un vrai bâtiment"
                faux_positifs.append(rec)
            elif verdict_classe == "non_evalue":
                rec["flag"] = "NON ÉVALUÉ — près d'un centroïde, test bâtiment manquant"
                non_evalues.append(rec)
        except Exception as e:  # noqa: BLE001
            erreurs += 1
            print(f"   ⚠ {cid}: {e}")
        if i % 20 == 0:
            _save_cache(cache)
    _save_cache(cache)

    doc = {
        "meta": {
            "generated_at": date.today().isoformat(),
            "threshold_m": THRESHOLD_M,
            "method": ("2 oracles géocodeur (geo.api.gouv.fr INSEE + Nominatim), match sur l'un OU "
                       "l'autre, ET coordonnée PAS sur un bâtiment (off/no_building) = géo fabriquée "
                       "probable. Le test bâtiment élimine les vrais DC de petites communes denses."),
            "note": "Interne newsroom — jamais dans le build public.",
            "angle_mort": ("ne teste que le centroïde de COMMUNE (reverse zoom 10) ; ne voit PAS "
                           "les aires sub-communales (outcode/postcode, ex. UB11) ; hors FR un seul "
                           "oracle (Nominatim), faute d'INSEE — 2ᵉ oracle mondial (GeoNames) à venir."),
            "counts": {"testées": len(fiches), "GÉO_FABRIQUÉE_PROBABLE": len(fabriquees),
                       "faux_positifs_sur_bâtiment": len(faux_positifs),
                       "non_evalues": len(non_evalues), "erreurs": erreurs},
        },
        "fabriquees_probables": sorted(fabriquees, key=lambda r: r["closest_m"]),
        "non_evalues": sorted(non_evalues, key=lambda r: r["closest_m"]),
        "faux_positifs": sorted(faux_positifs, key=lambda r: r["closest_m"]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    tmp.replace(OUT)
    print(f"testées {len(fiches)} · GÉO FABRIQUÉE PROBABLE {len(fabriquees)} · "
          f"non évalués {len(non_evalues)} · faux positifs (sur bâtiment) {len(faux_positifs)} · "
          f"erreurs {erreurs}")
    for r in fabriquees:
        print(f"   ⚠ {r['closest_m']:6.1f} m [{r['closest_oracle']}]  {r['commune']}  "
              f"{r['audit_verdict']}  {r['id']}")
    print(f"\nsortie : {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
