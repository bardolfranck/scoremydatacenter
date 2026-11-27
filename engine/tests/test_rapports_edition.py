# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""La vitrine des rapports ne présente que ce qu'elle sert, et chaque rapport dit sa date.

🔴 CE QUE CE GARDE A TROUVÉ À SA NAISSANCE (2026-11-27). La page « Bibliothèque » servait
depuis le 2026-07-14 une maquette : dix entrées fictives (« Data centers in Gallia — lorem
ipsum patria »), des prix d'exemple, des boutons « Rapport complet » sans rapport, et un
titre de page qui disait « (maquette) ». Trois rapports réels au milieu. Un lecteur y a vu
du latin et a conclu que le site n'était pas fini. Personne ne l'avait signalé en quatre
mois : la maquette était étiquetée, donc chacun la croyait inoffensive.

Deux règles, décidées par Franck le 2026-11-27 :
  · la vitrine ne liste que des rapports servis — pas de catalogue d'intentions ;
  · une édition est archivée six mois après son gel, ou dès que le corpus européen a doublé.
"""
import re

from engine.core import REPO_ROOT

SITE = REPO_ROOT / "site"
ETAT = SITE / "src" / "config" / "reportStatus.ts"
REGISTRE = SITE / "functions" / "_shared" / "reports.ts"
VITRINE = [
    SITE / "src" / "components" / "LibraryRevue.astro",
    SITE / "src" / "pages" / "fr" / "bibliotheque.astro",
    SITE / "src" / "pages" / "intelligence.astro",
    SITE / "src" / "pages" / "nl" / "bibliotheek.astro",
]
# Ce qui trahit une maquette servie. Cherché dans le CODE, pas dans les commentaires : le
# commentaire de LibraryRevue raconte justement l'histoire de la maquette retirée.
FICTION = re.compile(r"lorem|ipsum|maquette|mockup|fictif|fictional|exemple fictif", re.I)


def _sans_commentaires(texte: str) -> str:
    texte = re.sub(r"/\*.*?\*/", "", texte, flags=re.S)
    texte = re.sub(r"<!--.*?-->", "", texte, flags=re.S)
    return "\n".join(re.sub(r"(^|\s)//.*$", "", ligne) for ligne in texte.splitlines())


def test_la_vitrine_ne_sert_aucune_entree_fictive():
    for chemin in VITRINE:
        code = _sans_commentaires(chemin.read_text(encoding="utf-8"))
        trouve = FICTION.findall(code)
        assert not trouve, f"{chemin.relative_to(REPO_ROOT)} sert encore de la maquette : {trouve[:3]}"


def test_les_composants_de_la_maquette_ne_reviennent_pas():
    for nom in ("config/library.ts", "components/LibraryIndex.astro",
                "components/LibraryCard.astro", "components/LibraryTeaser.astro"):
        assert not (SITE / "src" / nom).exists(), f"{nom} est revenu — la vitrine n'en a plus besoin"


def test_chaque_rapport_du_registre_a_son_edition():
    """Un rapport livrable sans date de gel serait servi comme s'il parlait d'aujourd'hui."""
    servis = set(re.findall(r'slug:\s*"([^"]+)"', REGISTRE.read_text(encoding="utf-8")))
    bloc = re.search(r"REPORT_EDITIONS[^=]*=\s*\{(.*?)\n\};", ETAT.read_text(encoding="utf-8"), re.S)
    assert bloc, "REPORT_EDITIONS introuvable dans reportStatus.ts"
    editions = set(re.findall(r'^\s*"?([a-z-]+)"?:\s*\{\s*frozen:', bloc.group(1), re.M))
    assert servis, "aucun rapport lu dans le registre de livraison"
    assert servis <= editions, f"rapports sans édition datée : {sorted(servis - editions)}"
    for date in re.findall(r'frozen:\s*"([^"]+)"', bloc.group(1)):
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", date), date


def test_la_regle_de_fin_de_vie_est_celle_decidee():
    """Six mois OU doublement du corpus européen (Franck, 2026-11-27). La changer est une
    décision éditoriale : elle passe par Franck avant la PR, pas par ce fichier."""
    texte = ETAT.read_text(encoding="utf-8")
    assert re.search(r"EDITION_MAX_MONTHS\s*=\s*6;", texte)
    assert re.search(r"EDITION_MAX_GROWTH\s*=\s*2;", texte)
    # L'absence de corpus au build ne vaut jamais un doublement.
    assert "corpusNow !== null &&" in texte
