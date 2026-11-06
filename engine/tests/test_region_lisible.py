# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Une règle d'affichage ne tient que si TOUTES ses surfaces la lisent.

🔴 CE QUI S'EST PASSÉ LE 2026-11-06. `admin_area` est hétérogène par construction : un nom
(« New York »), un numéro de département (« 59 »), ou un CODE de subdivision (`ENG`, `VAN`).
La règle de lecture est écrite une fois, dans `site/src/config/lieu.ts` : on garde ce qui se
lit, on cache le code. Je l'ai câblée sur la fiche, le portrait et l'image sociale — et j'ai
publié en annonçant « 0 description portant un code ». C'était vrai des descriptions. Mais
les pages de chiffres clés par pays servaient encore « antwerpdc — Antwerpen (VAN) » et
« LDeX2 — Trafford (ENG) » : une QUATRIÈME surface, que j'ai trouvée en cherchant le code
dans le `dist` servi, pas dans le code source [[remonter-de-la-chaine-servie]].

CE QUE GARDE CE TEST : non pas que la règle existe, mais qu'aucune surface servie n'imprime
`admin_area` SANS passer par elle. La prochaine page qui affiche un lieu — et il en viendra,
une par langue et par pays — sera refusée tant qu'elle ne lit pas la règle commune. C'est la
même leçon qu'une liste tenue à deux endroits [[liste-a-deux-endroits-ment]] : ici la liste
est une règle, et ses copies sont des oublis.

⚠️ CE QUI RESTE AUTORISÉ, nommément : `config/related.ts` compare des `admin_area` pour
grouper des fiches voisines. Il ne les AFFICHE pas — un code est une clé de regroupement
parfaitement valable. Le test juge l'affichage, pas la lecture.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_SRC = REPO_ROOT / "site" / "src"
REGLE = SITE_SRC / "config" / "lieu.ts"

# Les surfaces SERVIES : ce qui finit en HTML ou en image sous les yeux d'un lecteur.
SURFACES = ("components", "pages")

# Les fichiers qui manipulent `admin_area` sans jamais l'afficher. Nommés, pas devinés.
SANS_AFFICHAGE = {
    "config/related.ts": "compare des admin_area pour grouper les fiches voisines",
}


def _fichiers_servis() -> list[Path]:
    fichiers: list[Path] = []
    for dossier in SURFACES:
        racine = SITE_SRC / dossier
        if not racine.is_dir():
            continue
        for f in racine.rglob("*"):
            if f.is_file() and f.suffix in {".astro", ".ts", ".tsx"}:
                fichiers.append(f)
    assert len(fichiers) > 50, (
        f"seulement {len(fichiers)} surfaces trouvées sous {SURFACES} — "
        "un contrôle sur un ensemble vide passe toujours"
    )
    return fichiers


def _affiche_le_code_brut(source: str) -> list[str]:
    """Les endroits où `admin_area` est interpolé dans du texte, hors règle commune."""
    fautes = []
    for ligne in source.splitlines():
        if "admin_area" not in ligne:
            continue
        # Un appel à la règle commune porte déjà le champ en argument : c'est conforme.
        if "regionLisible(" in ligne or "communeEtRegion(" in ligne:
            continue
        # `addressRegion` est du balisage Schema.org : lu par une machine qui ATTEND un code
        # de subdivision. Le masquage est une règle d'affichage, pas une correction de la
        # donnée — lieu.ts le dit en propres termes, et c'est la seule sortie brute voulue.
        if "addressRegion" in ligne:
            continue
        # Une interpolation (`${...}`) ou une accolade JSX autour du champ = de l'affichage.
        if re.search(r"\$\{[^}]*admin_area", ligne) or re.search(r"\{[^{}]*admin_area[^{}]*\}", ligne):
            fautes.append(ligne.strip())
    return fautes


def test_la_regle_de_region_existe_et_tranche():
    """La règle est écrite une fois, et elle décide des trois cas qu'on lui a soumis."""
    assert REGLE.is_file(), f"{REGLE} manque : la règle d'affichage n'a plus de source unique"
    source = REGLE.read_text(encoding="utf-8")
    for nom in ("regionLisible", "communeEtRegion"):
        assert f"export function {nom}" in source, f"{nom} n'est plus exportée par lieu.ts"


def test_aucune_surface_servie_nimprime_le_code_brut():
    """Toute surface qui AFFICHE une zone administrative passe par la règle commune."""
    coupables: dict[str, list[str]] = {}
    for f in _fichiers_servis():
        rel = str(f.relative_to(SITE_SRC))
        if rel in SANS_AFFICHAGE:
            continue
        fautes = _affiche_le_code_brut(f.read_text(encoding="utf-8"))
        if fautes:
            coupables[rel] = fautes
    assert not coupables, (
        "des surfaces servies affichent `admin_area` sans passer par lieu.ts — "
        "un code de subdivision (`ENG`, `VAN`) y sera servi comme un nom de région :\n"
        + "\n".join(f"  · {k}\n      {v[0][:120]}" for k, v in coupables.items())
    )


def test_le_test_voit_une_surface_fautive():
    """Contre-épreuve : la forme qu'avait la page de chiffres clés doit être refusée."""
    fautif = '<span class="stx-projloc"> — {e.municipality}{e.admin_area ? ` (${e.admin_area})` : ""}</span>'
    assert _affiche_le_code_brut(fautif), (
        "le détecteur ne reconnaît plus la forme exacte qui servait « Antwerpen (VAN) »"
    )
    conforme = '<span class="stx-projloc"> — {communeEtRegion(e.municipality, e.admin_area)}</span>'
    assert not _affiche_le_code_brut(conforme), "le détecteur accuse la forme conforme"


def test_les_exemptions_sont_reelles():
    """Un fichier exempté doit exister, et vraiment contenir le champ qu'on l'excuse d'avoir."""
    for rel, motif in SANS_AFFICHAGE.items():
        f = SITE_SRC / rel
        assert f.is_file(), f"exemption périmée : {rel} n'existe plus ({motif})"
        assert "admin_area" in f.read_text(encoding="utf-8"), (
            f"exemption inutile : {rel} ne porte plus `admin_area` ({motif})"
        )
