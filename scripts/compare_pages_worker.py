#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le Worker sert-il EXACTEMENT ce que sert Pages ? Comparaison octet par octet.

POURQUOI. Le site quitte Cloudflare Pages (plafond : 20 000 fichiers par déploiement) pour
un Worker avec fichiers statiques (100 000). Les deux hébergements ne traitent pas pareil
les barres finales, les `index.html`, les 404, `_redirects` et `_headers`. Une différence
là-dessus ne casse aucun test : elle change une redirection pour 13 000 URL indexées.
On ne la devine pas, on la mesure.

COMMENT. Deux serveurs locaux sur le MÊME `site/dist` :
    cd site && npx wrangler pages dev dist --port 8788                     # la référence
    cd site && npx wrangler dev --config wrangler.worker.jsonc --port 8789 # le candidat
puis :
    uv run python scripts/compare_pages_worker.py

Chaque URL est demandée aux deux, SANS suivre les redirections. On compare le code, tous
les en-têtes de réponse (sauf ceux qui changent à chaque requête, liste `VOLATILS`) et le
SHA-256 du corps. Sortie : un JSON complet et un résumé Markdown. Les écarts connus et sans
effet sont nommés un par un (`explication`) ; tout autre écart fait sortir le script en 1.

CE QUE ÇA NE PROUVE PAS. Les deux serveurs sont des émulations locales (miniflare). Elles
reprennent le code de routage de la production, pas le réseau de Cloudflare : le cache du
bord, la compression et HTTP/2 ne sont pas dans la mesure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests

RACINE = Path(__file__).resolve().parents[1]
DIST = RACINE / "site" / "dist"

# En-têtes qui diffèrent d'une requête à l'autre ou d'un processus à l'autre, sans rien
# dire de ce que reçoit le visiteur. Tout le reste est comparé.
VOLATILS = {"date", "cf-ray", "connection", "keep-alive", "transfer-encoding", "server",
            "report-to", "nel", "cf-cache-status", "alt-svc", "content-length",
            "content-encoding", "vary",
            # posé par `wrangler pages dev` seulement (« dev ») : absent de la production.
            "x-server-env"}
# Ceux qu'on veut voir nommés dans le résumé même quand ils sont égaux.
SUIVIS = ("location", "content-type", "cache-control", "x-robots-tag")

# Un site qui existe dans la carte (pour les appels d'API) — demandé par la consigne.
ID_TEMOIN = "fr-cogent-bordeaux"


def chemin_url(rel: str) -> str:
    return "/" + quote(rel, safe="/~!$&'()*+,;=:@")


def urls_fichiers() -> list[str]:
    return sorted(chemin_url(p.relative_to(DIST).as_posix()) for p in DIST.rglob("*") if p.is_file())


def urls_sitemap() -> list[str]:
    sortie = []
    for f in sorted(DIST.glob("sitemap-*.xml")):
        for loc in re.findall(r"<loc>([^<]+)</loc>", f.read_text()):
            u = urlsplit(loc.strip())
            if u.path:
                sortie.append(u.path + (f"?{u.query}" if u.query else ""))
    return sortie


def urls_variantes(fichiers: list[str]) -> list[str]:
    """Chaque page sans sa barre finale ; chaque `x.html` sans extension et avec barre."""
    sortie = []
    for u in fichiers:
        if u.endswith("/index.html"):
            base = u[: -len("index.html")]
            if base != "/":
                sortie.append(base.rstrip("/"))
            sortie.append(base)
            sortie.append(base + "index")
        elif u.endswith(".html"):
            sortie.append(u[: -len(".html")])
            sortie.append(u[: -len(".html")] + "/")
    return sortie


