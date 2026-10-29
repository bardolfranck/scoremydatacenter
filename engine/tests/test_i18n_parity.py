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
from engine.tests.i18n_table import bloc, chemins, debut_de_commentaire

PAGES = REPO_ROOT / "site" / "src" / "pages"

CONTENU = REPO_ROOT / "site" / "src" / "content"
LANGUES_TS = CONTENU / "langues.ts"

# Les tables de chaînes PARTAGÉES : un module qui porte la copie une fois par langue, au lieu
# de deux littéraux `t` tenus à la main dans deux pages. La fiche a ouvert la voie le
# 2026-10-29 ; le chrome a suivi. Leur parité se vérifie entre blocs de langue, pas entre
# pages — c'est `test_les_tables_partagees_portent_les_memes_cles` qui s'en charge.
TABLES_MODULES: dict[str, str] = {
    "fiche.ts": "la copie de la fiche",
    "chrome.ts": "le chrome, présent sur toutes les pages",
}
# Asymétries VOULUES dans un module partagé, par dernier segment de chemin.
# `nearbyMi` / `nearbyUnderMi` : la même phrase, l'unité du lieu. Elles ne sont atteignables
# que si `lang === "en"` ET le pays compte ses distances en miles (`PAYS_EN_MILES = {US}`,
# DcFiche.astro) — la table FR ne peut donc structurellement pas en avoir besoin, et fiche.ts
# le dit déjà. 🔴 Invisible jusqu'au 2026-10-29 : le relevé se faisait ligne par ligne, et
# `relation: { operator: …, nearbyMi: … }` tient sur une seule ligne.
ASYMETRIES_MODULES: dict[str, set[str]] = {
    "fiche.ts": {"nearbyMi", "nearbyUnderMi"},
}

# (FR page, EN twin, compare t keys?) — routes differ by design (localised slugs).
PAIRS = [
    ("fr/index.astro", "index.astro", True),
    # La copie de la fiche a quitté les deux pages pour `content/fiche.ts` (2026-10-29) :
    # sa parité se vérifie entre blocs de langue, par le test des tables partagées.
    ("fr/dc/[id].astro", "dc/[id].astro", False),
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
}


def _langues_vivantes() -> list[str]:
    """Les langues DÉCLARÉES vivantes, lues à leur source unique (`content/langues.ts`).

    Pas une liste recopiée ici : une langue en cours d'écriture n'est pas encore vivante, et
    c'est `langues.ts` qui décide. Recopier la liste dans le test, c'est la même faute que de
    recopier une table — elle finirait par ne plus dire la même chose.
    """
    m = re.search(r"LANGUES_VIVANTES = \[([^\]]*)\]", LANGUES_TS.read_text(encoding="utf-8"))
    assert m, "LANGUES_VIVANTES introuvable — le garde ne sait plus quelles langues comparer"
    langues = re.findall(r'"(\w+)"', m.group(1))
    assert len(langues) >= 2, f"une seule langue vivante ({langues}) : rien à comparer"
    return langues


def _t_keys(page: str) -> set[str]:
    """The NESTED key paths of a page's copy — `a`, `a.b`, `a.b.c`.

    Top-level keys alone let a whole nested group drift unseen: the fiche's two literals
    differed by ten lines and nobody could tell whether that was wrapping or a missing
    group. Paths answer it.
    """
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


