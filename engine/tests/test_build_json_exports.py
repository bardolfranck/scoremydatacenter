# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Les JSON du site s'importent sans exports nommés — sinon le build casse en grandissant.

🔴 CE QUE CE GARDE A TROUVÉ À SA NAISSANCE (2026-11-28). Le déploiement du jour a échoué sur
« Maximum call stack size exceeded » : les 3 512 fiches importées en `import.meta.glob(eager)`
forment un module de ~61 Mo où Vite déclarait une `const` par clé et par fiche. Une clé de plus
dans l'artefact (`permit_state`) a suffi. Le défaut ne dépend pas du code ajouté mais de la
TAILLE du corpus : il revient à chaque clé ou à chaque millier de fiches si l'option saute.
"""
import re

from engine.core import REPO_ROOT

SITE = REPO_ROOT / "site"


def test_vite_n_exporte_pas_les_cles_json():
    config = (SITE / "astro.config.mjs").read_text(encoding="utf-8")
    assert re.search(r"json:\s*\{\s*namedExports:\s*false\s*\}", config), \
        "astro.config.mjs doit garder vite.json.namedExports = false"


def test_aucun_import_nomme_de_json():
    """Sans exports nommés, `import { x } from "a.json"` casserait : il n'en existe aucun."""
    fautifs = []
    for p in list((SITE / "src").rglob("*.astro")) + list((SITE / "src").rglob("*.ts")):
        if re.search(r"import\s*\{[^}]*\}\s*from\s*['\"][^'\"]+\.json['\"]", p.read_text(encoding="utf-8")):
            fautifs.append(p.relative_to(REPO_ROOT).as_posix())
    assert not fautifs, fautifs


def test_les_globs_json_lisent_default():
    """Un glob eager de JSON se lit par `.default` ; une lecture par clé nommée renverrait undefined."""
    fautifs = []
    for p in list((SITE / "src").rglob("*.astro")) + list((SITE / "src").rglob("*.ts")):
        t = p.read_text(encoding="utf-8")
        if re.search(r"import\.meta\.glob\([^)]*\.json", t) and ".default" not in t:
            fautifs.append(p.relative_to(REPO_ROOT).as_posix())
    assert not fautifs, fautifs
