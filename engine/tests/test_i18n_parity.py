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
    # 🔴 PAIRS est une liste FR↔EN, née quand le site n'avait que deux langues. Une page
    # néerlandaise n'y entre pas — « la paire » n'existe plus, c'est une famille. Elle se
    # déclare donc dans `config/routes.ts`, qui est désormais la source de ce qui existe
    # dans quelle langue, et ce test accepte les deux déclarations. Fusionner PAIRS dans
    # la table reste à faire : PAIRS porte en plus un drapeau `compare` que la table n'a
    # pas. Tant que les deux vivent, c'est ici que leur union se lit.
    en_table = {
        c.strip("/").replace(":id", "[id]") for f in _familles().values() for c in f.values()
    }

    def _declaree_en_table(page: str) -> bool:
        adresse = page.removesuffix(".astro").removesuffix("/index")
        return adresse in en_table or adresse.removesuffix("index").strip("/") in en_table

    declarees = {fr for fr, _, _ in PAIRS} | {en for _, en, _ in PAIRS} | set(SANS_JUMELLE)
    orphelines = sorted(
        p for p in _pages_du_disque() - declarees if not _declaree_en_table(p)
    )
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
    # La page doit disparaître des DEUX déclarations : depuis que `config/routes.ts` est
    # une source valable, n'en amputer qu'une ne prouve plus rien — et c'est ce test qui l'a
    # dit, en cessant de mordre à la seconde où la table a pris le relais.
    ampute = [p for p in PAIRS if p[0] != "fr/actu.astro"]
    monkeypatch.setitem(globals(), "PAIRS", ampute)
    sans_actu = {
        ident: ch for ident, ch in _familles().items() if ident != "actu"
    }
    monkeypatch.setitem(globals(), "_familles", lambda: sans_actu)
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
# 63 → 43 le 2026-11-03 : les 20 noms de pays ont reçu leur néerlandais. Le cliquet a crié
# pour le DIRE — un cliquet qui ne signale que les hausses laisse oublier les baisses, et
# une dette qu'on ne voit pas diminuer est une dette qu'on cesse de rembourser.
DETTE_PAIRES_STATS = 43


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

# 🔴 CES TROIS ÉPREUVES LISENT UN SOUS-PRODUIT, PAS UNE SOURCE. `site/public/data/` est
# ignoré par git : il est ÉCRIT par `make build`. Or `make deploy` lance la suite AVANT le
# build (c'est écrit dans la cible). Un artefact plus vieux que le code qui l'émet fait donc
# tomber la suite en accusant « un pipeline a cessé d'émettre » — alors que rien n'a cessé :
# le fichier date d'avant le changement. C'est arrivé le 2026-11-04, dans l'arbre de
# déploiement, sur un artefact du 2 novembre, le jour où le néerlandais est arrivé sur main.
#
# On ne peut pas conclure d'un artefact périmé. On se TAIT donc, exactement comme on se tait
# quand il est absent — et les dents, elles, sont APRÈS le build : `scripts/
# check_langue_donnee_servie.py`, lancé par `make deploy` sur l'artefact frais.
SOURCES_DONNEE_SERVIE = (
    REPO_ROOT / "engine",            # scoring.py (_DOC_LABELS, CITABLE), artifacts.py
    REPO_ROOT / "data" / "methodology",  # d'où sort methodology.json
)


def _perimee(fichiers) -> str | None:
    """« Rien à comparer » : l'artefact est absent, ou plus vieux que ce qui l'écrit."""
    manquants = [f for f in fichiers if not f.is_file()]
    if manquants:
        return "donnée servie absente de ce checkout — rien à comparer"
    artefact = min(f.stat().st_mtime for f in fichiers)
    sources = [
        s for racine in SOURCES_DONNEE_SERVIE
        for s in (racine.rglob("*.py") if racine.name == "engine" else racine.rglob("*.json"))
        if "tests" not in s.parts
    ]
    recentes = [s for s in sources if s.stat().st_mtime > artefact]
    if recentes:
        return (
            f"artefact servi PÉRIMÉ ({len(recentes)} source(s) plus récentes, p.ex. "
            f"{recentes[0].relative_to(REPO_ROOT)}) — on ne conclut pas d'un sous-produit "
            f"d'avant le changement. Relancez `make build` ; les dents sont de toute façon "
            f"après le build (scripts/check_langue_donnee_servie.py)."
        )
    return None


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
    if (raison := _perimee(fichiers)) is not None:
        pytest.skip(raison)

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
    """Contre-épreuve : on déclare vivante une langue que la donnée ne porte pas.

    🔴 CETTE ÉPREUVE S'APPUYAIT SUR LE NÉERLANDAIS, et elle a cessé de mordre — parce que la
    donnée servie porte MAINTENANT le néerlandais : libellés d'indicateurs, noms de piliers,
    phrase citable. Une contre-épreuve adossée à un trou meurt le jour où le trou se comble,
    et elle meurt en silence : elle passe au vert pour la mauvaise raison.
    (C'est aussi, au passage, la meilleure nouvelle du jour : si on faisait passer `nl`
    vivante, le garde de la donnée servie ne s'y opposerait plus.)

    Elle s'appuie donc sur une langue qui n'existera jamais dans la donnée. Ce que le test
    doit prouver, c'est qu'il SAIT DIRE NON — pas que le néerlandais est incomplet.
    """
    if (raison := _perimee([DONNEE_SERVIE / "scores.json",
                            DONNEE_SERVIE / "methodology.json"])) is not None:
        pytest.skip(raison)
    monkeypatch.setitem(globals(), "_langues_vivantes", lambda: ["fr", "en", "zz"])
    with pytest.raises(AssertionError, match="ne portent pas toutes les langues vivantes"):
        test_la_donnee_servie_parle_toutes_les_langues_vivantes()


def test_la_donnee_servie_porte_deja_le_neerlandais():
    """Le constat, nommé : la donnée servie parle néerlandais, langue pas encore ouverte.

    Ce n'est pas un doublon du garde des langues vivantes — c'est le jalon qu'il ne peut pas
    dire, puisqu'il ne regarde que les langues DÉJÀ servies. Le jour où ce test tombe, c'est
    qu'un pipeline a cessé d'émettre le néerlandais ; on le saura avant d'ouvrir la langue,
    pas après.
    """
    import json

    fichiers = [DONNEE_SERVIE / "scores.json", DONNEE_SERVIE / "methodology.json"]
    if (raison := _perimee(fichiers)) is not None:
        pytest.skip(raison)
    objets: list = []
    for f in fichiers:
        _objets_bilingues(json.loads(f.read_text(encoding="utf-8")), objets)
    assert objets, "le relevé ne trouve aucun objet bilingue — il ne garde plus rien"
    sans_nl = [o for o in objets if "nl" not in o]
    assert not sans_nl, (
        f"{len(sans_nl)} objet(s) de la donnée servie sur {len(objets)} ne portent pas le "
        f"néerlandais — un pipeline a cessé de l'émettre. Exemple : "
        f"{list(sans_nl[0].items())[:2]}"
    )


QUESTIONS_DERIVEES = CONTENU / "questions-derivees.ts"


def _litteraux_par_langue(texte: str) -> list[set[str]]:
    """Les littéraux `{ fr: …, en: … }` d'un module, rendus comme ensembles de clés.

    Troisième forme d'i18n du dépôt, après les blocs `const FR/NL` et les littéraux tenus
    DANS un composant : une table dont CHAQUE entrée porte ses langues. `bloc()` ne sait pas
    la lire — elle n'a pas de bloc de langue — d'où ce relevé à part.
    """
    sortie: list[set[str]] = []
    # 🔴 `fr: string` est une DÉCLARATION DE TYPE, pas une chaîne. Ma première version les
    # comptait et annonçait douze traductions manquantes qui n'existaient pas — un garde qui
    # crie faux use la confiance qu'on lui fait aussi sûrement qu'un garde muet.
    for m in re.finditer(r"\bfr\s*:\s*[\"'`]", texte):
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
        sortie.append(set(re.findall(r"\b(\w+)\s*:\s*[\"'`]", texte[debut : i + 1])))
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


