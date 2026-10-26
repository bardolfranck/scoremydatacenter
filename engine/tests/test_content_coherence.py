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
    "legis.ga.gov",                 # Géorgie (l'Assemblée ne publie pas le code)
    # EXCEPTION MOTIVÉE — la Géorgie n'a AUCUNE source officielle libre de son code :
    # l'Assemblée générale renvoie vers LexisNexis, qui le publie sous contrat et protège
    # l'accès par un CAPTCHA. Le procureur général, lui, REPRODUIT le texte de la loi en
    # annexe de son guide officiel. Ce n'est pas un commentaire qu'on cite : c'est le texte,
    # reproduit par l'autorité qui l'applique, et la citation nomme ce détour.
    "law.georgia.gov",              # Géorgie — texte reproduit par le procureur général
    "media.ark.org",                # Arkansas — texte reproduit par le procureur général
    "nmdoj.gov",                    # Nouveau-Mexique — texte reproduit par le ministère de la Justice
    "codes.ohio.gov",               # Ohio
    "legis.state.pa.us",            # Pennsylvanie
    "palegis.us",                   # Pennsylvanie (nouveau domaine)
    "oksenate.gov",                 # Oklahoma
    "njleg.state.nj.us",            # New Jersey
    "ncleg.gov",                    # Caroline du Nord
    "leg.colorado.gov",             # Colorado
    "malegislature.gov",            # Massachusetts
    "oregonlegislature.gov",        # Oregon
    "legislature.mi.gov",           # Michigan
    "iga.in.gov",                   # Indiana         — bloqué
    "docs.legis.wisconsin.gov",     # Wisconsin
    "oscn.net",                     # Oklahoma
    "legis.la.gov",                 # Louisiane
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
    # `absente.ts` est exclu À DESSEIN : c'est le texte qu'on sert quand on n'a PAS de
    # juridiction, donc le seul fichier du dossier qui ne doit porter aucune affirmation
    # sourcée. Il a sa propre garde, juste en dessous, qui vérifie l'inverse.
    return sorted(p for p in PROCEDURE_DIR.glob("*.ts")
                  if p.name not in ("types.ts", "index.ts", "absente.ts"))


def test_le_texte_d_absence_ne_cite_aucune_loi():
    """ON NE SOURCE PAS CE QU'ON N'A PAS LU.

    `absente.ts` dit au lecteur ce qui reste vrai quand la juridiction n'est pas lue : qui
    décide, quel levier existe partout, et quelle question poser à notre place. Rien de tout
    cela ne s'appuie sur un article — et si un `cite:` apparaissait ici, ce serait le signe
    qu'une affirmation sourcée a glissé dans le texte du trou, là où personne ne la
    vérifierait jamais.

    Les fourchettes qu'il cite (« de trois jours ouvrés à trente ») sont DÉRIVÉES des
    juridictions déjà lues, pas d'un texte : elles se recalculent, elles ne se citent pas.
    """
    texte = (PROCEDURE_DIR / "absente.ts").read_text()
    assert 'cite: "' not in texte and "url: " not in texte, (
        "absente.ts porte une citation : une affirmation sourcée a glissé dans le texte "
        "servi quand il n'y a PAS de source"
    )
    n_fr = len(re.findall(r"^\s+fr: ", texte, re.M))
    n_en = len(re.findall(r"^\s+en: ", texte, re.M))
    assert n_fr == n_en and n_fr >= 9, f"parité FR/EN rompue : {n_fr} contre {n_en}"


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


QUESTIONS = REPO_ROOT / "site" / "src" / "content" / "questions-derivees.ts"


def test_une_question_par_indicateur_de_projet_et_aucune_pour_la_base():
    """LA DISTINCTION QUI FAIT TOUT : UN TROU DU DOSSIER N'EST PAS UN TROU DE NOTRE MESURE.

    Un indicateur du bloc PROJET/PROCESS non renseigné, c'est le porteur qui ne l'a pas
    documenté — une question à lui poser. Un indicateur du bloc BASE non collecté, c'est
    NOTRE trou : demander à un exploitant « quelle est l'intensité carbone du réseau local ? »
    n'a aucun sens, c'est à nous de la mesurer.

    La maquette du portrait tirait « à demander : quel poste de raccordement, quelle
    capacité » de E2 — un indicateur de BASE. Surlignée, fausse, et présentée au lecteur
    comme issue du dossier du porteur. Ce test interdit que ça revienne : chaque indicateur
    projet/process du MVP porte sa question, aucun indicateur de base n'en porte.
    """
    texte = QUESTIONS.read_text()
    declarees = set(re.findall(r"^  ([A-Z]\d+): \{", texte, re.M))
    attendues = {i["id"] for i in load_methodology()["indicators"]
                 if i.get("mvp") and i["block"] in ("project", "process")}
    base = {i["id"] for i in load_methodology()["indicators"]
            if i.get("mvp") and i["block"] == "base"}

    manquantes = sorted(attendues - declarees)
    assert not manquantes, (
        "ces indicateurs du dossier n'ont pas de question : le portrait sera muet sur un "
        "trou que le porteur DOIT combler — " + ", ".join(manquantes)
    )
    intruses = sorted(declarees & base)
    assert not intruses, (
        "ces indicateurs sont des mesures À NOUS, et le portrait les présenterait comme des "
        "questions au porteur — " + ", ".join(intruses)
    )


