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
import hashlib
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import avis as A
from . import fiche as F
from . import index as I
from . import mrae_site as M

# Empreintes des documents déjà traités dans CE run (les registres régionaux passent avant
# la source nationale, donc le doublon est toujours détecté du côté national).
_SEEN: dict[str, str] = {}
_SEEN_LOCK = threading.Lock()


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
        pdf = A.fetch_pdf(d.doc_url)
        with _SEEN_LOCK:
            _SEEN[hashlib.sha256(pdf).hexdigest()] = name
        av = A.extract(pdf, d.doc_url)
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


def one_national(doc, out_dir: Path, force: bool) -> dict:
    """Un document de l'index national : télécharger, CONFIRMER le sujet, puis extraire."""
    name = "mrae-" + slug(re.sub(r"\.pdf$", "", doc.doc_url.rsplit("/", 1)[-1])) + ".json"
    path = out_dir / name
    row = {"region": "FR", "intitule": doc.titre, "date": doc.date,
           "fichier": name, "doc_url": doc.doc_url, "origine": "site MRAe"}
    if path.exists() and not force:
        row["statut"] = "déjà extrait"
        return row
    try:
        pdf = A.fetch_pdf(doc.doc_url)
        digest = hashlib.sha256(pdf).hexdigest()
        # Le même avis est servi par le registre régional ET par le site national, sous deux
        # adresses différentes. Dédupliquer sur l'URL ne suffit donc pas : neuf fiches en
        # double dans le premier lot. L'empreinte du document tranche.
        with _SEEN_LOCK:
            if digest in _SEEN:
                row["statut"] = "doublon"
                row["raison"] = f"même document que {_SEEN[digest]} (empreinte identique)"
                return row
            _SEEN[digest] = name
        pages = A.pages_of(pdf)
    except A.NotADocument as e:
        row["statut"] = "lien non documentaire"
        row["raison"] = str(e)[:200]
        return row
    except Exception as e:  # noqa: BLE001
        row["statut"] = "échec"
        row["raison"] = f"{type(e).__name__}: {e}"[:200]
        return row
    # Le tri par titre ne discrimine pas (mesuré : 4 vrais avis sur 12). L'objet du document
    # est énoncé dans ses deux premières pages ; c'est là qu'on tranche, pas avant.
    if not M.confirms_datacenter(pages):
        row["statut"] = "hors sujet"
        row["raison"] = "« data center » n'est pas le sujet des deux premières pages"
        row["pages"] = len(pages)
        return row
    av = A.extract_from_pages(pages, doc.doc_url)
    d = F.build_national(doc, av)
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    row["statut"] = "extrait" if av.has_text_layer else "sans couche texte"
    row["faits"] = sum(len(v) for v in d["installation"]["faits"].values())
    row["recommandations"] = len(d["installation"]["recommandations_autorite"])
    row["pages"] = av.n_pages
    if av.warnings:
        row["avertissements"] = av.warnings
    return row


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--regions", default=",".join(I.REGIONS))
    ap.add_argument("--national", action="store_true",
                    help="ajouter l'index documentaire national (site MRAe) aux registres WFS")
    ap.add_argument("--query", default="data center")
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

    if a.national:
        try:
            docs = M.search(a.query)
        except Exception as e:  # noqa: BLE001
            print(f"site MRAe injoignable — {type(e).__name__}: {e}", file=sys.stderr)
            docs = []
        # Les registres ont déjà servi ces PDF pour certaines régions : on ne les repasse pas.
        already = {r["doc_url"] for r in rows if r.get("doc_url")}
        docs = [d for d in docs if d.doc_url not in already]
        print(f"site MRAe: {len(docs)} candidats nationaux", file=sys.stderr)
        with ThreadPoolExecutor(a.workers) as ex:
            rows += list(ex.map(lambda d: one_national(d, a.out, a.force), docs))

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