def test_les_tables_partagees_portent_les_memes_cles():
    """Chaque module de chaînes partagé doit porter les mêmes clés dans toutes les langues.

    Une table à deux endroits finit par mentir ; une table à UN endroit avec un bloc par
    langue ne mentira que si personne ne la compare. C'est ce test qui la compare, et c'est
    lui qui mord — pas le type TypeScript, puisque `astro build` tourne sans `astro check`
    (une clé absente rendrait `undefined` en silence dans la page).
    """
    langues = _langues_vivantes()
    for fichier, quoi in TABLES_MODULES.items():
        texte = (CONTENU / fichier).read_text(encoding="utf-8")
        exempt = ASYMETRIES_MODULES.get(fichier, set())
        tables = {
            lg: {k for k in chemins(bloc(texte, lg.upper())) if k.split(".")[-1] not in exempt}
            for lg in langues
        }
        reference, cles_ref = langues[0], tables[langues[0]]
        for lg in langues[1:]:
            manquantes = sorted(cles_ref - tables[lg])
            intruses = sorted(tables[lg] - cles_ref)
            assert not manquantes, (
                f"{fichier} ({quoi}) — {lg.upper()} n'a pas {len(manquantes)} clé(s) que "
                f"{reference.upper()} porte : {manquantes[:8]}. Servie telle quelle, la page "
                f"rendrait `undefined` : pas une erreur, un blanc."
            )
            assert not intruses, (
                f"{fichier} ({quoi}) — {lg.upper()} porte {len(intruses)} clé(s) inconnue(s) "
                f"de {reference.upper()} : {intruses[:8]}. Une clé renommée d'un seul côté est "
                f"le piège muet : la rubrique disparaît sans que rien ne casse."
            )


# Un garde non éprouvé est une piste d'audit qui ment : on rejoue la dérive qu'il interdit.
# La clé RENOMMÉE est le cas qui compte le plus — c'est le seul qui ne crie pas, parce que
# la page continue de se construire et rend `undefined` à l'endroit de la rubrique.
TABLE_FICHE = CONTENU / "fiche.ts"


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
    # On écrit la table dérivée dans un dossier jetable et on y fait pointer CONTENU : selon
    # la façon dont pytest collecte ce fichier, un chemin d'import en dur change de nom et le
    # patch échouerait — une contre-épreuve qui ne s'exécute pas ne prouve rien non plus.
    (tmp_path / "fiche.ts").write_text(mute, encoding="utf-8")
    (tmp_path / "chrome.ts").write_text(
        (CONTENU / "chrome.ts").read_text(encoding="utf-8"), encoding="utf-8"
    )
    monkeypatch.setitem(globals(), "CONTENU", tmp_path)
    with pytest.raises(AssertionError):
        test_les_tables_partagees_portent_les_memes_cles()


SRC_SITE = REPO_ROOT / "site" / "src"
GABARIT_FICHE = SRC_SITE / "components" / "DcFiche.astro"
_TEST_DE_LANGUE = re.compile(r'lang === "fr"')
# Quatre seaux, et un seul contient des mots. Pas d'heuristique sur le contenu de la chaîne :
# « carte » n'a pas de barre oblique et reste un chemin, tandis que « Carte » est un mot —
# seule une déclaration explicite les distingue sûrement, et elle se relit.
_DECLARE = re.compile(r"i18n:(route|format|donnee)")


def _branches_nues(chemin) -> list[str]:
    """Les tests de langue d'un fichier qui ne déclarent pas ce qu'ils sont.

    Une occurrence DANS un commentaire ne compte pas : ce fichier-ci et `fiche.ts` parlent du
    motif `lang === "fr" ? … : …` pour l'expliquer, et un garde qui compte sa propre
    documentation crie pour rien — on finit par baisser le chiffre au lieu de le lire.
    """
    nues = []
    for n, ligne in enumerate(chemin.read_text(encoding="utf-8").splitlines(), 1):
        m = _TEST_DE_LANGUE.search(ligne)
        if not m or _DECLARE.search(ligne):
            continue
        commentaire = debut_de_commentaire(ligne)
        if commentaire != -1 and commentaire < m.start():
            continue
        nues.append(f"  {chemin.relative_to(SRC_SITE)}:{n}  {ligne.strip()[:100]}")
    return nues


