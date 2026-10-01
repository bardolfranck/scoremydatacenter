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
import collections
import hashlib
import json
import re
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import avis as A
from . import bruit as BR
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
    row["champs"] = sorted({f["indicateur"] for fs in doc["installation"]["faits"].values() for f in fs})
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
    av = A.extract_from_pages(pages, doc.doc_url, sha256=digest)
    d = F.build_national(doc, av)
    d["source"]["region_detectee"] = M.region_of(pages)
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    row["statut"] = "extrait" if av.has_text_layer else "sans couche texte"
    row["region"] = d["source"]["region_detectee"] or "?"
    row["faits"] = sum(len(v) for v in d["installation"]["faits"].values())
    row["champs"] = sorted({f["indicateur"] for fs in d["installation"]["faits"].values() for f in fs})
    row["recommandations"] = len(d["installation"]["recommandations_autorite"])
    row["pages"] = av.n_pages
    if av.warnings:
        row["avertissements"] = av.warnings
    return row


def couverture(rows: list[dict]) -> dict:
    """La COMPTABILITÉ du lot : ce que les documents ont, et ce qu'ils n'ont pas.

    C'est le livrable, pas un sous-produit de l'extraction. Trois tableaux :

    · CHAMP × nombre d'avis qui le portent. La question produit : quels faits sont
      collectables À L'ÉCHELLE et lesquels sont anecdotiques. Un champ présent dans 8 avis
      sur 400 ne deviendra jamais un indicateur, quelle que soit son importance apparente.
    · RÉGION × nombre d'avis. Ce qui remplace « le Grand Est n'a rien » — une présomption
      tirée de noms de fichiers — par une mesure.
    · MOTIF DE REJET × nombre de documents. Le plus important pour nous : si le filtre se
      trompe, c'est là que ça se verra. Compter seulement ce qui passe revient à noter sa
      propre copie.
    """
    champs: collections.Counter = collections.Counter()
    regions: collections.Counter = collections.Counter()
    rejets: collections.Counter = collections.Counter()
    retenus = 0
    for r in rows:
        if r["statut"] in ("extrait", "déjà extrait"):
            retenus += 1
            champs.update(r.get("champs", []))
            regions[_region_name(r.get("region"))] += 1
        else:
            rejets[r["statut"]] += 1
    return {
        "schema": "smdc.registre-ae.couverture/1",
        "genere_le": time.strftime("%Y-%m-%d"),
        "documents_examines": len(rows),
        "avis_retenus": retenus,
        "champs": {"note": "nombre d'avis portant le champ, sur les avis retenus",
                   "sur": retenus,
                   "valeurs": dict(champs.most_common())},
        "regions": dict(regions.most_common()),
        "rejets": {"note": "pourquoi un document examiné n'a pas produit de fiche",
                   "valeurs": dict(rejets.most_common())},
    }


# Les fiches nationales portent le NOM de région lu dans l'avis, les fiches de registre le CODE
# de la spec. Sans normalisation, la même région apparaît deux fois dans la comptabilité (« IDF »
# ET « Île-de-France ») et sous-estime de moitié la concentration réelle — un chiffre publié faux.
REGION_NAMES = {
    "idf": "Île-de-France", "ge": "Grand Est", "paca": "Provence-Alpes-Côte d'Azur",
    "norm": "Normandie", "na": "Nouvelle-Aquitaine", "aura": "Auvergne-Rhône-Alpes",
}


def _region_name(code: str | None) -> str:
    if not code:
        return "?"
    return REGION_NAMES.get(code.strip().lower(), code)


def _fiche_region(d: dict) -> str:
    src = d.get("source") or {}
    return _region_name(src.get("region_detectee")
                        or ((src.get("registre") or {}).get("region")))


def _coverage_from_fiches(out_dir: Path) -> tuple[collections.Counter, collections.Counter, int]:
    """Recompter champs×avis et régions×avis À PARTIR DES FICHES servies (pour --revalidate)."""
    champs: collections.Counter = collections.Counter()
    regions: collections.Counter = collections.Counter()
    retenus = 0
    for p in sorted(out_dir.glob("*.json")):
        if p.name in ("index.json", "couverture.json"):
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            continue
        inst = d.get("installation") or {}
        if "faits" not in inst:
            continue
        retenus += 1
        champs.update({f["indicateur"] for fs in inst["faits"].values() for f in fs})
        regions[_fiche_region(d)] += 1
    return champs, regions, retenus


