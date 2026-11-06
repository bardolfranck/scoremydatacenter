# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Barrière d'avant-mise-en-ligne : une page d'une langue ne sert pas le texte d'une autre.

🔴 POURQUOI CETTE BARRIÈRE N'EST PAS UN TEST. Nos gardes de traduction comparent des CLÉS
(les deux langues ont-elles les mêmes entrées ?) et, en préviz, des COMPTES de blocs. Aucun
des deux ne voit du français servi sur une page néerlandaise : les clés sont là, les blocs
sont au même nombre, et le texte est français. C'est exactement ce qui s'est produit —
« Datacenters begrijpen » titrait en néerlandais et servait 152 blocs sur 185 en français,
parce que la page importait `CHECKLIST_FR` au lieu de `CHECKLIST_NL`. Deux conventions pour
désigner une langue dans le même dépôt (`TABLE.fr` et `TABLE_FR`), et un renommage qui n'en
voyait qu'une.

Ce qui le détecte : confronter le texte SERVI d'une page au texte SERVI de sa jumelle.
Un bloc identique mot pour mot d'une langue à l'autre est soit volontairement neutre, soit
une traduction qui n'a pas eu lieu — et il n'y a que deux façons de le savoir, le déclarer
ou le corriger.

LA DETTE EST DÉCLARÉE, PAS TOLÉRÉE EN SILENCE. Une langue en préparation a forcément des
pages qui ne sont pas prêtes ; le néerlandais n'est pas encore dans `LANGUES_VIVANTES`. Le
contrôle ne refuse donc pas la mise en ligne tant que le compte est CELUI QU'ON A DÉCLARÉ —
il refuse qu'il MONTE, et il demande de l'abaisser quand il descend. Même discipline que les
cliquets de la suite de tests : un trou qu'on mesure vaut mieux qu'un trou qu'on découvre
chez le lecteur, et une dette qu'on ne voit pas diminuer est une dette qu'on cesse de
rembourser. À zéro, la langue peut passer vivante.

Usage : python3 scripts/check_langue_servie.py [dossier] (défaut : site/dist)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(RACINE))
from engine.langues import pays_de_la_langue  # noqa: E402

# 🔴 LES PAYS DONT LA PROSE EST DUE DANS UNE LANGUE — déclaré, jamais déduit d'un préfixe.
# La doctrine est PAR PAYS (Franck, 2026-11-05) : l'édition néerlandaise doit sa prose aux
# sites néerlandais, pas aux 3 140 autres du corpus, qui s'y servent en anglais par choix.
# Le préfixe d'identifiant et le code de langue coïncident pour `nl`, et c'est précisément
# pourquoi il faut l'écrire : la coïncidence ne tient pas (un jour `en` → GB + IE + US), et
# un garde qui DÉDUIT son périmètre d'une coïncidence se tromperait en silence le jour où
# elle cesse.
# ⚠️ OUVERT, ET JE NE LE TRANCHE PAS : la Flandre. 42 fiches `be-`, dont une part parle
# néerlandais. Le lot livré ne couvre que `nl-` ; les inclure ici créerait 42 dettes d'un
# coup, les exclure par défaut est un choix éditorial que personne n'a fait. À Franck.
# 🔴 ET ELLE EST LUE, PLUS RECOPIÉE (2026-11-06). Cette liste vivait ici en dur, et elle
# y était JUSTE — c'est ce qui rend la recopie dangereuse. Le site a maintenant besoin du
# même périmètre pour décider quelles PAGES il bâtit : deux listes, et le jour où la
# Flandre entre, le site sort les pages belges pendant que la barrière continue de mesurer
# les seules « nl- » — elle se tairait sur une édition entière [[liste-a-deux-endroits-ment]].
# La source est `site/src/content/langues.ts`, lue par `engine.langues`.
PAYS_DE_LA_LANGUE = pays_de_la_langue()

