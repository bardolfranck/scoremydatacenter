# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Un titre qui contient la commune sans la MONTRER ne répond pas à la requête.

🔴 CE QUI S'EST PASSÉ. Les deux cascades de titre (fiche, portrait) dégradent le titre pour
tenir dans un budget d'affichage, et leur commentaire dit, à raison, que « 65 caractères est
une limite d'AFFICHAGE, pas d'indexation » : on tronque plutôt que de supprimer le lieu. Mais
les deux ne dégradaient que le LIEU — la région, puis l'angle — jamais le NOM. Sur les fiches
dont le nom dépasse à lui seul la largeur visible, le lieu restait donc dans la balise et
tombait hors de l'écran : « le lieu ne part jamais » était vrai du titre et faux de ce que
Google montre.

Mesuré sur les 3 292 fiches servies le 2026-11-07 : **14 fiches**, les mêmes sur la fiche et
sur le portrait. Quatre sont des énumérations de codes Amazon, une est le projet Matador.

CE QUE GARDE CE TEST : non pas que la règle existe, mais qu'AUCUN titre servi ne cache ce qui
suit son nom. La 15ᵉ fiche à nom long — et il en viendra, le corpus grossit par sondes — sera
refusée. C'est la même forme que la règle de région [[liste-a-deux-endroits-ment]] : la règle
vit à un seul endroit, `site/src/config/titre.ts`, et le test vérifie le SERVI, pas la source
[[remonter-de-la-chaine-servie]].

