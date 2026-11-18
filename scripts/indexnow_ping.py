#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Après une mise en ligne, signaler à IndexNow (Bing, Yandex…) les pages qui ont changé.

POURQUOI (2026-11-18). Bing Webmaster Tools : 1 876 pages indexées sur ~18 700, 0 clic en six
mois. Bing ne découvre le site qu'en repassant de lui-même. IndexNow lui dit, à chaque mise en
ligne, quelles adresses ont bougé : il vient les chercher au lieu d'attendre.

CE QUI EST SIGNALÉ. Les adresses du sitemap (donc jamais une page noindex), et seulement celles
dont le CONTENU a changé depuis le dernier signal réussi. L'empreinte porte sur le <main> de la
page, pas sur le fichier entier : un nouveau hash de bundle JS change tous les fichiers sans
changer une ligne de contenu, et resignaler 14 000 pages à chaque déploiement pour rien finit
par faire ignorer le site. Le premier passage (pas d'état local) signale tout, une fois.

L'ÉTAT. `site/.indexnow/etat.json` (hors Git) : adresse → empreinte, mis à jour SEULEMENT pour
les lots acceptés (200/202). Un lot refusé ou une panne réseau laisse l'état tel quel : ces
pages repartent au déploiement suivant.

NE BLOQUE JAMAIS. La mise en ligne est déjà faite quand ce script tourne : il prévient, il ne
casse rien (code de sortie 0 même en panne réseau). Il refuse en revanche (code 1) si la clé
publiée et la clé lue ne concordent pas — un signal avec une clé invérifiable est rejeté par
tous les moteurs, mieux vaut le savoir.

    uv run python scripts/indexnow_ping.py            # signale ce qui a changé
    uv run python scripts/indexnow_ping.py --dry-run  # compte sans rien envoyer
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "site" / "dist"
PUBLIC = ROOT / "site" / "public"
ETAT = ROOT / "site" / ".indexnow" / "etat.json"
HOST = "scoremydatacenter.org"
ORIGIN = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/indexnow"
LOT = 10_000  # plafond du protocole par requête

_CLE = re.compile(r"^[0-9a-f]{32}$")
_MAIN = re.compile(r"<main\b.*?</main>", re.S | re.I)
_LOC = re.compile(r"<loc>([^<]+)</loc>")


def cle() -> str:
    """La clé = le nom du fichier `<clé>.txt` de site/public, dont le contenu est la clé même."""
    trouvees = [p for p in PUBLIC.glob("*.txt") if _CLE.match(p.stem)]
    if len(trouvees) != 1:
        raise SystemExit(f"indexnow: {len(trouvees)} fichier(s) clé dans site/public (attendu : 1)")
    p = trouvees[0]
    if p.read_text(encoding="utf-8").strip() != p.stem:
        raise SystemExit(f"indexnow: {p.name} ne contient pas sa propre clé — moteurs = refus")
    return p.stem


def adresses(dist: Path = DIST) -> list[str]:
    out: list[str] = []
    for sm in sorted(dist.glob("sitemap-*.xml")):
        if sm.name == "sitemap-index.xml":
            continue
        out += _LOC.findall(sm.read_text(encoding="utf-8"))
    return [u for u in out if u.startswith(ORIGIN + "/")]


def fichier(url: str, dist: Path = DIST) -> Path:
    chemin = url[len(ORIGIN):].lstrip("/")
    if not chemin or chemin.endswith("/"):
        return dist / chemin / "index.html"
    return dist / chemin


def empreinte(p: Path) -> str | None:
    try:
        html = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = _MAIN.search(html)
    return hashlib.sha256((m.group(0) if m else html).encode("utf-8")).hexdigest()[:20]


def a_signaler(urls: list[str], etat: dict[str, str], dist: Path = DIST) -> dict[str, str]:
    """Adresse → nouvelle empreinte, pour les seules pages dont le contenu a changé."""
    neuf: dict[str, str] = {}
    for u in urls:
        e = empreinte(fichier(u, dist))
        if e is not None and etat.get(u) != e:
            neuf[u] = e
    return neuf


def envoyer(key: str, lot: list[str]) -> int:
    corps = json.dumps({"host": HOST, "key": key, "keyLocation": f"{ORIGIN}/{key}.txt",
                        "urlList": lot}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=corps, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    key = cle()
    if not (DIST / f"{key}.txt").exists():
        print(f"indexnow: {key}.txt absent de dist — rebâtir avant de signaler", file=sys.stderr)
        return 1
    urls = adresses()
    etat = json.loads(ETAT.read_text(encoding="utf-8")) if ETAT.exists() else {}
    neuf = a_signaler(urls, etat)
    print(f"indexnow: {len(urls)} adresses au sitemap · {len(neuf)} à signaler"
          + (" (premier passage : tout)" if not etat else ""))
    if a.dry_run or not neuf:
        return 0
    liste = sorted(neuf)
    acceptees = 0
    for i in range(0, len(liste), LOT):
        lot = liste[i:i + LOT]
        try:
            code = envoyer(key, lot)
        except (urllib.error.URLError, OSError) as e:
            print(f"⚠ indexnow: lot {i // LOT + 1} non envoyé ({e}) — repartira au prochain déploiement")
            continue
        if code in (200, 202):
            acceptees += len(lot)
            for u in lot:
                etat[u] = neuf[u]
        else:
            print(f"⚠ indexnow: lot {i // LOT + 1} refusé (HTTP {code}) — repartira au prochain déploiement")
    if acceptees:
        ETAT.parent.mkdir(parents=True, exist_ok=True)
        ETAT.write_text(json.dumps(etat, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"indexnow: {acceptees}/{len(liste)} adresses acceptées")
    return 0


if __name__ == "__main__":
    sys.exit(main())