def revalidate(out_dir: Path) -> dict:
    """Réappliquer les règles COURANTES aux phrases DÉJÀ STOCKÉES — aucun réseau.

    Transforme une retouche en opération DÉTERMINISTE et rejouable : au dégel, la vraie
    ré-extraction doit être un non-événement. On ne retire QUE ce qu'une règle REJETTE
    (`avis.rejection_reason`), jamais ce qui est seulement « non reproduit » — un silence
    n'est pas une preuve. Chaque fiche touchée est horodatée `revalidation` pour qu'un
    lecteur distingue une fiche extraite d'une fiche revalidée.
    """
    today = time.strftime("%Y-%m-%d")
    touched = 0
    removed_total = 0
    by_field: collections.Counter = collections.Counter()
    for p in sorted(out_dir.glob("*.json")):
        if p.name in ("index.json", "couverture.json"):
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            continue
        inst = d.get("installation") or {}
        faits = inst.get("faits")
        if not faits:
            continue
        removed: list[dict] = []
        for theme in list(faits):
            kept = []
            for f in faits[theme]:
                motif = A.rejection_reason(f.get("indicateur"), f.get("valeur"), f.get("phrase", ""))
                if motif is None:
                    kept.append(f)
                else:
                    removed.append({"indicateur": f.get("indicateur"),
                                    "valeur": f.get("valeur"), "page": f.get("page"), "motif": motif})
                    by_field[f.get("indicateur")] += 1
            if kept:
                faits[theme] = kept
            else:
                del faits[theme]
        if removed:
            d["revalidation"] = {
                "date": today,
                "regle": ("retrait des seuls faits POSITIVEMENT rejetés par les règles courantes "
                          "(motif de rejet, agrégat de site, borne, champ retiré) ; jamais un "
                          "fait seulement non reproduit"),
                "faits_retires": removed,
            }
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            touched += 1
            removed_total += len(removed)
    return {"fiches_touchees": touched, "faits_retires": removed_total,
            "par_champ": dict(by_field.most_common())}


_BRUIT_LABELS = {"bruit_bandes": "Bruit par point et période",
                 "bruit_emergence_bandes": "Émergence par période"}
_BRUIT_FLOOR = ("PLANCHER, pas la couverture réelle : les bandes sont DÉRIVÉES des phrases déjà "
                "extraites (aucun réseau) ; une bande portée par une phrase que l'ancienne ancre "
                "ne captait pas n'y figure pas. La vraie couverture du bruit sera connue à la "
                "ré-extraction (dégel) — l'écart mesurera ce que la dérivation ne pouvait voir.")


def rederive_bruit(out_dir: Path) -> dict:
    """AJOUTER les bandes de bruit structurées, dérivées des PHRASES DÉJÀ STOCKÉES (aucun réseau).

    Opération SÉPARÉE du revalidate (qui, lui, retire) : mélanger ajout et retrait dans un même
    passage brouillerait la trace. Stamp distinct `derivation_bruit`. RÉSERVE : ne voit que les
    phrases ayant déjà produit un fait ; le compte obtenu est un PLANCHER, pas une mesure.
    """
    today = time.strftime("%Y-%m-%d")
    touched = added = 0
    listing: list[tuple[str, list[str]]] = []
    for p in sorted(out_dir.glob("*.json")):
        if p.name in ("index.json", "couverture.json"):
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            continue
        faits = (d.get("installation") or {}).get("faits")
        if not faits:
            continue
        phrases: dict[str, int] = {}
        for lst in faits.values():
            for f in lst:
                ph = f.get("phrase")
                if ph and ph not in phrases:
                    phrases[ph] = f.get("page")
        existing = {(f["indicateur"], str(f.get("valeur")))
                    for f in faits.get("bruit", []) if f["indicateur"] in _BRUIT_LABELS}
        new_facts: list[dict] = []
        points: list[str] = []
        for ph, page in phrases.items():
            for fid, bands in (("bruit_bandes", BR.parse_levels(ph)),
                               ("bruit_emergence_bandes", BR.parse_emergences(ph))):
                for band in bands:
                    key = (fid, str(band))
                    if key in existing:
                        continue
                    existing.add(key)
                    new_facts.append({"indicateur": fid, "libelle": _BRUIT_LABELS[fid],
                                      "theme": "bruit", "valeur": band, "phrase": ph, "page": page})
                    if band.get("point"):
                        points.append(band["point"])
        if new_facts:
            faits.setdefault("bruit", []).extend(new_facts)
            d["derivation_bruit"] = {
                "date": today,
                "source": "bandes dérivées des phrases déjà extraites, sans réseau",
                "reserve": _BRUIT_FLOOR,
                "bandes_ajoutees": len(new_facts),
            }
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            touched += 1
            added += len(new_facts)
            listing.append((p.name, sorted(set(points))))
    return {"fiches_touchees": touched, "bandes_ajoutees": added, "listing": listing}


