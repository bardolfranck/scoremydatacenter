# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le LOT : toutes les régions outillées → un JSON d'extraction par dossier, plus un index.

    python -m pipelines.registers.run --out ../smdc-newsroom/registres

Un dossier qui échoue n'arrête pas le lot : il est consigné avec SA RAISON dans l'index.
Un lot qui s'arrête au premier PDF absent oblige à tout relancer et pousse à mettre un
`except: pass` — on préfère un index qui dit exactement ce qui manque et pourquoi.

Reprise : un fichier déjà écrit n'est pas retéléchargé (`--force` pour refaire). Ces PDF
font 1 à 3 Mo et le service qui les sert n'est pas rapide.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import avis as A
from . import fiche as F
from . import index as I


def slug(*parts: str) -> str:
    s = "-".join(p for p in parts if p)
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_]+", "-", s)[:70].strip("-")


def one(region: str, d: I.Dossier, out_dir: Path, force: bool) -> dict:
    name = slug(region, d.commune or d.intitule[:30], d.numero_avis) + ".json"
    path = out_dir / name
    row = {"region": region, "commune": d.commune, "intitule": d.intitule,
           "date": d.date_avis or d.date_reception, "fichier": name, "doc_url": d.doc_url}
    if path.exists() and not force:
        row["statut"] = "déjà extrait"
        return row
    if not d.doc_url:
        row["statut"] = "sans lien"
        row["raison"] = "le registre ne porte pas de lien vers l'avis"
        return row
    try:
        av = A.extract(A.fetch_pdf(d.doc_url), d.doc_url)
    except A.NotADocument as e:
        row["statut"] = "lien non documentaire"
        row["raison"] = str(e)[:200]
        return row
    except Exception as e:  # noqa: BLE001
        row["statut"] = "échec"
        row["raison"] = f"{type(e).__name__}: {e}"[:200]
        return row
    doc = F.build(d, av)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    row["statut"] = "extrait" if av.has_text_layer else "sans couche texte"
    row["faits"] = sum(len(v) for v in doc["installation"]["faits"].values())
    row["recommandations"] = len(doc["installation"]["recommandations_autorite"])
    row["pages"] = av.n_pages
    if av.warnings:
        row["avertissements"] = av.warnings
    return row


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--regions", default=",".join(I.REGIONS))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, I.Dossier]] = []
    for r in a.regions.split(","):
        try:
            ds = I.fetch(r)
        except Exception as e:  # noqa: BLE001
            print(f"{r}: registre injoignable — {type(e).__name__}: {e}", file=sys.stderr)
            continue
        print(f"{r}: {len(ds)} dossiers", file=sys.stderr)
        jobs += [(r, d) for d in ds]

    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(lambda j: one(j[0], j[1], a.out, a.force), jobs))

    index = {"schema": "smdc.registre-ae.index/1",
             "genere_le": time.strftime("%Y-%m-%d"),
             "regions_outillees": sorted(I.REGIONS),
             "dossiers": rows}
    (a.out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    by = {}
    for r in rows:
        by[r["statut"]] = by.get(r["statut"], 0) + 1
    print(f"\n{len(rows)} dossiers en {time.time()-t0:.0f}s → {a.out}", file=sys.stderr)
    for k, v in sorted(by.items(), key=lambda x: -x[1]):
        print(f"  {v:3d}  {k}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