BLOCS_RICHES = CONTENU / "understand-blocks.ts"


def _blocs_de_comprendre(langue: str) -> list[tuple[str, str, str]]:
    """(id, ancre, slot) des blocs de « Comprendre », dans l'ordre, pour une langue."""
    texte = (CONTENU / "comprendre.ts").read_text(encoding="utf-8")
    m = re.search(rf"^const {langue.upper()}\b.*?blocks:\s*\[(.*?)\n\s*\],", texte, re.S | re.M)
    if not m:
        return []
    return [
        (i, a, s or "")
        for i, a, s in re.findall(
            r'id:\s*"([^"]+)",\s*anchor:\s*"([^"]+)"[^}]*?(?:slot:\s*"([^"]+)")?[^}]*\}',
            m.group(1),
        )
    ]


def test_l_ancre_ne_sert_plus_de_cle_de_donnees():
    """L'ancre d'un bloc est une ADRESSE ; sa clé de données est un identifiant stable.

    🔴 Trouvé par la préviz, au rendu, et invisible à tout le reste : la page « Comprendre »
    néerlandaise rendait **144 blocs contre 182 en français**. Les tables riches étaient
    indexées par l'ancre — `RICH_FR` sur `commune`, `droits`… — et la page néerlandaise
    demandait `gemeente`, `rechten`. Personne ne répondait. Rien ne cassait : le contenu
    n'était simplement jamais DEMANDÉ, et quatre des cinq blocs documentés disparaissaient.

    Les clés étaient justes des deux côtés ; c'est leur COUPLAGE qui était faux — une ancre
    traduite (ce qu'elle doit être, l'anglais le fait depuis toujours) emportait avec elle une
    clé qui, elle, ne doit pas bouger. [[id-daffichage-perime-rubrique-muette]] appliqué à
    une adresse.

    Les identifiants sont choisis DIFFÉRENTS des ancres de chaque langue (sauf `faq`, dont le
    sigle est universel — d'où `faq-block`) : un id qui ressemble à l'ancre d'une langue
    invite à les refusionner le jour où « ça marche quand même ».
    """
    langues = _langues_declarees()
    reference = _blocs_de_comprendre(langues[0])
    assert len(reference) >= 5, (
        f"{len(reference)} bloc(s) relevés dans comprendre.ts — le relevé ne cherche plus"
    )
    ids_ref = [i for i, _, _ in reference]
    for lg in langues[1:]:
        ids = [i for i, _, _ in _blocs_de_comprendre(lg)]
        assert ids == ids_ref, (
            f"comprendre.ts — les identifiants de bloc de {lg.upper()} ne sont pas ceux de "
            f"{langues[0].upper()} : {ids} ≠ {ids_ref}. Un id est la même chose dans toutes "
            f"les langues ; c'est l'ancre qui se traduit."
        )

    texte = BLOCS_RICHES.read_text(encoding="utf-8")
    tables = {
        m.group(1): set(
            re.findall(r'^\s{2}"([\w-]+)":\s*\{', m.group(2), re.M)
        )
        for m in re.finditer(
            r"export const RICH_(\w+)[^=]*= \{(.*?)^\};", texte, re.S | re.M
        )
    }
    assert tables, "aucune table RICH_* relevée — le garde ne garde plus rien"
    connus = set(ids_ref)
    for nom, cles in tables.items():
        intruses = sorted(cles - connus)
        assert not intruses, (
            f"RICH_{nom} porte {len(intruses)} clé(s) qui ne sont l'identifiant d'aucun "
            f"bloc : {intruses}. Servie telle quelle, cette entrée n'est jamais demandée — "
            f"elle ne manque pas à l'écran, elle n'existe pas."
        )
    communes = set.intersection(*tables.values()) if len(tables) > 1 else next(iter(tables.values()))
    for nom, cles in tables.items():
        manquantes = sorted(communes - cles)
        assert not manquantes, (
            f"RICH_{nom} n'a pas {manquantes}, que les autres langues portent — le bloc "
            f"serait vide dans cette langue seulement, sans erreur"
        )


def test_le_garde_du_decouplage_mord_vraiment(tmp_path, monkeypatch):
    """Contre-épreuve : une table riche réindexée sur l'ancre d'une langue."""
    faux = tmp_path / "understand-blocks.ts"
    faux.write_text(
        'export const RICH_FR: Record<string, RichBlock> = {\n'
        '  "gemeente": { intro: "x" },\n'
        "};\n",
        encoding="utf-8",
    )
    monkeypatch.setitem(globals(), "BLOCS_RICHES", faux)
    with pytest.raises(AssertionError, match="n'est jamais demandée|identifiant d'aucun"):
        test_l_ancre_ne_sert_plus_de_cle_de_donnees()


# Les liens internes d'une table de langue doivent rester DANS cette langue. Exemptions
# déclarées, avec leur raison — vide aujourd'hui : il n'y a pas de bonne raison d'envoyer un
# lecteur sur une page qu'il ne lit pas, et si une page n'existe que dans une langue, c'est
# cette absence-là qu'il faut traiter, pas la masquer par un lien.
# `altHref` EST le lien vers l'autre langue : c'est sa raison d'être, pas une faute. (Et
# c'est précisément lui qui devra devenir un sélecteur le jour où il y aura trois langues —
# voir `content/langues.ts`.)
LIENS_HORS_LANGUE_OK: dict[str, set[str]] = {f: {"altHref"} for f in TABLES_MODULES}


def test_une_table_de_langue_ne_renvoie_pas_vers_une_autre_langue():
    """Un lien interne d'une table NL ou EN ne doit pas pointer vers `/fr/…`.

    🔴 Trouvé par le traducteur en relisant son propre travail, et c'est un bug de
    PRODUCTION, pas un défaut néerlandais : la page « Comprendre » anglaise renvoyait son
    lecteur vers la carte FRANÇAISE. Les tables néerlandaises en portent davantage, pour une
    raison bénigne — elles sont nées d'une copie du français — mais elles partiraient en
    ligne avec.

    Un lien est une ROUTE, pas une chaîne : il ne se traduit pas, il se REMAPPE. Et rien ne
    le signale, puisque la page de destination existe et s'affiche : le lecteur change
    simplement de langue sans l'avoir demandé.
    """
    racines = {lg: f"/{lg}/" for lg in _langues_declarees() if lg != "en"}
    fautes: list[str] = []
    for fichier in TABLES_MODULES:
        texte = (CONTENU / fichier).read_text(encoding="utf-8")
        for lg in _langues_declarees():
            try:
                valeurs = _valeurs(bloc(texte, lg.upper()))
            except AssertionError:
                continue
            exempt = LIENS_HORS_LANGUE_OK.get(fichier, set())
            for cle, val in valeurs.items():
                if cle in exempt:
                    continue
                for autre, racine in racines.items():
                    if autre != lg and racine in val:
                        fautes.append(f"  {fichier} · {lg.upper()} · {cle} → {racine}")
    assert not fautes, (
        f"{len(fautes)} lien(s) interne(s) envoient le lecteur dans une AUTRE langue :\n"
        + "\n".join(sorted(set(fautes))[:20])
        + "\n\nUn lien est une route, pas une chaîne : il se remappe. Rien ne le signale, "
        "puisque la page de destination existe — le lecteur change de langue sans l'avoir "
        "demandé."
    )