# Les surfaces néerlandaises qui reprennent encore le texte d'une autre langue, au
# 2026-11-06 — QUATRE :
#   · /nl/indices/ est SORTIE de cette liste : ses 8 dernières chaînes (encart, légende,
#     dénominateurs) sont traduites, et sa page n'a plus une seule branche binaire. La
#     carte néerlandaise existe aussi — `/nl/kaart/`, première des sept pages manquantes.
#   · /nl/vergelijken/ (5 blocs EN) — le comparateur porte sa copie en douze ternaires
#     binaires dans le composant ; c'est de la plomberie à faire, pas une traduction.
#   · /nl/bibliotheek/ et /nl/bibliotheek/alles/ (FR et EN) — la bibliothèque est déclarée
#     NON traduite par Franck tant qu'il n'en décide pas autrement.
#   · /nl/ (3 blocs FR) — les titres d'actu, produits par le pipeline de veille dans le
#     dépôt privé : `headline_i18n` ne porte que fr et en. Reporté par Franck.
# 🔴 DEUX CHOSES VIVAIENT DANS UN SEUL CHIFFRE, ET ÇA RENDAIT LE VERROU INOUVRABLE.
# « 4 surfaces » mélangeait une DETTE (du travail qui reste) et des EXEMPTIONS (des
# décisions prises). Trois des quatre étaient des choix de Franck — la bibliothèque n'est
# pas traduite, les titres d'actu sont reportés — donc le compte ne pouvait pas tomber à
# zéro, donc la langue ne pouvait JAMAIS être offerte. Un verrou qu'aucun travail n'ouvre
# n'est pas un verrou, c'est un mur.
#
# Les deux sont donc séparés, et les exemptions sont NOMMÉES, DATÉES et ATTRIBUÉES — jamais
# un silence. Elles restent COMPTÉES et AFFICHÉES à chaque passage : une exemption muette
# rend le garde aveugle [[exemption-nest-pas-obligation]], et leur nombre ne peut que
# baisser (`test_les_exemptions_de_prose_ne_peuvent_que_baisser`).
EXEMPTIONS_NL: dict[str, str] = {
    "/nl/bibliotheek/":
        "bibliothèque déclarée NON traduite (Franck, 2026-11-05) — produit payant, sa prose "
        "se décide avec son modèle, pas avec l'ouverture d'une langue",
    "/nl/bibliotheek/alles/":
        "même décision que l'index de la bibliothèque",
    "/nl/":
        "trois titres d'ACTU, produits par le pipeline de veille du dépôt privé : "
        "`headline_i18n` ne porte que fr et en. Reporté par Franck le 2026-11-05 — le jour "
        "où la veille émet `nl`, cette exemption tombe sans rien changer ici",
}

# Ce qui RESTE À PAYER, et seulement ça. À zéro, la langue peut passer vivante — et elle y
# est passée le 2026-11-06, le comparateur étant le dernier : sa table est à trois colonnes,
# ses sept chaînes de gabarit sont rentrées, son chemin de fiche et sa locale sont dérivés.
# Le cliquet reste à 0 : il refuse désormais la PREMIÈRE surface qui reviendrait.
DETTE_SURFACES_NL = 0

# Les blocs qui sont les MÊMES dans toutes les langues PAR DÉCISION, pas par négligence.
# Chaque motif est une règle de la maison, pas une exception de confort :
#   · les identifiants juridiques (AGPL-3.0, ODbL, CC BY-SA) et le copyright ne se
#     traduisent pas — ce sont des noms d'instruments ;
#   · un TITRE DE SOURCE se cite verbatim, dans sa langue d'origine : « ADEME, Prospective
#     des consommations des data centers » traduit en néerlandais devient introuvable ;
#   · une liste de noms d'organismes séparés par « · » (France Datacenter · Gimélec · AGIT)
#     est une énumération de noms propres ;
#   · un nom de site suivi de « ↗ » est le nom d'un data center, pas une phrase.
NEUTRES = re.compile(
    r"AGPL-3\.0|CC BY-SA|ODbL|©\s*20\d\d|European Code of Conduct|ISO/IEC|Nutri-Score"
    r"|·|↗|«.*»"
)

# Les paires à confronter : la page néerlandaise, et sa jumelle française.
# Lues de la table de routes pour ne pas recopier une liste qui vieillirait.
ROUTES = RACINE / "site" / "src" / "config" / "routes.ts"


def _paires() -> list[tuple[str, str, str]]:
    texte = ROUTES.read_text(encoding="utf-8")
    debut = texte.index("export const FAMILLES")
    region = texte[debut : texte.index("\nconst SEGMENTS", debut)]
    paires = []
    for morceau in re.split(r'\bid:\s*"', region)[1:]:
        chemins = dict(re.findall(r'\b(en|fr|nl):\s*"([^"]*)"', morceau.split("{ id:")[0]))
        if "nl" not in chemins:
            continue
        for autre in ("fr", "en"):
            if autre in chemins:
                paires.append((chemins["nl"], chemins[autre], autre))
    return paires


