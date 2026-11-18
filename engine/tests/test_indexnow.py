# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""IndexNow : une clé vérifiable, et seules les pages au contenu changé repartent.

Les deux défauts qui rendraient le signal inutile sans bruit : une clé que les moteurs ne
peuvent pas vérifier (refus silencieux de tout), et un signal qui renvoie les 14 000 pages à
chaque déploiement parce qu'un hash de bundle a bougé (le site finit ignoré).
"""
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_spec = importlib.util.spec_from_file_location("indexnow_ping", REPO_ROOT / "scripts" / "indexnow_ping.py")
ix = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ix)


def test_cle_unique_et_auto_verifiable():
    key = ix.cle()  # lève si 0 ou 2 fichiers clé, ou si le contenu ≠ le nom
    assert (REPO_ROOT / "site" / "public" / f"{key}.txt").read_text().strip() == key


def test_adresse_vers_fichier():
    d = Path("/d")
    assert ix.fichier("https://scoremydatacenter.org/", d) == d / "index.html"
    assert ix.fichier("https://scoremydatacenter.org/fr/dc/x/", d) == d / "fr/dc/x/index.html"
    assert ix.fichier("https://scoremydatacenter.org/a.txt", d) == d / "a.txt"


def _page(d: Path, rel: str, main: str, bundle: str) -> None:
    p = d / rel / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f'<html><script src="/_astro/{bundle}.js"></script><main>{main}</main></html>')


def test_seul_le_contenu_change_repart(tmp_path):
    urls = ["https://scoremydatacenter.org/a/", "https://scoremydatacenter.org/b/"]
    _page(tmp_path, "a", "note B", "h1")
    _page(tmp_path, "b", "note C", "h1")
    premier = ix.a_signaler(urls, {}, tmp_path)
    assert set(premier) == set(urls)  # premier passage : tout
    # nouveau bundle partout, contenu de b seul modifié → seule b repart
    _page(tmp_path, "a", "note B", "h2")
    _page(tmp_path, "b", "note D", "h2")
    assert set(ix.a_signaler(urls, premier, tmp_path)) == {urls[1]}


def test_page_absente_ne_part_pas(tmp_path):
    assert ix.a_signaler(["https://scoremydatacenter.org/absente/"], {}, tmp_path) == {}