def test_le_lien_vers_l_autre_langue_ne_pointe_pas_sur_soi():
    """`altHref` doit sortir de sa langue — sinon il ne mène nulle part de nouveau.

    🔴 Je l'ai cassé moi-même en remappant les liens internes : mon exemption d'`altHref`
    vivait dans le GARDE et pas dans le script de remplacement, et la page « Comprendre »
    anglaise s'est mise à proposer sa propre version anglaise. Rien ne casse — le lien est
    valide, la page existe, elle s'affiche — et le lecteur clique sur « FR » pour rester en
    anglais. Un garde qui exempte un cas doit aussi savoir dire quand ce cas est faux.
    """
    racines = {lg: f"/{lg}/" for lg in _langues_declarees() if lg != "en"}
    fautes: list[str] = []
    for fichier in TABLES_MODULES:
        texte = (CONTENU / fichier).read_text(encoding="utf-8")
        for lg in _langues_declarees():
            try:
                alt = _valeurs(bloc(texte, lg.upper())).get("altHref")
            except AssertionError:
                continue
            if not alt:
                continue
            sienne = racines.get(lg)
            chez_soi = alt.startswith(sienne) if sienne else not any(
                alt.startswith(r) for r in racines.values()
            )
            if chez_soi:
                fautes.append(f"  {fichier} · {lg.upper()} · altHref = {alt}")
    assert not fautes, (
        "des pages proposent « l'autre langue » et renvoient vers la LEUR :\n"
        + "\n".join(fautes)
        + "\n\nLe lien est valide et la page s'affiche : le lecteur clique pour changer de "
        "langue et ne change pas de langue."
    )


def test_le_schema_de_methodologie_admet_chaque_langue_declaree():
    """Le schéma et `langues.ts` doivent dire la MÊME liste de langues.

    🔴 Deux vocabulaires, encore. En posant le néerlandais sur les 61 libellés de la méthode,
    dix-neuf tests ont échoué : le schéma refusait la clé `nl` (`additionalProperties: false`)
    sur une donnée que l'on venait justement de compléter. C'est la même histoire que le
    statut `unknown` du 2026-11-02 — le refus était correct, ce qui manquait était le PONT.

    Seuls `fr` et `en` restent EXIGÉS : une langue en préparation a le droit d'être
    incomplète, c'est `LANGUES_VIVANTES` qui décide de ce qui est servi.
    """
    import json

    schema = json.loads(
        (REPO_ROOT / "data" / "schema" / "methodology.schema.json").read_text(encoding="utf-8")
    )
    admises = set(schema["$defs"]["bilingual_label"]["properties"])
    declarees = set(_langues_declarees())
    manquantes = sorted(declarees - admises)
    assert not manquantes, (
        f"le schéma de méthodologie n'admet pas {manquantes}, que `langues.ts` déclare : "
        f"poser ces libellés ferait REFUSER la méthodologie au gate de corpus, sur une "
        f"donnée pourtant complète"
    )
    intruses = sorted(admises - declarees)
    assert not intruses, (
        f"le schéma admet {intruses} que `langues.ts` ne déclare pas — une langue qui "
        f"n'existe nulle part ailleurs finirait par être servie sans table"
    )


def test_les_notes_de_bas_de_page_suivent_l_identifiant_stable():
    """Une note de source pointe sur l'identifiant du bloc, jamais sur son ancre traduite.

    Même leçon que le découplage, un cran plus bas : le gabarit engendre `id="src-<id>-N"`,
    donc un renvoi écrit `#src-rechten-1` ne mène nulle part — et ne casse rien, puisqu'un
    ancrage absent laisse simplement le lecteur où il est.
    """
    ids = {i for i, _, _ in _blocs_de_comprendre(_langues_declarees()[0])}
    assert ids, "aucun identifiant de bloc relevé — le garde ne garde plus rien"
    fautes: list[str] = []
    for fichier in sorted((CONTENU).rglob("*.ts")):
        for cle in set(re.findall(r"#src-([a-z-]+?)-\d+", fichier.read_text(encoding="utf-8"))):
            if cle not in ids:
                fautes.append(f"  {fichier.name} · #src-{cle}-N")
    assert not fautes, (
        "des renvois de source pointent sur une ancre et non sur un identifiant de bloc :\n"
        + "\n".join(sorted(set(fautes)))
        + f"\n\nIdentifiants valides : {sorted(ids)}. Un renvoi qui ne tombe nulle part ne "
        "casse rien : il laisse le lecteur où il est."
    )


VALEURS_TS = REPO_ROOT / "site" / "src" / "config" / "indicatorValues.ts"


def test_le_bloc_qui_explique_la_note_parle_chaque_langue_servie():
    """« Ce qui pèse le plus ici » doit avoir ses mots dans chaque langue SERVIE.

    C'est la seule phrase de la fiche qui explique la note d'un coup d'œil, en mots
    d'habitant. Faute de mots, la fonction rend `null` et le bloc DISPARAÎT — un silence
    préférable à de l'anglais au milieu d'une page néerlandaise, mais un silence quand même.
    Il est acceptable pendant la rédaction, pas une fois la langue servie : le lecteur aurait
    alors une page entièrement traduite dont manque, sans explication, la phrase qui résume.
    """
    texte = VALEURS_TS.read_text(encoding="utf-8")
    vivantes = set(_langues_vivantes())

    def bloc_de(table: str) -> str:
        m = re.search(rf"(?:export )?const {table}[^=]*= \{{(.*?)\n\}};", texte, re.S)
        assert m, f"{table} introuvable — le garde ne garde plus rien"
        return m.group(1)

    # 🔴 Deux FORMES, et ma première version les a confondues : dans les deux premières
    # tables la langue est une sous-clé (`E1: { fr, en, nl }`), dans `PHRASES` elle EST la
    # clé (`fr: { ici, part }`). Le garde criait donc sur une table parfaitement complète.
    phrases = set(re.findall(r"^  (\w+):\s*\{", bloc_de("PHRASES"), re.M))
    manquantes = sorted(vivantes - phrases)
    assert not manquantes, (
        f"PHRASES n'a pas de motif pour {manquantes} — le bloc se tairait dans une langue "
        f"servie, et le lecteur n'aurait aucun moyen de savoir qu'il manque quelque chose"
    )

    for table in ("FACTEUR_DOMINANT", "GENTILES"):
        entrees = re.findall(r"^  [\"']?[\w\-]+[\"']?:\s*\{(.*?)\},?$", bloc_de(table), re.M | re.S)
        assert entrees, f"{table} : aucune entrée relevée"
        manquantes = {
            lg for e in entrees for lg in vivantes
            if not re.search(rf"\b{lg}:", e)
        }
        assert not manquantes, (
            f"{table} ne porte pas {sorted(manquantes)} sur toutes ses entrées — le bloc "
            f"« ce qui pèse le plus ici » se tairait dans une langue servie, et le lecteur "
            f"n'aurait aucun moyen de savoir qu'il manque quelque chose"
        )


