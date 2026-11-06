# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le CONTRAT DE DONNÉE accepte-t-il toutes les langues déclarées, ou seulement quatre fois
sur cinq ?

🔴 CE QUE CE GARDE A TROUVÉ LE JOUR OÙ IL A ÉTÉ ÉCRIT (2026-11-06). Le néerlandais avait
été ouvert dans le schéma à QUATRE endroits — `synthesis.site`, `synthesis.site.lead`,
`synthesis.project_process`, `synthesis.project_process.lead` — et PAS au cinquième,
`identity.summary`. Rien ne l'a vu : la suite était verte, les 370 tests passaient, et
`identity.summary` n'a parlé qu'au moment où les 151 fiches traduites sont arrivées dans le
corpus. Le déploiement s'est arrêté sur 151 fiches invalides, et il s'est arrêté AU BON
ENDROIT — avant le build, avant la publication. Mais il s'est arrêté chez Franck, en pleine
mise en ligne, sur un défaut vieux de la veille.

LA FAUTE N'EST PAS L'OUBLI, C'EST LA LISTE TENUE À LA MAIN. Ouvrir une langue, c'était
retrouver tous les objets par-langue du schéma et les élargir un par un — un geste qui
réussit à 80 % et dont le reliquat ne se voit qu'à l'exécution
[[liste-a-deux-endroits-ment]]. Le garde ne garde donc pas `nl` : il garde l'UNIFORMITÉ. Tout
objet du schéma qui porte `fr` et `en` doit porter les langues déclarées par
`site/src/content/langues.ts`, la source unique [[producteur-ecrit-un-champ-par-langue]].

CE QU'IL NE GARDE PAS, ET POURQUOI. Il n'exige pas qu'une langue soit REMPLIE : une fiche
texane ne porte pas de prose néerlandaise, et c'est voulu — la prose d'une langue est due sur
les fiches de SON pays. `required` reste donc `fr` + `en`, et une langue ouverte est
seulement ACCEPTÉE. Le garde vérifie aussi `additionalProperties: false`, sans quoi il ne
garderait rien : un objet ouvert accepterait `nl` sans le déclarer, et accepterait aussi
`n1`.
"""

import json
from pathlib import Path

from engine.langues import langues_declarees

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA = REPO_ROOT / "data" / "schema" / "datacenter.schema.json"

# Le relevé a trouvé 6 objets par-langue le jour où il a été écrit. Le minimum est déclaré
# pour qu'un analyseur qui se tromperait en silence ne rende pas ZÉRO objet : un contrôle sur
# l'ensemble vide passe toujours [[jeu-de-validation-perimetre-et-sens]].
OBJETS_PAR_LANGUE_ATTENDUS = 6


def _objets_par_langue(schema: dict) -> dict[str, dict]:
    """Tout nœud du schéma dont les `properties` portent `fr` ET `en`.

    Reconnu par sa FORME, jamais par son nom : `summary`, `label`, `lead` et le corps des
    piliers n'ont aucun mot en commun [[cle-polyseme-travailler-par-paire]].
    """
    trouves: dict[str, dict] = {}

    def descend(noeud: object, chemin: str) -> None:
        if not isinstance(noeud, dict):
            return
        props = noeud.get("properties")
        if isinstance(props, dict) and {"fr", "en"} <= set(props):
            trouves[chemin or "root"] = noeud
        for cle, valeur in noeud.items():
            if cle in ("properties", "definitions", "$defs", "patternProperties"):
                if isinstance(valeur, dict):
                    for nom, sous in valeur.items():
                        descend(sous, f"{chemin}.{nom}")
            elif cle in ("items", "additionalProperties"):
                if isinstance(valeur, dict):
                    descend(valeur, f"{chemin}[]")
            elif cle in ("oneOf", "anyOf", "allOf") and isinstance(valeur, list):
                for i, sous in enumerate(valeur):
                    descend(sous, f"{chemin}|{i}")

    descend(schema, "")
    return trouves


def _langues_du_noeud(noeud: dict) -> set[str]:
    """Les clés de langue d'un objet par-langue : les codes à deux lettres, pas `lead`."""
    return {c for c in noeud["properties"] if len(c) == 2 and c.isalpha()}


