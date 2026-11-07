# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Un ratio dont les facteurs vivent dans une phrase n'est vérifiable par personne.

🔴 MESURÉ LE 2026-11-07 sur les 305 fiches du corpus servi qui portent un L2 chiffré :
**302 avaient leur dénominateur dans le TITRE DE SOURCE**, zéro dans un champ, et **3 nulle
part** (`fr-dataone`, `fr-colt-paris-sw`, `fr-colt-paris-sw-dh10`). Les trois ne sont pas
passées par négligence : rien ne pouvait les refuser. Mon propre balayage les a d'abord
ratées en cherchant une clé de provenance — et un balayage qui rate est la meilleure preuve
qu'un champ manque.

Deux conséquences qui ont décidé ce changement, et qui ne sont pas cosmétiques :
· la calibration doit montrer à Franck le DELTA DES LETTRES avant qu'il signe une grille
  neuve ; ça suppose de recalculer 305 ratios par machine, pas de parser du français ;
· le champ `population` qui existe dans 1 710 provenances n'est PAS celui du calcul — aucun
  L2 n'en dérive. Deux populations, deux rôles, aucune ne faisait foi
  [[liste-a-deux-endroits-ment]].

⚠️ CE QUE CES TESTS NE FONT PAS. Ils ne vérifient pas que les facteurs sont REMPLIS : aucune
fiche ne les porte encore, et un garde qui exige un champ que personne n'écrit bloque tout le
corpus. L'ordre convenu avec la calibration est : schéma → filières écrivent → garde
d'exigence. Ce fichier tient les deux premières marches, et prépare la troisième en vérifiant
que le CONTRÔLEUR fonctionne même quand il n'a rien à contrôler.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA = REPO_ROOT / "data" / "schema" / "datacenter.schema.json"
FACTEURS = ("power_mw", "local_population", "population_base", "population_vintage")


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_les_quatre_facteurs_sont_declares_et_l_entree_reste_stricte():
    ind = _schema()["$defs"]["indicator"]
    assert ind.get("additionalProperties") is False, (
        "l'entrée d'indicateur n'est plus stricte — n'importe quelle clé passerait, et c'est "
        "justement la rigueur qui fait qu'un facteur mal nommé est REFUSÉ au lieu d'être servi"
    )
    manquants = [f for f in FACTEURS if f not in ind["properties"]]
    assert not manquants, f"facteurs non déclarés : {manquants}"


def test_la_base_du_denominateur_est_un_enum_ferme():
    base = _schema()["$defs"]["indicator"]["properties"]["population_base"]
    assert "enum" in base, (
        "`population_base` doit être un enum FERMÉ : c'est la clé qui dissout la polysémie, "
        "une chaîne libre la recréerait"
    )
    assert set(base["enum"]) == {"place", "county_unincorporated", "radius"}


def test_le_rayon_separe_sa_nature_de_son_reglage():
    """`radius_10km` aurait fait d'un RÉGLAGE une migration — et un libellé par rayon.

    La base dit la NATURE, un champ à part dit le RÉGLAGE. Même famille que la constante
    encodée dans un nom : on ne peut plus la changer sans réécrire la donnée.
    """
    props = _schema()["$defs"]["indicator"]["properties"]
    assert "population_radius_km" in props, "le réglage du rayon n'a pas de champ à lui"
    encodees = [v for v in props["population_base"]["enum"] if "km" in v]
    assert not encodees, (
        f"valeur(s) d'enum encodant un rayon : {encodees} — changer R deviendrait une "
        "migration de données et un libellé de plus à traduire"
    )


def test_le_millesime_est_une_annee_bornee_pas_une_chaine():
    """Un millésime sans date ne reproduit rien — et une chaîne en autorise trois écritures.

    Première version de ce champ : une chaîne avec un motif exigeant quatre chiffres
    (« Census 2020 »). La calibration a tranché mieux, et pour une raison que j'avais
    manquée : la SOURCE vit déjà en provenance, donc la répéter dans le millésime crée deux
    autorités pour un même fait [[liste-a-deux-endroits-ment]] — tandis que « Census 2020 »,
    « census 2020 » et « 2020 Census » sont trois écritures d'un seul nombre.
    """
    champ = _schema()["$defs"]["indicator"]["properties"]["population_vintage"]
    assert "integer" in champ["type"], (
        "le millésime doit être une ANNÉE entière : une chaîne autorise plusieurs écritures "
        "du même fait, et redonde la source déjà portée par la provenance"
    )
    assert champ["minimum"] >= 1990 and champ["maximum"] <= 2035, (
        "l'année doit être bornée, sinon 20 ou 202 passent pour un millésime"
    )
    assert "pattern" not in champ, "un motif de chaîne n'a plus de sens sur un entier"