# 🔴 UNE DETTE, PAS DES EXEMPTIONS. Chaque ligne est un fichier qui choisit encore ses mots
# par un test de langue, avec le nombre exact de branches nues qu'il lui reste. Le chiffre
# doit être EXACT : quand on en retire, on le baisse, et il ne peut jamais remonter. Un
# fichier NOUVEAU n'est pas dans la liste, donc il doit naître à zéro.
#
# C'est ce qui remplace « on fera le reste plus tard » par une quantité qu'on voit diminuer.
# État au 2026-10-29, après la fiche ET le chrome : 104 branches nues dans 27 fichiers.
DETTE_I18N: dict[str, int] = {
    "components/AboutSection.astro": 1,
    "components/ActuFeed.astro": 6,
    "components/ActuStrip.astro": 2,
    "components/Comparateur.astro": 12,
    "components/CountryRing.astro": 2,
    "components/DevelopersPage.astro": 1,
    "components/DossierEnvironnemental.astro": 5,
    "components/FeedbackBand.astro": 1,
    "components/IndicesMap.astro": 1,
    "components/IndicesPage.astro": 5,
    "components/KeyReveal.astro": 1,
    "components/Landing.astro": 14,
    "components/LibraryIndex.astro": 2,
    "components/LibraryRevue.astro": 7,
    "components/Normes.astro": 1,
    "components/PressPage.astro": 1,
    "components/ProjectsStrip.astro": 2,
    "components/Ranking.astro": 3,
    "components/ReportDownload.astro": 6,
    "components/SatelliteWall.astro": 1,
    "components/SitePortrait.astro": 5,
    "components/StatsPage.astro": 11,
    "config/indicatorValues.ts": 2,
    "config/reportStatus.ts": 1,
    "config/stats.ts": 6,
    "pages/og/indices/[key].png.ts": 4,
    "pages/og/stats/[key].png.ts": 1,
}


def _sources_site() -> list:
    return sorted(
        [p for p in SRC_SITE.rglob("*.astro")] + [p for p in SRC_SITE.rglob("*.ts")]
    )


def test_la_dette_i18n_ne_remonte_jamais():
    """Le cliquet : un fichier déjà fait reste à zéro, et la dette ne peut que baisser.

    Sans ce test, « les autres fichiers suivront » est une intention. Avec lui, c'est un
    nombre : chaque mot sorti d'un gabarit fait baisser un chiffre qui ne remonte pas, et un
    fichier nouveau ne peut pas naître avec de la prose en dur.
    """
    trop, a_baisser, nouveaux = [], [], []
    for p in _sources_site():
        rel = str(p.relative_to(SRC_SITE))
        nues = _branches_nues(p)
        attendu = DETTE_I18N.get(rel)
        if attendu is None:
            if nues:
                nouveaux.append((rel, nues))
        elif len(nues) > attendu:
            trop.append((rel, attendu, len(nues), nues[attendu:]))
        elif len(nues) < attendu:
            a_baisser.append((rel, attendu, len(nues)))

    messages = []
    for rel, nues in nouveaux:
        messages.append(
            f"{rel} n'est pas dans la dette et porte {len(nues)} test(s) de langue nus :\n"
            + "\n".join(nues)
        )
    for rel, attendu, trouve, surplus in trop:
        messages.append(
            f"{rel} : la dette dit {attendu}, j'en trouve {trouve}. La dette ne remonte pas.\n"
            + "\n".join(surplus)
        )
    for rel, attendu, trouve in a_baisser:
        messages.append(
            f"{rel} : la dette dit {attendu}, il n'en reste que {trouve} — baissez le chiffre "
            f"dans DETTE_I18N (ou retirez la ligne si c'est 0). Un cliquet qui garde un vieux "
            f"chiffre autorise la prose à revenir jusque-là."
        )
    assert not messages, "\n\n".join(messages) + (
        "\n\nUn MOT va dans une table de chaînes (il se traduit). Une route, un format ou un "
        "champ bilingue de la donnée reste sur place et se déclare `/* i18n:route */`, "
        "`/* i18n:format */` ou `/* i18n:donnee */`."
    )


def test_le_cliquet_de_dette_mord_dans_les_deux_sens(tmp_path, monkeypatch):
    """Contre-épreuve : le cliquet doit voir une dette qui remonte ET une dette périmée."""
    monkeypatch.setitem(DETTE_I18N, "components/Landing.astro", 13)  # on en déclare un de moins
    with pytest.raises(AssertionError, match="ne remonte pas"):
        test_la_dette_i18n_ne_remonte_jamais()
    monkeypatch.setitem(DETTE_I18N, "components/Landing.astro", 99)  # on en déclare trop
    with pytest.raises(AssertionError, match="baissez le chiffre"):
        test_la_dette_i18n_ne_remonte_jamais()


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
