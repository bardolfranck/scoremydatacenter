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
    "portrait.ts": "la copie du portrait de site",
    "commun.ts": "les phrases servies par plusieurs surfaces",
    # La surface EXPLICATIVE, sortie des pages le 2026-10-29 (périmètre signé par Franck :
    # fiche + portrait + le menu « Comprendre », rien d'autre). Chaque module portait sa
    # copie en littéral DANS CHACUNE des deux pages ; ici il n'y a qu'un endroit.
    "acceptabilite.ts": "la page de concept « L'acceptabilité »",
    "notation.ts": "la page de concept « La notation »",
    "nuisances.ts": "la page de concept « Les nuisances »",
    "comprendre.ts": "la page « Comprendre les data centers »",
    "normes.ts": "la page « Les normes · où on se situe »",
    "methodologie.ts": "la page « Méthode »",
    "sources.ts": "la page « Sources & licences »",
    "glossaire.ts": "le glossaire",
    "portrait-explainer.ts": "la page qui EXPLIQUE le portrait (le portrait est dans portrait.ts)",
    "dossier.ts": "le bloc « dossier environnemental » de la fiche",
    # L'ACCUEIL, entré dans le périmètre le 2026-10-29 : « bien entendu la Home Page en NL
    # aussi, c'est évident — un hollandais arrive sur la home et veut la voir traduite »
    # (Franck). Il porte aussi les mots des quatre bandeaux, qui ne recevaient que `lang`.
    "accueil.ts": "la copie de la page d'accueil, bandeaux compris",
    "feedback.ts": "le bandeau « votre avis » (accueil + revue de la bibliothèque)",
}
# Asymétries VOULUES dans un module partagé, par dernier segment de chemin.
# `nearbyMi` / `nearbyUnderMi` : la même phrase, l'unité du lieu. Elles ne sont atteignables
# que si `lang === "en"` ET le pays compte ses distances en miles (`PAYS_EN_MILES = {US}`,
# DcFiche.astro) — la table FR ne peut donc structurellement pas en avoir besoin, et fiche.ts
# le dit déjà. 🔴 Invisible jusqu'au 2026-10-29 : le relevé se faisait ligne par ligne, et
# `relation: { operator: …, nearbyMi: … }` tient sur une seule ligne.
# `contextNotice` / `inFranceLabel` / `tag` : l'anglais signale ce qui est spécifique à la
# France à un lecteur qui n'y est pas ; le français n'a structurellement pas ce besoin. Le
# gabarit teste ces clés (`t.x && …`), donc leur absence côté FR ne rend rien. Déclarées ici
# depuis que la copie a quitté les pages (elles vivaient dans `EXTRA_OK`, par page).
ASYMETRIES_MODULES: dict[str, set[str]] = {
    "fiche.ts": {"nearbyMi", "nearbyUnderMi"},
    "comprendre.ts": {"contextNotice", "inFranceLabel", "tag"},
}