def test_chaque_pays_du_corpus_a_son_nom_dans_chaque_langue_servie():
    """Un pays servi sans nom dans une langue s'affiche en CODE ISO.

    « Deze site ligt in **NL** » — relevé par la relecture native. Le gabarit rend
    `COUNTRY_NAMES[iso]?.[lang] ?? iso` : le repli est le code, et un code se lit comme une
    donnée non traduite, parce que c'en est une.

    Le garde part du CORPUS, pas de la table : c'est l'arrivée d'un pays qui crée le trou,
    et elle arrive par la donnée. Il se tait quand la donnée servie n'est pas là.
    """
    import json

    dossier = REPO_ROOT / "site" / "public" / "data" / "dc"
    if not dossier.is_dir():
        pytest.skip("donnée servie absente de ce checkout — rien à comparer")
    pays = {
        json.loads(f.read_text(encoding="utf-8")).get("country")
        for f in dossier.glob("*.json")
    } - {None}
    assert len(pays) >= 5, f"{len(pays)} pays relevés — le relevé ne cherche plus"

    texte = (REPO_ROOT / "site" / "src" / "config" / "stats.ts").read_text(encoding="utf-8")
    m = re.search(r"(?:const|export const) COUNTRY_NAMES[^=]*= \{(.*?)\n\};", texte, re.S)
    assert m, "COUNTRY_NAMES introuvable"
    noms = {
        cle: set(re.findall(r"\b(\w+):\s*\"", corps))
        for cle, corps in re.findall(r"(\w+):\s*\{([^}]*)\}", m.group(1))
    }
    vivantes = set(_langues_vivantes())
    fautes = sorted(
        f"  {iso} — manque {sorted(vivantes - noms.get(iso, set()))}"
        for iso in pays
        if vivantes - noms.get(iso, set())
    )
    assert not fautes, (
        f"{len(fautes)} pays du corpus n'ont pas leur nom dans toutes les langues servies :\n"
        + "\n".join(fautes)
        + "\n\nIls s'afficheraient en code ISO — ce qui se lit comme une donnée non traduite."
    )


# ─────────────────────────────────────────────────────────────────────────────────────────
# La CINQUIÈME racine de chaînes : `content/procedure/*.ts`, le bloc juridique.
#
# C'est le seul endroit du site qui dise au lecteur quoi FAIRE : qui décide, quelle fenêtre
# est encore ouverte, quel délai ne revient pas. Donc le bloc qui se traduit en PREMIER et
# pas en dernier — un riverain néerlandais qui lit son délai de recours en anglais n'est pas
# armé, il est renvoyé à sa complexité.
#
# Les quatre autres racines sont au harnais (`TABLES_MODULES`, `DETTE_I18N`). Celle-ci ne
# pouvait pas y entrer : ses chaînes ne sont pas des libellés d'interface mais de la prose
# SOURCÉE — chaque phrase porte son article, son lien vers le texte et la date de lecture en
# vigueur. Elle se traduit, elle ne se régénère pas : la version française est la référence,
# et la néerlandaise doit dire la MÊME chose, pas une chose vraisemblable.
#
# `cite` et `url` restent hors périmètre : une référence d'article se cite comme la
# juridiction la cite. Traduire « Algemene wet bestuursrecht, art. 6:7 » serait rendre la
# source introuvable.
#
# DEUX nombres, et ils ne mesurent pas la même chose — les confondre a fait échouer ce test
# dès la première passe de traduction, et c'était la bonne alarme : le TOTAL des champs de
# prose ne bouge que si on ajoute ou retire une affirmation juridique, la DETTE ne bouge
# qu'avec la traduction. Un seul compteur pour les deux aurait laissé une affirmation
# disparaître sans bruit du jour où la dette baissait.
CHAMPS_PROCEDURE = 181  # 19 fichiers, 2026-11-03
# 181 → 93 le 2026-11-03 : première passe de rapports-SMDC, 88 champs posés par
# `scripts/injecter_traduction_procedure.py` (ancrage par rang, nombres vérifiés).
# 93 → 94 le même jour, et le cliquet a eu raison de refuser : la #304 a réécrit l'autorité
# néerlandaise (« instruction communale » était faux pour exactement les gros data centers
# qu'on note — c'est la province, voire le Rijk, qui décide). Le néerlandais posé traduisait
# fidèlement la phrase d'AVANT ; une traduction fidèle d'un texte périmé est un texte périmé.
# Le champ est donc retourné à la dette, et cette hausse est DÉCLARÉE au lieu d'être subie.
# 94 → 0 le 2026-11-03 : passe B de rapports-SMDC. Les 181 affirmations du bloc juridique
# parlent néerlandais. Le cliquet reste — il dira si une affirmation ajoutée part sans sa
# traduction, et c'est précisément le bloc où cela se verrait le moins.
DETTE_NL_PROCEDURE = 0

PROCEDURE = CONTENU / "procedure"

# fr, puis en, puis — quand il existe — nl. L'ordre fait partie de la règle : des champs qui
# se suivent toujours dans le même ordre se relisent en diagonale et se diffent ligne à ligne.
_PROSE = re.compile(
    r'fr:\s*"(?:[^"\\]|\\.)*",\s*en:\s*"(?:[^"\\]|\\.)*",(\s*nl:\s*")?',
    re.S,
)


def _prose_juridique() -> list[tuple[str, int, int]]:
    """Par fichier : (nom, champs de prose, champs qui portent déjà le néerlandais)."""
    releve = []
    for chemin in sorted(PROCEDURE.glob("*.ts")):
        if chemin.name == "types.ts":
            continue  # les déclarations de type ne sont pas des chaînes
        trouves = _PROSE.findall(chemin.read_text(encoding="utf-8"))
        if trouves:
            releve.append((chemin.name, len(trouves), sum(1 for g in trouves if g)))
    return releve


def test_le_releve_du_bloc_juridique_voit_bien_les_champs():
    """Contre-épreuve du relevé lui-même : un compteur qui mesure à côté rassure comme un juste.

    🔴 Déjà vu deux fois : un garde qui comptait `fr: string` (une DÉCLARATION de type) comme
    une chaîne, et un garde qui confondait deux formes de table. Ici on vérifie que le relevé
    retrouve le total attendu ET qu'il ne compte pas les trois interfaces de `types.ts`.
    """
    releve = _prose_juridique()
    total = sum(n for _, n, _ in releve)
    assert total == CHAMPS_PROCEDURE, (
        f"{total} champs de prose relevés dans content/procedure/, le total déclaré est "
        f"{CHAMPS_PROCEDURE}. En plus : de la prose juridique vient d'être ajoutée, elle doit "
        f"partir en traduction avec le reste. En moins : une affirmation juridique a disparu, "
        f"et ça ne se constate pas en passant. Dans les deux cas, corrigez CHAMPS_PROCEDURE "
        f"à {total} EXPRÈS, et la dette avec."
    )
    assert "types.ts" not in {nom for nom, _, _ in releve}
    assert len(releve) >= 19, f"19 fichiers portent de la prose, le relevé en voit {len(releve)}"


def test_la_dette_nl_du_bloc_juridique_ne_peut_que_baisser():
    """Le bloc juridique en néerlandais : ce qui manque est COMPTÉ, pas découvert en servant.

    Tant qu'un champ n'a pas son `nl`, le repli déclaré de `L()` sert l'anglais. Ce n'est pas
    une panne, c'est une dette — mais une dette qu'on voit, dont on connaît le fichier, et qui
    descend à chaque passe. Le test crie aussi quand elle BAISSE : une dette qu'on ne voit pas
    diminuer est une dette qu'on cesse de rembourser.
    """
    releve = _prose_juridique()
    restants = sum(n - fait for _, n, fait in releve)
    assert restants <= DETTE_NL_PROCEDURE, (
        f"{restants} champs du bloc juridique sans néerlandais, la dette déclarée est "
        f"{DETTE_NL_PROCEDURE}"
    )
    if restants < DETTE_NL_PROCEDURE:
        reste = ", ".join(f"{nom} {n - fait}" for nom, n, fait in releve if n > fait) or "aucun"
        pytest.fail(
            f"bonne nouvelle, et le cliquet doit suivre : plus que {restants} champs sans "
            f"néerlandais (déclaré : {DETTE_NL_PROCEDURE}). Abaissez DETTE_NL_PROCEDURE à "
            f"{restants}. Il reste : {reste}."
        )


