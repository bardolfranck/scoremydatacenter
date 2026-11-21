# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Contrôle qualité des liens de documents (spec du dictionnaire §6, Franck 2026-11-21).

Deux usages, un seul classement :

  ecriture — dès qu'on touche une fiche. Seuls les liens NOUVEAUX ou MODIFIÉS par rapport à
             une révision git (défaut HEAD) sont ouverts : un lien mauvais n'entre pas.
             `--index` lit la version indexée (crochet pre-commit), sinon le disque.
             Code de sortie 1 si un lien est cassé, a migré, ment ou ne répond pas.

  routine  — à date fixe. Par hôte : un ÉCHANTILLON de liens servis (5 par défaut). Si
             l'échantillon casse (≥ 2 échecs), c'est probablement la SOURCE qui a migré : on
             vérifie alors tous les liens de CET hôte, et seulement lui. Rapport JSON daté ;
             code de sortie 1 s'il y a quelque chose à faire.

Ce qui compte comme cassé : 404/410 ; une redirection PERMANENTE vers une autre page
(migration — on re-pointe, on ne laisse pas le lecteur rebondir) ; un « 200 qui ment »
(page d'erreur servie en 200, HTML à la place d'un PDF). Un 401/403/429 n'est PAS cassé :
« non vérifiable automatiquement » (anti-robot), à revoir au navigateur. Courtoisie : une
requête par hôte toutes les 2 s au plus — le vrai coût n'est pas la CPU, c'est d'être bloqué.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.core import datacenter_paths  # noqa: E402

CAL = Path(os.environ.get("NEWSROOM_CAL",
                          Path(__file__).resolve().parent.parent.parent / "smdc-newsroom" / "calibration"))
CHAMPS = ("official_documents", "project_party_documents")
UA = "ScoreMyDataCenter-link-check/1.0 (+https://scoremydatacenter.org)"
PAUSE_PAR_HOTE = 2.0
ECHECS = {"casse", "migre", "suspect", "injoignable"}
_INTROUVABLE = re.compile(
    rb"(page not found|not found</title>|404 not found|no longer available|page introuvable|"
    rb"document introuvable|pagina niet gevonden|niet gevonden</title>|seite nicht gefunden|"
    rb"nicht gefunden</title>)", re.I)


# ---------------------------------------------------------------- classement (pur, testé)

def _meme_page(a: str, b: str) -> bool:
    """Une redirection http→https, www, ou barre finale ne change pas la page."""
    pa, pb = urlparse(a), urlparse(b)
    ha = (pa.hostname or "").removeprefix("www.")
    hb = (pb.hostname or "").removeprefix("www.")
    return ha == hb and pa.path.rstrip("/") == pb.path.rstrip("/") and pa.query == pb.query


def classer(url: str, statut: int | None, redirections: list[tuple[int, str]],
            content_type: str = "", debut: bytes = b"") -> str:
    """ok | casse | migre | suspect | non_verifiable | injoignable."""
    for code, cible in redirections:
        if code in (301, 308) and not _meme_page(url, cible):
            return "migre"
    if statut is None or statut >= 500:
        return "injoignable"
    if statut in (404, 410):
        return "casse"
    if statut in (401, 403, 429):
        return "non_verifiable"
    if statut >= 400:
        return "casse"
    ct = (content_type or "").lower()
    if urlparse(url).path.lower().endswith(".pdf") and "html" in ct:
        return "suspect"
    if "html" in ct and _INTROUVABLE.search(debut[:65536]):
        return "suspect"
    return "ok"


# ---------------------------------------------------------------- réseau