def _noms_propres(dossier: Path) -> set[str]:
    """Les noms de sites, d'opérateurs et de communes du corpus SERVI.

    🔴 Sans eux, la barrière se noie. L'accueil néerlandais faisait remonter 24 blocs
    « français » : vingt étaient des noms de data centers et de communes — « AtlasEdge DC
    Brussels BRU001 », « Hetzner Online FSN1 (Falkenstein) » — identiques par nature, et
    deux seulement étaient de vrais titres d'actualité non traduits. Un garde dont le signal
    utile représente 8 % de ce qu'il crie ne sera pas lu.
    """
    import json

    chemin = dossier / "data" / "map.geojson"
    if not chemin.is_file():
        return set()
    noms: set[str] = set()
    for f in json.loads(chemin.read_text(encoding="utf-8")).get("features", []):
        p = f.get("properties", {})
        for cle in ("name", "operator", "municipality"):
            if valeur := p.get(cle):
                noms.add(valeur.strip())
                # « Nom — Commune », la forme des vignettes de l'accueil et du mur satellite
                if (commune := p.get("municipality")) and cle == "name":
                    noms.add(f"{valeur.strip()} — {commune.strip()}")
    return noms


def _neutres_par_nature(dossier: Path, chemin_nl: str) -> set[str]:
    """Les blocs que le français et l'anglais servent À L'IDENTIQUE sur cette page.

    Ce ne sont pas des traductions manquantes : ce sont des champs qui ne se traduisent pas.
    Le relevé les apprend des deux langues en ligne au lieu de les énumérer à la main.
    """
    # 🔴 LA CLÉ DOIT ÊTRE LE CHEMIN CONCRET, PAS LE MOTIF. Première version : la recherche
    # se faisait sur « /nl/dc/:id/portret/ » alors que la page examinée est
    # « /nl/dc/nl-eurofiber-datacenter-arnhem/portret/ ». Aucune correspondance, donc aucun
    # bloc neutre, donc les 3 267 portraits remontaient leurs citations d'articles comme des
    # traductions manquantes. Un garde qui ne trouve rien ne dit pas qu'il n'a rien trouvé :
    # il dit que tout est faux [[absence-ressemble-a-zero]].
    familles = {}
    for nl, fr, en in _trios():
        if ":id" in nl:
            avant = nl.split(":id", 1)[0]
            if chemin_nl.startswith(avant):
                ident = chemin_nl[len(avant):].split("/", 1)[0]
                familles[chemin_nl] = (fr.replace(":id", ident), en.replace(":id", ident))
        else:
            familles[nl] = (fr, en)
    paire = familles.get(chemin_nl)
    if not paire:
        return set()
    blocs = []
    for chemin in paire:
        f = dossier / chemin.strip("/") / "index.html"
        if not f.is_file():
            return set()
        blocs.append(set(_blocs(f)))
    return blocs[0] & blocs[1]


def _trios() -> list[tuple[str, str, str]]:
    """Par famille : (chemin nl, chemin fr, chemin en) — celles qui ont les trois."""
    texte = ROUTES.read_text(encoding="utf-8")
    debut = texte.index("export const FAMILLES")
    region = texte[debut : texte.index("\nconst SEGMENTS", debut)]
    trios = []
    for morceau in re.split(r'\bid:\s*"', region)[1:]:
        c = dict(re.findall(r'\b(en|fr|nl):\s*"([^"]*)"', morceau.split("{ id:")[0]))
        if {"nl", "fr", "en"} <= c.keys():
            trios.append((c["nl"], c["fr"], c["en"]))
    return trios


