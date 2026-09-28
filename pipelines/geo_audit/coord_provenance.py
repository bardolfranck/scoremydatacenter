# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""LIVRABLE 2 — registre de PROVENANCE de la coordonnée, fiche par fiche.

Reconstruit, à partir des fichiers EXISTANTS (aucun réseau, aucun scrape), l'origine
de la coordonnée de chaque DC : la source, sa date, la méthode. Là où l'origine est
IRRÉCUPÉRABLE, on l'écrit explicitement (`source: "unrecorded"`) — un trou nommé vaut
mieux qu'une valeur fausse.

Distinction que le chef exige et qu'on ne franchit pas :
  - la CONFIRMATION de position (le point tombe sur un bâtiment OSM) vit dans
    on-building.json ; elle ne prouve PAS d'où venait la coordonnée.
  - `_dcwatch_power.provenance.json` est la provenance de la PUISSANCE, jamais de
    la coordonnée : on ne s'en sert pas ici.

Chaîne de priorité, par fiche :
  1. sidecar per-fiche avec `osm_origin` (osm_id) ....... OpenStreetMap, id tracé
  2. sidecar avec `announcement_provenance` (DCWatch/OSM/presse) . selon son contenu
  3. sidecar avec `coordinates_input` mais sans osm_origin ...... coordonnée FOURNIE
       au pipeline spatial ; on cherche l'amont (DCmag), sinon amont non consigné
  4. fiche listée dans `_dcmag_location_leads` fills ... carte.dcmag.fr (lead de localisation)
  5. sinon .............................................. unrecorded (trou nommé)

Sortie = NEWSROOM PRIVÉ, jamais dans le build public :
  calibration/coordinate-provenance/registry.json

Usage : python -m pipelines.geo_audit.coord_provenance
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

NEWSROOM = Path(__file__).resolve().parents[3] / "smdc-newsroom"
CAL = NEWSROOM / "calibration"
OUT = CAL / "coordinate-provenance" / "registry.json"


def _load(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _aggregate_fills(name: str) -> dict:
    """fills d'un fichier de provenance agrégé (_dcmag_location_leads, …), s'il existe."""
    for p in CAL.rglob(f"{name}.provenance.json"):
        return _load(p).get("fills") or {}
    return {}


def _coord_from_sidecar(side: dict) -> dict | None:
    """Provenance de coordonnée lisible directement dans le sidecar per-fiche."""
    osm = side.get("osm_origin")
    if isinstance(osm, dict) and osm.get("osm_id"):
        return {
            "source": "OpenStreetMap",
            "osm_object": str(osm["osm_id"]),
            "method": "spatial-pipeline osm_origin",
            "attribution": osm.get("attribution") or "OpenStreetMap contributors, ODbL 1.0",
            "date": side.get("generated_at"),
            "confidence": "recorded",
        }
    ann = side.get("announcement_provenance")
    if isinstance(ann, dict) and (ann.get("source") or ann.get("url")):
        return {
            "source": ann.get("source") or ann.get("publisher") or "announcement",
            "url": ann.get("url"),
            "method": "announcement/provenance sidecar",
            "attribution": ann.get("attribution"),
            "date": ann.get("date") or ann.get("accessed") or side.get("generated_at"),
            "confidence": "recorded",
        }
    return None


def build() -> dict:
    dcmag = _aggregate_fills("_dcmag_location_leads")
    registry: dict[str, dict] = {}

    for p in sorted(CAL.glob("datacenters*/*.json")):
        if p.name.endswith("provenance.json"):
            continue
        d = _load(p)
        ident = d.get("identity") or {}
        co = ident.get("coordinates") or {}
        if co.get("lat") is None:
            continue
        sid = p.stem
        side = _load(p.with_suffix(".provenance.json")) if p.with_suffix(".provenance.json").exists() else {}

        rec = _coord_from_sidecar(side)
        if rec is None and "coordinates_input" in side and sid in dcmag:
            lead = dcmag[sid]
            rec = {"source": lead.get("location_lead") or "carte.dcmag.fr", "method": "DCmag location lead",
                   "attribution": "dcmag.fr (média commercial, non open)", "date": lead.get("accessed"),
                   "confidence": "recorded"}
        elif rec is None and "coordinates_input" in side:
            rec = {"source": "unrecorded", "method": "coordonnée fournie au pipeline spatial ; amont non consigné",
                   "date": side.get("generated_at"), "confidence": "hole"}
        elif rec is None and sid in dcmag:
            lead = dcmag[sid]
            rec = {"source": lead.get("location_lead") or "carte.dcmag.fr", "method": "DCmag location lead",
                   "attribution": "dcmag.fr (média commercial, non open)", "date": lead.get("accessed"),
                   "confidence": "recorded"}
        elif rec is None:
            rec = {"source": "unrecorded", "method": None, "date": None, "confidence": "hole",
                   "note": "aucun sidecar exploitable ; origine de la coordonnée à reconstituer ou irrécupérable"}

        rec = {k: v for k, v in rec.items() if v is not None}
        registry[sid] = rec

    return registry


def main() -> None:
    reg = build()
    holes = sum(1 for r in reg.values() if r.get("confidence") == "hole")
    by_source: dict[str, int] = {}
    for r in reg.values():
        src = r.get("source")
        if isinstance(src, dict):  # sidecar où `source` est un objet {title/url/…}
            src = src.get("title") or src.get("source") or src.get("name") or json.dumps(src, ensure_ascii=False)[:60]
        key = src if r.get("confidence") == "recorded" else "unrecorded"
        by_source[key] = by_source.get(key, 0) + 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "generated_at": date.today().isoformat(),
            "note": "Provenance de la COORDONNÉE, fiche par fiche. Reconstruit depuis les fichiers existants. "
                    "Trou nommé (source=unrecorded) là où l'origine est irrécupérable. "
                    "CONFIRMATION de position = on-building.json, à ne pas confondre. "
                    "Interne newsroom — JAMAIS dans le build public.",
            "counts": {"fiches": len(reg), "recorded": len(reg) - holes, "unrecorded": holes},
            "by_source": dict(sorted(by_source.items(), key=lambda kv: -kv[1])),
        },
        "fiches": dict(sorted(reg.items())),
    }
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    os.replace(tmp, OUT)

    print(f"fiches ........ {len(reg)}")
    print(f"provenance OK . {len(reg) - holes}")
    print(f"TROU nommé .... {holes}")
    print("\npar source :")
    for k, v in payload["meta"]["by_source"].items():
        print(f"  {v:5}  {k}")
    print(f"\nregistre : {OUT}")


if __name__ == "__main__":
    main()