# ─────────────────────────────────────────────────────────────────────────────────────────
# UN LIEN DE MENU QUI NE MÈNE NULLE PART.
#
# Le menu et le pied de page s'affichent sur les 13 169 pages. Leurs adresses sont écrites à
# la main, par langue, dans `config/nav.ts` et `content/chrome.ts` — et rien ne vérifiait
# qu'une de ces adresses correspond à une page qui EXISTE. Le garde de parité compare la
# FORME des deux menus (mêmes gestes, même nature) ; il ne va jamais voir si le fichier est
# là. Un slug traduit sans sa page est donc un 404 servi partout, et c'est précisément ce
# qu'une langue nouvelle produit : les dix-neuf adresses néerlandaises du menu existent dans
# la table et aucune n'a de page.
#
# La règle suit `langues.ts` : une langue VIVANTE n'a pas droit à un seul lien mort ; une
# langue EN PRÉPARATION a une dette, comptée, qui ne peut que baisser — et qui doit valoir
# zéro le jour où on la fait passer vivante.
CHROME_TS = REPO_ROOT / "site" / "src" / "content" / "chrome.ts"
# Dette de la langue en préparation, 2026-11-03 : les 22 pages néerlandaises que le menu et
# le pied de page promettent et qui n'existent pas. 19 viennent du menu, 3 du pied seul
# (presse, contact, mentions légales) — et c'est le genre d'écart qu'on ne voit qu'en
# relevant les DEUX tables : la nôtre ne promettait pas la même chose aux deux endroits.
# 22 → 7 le 2026-11-03 : quinze pages néerlandaises écrites. Les sept qui restent sont
# celles qui portent leur PROPRE copie de référencement (titre, description) dans la page
# au lieu d'une table — carte, actu, développeurs, la note pas à pas, chiffres, presse,
# qui sommes-nous. Ce n'est pas du harnais : il faut les écrire en néerlandais.
DETTE_PAGES_EN_PREPARATION = 7


def _liens_de_chrome(langue: str) -> list[str]:
    """Les adresses de PAGE du menu et du pied de page d'une langue.

    Les ancres (`/fr/#faq`) sont écartées : elles mènent à une section, pas à un fichier.
    La requête (`?v=2`) l'est aussi — elle s'ajoute à une adresse, elle ne la change pas.
    """
    liens: list[str] = []
    # 🔴 La borne de FIN se déclare par fichier, et c'est tout l'enjeu du relevé : une
    # première version cherchait « le prochain `const XX` » avec un `\b` après les deux
    # lettres — qui ne mord pas devant le souligné de `NL_NAV`. Le bloc français courait
    # donc jusqu'au bout du fichier et avalait les adresses néerlandaises : le garde
    # annonçait 38 liens morts dans une langue EN LIGNE. Un relevé qu'on ne confronte pas à
    # un ordre de grandeur attendu raconte n'importe quoi avec aplomb.
    for fichier, debut, borne in (
        (NAV_TS, f"export const {langue.upper()}_NAV", r"^export const \w+"),
        (CHROME_TS, f"const {langue.upper()}", r"^const [A-Z]{2}\W"),
    ):
        texte = fichier.read_text(encoding="utf-8")
        i = texte.index(debut)
        suite = texte[i + len(debut):]
        prochain = re.search(borne, suite, re.M)
        region = suite[: prochain.start()] if prochain else suite
        lignes = []
        for ligne in region.splitlines():
            c = debut_de_commentaire(ligne)
            lignes.append(ligne if c == -1 else ligne[:c])
        liens += re.findall(r'href:\s*"([^"]*)"', "\n".join(lignes))
    return [h.split("?")[0] for h in liens if "#" not in h]


def _page_absente(href: str) -> bool:
    """Vrai si aucun fichier de `pages/` ne rend cette adresse."""
    chemin = href.strip("/")
    if not chemin:
        return not (PAGES / "index.astro").exists()
    return not (PAGES / f"{chemin}.astro").exists() and not (
        PAGES / chemin / "index.astro"
    ).exists()


def test_le_releve_des_liens_de_navigation_voit_bien_les_deux_fichiers():
    """Contre-épreuve du relevé : un garde qui ne lit rien déclare tout bon.

    Le menu d'une langue vivante porte une vingtaine de liens de page et le pied une
    douzaine. Si le relevé en voyait trois, le test suivant passerait en ne gardant rien.
    """
    for langue in _langues_vivantes():
        liens = _liens_de_chrome(langue)
        assert len(liens) >= 25, (
            f"{len(liens)} liens de page relevés pour « {langue} » : le relevé ne lit plus "
            f"nav.ts ou chrome.ts, et le garde des liens morts ne garde plus rien"
        )
    # et il doit savoir dire qu'une adresse n'existe pas
    assert _page_absente("/nl/une-page-qui-n-existe-pas/")
    assert not _page_absente("/fr/methodologie/")


def test_aucun_lien_de_navigation_ne_mene_au_vide_dans_une_langue_servie():
    """Une langue en ligne n'a pas droit à un seul lien mort dans son menu ou son pied.

    Ces deux éléments sont sur TOUTES les pages : un slug traduit dont la page manque n'est
    pas un petit défaut local, c'est un 404 offert au lecteur depuis les 13 169 pages.
    """
    morts = [
        f"  {langue} → {href}"
        for langue in _langues_vivantes()
        for href in _liens_de_chrome(langue)
        if _page_absente(href)
    ]
    assert not morts, (
        f"{len(morts)} lien(s) de navigation sans page, dans une langue SERVIE :\n"
        + "\n".join(morts)
    )


def test_la_dette_de_pages_de_la_langue_en_preparation_ne_peut_que_baisser():
    """Ce qui manque à la langue en préparation pour pouvoir passer vivante.

    Ce nombre EST la liste des pages à écrire — pas une estimation. Il doit valoir zéro le
    jour où la langue rejoint `LANGUES_VIVANTES`, et le test précédent prend alors le relais.
    """
    vivantes = set(_langues_vivantes())
    attente = [lg for lg in _langues_declarees() if lg not in vivantes]
    morts = sorted({
        f"{lg} → /{href.strip('/')}/"
        for lg in attente
        for href in _liens_de_chrome(lg)
        if _page_absente(href)
    })
    assert len(morts) <= DETTE_PAGES_EN_PREPARATION, (
        f"{len(morts)} adresses de la langue en préparation sans page, la dette déclarée est "
        f"{DETTE_PAGES_EN_PREPARATION} : un slug vient d'être ajouté au menu sans sa page.\n"
        + "\n".join(f"  {m}" for m in morts)
    )
    if len(morts) < DETTE_PAGES_EN_PREPARATION:
        pytest.fail(
            f"bonne nouvelle, et le cliquet doit suivre : plus que {len(morts)} adresse(s) "
            f"sans page (déclaré : {DETTE_PAGES_EN_PREPARATION}). Abaissez "
            f"DETTE_PAGES_EN_PREPARATION à {len(morts)}.\n"
            + "\n".join(f"  {m}" for m in morts)
        )