⚠️ ET LA COUPE DOIT SE VOIR. Une troncature tombée sur une frontière de mot se lit comme un
nom entier : « … HOSPITALS - MEAD » (60 caractères pile) a été pris pour un nom complet le
2026-11-06, alors qu'il manquait « OWMONT BUILD B » [[noms-tronques-par-la-collecte]].
L'ellipsis n'est pas cosmétique, c'est elle qui empêche le titre d'affirmer un nom faux — un
test le vérifie séparément.
"""

import html
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_SRC = REPO_ROOT / "site" / "src"
DIST = REPO_ROOT / "site" / "dist"
REGLE = SITE_SRC / "config" / "titre.ts"

# La largeur visible, lue dans la règle plutôt que recopiée ici : deux copies d'un seuil
# divergent, et c'est le seuil qui définit la cohorte.
def _visible() -> int:
    m = re.search(r"VISIBLE_SERP\s*=\s*(\d+)", REGLE.read_text(encoding="utf-8"))
    assert m, "VISIBLE_SERP n'est plus déclaré dans config/titre.ts"
    return int(m.group(1))


# 🔴 LA COHORTE, NOMMÉE. Franck a autorisé un geste sur QUATORZE fiches, pas sur une famille
# ouverte. Le compter ne suffit pas : la première version de la règle mélangeait le budget de
# confort (65) et la largeur affichée (57) et raccourcissait **117 fiches** — un élargissement
# silencieux qu'un simple total n'aurait pas montré. Les ids sont donc écrits ici.
#
# Ce que fait ce témoin quand le corpus grossit : il TOMBE. C'est voulu. Une 15ᵉ fiche à nom
# long est une décision (on la raccourcit aussi ? on révise la largeur ?), pas un effet de
# bord. Même discipline que la dette nom/statut : l'ensemble reste déclaré pour refuser le
# premier cas nouveau [[cliquet-nest-pas-verrou]].
COHORTE_NOM_RACCOURCI = {
    "fr-bnp-paribas-centre-de-traitement-informatique-cti-marne-nord",
    "fr-maconnais-beaujolais-agglomeration-mba-et-datavest-capital",
    "fr-sm5-sm6-sm7-credit-mutuel-euro-information-verlinghem",
    "nl-rijksuniversiteit-groningen-coenraad-bron-center-grouwelerie",
    "us-amazon-data-services-iad-130-iad-131-iad-313-and-dca-072",
    "us-amazon-data-services-inc-iad-12-iad-15-iad-16-iad-76-iad-230",
    "us-amazon-data-services-inc-iad-50-iad-60-iad-71-iad-78-iad-79-iad-80",
    "us-amazon-data-services-inc-iad-73-iad-74-iad-602-iad-193-iad-194",
    "us-crane-clean-energy-center-three-mile-island-unit-1-restart",
    "us-east-charlotte-data-center-near-reedy-creek-nature-preserve",
    "us-iskander-lc-1a-jamshid-lc-1b-kaveh-lc2-lohrasp-ventures-lc3",
    "us-ozaukee-county-distribution-interconnection-project-lighthouse",
    "us-project-matador-trump-advanced-energy-and-intelligence-cam",
    "us-university-of-north-carolina-hospitals-mead-inactive",
}


def _titres(motif: str) -> list[tuple[str, Path]]:
    out = []
    for p in DIST.glob(motif):
        m = re.search(r"<title>(.*?)</title>", p.read_text(encoding="utf-8")[:4000], re.S)
        if m:
            out.append((html.unescape(m.group(1)).strip(), p))
    return out


def test_les_deux_surfaces_lisent_la_meme_regle():
    assert REGLE.is_file(), f"{REGLE} manque — la règle partagée est le pivot"
    for nom in ("DcFiche.astro", "SitePortrait.astro"):
        src = (SITE_SRC / "components" / nom).read_text(encoding="utf-8")
        assert "nomVisible(" in src, (
            f"{nom} construit un titre sans la règle de largeur : sa cascade dégradera le "
            "lieu et jamais le nom, et le défaut reviendra par cette surface"
        )


@pytest.mark.parametrize(
    "motif,surface",
    [("dc/*/index.html", "fiche EN"), ("dc/*/portrait/index.html", "portrait EN"),
     ("fr/dc/*/index.html", "fiche FR"), ("fr/dc/*/portrait/index.html", "portrait FR")],
)
def test_aucun_titre_servi_ne_cache_ce_qui_suit_le_nom(motif, surface):
    if not DIST.is_dir():
        pytest.skip("site non construit dans cette copie")
    titres = _titres(motif)
    if not titres:
        pytest.skip(f"aucune page {surface} dans ce dist")
    assert len(titres) > 100, (
        f"seulement {len(titres)} titres {surface} — un contrôle sur un ensemble presque "
        "vide passe toujours"
    )
    limite = _visible()
    fautifs = [(t, p.relative_to(DIST).as_posix())
               for t, p in titres if t.find(" — ") > limite]
    assert not fautifs, (
        f"{len(fautifs)} titre(s) {surface} dont tout ce qui suit le nom commence après le "
        f"{limite}ᵉ caractère — donc hors de ce que Google montre :\n  - "
        + "\n  - ".join(f"{t[:72]}…  ({p})" for t, p in fautifs[:12])
        + "\n→ la cascade doit pouvoir raccourcir le NOM (config/titre.ts), pas seulement "
          "le lieu."
    )


def test_le_nom_du_titre_est_le_nom_SERVI_ou_un_prefixe_marque():
    """La seule lecture qui voit une troncature : confronter le titre au nom que la page a REÇU.

    Deux versions de ce test ont échoué avant celle-ci, et les deux pour la même raison —
    j'ai cherché la vérité au mauvais endroit de la chaîne :

    1. « tout nom qui occupe la largeur utile doit porter une ellipsis » : accusait 30 titres
       innocents. Un nom de 54 caractères est complet, pas coupé. Un titre seul ne dit pas
       s'il a été raccourci.
    2. comparer au nom du CORPUS : accusait 8 titres innocents, parce que le producteur
       NORMALISE le nom avant de le servir (`FREE_PRO_-_ROCK` → `FREE PRO - ROCK`). Le nom
       que la page affiche n'est pas celui du corpus, il est celui de l'artefact
       [[remonter-de-la-chaine-servie]].

    D'où la troisième : on lit `public/data/dc/{id}.json`, exactement ce que la page reçoit.
    Et on ne découpe PAS le titre sur « — » : `fr-montereau-aion` s'appelle « Montereau —
    Vallée de la Seine (AION) », donc le séparateur existe DANS le nom.
    """
    if not DIST.is_dir():
        pytest.skip("site non construit dans cette copie")
    import json

    servis = REPO_ROOT / "site" / "public" / "data" / "dc"
    if not servis.is_dir():
        pytest.skip("artefacts par fiche absents de cette copie")
    noms = {}
    for f in servis.glob("*.json"):
        try:
            noms[f.stem] = json.loads(f.read_text(encoding="utf-8")).get("name") or ""
        except (OSError, ValueError):
            continue

    fautifs, coupes, vus = [], 0, 0
    for titre, p in _titres("dc/*/portrait/index.html"):
        nom = noms.get(p.parent.parent.name)
        if not nom:
            continue
        vus += 1
        if titre.startswith(nom):
            continue  # nom complet : rien à prouver
        # Sinon le titre ne peut être légitime que raccourci : un préfixe du nom, marqué.
        avant = titre.split("\u2026", 1)[0]
        if "\u2026" not in titre or not nom.startswith(avant.rstrip(" /,;:·-–—(")):
            fautifs.append(f"{p.parent.parent.name} : titre « {titre[:60]} » vs nom « {nom} »")
        else:
            coupes += 1
    assert vus > 100, f"seulement {vus} portraits appariés au servi — contrôle presque vide"
    assert not fautifs, (
        "le titre porte un nom qui n'est ni le nom servi, ni un préfixe marqué par une "
        "ellipsis — donc il AFFIRME un nom qui n'existe pas :\n  - "
        + "\n  - ".join(fautifs[:10])
    )
    assert coupes, (
        "aucun titre ne raccourcit son nom alors que le corpus en contient de trop longs : "
        "la marche de la cascade n'est pas atteinte, et ce test passerait sur le vide"
    )


@pytest.mark.parametrize(
    "motif,profondeur,surface",
    [("dc/*/index.html", 1, "fiche EN"), ("dc/*/portrait/index.html", 2, "portrait EN"),
     ("fr/dc/*/index.html", 1, "fiche FR"), ("fr/dc/*/portrait/index.html", 2, "portrait FR")],
)
def test_la_cohorte_raccourcie_est_celle_qui_a_ete_autorisee(motif, profondeur, surface):
    """Quatorze fiches, nommées — et les quatre surfaces doivent tomber sur les MÊMES."""
    if not DIST.is_dir():
        pytest.skip("site non construit dans cette copie")
    titres = _titres(motif)
    if not titres:
        pytest.skip(f"aucune page {surface} dans ce dist")
    vus = set()
    for titre, p in titres:
        if "\u2026" in titre:
            dossier = p.parent if profondeur == 1 else p.parent.parent
            vus.add(dossier.name)
    nouvelles = sorted(vus - COHORTE_NOM_RACCOURCI)
    parties = sorted(COHORTE_NOM_RACCOURCI - vus)
    assert not nouvelles, (
        f"{len(nouvelles)} fiche(s) hors cohorte voient leur nom raccourci sur {surface} :\n  - "
        + "\n  - ".join(nouvelles[:12])
        + "\n→ soit la règle s'est élargie sans qu'on le décide, soit le corpus a grossi et "
          "c'est une décision à prendre, puis à écrire dans COHORTE_NOM_RACCOURCI."
    )
    assert not parties, (
        f"{len(parties)} fiche(s) de la cohorte ne sont plus raccourcies sur {surface} :\n  - "
        + "\n  - ".join(parties[:12])
        + "\n→ leur nom a-t-il changé ? la règle s'est-elle désarmée ? Un témoin qui maigrit "
          "tout seul est un témoin qui ne garde plus rien."
    )