def urls_redirections() -> list[str]:
    """Les sources de `_redirects`, telles quelles, sans barre, et avec une requête."""
    sortie = []
    red = DIST / "_redirects"
    if not red.exists():
        return sortie
    for ligne in red.read_text().splitlines():
        mots = ligne.split()
        if len(mots) < 2 or mots[0].startswith("#"):
            continue
        src = mots[0]
        if "*" in src:
            src = src.replace("*", "temoin-" + "x" * 6 + ".json")
        sortie += [src, src.rstrip("/") or "/", src + "?utm_source=test"]
    return sortie


def urls_divers() -> list[str]:
    dc = sorted((RACINE / "site" / "public" / "data" / "dc").glob("*.json"))[:5]
    return [
        "/", "/index.html", "/fr", "/fr/", "/fr/index.html", "//", "/fr//",
        "/nope", "/nope/", "/nope.html", "/nope/deeper/still/", "/fr/nope/", "/dc/nope/",
        "/dc/nope/portrait/", "/assets/nope.js", "/_astro/nope.css", "/data/nope.json",
        "/data/nope.geojson", "/404", "/404/", "/404.html", "/_redirects", "/_headers",
        "/_routes.json", "/_worker.js", "/functions/api/classement.ts",
        "/data/map.geojson", "/data/watchlist.geojson", "/data/gone.json", "/data/scores.json",
        "/data/latest.json", "/data/dc/", "/data/dc", "/data/comparator/fr.json",
        "/data/actu/latest.json", "/data/lieux/regions.json", "/robots.txt", "/llms.txt",
        "/sitemap-index.xml", "/favicon.ico", "/favicon.svg", "/.well-known/security.txt",
        "/?utm_source=x", "/fr/?dc=" + ID_TEMOIN, "/FR/", "/Fr/classement/",
        "/fr/classement/?page=2", "/fr/classement?page=2", "/%66r/", "/fr/%2e%2e/",
        "/fr/dc/" + ID_TEMOIN, "/fr/dc/" + ID_TEMOIN + "/", "/fr/dc/" + ID_TEMOIN + "/index.html",
        "/fr/dc/" + ID_TEMOIN + "/portrait", "/dc/" + ID_TEMOIN + ".html",
        "/api", "/api/", "/api/nope", "/api/carte", "/api/carte/", "/api/carte/nope",
        "/api/report", "/api/report/nope", "/api/classement/", "/api/carte/site/",
    ] + [f"/data/dc/{p.name}" for p in dc]