def _blocs(fichier: Path) -> list[str]:
    """Le texte VISIBLE d'une page, par blocs — scripts et styles exclus.

    🔴 LE TEXTE EST DÉSÉCHAPPÉ, et ce n'est pas une politesse. Le relevé comparait du HTML
    échappé à des noms propres lus dans `map.geojson`, qui ne l'est pas : « Interconnect
    Services DC3 's-Hertogenbosch » arrivait ici en `&#39;s-Hertogenbosch`, ne correspondait
    à aucun nom du corpus, et remontait comme une phrase non traduite sur chaque fiche
    néerlandaise qui le cite. Un nom de ville néerlandais sur deux porte cette apostrophe
    ('s-Hertogenbosch, 's-Gravenhage) : c'est la troisième langue qui a révélé le défaut,
    pas un changement de code [[troisieme-langue-revele-les-binaires]].
    """
    import html

    t = fichier.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
    if "<body" in t:
        t = t[t.index("<body") :]
    # 25 caractères : en dessous, un mot isolé peut légitimement coïncider (« Contact »,
    # « API », un nom de commune). Au-dessus, une phrase identique est une phrase non traduite.
    return [
        b for b in (html.unescape(s).strip() for s in re.split(r"<[^>]+>", t)) if len(b) > 25
    ]