class _Trace(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.redirections: list[tuple[int, str]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirections.append((code, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_dernier_appel: dict[str, float] = {}


def ouvrir(url: str, timeout: float = 20.0) -> dict:
    hote = urlparse(url).hostname or ""
    attente = _dernier_appel.get(hote, 0) + PAUSE_PAR_HOTE - time.monotonic()
    if attente > 0:
        time.sleep(attente)
    trace = _Trace()
    opener = urllib.request.build_opener(trace)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    statut, ct, debut = None, "", b""
    try:
        with opener.open(req, timeout=timeout) as r:
            statut, ct, debut = r.status, r.headers.get("Content-Type", ""), r.read(65536)
    except urllib.error.HTTPError as e:
        statut, ct = e.code, e.headers.get("Content-Type", "") if e.headers else ""
    except Exception:  # noqa: BLE001 — DNS, TLS, délai : injoignable, pas cassé
        statut = None
    finally:
        _dernier_appel[hote] = time.monotonic()
    return {"url": url, "statut": statut, "redirections": trace.redirections,
            "resultat": classer(url, statut, trace.redirections, ct, debut)}


# ---------------------------------------------------------------- quels liens

def liens(fiche: dict) -> set[str]:
    """Les liens SERVIS. Un document marqué `link_unavailable_since` n'a plus de lien servi :
    on ne le rouvre pas à chaque passage (il est déjà connu mort)."""
    ident = (fiche or {}).get("identity") or {}
    return {str(d.get("url")) for c in CHAMPS for d in ident.get(c) or []
            if isinstance(d, dict) and not d.get("link_unavailable_since")}


def liens_nouveaux(avant: dict | None, apres: dict) -> set[str]:
    return liens(apres) - liens(avant or {})


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout


def a_controler_ecriture(cal: Path, base: str, index: bool) -> list[tuple[str, str]]:
    repo = Path(_git(cal, "rev-parse", "--show-toplevel").strip())
    rel = cal.resolve().relative_to(repo)
    if index:
        noms = _git(repo, "diff", "--cached", "--name-only", "--diff-filter=AM", base, "--", str(rel)).split()
    else:
        noms = (_git(repo, "diff", "--name-only", "--diff-filter=AM", base, "--", str(rel)).split()
                + _git(repo, "ls-files", "--others", "--exclude-standard", "--", str(rel)).split())
    out = []
    for n in sorted(set(noms)):
        if not n.endswith(".json") or n.endswith(".provenance.json"):
            continue
        try:
            apres = json.loads(_git(repo, "show", f":{n}") if index else (repo / n).read_text("utf-8"))
        except ValueError:
            continue
        try:
            avant = json.loads(_git(repo, "show", f"{base}:{n}") or "null")
        except ValueError:
            avant = None
        out += [(Path(n).stem, u) for u in sorted(liens_nouveaux(avant, apres))]
    return out


# ---------------------------------------------------------------- modes

def mode_ecriture(args) -> int:
    cibles = a_controler_ecriture(args.cal, args.base, args.index)
    if not cibles:
        print("controle-liens : aucun lien nouveau ou modifié")
        return 0
    rc = 0
    for fiche, url in cibles:
        r = ouvrir(url)
        if r["resultat"] in ECHECS:
            rc = 1
        print(f"{r['resultat']:15} {fiche}  {url}  (HTTP {r['statut']})")
    if rc:
        print("controle-liens : un lien ne passe pas — corriger avant d'écrire (spec §6)")
    return rc


def mode_routine(args) -> int:
    par_hote: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for p in datacenter_paths(args.cal):
        try:
            fiche = json.loads(p.read_text("utf-8"))
        except ValueError:
            continue
        for u in sorted(liens(fiche)):
            par_hote[urlparse(u).hostname or "?"].append((p.stem, u))
    alea = random.Random(date.today().isoformat())
    rapport, a_faire = {"date": date.today().isoformat(), "echantillon": args.echantillon, "hotes": {}}, 0
    for hote, docs in sorted(par_hote.items()):
        tirage = docs if len(docs) <= args.echantillon else alea.sample(docs, args.echantillon)
        res = [{"fiche_id": f, **ouvrir(u)} for f, u in tirage]
        echecs = [r for r in res if r["resultat"] in ECHECS]
        diag = "ok"
        if len(echecs) >= 2 and len(docs) > len(tirage):
            # Panne de SOURCE probable : on balaie CET hôte, et lui seul.
            deja = {r["url"] for r in res}
            res += [{"fiche_id": f, **ouvrir(u)} for f, u in docs if u not in deja]
            echecs = [r for r in res if r["resultat"] in ECHECS]
        if echecs:
            diag = "source" if len(echecs) >= 2 else "document"
            a_faire += 1
        rapport["hotes"][hote] = {"servis": len(docs), "verifies": len(res), "diagnostic": diag,
                                  "resultats": res}
        print(f"{diag:9} {hote}  {len(echecs)}/{len(res)} en échec ({len(docs)} servis)")
    args.rapport.mkdir(parents=True, exist_ok=True)
    sortie = args.rapport / f"{rapport['date']}.json"
    sortie.write_text(json.dumps(rapport, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"controle-liens : rapport {sortie}")
    return 1 if a_faire else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    e = sub.add_parser("ecriture")
    e.add_argument("--cal", type=Path, default=CAL)
    e.add_argument("--base", default="HEAD")
    e.add_argument("--index", action="store_true")
    r = sub.add_parser("routine")
    r.add_argument("--cal", type=Path, default=CAL)
    r.add_argument("--echantillon", type=int, default=5)
    r.add_argument("--rapport", type=Path, default=CAL.parent / "analysis" / "sources" / "controle-liens")
    args = ap.parse_args(argv)
    return mode_ecriture(args) if args.mode == "ecriture" else mode_routine(args)


if __name__ == "__main__":
    sys.exit(main())