def appels_api() -> list[tuple[str, str, dict | None, bytes | None]]:
    """(méthode, url, en-têtes, corps). Jamais d'adresse valide : aucun courriel ne part."""
    j = {"content-type": "application/json"}
    g = [
        "/api/carte/site?t=0", "/api/carte/site?t=99999", "/api/carte/site?t=-1",
        "/api/carte/site?t=abc", "/api/carte/site", f"/api/carte/site?id={ID_TEMOIN}",
        "/api/carte/site?id=nope", "/api/carte/recherche?q=equinix", "/api/carte/recherche?q=",
        "/api/carte/recherche", "/api/carte/recherche?q=bordeaux", "/api/carte/recherche?q=%C3%A9",
        f"/api/carte/voisins?id={ID_TEMOIN}", "/api/carte/voisins?id=nope", "/api/carte/voisins",
        "/api/veille/site?t=0", "/api/veille/site?t=99999", "/api/veille/site",
        "/api/classement?src=/fr/classement/&page=2", "/api/classement?src=/fr/classement/",
        "/api/classement?src=/classement/&page=3", "/api/classement?src=/ranking/&page=2",
        "/api/classement?src=/fr/classement/&tri=water&ordre=asc",
        "/api/classement?src=/fr/classement/&q=equinix",
        "/api/classement?src=/fr/classement/&lieu=46.257,6.11",
        "/api/classement?src=/fr/classement/&lieu=abc",
        "/api/classement?src=/fr/classement/&statut=operational&page=1",
        "/api/classement?src=/fr/classement/&page=99999", "/api/classement?src=/nope/",
        "/api/classement", "/api/report/subscribe", "/api/report/confirm",
        "/api/report/confirm?token=deadbeef", "/api/report/confirm?token=" + "0" * 64,
        "/api/report/download", "/api/report/download?token=deadbeef",
        "/api/report/download?token=" + "0" * 64, "/api/report/unsubscribe",
        "/api/report/unsubscribe?token=deadbeef", "/api/report/unsubscribe?token=" + "0" * 64,
    ]
    appels = [("GET", u, None, None) for u in g]
    appels += [("HEAD", u, None, None) for u in (
        "/", "/fr/", "/fr", "/nope", "/data/map.geojson", "/data/dc/x.json",
        "/api/carte/site?t=0", "/api/classement?src=/fr/classement/&page=2",
        "/api/report/subscribe")]
    appels += [("OPTIONS", u, None, None) for u in ("/", "/api/carte/site?t=0", "/api/report/subscribe")]
    appels += [
        ("POST", "/api/report/subscribe", None, None),
        ("POST", "/api/report/subscribe", j, b"not json"),
        ("POST", "/api/report/subscribe", j, b"{}"),
        ("POST", "/api/report/subscribe", j, b'{"consent":false}'),
        ("POST", "/api/report/subscribe", j, b'{"consent":true}'),
        ("POST", "/api/report/subscribe", j, b'{"consent":true,"report":"nope"}'),
        ("POST", "/api/report/subscribe", j, b'{"consent":true,"company":"bot","email":"x"}'),
        ("POST", "/api/report/unsubscribe", None, None),
        ("POST", "/api/report/unsubscribe?token=deadbeef", None, None),
        ("POST", "/api/report/confirm", None, None),
        ("POST", "/api/carte/site?t=0", None, None),
        ("POST", "/api/classement?src=/fr/classement/", None, None),
        ("POST", "/", None, None), ("POST", "/fr/", None, None), ("POST", "/nope", None, None),
        ("PUT", "/api/carte/site?t=0", None, None), ("DELETE", "/fr/", None, None),
    ]
    return appels


def rapports_invalides() -> list[tuple[str, str, dict | None, bytes | None]]:
    """Un rapport RÉEL avec une adresse au format invalide : la validation doit refuser de
    la même façon des deux côtés, avant tout accès à la base ou à l'envoi."""
    src = RACINE / "site" / "functions" / "_shared" / "reports.ts"
    slugs = sorted(set(re.findall(r'slug:\s*"([^"]+)"', src.read_text()))) if src.exists() else []
    j = {"content-type": "application/json"}
    return [("POST", "/api/report/subscribe", j,
             json.dumps({"consent": True, "report": s, "email": "pas-une-adresse", "lang": "fr"}).encode())
            for s in slugs[:4]]


def demande(session: requests.Session, base: str, appel) -> dict:
    methode, url, entetes, corps = appel
    for essai in range(3):
        try:
            r = session.request(methode, base + url, headers=entetes, data=corps,
                                allow_redirects=False, timeout=60)
            h = {k.lower(): v for k, v in r.headers.items() if k.lower() not in VOLATILS}
            return {"status": r.status_code, "headers": h,
                    "sha": hashlib.sha256(r.content).hexdigest(), "len": len(r.content)}
        except requests.RequestException as e:  # noqa: PERF203
            err = f"{type(e).__name__}: {e}"
            time.sleep(0.5 * (essai + 1))
    return {"status": -1, "headers": {}, "sha": "", "len": 0, "erreur": err}


def ecarts(a: dict, b: dict) -> list[str]:
    """La NATURE de chaque écart, formulée pour que des écarts de même cause se groupent."""
    sortie = []
    if a["status"] != b["status"]:
        sortie.append(f"code {a['status']} → {b['status']}")
    for k in sorted(set(a["headers"]) | set(b["headers"])):
        va, vb = a["headers"].get(k), b["headers"].get(k)
        if va == vb:
            continue
        if va is None:
            sortie.append(f"en-tête {k} : ajouté par le Worker")
        elif vb is None:
            sortie.append(f"en-tête {k} : absent du Worker")
        elif k in SUIVIS:
            sortie.append(f"en-tête {k} : valeur différente")
        else:
            sortie.append(f"en-tête {k} : valeur différente")
    if a["sha"] != b["sha"]:
        sortie.append("corps différent")
    return sortie