def main() -> int:
    dossier = Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / "site" / "dist"
    if not dossier.is_dir():
        print(f"langue servie : {dossier} n'existe pas", file=sys.stderr)
        return 1

    noms = _noms_propres(dossier)

    def _echantillon(motif_nl: str, motif_autre: str) -> list[tuple[str, str]]:
        """Les pages d'une famille à segment variable — un ÉCHANTILLON, pas la totalité.

        🔴 Les fiches et les portraits sont 6 534 pages néerlandaises : ce sont LE produit,
        et les exclure du contrôle parce qu'elles sont nombreuses reviendrait à ne vérifier
        que les pages qui comptent le moins. On en tire donc un échantillon régulier —
        trente, répartis dans l'ordre alphabétique des identifiants.

        🔴 ET L'ÉCHANTILLON EST CELUI DU PAYS DE LA LANGUE (Franck, 2026-11-05). Première
        version : trente identifiants tirés de TOUT le corpus, « ce qui balaie les pays ».
        Ça mesurait une dette qui n'existe pas. La doctrine est PAR PAYS : la prose
        néerlandaise est due sur les sites néerlandais, et une fiche texane servie en anglais
        sur l'édition néerlandaise est VOULUE, pas un trou. Un balayage du corpus faisait
        donc remonter 29 pages sur 30 comme fautives, et aucune quantité de travail n'aurait
        pu les rendre vertes : l'instrument interdisait l'ouverture de la langue pour une
        raison fausse.

        ⚠️ L'EXEMPTION NE DOIT PAS RENDRE LA FAMILLE MUETTE. Ce qui sort du contrôle, ce sont
        les fiches ÉTRANGÈRES — pas la famille. Les 152 fiches néerlandaises restent gardées,
        et si le relevé n'en trouve aucune il REFUSE DE CONCLURE : un échantillon vide passe
        toujours, et c'est la façon la plus discrète de perdre un garde.
        """
        avant, apres = motif_nl.split(":id", 1)
        racine = dossier / avant.strip("/")
        if not racine.is_dir():
            return []
        tous = sorted(d.name for d in racine.iterdir() if d.is_dir())
        prefixes = PAYS_DE_LA_LANGUE["nl"]
        if prefixes == "tous":
            prefixes = tuple(sorted({i.split("-", 1)[0] for i in tous}))
        ids = [i for i in tous if i.split("-", 1)[0] in prefixes]
        if tous and not ids:
            raise SystemExit(
                f"langue servie : aucune fiche d'un pays de la langue néerlandaise parmi "
                f"{len(tous)} identifiants de {avant} (préfixes attendus : "
                f"{', '.join(sorted(prefixes))}). Le relevé ne sait plus reconnaître les "
                f"fiches dues dans cette langue — il ne mesurerait plus rien, et un contrôle "
                f"sur l'ensemble vide passe toujours."
            )
        if not ids:
            return []
        pas = max(1, len(ids) // 30)
        return [
            (motif_nl.replace(":id", i), motif_autre.replace(":id", i))
            for i in ids[::pas][:30]
        ]

    fautes: list[tuple[str, str, int, int, list[str]]] = []
    vues = set()
    a_voir: list[tuple[str, str, str]] = []
    for chemin_nl, chemin_autre, langue in _paires():
        if ":id" in chemin_nl:
            a_voir += [(a, b, langue) for a, b in _echantillon(chemin_nl, chemin_autre)]
        else:
            a_voir.append((chemin_nl, chemin_autre, langue))

    for chemin_nl, chemin_autre, langue in a_voir:
        f_nl = dossier / chemin_nl.strip("/") / "index.html"
        f_autre = dossier / chemin_autre.strip("/") / "index.html"
        if not f_nl.exists():
            continue  # page pas encore écrite : c'est la dette du menu, pas celle-ci
        vues.add(chemin_nl)
        if not f_autre.exists():
            continue
        nl, autre = _blocs(f_nl), set(_blocs(f_autre))
        # 🔴 LA RÈGLE QUI ÉVITE LA LISTE D'EXCEPTIONS : un bloc IDENTIQUE entre le français
        # et l'anglais n'est pas une traduction manquante — c'est un champ qui ne se traduit
        # pas. Un nom de jeu de données (« ADEME Base Empreinte »), un instrument juridique,
        # une colonne « référentiel » : les deux langues servies le portent déjà tel quel.
        # Sans cette règle, /nl/methodologie/ remontait 17 blocs qui ne sont pas des fautes.
        # Avec elle, le garde n'a pas besoin qu'on énumère ce qu'il doit ignorer — ce sont
        # les deux langues EN LIGNE qui le disent, et elles ne vieillissent pas.
        neutres_par_nature = _neutres_par_nature(dossier, chemin_nl)
        communs = [
            b for b in dict.fromkeys(nl)
            if b in autre
            and b not in neutres_par_nature
            and not NEUTRES.search(b)
            and b not in noms
        ]
        if communs:
            fautes.append((chemin_nl, langue, len(communs), len(nl), communs))

    if not vues:
        print("langue servie : aucune page néerlandaise dans ce build", file=sys.stderr)
        return 0
    # Une famille à segment variable compte pour UNE surface, pas pour ses trente échantillons.
    def _surface(chemin: str) -> str:
        for nl, _, _ in _trios():
            if ":id" in nl:
                avant, apres = nl.split(":id", 1)
                if chemin.startswith(avant) and chemin.endswith(apres):
                    return nl
        return chemin

    toutes = {_surface(f[0]) for f in fautes}
    # Une exemption déclarée sort du COMPTE, jamais de la VUE.
    exemptees = sorted(s for s in toutes if s in EXEMPTIONS_NL)
    surfaces = {s for s in toutes if s not in EXEMPTIONS_NL}
    for s in exemptees:
        print(f"  exemptée — {s:40} {EXEMPTIONS_NL[s]}")
    disparues = sorted(s for s in EXEMPTIONS_NL if s not in toutes)
    if disparues:
        print(
            "  bonne nouvelle : ces surfaces sont propres et leur exemption ne sert plus — "
            + ", ".join(disparues) + " (retirez-les de EXEMPTIONS_NL)"
        )
    if len(surfaces) > DETTE_SURFACES_NL:
        print(
            f"langue servie : {len(surfaces)} surfaces néerlandaises reprennent le texte "
            f"d'une autre langue, la dette déclarée est {DETTE_SURFACES_NL} — une surface "
            f"vient de régresser :",
            file=sys.stderr,
        )
    elif len(surfaces) < DETTE_SURFACES_NL:
        print(
            f"langue servie : bonne nouvelle, et le compte doit suivre — plus que "
            f"{len(surfaces)} surfaces (déclaré : {DETTE_SURFACES_NL}). Abaissez "
            f"DETTE_SURFACES_NL à {len(surfaces)} dans ce fichier.",
            file=sys.stderr,
        )
    if fautes:
        print(
            f"  détail — {len({f[0] for f in fautes})} page(s) sur {len(vues)} examinée(s) :",
            file=sys.stderr,
        )
        for chemin, langue, n, total, communs in sorted(fautes, key=lambda x: -x[2]):
            print(
                f"  {chemin:44} {n:4} bloc(s) sur {total} en {langue.upper()}",
                file=sys.stderr,
            )
            for b in sorted(communs, key=len, reverse=True)[:2]:
                print(f"       · {b[:100]}", file=sys.stderr)
        # Une amélioration ne BLOQUE pas une mise en ligne — elle la commente. Seule une
        # régression refuse de partir : c'est la différence entre un cliquet de suite de
        # tests (qui doit casser pour qu'on mette le compte à jour) et une barrière de
        # déploiement (qui ne doit refuser que ce qui est plus mauvais qu'annoncé).
        return 1 if len(surfaces) > DETTE_SURFACES_NL else 0
    print(
        f"✓ langue servie : les {len(vues)} pages néerlandaises ne reprennent aucun bloc "
        f"français ni anglais"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