def _content_fp(d: dict) -> str:
    """Empreinte du CONTENU LU : phrases des faits + recommandations, normalisées.

    Le `sha256` du FICHIER ne voit pas les quasi-doublons — le même avis ré-exporté à quelques
    octets près, ou servi par le registre régional ET le site national sous deux URL. Le bon
    discriminant est le texte lu, en minuscules, sans accents ni ponctuation.
    """
    parts: list[str] = []
    for lst in d.get("installation", {}).get("faits", {}).values():
        parts.extend(str(f.get("phrase", "")) for f in lst)
    parts.extend(str(r.get("texte", "")) for r in d.get("installation", {}).get("recommandations_autorite", []))
    s = unicodedata.normalize("NFKD", " ".join(parts))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return hashlib.sha256(re.sub(r"[^a-z0-9]", "", s).encode()).hexdigest()


def dedup_contenu(out_dir: Path) -> dict:
    """Fusionner les avis EN DOUBLON PAR CONTENU (aucun réseau). Déterministe, idempotent.

    Deux garde-fous payés par le test : (1) NE dédupliquer QUE les fiches à couche texte — une
    empreinte vide regrouperait à tort les scans illisibles, qui sont des documents DISTINCTS
    qu'on ne sait pas lire ; (2) quand un avis existe en version REGISTRE (acte administratif :
    pétitionnaire, INSEE, procédure, géométrie) et en version site national, GARDER le registre
    et consigner l'autre URL en source alternative — deux services publient le même avis, c'est
    une information, pas un déchet.
    """
    today = time.strftime("%Y-%m-%d")
    fiches = []
    for p in sorted(out_dir.glob("*.json")):
        if p.name in ("index.json", "couverture.json"):
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            continue
        inst = d.get("installation")
        if not inst:
            continue
        src = d.get("source") or {}
        has_text = (src.get("pdf") or {}).get("couche_texte", True)
        fiches.append({"path": p, "d": d, "text": has_text,
                       "registre": src.get("registre") is not None,
                       "nfaits": sum(len(v) for v in inst.get("faits", {}).values()),
                       "url": src.get("doc_url", "")})
    groups: dict[str, list] = {}
    for rec in fiches:
        if not rec["text"]:
            continue  # jamais de dédup sur une empreinte vide
        groups.setdefault(_content_fp(rec["d"]), []).append(rec)

    removed: list[str] = []
    merges: list[tuple] = []
    for recs in groups.values():
        if len(recs) < 2:
            continue
        # keeper : le registre d'abord, puis le plus riche, puis par nom (déterministe).
        keeper = sorted(recs, key=lambda r: (not r["registre"], -r["nfaits"], r["path"].name))[0]
        kd = keeper["d"]
        alts = kd.setdefault("source", {}).setdefault("sources_alternatives", [])
        fused = []
        for rec in recs:
            if rec is keeper:
                continue
            if rec["url"] and rec["url"] not in alts:
                alts.append(rec["url"])
            fused.append({"fichier": rec["path"].name, "doc_url": rec["url"]})
            rec["path"].unlink()
            removed.append(rec["path"].name)
        kd["dedup"] = {
            "date": today,
            "methode": ("empreinte du CONTENU lu (NFKD, minuscules, sans ponctuation) ; le "
                        "sha256 du fichier ne voit pas les ré-exports différant de quelques octets"),
            "fusionnee_depuis": fused,
        }
        keeper["path"].write_text(json.dumps(kd, ensure_ascii=False, indent=2), encoding="utf-8")
        merges.append((keeper["path"].name, [f["fichier"] for f in fused]))
    return {"fiches_fusionnees": removed, "merges": merges,
            "sans_couche_texte": sum(1 for r in fiches if not r["text"])}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--regions", default=",".join(I.REGIONS))
    ap.add_argument("--national", action="store_true",
                    help="ajouter l'index documentaire national (site MRAe) aux registres WFS")
    ap.add_argument("--query", default=",".join(M.QUERIES),
                    help="requêtes séparées par des virgules ; leur UNION est passée")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--revalidate", action="store_true",
                    help="réappliquer les règles courantes aux fiches DÉJÀ stockées (aucun "
                         "réseau) et retirer les faits positivement rejetés ; régénère couverture.json")
    ap.add_argument("--rederive-bruit", dest="rederive_bruit", action="store_true",
                    help="AJOUTER les bandes de bruit dérivées des phrases déjà stockées (aucun "
                         "réseau) ; opération séparée du revalidate, trace datée distincte")
    ap.add_argument("--dedup-contenu", dest="dedup_contenu", action="store_true",
                    help="fusionner les avis en doublon PAR CONTENU LU (aucun réseau) ; garde la "
                         "fiche de registre, consigne l'URL alternative ; régénère couverture.json")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)

    if a.dedup_contenu:
        if not a.out.is_dir():
            print(f"--dedup-contenu : {a.out} introuvable", file=sys.stderr)
            return 2
        summary = dedup_contenu(a.out)
        champs, regions, retenus = _coverage_from_fiches(a.out)
        cov_path = a.out / "couverture.json"
        cov = json.loads(cov_path.read_text()) if cov_path.exists() else {}
        cov.pop("avis_retenus", None)   # ambigu une fois dédupliqué : seul avis_distincts fait foi
        cov["avis_distincts"] = retenus
        cov["champs"] = {"note": "nombre d'avis DISTINCTS portant le champ", "sur": retenus,
                         "valeurs": dict(champs.most_common())}
        cov["regions"] = dict(regions.most_common())
        cov["dedup"] = {"date": time.strftime("%Y-%m-%d"),
                        "fiches_fusionnees": len(summary["fiches_fusionnees"]),
                        "note": ("dénominateur = avis DISTINCTS par contenu lu ; les fiches sans "
                                 "couche texte restent distinctes (documents illisibles, pas doublons)")}
        cov_path.write_text(json.dumps(cov, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"dedup-contenu : {len(summary['fiches_fusionnees'])} fiche(s) fusionnée(s) ; "
              f"{retenus} avis distincts.", file=sys.stderr)
        for keeper, fused in summary["merges"]:
            print(f"  gardé {keeper}\n      ← {', '.join(fused)}", file=sys.stderr)
        return 0

    if a.rederive_bruit:
        if not a.out.is_dir():
            print(f"--rederive-bruit : {a.out} introuvable", file=sys.stderr)
            return 2
        summary = rederive_bruit(a.out)
        champs, regions, retenus = _coverage_from_fiches(a.out)
        cov_path = a.out / "couverture.json"
        cov = json.loads(cov_path.read_text()) if cov_path.exists() else {}
        cov.pop("avis_retenus", None)   # le dénominateur vit dans champs.sur / avis_distincts
        cov["champs"] = {"note": "nombre d'avis portant le champ", "sur": retenus,
                         "valeurs": dict(champs.most_common())}
        cov["regions"] = dict(regions.most_common())
        cov["bruit"] = {"fiches_avec_bande": summary["fiches_touchees"], "note": _BRUIT_FLOOR}
        cov["derivation_bruit"] = {"date": time.strftime("%Y-%m-%d"),
                                   "fiches_touchees": summary["fiches_touchees"],
                                   "bandes_ajoutees": summary["bandes_ajoutees"]}
        cov_path.write_text(json.dumps(cov, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"rederive-bruit : {summary['bandes_ajoutees']} bande(s) ajoutée(s) sur "
              f"{summary['fiches_touchees']} fiche(s) (PLANCHER).", file=sys.stderr)
        for name, points in summary["listing"]:
            print(f"  {name}\n      points : {', '.join(points) if points else '(aucun point nommé)'}",
                  file=sys.stderr)
        return 0

    if a.revalidate:
        if not a.out.is_dir():
            print(f"--revalidate : {a.out} introuvable", file=sys.stderr)
            return 2
        champs_av, _reg_av, _ = _coverage_from_fiches(a.out)   # AVANT
        summary = revalidate(a.out)
        champs_ap, regions_ap, retenus = _coverage_from_fiches(a.out)  # APRÈS
        cov_path = a.out / "couverture.json"
        old = json.loads(cov_path.read_text()) if cov_path.exists() else {}
        cov = {
            "schema": "smdc.registre-ae.couverture/1",
            "genere_le": time.strftime("%Y-%m-%d"),
            "mode": "revalidate",
            # pas de total à part : le dénominateur vit dans champs.sur, un seul endroit (deux
            # nombres voisins qui disent des choses différentes finissent toujours confondus).
            "champs": {"note": "nombre d'avis portant le champ, après revalidation",
                       "sur": retenus, "valeurs": dict(champs_ap.most_common())},
            "regions": dict(regions_ap.most_common()),
            # Les motifs de REJET de documents datent de la dernière récolte : la revalidation
            # ne réexamine pas de documents, seulement des faits déjà extraits. On les conserve
            # tels quels en le disant, plutôt que de les effacer ou de les prétendre à jour.
            "rejets": old.get("rejets", {"note": "indisponible hors récolte"}),
            "revalidation": {"date": time.strftime("%Y-%m-%d"),
                             "fiches_touchees": summary["fiches_touchees"],
                             "faits_retires": summary["faits_retires"],
                             "par_champ": summary["par_champ"]},
        }
        cov_path.write_text(json.dumps(cov, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"revalidate : {summary['faits_retires']} fait(s) retiré(s) sur "
              f"{summary['fiches_touchees']} fiche(s).", file=sys.stderr)
        print("champ : avant → après (effondrement = 0 restant)", file=sys.stderr)
        for fid in sorted(summary["par_champ"]):
            print(f"  {fid:28s} {champs_av.get(fid, 0):3d} → {champs_ap.get(fid, 0):3d}"
                  f"{'  <-- EFFONDREMENT' if champs_ap.get(fid, 0) == 0 else ''}", file=sys.stderr)
        return 0

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
        docs, vus = [], set()
        for q in [x.strip() for x in a.query.split(",") if x.strip()]:
            try:
                found = M.search(q)
            except M.SearchUnavailable as e:
                # On ARRÊTE le passage national : continuer produirait un index qui affirme
                # « rien trouvé » pour les requêtes suivantes alors que le service ne cherche
                # plus. Mieux vaut un lot partiel qui le dit qu'un lot complet qui ment.
                print(f"ARRÊT du passage national — {e}", file=sys.stderr)
                break
            except Exception as e:  # noqa: BLE001
                print(f"site MRAe, requête {q!r} — {type(e).__name__}: {e}", file=sys.stderr)
                continue
            neuf = [d for d in found if d.doc_url not in vus]
            vus.update(d.doc_url for d in found)
            docs += neuf
            print(f"  {q:34s} {len(found):4d} candidats, {len(neuf):4d} inédits", file=sys.stderr)
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
    (a.out / "couverture.json").write_text(
        json.dumps(couverture(rows), ensure_ascii=False, indent=2), encoding="utf-8")

    by = {}
    for r in rows:
        by[r["statut"]] = by.get(r["statut"], 0) + 1
    print(f"\n{len(rows)} dossiers en {time.time()-t0:.0f}s → {a.out}", file=sys.stderr)
    for k, v in sorted(by.items(), key=lambda x: -x[1]):
        print(f"  {v:3d}  {k}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