def test_chaque_stade_de_procedure_porte_son_verbe():
    """UNE QUESTION SANS SON VERBE EST UN VŒU.

    « Quel volume d'eau par an ? » ne s'obtient pas de la même façon avant le dépôt du
    dossier, pendant l'enquête, ou dix ans après la mise en service — et parfois ne s'obtient
    plus du tout. Le verbe vient des fenêtres du dossier juridique ; il doit exister pour
    CHAQUE statut que le corpus sait produire, sinon une fiche entière perd sa conjugaison.
    """
    texte = QUESTIONS.read_text()
    verbes = set(re.findall(r"^  (\w+): \{$", texte[texte.index("export const VERBES"):], re.M))
    artefacts = REPO_ROOT / "site" / "public" / "data" / "dc"
    if not any(artefacts.glob("*.json")):
        pytest.skip("artefacts non construits — rien à confronter")
    statuts = {json.loads(p.read_text()).get("project_status") for p in artefacts.glob("*.json")}
    manquants = sorted(s for s in statuts if s and s not in verbes)
    assert not manquants, (
        "ces statuts du corpus n'ont pas de verbe : leurs fiches poseraient des questions "
        "sans dire quand les poser — " + ", ".join(manquants)
    )


def test_le_compte_du_portrait_decrit_ce_que_la_lettre_resume():
    """UN COMPTE QUI NE DÉCRIT PAS SA LETTRE FAIT DOUTER DE LA LETTRE.

    La sous-note d'un pilier est agrégée sur TOUS ses indicateurs MVP — bloc projet et
    process compris. Le portrait affichait d'abord un dénominateur limité au bloc base : la
    transparence de Fouju, dont la lettre A repose sur T1 et T2 (process), sortait donc
    « 0 mesure sur 0 » sous un A parfaitement fondé. J'en ai conclu que la lettre était
    infondée et je l'ai retirée — en cassant le seul pilier du corpus qui porte une note de
    transparence.

    Le compte doit décrire ce que la lettre résume, sinon il contredit la lettre, et c'est
    le compte qui a tort.
    """
    gabarit = (REPO_ROOT / "site" / "src" / "components" / "SitePortrait.astro").read_text()
    assert 'd.mvp && d.pillar === p' in gabarit and 'd.block === "base" && d.pillar' not in gabarit, (
        "le dénominateur du portrait est revenu au seul bloc base : il décrira moins que ce "
        "que la lettre du pilier résume"
    )


PORTRAIT = REPO_ROOT / "site" / "src" / "components" / "SitePortrait.astro"


def test_le_portrait_n_expose_jamais_un_code_d_indicateur():
    """NOTRE TAXONOMIE N'EST PAS DU CONTENU PUBLIC.

    Le portrait affichait « F4 », « T1 », « W4 » à côté de chaque question, et une phrase
    expliquait au lecteur que « chaque ligne vient d'un indicateur du dossier, nommé à
    côté ». Deux fautes en une : ces codes ne veulent rien dire pour un riverain, et ils
    livrent la structure de notre grille à qui voudrait la recopier — la même grille que
    l'anti-pillage protège partout ailleurs.

    Un portrait pose des questions en français. D'où elles sortent nous regarde.
    """
    gabarit = PORTRAIT.read_text()
    fuites = re.findall(r"\{q\.id\}|\{m\.id\}|\{i\.id\}", gabarit)
    assert not fuites, (
        "le portrait rend un identifiant d'indicateur : " + ", ".join(sorted(set(fuites)))
    )

    for page in (REPO_ROOT / "site" / "src" / "pages" / "fr" / "dc" / "[id]" / "portrait.astro",
                 REPO_ROOT / "site" / "src" / "pages" / "dc" / "[id]" / "portrait.astro"):
        texte = page.read_text()
        for aveu in ("indicateur du dossier", "named beside", "comes from one measure"):
            assert aveu not in texte, (
                f"{page.name} explique au lecteur d'où viennent les lignes : "
                f"« {aveu} ». La provenance interne ne se raconte pas."
            )