def test_aucun_lien_de_navigation_ne_perd_sa_barre_finale():
    """Menu et pied de page : chaque adresse interne porte sa barre, sinon c'est un détour.

    🔴 Trouvé en câblant le néerlandais, et vivant depuis des mois : VINGT-ET-UNE adresses
    du pied de page n'avaient pas leur barre finale — dont quatorze dans les deux langues
    EN LIGNE. Vérifié en production avant de le dire : `/map` répond 308 vers `/map/`, et
    `/fr/carte` pareil. Le pied s'affiche sur les 13 169 pages, donc chaque clic sur « Carte »,
    « Classement », « Contact » ou « Mentions légales » payait une redirection.

    La règle est déjà acquise ailleurs (l'incident des liens « autre langue ») ; elle ne
    l'était pas ici, parce que personne n'avait regardé cette table-là.
    """
    fautes = []
    for fichier in (NAV_TS, CHROME_TS):
        for href in re.findall(r'href:\s*"([^"]*)"', fichier.read_text(encoding="utf-8")):
            if href.startswith("/") and "#" not in href and "?" not in href and not href.endswith("/"):
                fautes.append(f"  {fichier.name} → {href}")
    assert not fautes, (
        f"{len(fautes)} adresse(s) de navigation sans barre finale — une redirection par clic, "
        f"sur toutes les pages du site :\n" + "\n".join(fautes)
    )


# ─────────────────────────────────────────────────────────────────────────────────────────
# LA TABLE DE ROUTES — « la même page, dans chaque langue », déclarée une fois.
#
# Elle remplace les 81 `altHref` qui supposaient DEUX langues. Mais une table qui déclare des
# adresses est une troisième liste à côté du menu et du pied de page : si les trois ne disent
# pas la même chose, le sélecteur de langue envoie le lecteur sur une adresse que personne ne
# sert, et le cluster hreflang raconte à Google une correspondance qui n'existe pas.
ROUTES_TS = REPO_ROOT / "site" / "src" / "config" / "routes.ts"


def _familles() -> dict[str, dict[str, str]]:
    """La table de routes, lue à sa source : id → {langue: chemin}."""
    texte = ROUTES_TS.read_text(encoding="utf-8")
    debut = texte.index("export const FAMILLES")
    fin = texte.index("\nconst SEGMENTS", debut)
    region = texte[debut:fin]
    lignes = []
    for ligne in region.splitlines():
        c = debut_de_commentaire(ligne)
        lignes.append(ligne if c == -1 else ligne[:c])
    region = "\n".join(lignes)

    table: dict[str, dict[str, str]] = {}
    morceaux = re.split(r'\bid:\s*"', region)[1:]
    for morceau in morceaux:
        ident, reste = morceau.split('"', 1)
        chemins = dict(re.findall(r'\b(en|fr|nl):\s*"([^"]*)"', reste.split("{ id:")[0]))
        table[ident] = chemins
    return table


def test_le_releve_de_la_table_de_routes_voit_bien_les_familles():
    """Contre-épreuve : une table lue de travers déclarerait tout cohérent."""
    familles = _familles()
    assert len(familles) >= 30, f"{len(familles)} familles relevées — le relevé ne lit plus routes.ts"
    assert familles["fiche"] == {
        "en": "/dc/:id/", "fr": "/fr/dc/:id/", "nl": "/nl/dc/:id/"
    }, familles.get("fiche")
    # une famille volontairement à deux langues doit sortir SANS néerlandais
    assert "nl" not in familles["rapport-france"], familles["rapport-france"]


def test_la_table_de_routes_et_le_menu_disent_la_meme_chose():
    """Toute adresse promise par le menu ou le pied doit être une adresse de la table.

    Sinon le sélecteur de langue et la navigation ne parlent pas du même site : on peut
    arriver sur une page par le menu et n'avoir aucun moyen d'en changer la langue, ou se
    faire proposer une langue vers une adresse que rien ne sert.
    """
    familles = _familles()
    for langue in _langues_declarees():
        connus = {c for f in familles.values() if (c := f.get(langue))}
        # Mêmes exemptions que la couverture : les pages de chiffres portent leur paire
        # page par page, parce que leur périmètre par défaut dépend de la langue.
        EXEMPTES = {"/figures/", "/fr/chiffres/", "/nl/kerncijfers/"}
        absents = sorted({
            f"/{href.strip('/')}/" for href in _liens_de_chrome(langue)
            if f"/{href.strip('/')}/" not in connus and f"/{href.strip('/')}/" not in EXEMPTES
        })
        assert not absents, (
            f"{len(absents)} adresse(s) du menu ou du pied « {langue} » ne sont pas dans la "
            f"table de routes — elles n'auront pas de sélecteur de langue :\n"
            + "\n".join(f"  {a}" for a in absents)
        )


def test_la_table_de_routes_couvre_toute_page_servie():
    """Une page qui n'est dans aucune famille n'a pas de sélecteur de langue.

    Le relevé part des FICHIERS, pas de la table : c'est la seule direction qui trouve une
    page oubliée. Partir de la table ne dirait que ce que la table sait déjà.
    """
    familles = _familles()
    tous = {c for f in familles.values() for c in f.values()}
    # Un fichier de page devient une adresse : `fr/carte.astro` → `/fr/carte/`, un segment
    # dynamique `[id]` → `:id`. La préviz, les générateurs d'images et la 404 n'en sont pas.
    # Exemptions DÉCLARÉES, avec leur raison — une exemption muette est un trou.
    # Les pages de chiffres ne se mettent pas en table : leur périmètre par défaut dépend
    # de la langue (France en français, Europe en anglais), donc la même adresse n'y porte
    # pas le même contenu. Elles gardent la paire déclarée page par page.
    HORS_TABLE = {
        "figures/index.astro", "figures/[perimeter].astro",
        "fr/chiffres/index.astro", "fr/chiffres/[perimetre].astro",
    }
    orphelines = []
    for chemin in sorted(PAGES.rglob("*.astro")):
        rel = chemin.relative_to(PAGES).as_posix()
        if rel.startswith(("previz/", "og/")) or rel == "404.astro" or rel in HORS_TABLE:
            continue
        adresse = "/" + re.sub(r"\[\.{3}?(\w+)\]", ":id", rel.removesuffix(".astro")).replace(
            "/index", ""
        ).removesuffix("index") + "/"
        adresse = re.sub(r"/{2,}", "/", adresse.replace("[id]", ":id").replace("[perimetre]", ":id")
                         .replace("[perimeter]", ":id"))
        if adresse not in tous:
            orphelines.append(f"  {rel} → {adresse}")
    assert not orphelines, (
        f"{len(orphelines)} page(s) hors de la table de routes — aucun sélecteur de langue "
        f"ne pourra les relier à leurs sœurs :\n" + "\n".join(orphelines)
    )


def test_chaque_bloc_de_langue_porte_le_menu_de_SA_langue():
    """Une table de contenu qui porte un `nav:` doit porter CELUI de sa langue.

    🔴 Trouvé en confrontant le HTML servi, pas en relisant le code : l'accueil néerlandais
    et « Datacenters begrijpen » affichaient le MENU FRANÇAIS — tous les liens vers /fr/ —
    parce que leurs blocs `nl` déclaraient `nav: FR_NAV`. Ni la relecture native (qui lit
    des mots, pas du câblage) ni la parité de clés (la clé `nav` était bien là) ni la préviz
    (même nombre de blocs) ne pouvaient le voir.

    Le menu vit à deux endroits : `config/nav.ts` et le `nav:` de chaque bloc de langue.
    Tant qu'il en est ainsi, c'est ce test qui tient le lien.
    """
    fautes = []
    for nom in ("accueil.ts", "comprendre.ts", "fiche.ts", "portrait.ts"):
        chemin = CONTENU / nom
        if not chemin.is_file():
            continue
        texte = chemin.read_text(encoding="utf-8")
        for langue in _langues_declarees():
            # le bloc de cette langue : de sa déclaration à la suivante
            m = re.search(rf"^(?:export )?const [A-Z_]*{langue.upper()}\b.*?= \{{", texte, re.M | re.S)
            if not m:
                continue
            suite = texte[m.end():]
            fin = re.search(r"^(?:export )?const [A-Z]", suite, re.M)
            region = suite[: fin.start()] if fin else suite
            for trouve in re.findall(r"nav:\s*(\w+)", region):
                if trouve != f"{langue.upper()}_NAV":
                    fautes.append(
                        f"  {nom}, bloc {langue} → nav: {trouve} (attendu {langue.upper()}_NAV)"
                    )
    assert not fautes, (
        "une table de contenu sert le menu d'une AUTRE langue — donc des liens qui sortent "
        "le lecteur de sa langue à chaque clic :\n" + "\n".join(fautes)
    )