def test_aucun_champ_ne_stocke_le_ratio():
    """Le ratio DÉRIVE de ses deux facteurs. Stocké, il devient une troisième autorité."""
    props = _schema()["$defs"]["indicator"]["properties"]
    stockes = [k for k in props if "ratio" in k.lower()]
    assert not stockes, (
        f"champ(s) de ratio déclaré(s) : {stockes} — un ratio stocké peut contredire ses "
        "facteurs, et alors plus personne ne sait lequel fait foi"
    )


def test_aucune_valeur_d_enum_du_schema_ne_porte_d_accent():
    """🔴 LE PIÈGE ÉVITÉ DE JUSTESSE. La calibration proposait un état `site_isolé`.

    Une valeur d'enum accentuée est une valeur qu'on ne grep pas du premier coup, qui voyage
    mal en URL et en en-tête, et qui ne ressemble à aucune autre du dépôt (`non_documente`,
    `county_unincorporated`, `not_collected` — toutes ASCII). Et surtout : les valeurs
    d'enum FINISSENT À L'ÉCRAN quand un libellé manque, famille de défaut déjà vue cinq fois
    ici. Ce test refuse la première.
    """
    fautives = []

    def visiter(noeud, chemin=""):
        if isinstance(noeud, dict):
            for valeur in noeud.get("enum", []) or []:
                if isinstance(valeur, str) and not valeur.isascii():
                    fautives.append(f"{chemin} → {valeur!r}")
            for cle, sous in noeud.items():
                visiter(sous, f"{chemin}/{cle}")
        elif isinstance(noeud, list):
            for i, sous in enumerate(noeud):
                visiter(sous, f"{chemin}[{i}]")

    visiter(_schema())
    assert not fautives, (
        "valeur(s) d'enum non ASCII dans le schéma public :\n  - "
        + "\n  - ".join(fautives)
        + "\n→ écrire la valeur en ASCII (`site_isole`) et mettre l'accent dans le LIBELLÉ, "
          "qui est traduit, pas dans la clé, qui est une donnée."
    )


def _ratios_incoherents(fiches) -> list[str]:
    """Les L2 dont les facteurs ne redonnent pas la valeur servie. Le contrôleur de la
    marche 3, écrit maintenant pour qu'il soit TESTÉ avant d'avoir du grain à moudre."""
    fautes = []
    for fiche in fiches:
        for entree in fiche.get("indicators") or []:
            if (entree.get("code") or entree.get("id")) != "L2":
                continue
            mw, pop, val = (entree.get("power_mw"), entree.get("local_population"),
                            entree.get("value"))
            if not (isinstance(mw, (int, float)) and isinstance(pop, int) and pop > 0
                    and isinstance(val, (int, float))):
                continue
            attendu = mw / pop * 1000
            if abs(attendu - val) > max(0.01, abs(val) * 0.001):
                fautes.append(
                    f"{fiche.get('id')} : {mw} MW / {pop} hab × 1000 = {attendu:.4f}, "
                    f"mais la valeur servie est {val}")
    return fautes


def test_le_controleur_de_ratio_attrape_une_incoherence_fabriquee():
    """Un contrôle qui n'a rien à contrôler doit quand même prouver qu'il mord."""
    bon = {"id": "zz-bon", "indicators": [
        {"id": "L2", "status": "measured", "value": 29.9412,
         "power_mw": 6000, "local_population": 200393}]}
    faux = {"id": "zz-faux", "indicators": [
        {"id": "L2", "status": "measured", "value": 29.9412,
         "power_mw": 6000, "local_population": 100000}]}
    assert _ratios_incoherents([bon]) == []
    assert len(_ratios_incoherents([faux])) == 1


def test_aucun_L2_servi_ne_contredit_ses_propres_facteurs():
    """Vrai aujourd'hui sur l'ensemble VIDE — et le test le DIT, au lieu de rassurer."""
    cal = REPO_ROOT.parent / "smdc-newsroom" / "calibration"
    if not cal.is_dir():
        pytest.skip("corpus privé absent de cette copie")
    from engine.core import datacenter_paths

    fiches = [json.loads(p.read_text(encoding="utf-8")) for p in datacenter_paths(cal)]
    porteuses = [f for f in fiches
                 if any((e.get("code") or e.get("id")) == "L2" and "local_population" in e
                        for e in f.get("indicators") or [])]
    fautes = _ratios_incoherents(fiches)
    assert not fautes, "un L2 servi contredit ses facteurs :\n  - " + "\n  - ".join(fautes)
    if not porteuses:
        # L'absence de matière est l'état ATTENDU tant que les filières n'ont pas écrit.
        # On l'affirme explicitement : sinon ce test passera encore le jour où le champ
        # sera écrit DE TRAVERS et où plus personne ne saura qu'il n'a jamais rien vu.
        assert fautes == [], "contrôle sur l'ensemble vide — aucune fiche ne porte encore ses facteurs"