# 🔴 UN ÉCART EXPLIQUÉ N'EST PAS UN ÉCART TU. Les deux hébergements ne sont pas le même
# logiciel : certaines réponses diffèrent sans que le visiteur ni un moteur n'y voient rien.
# Chaque règle ci-dessous nomme UN écart mesuré, dit pourquoi il existe et ce qu'il change.
# Elle ne reconnaît que sa forme exacte : tout écart qui n'entre dans aucune reste « à
# examiner » et fait échouer le script. Ajouter une règle ici est une décision, pas un réglage.
NO_STORE, REVALIDE = "no-store", "public, max-age=0, must-revalidate"


def explication(appel, a: dict, b: dict, e: list[str]) -> str | None:
    methode, url = appel[0], appel[1]
    chemin = url.split("?")[0]
    ha, hb = a["headers"], b["headers"]
    natures = set(e)
    meme_corps = a["sha"] == b["sha"]
    meme_code = a["status"] == b["status"]
    etag = {"en-tête etag : valeur différente", "en-tête etag : ajouté par le Worker",
            "en-tête etag : absent du Worker"}
    if meme_code and meme_corps and natures == {"en-tête etag : valeur différente"}:
        return ("etag calculé autrement (même corps) — le navigateur revalide une fois après "
                "la bascule, puis plus rien")
    if (a["status"], b["status"]) == (308, 307) and ha.get("location") == hb.get("location") \
            and (chemin.endswith(".html") or chemin.endswith("/")) and natures == {"code 308 → 307"}:
        return ("adresse en `.html` explicite (/x/index.html, /404.html) ou barre en trop sur un "
                "fichier (/404/) : redirection 307 au lieu de 308, même cible — aucune page, "
                "aucun plan de site ne lie ces adresses")
    if meme_code and a["status"] == 301 and ha.get("location") == hb.get("location") \
            and natures <= {"corps différent", "en-tête content-type : absent du Worker"}:
        return ("301 de `_redirects` : même code, même cible ; Pages joint un corps texte de "
                "quelques octets, le Worker n'en joint pas")
    if meme_code and meme_corps and a["status"] == 404 and ha.get("cache-control") == NO_STORE \
            and hb.get("cache-control") in (REVALIDE, "no-store, max-age=0") \
            and natures <= {"en-tête cache-control : valeur différente"} | etag:
        return ("page 404 : même page ; `no-store` sous Pages, « à revalider à chaque fois » "
                "sous le Worker — dans les deux cas elle n'est jamais servie périmée")
    if meme_code and meme_corps and ha.get("content-type") == "application/javascript" \
            and (hb.get("content-type") or "").startswith("text/javascript") \
            and natures <= {"en-tête content-type : valeur différente"} | etag:
        return "script JS : `application/javascript` devient `text/javascript`, les deux sont valides"
    if a["status"] == 502 and b["status"] == 404 and chemin in ("/_headers", "/_redirects"):
        return ("/_headers et /_redirects : erreur 502 de `wrangler pages dev` (la production "
                "Pages répond 404, mesuré) ; le Worker répond 404")
    if "//" in chemin and a["status"] in (200, 404) and b["status"] == 307:
        return ("double barre dans l'adresse (// ou /fr//) : Pages sert la page telle quelle, "
                "le Worker redirige vers l'adresse propre")
    if chemin != chemin.lower() and a["status"] == 200 and b["status"] == 404:
        return ("majuscules dans l'adresse (/FR/) : `wrangler pages dev` lit un disque macOS "
                "insensible à la casse ; la production Pages répond 404 (mesuré), comme le Worker")
    if chemin.startswith("/api/") and chemin.endswith("/") and ha.get("x-robots-tag") \
            and b["status"] == 404 and not hb.get("x-robots-tag"):
        return ("route d'API avec une barre finale (/api/classement/) : Pages la tolère, le "
                "Worker rend la page 404 — aucun appel du site n'écrit cette forme (vérifié)")
    if chemin.rsplit("/", 1)[-1] in (".DS_Store", ".assetsignore") and a["status"] == 200 and b["status"] == 404:
        return ("fichier écarté du Worker par `.assetsignore` (.DS_Store, .assetsignore) : "
                "`wrangler pages dev` le sert en local, la production Pages écarte déjà .DS_Store")
    if methode == "GET" and chemin.endswith(".html") and a["status"] == 404 and b["status"] == 307:
        return ("/x.html pour une page servie en /x/ : 404 sous Pages, redirection vers la "
                "page sous le Worker")
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pages", default="http://127.0.0.1:8788")
    ap.add_argument("--worker", default="http://127.0.0.1:8789")
    ap.add_argument("--concurrence", type=int, default=16)
    ap.add_argument("--limite", type=int, default=0, help="n'échantillonner que N URL de fichiers (essai)")
    ap.add_argument("--sortie", default=str(RACINE / "site" / ".compare-pages-worker"))
    args = ap.parse_args()

    if not DIST.is_dir():
        raise SystemExit(f"{DIST} n'existe pas : lancez le build d'abord.")

    fichiers = urls_fichiers()
    familles = {
        "fichier de dist": fichiers,
        "URL du sitemap": urls_sitemap(),
        "variante (barre finale, index, .html)": urls_variantes(fichiers),
        "source de _redirects": urls_redirections(),
        "divers (404, bouchons, casse)": urls_divers(),
    }
    appels, vus = [], set()
    for famille, urls in familles.items():
        if args.limite:
            pas = max(1, len(urls) // args.limite)
            urls = urls[::pas]
        for u in urls:
            if ("GET", u) not in vus:
                vus.add(("GET", u))
                appels.append((famille, ("GET", u, None, None)))
    appels += [("API", a) for a in appels_api() + rapports_invalides()]
    compte_famille = defaultdict(int)
    for famille, _ in appels:
        compte_famille[famille] += 1
    print(f"{len(appels)} requêtes par serveur · " + " · ".join(f"{k} {v}" for k, v in compte_famille.items()),
          flush=True)

    def session() -> requests.Session:
        s = requests.Session()
        ad = requests.adapters.HTTPAdapter(pool_connections=args.concurrence, pool_maxsize=args.concurrence)
        s.mount("http://", ad)
        s.headers.update({"accept-encoding": "identity", "user-agent": "compare-pages-worker"})
        return s

    sp, sw = session(), session()
    t0 = time.time()
    fait = [0]

    def une(item):
        famille, appel = item
        a, b = demande(sp, args.pages, appel), demande(sw, args.worker, appel)
        fait[0] += 1
        if fait[0] % 2000 == 0:
            print(f"  {fait[0]}/{len(appels)} · {time.time() - t0:.0f}s", flush=True)
        return famille, appel, a, b

    with ThreadPoolExecutor(args.concurrence) as pool:
        resultats = list(pool.map(une, appels))

    groupes: dict[str, list] = defaultdict(list)
    expliques: dict[str, list] = defaultdict(list)
    differents, erreurs = [], 0
    codes = defaultdict(int)
    for famille, appel, a, b in resultats:
        codes[a["status"]] += 1
        if a["status"] == -1 or b["status"] == -1:
            erreurs += 1
        e = ecarts(a, b)
        if e:
            pourquoi = explication(appel, a, b, e) if -1 not in (a["status"], b["status"]) else None
            differents.append({"famille": famille, "methode": appel[0], "url": appel[1],
                               "corps": appel[3].decode() if appel[3] else None,
                               "ecarts": e, "explication": pourquoi, "pages": a, "worker": b})
            if pourquoi:
                expliques[pourquoi].append((famille, appel, a, b, e))
                continue
            for nature in e:
                groupes[nature].append((famille, appel, a, b))

    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "resultat.json").write_text(json.dumps({
        "requetes": len(appels), "par_famille": dict(compte_famille),
        "codes_pages": {str(k): v for k, v in sorted(codes.items())},
        "erreurs_reseau": erreurs, "differentes": len(differents),
        "identiques": len(appels) - len(differents),
        "expliquees": {k: len(v) for k, v in sorted(expliques.items(), key=lambda kv: -len(kv[1]))},
        "a_examiner": sum(1 for d in differents if not d["explication"]),
        "par_nature": {k: len(v) for k, v in sorted(groupes.items(), key=lambda kv: -len(kv[1]))},
        "details": differents,
    }, ensure_ascii=False, indent=1))

    md = ["# Comparaison Pages ↔ Worker", "",
          f"- **{len(appels)} requêtes** par serveur, en {time.time() - t0:.0f} s "
          f"(Pages `{args.pages}`, Worker `{args.worker}`)",
          "- par famille : " + " · ".join(f"{k} {v}" for k, v in compte_famille.items()),
          "- codes rendus par Pages : " + " · ".join(f"{k} × {v}" for k, v in sorted(codes.items())),
          f"- erreurs réseau : {erreurs}",
          f"- strictement identiques (code, en-têtes, corps) : **{len(appels) - len(differents)}**",
          f"- écart expliqué et sans effet : **{sum(len(v) for v in expliques.values())}**",
          f"- **écart à examiner : {sum(1 for d in differents if not d['explication'])}**", ""]
    if not differents:
        md.append("**Zéro différence** : même code, mêmes en-têtes, même corps partout.")
    if expliques:
        md += ["# Écarts expliqués", ""]
    for pourquoi, items in sorted(expliques.items(), key=lambda kv: -len(kv[1])):
        md += [f"## {len(items)} × {pourquoi}", ""]
        for famille, appel, a, b, e in items[:3]:
            md.append(f"- `{appel[0]} {appel[1]}` — Pages {a['status']} · Worker {b['status']} — "
                      + " ; ".join(e))
        md.append("")
    if groupes:
        md += ["# Écarts à examiner (par nature)", ""]
    for nature, items in sorted(groupes.items(), key=lambda kv: -len(kv[1])):
        par_famille = defaultdict(int)
        for famille, *_ in items:
            par_famille[famille] += 1
        md += [f"## {nature} — {len(items)}", "",
               "Familles : " + " · ".join(f"{k} {v}" for k, v in par_famille.items()), ""]
        for famille, appel, a, b in items[:3]:
            md.append(f"- `{appel[0]} {appel[1]}`" + (f" corps `{appel[3].decode()}`" if appel[3] else ""))
            cle = nature.split(" ")[1] if nature.startswith("en-tête") else None
            if cle:
                md.append(f"  - Pages : `{a['headers'].get(cle)}` · Worker : `{b['headers'].get(cle)}`")
            else:
                md.append(f"  - Pages : {a['status']} · {a['len']} o · `{a['headers'].get('location', '')}` "
                          f"— Worker : {b['status']} · {b['len']} o · `{b['headers'].get('location', '')}`")
        md.append("")
    (sortie / "resume.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:10]))
    for pourquoi, items in sorted(expliques.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(items):>6d}  expliqué : {pourquoi[:110]}")
    for nature, items in sorted(groupes.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(items):>6d}  À EXAMINER : {nature}")
    print(f"→ {sortie}/resume.md · {sortie}/resultat.json")
    if erreurs:
        return 2
    return 1 if groupes else 0


if __name__ == "__main__":
    sys.exit(main())