# La table de routes est une PROMESSE faite au sélecteur de langue : « cette page existe
# aussi en néerlandais ». Le test précédent va des fichiers vers la table (trouver une page
# oubliée) ; celui-ci va de la table vers les fichiers — et c'est le sens qui trouve une
# promesse en trop. En préviz, le sélecteur propose déjà le néerlandais : une colonne qui
# désigne une page inexistante y envoie le relecteur sur un 404.
#
# Sept chemins néerlandais déclarés sans page, 2026-11-03 : la carte, l'actu, les chiffres
# du parc, les développeurs et leur clé, la presse, qui-sommes-nous, la note pas à pas. Ce
# sont les pages dont le GABARIT ne parle que deux langues — leur colonne reste dans la
# table parce qu'elle dit où la page ira, et le compte dit qu'elle n'y est pas encore.
DETTE_ROUTES_EN_PREPARATION = 7


def _routes_sans_page(langue: str) -> list[str]:
    return sorted(
        f"{ident} → {chemin}"
        for ident, chemins in _familles().items()
        if (chemin := chemins.get(langue)) and ":id" not in chemin and _page_absente(chemin)
    )


def test_la_table_de_routes_ne_promet_aucune_page_absente_dans_une_langue_servie():
    """Une langue en ligne : chaque colonne de la table désigne une page qui existe.

    Sinon le sélecteur de langue envoie le lecteur sur un 404 — et c'est le pire endroit
    pour un lien mort, parce qu'il est en haut de toutes les pages du site.
    """
    for langue in _langues_vivantes():
        absentes = _routes_sans_page(langue)
        assert not absentes, (
            f"{len(absentes)} chemin(s) déclaré(s) dans config/routes.ts pour « {langue} » "
            f"sans page correspondante :\n" + "\n".join(f"  {a}" for a in absentes)
        )


def test_la_dette_de_routes_de_la_langue_en_preparation_ne_peut_que_baisser():
    """Les colonnes néerlandaises qui désignent une page pas encore écrite.

    Distinct de la dette du MENU : le menu promet au visiteur, la table promet au sélecteur
    de langue. Les deux listes ne se recouvrent pas tout à fait — la clé d'API, par exemple,
    n'est dans aucun menu et a bien une colonne néerlandaise.
    """
    vivantes = set(_langues_vivantes())
    absentes = [
        a for lg in _langues_declarees() if lg not in vivantes for a in _routes_sans_page(lg)
    ]
    assert len(absentes) <= DETTE_ROUTES_EN_PREPARATION, (
        f"{len(absentes)} colonne(s) de la table désignent une page absente, la dette "
        f"déclarée est {DETTE_ROUTES_EN_PREPARATION} : une colonne vient d'être ajoutée "
        f"sans sa page.\n" + "\n".join(f"  {a}" for a in absentes)
    )
    if len(absentes) < DETTE_ROUTES_EN_PREPARATION:
        pytest.fail(
            f"bonne nouvelle, et le cliquet doit suivre : plus que {len(absentes)} "
            f"colonne(s) sans page (déclaré : {DETTE_ROUTES_EN_PREPARATION}). Abaissez "
            f"DETTE_ROUTES_EN_PREPARATION à {len(absentes)}."
        )


# ---------------------------------------------------------------------------
# Les barrières d'après-build existent-elles, et sont-elles lancées ?
# ---------------------------------------------------------------------------

MAKEFILE = REPO_ROOT / "Makefile"


def _cibles() -> dict[str, tuple[list[str], str]]:
    """Le Makefile en {cible: (prérequis, recette)} — lecture plate, pas d'évaluation."""
    cibles: dict[str, tuple[list[str], str]] = {}
    nom, prereqs, recette = None, [], []
    for ligne in MAKEFILE.read_text(encoding="utf-8").splitlines():
        if ligne.startswith("\t"):
            recette.append(ligne)
            continue
        m = re.match(r"^([a-z][\w.-]*):(?!=)(.*)$", ligne)
        if m:
            if nom:
                cibles[nom] = (prereqs, "\n".join(recette))
            nom, prereqs, recette = m.group(1), m.group(2).split(), []
    if nom:
        cibles[nom] = (prereqs, "\n".join(recette))
    return cibles


def _cible_deploy() -> str:
    """La recette de `deploy`, SEULE — ce qui est lancé après le build est ici."""
    return _cibles()["deploy"][1]


def _recettes_atteintes_par_deploy() -> str:
    """🔴 LA FERMETURE, pas la seule cible. `check_headers.py` n'est pas dans le corps de
    `deploy` : il est lancé par `headers-check`, prérequis de `test`, que `deploy` appelle.
    Un relevé qui ne regarde que `deploy` l'aurait déclaré « jamais lancé » — un garde qui
    mesure à côté, exactement ce qu'on corrige ici. On suit donc les prérequis ET les
    `$(MAKE) x`, de proche en proche.
    """
    cibles = _cibles()
    vues, pile, morceaux = set(), ["deploy"], []
    while pile:
        nom = pile.pop()
        if nom in vues or nom not in cibles:
            continue
        vues.add(nom)
        prereqs, recette = cibles[nom]
        morceaux.append(recette)
        pile += prereqs + re.findall(r"\$\(MAKE\)\s+([a-z][\w.-]*)", recette)
    return "\n".join(morceaux)


def test_toute_barriere_dapres_build_est_lancee_par_deploy():
    """Un contrôle qui vit dans `scripts/check_*` et que `deploy` n'appelle pas ne garde rien.

    🔴 CE TEST NAÎT D'UN DÉPLACEMENT. Le garde de la donnée servie était une épreuve de
    cette suite ; il lisait un fichier qu'`make build` écrit, et la suite tourne AVANT le
    build. Il est donc parti en barrière d'après-build. Déplacer des dents d'un test vers une
    ligne de Makefile, c'est les rendre supprimables sans que rien ne crie — à moins qu'un
    test ne tienne la ligne. Il la tient.

    La règle est dans un sens seulement : une barrière DOIT être appelée. On ne demande pas
    l'inverse (`deploy` appelle aussi des scripts qui ne s'appellent pas `check_*`).
    """
    barrieres = sorted(p.name for p in (REPO_ROOT / "scripts").glob("check_*.py"))
    assert barrieres, "plus aucun script scripts/check_*.py — le relevé cherche à côté"
    atteintes = _recettes_atteintes_par_deploy()
    absentes = [n for n in barrieres if n not in atteintes]
    assert not absentes, (
        f"{len(absentes)} barrière(s) existent dans scripts/ mais `make deploy` ne les "
        f"lance pas : {absentes}. Un contrôle qu'on n'appelle pas rassure sans garder — "
        f"soit on le câble dans la cible deploy, soit on le supprime."
    )


