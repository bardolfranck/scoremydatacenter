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
    # 🔴 Les 22 paires ci-dessous ont été AJOUTÉES le 2026-10-29. Jusque-là la liste en
    # déclarait 11 sur 33 : le garde censé empêcher l'EN de décrocher couvrait un tiers des
    # pages, et les 22 autres — dont les quatre rapports, les indices, les chiffres et la
    # page nuisances — n'étaient gardées par rien. Une liste de paires tenue à côté des
    # pages réelles finit par mentir ; voir le test de complétude en bas de ce fichier, qui
    # ferme désormais la classe.
    ("fr/acceptabilite-data-center.astro", "acceptability-of-data-centers.astro", True),
    ("fr/actu.astro", "news.astro", True),
    ("fr/glossaire.astro", "glossary.astro", True),
    ("fr/normes.astro", "standards.astro", True),
    ("fr/notation-data-center.astro", "data-center-rating.astro", True),
    ("fr/nuisances-data-center.astro", "data-center-nuisances.astro", True),
    ("fr/portrait-du-site.astro", "site-portrait.astro", True),
    ("fr/presse.astro", "press.astro", False),            # prose en dur dans le gabarit
    ("fr/sources.astro", "sources.astro", True),
    ("fr/dc/[id]/portrait.astro", "dc/[id]/portrait.astro", True),
    ("fr/indices.astro", "indices.astro", False),         # gabarit IndicesPage, pas d'objet t
    ("fr/comparer.astro", "compare.astro", False),        # gabarit ComparerPage, pas d'objet t
    ("fr/chiffres/index.astro", "figures/index.astro", False),        # gabarit StatsPage
    ("fr/chiffres/[perimetre].astro", "figures/[perimeter].astro", False),  # gabarit StatsPage
    ("fr/developpeurs.astro", "developers.astro", False),      # gabarit DevelopersPage
    ("fr/developpeurs/cle.astro", "developers/key.astro", False),   # gabarit KeyReveal
    ("fr/la-note-pas-a-pas.astro", "the-grade-step-by-step.astro", False),  # prose en dur
    ("fr/qui-sommes-nous.astro", "who-we-are.astro", False),   # prose en dur
    ("fr/rapports/banques.astro", "reports/banks.astro", False),     # gabarit ReportDownload
    ("fr/rapports/big-tech.astro", "reports/big-tech.astro", False),
    ("fr/rapports/france.astro", "reports/france.astro", False),
    ("fr/rapports/nederland.astro", "reports/nederland.astro", False),
]
# Pages sans jumelle, et pourquoi. Toute autre page doit figurer dans PAIRS — c'est le test
# de complétude qui l'exige, et c'est ce qui empêche la liste ci-dessus de rester en arrière.
SANS_JUMELLE: dict[str, str] = {
    "fr/apercu-partage.astro": "outil interne FR (galerie d'aperçus OG), rien à traduire",
    "404.astro": "la page 404 d'Astro est servie à la racine pour toutes les langues",
}

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
    # `nearbyMi` / `nearbyUnderMi` : la même phrase, l'unité du lieu. Elles ne sont
    # atteignables que si `lang === "en"` ET le pays compte ses distances en miles
    # (`PAYS_EN_MILES = {US}`, DcFiche.astro) — la table FR ne peut donc structurellement
    # pas en avoir besoin, et le code le dit déjà dans fiche.ts.
    # 🔴 Cette asymétrie était INVISIBLE jusqu'au 2026-10-29 : le relevé des clés se faisait
    # ligne par ligne, et `relation: { operator: …, nearbyMi: … }` tient sur une seule ligne,
    # donc seul le parent était compté. Le relevé caractère par caractère la montre.
    "dc/[id].astro": {"nearbyMi", "nearbyUnderMi"},
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


def _pages_du_disque() -> set[str]:
    """Toutes les pages `.astro`, chemin relatif à `pages/`, sauf les générateurs d'images.

    `og/**` ne rend pas une page lisible : ce sont des PNG dessinés. Leur texte bilingue est
    un vrai sujet, mais il ne se garde pas par parité de clés — il n'y a pas d'objet `t`.
    """
    return {
        str(p.relative_to(PAGES))
        for p in PAGES.rglob("*.astro")
        if not str(p.relative_to(PAGES)).startswith("og/")
    }


def test_toute_page_est_declaree_dans_la_liste_des_paires():
    """LA LISTE DES PAIRES NE DOIT PAS RESTER EN ARRIÈRE DES PAGES RÉELLES.

    Le 2026-10-29 : **33 paires de pages sur le disque, 11 déclarées**. Le garde censé
    empêcher l'anglais de décrocher ne regardait qu'un tiers du site — et les deux tiers
    muets contenaient les quatre rapports, les indices, les chiffres, et la page nuisances.
    Rien ne criait, parce que le garde ne parcourait que SA liste : une énumération tenue à
    côté de la réalité qu'elle prétend décrire, c'est-à-dire une liste qui finit par mentir.

    Désormais une page nouvelle doit se déclarer — en paire, ou dans SANS_JUMELLE avec sa
    raison. L'oubli casse la suite au lieu de laisser une page sans garde.
    """
    declarees = {fr for fr, _, _ in PAIRS} | {en for _, en, _ in PAIRS} | set(SANS_JUMELLE)
    orphelines = sorted(_pages_du_disque() - declarees)
    assert not orphelines, (
        f"{len(orphelines)} page(s) ne sont déclarées nulle part :\n"
        + "\n".join(f"  · {p}" for p in orphelines)
        + "\n\nAjoutez la paire dans PAIRS (avec `compare=False` si la page porte sa prose "
        "en dur dans un gabarit), ou la page dans SANS_JUMELLE avec sa raison. Une page non "
        "déclarée n'est gardée par rien, et son anglais peut décrocher sans que ça se voie."
    )


def test_une_liste_de_paires_perimee_ne_passe_pas(monkeypatch):
    """Contre-épreuve : une page retirée de la liste doit être signalée.

    C'est exactement la panne vécue — la page existait, la liste l'ignorait, le garde se
    taisait. Si ce test-ci ne mord pas, le précédent ne garantit rien.
    """
    ampute = [p for p in PAIRS if p[0] != "fr/actu.astro"]
    monkeypatch.setitem(globals(), "PAIRS", ampute)
    with pytest.raises(AssertionError, match="déclarées nulle part"):
        test_toute_page_est_declaree_dans_la_liste_des_paires()


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
