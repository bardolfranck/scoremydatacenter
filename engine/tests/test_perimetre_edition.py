# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Une édition de pays couvre SON pays — et le plafond de fichiers le dit avant l'hébergeur.

🔴 CE QUI S'EST PASSÉ LE 2026-11-06. `make deploy` : suite verte, build vert, sept barrières
vertes, puis wrangler — « Pages only supports up to 20,000 files ». 24 047 fichiers, rien de
publié. L'édition néerlandaise bâtissait une page par fiche du MONDE : 3 292 pages, dont
1 702 américaines, servant de la prose anglaise sous une adresse néerlandaise.

LE DÉFAUT N'ÉTAIT PAS LE PLAFOND, c'était un périmètre que personne n'avait déclaré. La
doctrine existait déjà, et par écrit : « 151 fiches NL. point final » (Franck, 2026-11-05).
La barrière d'après-build la connaissait même — elle en gardait une COPIE en dur. Le site,
lui, ne la connaissait pas : il bâtissait tout. Une doctrine tenue à un seul endroit ne tient
que l'endroit où elle est écrite [[liste-a-deux-endroits-ment]].

CE QUE GARDENT CES TESTS, et pourquoi deux et pas un :
· le PÉRIMÈTRE est déclaré pour chaque langue, et la route d'une édition de pays le lit
  vraiment — sans quoi la déclaration est décorative et le build reprend le corpus entier ;
· le PLAFOND est mesuré avant le départ, parce qu'il ne dépend pas de cette cause-là : la
  prochaine langue ou le prochain lot de vignettes le pousseront tout autant
  [[figer-par-test-revele-les-fantomes]].
"""

import importlib
import re
from pathlib import Path

from engine.langues import langues_declarees, pays_de_la_langue, racine_de_la_langue

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PAGES = REPO_ROOT / "site" / "src" / "pages"
FILTRE = "fichesDeLaLangue"


GLOB_DU_CORPUS = "public/data/dc/*.json"


def _routes_du_corpus(lang: str) -> list[Path]:
    """TOUTE route de l'édition d'une langue qui énumère le corpus.

    🔴 JUGÉ SUR LE GESTE, PAS SUR LE NOM DE FICHIER. Mon premier garde ne regardait que
    `dc/[id].astro` — et l'édition néerlandaise avait une SECONDE route, le portrait de
    site, qui globait le corpus elle aussi. Le filtre posé sur la première a fait tomber
    3 292 pages ; le portrait en a sorti 3 292 autres, et le plafond est resté franchi. Un
    garde dont le périmètre est plus étroit que celui du producteur rassure comme un juste
    [[controle-au-mauvais-niveau]].

    Une langue à la RACINE du site (« / ») n'est pas scopable par son dossier : ses routes
    voisinent avec celles de toutes les autres. Aucune langue de pays n'est à la racine
    aujourd'hui ; le jour où ça arrive, ce relevé doit être repris, et l'assertion de
    `test_la_route_dune_edition_de_pays_lit_son_perimetre` le dira en ne trouvant rien.
    """
    racine = racine_de_la_langue()[lang].strip("/")
    if not racine:
        return []
    base = PAGES / racine
    if not base.is_dir():
        return []
    return sorted(
        f
        for f in base.rglob("*")
        if f.is_file()
        and f.suffix in (".astro", ".ts")
        and GLOB_DU_CORPUS in f.read_text(encoding="utf-8")
    )


def test_le_perimetre_est_declare_pour_chaque_langue():
    table = pays_de_la_langue()
    for lang in langues_declarees():
        assert lang in table, f"{lang} n'a pas de périmètre déclaré"
        valeur = table[lang]
        assert valeur == "tous" or (isinstance(valeur, list) and valeur), (
            f"{lang} : le périmètre vaut {valeur!r}. Une liste VIDE ne veut rien dire — "
            f"elle bâtirait une édition sans aucune fiche, et une édition vide ne crie pas "
            f"[[absence-ressemble-a-zero]]."
        )


def test_la_route_dune_edition_de_pays_lit_son_perimetre():
    """Déclarer ne suffit pas : la route doit filtrer.

    C'est exactement l'écart qui a coûté le déploiement — la doctrine écrite d'un côté, le
    build qui globe tout de l'autre.
    """
    table = pays_de_la_langue()
    for lang in langues_declarees():
        if table[lang] == "tous":
            continue
        routes = _routes_du_corpus(lang)
        assert routes, (
            f"{lang} a un périmètre de pays déclaré mais AUCUNE route de son édition "
            f"n'énumère le corpus. Soit l'édition n'existe pas, soit ce relevé ne la voit "
            f"plus — et un relevé vide rend ce test vert sans rien garder."
        )
        nues = [r for r in routes if FILTRE not in r.read_text(encoding="utf-8")]
        assert not nues, (
            "ces routes bâtiront une page pour CHAQUE fiche du monde, en prose de repli sous "
            f"une adresse {lang}, et le sitemap les déclarera toutes : "
            + ", ".join(str(r.relative_to(REPO_ROOT)) for r in nues)
            + ". C'est ce qui a fait 24 047 fichiers le 2026-11-06 — puis 20 907 quand une "
            "seule des deux routes a été filtrée — pour un plafond de 20 000."
        )


def test_le_garde_de_perimetre_mord_vraiment():
    """La route d'avant, privée de son filtre, doit faire crier le garde."""
    de_pays = [lg for lg in langues_declarees() if pays_de_la_langue()[lg] != "tous"]
    assert de_pays, "aucune édition de pays déclarée : le test précédent ne prouve rien"
    for lang in de_pays:
        routes = _routes_du_corpus(lang)
        assert len(routes) >= 2, (
            f"l'édition « {lang} » n'a plus qu'{len(routes)} route(s) qui énumère(nt) le "
            f"corpus. Elle en avait DEUX le 2026-11-06 — la fiche et le portrait — et c'est "
            f"la seconde, oubliée, qui a tenu le plafond franchi."
        )
        for route in routes:
            texte = route.read_text(encoding="utf-8")
            ampute = texte.replace(FILTRE, "Object.values")
            assert FILTRE not in ampute, "la mutilation n'a pas pris, le test ne prouve rien"
            assert ampute != texte