def test_le_releve_voit_ce_qu_il_doit_voir():
    objets = _objets_par_langue(json.loads(SCHEMA.read_text()))
    assert len(objets) >= OBJETS_PAR_LANGUE_ATTENDUS, (
        f"Le relevé ne trouve que {len(objets)} objet(s) par-langue dans le schéma, alors "
        f"qu'il en existait {OBJETS_PAR_LANGUE_ATTENDUS}. Ce n'est pas le schéma qui a "
        f"maigri, c'est l'analyseur qui est devenu aveugle — et un analyseur aveugle rend "
        f"un garde VERT. Trouvés : {sorted(objets)}"
    )
    assert ".identity.summary" in objets, (
        "Le relevé ne voit plus `identity.summary` — l'objet même qui a bloqué le "
        f"déploiement du 2026-11-06. Trouvés : {sorted(objets)}"
    )


def test_chaque_objet_par_langue_accepte_les_langues_declarees():
    attendues = set(langues_declarees())
    objets = _objets_par_langue(json.loads(SCHEMA.read_text()))
    amputes = {
        chemin: sorted(attendues - _langues_du_noeud(noeud))
        for chemin, noeud in objets.items()
        if attendues - _langues_du_noeud(noeud)
    }
    assert not amputes, (
        "Des objets par-langue du schéma refusent une langue DÉCLARÉE : "
        + ", ".join(f"{c} (manque {', '.join(m)})" for c, m in sorted(amputes.items()))
        + ". Une fiche qui porte cette langue sera REFUSÉE par `validate_corpus`, et le "
        "déploiement s'arrêtera — pas sur un test, sur la mise en ligne."
    )


def test_une_langue_ouverte_nest_pas_une_langue_exigee():
    """Ouvrir `nl` ne doit pas rendre la prose néerlandaise obligatoire sur une fiche texane.

    La prose d'une langue est due sur les fiches de SON pays ; partout ailleurs le repli
    déclaré est la réponse juste, pas un manque.
    """
    objets = _objets_par_langue(json.loads(SCHEMA.read_text()))
    for chemin, noeud in sorted(objets.items()):
        exigees = {c for c in noeud.get("required", []) if len(c) == 2 and c.isalpha()}
        assert exigees == {"fr", "en"}, (
            f"{chemin} exige {sorted(exigees)}. Seuls `fr` et `en` peuvent être exigés : "
            "exiger une langue de pays reviendrait à refuser toutes les fiches des autres "
            "pays."
        )


def test_un_objet_par_langue_est_ferme():
    """Sans `additionalProperties: false`, ce garde ne garde rien.

    Un objet ouvert accepte `nl` sans l'avoir déclaré — donc le garde passerait au vert sur
    un schéma qui ne dit rien. Il accepterait aussi `n1`, et une faute de frappe de langue
    ne se voit NULLE PART : le repli sert l'anglais, sans erreur et sans blanc.
    """
    objets = _objets_par_langue(json.loads(SCHEMA.read_text()))
    ouverts = [c for c, n in objets.items() if n.get("additionalProperties") is not False]
    assert not ouverts, (
        "Ces objets par-langue sont ouverts, donc non gardés : " + ", ".join(sorted(ouverts))
    )


def test_le_garde_mord_vraiment():
    """Confronté au schéma d'AVANT (le néerlandais absent d'`identity.summary`), le garde
    doit nommer ce chemin-là. Un garde qu'on n'a pas vu refuser n'est pas un garde."""
    schema = json.loads(SCHEMA.read_text())
    objets = _objets_par_langue(schema)
    assert objets, "relevé vide : le reste du test ne prouverait rien"

    sommaire = schema["properties"]["identity"]["properties"]["summary"]
    retiree = sorted(set(langues_declarees()) - {"fr", "en"})
    assert retiree, "pas de troisième langue déclarée : rien à retirer, test sans objet"
    for lg in retiree:
        sommaire["properties"].pop(lg, None)

    attendues = set(langues_declarees())
    amputes = [
        chemin
        for chemin, noeud in _objets_par_langue(schema).items()
        if attendues - _langues_du_noeud(noeud)
    ]
    assert amputes == [".identity.summary"], (
        "Le schéma mutilé exactement comme il l'était le 2026-11-06 devrait faire crier le "
        f"garde sur `.identity.summary` et sur lui seul ; il nomme {amputes}."
    )
