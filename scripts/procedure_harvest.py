# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
#!/usr/bin/env python3
"""Moissonneur de textes de loi — outil du dossier site/src/content/procedure/.

⚠️ À LANCER DEPUIS UNE SORTIE RÉSEAU AMÉRICAINE pour les États des États-Unis : la plupart
des recueils officiels d'État géobloquent les adresses non américaines, et le symptôme est
une connexion refusée qu'on prendrait pour une panne. Usage :
    python3 scripts/procedure_harvest.py cibles.json resultat.json
où cibles.json est une liste de [nom, citation, url_officielle, motif_regex] — lit la page OFFICIELLE et en extrait la phrase du délai.

Il n'INTERPRÈTE rien : il rapporte le passage brut autour du motif, à charge de l'humain
(ou du modèle) d'en écrire l'affirmation. Un motif absent est un échec rapporté, jamais une
valeur devinée. Repli sur l'instantané Wayback quand l'officiel ne répond pas — en
conservant l'URL officielle comme citation.
"""
import json, re, sys, html, urllib.parse, subprocess, concurrent.futures as cf

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

def get(url, timeout=90):
    """Octets de la page. Un PDF est converti en texte par pdftotext — plusieurs recueils
    d'État (Colorado, Wyoming) ne publient leur code QUE sous cette forme."""
    r = subprocess.run(["curl", "-s", "-L", "-A", UA, "--max-time", str(timeout), url],
                       capture_output=True)
    brut = r.stdout
    if brut[:5] == b"%PDF-":
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(brut); chemin = f.name
        try:
            o = subprocess.run(["pdftotext", "-layout", chemin, "-"], capture_output=True)
            return "\x00PDF\x00" + o.stdout.decode("utf-8", "replace")
        finally:
            os.unlink(chemin)
    return brut.decode("utf-8", "replace")

def texte(brut):
    if brut.startswith("\x00PDF\x00"):           # déjà du texte : ne pas le passer au dé-balisage
        return re.sub(r"\s+", " ", brut[5 + 3:])
    t = re.sub(r"(?is)<(script|style|noscript|head).*?</\1>", " ", brut)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)

def wayback(url):
    q = urllib.parse.quote(url, safe="")
    try:
        d = json.loads(get(f"https://archive.org/wayback/available?url={q}", 30))
        s = d.get("archived_snapshots", {}).get("closest")
        return (s["url"], s["timestamp"]) if s else (None, None)
    except Exception:
        return (None, None)

def moissonne(nom, cite, url, motif, avant=520, apres=360):
    t = texte(get(url))
    via, stamp = None, None
    if len(t) < 2000:
        snap, stamp = wayback(url)
        if snap:
            t, via = texte(get(snap)), snap
    m = re.search(motif, t, re.I)
    if not m:
        return {"etat": nom, "cite": cite, "url": url, "ok": False,
                "pourquoi": "motif absent" if len(t) >= 2000 else f"page vide ({len(t)} car.)",
                "via": via}
    return {"etat": nom, "cite": cite, "url": url, "ok": True,
            "extrait": t[max(0, m.start() - avant): m.start() + apres],
            "via": via, "instantane": stamp}

CIBLES = json.load(open(sys.argv[1]))
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    res = list(ex.map(lambda c: moissonne(*c), CIBLES))
json.dump(res, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
ok = [r for r in res if r["ok"]]
print(f"{len(ok)}/{len(res)} moissonnés")
for r in res:
    if not r["ok"]:
        print(f"  ÉCHEC {r['etat']:18} {r['pourquoi']}")
