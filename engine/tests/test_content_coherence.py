# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Copy <-> product coherence gate (methodology-lead request, 2026-07-06).

Three consecutive review loops caught the same defect class: site copy
asserting numbers the engine does not display (close_to ranges, one-decimal
claims, notice periods). This test makes the tripwire mechanical: every
quantitative claim on the landing pages must match the methodology and the
engine constants. Change a parameter -> the build breaks until the copy is
updated (and vice versa)."""

import json
import re
from pathlib import Path

import pytest

from engine.core import REPO_ROOT, load_methodology

PAGES = {
    "en": (REPO_ROOT / "site" / "src" / "pages" / "index.astro").read_text(),
    "fr": (REPO_ROOT / "site" / "src" / "pages" / "fr" / "index.astro").read_text(),
}


@pytest.fixture(scope="module")
def methodology():
    return load_methodology()


def test_indicator_count_claims_match_methodology(methodology):
    # LE CHIFFRE ANNONCÉ EST CELUI DE LA NOTE, PAS DU CATALOGUE. Les deux pages disent « deux
    # notes A–E … À PARTIR DE N indicateurs » : un indicateur informationnel (weight_in_pillar 0,
    # publié comme fait, jamais noté) n'en fait donc pas partie, et le compter aurait annoncé que
    # F6/F7 alimentent la note — exactement ce que leur doctrine interdit (2026-10-06, méthodo
    # v0.3.0). Compter le catalogue brut rendait ce test faux dans le sens le plus coûteux : il
    # aurait fait corriger la copie VRAIE pour la rendre fausse.
    real = sum(1 for i in methodology["indicators"] if not i.get("informational"))
    for lang, text in PAGES.items():
        for claimed in re.findall(r"(\d+)\s+indicat(?:or|eur)s", text):
            assert int(claimed) == real, (
                f"{lang} copy claims {claimed} indicators, methodology defines {real}"
            )


def test_pillar_count_claims_match_methodology(methodology):
    real = len(methodology["pillars"])
    claims = {
        "en": re.findall(r"(\d+)\s+pillars", PAGES["en"]),
        "fr": re.findall(r"(\d+)\s+piliers", PAGES["fr"]) + (["5"] if "cinq piliers" in PAGES["fr"] else []),
    }
    for lang, found in claims.items():
        assert found, f"{lang} copy no longer states the pillar count — intentional?"
        for claimed in found:
            assert int(claimed) == real, f"{lang} copy claims {claimed} pillars, methodology defines {real}"


def test_coverage_threshold_claims_match_parameters(methodology):
    real_pct = round(methodology["parameters"]["min_coverage"] * 100)
    for lang, text in PAGES.items():
        for claimed in re.findall(r"(\d+)\s?%\s(?:de couverture|coverage)", text):
            assert int(claimed) == real_pct, (
                f"{lang} copy claims a {claimed}% coverage floor, parameters say {real_pct}%"
            )


# --- Firewall (brief 2026-07-06 §1) + forbidden phrases (brief 2026-07-15 §4.I.2) ---
# The "we help the project, never the grade" firewall stays stated where it does
# legal/positioning work. The OLD prior-notice mechanism (grade-triggered right of
# reply, >=15-day hold) was retired on the 2026-07-15 legal review: its phrases are
# BANNED from every living surface so it can never crawl back through an old
# template or a copy-paste.
_SITE = REPO_ROOT / "site" / "src" / "pages"
FIREWALL_SOURCES = {
    "landing-fr": PAGES["fr"],
    "mentions-legales": (_SITE / "fr" / "mentions-legales.astro").read_text(),
    "methodologie": (_SITE / "fr" / "methodologie.astro").read_text(),
    "readme": (REPO_ROOT / "README.md").read_text(),
}


def test_firewall_line_present_where_required():
    for name, text in FIREWALL_SOURCES.items():
        low = text.lower()
        assert "jamais la note" in low or "never the grade" in low, (
            f"{name} no longer carries the firewall ('on aide le projet, jamais la note')"
        )


# Every phrase of the retired mechanism, FR + EN (case-insensitive, singular/plural,
# NBSP-tolerant). A hit anywhere on a living surface breaks the build.
FORBIDDEN_PHRASES = [
    r"droits?\s+de\s+réponse\s+préalables?",
    r"prior\s+rights?\s+of\s+reply",
    r"au\s+moins\s+(15|quinze)\s+jours",
    r"at\s+least\s+(15|fifteen)\s+days",
    r"[≥>]=?\s*15\s*j\b",
    r"contradictoires?\s+déclenchés?\s+par\s+la\s+note",
    r"grade-triggered",
    r"droit\s+de\s+réponse\s+en\s+cours",
    r"right\s+of\s+reply\s+in\s+progress",
    r"deux\s+droits\s+sur\s+chaque\s+fiche",
    r"two\s+rights\s+on\s+every\s+(fiche|datasheet)",
    r"sollicité,?\s+sans\s+réponse",
    r"solicited,?\s+no\s+(reply|response)",
    r"l'opérateur\s+dispose\s+d'un\s+droit\s+de\s+réponse",
    # the pre-review draft banner must never ship again (seen LIVE 2026-07-16)
    r"ne\s+pas\s+publier\s+en\s+l'état",
    r"do\s+not\s+publish\s+as-is",
    r"version\s+de\s+travail\s+—",
]

# B-1 généralisé (Franck 2026-07-27) : jamais de dépendance STRUCTURELLE à UNE SOURCE,
# quelle qu'elle soit. On écrit « contient des informations de », jamais « basé sur /
# issu de / construit à partir de / grâce à <source> » (idem EN). Ciblé sur un NOM DE
# SOURCE pour ne pas casser les usages légitimes (« basé sur une méthode ouverte »).
_SOURCE_NAMES = (
    r"(?:dcwatch|hubblo|openstreetmap|\bosm\b|datacentertracker|eurostat|g[ée]orisques"
    r"|vigieau|propluvia|bnpe|hub'?eau|insee|inpn|cerema|\brte\b|esri|gdelt)"
)
FORBIDDEN_PHRASES += [
    rf"bas[ée]s?\s+sur.{{0,30}}{_SOURCE_NAMES}",
    rf"construit.{{0,30}}{_SOURCE_NAMES}",
    rf"issus?\s+de.{{0,20}}{_SOURCE_NAMES}",
    rf"gr[âa]ce\s+à.{{0,30}}{_SOURCE_NAMES}",
    rf"based\s+on.{{0,30}}{_SOURCE_NAMES}",
    rf"built\s+(?:from|on).{{0,30}}{_SOURCE_NAMES}",
    rf"derived\s+from.{{0,30}}{_SOURCE_NAMES}",
]

# D-1 (avis cabinet Batch D, 2026-07-27) : Sahara occidental — terminologie ONU
# EXCLUSIVE (« territoire non autonome »). Ces expressions traduisent une position
# politique et sont bannies de TOUTE surface (l'observatoire ne qualifie pas le territoire).
FORBIDDEN_PHRASES += [
    r"territoires?\s+marocains?",
    r"territoires?\s+occup[ée]s?",
    r"territoires?\s+lib[ée]r[ée]s?",
    r"provinces?\s+du\s+sud",
    r"sahara\s+marocain",
    r"moroccan\s+(?:territory|sahara)",
    r"occupied\s+territor(?:y|ies)",
    r"liberated\s+territor(?:y|ies)",
    r"southern\s+provinces",
]


def _living_surfaces():
    """Every user-facing source: site pages/components/content + README + docs."""
    roots = [REPO_ROOT / "site" / "src", REPO_ROOT / "docs"]
    files = [p for r in roots for p in r.rglob("*") if p.suffix in (".astro", ".ts", ".md")]
    files.append(REPO_ROOT / "README.md")
    return files


def test_forbidden_phrases_never_reappear():
    hits = []
    for path in _living_surfaces():
        text = path.read_text().replace("\u00a0", " ").lower()
        for pattern in FORBIDDEN_PHRASES:
            if re.search(pattern, text):
                hits.append(f"{path.relative_to(REPO_ROOT)}: {pattern!r}")
    assert not hits, (
        "forbidden phrase(s) of the retired prior-notice mechanism resurfaced "
        "(legal review 2026-07-15 — grades publish directly):\n" + "\n".join(hits)
    )


def test_forbidden_phrases_lint_actually_bites(tmp_path):
    # negative test: reintroduce one banned formula in a fake template -> the lint must flag it
    fake = tmp_path / "old-template.astro"
    fake.write_text("<p>Une note D ouvre un droit de réponse préalable d'au moins 15 jours.</p>")
    text = fake.read_text().lower()
    assert any(re.search(pat, text) for pat in FORBIDDEN_PHRASES), (
        "the forbidden-phrases lint no longer catches the canonical banned sentence"
    )


# --- Gate 7 (prose): a grade letter is never rendered outside <ScoreBadge> --------
# Seen live (2026-07-10): an LLM-written accroche pinned at "site C, piliers D"
# rendered next to recomputed badges saying D and E after a recalibration. Prose
# citing a letter duplicates computed state and WILL drift; the badge carries the
# letter, the prose carries the why.

from engine.artifacts import build_artifacts, synthesis_grade_citations
from engine.core import GateError, load_datacenters


def _stale_dc():
    return {
        "id": "zz-stale",
        "synthesis": {"site": {
            "fr": "La note de site C reflète cet équilibre (piliers Énergie D et Foncier D).",
            "en": "These signals place the site at grade C.",
        }},
    }


def test_synthesis_prose_citing_letters_is_detected():
    hits = synthesis_grade_citations(_stale_dc())
    assert len(hits) >= 3  # note de site C, piliers ... D, at grade C


def test_letter_free_prose_passes():
    clean = {"id": "zz-clean", "synthesis": {"site": {
        "fr": "La note de site reflète cet équilibre : mesures ERC engagées, PUE 1,2 annoncé. À noter.",
        "en": "The site grade reflects the constraint; the Energy pillar stays low. E-fuels and ERC measures.",
    }}}
    assert synthesis_grade_citations(clean) == []


def test_build_refuses_grade_letters_in_prose(methodology, tmp_path, alpha):
    stale = dict(alpha, **{"synthesis": _stale_dc()["synthesis"]})
    with pytest.raises(GateError, match="GATE 7 \\(prose\\)"):
        build_artifacts({stale["id"]: stale}, methodology, out_dir=tmp_path, watchlist=[])


def test_committed_corpus_prose_is_letter_free():
    for dc in load_datacenters().values():
        assert synthesis_grade_citations(dc) == []

# --- Ranking register (brief 2026-07-12 · A-27): we situate, we never judge ------
# The percentile-context voice is the ONLY allowed voice on the ranking. Judgment
# words ("pire", "cancre", "mur de la honte", "flop"…) are banned from its copy.
RANKING_SOURCES = {
    "classement-fr": (REPO_ROOT / "site" / "src" / "pages" / "fr" / "classement.astro").read_text(),
    "ranking-en": (REPO_ROOT / "site" / "src" / "pages" / "ranking.astro").read_text(),
    "ranking-component": (REPO_ROOT / "site" / "src" / "components" / "Ranking.astro").read_text(),
}
JUDGMENT_WORDS = [r"\bpires?\b", r"\bcancres?\b", r"\bhonte\b", r"\bflops?\b",
                  r"\bworst\b", r"\bshame\b", r"\blosers?\b"]


def test_ranking_copy_situates_never_judges():
    for name, text in RANKING_SOURCES.items():
        low = text.lower()
        for pattern in JUDGMENT_WORDS:
            assert re.search(pattern, low) is None, (
                f"{name} uses the judgment word {pattern!r} — the ranking situates in the "
                "distribution (percentile-context register), it never judges (A-27)"
            )


def test_ranking_states_its_denominator_and_version():
    for name in ("classement-fr", "ranking-en"):
        text = RANKING_SOURCES[name]
        assert "{n}" in text and "{version}" in text, (
            f"{name} no longer states the percentile reference (N projects + methodology "
            "version) — a percentile without its denominator is a naked judgment (A-27)"
        )


FICHE_PAGES = {
    "en": REPO_ROOT / "site" / "src" / "pages" / "dc" / "[id].astro",
    "fr": REPO_ROOT / "site" / "src" / "pages" / "fr" / "dc" / "[id].astro",
}
# Tout statut qu'un indicateur peut porter dans un artefact servi. Le corpus du 2026-10-20 en
# produit cinq ; la liste est ici pour que l'ajout d'un sixième casse le build au lieu de
# passer en silence.
STATUTS_SERVIS = ("measured", "announced", "estimated", "missing", "not_collected")


@pytest.mark.parametrize("lang", sorted(FICHE_PAGES))
def test_chaque_statut_servi_a_un_libelle_sur_la_fiche(lang):
    """UN ÉTAT SANS LIBELLÉ S'AFFICHE COMME UNE CASE VIDE, ET UNE CASE VIDE NE DIT RIEN.

    `indStatus` ne nommait que trois statuts sur cinq. `not_collected` — 48 135 lignes du
    corpus, la majorité du tableau — rendait une cellule d'état VIDE, indistinguable d'un
    oubli de mise en page. Or c'est précisément la distinction qui compte pour le lecteur :
    « absent du dossier » est un fait constaté qui pèse comme un zéro dans la note, « pas
    encore cherché » est notre lacune et ne pénalise personne.
    """
    texte = FICHE_PAGES[lang].read_text()
    bloc = texte.split("indStatus:", 1)[1].split("},", 1)[0]
    for statut in STATUTS_SERVIS:
        assert f"{statut}:" in bloc, f"[{lang}] le statut « {statut} » n'a pas de libellé"


@pytest.mark.parametrize("lang", sorted(FICHE_PAGES))
def test_l_enumeration_de_l_etat_des_donnees_boucle(lang):
    """Une énumération qui ne fait pas son total ment par omission.

    La phrase annonçait « 26 indicateurs suivis » puis en détaillait 11 : les quinze que nous
    n'avons pas cherchés — la plus grosse part de notre ignorance — étaient les seuls à ne pas
    être dits. Les estimations manquaient aussi.
    """
    texte = FICHE_PAGES[lang].read_text()
    phrase = [l for l in texte.splitlines() if l.strip().startswith("dataState:")][0]
    for champ in ("{n}", "{measured}", "{announced}", "{missing}", "{notCollected}"):
        assert champ in phrase, f"[{lang}] {champ} absent de la phrase d'état des données"


BLOCS = REPO_ROOT / "site" / "src" / "content" / "understand-blocks.ts"


def _moities() -> tuple[str, str]:
    """Le fichier déclare RICH_FR puis RICH_EN : on compare les deux moitiés.

    On part de RICH_FR et non du début : la déclaration de type qui précède contient elle
    aussi `lead:`, `label:` et `q:`, et les compter faisait échouer le test sur un écart de
    un — côté français, puisque le type est de ce côté-là de la coupure.
    """
    texte = BLOCS.read_text()
    debut = texte.index("export const RICH_FR")
    i = texte.index("export const RICH_EN")
    return texte[debut:i], texte[i:]


@pytest.mark.parametrize("marqueur,quoi", [
    ("lead:", "points de contenu"),
    ("{ label:", "sources citées"),
    ("q:", "questions de la FAQ"),
])
def test_les_blocs_comprendre_restent_a_parite_fr_en(marqueur, quoi):
    """DEUX LISTES PARALLÈLES FINISSENT TOUJOURS PAR DIVERGER.

    RICH_FR et RICH_EN sont deux rédactions du même contenu. Le 2026-10-22 une correction
    juridique — le délai de recours des tiers, DEUX mois et non quatre — a été portée en
    français seulement : pendant quelques heures la page anglaise a continué d'annoncer un
    délai faux, dans le sens qui fait perdre son recours au lecteur. Rien ne l'a signalé.

    Ce test ne compare pas les textes (ils n'ont aucune raison de se correspondre mot à mot),
    il compare les STRUCTURES : autant de points, de sources et de questions d'un côté que de
    l'autre. Un ajout dans une seule langue casse le build.
    """
    fr, en = _moities()
    n_fr, n_en = fr.count(marqueur), en.count(marqueur)
    assert n_fr == n_en, (
        f"{quoi} : {n_fr} en français contre {n_en} en anglais — une langue a été enrichie "
        "sans l'autre (voir l'incident du délai de recours, 2026-10-22)"
    )


NAV = REPO_ROOT / "site" / "src" / "config" / "nav.ts"


def test_les_liens_de_navigation_finissent_par_une_barre_oblique():
    """UN LIEN SANS BARRE FINALE EST UNE REDIRECTION, RÉPÉTÉE SUR CHAQUE PAGE.

    Le site sert ses pages en dossiers : /fr/classement redirige vers /fr/classement/.
    La navigation étant présente sur les 6 660 pages, un seul href incomplet produit 6 660
    redirections — et Google, qui les suit, classe l'URL d'origine « page avec redirection »
    et ne l'indexe pas. Relevé en Search Console le 2026-10-22 : 1 474 URLs dans ce cas,
    tout le maillage interne passant par une redirection, pendant qu'une page importante
    (/acceptability-of-data-centers/) n'avait JAMAIS été explorée. Le sitemap, lui, était
    correct : c'est bien nos liens qui dépensaient le budget d'exploration.

    Exceptions légitimes : une ancre (/fr/#faq) et une requête (/fr/comparer/?v=2), qui
    portent déjà leur barre avant le # ou le ?.
    """
    texte = NAV.read_text()
    fautifs = [h for h in re.findall(r'href: "(/[^"]*)"', texte)
               if "#" not in h and "?" not in h and not h.endswith("/")]
    assert not fautifs, (
        "ces liens de navigation déclencheront une redirection sur chaque page du site : "
        + ", ".join(fautifs)
    )


PROCEDURE_DIR = REPO_ROOT / "site" / "src" / "content" / "procedure"

# Les seuls hôtes dont nous acceptons un lien dans un bloc « procédure » : ceux qui
# servent le TEXTE. Un cabinet d'avocats, un blog spécialisé ou un guide ministériel
# commentent le texte — et le commentaire vieillit sans le dire. Le 2026-10-22 nous
# avons publié « quatre mois » pour le délai de recours des tiers : exact de 2017 à
# 2024, faux depuis le décret n° 2024-423, et lu dans un commentaire.
# Déclarer un hôte ici ne crée aucune affirmation : c'est le registre de l'endroit où la loi
# d'un pays se LIT. On y inscrit donc aussi les pays dont la procédure reste à écrire, pour
# que la lecture commence au bon endroit plutôt que sur le premier résultat venu.
HOTES_DE_TEXTE = (
    "eur-lex.europa.eu",       # Union européenne — socle des directives
    "legifrance.gouv.fr",      # France
    "nysenate.gov",            # État de New York
    # Recueils d'ÉTAT américains — un par État, conséquence directe de l'absence de permis
    # fédéral. Ceux marqués « bloqué » refusent l'accès automatisé depuis notre environnement
    # (403, Cloudflare, connexion refusée) : la loi est lisible, pas le site.
    "leginfo.legislature.ca.gov",   # Californie
    "law.lis.virginia.gov",         # Virginie
    "statutes.capitol.texas.gov",   # Texas
    "app.leg.wa.gov",               # Washington
    "flsenate.gov",                 # Floride
    "revisor.mn.gov",               # Minnesota
    "legis.iowa.gov",               # Iowa
    "azleg.gov",                    # Arizona
    "revisor.mo.gov",               # Missouri
    "mgaleg.maryland.gov",          # Maryland
    "scstatehouse.gov",             # Caroline du Sud
    "delcode.delaware.gov",         # Delaware
    "legislature.vermont.gov",      # Vermont
    "code.dccouncil.gov",           # District de Columbia
    "legislature.maine.gov",        # Maine
    "ksrevisor.gov",                # Kansas
    "mca.legmt.gov",                # Montana
    "cga.ct.gov",                   # Connecticut
    "le.utah.gov",                  # Utah
    "sdlegislature.gov",            # Dakota du Sud
    "code.wvlegislature.gov",       # Virginie-Occidentale
    "ilga.gov",                     # Illinois        — injoignable
    "legis.ga.gov",                 # Géorgie         — bloqué
    "codes.ohio.gov",               # Ohio
    "legis.state.pa.us",            # Pennsylvanie
    "palegis.us",                   # Pennsylvanie (nouveau domaine)
    "oksenate.gov",                 # Oklahoma
    "njleg.state.nj.us",            # New Jersey      — bloqué
    "ncleg.gov",                    # Caroline du Nord
    "leg.colorado.gov",             # Colorado
    "malegislature.gov",            # Massachusetts
    "oregonlegislature.gov",        # Oregon
    "legislature.mi.gov",           # Michigan
    "iga.in.gov",                   # Indiana         — bloqué
    "docs.legis.wisconsin.gov",     # Wisconsin
    "oscn.net",                     # Oklahoma
    "legis.la.gov",                 # Louisiane       — bloqué
    "apps.legislature.ky.gov",      # Kentucky        — bloqué
    "nebraskalegislature.gov",      # Nebraska
    "leg.state.nv.us",              # Nevada
    "nmonesource.com",              # Nouveau-Mexique — bloqué
    "wyoleg.gov",                   # Wyoming
    "gencourt.state.nh.us",         # New Hampshire
    "legislature.idaho.gov",        # Idaho
    "ndlegis.gov",                  # Dakota du Nord
    "capitol.hawaii.gov",           # Hawaï           — bloqué
    "akleg.gov",                    # Alaska          — bloqué
    "rilegislature.gov",            # Rhode Island
    "law.cornell.edu",         # Cornell LII — reproduction du NYCRR
    "gesetze-im-internet.de",  # Allemagne (fédéral)
    "wetten.overheid.nl",      # Pays-Bas
    "legislation.gov.uk",      # Royaume-Uni
    "boe.es",                  # Espagne
    "fedlex.admin.ch",         # Suisse (fédéral — JAMAIS pour un permis cantonal)
    "normattiva.it",           # Italie
    "isap.sejm.gov.pl",        # Pologne           — à écrire
    "riksdagen.se",            # Suède             — à écrire
    "lovdata.no",              # Norvège           — à écrire
    "ejustice.just.fgov.be",   # Belgique (fédéral)
    "finlex.fi",               # Finlande          — à écrire
    "retsinformation.dk",      # Danemark          — à écrire
    "irishstatutebook.ie",     # Irlande           — à écrire
    "legilux.public.lu",       # Luxembourg        — à écrire
    "diariodarepublica.pt",    # Portugal          — à écrire
    "ris.bka.gv.at",           # Autriche
    "dziennikustaw.gov.pl",    # Pologne           — à écrire (ISAP bloque)
    "codex.vlaanderen.be",     # Flandre           — à écrire
    # Recueils CANTONAUX suisses — un par canton, c'est la conséquence directe du fait
    # qu'il n'existe pas de droit suisse du permis de construire.
    "zh.ch",                   # Zurich (zhlex)
    "belex.sites.be.ch",       # Berne
    "bgs.zg.ch",               # Zoug
    "bdlf.fr.ch",              # Fribourg
    "silgeneve.ch",            # Genève
    "srl.lu.ch",               # Lucerne
    "lex.vs.ch",               # Valais
    "gesetzessammlung.sg.ch",  # Saint-Gall
    "gesetzessammlung.bs.ch",  # Bâle-Ville
    "bgs.so.ch",               # Soleure
    "rechtsbuch.tg.ch",        # Thurgovie
    "rechtsbuch.sh.ch",        # Schaffhouse
    "bl.clex.ch",              # Bâle-Campagne
    "prestations.vd.ch",       # Vaud    — à écrire (application monopage)
    "rsju.jura.ch",            # Jura    — à écrire (PDF de versions périmées)
    "rl.ti.ch",                # Tessin  — à écrire
)


def _fichiers_de_procedure() -> list[Path]:
    return sorted(p for p in PROCEDURE_DIR.glob("*.ts")
                  if p.name not in ("types.ts", "index.ts"))


def test_il_existe_au_moins_un_fichier_de_procedure():
    """Garde-fou du test suivant : une boucle sur zéro fichier passe toujours."""
    assert _fichiers_de_procedure(), f"aucun fichier de procédure dans {PROCEDURE_DIR}"


@pytest.mark.parametrize("fichier", _fichiers_de_procedure(), ids=lambda p: p.stem)
def test_toute_affirmation_de_procedure_porte_son_texte_source(fichier):
    """LES BLOCS « PROCÉDURE » SONT LE SEUL ENDROIT OÙ NOUS DISONS QUOI FAIRE.

    Ailleurs nous publions un fait et sa source ; ici nous disons à un élu ou à un riverain
    qu'il lui reste deux mois, ou cinq jours ouvrés. Une erreur ne se lit pas comme une
    erreur : elle se lit comme un délai, et le lecteur le laisse passer.

    D'où la règle, vérifiée fichier par fichier : chaque affirmation porte l'article qui la
    crée (`cite`), un lien vers le TEXTE et non vers un commentaire (`url`), et la date à
    laquelle nous avons lu ce texte dans sa version en vigueur (`verified`).
    """
    texte = fichier.read_text()
    n_affirmations = len(re.findall(r'\bcite: "', texte))
    if not n_affirmations:
        # Un fichier SANS affirmation est légitime, et c'est même un résultat : la Suisse
        # n'a aucun délai fédéral applicable à un permis de construire, et l'art. 50 PA
        # (« 30 jours »), qui se trouve en deux clics, ne régit que la procédure FÉDÉRALE.
        # Le citer serait le bon texte au mauvais périmètre. Mais un fichier vide doit
        # alors le DIRE : aucune juridiction servie, et un cadre qui explique pourquoi.
        assert "subdivisions: {}" in texte or "national:" not in texte, (
            f"{fichier.name} n'a aucune affirmation mais sert quand même une juridiction"
        )
        assert "frame: {" in texte, (
            f"{fichier.name} est vide sans dire pourquoi — un pays sans procédure publiable "
            "doit porter le constat, sinon il se lit comme un oubli"
        )
        return

    for champ, motif in (("cite", r'cite: "[^"]{8,}"'),
                         ("url", r'url: "https://[^"]+"'),
                         ("verified", r'verified: "\d{4}-\d{2}-\d{2}"')):
        trouves = re.findall(motif, texte)
        assert len(trouves) == n_affirmations, (
            f"{fichier.name} : {n_affirmations} affirmations mais {len(trouves)} champs "
            f"`{champ}` valides — une affirmation sans sa trace n'est pas publiable"
        )

    for url in re.findall(r'url: "(https://[^"]+)"', texte):
        assert any(h in url for h in HOTES_DE_TEXTE), (
            f"{fichier.name} : {url} n'est pas un hôte qui sert le texte de loi. "
            "Un commentaire vieillit sans le dire (incident « quatre mois », 2026-10-22)"
        )


@pytest.mark.parametrize("fichier", _fichiers_de_procedure(), ids=lambda p: p.stem)
def test_les_affirmations_de_procedure_sont_bilingues(fichier):
    """Même raison que la parité des blocs « Comprendre » : une correction portée dans une
    seule langue laisse l'autre annoncer un délai faux, et rien ne le signale."""
    texte = fichier.read_text()
    n_fr, n_en = len(re.findall(r'^\s+fr: "', texte, re.M)), len(re.findall(r'^\s+en: "', texte, re.M))
    assert n_fr == n_en, (
        f"{fichier.name} : {n_fr} formulations françaises contre {n_en} anglaises"
    )


def test_le_registre_des_procedures_couvre_le_corpus():
    """UN PAYS ABSENT DU REGISTRE EST UN TROU QUE PERSONNE NE VOIT.

    Le registre liste les pays du corpus et NE SAUTE PAS ceux dont la procédure n'est pas
    lue : il les déclare à `null`. Un trou déclaré se compte et se rattrape ; un trou omis
    se découvre quand un lecteur néerlandais lit une procédure française.

    Ce test lit les pays réellement servis et exige une ligne pour chacun. Un nouveau pays
    dans le corpus casse donc le build, et impose le choix : lire la loi, ou déclarer le trou.
    """
    artefacts = REPO_ROOT / "site" / "public" / "data" / "dc"
    fiches = sorted(artefacts.glob("*.json"))
    if not fiches:
        pytest.skip("artefacts non construits (corpus privé) — rien à confronter")

    pays = {json.loads(p.read_text()).get("country") for p in fiches} - {None}
    declares = set(re.findall(r'^  ([A-Z]{2})[:,]', (PROCEDURE_DIR / "index.ts").read_text(), re.M))
    manquants = sorted(pays - declares)
    assert not manquants, (
        "ces pays sont servis sans ligne au registre des procédures : "
        + ", ".join(manquants)
        + " — ajoutez-les, à `null` si la loi n'est pas lue"
    )


def _lignes_comparateur(dossier: Path):
    """Chaque ligne de site d'un fichier comparateur, quelle que soit sa profondeur."""
    def descendre(o):
        if isinstance(o, dict):
            if "piliers" in o:
                yield o
                return
            for v in o.values():
                yield from descendre(v)
        elif isinstance(o, list):
            for v in o:
                yield from descendre(v)
    for f in sorted(dossier.glob("*.json")):
        yield from descendre(json.loads(f.read_text()))


def test_le_comparateur_ne_publie_aucune_lettre_que_la_fiche_retient():
    """UNE LETTRE RETIRÉE DE LA FICHE NE DOIT REPARAÎTRE NULLE PART.

    Le comparateur se construisait AVANT `scrub-grades` et lisait donc les artefacts non
    blanchis. Mesuré le 2026-10-23 sur us-stamp-data-center : le comparateur publiait
    « energy E · water E · land B · local_impact C » pendant que la fiche du même site
    affichait « en attente » sur les cinq piliers — dont ce C d'impact local qu'on venait
    justement de décider de taire, parce qu'il tient sur une seule mesure. 387 fiches
    concernées, en production.

    La règle « la fiche a raison, les agrégats la suivent » existait depuis le 2026-10-16 ;
    le comparateur n'était simplement pas dans le périmètre du blanchiment. Ce test l'y met :
    il confronte, site par site, ce que le comparateur publie à ce que la fiche servie publie.
    """
    artefacts = REPO_ROOT / "site" / "public" / "data"
    comparateur, fiches = artefacts / "comparator", artefacts / "dc"
    if not comparateur.exists() or not any(fiches.glob("*.json")):
        pytest.skip("artefacts non construits (corpus privé) — rien à confronter")

    servi = {}
    for p in fiches.glob("*.json"):
        d = json.loads(p.read_text())
        bande = d.get("provisional_band") or {}
        sous = d.get("pillar_bands") or {}
        if isinstance(bande.get("central"), str):
            # Lettre définitive retenue : la fiche ne publie que les sous-notes PROBABLES.
            servi[d["id"]] = {pid: b["central"] for pid, b in sous.items()}
        else:
            servi[d["id"]] = {pid: v.get("grade") for pid, v in (d.get("pillars") or {}).items()
                              if v.get("grade") in ("A", "B", "C", "D", "E")}

    ecarts = []
    for ligne in _lignes_comparateur(comparateur):
        attendu = servi.get(ligne.get("id"))
        if attendu is None:
            continue
        for pilier, lettre in (ligne.get("piliers") or {}).items():
            if attendu.get(pilier) != lettre:
                ecarts.append(f"{ligne['id']}/{pilier}: comparateur {lettre!r} "
                              f"contre fiche {attendu.get(pilier)!r}")
    assert not ecarts, (
        f"{len(ecarts)} lettre(s) publiée(s) par le comparateur et retenue(s) par la fiche — "
        "le comparateur se construit-il toujours APRÈS scrub-grades ? "
        + "; ".join(ecarts[:5])
    )