# --- Un compte de corpus ne tient pas dans un titre ------------------------------
# Vu en prod (2026-10-26) : « Classement des data centers A–E — 1 400+ sites notés »,
# en titre ET en meta description des deux pages classement, alors que le corpus servait
# 2 195 sites notés. Ce chiffre était juste le jour où il a été écrit ; il a vieilli en
# silence, dans la première ligne du snippet Google, là où personne ne relit.
#
# La règle qui en sort : un titre et une description portent une PROMESSE, pas un
# inventaire. L'unité (« site par site ») ne vieillit pas ; le compte, oui. Et le compte
# exact, s'il doit paraître, se dérive du corpus — il ne se tape pas à la main.

COMPTE_EN_DUR = re.compile(r"\d[\d  ,.]{2,}\+?\s*(?:sites?|data[  -]?centers?|fiches?)", re.I)


# Deux formes coexistent dans les pages : un objet `t` ({pageTitle, metaDescription}) pour
# les pages qui partagent un gabarit FR/EN, et les props `title=`/`description=` passées
# directement à <Base> pour les pages minces. Le garde-fou doit voir LES DEUX — il a d'abord
# été écrit sur la seule première forme, et la carte, qui emploie la seconde, lui est passée
# sous le nez (2026-10-26). Un gate qui ne voit pas toute sa grille ne garde rien.
_FORMES = (
    r"\b(pageTitle|metaDescription)\s*:\s*\"((?:[^\"\\]|\\.)*)\"",
    r"^\s*(title|description)=\"((?:[^\"\\]|\\.)*)\"",
)


def _entetes_de_pages():
    """(fichier, champ, valeur) pour chaque titre/description de page, les deux formes."""
    for page in (REPO_ROOT / "site" / "src" / "pages").rglob("*.astro"):
        texte = page.read_text()
        for forme in _FORMES:
            for champ, valeur in re.findall(forme, texte, re.M):
                yield page, champ, valeur


def test_aucun_titre_ni_description_n_annonce_un_compte_de_corpus():
    fautes = [
        f"{page.relative_to(REPO_ROOT)} · {champ} : « {COMPTE_EN_DUR.search(valeur).group(0).strip()} »"
        for page, champ, valeur in _entetes_de_pages()
        if COMPTE_EN_DUR.search(valeur)
    ]
    assert not fautes, (
        "un compte de corpus est écrit en dur dans un en-tête de page — il vieillira sans "
        "que rien ne le signale, et c'est ce que Google affiche :\n" + "\n".join(fautes)
    )


def test_le_garde_fou_du_compte_mord_vraiment():
    # test négatif : les deux formulations retirées le 2026-10-26, et leurs variantes
    # plausibles, doivent être attrapées — sinon le garde-fou ne garde rien.
    for ancienne in (
        "Classement des data centers A–E — 1 400+ sites notés",
        "Data-center ranking A–E — 1,400+ sites scored",
        "Classez 1 400+ data centers par leur note d'acceptabilité A–E",
        "2 195 fiches notées",
        "Rank 3,283 datacenters",
    ):
        assert COMPTE_EN_DUR.search(ancienne), f"le garde-fou laisse passer « {ancienne} »"
    # et il ne doit PAS mordre sur une norme ni sur la formule qui remplace le compte
    for innocente in (
        "PUE, ISO/IEC 30134, Green Grid, ETSI — la première note d'acceptabilité, site par site",
        "La note d'acceptabilité A–E, site par site : énergie, eau, sol, impact local.",
        "Quels data centers passent, lesquels échouent ?",
    ):
        assert not COMPTE_EN_DUR.search(innocente), f"le garde-fou mord à tort sur « {innocente} »"


def test_le_garde_fou_voit_les_deux_formes_d_en_tete():
    """Mutation vivante : le garde-fou doit couvrir la carte, qui n'utilise pas `t`."""
    vus = {page.name for page, _, _ in _entetes_de_pages()}
    for mince in ("carte.astro", "map.astro"):
        assert mince in vus, (
            f"{mince} n'est plus lu par le garde-fou des en-têtes — c'est par là que "
            "« 1 400+ » serait revenu"
        )
    champs = {champ for _, champ, _ in _entetes_de_pages()}
    assert {"title", "description"} <= champs and {"pageTitle", "metaDescription"} <= champs, (
        f"le garde-fou ne voit plus les deux formes d'en-tête : {sorted(champs)}"
    )