def test_la_barriere_de_la_donnee_servie_est_bien_apres_le_build():
    """L'ORDRE porte la règle : cette barrière ne peut pas être vérifiée avant `make build`.

    Elle lit `site/public/data/`, que le build écrit. Placée avant, elle jugerait l'artefact
    du déploiement PRÉCÉDENT — c'est la faute exacte qu'on vient de corriger, réintroduite à
    l'envers.
    """
    corps = _cible_deploy()
    i_build = corps.find("$(MAKE) build")
    i_barriere = corps.find("check_langue_donnee_servie.py")
    assert i_build >= 0, "`deploy` n'appelle plus `make build` — l'ordre n'a plus de sens"
    assert i_barriere > i_build, (
        "check_langue_donnee_servie.py est lancé AVANT `make build` : il jugerait "
        "l'artefact du déploiement précédent, pas celui qui part."
    )


def test_le_garde_des_barrieres_mord_vraiment(monkeypatch, tmp_path):
    """Contre-épreuve : on décâble une barrière du Makefile, le garde doit refuser.

    Sans ça, le garde passerait au vert parce qu'il ne trouve rien à relever — pas parce que
    tout est câblé.
    """
    faux = tmp_path / "Makefile"
    faux.write_text(
        MAKEFILE.read_text(encoding="utf-8").replace(
            "\tuv run python scripts/check_langue_donnee_servie.py\n", ""
        ),
        encoding="utf-8",
    )
    monkeypatch.setitem(globals(), "MAKEFILE", faux)
    with pytest.raises(AssertionError, match="check_langue_donnee_servie.py"):
        test_toute_barriere_dapres_build_est_lancee_par_deploy()


def test_le_garde_de_lordre_mord_vraiment(monkeypatch, tmp_path):
    """Contre-épreuve : on remonte la barrière AVANT le build, le garde doit refuser."""
    corps = MAKEFILE.read_text(encoding="utf-8")
    ligne = "\tuv run python scripts/check_langue_donnee_servie.py\n"
    faux = tmp_path / "Makefile"
    faux.write_text(
        corps.replace(ligne, "").replace("\t$(MAKE) build\n", ligne + "\t$(MAKE) build\n"),
        encoding="utf-8",
    )
    monkeypatch.setitem(globals(), "MAKEFILE", faux)
    with pytest.raises(AssertionError, match="AVANT `make build`"):
        test_la_barriere_de_la_donnee_servie_est_bien_apres_le_build()


# ══════════════════════════════════════════════════════════════════════════════════════════
# UN REPLI DE LANGUE EST UNE RÈGLE, PAS UN TERNAIRE QU'ON RECOPIE
# ══════════════════════════════════════════════════════════════════════════════════════════
# 🔴 CE QUE CE GARDE A TROUVÉ EN NAISSANT. Cinq composants portaient chacun leur version du
# repli d'un champ par langue, et tous les cinq terminaient sur le FRANÇAIS :
# `obj?.[lang] ?? obj?.fr ?? ""`. Avec deux langues la seconde branche n'est JAMAIS prise
# (`lang` vaut `fr` ou `en`, les deux clés existent) : du code mort depuis le premier jour,
# qui s'exécute pour la première fois le jour d'une troisième langue — et qui sert alors du
# français à un lecteur néerlandais, sans erreur et sans blanc.
#
# Mesuré le même jour : 3 292 fiches servies, 0 avec `synthesis.nl`. Le périmètre de
# traduction européen avait été décidé sur un « repli anglais » qui n'existait pas.
#
# Le repli est donc DÉCLARÉ une fois (`donnee()` / `copie()` dans `content/langues.ts`) et
# les composants le consomment. Ce garde interdit de le re-déclarer : un sixième ternaire
# serait muet comme les cinq premiers [[liste-a-deux-endroits-ment]].
#
# ⚠️ CE QUE CE GARDE NE DIT PAS, et il ne doit pas prétendre le dire. Il ne voit que le repli
# qui termine sur une langue EN DUR. Un accès par langue qui replie sur `""` (un libellé qui
# devient muet) ou qui ne replie PAS du tout (`undefined` rendu) casse aussi sur une langue
# neuve — autrement, et ça ne se répare pas par un ordre de secours mais par la colonne de la
# langue. Un garde qui dépasserait son mandat ici rassurerait sur deux familles qu'il ne
# regarde pas [[gate-qui-depasse-son-mandat]].
_REPLI_DE_LANGUE = re.compile(
    r"\[(?:lang|langue|W\.lang)\]"                  # un accès indexé par la langue…
    r"[^;\n]*?(?:\?\?|\|\|)\s*[^;\n]*?"            # …suivi d'un repli…
    r"(?:\.(?:fr|en|nl)\b|\[\"(?:fr|en|nl)\"\])"   # …dont la cible est une langue EN DUR
)
# La source du repli, seul fichier où la règle a le droit de s'écrire.
SOURCE_DU_REPLI = "content/langues.ts"


def test_aucun_composant_ne_redeclare_son_repli_de_langue():
    """Le repli d'un champ par langue s'écrit à UN endroit, et nulle part ailleurs.

    Recopié, il dérive : les cinq copies trouvées le 2026-11-04 terminaient toutes sur le
    français alors que les deux replis justes du site (`copie()`, le portrait) terminaient sur
    l'anglais. La maison était coupée en deux, et c'est exactement pour ça que personne ne
    l'avait vu — chaque composant avait l'air cohérent avec lui-même.
    """
    fautes = []
    for p in _sources_site():
        rel = str(p.relative_to(SRC_SITE))
        if rel == SOURCE_DU_REPLI:
            continue
        for n, ligne in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            m = _REPLI_DE_LANGUE.search(ligne)
            if not m:
                continue
            c = debut_de_commentaire(ligne)
            if c != -1 and c < m.start():
                continue  # un commentaire qui PARLE du motif n'est pas le motif
            fautes.append(f"  {rel}:{n}  {ligne.strip()[:110]}")

    assert not fautes, (
        f"{len(fautes)} repli(s) de langue re-déclarés hors de {SOURCE_DU_REPLI} :\n"
        + "\n".join(fautes)
        + f"\n\nUn repli par langue est une RÈGLE, pas une commodité de gabarit. Elle vit dans "
        f"`{SOURCE_DU_REPLI}` : `donnee(objet, lang)` pour un champ de DONNÉE (chaîne "
        f"langue → en → fr), `copie(table, lang)` pour la copie d'un composant. Recopiée ici, "
        f"elle dérive — et sa dérive est muette, parce qu'avec deux langues la branche de "
        f"repli ne s'exécute jamais."
    )


def test_le_garde_du_repli_mord_vraiment(tmp_path, monkeypatch):
    """Contre-épreuve : le motif exact qui a été réparé doit être refusé.

    Sans elle, ce garde peut cesser de voir (un `[lang]` écrit autrement, une ligne découpée)
    et rester vert — un instrument qui mesure à côté rassure comme un juste.
    """
    faux = tmp_path / "components"
    faux.mkdir()
    (faux / "Fautif.astro").write_text(
        'const L = (obj: any) => obj?.[lang] ?? obj?.fr ?? "";\n', encoding="utf-8"
    )
    # Et la variante de l'île de carte, qui n'a ni `?.` ni le même nom de variable.
    (faux / "Ile.astro").write_text(
        'const l = (f: any) => (f.label || {})[W.lang] ?? (f.label || {}).fr ?? "";\n',
        encoding="utf-8",
    )
    monkeypatch.setitem(globals(), "SRC_SITE", tmp_path)
    monkeypatch.setitem(
        globals(), "_sources_site", lambda: sorted(tmp_path.rglob("*.astro"))
    )
    with pytest.raises(AssertionError) as e:
        test_aucun_composant_ne_redeclare_son_repli_de_langue()
    assert "Fautif.astro" in str(e.value) and "Ile.astro" in str(e.value)
