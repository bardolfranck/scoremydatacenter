# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Un rapport retiré n'est plus annoncé : le menu ne le met plus en vitrine.

🔴 CE QUE CE GARDE A TROUVÉ À SA NAISSANCE (2026-11-05). Le rapport Pays-Bas avait été
retiré le 7 octobre — le registre Seveso national avait fait tomber les deux notes A sur
lesquelles le document était BÂTI, donc son cadrage et non un passage. Trois surfaces
avaient tiré la conséquence : la fonction de livraison répond 410, l'aperçu a été remplacé
par la note de retrait, la prise d'adresse refuse. Le MENU, lui, l'annonçait encore sur
chaque page du site, dans les deux langues — « Rapport — Les Pays-Bas » et « Netherlands
report » — et la page continuait de le vendre.

Ce qui rend ce défaut durable : trois surfaces sur quatre avaient raison. La correction
avait été faite là où on regarde (le fichier), pas là où on passe (le menu).

CE QUE CE TEST PEUT ET NE PEUT PAS. Il tient la partie DÉCIDABLE SUR LES SOURCES : aucune
adresse d'un rapport retiré dans la table du menu. Ce que la page SERT — la maquette de
couverture, le sommaire, le chiffre d'accroche, le formulaire — n'existe que dans
l'artefact, et la CI ne construit pas : c'est `scripts/check_rapport_retire.py`, barrière
de `make deploy`, qui le voit. Les deux lisent la MÊME table d'état.
"""
import pytest

from engine.core import REPO_ROOT
from engine.tests.i18n_table import bloc, chemins

import scripts.check_rapport_retire as C

TABLE = C.TABLE_ETAT.read_text(encoding="utf-8")
MENU = C.MENU.read_text(encoding="utf-8")


def test_les_deux_lectures_de_la_table_d_etat_disent_la_meme_chose():
    """La barrière lit la table d'état avec son propre analyseur : il doit dire la même
    chose que celui de la table de chaînes, déjà éprouvé. Deux lectures d'accord valent
    mieux qu'une lecture seule — un analyseur qui se trompe en SILENCE trouve zéro rapport
    retiré, et un contrôle sur zéro rapport passe toujours."""
    par_chemins = {
        chemin.split(".")[0]
        for chemin in chemins(bloc(TABLE, "REPORT_STATUS"))
        if chemin.endswith(".withdrawn")
    }
    assert C.slugs_retires(TABLE) == par_chemins, (
        f"l'analyseur de la barrière voit {sorted(C.slugs_retires(TABLE))}, celui de la "
        f"table de chaînes {sorted(par_chemins)}"
    )
    assert par_chemins, (
        "aucun rapport retiré dans la table d'état : si c'est vrai, ce fichier de test n'a "
        "plus d'objet ; si c'est faux, la lecture est cassée et tous les contrôles qui "
        "suivent passent sur l'ensemble vide"
    )


@pytest.mark.parametrize("slug", sorted(C.slugs_retires(TABLE)))
def test_un_rapport_retire_garde_une_adresse_servie(slug):
    """Le PÉRIMÈTRE du contrôle, avant son verdict. Un rapport retiré garde sa page : elle
    porte la note datée, et c'est elle qui adresse les copies déjà téléchargées. Si plus
    aucune page ne porte le slug, l'adresse rend un 404 — qui ne rétracte rien — et le
    contrôle du menu ci-dessous n'a plus rien à comparer."""
    assert C.urls_servies(slug), (
        f"{slug} est retiré mais aucune page ne passe `report=\"{slug}\"` au gabarit : "
        f"l'adresse ne répond plus, ou le slug a changé de nom d'un côté seulement"
    )


def test_un_rapport_retire_ne_reste_pas_au_menu():
    """Présenter un rapport, c'est le servir — et le menu est sur chaque page du site."""
    fautifs = C.menu_fautif(TABLE, MENU)
    assert not fautifs, "\n".join(
        f"{slug} est retiré et {C.MENU.name} annonce encore {url}" for slug, url in fautifs
    ) + (
        "\n\nUn rapport retiré se retire du menu. Son adresse continue de répondre et de "
        "porter la note datée — on la trouve par la bibliothèque et par la recherche."
    )


def test_le_garde_du_menu_mord_vraiment(tmp_path):
    """Le garde confronté à la faute qu'il est né pour voir : la table du 7 octobre, et le
    menu d'avant le 5 novembre. Sans cette épreuve, un analyseur qui ne trouve plus la
    table — renommée, déplacée — rendrait une liste vide, et une liste vide est un succès."""
    table = """
export const REPORT_STATUS: Record<string, ReportStatus> = {
  nederland: {
    withdrawn: { since: "2026-10-07", fr: "Rapport retiré.", en: "Report withdrawn." },
  },
  "big-tech": {
    erratum: { since: "2026-10-07", fr: "Errata.", en: "Erratum." },
  },
};
"""
    menu = """
export const FR_NAV: NavNode[] = [
  { href: "/fr/rapports/france/", label: "Rapport — La France" },
  { href: "/fr/rapports/nederland/", label: "Rapport — Les Pays-Bas" },
];
export const EN_NAV: NavNode[] = [
  { href: "/reports/big-tech/", label: "Big Tech-AI report" },
];
"""
    pages = tmp_path / "pages"
    (pages / "fr" / "rapports").mkdir(parents=True)
    (pages / "reports").mkdir(parents=True)
    (pages / "fr" / "rapports" / "nederland.astro").write_text(
        '<ReportDownload lang="fr" report="nederland" />', encoding="utf-8"
    )
    (pages / "reports" / "nederland.astro").write_text(
        '<ReportDownload lang="en" report="nederland" />', encoding="utf-8"
    )
    (pages / "reports" / "big-tech.astro").write_text(
        '<ReportDownload lang="en" report="big-tech" />', encoding="utf-8"
    )

    assert C.slugs_retires(table) == {"nederland"}, "le retrait doit se lire, l'errata non"
    assert C.urls_servies("nederland", pages) == {
        "/fr/rapports/nederland/",
        "/reports/nederland/",
    }, "les deux adresses du rapport se dérivent du nom de fichier, barre finale comprise"
    assert C.menu_fautif(table, menu, pages) == [
        ("nederland", "/fr/rapports/nederland/")
    ], "le menu FR annonce le rapport retiré : le garde doit le nommer, et lui seul"
    # Et il se taira dès que le menu sera corrigé — un garde qui crie toujours ne garde rien.
    assert C.menu_fautif(table, menu.replace('"/fr/rapports/nederland/"', '"/fr/actu/"'), pages) == []


def test_la_barriere_est_bien_une_barriere_de_deploy():
    """Le contrôle de l'artefact ne sert à rien s'il n'est pas lancé. Il tourne dans
    `make deploy`, après le build et avant l'envoi — comme ses voisins, et pour la même
    raison : la suite de tests tourne avant le build, la CI ne construit pas."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    deploy = makefile.split("\ndeploy:", 1)[1].split("wrangler pages deploy", 1)[0]
    assert "scripts/check_rapport_retire.py" in deploy, (
        "`make deploy` ne lance pas scripts/check_rapport_retire.py : la barrière existe "
        "et personne ne la franchit"
    )