def test_le_plafond_refuse_au_dessus_et_alerte_avant():
    plafond = importlib.import_module("scripts.check_plafond_fichiers")
    assert plafond.LIMITE == 20_000, (
        "la limite n'est pas un réglage : c'est le refus de Cloudflare Pages par "
        "déploiement. La changer sans changer de forfait publie dans le vide."
    )
    assert not plafond.refuse(plafond.LIMITE)
    assert plafond.refuse(plafond.LIMITE + 1)
    assert plafond.refuse(24_047), "le compte du 2026-11-06 doit être refusé"
    assert plafond.alerte(plafond.LIMITE - plafond.MARGE + 1)
    assert not plafond.alerte(plafond.LIMITE - plafond.MARGE)
    assert plafond.MARGE > 0


def test_le_plafond_suit_la_cible(monkeypatch):
    """Pages plafonne à 20 000, le Worker à 100 000 : le même dist ne se mesure pas pareil.

    Le défaut reste Pages — le plafond le plus bas — et une cible inconnue est refusée au
    lieu d'être ramenée au défaut : une faute de frappe ne choisit pas un plafond.
    """
    plafond = importlib.import_module("scripts.check_plafond_fichiers")
    assert plafond.LIMITES == {"pages": 20_000, "worker": 100_000}
    monkeypatch.delenv("CIBLE", raising=False)
    assert plafond.cible() == "pages"
    monkeypatch.setenv("CIBLE", "worker")
    assert plafond.cible() == "worker"
    limite = plafond.LIMITES["worker"]
    assert not plafond.refuse(24_047, limite), "24 047 fichiers rentrent dans un Worker"
    assert plafond.refuse(limite + 1, limite)
    assert plafond.alerte(limite - plafond.MARGE + 1, limite)
    assert not plafond.alerte(24_047, limite)
    monkeypatch.setenv("CIBLE", "wroker")
    try:
        plafond.cible()
    except SystemExit as e:
        assert "inconnue" in str(e)
    else:
        raise AssertionError("une cible inconnue a été acceptée")


def test_le_plafond_refuse_de_conclure_sur_un_dist_maigre(tmp_path, monkeypatch):
    """Un `dist` vide compte zéro et passerait : l'absence ressemble à zéro.

    Le plancher de plausibilité est ce qui distingue « ça rentre » de « je n'ai rien
    mesuré » [[service-degrade-ment-plancher]].
    """
    plafond = importlib.import_module("scripts.check_plafond_fichiers")
    maigre = tmp_path / "dist"
    maigre.mkdir()
    (maigre / "index.html").write_text("<!doctype html>")
    monkeypatch.setattr(plafond, "DIST", maigre)
    try:
        plafond.main()
    except SystemExit as e:
        assert "trop peu" in str(e), f"refus attendu sur le plancher, obtenu : {e}"
    else:
        raise AssertionError(
            "la barrière a conclu sur 1 fichier — elle aurait publié un dist vide sans rien "
            "dire"
        )


def test_le_plafond_compte_les_fichiers_pas_les_repertoires(tmp_path):
    plafond = importlib.import_module("scripts.check_plafond_fichiers")
    for i in range(3):
        d = tmp_path / f"page-{i}"
        d.mkdir()
        (d / "index.html").write_text("x")
    (tmp_path / "racine.txt").write_text("x")
    assert plafond.compte(tmp_path) == 4
    poids = dict((nom, n) for n, nom in plafond.par_repertoire(tmp_path))
    assert poids["(racine)"] == 1 and poids["page-0/"] == 1


def test_le_perimetre_nest_pas_deduit_du_code_de_langue():
    """`nl` → fiches `nl-` est une COÏNCIDENCE, pas une règle.

    Elle tient pour le néerlandais et se trompe pour l'anglais (GB + IE + US). Un périmètre
    déduit d'une coïncidence se tromperait en silence le jour où elle cesse — donc la
    déclaration doit exister en propre, pas être devinable.
    """
    source = (REPO_ROOT / "site" / "src" / "content" / "langues.ts").read_text()
    bloc = re.search(r"PAYS_DE_LA_LANGUE[^=]*=\s*\{(.*?)\n\};", source, re.DOTALL)
    assert bloc, "PAYS_DE_LA_LANGUE a disparu de langues.ts"
    assert '"tous"' in bloc.group(1), (
        "plus aucune édition ne couvre le corpus entier : si le français et l'anglais ont "
        "perdu leur « tous », les deux éditions de référence viennent d'être amputées"
    )