# (FR page, EN twin, compare t keys?) — routes differ by design (localised slugs).
PAIRS = [
    ("fr/index.astro", "index.astro", False),
    # La copie de la fiche a quitté les deux pages pour `content/fiche.ts` (2026-10-29) :
    # sa parité se vérifie entre blocs de langue, par le test des tables partagées.
    ("fr/dc/[id].astro", "dc/[id].astro", False),
    ("fr/classement.astro", "ranking.astro", True),
    ("fr/carte.astro", "map.astro", False),          # inline labels, no t object
    ("fr/methodologie.astro", "methodology.astro", False),
    ("fr/mentions-legales.astro", "legal.astro", False),  # t.sections carry prose, headings differ per language
    ("fr/contact.astro", "contact.astro", False),
    ("fr/comprendre.astro", "understand.astro", False),
    ("fr/comprendre/one-pager.astro", "understand/one-pager.astro", False),
    ("fr/bibliotheque.astro", "intelligence.astro", True),
    ("fr/bibliotheque/tous.astro", "intelligence/all.astro", True),
    # 🔴 Les 22 paires ci-dessous ont été AJOUTÉES le 2026-10-29. Jusque-là la liste en
    # déclarait 11 sur 33 : le garde censé empêcher l'EN de décrocher couvrait un tiers des
    # pages, et les 22 autres — dont les quatre rapports, les indices, les chiffres et la
    # page nuisances — n'étaient gardées par rien. Une liste de paires tenue à côté des
    # pages réelles finit par mentir ; voir le test de complétude en bas de ce fichier, qui
    # ferme désormais la classe.
    ("fr/acceptabilite-data-center.astro", "acceptability-of-data-centers.astro", False),
    ("fr/actu.astro", "news.astro", True),
    ("fr/glossaire.astro", "glossary.astro", False),
    ("fr/normes.astro", "standards.astro", False),
    ("fr/notation-data-center.astro", "data-center-rating.astro", False),
    ("fr/nuisances-data-center.astro", "data-center-nuisances.astro", False),
    ("fr/portrait-du-site.astro", "site-portrait.astro", False),
    ("fr/presse.astro", "press.astro", False),            # prose en dur dans le gabarit
    ("fr/sources.astro", "sources.astro", False),
    # Copie sortie des deux pages vers `content/portrait.ts` (2026-10-29) : sa parité se
    # vérifie entre blocs de langue, par le test des tables partagées.
    ("fr/dc/[id]/portrait.astro", "dc/[id]/portrait.astro", False),
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
# Les pages dont la COPIE A QUITTÉ la page pour un module partagé. Leur paire est à
# `compare=False`, mais pas pour la même raison que « prose en dur dans le gabarit » : leur
# parité est gardée AILLEURS, entre blocs de langue. Sans cette table, les deux raisons se
# confondraient dans un même `False`, et une table réinstallée en littéral dans une page
# repasserait inaperçue — c'est `test_une_page_migree_ne_reprend_pas_sa_copie` qui l'interdit.
COPIE_EN_MODULE: dict[str, str] = {
    "fr/index.astro": "accueil.ts",
    "fr/acceptabilite-data-center.astro": "acceptabilite.ts",
    "fr/glossaire.astro": "glossaire.ts",
    "fr/normes.astro": "normes.ts",
    "fr/notation-data-center.astro": "notation.ts",
    "fr/nuisances-data-center.astro": "nuisances.ts",
    "fr/portrait-du-site.astro": "portrait-explainer.ts",
    "fr/sources.astro": "sources.ts",
    "fr/comprendre.astro": "comprendre.ts",
    "fr/methodologie.astro": "methodologie.ts",
    "fr/dc/[id].astro": "fiche.ts",
    "fr/dc/[id]/portrait.astro": "portrait.ts",
}

# Pages sans jumelle, et pourquoi. Toute autre page doit figurer dans PAIRS — c'est le test
# de complétude qui l'exige, et c'est ce qui empêche la liste ci-dessus de rester en arrière.
SANS_JUMELLE: dict[str, str] = {
    "fr/apercu-partage.astro": "outil interne FR (galerie d'aperçus OG), rien à traduire",
    "404.astro": "la page 404 d'Astro est servie à la racine pour toutes les langues",
    # Le harnais de relecture du néerlandais : ces deux pages n'ont pas de jumelle parce
    # qu'elles ne sont pas servies — leur portillon rend `[]` sans SMDC_PREVIZ=1, et
    # `test_la_previz_ne_sort_rien_en_production` est ce qui le garde.
    "previz/[gabarit].astro": "préviz d'une langue en préparation, jamais construite en prod",
    "previz/duo/[gabarit].astro": "côte-à-côte FR↔NL de relecture, jamais construit en prod",
}

# Deliberate asymmetries: keys one language needs and the other, by design, does not.
# understand (EN) flags the France-centric content ("In France" tags + context notice);
# the FR page needs no such flag. Anything NOT listed here must exist on both sides.
# `blocks.*.tag` carries that same "France" flag inside the nested blocks: it only became
# visible when this test started reading NESTED paths (2026-10-29) — the top-level-only
# comparison had never seen it. Same asymmetry, same reason, just one level down.
# 🔴 VIDE, et c'est voulu : la seule asymétrie de page connue (understand.astro) a suivi sa
# copie dans `content/comprendre.ts` et se déclare maintenant dans `ASYMETRIES_MODULES`. Une
# exemption laissée là après le départ de ce qu'elle exemptait ne garde plus rien et peut
# dispenser une dérive future du même nom.
EXTRA_OK: dict[str, set[str]] = {}
# Nested paths exempted for the same reason, matched on their LAST segment: the France flag
# repeats under every block, and listing each full path would be a list that rots.
EXTRA_OK_IMBRIQUE: dict[str, set[str]] = {}


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


def _langues_declarees() -> list[str]:
    """Toutes les langues qui ont une table, SERVIES OU NON — lues à leur source unique.

    Une langue en préparation (`nl` depuis le 2026-11-02) a ses clés gardées comme une
    langue vivante : c'est ce qui l'empêche de dériver pendant les semaines où elle s'écrit.
    Ce qu'elle n'a pas, c'est une page qui la sert.
    """
    texte = LANGUES_TS.read_text(encoding="utf-8")
    vivantes = _langues_vivantes()
    m = re.search(r"LANGUES_EN_PREPARATION = \[([^\]]*)\]", texte)
    preparation = re.findall(r'"(\w+)"', m.group(1)) if m else []
    return vivantes + [lg for lg in preparation if lg not in vivantes]


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
    # 🔴 Les langues DÉCLARÉES, pas seulement les vivantes : une langue en préparation qui
    # dérive pendant sa rédaction arrive incomplète le jour où on l'ouvre, et c'est le pire
    # moment pour s'en apercevoir.
    langues = _langues_declarees()
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


def test_une_page_migree_ne_reprend_pas_sa_copie():
    """Une page dont la copie est partie en module ne doit pas se remettre à la porter.

    🔴 C'est ce qui donne un SENS à son `compare=False`. Deux raisons très différentes
    partagent ce même `False` : « cette page n'a pas d'objet `t` » et « sa parité est gardée
    ailleurs ». Sans ce test, quelqu'un qui réinstalle un littéral `const t = {…}` dans l'une
    des pages migrées sortirait sa copie de TOUTE surveillance — le garde de paires l'ignore
    (False), le garde de modules ne regarde pas les pages — et l'anglais pourrait décrocher
    exactement comme il l'a fait deux fois avant que ce fichier existe.
    """
    for page, module in COPIE_EN_MODULE.items():
        for chemin in (page, dict(((f, e) for f, e, _ in PAIRS))[page]):
            texte = (PAGES / chemin).read_text(encoding="utf-8")
            assert "const t = {" not in texte, (
                f"{chemin} porte de nouveau un littéral `const t = {{…}}` alors que sa copie "
                f"vit dans `content/{module}`. Sa paire est à `compare=False` : ce littéral "
                f"n'est gardé par RIEN. Remettre la copie dans le module, ou repasser la "
                f"paire à `True`."
            )
            assert f'content/{module.removesuffix(".ts")}"' in texte, (
                f"{chemin} n'importe plus `content/{module}` — soit la copie est repartie "
                f"ailleurs sans que cette table le dise, soit la page ne sert plus la table "
                f"gardée. Dans les deux cas `COPIE_EN_MODULE` ne décrit plus la réalité."
            )


def test_le_garde_des_pages_migrees_mord_vraiment(tmp_path, monkeypatch):
    """On rejoue la régression : un littéral remis dans une page migrée."""
    page = "fr/comprendre.astro"
    faux = tmp_path / page
    faux.parent.mkdir(parents=True, exist_ok=True)
    texte = (PAGES / page).read_text(encoding="utf-8")
    faux.write_text(texte.replace("const t = COMPRENDRE.fr;", "const t = {\n  h1: \"…\",\n};"), encoding="utf-8")
    # l'autre page de la paire reste celle du dépôt : on ne teste qu'un côté à la fois
    for autre in (PAGES / "understand.astro",):
        (tmp_path / autre.name).write_text(autre.read_text(encoding="utf-8"), encoding="utf-8")
    # 🔴 `setitem(globals(), …)` et NON `setattr("engine.tests.test_i18n_parity.PAGES", …)` :
    # la cible par chemin pointé a importé un AUTRE objet module que celui où tourne le test,
    # la rustine s'est posée sur le jumeau, le faux a été lu depuis le dépôt réel — et la
    # contre-épreuve est passée sans mordre. C'est la contre-épreuve qui l'a dit ; une
    # rustine qui ne prend pas ne se voit nulle part ailleurs.
    monkeypatch.setitem(globals(), "PAGES", tmp_path)
    monkeypatch.setitem(globals(), "COPIE_EN_MODULE", {page: "comprendre.ts"})
    with pytest.raises(AssertionError, match="littéral"):
        test_une_page_migree_ne_reprend_pas_sa_copie()


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
#
# 🔴 LE TOTAL CI-DESSOUS EST VÉRIFIÉ PAR UN TEST, et il l'est depuis qu'il a eu tort. Un
# en-tête qui annonce un chiffre que rien ne recompte est une piste d'audit qui ment : il
# reste juste tant que personne ne touche à la table, et c'est précisément quand on y touche
# qu'on le lit. La ligne « État au … » doit donc être tenue comme du code.
# État au 2026-10-29, après la fiche, le chrome, le portrait, « Comprendre » et l'ACCUEIL : 62 branches nues dans 15 fichiers.
DETTE_I18N: dict[str, int] = {
    "components/ActuFeed.astro": 6,
    "components/Comparateur.astro": 12,
    "components/DevelopersPage.astro": 1,
    "components/IndicesMap.astro": 1,
    "components/IndicesPage.astro": 5,
    "components/KeyReveal.astro": 1,
    "components/LibraryIndex.astro": 2,
    "components/LibraryRevue.astro": 7,
    "components/PressPage.astro": 1,
    "components/Ranking.astro": 3,
    "components/ReportDownload.astro": 6,
    "components/StatsPage.astro": 11,
    "config/reportStatus.ts": 1,
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


NAV_TS = REPO_ROOT / "site" / "src" / "config" / "nav.ts"


def _menu(langue: str) -> list[tuple]:
    """La FORME du menu d'une langue : la suite de ses nœuds, sans les mots.

    Un groupe sort en `("groupe", n)`, un lien en `("lien", "page"|"ancre")`. Ni les
    libellés ni les slugs ne sont comparés — ce sont justement les deux choses qui DOIVENT
    différer d'une langue à l'autre. Ce qui ne doit pas différer, c'est la liste des gestes
    offerts au visiteur et leur NATURE : un lien de page d'un côté et une ancre de la page
    d'accueil de l'autre, c'est l'anglais qui décroche — l'en-tête de `nav.ts` le promet
    (« Same action → same destination as FR ») et rien ne le vérifiait.
    """
    texte = NAV_TS.read_text(encoding="utf-8")
    debut = texte.index(f"export const {langue}_NAV")
    fin = texte.index("\n];", debut)
    # 🔴 Les commentaires d'abord : ce fichier porte un paragraphe entier de `href` mis en
    # commentaire (le comparateur retiré puis remis au menu). Les compter serait compter des
    # entrées qui ne s'affichent pas.
    lignes = []
    for ligne in texte[debut:fin].splitlines():
        c = debut_de_commentaire(ligne)
        lignes.append(ligne if c == -1 else ligne[:c])
    region = "\n".join(lignes)

    noeuds: list[tuple] = []
    profondeur = 0
    enfants = 0
    for jeton in re.finditer(r'children:\s*\[|href:\s*"([^"]*)"|\]', region):
        t = jeton.group(0)
        if t.startswith("children"):
            profondeur = 1
            enfants = 0
        elif t == "]":
            if profondeur == 1:
                noeuds.append(("groupe", enfants))
                profondeur = 0
        else:
            href = jeton.group(1)
            nature = "ancre" if "#" in href else "page"
            if profondeur == 1:
                enfants += 1
                noeuds.append(("enfant", nature))
            else:
                noeuds.append(("lien", nature))
    return noeuds


def test_le_menu_offre_les_memes_gestes_dans_les_deux_langues():
    """Le menu de chaque langue doit proposer les mêmes entrées, de la même nature.

    C'est le seul élément de ce dépôt qui s'affiche sur les 16 783 pages, et il vivait en
    deux listes tenues à la main sans que rien ne les compare. L'en-tête de `nav.ts` promet
    « Map and Ranking are real EN pages, not homepage anchors or FR fallbacks » : une
    promesse écrite en commentaire, que ce test transforme en garantie.
    """
    langues = [lg.upper() for lg in _langues_vivantes()]
    reference = _menu(langues[0])
    assert reference, "le menu de la langue de référence est vide — le relevé ne lit plus nav.ts"
    for lg in langues[1:]:
        autre = _menu(lg)
        assert len(autre) == len(reference), (
            f"{lg}_NAV a {len(autre)} nœuds contre {len(reference)} pour {langues[0]}_NAV : "
            f"une langue offre un geste que l'autre n'offre pas"
        )
        for i, (a, b) in enumerate(zip(reference, autre)):
            assert a == b, (
                f"{lg}_NAV diffère de {langues[0]}_NAV au nœud {i} : {b} contre {a}. Un lien "
                f"de page d'un côté et une ancre de l'accueil de l'autre, c'est exactement la "
                f"façon dont l'anglais a décroché deux fois."
            )


def test_le_garde_du_menu_mord_vraiment(tmp_path, monkeypatch):
    """Contre-épreuve : une entrée EN repliée sur une ancre de l'accueil."""
    faux = tmp_path / "nav.ts"
    texte = NAV_TS.read_text(encoding="utf-8")
    faux.write_text(texte.replace('{ href: "/ranking/", label: "Ranking" }',
                                  '{ href: "/#ranking", label: "Ranking" }', 1), encoding="utf-8")
    monkeypatch.setitem(globals(), "NAV_TS", faux)
    with pytest.raises(AssertionError, match="décroché"):
        test_le_menu_offre_les_memes_gestes_dans_les_deux_langues()


# 🔴 LA SURFACE QUI SE TRADUIT, déclarée par ses POINTS D'ENTRÉE (périmètre signé par
# Franck le 2026-10-29) : la fiche, le portrait, et le menu « Comprendre ». Pas la
# bibliothèque, pas les rapports, pas le mur Actu, pas qui-sommes-nous.
#
# Le reste du site garde sa dette, et c'est assumé : y câbler une table ne servirait AUCUNE
# langue nouvelle. Mais sur cette surface-ci l'exigence est absolue — zéro branche nue, sur
# la FERMETURE TRANSITIVE des imports, pas seulement sur les fichiers nommés. C'est ce que
# le cliquet seul ne garantit pas : un composant endetté qu'on importerait DEPUIS la fiche
# ferait entrer sa dette dans la surface traduite sans faire remonter aucun total.
SURFACE_TRADUITE = (
    "components/DcFiche.astro",
    "components/SitePortrait.astro",
    "layouts/Base.astro",
    "pages/fr/acceptabilite-data-center.astro",
    "pages/fr/notation-data-center.astro",
    "pages/fr/nuisances-data-center.astro",
    "pages/fr/comprendre.astro",
    "pages/fr/normes.astro",
    "pages/fr/methodologie.astro",
    "pages/fr/sources.astro",
    "pages/fr/glossaire.astro",
    "pages/fr/la-note-pas-a-pas.astro",
    "pages/fr/portrait-du-site.astro",
    # L'accueil est entré dans le périmètre le 2026-10-29. Il amène ses quatre bandeaux, qui
    # ne recevaient que `lang` et portaient donc chacun sa petite table en ternaire.
    "pages/fr/index.astro",
    "pages/index.astro",
)


# Le volume minimal qu'un relevé honnête doit ramener. Une constante, et non un nombre écrit
# dans le test : la contre-épreuve l'abaisse pour éprouver l'AUTRE garantie — sans quoi elle
# ne prouverait que le garde-fou de volume, en croyant prouver le compte de branches.
_SEUIL_FERMETURE = 40


def _fermeture(entrees) -> set[str]:
    """Tous les fichiers atteignables par import depuis ces points d'entrée."""
    vus: set[str] = set()
    pile = list(entrees)
    while pile:
        rel = pile.pop()
        if rel in vus:
            continue
        for candidat in (rel, rel + ".ts", rel + ".astro"):
            chemin = SRC_SITE / candidat
            if chemin.is_file():
                break
        else:
            continue
        if candidat in vus:
            continue
        vus.add(candidat)
        for imp in re.findall(r'from "(\.[^"]+)"', chemin.read_text(encoding="utf-8")):
            try:
                pile.append(str((chemin.parent / imp).resolve().relative_to(SRC_SITE.resolve())))
            except ValueError:
                pass
    return vus


def test_la_surface_traduite_est_a_zero_branche_nue():
    """Sur la surface qui se traduit, aucun fichier ne choisit plus ses mots par test de langue.

    Le cliquet dit que le reste du site ne s'aggrave pas ; ce test-ci dit que la surface où
    le néerlandais va passer est PRÊTE. Les deux sont nécessaires : un fichier peut être en
    règle avec le cliquet (son compte n'a pas monté) et faire quand même entrer dix branches
    dans la fiche le jour où on l'y importe.
    """
    fichiers = sorted(_fermeture(SURFACE_TRADUITE))
    assert len(fichiers) > _SEUIL_FERMETURE, (
        f"la fermeture ne ramène que {len(fichiers)} fichiers — le relevé ne suit plus les "
        f"imports, et un test qui ne voit plus rien ne garde rien"
    )
    fautifs = {}
    for rel in fichiers:
        nues = _branches_nues(SRC_SITE / rel)
        if nues:
            fautifs[rel] = nues
    assert not fautifs, (
        "la surface traduite a repris des branches nues :\n"
        + "\n".join(l for nues in fautifs.values() for l in nues)
        + "\n\nUne chaîne choisie par `lang === \"fr\"` est une chaîne qu'une langue "
        "nouvelle ne trouvera pas. Ou bien elle rejoint la table de sa surface, ou bien "
        "elle déclare ce qu'elle est (`i18n:route`, `i18n:format`, `i18n:donnee`)."
    )


def test_le_garde_de_la_surface_traduite_mord_vraiment(tmp_path, monkeypatch):
    """Contre-épreuve : une phrase remise en ternaire dans le gabarit de la fiche."""
    faux_src = tmp_path / "src"
    for rel in ("components", "content", "layouts", "pages/fr", "config"):
        (faux_src / rel).mkdir(parents=True, exist_ok=True)
    gabarit = faux_src / "components" / "DcFiche.astro"
    gabarit.write_text(
        '---\nconst x = lang === "fr" ? "voisinage" : "neighbourhood";\n---\n', encoding="utf-8"
    )
    monkeypatch.setitem(globals(), "SRC_SITE", faux_src)
    monkeypatch.setitem(globals(), "SURFACE_TRADUITE", ("components/DcFiche.astro",))
    # le seuil de volume protège d'un relevé muet : on l'abaisse pour éprouver l'autre garde
    monkeypatch.setitem(globals(), "_SEUIL_FERMETURE", 0)
    with pytest.raises(AssertionError, match="repris des branches nues"):
        test_la_surface_traduite_est_a_zero_branche_nue()


STATUTS_TS = CONTENU / "statuts.ts"
# Le volume minimal qu'un relevé honnête ramène — en constante, pour que la contre-épreuve
# puisse l'abaisser et éprouver l'AUTRE garantie (leçon du 2026-10-29).
_SEUIL_TABLES_STATUT = 14


def _statuts_declares() -> list[str]:
    """Le vocabulaire des statuts, lu à sa source unique (`content/statuts.ts`)."""
    texte = STATUTS_TS.read_text(encoding="utf-8")
    pipeline = re.search(r"PIPELINE = \[([^\]]*)\]", texte)
    assert pipeline, "PIPELINE introuvable dans statuts.ts"
    valeurs = re.findall(r'"(\w+)"', pipeline.group(1))
    suite = re.search(r"STATUTS = \[\.\.\.PIPELINE,([^\]]*)\]", texte)
    assert suite, "STATUTS introuvable dans statuts.ts"
    return valeurs + re.findall(r'"(\w+)"', suite.group(1))


def _tables_de_statut() -> list[tuple[str, int, set[str]]]:
    """Toutes les tables qui LIBELLENT un statut, CHERCHÉES dans le code.

    🔴 Pas une liste tenue à la main : il y en avait seize, dans seize fichiers, et c'est
    précisément parce que personne ne les avait comptées qu'une valeur pouvait manquer dans
    l'une d'elles sans que rien ne casse — la page affiche alors la valeur BRUTE, en anglais,
    au milieu d'une page française.

    Reconnaître une table de statuts sans la nommer : ses clés doivent être INCLUSES dans le
    vocabulaire déclaré, et elle doit libeller `operational`. Ce qui écarte, sans liste
    d'exceptions : la table des couleurs du comparateur (son vocabulaire est autre —
    `abandoned`, `decommissioned`, `litigation`…), la table des statuts d'INDICATEUR
    (`measured`/`estimated`), et la puce satellite, qui ne parle QUE des projets et n'a donc
    pas à libeller `operational`.
    """
    vocabulaire = set(_statuts_declares())
    trouvees = []
    for chemin in sorted(SRC_SITE.rglob("*")):
        if chemin.suffix not in (".ts", ".astro") or not chemin.is_file():
            continue
        texte = chemin.read_text(encoding="utf-8")
        for m in re.finditer(r'announced:\s*[`"\']', texte):
            ouverture = texte.rfind("{", 0, m.start())
            if ouverture < 0:
                continue
            profondeur, j = 0, ouverture
            while j < len(texte):
                if texte[j] == "{":
                    profondeur += 1
                elif texte[j] == "}":
                    profondeur -= 1
                    if profondeur == 0:
                        break
                j += 1
            bloc = texte[ouverture : j + 1]
            cles = set(re.findall(r'(\w+):\s*[`"\']', bloc))
            if not cles <= vocabulaire or "operational" not in cles:
                continue
            ligne = texte[:ouverture].count("\n") + 1
            trouvees.append((str(chemin.relative_to(SRC_SITE)), ligne, cles))
    return trouvees


def test_chaque_table_de_statut_libelle_chaque_statut():
    """Aucune table ne doit oublier un statut — une valeur sans libellé s'affiche BRUTE.

    C'est le piège de `?? dc.project_status` : il n'y a pas d'erreur, il y a « unknown » en
    anglais dans l'en-tête d'une fiche française. [[absence-ressemble-a-zero]] appliqué au
    vocabulaire.
    """
    vocabulaire = _statuts_declares()
    tables = _tables_de_statut()
    assert len(tables) >= _SEUIL_TABLES_STATUT, (
        f"seulement {len(tables)} table(s) de statut trouvée(s) — le relevé ne cherche plus, "
        f"et un relevé qui ne trouve rien ne garde rien"
    )
    fautives = [
        (f, n, sorted(set(vocabulaire) - cles)) for f, n, cles in tables
        if set(vocabulaire) - cles
    ]
    assert not fautives, "des tables de statut n'en libellent pas tous :\n" + "\n".join(
        f"  {f}:{n} — manque {manquants}" for f, n, manquants in fautives
    )


def test_le_garde_des_tables_de_statut_mord_vraiment(tmp_path, monkeypatch):
    """Contre-épreuve : un statut retiré d'UNE des seize tables."""
    faux = tmp_path / "content"
    faux.mkdir(parents=True)
    (faux / "statuts.ts").write_text(
        STATUTS_TS.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (faux / "fiche.ts").write_text(
        'const FR = { status: { announced: "A", permitting: "P", '
        'under_construction: "C", operational: "O" } };\n', encoding="utf-8"
    )
    monkeypatch.setitem(globals(), "SRC_SITE", tmp_path)
    monkeypatch.setitem(globals(), "STATUTS_TS", faux / "statuts.ts")
    monkeypatch.setitem(globals(), "_SEUIL_TABLES_STATUT", 0)
    with pytest.raises(AssertionError, match="manque"):
        test_chaque_table_de_statut_libelle_chaque_statut()


def test_le_vocabulaire_des_statuts_est_le_meme_dans_la_donnee_et_a_l_affichage():
    """Le schéma des fiches et la table d'affichage doivent dire le MÊME vocabulaire.

    🔴 Le vocabulaire a DEUX sources, et c'est le schéma qui l'a rappelé : `unknown` a été
    déclaré côté affichage (`content/statuts.ts`) et posé sur 8 fiches, et le gate de corpus
    a refusé les 8 — « 'unknown' is not one of [...] ». Le refus était le bon ; ce qui
    manquait, c'est le lien. Sans ce test, l'inverse serait silencieux : une valeur admise par
    le schéma, posée sur des fiches, et sans libellé nulle part → la valeur brute s'affiche.

    Le schéma de la WATCHLIST reste volontairement plus étroit (pas de `unknown`) : une
    entrée en veille est un projet qu'une source publique décrit, donc son stade est déclaré.
    L'asymétrie est écrite ici pour être relue, pas découverte.
    """
    import json

    schema = json.loads(
        (REPO_ROOT / "data" / "schema" / "datacenter.schema.json").read_text(encoding="utf-8")
    )
    noeud = schema["properties"]["identity"]["properties"]["project_status"]
    assert sorted(noeud["enum"]) == sorted(_statuts_declares()), (
        f"le schéma admet {sorted(noeud['enum'])} et l'affichage déclare "
        f"{sorted(_statuts_declares())} — une valeur admise sans libellé s'affiche BRUTE, "
        f"une valeur libellée sans être admise fait refuser la fiche au gate de corpus"
    )

    veille = json.loads(
        (REPO_ROOT / "data" / "schema" / "watchlist.schema.json").read_text(encoding="utf-8")
    )
    enum_veille = set(_enum_statut_watchlist(veille))
    assert enum_veille < set(_statuts_declares()), (
        "la watchlist doit rester un SOUS-ENSEMBLE strict du vocabulaire des fiches ; si elle "
        "s'élargit, la raison de l'asymétrie a changé et ce test doit être réécrit"
    )
    assert "unknown" not in enum_veille, (
        "`unknown` dans la watchlist : si une entrée en veille peut avoir un stade non "
        "établi, la raison écrite dans ce test ne tient plus"
    )


def _enum_statut_watchlist(schema: dict) -> list[str]:
    """L'enum de statut du schéma de veille, où qu'il soit niché."""
    pile = [schema]
    while pile:
        noeud = pile.pop()
        if isinstance(noeud, dict):
            cible = noeud.get("project_status")
            if isinstance(cible, dict) and "enum" in cible:
                return cible["enum"]
            pile.extend(v for v in noeud.values() if isinstance(v, (dict, list)))
        elif isinstance(noeud, list):
            pile.extend(v for v in noeud if isinstance(v, (dict, list)))
    raise AssertionError("enum project_status introuvable dans le schéma de veille")


def test_une_langue_ne_devient_vivante_que_traduite():
    """Une langue ne passe en PRÉPARATION → VIVANTE que si CHAQUE module est traduit.

    🔴 C'est le garde qui protège la mise en ligne du néerlandais. Ses 740 chaînes ont été
    créées le 2026-11-02 en COPIANT le texte français — à dessein : un traducteur natif a
    besoin de la source en place. Mais une copie du français dans un bloc nommé `nl` est
    exactement ce qui part en ligne sans que personne ne le voie, et en une seule fois.

    🔴 ET IL SE COMPTE PAR MODULE, PAS EN BLOC. Première version : un ratio AGRÉGÉ sur toute
    la surface. Le traducteur a prévenu, et la mesure lui a donné raison plus durement qu'il
    ne le disait — au 2026-11-02, l'agrégat tombait à **15 %**, donc « traduite », pendant que
    `glossaire.ts` (20 chaînes sur 20) et `dossier.ts` (38 sur 38) étaient ENCORE
    INTÉGRALEMENT EN FRANÇAIS. Douze modules traduits payaient pour les quatre autres. Une
    moyenne sur des parties indépendantes ne dit rien de la pire d'entre elles : c'est la
    même faute que de compter des fiches mesurées au lieu de comparer des ensembles
    [[gate-deux-populations-meme-racine]].

    Le seuil n'est pas zéro : des valeurs restent légitimement identiques d'une langue à
    l'autre — un sigle (« PUE »), une URL, un nom propre, « data center » en néerlandais. On
    refuse un MODULE dont la majorité des chaînes est encore celle du français.
    """
    vivantes = _langues_vivantes()
    reference = vivantes[0]
    for lg in vivantes[1:]:
        fautifs: list[tuple[str, int, int]] = []
        for fichier in TABLES_MODULES:
            texte = (CONTENU / fichier).read_text(encoding="utf-8")
            try:
                ref = _valeurs(bloc(texte, reference.upper()))
                autre = _valeurs(bloc(texte, lg.upper()))
            except AssertionError:
                continue
            communes = [c for c in ref if c in autre]
            if not communes:
                continue
            identiques = sum(1 for c in communes if autre[c] == ref[c])
            if identiques / len(communes) >= _SEUIL_MODULE_TRADUIT:
                fautifs.append((fichier, identiques, len(communes)))
        assert not fautifs, (
            f"la langue {lg.upper()} est déclarée VIVANTE mais {len(fautifs)} module(s) ont "
            f"leurs chaînes encore identiques au {reference.upper()} :\n"
            + "\n".join(
                f"  · {f} — {i} sur {t} ({round(100 * i / t)} %)" for f, i, t in fautifs
            )
            + f"\n\nUne table copiée n'est pas une table traduite. Remettre {lg.upper()} dans "
            f"`LANGUES_EN_PREPARATION` jusqu'à ce que CHAQUE module soit écrit : un module "
            f"oublié sert du français sous pavillon étranger, sur toutes ses pages."
        )


# La part de chaînes identiques au-delà de laquelle un module n'est pas traduit. Par MODULE :
# un agrégat laisserait les modules écrits payer pour les modules oubliés.
_SEUIL_MODULE_TRADUIT = 0.5


def test_le_garde_de_traduction_mord_vraiment(tmp_path, monkeypatch):
    """Contre-épreuve : une langue vivante aux valeurs copiées fait rougir le garde.

    🔴 Éprouvé sur une table FABRIQUÉE, pas sur l'état réel de `nl` : la première version
    de ce canari supposait `nl` non traduite — il a cassé le jour où la traduction a
    dépassé 50 %, c'est-à-dire exactement quand tout allait bien. Un canari qui dépend
    de l'avancement du travail mesure l'avancement, pas le garde.
    """
    fausse = tmp_path / "fausse-table.ts"
    fausse.write_text(
        'const FR = {\n  a: "bonjour",\n  b: "le monde",\n};\n\n'
        'const XX: typeof FR = {\n  a: "bonjour",\n  b: "le monde",\n};\n',
        encoding="utf-8",
    )
    monkeypatch.setitem(globals(), "CONTENU", tmp_path)
    monkeypatch.setitem(globals(), "TABLES_MODULES", {"fausse-table.ts": "table fabriquée"})
    monkeypatch.setitem(globals(), "_langues_vivantes", lambda: ["fr", "xx"])
    with pytest.raises(AssertionError, match="encore identiques"):
        test_une_langue_ne_devient_vivante_que_traduite()


def _valeurs(litteral: str) -> dict[str, str]:
    """Les chaînes d'un littéral, par chemin de clé — pour comparer deux langues.

    Même discipline que `chemins()` : lecture caractère par caractère, une clé n'est reconnue
    que là où une clé peut commencer. On ne relève que les valeurs de type CHAÎNE ; un nombre
    ou un booléen n'a pas à différer d'une langue à l'autre.
    """
    import engine.tests.i18n_table as it

    sortie: dict[str, str] = {}
    prefixe: list[str] = []
    pile: list[tuple[str, str | None]] = []
    attente: str | None = None
    attend_cle = False
    i = it._saute_blanc_et_commentaires(litteral, 0)
    while i < len(litteral):
        i = it._saute_blanc_et_commentaires(litteral, i)
        if i >= len(litteral):
            break
        c = litteral[i]
        if c in "{[":
            pile.append(("obj" if c == "{" else "arr", attente))
            if attente is not None:
                prefixe.append(attente)
            attente, attend_cle = None, c == "{"
            i += 1
            continue
        if c in "}]":
            if pile:
                _, seg = pile.pop()
                if seg is not None and prefixe and prefixe[-1] == seg:
                    prefixe.pop()
            attente = None
            attend_cle = bool(pile) and pile[-1][0] == "obj"
            i += 1
            continue
        if c in "\"'`":
            fin = it._fin_de_chaine(litteral, i)
            apres = it._saute_blanc_et_commentaires(litteral, fin)
            if attend_cle and apres < len(litteral) and litteral[apres] == ":":
                nom = litteral[i + 1 : fin - 1]
                attente, attend_cle = nom, False
                i = apres + 1
                continue
            if attente is not None:
                sortie[".".join(prefixe + [attente])] = litteral[i + 1 : fin - 1]
            i = fin
            continue
        m = it._IDENT.match(litteral, i)
        if m:
            apres = it._saute_blanc_et_commentaires(litteral, m.end())
            if attend_cle and apres < len(litteral) and litteral[apres] == ":":
                attente, attend_cle = m.group(), False
                i = apres + 1
                continue
            i = m.end()
            continue
        if c == ",":
            attente = None
            attend_cle = bool(pile) and pile[-1][0] == "obj"
        i += 1
    return sortie


def test_le_total_annonce_en_tete_est_le_bon():
    """L'en-tête de `DETTE_I18N` annonce un total : il doit être celui de la table.

    🔴 Il avait tort. La ligne disait « 99 branches dans 26 fichiers » quand la table en
    portait 85 dans 22 — un commentaire ne suit pas une table toute seule. Les gardes
    comptent ce qui est publié, jamais le commentaire qui le JUSTIFIE : celui-ci est
    désormais compté.
    """
    texte = __file__ and open(__file__, encoding="utf-8").read()
    m = re.search(r"État au [\d-]+.*?: (\d+) branches nues dans (\d+) fichiers", texte)
    assert m, (
        "la ligne « État au … : N branches nues dans M fichiers » a disparu de l'en-tête de "
        "DETTE_I18N — sans elle, personne ne lit le total, et le cliquet perd son compteur"
    )
    annonce_branches, annonce_fichiers = int(m.group(1)), int(m.group(2))
    assert annonce_branches == sum(DETTE_I18N.values()), (
        f"l'en-tête annonce {annonce_branches} branches, la table en porte "
        f"{sum(DETTE_I18N.values())}"
    )
    assert annonce_fichiers == len(DETTE_I18N), (
        f"l'en-tête annonce {annonce_fichiers} fichiers, la table en porte {len(DETTE_I18N)}"
    )


def test_le_cliquet_de_dette_mord_dans_les_deux_sens(tmp_path, monkeypatch):
    """Contre-épreuve : le cliquet doit voir une dette qui remonte ET une dette périmée.

    🔴 Le fichier éprouvé est PRIS DANS LA TABLE, il n'est plus nommé en dur. La version
    d'avant visait `components/Landing.astro` — qui est passé à zéro et a quitté la table le
    2026-10-29, emportant la contre-épreuve avec lui. Une contre-épreuve qui nomme sa cible
    meurt le jour où on répare cette cible, c'est-à-dire exactement quand on y touche.
    """
    cible, compte = next(iter(sorted(DETTE_I18N.items())))
    monkeypatch.setitem(DETTE_I18N, cible, compte - 1)  # on en déclare un de moins
    with pytest.raises(AssertionError, match="ne remonte pas"):
        test_la_dette_i18n_ne_remonte_jamais()
    monkeypatch.setitem(DETTE_I18N, cible, compte + 99)  # on en déclare trop
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


# ──────────────────────────────────────────────────────────────────────────────────────────
# Le lecteur qui n'est PAS en France doit savoir que le guide parle du droit français
# ──────────────────────────────────────────────────────────────────────────────────────────
PREVIZ_TS = REPO_ROOT / "site" / "src" / "config" / "previz.ts"
PAGES_PREVIZ = PAGES / "previz"


def test_une_langue_servie_hors_france_porte_son_avertissement_de_contexte():
    """`comprendre` doit porter son avertissement de contexte dans toute langue servie ≠ FR.

    🔴 CE QUE `ASYMETRIES_MODULES` NE FAISAIT PAS. Les trois clés `contextNotice`,
    `inFranceLabel` et `tag` y sont déclarées comme une asymétrie VOULUE — l'anglais les
    porte, le français n'en a structurellement pas besoin. Mais une exemption rend une clé
    INVISIBLE au garde de parité : elle n'oblige personne à l'écrire. Le néerlandais pouvait
    donc arriver sans elles, passer toute la suite au vert, et dire à un élu néerlandais que
    le délai de recours français est le sien. C'est [[favorable-par-absence-de-detection]]
    appliqué à une exemption : l'absence de reproche n'est pas une garantie.

    L'obligation mord au moment où la langue devient VIVANTE, pas pendant la rédaction :
    c'est le moment où la page serait servie, et une langue en préparation a le droit d'être
    incomplète. La liste des langues concernées n'est pas recopiée ici — elle se DÉRIVE : la
    France est le seul lecteur chez lui, toute autre langue servie est un lecteur ailleurs.
    """
    requises = ASYMETRIES_MODULES["comprendre.ts"]
    assert requises, "l'asymétrie de `comprendre.ts` est vide — ce garde ne garde plus rien"
    texte = (CONTENU / "comprendre.ts").read_text(encoding="utf-8")
    for lg in sorted(set(_langues_vivantes()) - {"fr"}):
        cles = {c.split(".")[-1] for c in chemins(bloc(texte, lg.upper()))}
        manquantes = sorted(requises - cles)
        assert not manquantes, (
            f"comprendre.ts — {lg.upper()} est servie et ne porte pas {manquantes}. Le guide "
            f"« Comprendre » est écrit depuis le droit FRANÇAIS (droits, calendrier, enquête "
            f"publique) ; sans cet avertissement, la page laisse croire à un lecteur de "
            f"{lg.upper()} que les délais français sont les siens. Le gabarit teste ces clés "
            f"(`t.x && …`), donc leur absence ne casse rien : elle efface l'avertissement."
        )


def test_le_garde_d_avertissement_hors_france_mord_vraiment(tmp_path, monkeypatch):
    """Contre-épreuve : une langue servie dont `comprendre` a perdu son avertissement."""
    faux = tmp_path / "content"
    faux.mkdir(parents=True)
    (faux / "comprendre.ts").write_text(
        'const FR = { titre: "Comprendre" };\n'
        'const NL = { titre: "Begrijpen" };\n',
        encoding="utf-8",
    )
    monkeypatch.setitem(globals(), "CONTENU", faux)
    monkeypatch.setitem(globals(), "_langues_vivantes", lambda: ["fr", "nl"])
    with pytest.raises(AssertionError, match="est servie et ne porte pas"):
        test_une_langue_servie_hors_france_porte_son_avertissement_de_contexte()


def test_chaque_langue_declaree_sait_ou_elle_vit():
    """`RACINE` doit couvrir toute langue déclarée, et par une adresse qui lui est propre.

    Le layout construisait son lien d'accueil avec `lang === "en" ? "/" : "/fr/"`. Un ternaire
    binaire ne SIGNALE pas le cas qu'il ignore, il en choisit un : le néerlandais serait parti
    sur l'accueil français, sans un mot. Une langue de plus que la table ne connaît rend
    `undefined` dans un href — c'est-à-dire un lien mort, pas une erreur.
    """
    texte = (CONTENU / "langues.ts").read_text(encoding="utf-8")
    m = re.search(r"RACINE: Record<LangueDeclaree, string> = \{([^}]*)\}", texte)
    assert m, "RACINE introuvable dans langues.ts — le harnais ne sait plus où vit une langue"
    racines = dict(re.findall(r'(\w+):\s*"([^"]*)"', m.group(1)))
    declarees = set(_langues_declarees())
    manquantes = sorted(declarees - set(racines))
    assert not manquantes, (
        f"des langues déclarées n'ont pas de racine : {manquantes} — leur lien d'accueil "
        f"rendrait `undefined`, un lien mort sur toutes leurs pages"
    )
    doublons = [r for r in racines.values() if list(racines.values()).count(r) > 1]
    assert not doublons, (
        f"deux langues partagent la même racine ({sorted(set(doublons))}) : l'une servirait "
        f"les pages de l'autre"
    )


def test_la_previz_ne_sort_rien_en_production():
    """Une page de préviz doit tenir son portillon dans `getStaticPaths`, jamais dans le gabarit.

    🔴 La forme COMPTE. Une page Astro sans `getStaticPaths` est toujours construite, et un
    `if` qui ne rend rien laisse quand même un fichier HTML dans `dist/` : une langue
    déclarée « en préparation » serait servie sous une autre adresse. Rendre `[]` est la
    seule forme qui ne produise pas un octet — et c'est `cheminsPreviz()` qui la porte, à un
    seul endroit, lu depuis l'environnement.
    """
    source = PREVIZ_TS.read_text(encoding="utf-8")
    assert "process.env.SMDC_PREVIZ" in source, (
        "le portillon de préviz ne lit plus l'environnement — s'il devient constant, les "
        "pages de préviz partent en production"
    )
    assert re.search(r"return PREVIZ \? fabrique\(\) : \[\]", source), (
        "`cheminsPreviz` ne rend plus `[]` quand le portillon est fermé"
    )
    pages = sorted(PAGES_PREVIZ.rglob("*.astro"))
    assert pages, f"aucune page sous {PAGES_PREVIZ.relative_to(REPO_ROOT)} — le relevé ne cherche plus"
    for page in pages:
        texte = page.read_text(encoding="utf-8")
        assert "getStaticPaths" in texte and "cheminsPreviz(" in texte, (
            f"{page.relative_to(PAGES)} ne passe pas par `cheminsPreviz()` dans un "
            f"`getStaticPaths` : elle serait construite en production"
        )


def test_les_trous_nommes_sont_les_memes_dans_toutes_les_langues():
    """Une chaîne traduite doit porter EXACTEMENT les mêmes trous `{nom}` que sa source.

    🔴 Le trou perdu est muet. `"{v} sites à {commune}"` traduit sans `{commune}` ne casse
    rien : la phrase s'affiche, bien tournée, et la commune a disparu. Le trou EN TROP est
    pire — `{commune}` dans une langue où le code ne le remplit pas s'affiche tel quel, en
    accolades, sur la page. Aucun des deux ne lève d'erreur ; `astro build` ne tourne pas
    `astro check`, et de toute façon une chaîne est une chaîne.

    L'épreuve porte sur les langues DÉCLARÉES, pas seulement servies : c'est pendant la
    rédaction qu'un trou se perd, et une langue en préparation part d'une copie où les trous
    sont justes — la faute est donc datable au geste qui l'introduit. L'ORDRE est libre :
    l'interpolation se fait par nom (`.replace("{grade}", …)`), et une langue a le droit de
    tourner sa phrase autrement. C'est l'ENSEMBLE qui doit tenir.
    """
    declarees = _langues_declarees()
    reference = declarees[0]
    fautes: list[str] = []
    for fichier in TABLES_MODULES:
        texte = (CONTENU / fichier).read_text(encoding="utf-8")
        try:
            ref = _valeurs(bloc(texte, reference.upper()))
        except AssertionError:
            continue
        for lg in declarees[1:]:
            try:
                autre = _valeurs(bloc(texte, lg.upper()))
            except AssertionError:
                continue
            for cle, val in ref.items():
                if cle not in autre:
                    continue  # l'absence de clé est l'affaire du garde de parité
                attendus = set(re.findall(r"\{[a-zA-Z_][\w]*\}", val))
                servis = set(re.findall(r"\{[a-zA-Z_][\w]*\}", autre[cle]))
                if attendus != servis:
                    perdus = sorted(attendus - servis)
                    ajoutes = sorted(servis - attendus)
                    fautes.append(
                        f"  {fichier} · {lg.upper()} · {cle} —"
                        + (f" trou(s) PERDU(S) {perdus}" if perdus else "")
                        + (f" trou(s) EN TROP {ajoutes}" if ajoutes else "")
                    )
    assert not fautes, (
        f"{len(fautes)} chaîne(s) traduites n'ont plus les trous de leur source :\n"
        + "\n".join(fautes[:20])
        + "\n\nUn trou perdu efface une donnée sans rien casser ; un trou en trop s'affiche "
        "en accolades sur la page. L'ordre est libre, l'ensemble ne l'est pas."
    )


def test_chaque_langue_declaree_a_sa_regle_de_pluriel():
    """Toute langue déclarée doit porter sa RÈGLE de pluriel, pas hériter de celle du voisin.

    Le français met zéro au singulier, l'anglais et le néerlandais au pluriel. Un
    `n > 1 ? … : …` dans un gabarit applique donc la règle française au néerlandais sans
    rien signaler. Une langue sans règle rendrait `REGLE_PLURIEL[lang]` → `undefined`, puis
    `undefined(n)` : là, au moins, ça casse. Ce test empêche d'en arriver là.
    """
    texte = (CONTENU / "langues.ts").read_text(encoding="utf-8")
    m = re.search(
        r"REGLE_PLURIEL: Record<LangueDeclaree, \(n: number\) => FormePluriel> = \{(.*?)\n\};",
        texte,
        re.S,
    )
    assert m, "REGLE_PLURIEL introuvable dans langues.ts"
    reglees = set(re.findall(r"^\s*(\w+):", m.group(1), re.M))
    manquantes = sorted(set(_langues_declarees()) - reglees)
    assert not manquantes, (
        f"des langues déclarées n'ont pas de règle de pluriel : {manquantes} — leurs phrases "
        f"à compte prendraient la règle d'une autre langue, ou rien du tout"
    )


# La prose qui vit HORS des tables gardées : `config/stats.ts` porte les phrases des chiffres
# de l'accueil et des pages de chiffres sous forme de paires `{ fr: …, en: … }`. Elles sont
# dans le périmètre signé (l'accueil en fait partie) mais pas dans `TABLES_MODULES` — donc pas
# dans le garde de parité. Le compte est DÉCLARÉ et ne peut que baisser : un cliquet, comme
# `DETTE_I18N`, parce qu'un trou qu'on mesure vaut mieux qu'un trou qu'on découvre en servant.
DETTE_PAIRES_STATS = 63


def test_la_prose_hors_table_ne_grossit_jamais():
    """`config/stats.ts` ne doit pas accumuler de prose à deux langues en douce.

    🔴 Trouvé par la préviz, pas par un test : l'accueil néerlandais PLANTAIT sur `fmtPct`
    parce que la table de formes s'arrêtait à deux langues. Le format, lui, se déclare en une
    ligne (c'est fait). Mais derrière il reste les PHRASES, les lignes de source, les noms de
    pays et les périmètres — de la prose, qui n'est pas au harnais et ne peut pas s'inventer.
    Tant qu'elle est là, l'accueil néerlandais ne peut pas être complet, et ce nombre le dit.
    """
    texte = (REPO_ROOT / "site" / "src" / "config" / "stats.ts").read_text(encoding="utf-8")
    paires = re.findall(
        r'\{\s*fr:\s*"(?:[^"\\]|\\.)*",\s*en:\s*"(?:[^"\\]|\\.)*"\s*\}', texte
    )
    assert len(paires) <= DETTE_PAIRES_STATS, (
        f"{len(paires)} paires fr/en dans config/stats.ts, la dette déclarée est "
        f"{DETTE_PAIRES_STATS} : de la prose vient d'être ajoutée hors des tables gardées. "
        f"Elle doit rejoindre un module de `TABLES_MODULES`, où la parité se vérifie."
    )
    if len(paires) < DETTE_PAIRES_STATS:
        pytest.fail(
            f"bonne nouvelle, et le cliquet doit suivre : plus que {len(paires)} paires "
            f"(déclaré : {DETTE_PAIRES_STATS}). Abaissez DETTE_PAIRES_STATS à {len(paires)}."
        )


DONNEE_SERVIE = REPO_ROOT / "site" / "public" / "data"


def _objets_bilingues(noeud, sortie: list) -> None:
    """Les objets de la donnée servie qui portent une chaîne PAR LANGUE."""
    if isinstance(noeud, dict):
        if "fr" in noeud and "en" in noeud and all(
            isinstance(v, str) for v in noeud.values() if v is not None
        ):
            sortie.append(noeud)
            return
        for v in noeud.values():
            _objets_bilingues(v, sortie)
    elif isinstance(noeud, list):
        for v in noeud:
            _objets_bilingues(v, sortie)


def test_la_donnee_servie_parle_toutes_les_langues_vivantes():
    """La DONNÉE servie doit porter chaque langue vivante, pas seulement les tables du site.

    🔴 Trouvé par la préviz, au rendu, pas par un test : une page de portrait néerlandaise
    affiche ses libellés d'indicateur et ses questions à poser **en anglais**. Pas une
    erreur, pas un blanc — `SitePortrait.astro` lit `lang === "fr" ? o.fr : o.en`, donc toute
    langue qui n'est pas le français reçoit l'anglais. C'est le piège des 17 ternaires, mais
    sur le seul bloc qui dit au lecteur **ce qu'il peut faire**.

    Ces chaînes ne vivent pas dans `content/` : elles sont ÉMISES par le pipeline. Les
    traduire n'est donc pas un geste de harnais, et ce test ne corrige rien — il refuse
    qu'on serve une langue à qui la donnée ne répond pas.

    Il se TAIT quand la donnée n'est pas là (la CI du dépôt public ne l'a pas : `site/public/
    data/` est ignoré) — même discipline que les gates de corpus : un côté absent, rien à
    comparer, rien à garder.

    ANGLE MORT DÉCLARÉ : on ne parcourt que `scores.json` et `methodology.json`, qui portent
    le vocabulaire PARTAGÉ (433 chaînes distinctes mesurées le 2026-11-02, ~3 150 mots). Les
    3 267 fiches portent EN PLUS leur prose propre (accroche, justification par badge) ;
    les parcourir ajouterait 65 Mo de lecture à chaque `make test`. Ce trou est déclaré ici,
    pas découvert en servant.
    """
    import json

    fichiers = [DONNEE_SERVIE / "scores.json", DONNEE_SERVIE / "methodology.json"]
    if not all(f.is_file() for f in fichiers):
        pytest.skip("donnée servie absente de ce checkout — rien à comparer")

    vivantes = set(_langues_vivantes())
    objets: list = []
    for f in fichiers:
        _objets_bilingues(json.loads(f.read_text(encoding="utf-8")), objets)
    assert objets, "aucun objet bilingue trouvé — le relevé ne cherche plus au bon endroit"

    distinctes = {
        tuple(sorted(o.items())) for o in objets if vivantes - set(o)
    }
    assert not distinctes, (
        f"{len(distinctes)} chaîne(s) distinctes de la donnée servie ne portent pas toutes "
        f"les langues vivantes ({sorted(vivantes)}) : le pipeline ne les émet pas. Servies "
        f"telles quelles, elles sortent en ANGLAIS sur une page qui n'est pas anglaise — "
        f"sans erreur et sans blanc. Exemple : {sorted(distinctes)[0][:2]}"
    )


def test_le_garde_de_la_donnee_servie_mord_vraiment(monkeypatch):
    """Contre-épreuve : on déclare `nl` vivante — la donnée, elle, ne le sait pas.

    C'est l'épreuve qui donne sa valeur au test précédent : elle prouve qu'il dira NON le
    jour où quelqu'un ouvrira le néerlandais sans que le pipeline ait suivi.
    """
    if not (DONNEE_SERVIE / "scores.json").is_file():
        pytest.skip("donnée servie absente de ce checkout")
    monkeypatch.setitem(globals(), "_langues_vivantes", lambda: ["fr", "en", "nl"])
    with pytest.raises(AssertionError, match="ne portent pas toutes les langues vivantes"):
        test_la_donnee_servie_parle_toutes_les_langues_vivantes()


QUESTIONS_DERIVEES = CONTENU / "questions-derivees.ts"


def _litteraux_par_langue(texte: str) -> list[set[str]]:
    """Les littéraux `{ fr: …, en: … }` d'un module, rendus comme ensembles de clés.

    Troisième forme d'i18n du dépôt, après les blocs `const FR/NL` et les littéraux tenus
    DANS un composant : une table dont CHAQUE entrée porte ses langues. `bloc()` ne sait pas
    la lire — elle n'a pas de bloc de langue — d'où ce relevé à part.
    """
    sortie: list[set[str]] = []
    for m in re.finditer(r"\bfr\s*:", texte):
        debut = texte.rfind("{", 0, m.start())
        if debut < 0:
            continue
        profondeur, i = 0, debut
        while i < len(texte):
            if texte[i] == "{":
                profondeur += 1
            elif texte[i] == "}":
                profondeur -= 1
                if profondeur == 0:
                    break
            i += 1
        sortie.append(set(re.findall(r"\b(\w+)\s*:", texte[debut : i + 1])))
    return sortie


def test_les_questions_a_poser_parlent_toutes_les_langues_vivantes():
    """`questions-derivees.ts` doit porter chaque langue servie — il n'était gardé par RIEN.

    🔴 C'est le module qui engendre les « à demander » du portrait : la seule phrase du site
    qui dise à un lecteur quoi réclamer, et à qui. Il a échappé aux deux gardes existants
    parce qu'il a une TROISIÈME forme — ni blocs `const FR/NL`, ni littéral dans un
    composant, mais `Record<clé, {fr, en}>`. La préviz l'a montré en anglais sur une page
    néerlandaise, et `TABLES_MODULES` ne pouvait pas le voir : on n'y déclare que ce qu'on
    sait lire.

    Et il a d'abord été imputé au pipeline (`registers/absence.py`) : la chaîne servie n'y
    est pas. Vérifier d'où vient VRAIMENT une chaîne avant de décider qui doit l'écrire —
    une carte de provenance fausse envoie le travail au mauvais dépôt.
    """
    texte = QUESTIONS_DERIVEES.read_text(encoding="utf-8")
    litteraux = _litteraux_par_langue(texte)
    assert len(litteraux) >= 10, (
        f"seulement {len(litteraux)} littéral(aux) de langue relevé(s) dans "
        f"{QUESTIONS_DERIVEES.name} — le relevé ne cherche plus"
    )
    vivantes = set(_langues_vivantes())
    manquants = [sorted(vivantes - cles) for cles in litteraux if vivantes - cles]
    assert not manquants, (
        f"{len(manquants)} question(s) ou amorce(s) ne portent pas toutes les langues "
        f"vivantes : il manque {sorted({l for m in manquants for l in m})}. Servies telles "
        f"quelles, elles sortent dans une autre langue que celle de la page — c'est la "
        f"phrase qui dit au lecteur quoi réclamer."
    )


def test_le_garde_des_questions_a_poser_mord_vraiment(tmp_path, monkeypatch):
    """Contre-épreuve sur une table fabriquée, pas sur l'avancement du travail."""
    faux = tmp_path / "questions-derivees.ts"
    faux.write_text(
        "export const Q = {\n" + "".join(
            f'  q{i}: {{ fr: "a{i}", en: "b{i}" }},\n' for i in range(12)
        ) + "};\n",
        encoding="utf-8",
    )
    monkeypatch.setitem(globals(), "QUESTIONS_DERIVEES", faux)
    monkeypatch.setitem(globals(), "_langues_vivantes", lambda: ["fr", "en", "nl"])
    with pytest.raises(AssertionError, match="ne portent pas toutes les langues"):
        test_les_questions_a_poser_parlent_toutes_les_langues_vivantes()
