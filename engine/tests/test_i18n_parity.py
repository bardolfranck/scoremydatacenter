# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""FR ↔ EN parity invariant (i18n §13) — the build breaks when a language drifts.

EN silently lagged FR twice (old contradictoire copy, fiche links landing on FR).
Doctrine: shared templates + per-language t objects; this test makes the drift
mechanical to catch: every FR page has its EN twin, and paired thin pages define
t objects with the SAME top-level keys (a string added on one side without its
translation breaks the suite).
"""

import re

import pytest

from engine.core import REPO_ROOT
from engine.tests.i18n_table import bloc, chemins

PAGES = REPO_ROOT / "site" / "src" / "pages"

# Une paire dont la copie a QUITTÉ les deux pages pour un module partagé : la parité s'y lit
# entre les blocs par langue, et non plus entre deux littéraux `t` tenus à la main.
# La fiche a ouvert la voie le 2026-10-29 (127 clés, écrites deux fois jusque-là).
TABLES_PARTAGEES: dict[str, tuple] = {
    "fr/dc/[id].astro": (REPO_ROOT / "site" / "src" / "content" / "fiche.ts", "FR"),
    "dc/[id].astro": (REPO_ROOT / "site" / "src" / "content" / "fiche.ts", "EN"),
}

# (FR page, EN twin, compare t keys?) — routes differ by design (localised slugs).
PAIRS = [
    ("fr/index.astro", "index.astro", True),
    ("fr/dc/[id].astro", "dc/[id].astro", True),
    ("fr/classement.astro", "ranking.astro", True),
    ("fr/carte.astro", "map.astro", False),          # inline labels, no t object
    ("fr/methodologie.astro", "methodology.astro", True),
    ("fr/mentions-legales.astro", "legal.astro", False),  # t.sections carry prose, headings differ per language
    ("fr/contact.astro", "contact.astro", False),
    ("fr/comprendre.astro", "understand.astro", True),
    ("fr/comprendre/one-pager.astro", "understand/one-pager.astro", False),
    ("fr/bibliotheque.astro", "intelligence.astro", True),
    ("fr/bibliotheque/tous.astro", "intelligence/all.astro", True),
]
# FR-only internal tooling, exempt from parity: fr/apercu-partage.astro (OG preview gallery).

# Deliberate asymmetries: keys one language needs and the other, by design, does not.
# understand (EN) flags the France-centric content ("In France" tags + context notice);
# the FR page needs no such flag. Anything NOT listed here must exist on both sides.
# `blocks.*.tag` carries that same "France" flag inside the nested blocks: it only became
# visible when this test started reading NESTED paths (2026-10-29) — the top-level-only
# comparison had never seen it. Same asymmetry, same reason, just one level down.
EXTRA_OK: dict[str, set[str]] = {
    "understand.astro": {"contextNotice", "inFranceLabel"},
}
# Nested paths exempted for the same reason, matched on their LAST segment: the France flag
# repeats under every block, and listing each full path would be a list that rots.
EXTRA_OK_IMBRIQUE: dict[str, set[str]] = {
    "understand.astro": {"tag"},
}


def _t_keys(page: str) -> set[str]:
    """The NESTED key paths of a page's copy — `a`, `a.b`, `a.b.c`.

    Top-level keys alone let a whole nested group drift unseen: the fiche's two literals
    differed by ten lines and nobody could tell whether that was wrapping or a missing
    group. Paths answer it. The copy is read from the page's `t` literal, or — once a pair
    has moved its copy out — from the shared module named in TABLES_PARTAGEES.
    """
    if page in TABLES_PARTAGEES:
        fichier, declaration = TABLES_PARTAGEES[page]
        return chemins(bloc(fichier.read_text(encoding="utf-8"), declaration))
    return chemins(bloc((PAGES / page).read_text(encoding="utf-8"), "t"))


def _sans_exemptions(cles: set[str], page: str) -> set[str]:
    nus = EXTRA_OK.get(page, set())
    feuilles = EXTRA_OK_IMBRIQUE.get(page, set())
    return {
        c for c in cles
        if c not in nus and c.split(".")[0] not in nus and c.split(".")[-1] not in feuilles
    }


def test_every_fr_page_has_its_en_twin():
    for fr, en, _ in PAIRS:
        assert (PAGES / fr).exists(), f"FR page missing: {fr}"
        assert (PAGES / en).exists(), (
            f"EN twin missing for {fr}: expected {en} — FR and EN advance together (i18n §13)"
        )


def test_paired_t_objects_share_their_keys():
    for fr, en, compare in PAIRS:
        if not compare:
            continue
        fr_keys = _sans_exemptions(_t_keys(fr), fr)
        en_keys = _sans_exemptions(_t_keys(en), en)
        missing_en = fr_keys - en_keys
        missing_fr = en_keys - fr_keys
        assert not missing_en and not missing_fr, (
            f"t-object drift between {fr} and {en}: "
            f"missing in EN={sorted(missing_en)} · missing in FR={sorted(missing_fr)} — "
            "add the translation on the other side, never let one language lag"
        )


# Un garde non éprouvé est une piste d'audit qui ment : on rejoue la dérive qu'il interdit.
# La clé RENOMMÉE est le cas qui compte le plus — c'est le seul qui ne crie pas, parce que
# la page continue de se construire et rend `undefined` à l'endroit de la rubrique.
TABLE_FICHE = REPO_ROOT / "site" / "src" / "content" / "fiche.ts"


def _derive_le_bloc_en(texte: str, transformation) -> str:
    """Applique la dérive AU BLOC EN seulement.

    Une dérive appliquée au fichier entier frappe le bloc FR en premier (il est écrit avant)
    et laisse l'EN intact : on comparerait alors un FR amputé à lui-même, et la contre-épreuve
    passerait en annonçant qu'elle a mordu. Elle ne prouverait rien.
    """
    i = texte.index("const EN")
    return texte[:i] + transformation(texte[i:])


@pytest.mark.parametrize(
    "nom,derive",
    [
        ("clé de 1er niveau retirée", lambda t: re.sub(r"^  tagline: .*\n", "", t, count=1, flags=re.M)),
        ("clé imbriquée retirée", lambda t: re.sub(r"^    verifiedTip: .*\n", "", t, count=1, flags=re.M)),
        ("clé renommée d'un seul côté", lambda t: t.replace("  powerUnknown:", "  powerUnkown:", 1)),
    ],
)
def test_le_garde_de_parite_mord_vraiment(nom, derive, tmp_path, monkeypatch):
    texte = TABLE_FICHE.read_text(encoding="utf-8")
    mute = _derive_le_bloc_en(texte, derive)
    assert mute != texte, f"la dérive « {nom} » n'a rien changé : le test ne prouve rien"
    faux = tmp_path / "fiche.ts"
    faux.write_text(mute, encoding="utf-8")
    # On patche l'entrée de TABLES_PARTAGEES, pas un chemin d'import en dur : selon la façon
    # dont pytest collecte ce fichier, ce chemin change de nom et le patch échouerait — une
    # contre-épreuve qui ne s'exécute pas ne prouve rien non plus.
    monkeypatch.setitem(TABLES_PARTAGEES, "dc/[id].astro", (faux, "EN"))
    with pytest.raises(AssertionError):
        test_paired_t_objects_share_their_keys()


GABARIT_FICHE = REPO_ROOT / "site" / "src" / "components" / "DcFiche.astro"
_TEST_DE_LANGUE = re.compile(r'lang === "fr"')
# Quatre seaux, et un seul contient des mots. Pas d'heuristique sur le contenu de la chaîne :
# « carte » n'a pas de barre oblique et reste un chemin, tandis que « Carte » est un mot —
# seule une déclaration explicite les distingue sûrement, et elle se relit.
_DECLARE = re.compile(r"i18n:(route|format|donnee)")


def test_le_gabarit_de_la_fiche_ne_choisit_plus_de_mot_par_test_de_langue():
    """Dans la fiche, un `lang === "fr"` ne doit plus produire un MOT.

    « Note en attente » y était écrit TROIS fois — trois copies à faire vieillir ensemble, et
    une langue nouvelle aurait eu trois endroits à remplir pour une seule phrase. Les 33
    chaînes qui vivaient là ont rejoint `content/fiche.ts` le 2026-10-29.

    Ce qui reste légitime dans le gabarit, et doit se déclarer :
      · `i18n:route`  — un CHEMIN (`/fr/carte/` contre `/map/`) ;
      · `i18n:format` — un FORMAT (virgule décimale, ordre des composantes d'une date) ;
      · `i18n:donnee` — un champ BILINGUE DE LA DONNÉE (`activity_fr` / `activity_en`) : le
        texte vient du corpus, pas de nous, et il n'a rien à faire dans une table d'interface.
    Aucun des trois n'est un mot que nous écrivons, et une langue nouvelle n'a rien à en dire.
    """
    nues = []
    for n, ligne in enumerate(GABARIT_FICHE.read_text(encoding="utf-8").splitlines(), 1):
        if _TEST_DE_LANGUE.search(ligne) and not _DECLARE.search(ligne):
            nues.append(f"  {GABARIT_FICHE.name}:{n}  {ligne.strip()[:100]}")
    assert not nues, (
        f"{len(nues)} test(s) de langue non déclaré(s) dans le gabarit de la fiche.\n"
        + "\n".join(nues)
        + "\n\nUn MOT va dans `site/src/content/fiche.ts` (il se traduit, et une langue "
        "nouvelle doit l'y trouver). Une route, un format ou un champ de la donnée reste ici "
        "et se déclare `/* i18n:route */`, `/* i18n:format */` ou `/* i18n:donnee */`."
    )


def test_le_garde_du_gabarit_mord_vraiment(tmp_path, monkeypatch):
    """Contre-épreuve : une chaîne remise en dur dans le gabarit doit être vue.

    C'est la régression qui guette — on répare une phrase à l'endroit où elle s'affiche, en
    ternaire, parce que c'est là qu'on la lit. La langue suivante ne la trouverait jamais.
    """
    rechute = GABARIT_FICHE.read_text(encoding="utf-8").replace(
        "{t.notScoredFlag}",
        '{lang === "fr" ? "non noté · fait contextuel" : "not scored · contextual fact"}',
        1,
    )
    faux = tmp_path / "DcFiche.astro"
    faux.write_text(rechute, encoding="utf-8")
    monkeypatch.setitem(globals(), "GABARIT_FICHE", faux)
    with pytest.raises(AssertionError, match="non déclaré"):
        test_le_gabarit_de_la_fiche_ne_choisit_plus_de_mot_par_test_de_langue()


def test_la_lecture_de_table_refuse_une_extraction_tronquee():
    """La post-condition du scanner, éprouvée : un littéral sans `;` final doit crier.

    C'est le défaut qui a failli passer : une accolade comptée de travers (apostrophe dans
    un commentaire) arrêtait la lecture sur un sous-objet, et la table amputée paraissait
    complète. Ce qui n'est pas lu ne manque à personne — voilà pourquoi ça se teste.
    """
    # Une accolade fermante DE TROP ferme le littéral sur `a`, et `, b: 2 };` reste dehors :
    # c'est la forme que prend une accolade mal comptée. Le cas naïf (`b: { c: 2 }` suivi
    # d'une virgule) est équilibré et ne tronque rien — il ne testait rien.
    tronque = "const EN: typeof FR = { a: 1 } , b: 2 };\n"
    with pytest.raises(AssertionError, match="ne se termine pas sur un `;`"):
        bloc(tronque, "EN")
