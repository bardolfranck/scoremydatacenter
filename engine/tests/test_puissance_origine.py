# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Une puissance ne se sert jamais nue — et le mot de sa provenance n'existe qu'une fois.

🔴 CE QUI S'EST PASSÉ LE 2026-11-07. En vérifiant les 6 000 MW du projet Matador avant de les
écrire dans un titre de SERP, j'ai cherché leur source : il n'y en a aucune. Mesuré ensuite
sur le corpus SERVI (3 292 fiches, accesseur) : 349 fiches portent une puissance, **aucune
n'est mesurée** (133 « annoncé », 92 « estimé », 124 sans rien), et l'affichage ne
distinguait QUE « estimé ». Donc 257 chiffres de presse étaient servis avec l'autorité d'une
mesure — dont les QUATRE que la page d'accueil met en vitrine (10 000, 10 000, 9 000, 6 000),
tous dans le lot sans qualificatif.

Le commentaire du code énonçait pourtant la règle — « never served as a bare fact » — et sa
mise en œuvre couvrait un cas sur trois. Une règle énoncée et appliquée au tiers est pire
qu'une règle absente : elle rassure [[gate-qui-depasse-son-mandat]].

CE QUE GARDENT CES TESTS, et ce qu'ils ne gardent pas :
· qu'aucune surface servie n'imprime `power_mw` sans passer par la dérivation commune ;
· que le vocabulaire de la provenance est le MÊME des deux côtés — `engine/puissance.py`
  écrit `non_documente`, le module d'affichage doit lire ce mot-là et pas un synonyme ;
· que le libellé existe dans les trois langues servies ;
· que le producteur TRANSPORTE la provenance : un champ absent se lit comme un état, et
  l'exemplaire de la page chiffres voyageait sans elle — les 221 puissances françaises,
  qualifiées dans la donnée, se seraient affichées « non sourcé » [[absence-ressemble-a-zero]].

Ils ne garantissent PAS que les 124 trous se referment : c'est le travail des filières US et
NL. Ils garantissent qu'on ne les présente plus comme des mesures.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_SRC = REPO_ROOT / "site" / "src"
REGLE = SITE_SRC / "config" / "puissance.ts"

# Les surfaces SERVIES : ce qui finit en HTML ou en image sous les yeux d'un lecteur.
SURFACES = ("components", "pages")

# Les fichiers qui manipulent la puissance sans jamais l'AFFICHER. Nommés, pas devinés.
SANS_AFFICHAGE = {
    # Le tri de la colonne puissance : une clé de tri n'est pas une phrase.
    "components/Ranking.astro": "data-k-power est une clé de tri, pas un affichage",
    # Le dossier environnemental liste des champs d'un formulaire réglementaire dont les
    # noms contiennent « power_mw » (`backup_generator_unit_power_mw`…) : ce sont des
    # CLÉS de dossier déclaratif, pas notre champ `identity.power_mw`.
    "components/DossierEnvironnemental.astro": "énumère des clés de formulaire réglementaire",
}


def _fichiers_servis() -> list[Path]:
    fichiers: list[Path] = []
    for dossier in SURFACES:
        racine = SITE_SRC / dossier
        if not racine.is_dir():
            continue
        for f in racine.rglob("*"):
            if f.is_file() and f.suffix in {".astro", ".ts", ".tsx"}:
                fichiers.append(f)
    assert len(fichiers) > 50, (
        f"seulement {len(fichiers)} surfaces trouvées sous {SURFACES} — "
        "un contrôle sur un ensemble vide passe toujours"
    )
    return fichiers


def test_la_regle_commune_existe_et_nomme_les_quatre_etats():
    assert REGLE.is_file(), f"{REGLE} manque — la dérivation commune est le pivot du reste"
    src = REGLE.read_text(encoding="utf-8")
    for etat in ("measured", "announced", "estimated", "non_documente"):
        assert f'"{etat}"' in src, f"l'état {etat} n'est pas nommé dans la règle commune"


def test_le_mot_du_quatrieme_etat_est_celui_du_moteur():
    """Deux vocabulaires pour un même état, c'est une liste tenue à deux endroits."""
    moteur = (REPO_ROOT / "engine" / "puissance.py").read_text(encoding="utf-8")
    m = re.search(r'"origine":\s*i\.get\("power_mw_status"\)\s*or\s*"([a-z_]+)"', moteur)
    assert m, (
        "le moteur ne nomme plus le quatrième état là où ce test le cherche "
        "(engine/puissance.py, clé « origine ») — vérifier avant de relâcher"
    )
    mot = m.group(1)
    src = REGLE.read_text(encoding="utf-8")
    assert f'"{mot}"' in src, (
        f"le moteur écrit « {mot} » et l'affichage ne le lit pas : un état du moteur "
        "tomberait silencieusement dans le cas par défaut"
    )


def test_le_libelle_existe_dans_les_trois_langues_servies():
    src = REGLE.read_text(encoding="utf-8")
    # On lit le bloc LIBELLES, pas tout le fichier : un commentaire ne libelle rien.
    bloc = src[src.index("const LIBELLES"):src.index("/** La provenance d'une puissance")]
    for etat in ("announced", "estimated", "non_documente"):
        ligne = [l for l in bloc.splitlines() if l.strip().startswith(f"{etat}:")]
        assert ligne, f"aucun libellé pour {etat}"
        for langue in ("fr:", "en:", "nl:"):
            assert langue in ligne[0], (
                f"le libellé de {etat} ne dit rien en {langue[:-1]} — une langue à moitié "
                "remplie se lit comme une langue complète"
            )


def test_aucune_surface_n_imprime_la_puissance_sans_la_regle():
    """Le test juge l'AFFICHAGE, pas la lecture : une clé de tri reste autorisée."""
    fautes: list[str] = []
    for f in _fichiers_servis():
        rel = f.relative_to(SITE_SRC).as_posix()
        src = f.read_text(encoding="utf-8")
        if "power_mw" not in src:
            continue
        if rel in SANS_AFFICHAGE:
            continue
        if "puissanceServie" in src:
            continue
        fautes.append(rel)
    assert not fautes, (
        "ces surfaces servent une puissance sans passer par config/puissance.ts :\n  - "
        + "\n  - ".join(fautes)
        + "\n→ soit elles lisent la dérivation commune, soit elles se déclarent dans "
          "SANS_AFFICHAGE avec la raison. Un chiffre nu se lit comme une mesure."
    )


def test_le_producteur_transporte_la_provenance():
    """Un champ absent se lit comme un état : l'exemplaire doit porter sa provenance."""
    stats = (REPO_ROOT / "engine" / "stats.py").read_text(encoding="utf-8")
    bloc = stats[stats.index('"power_mw": ident.get("power_mw")'):]
    bloc = bloc[: bloc.index("}")]
    assert '"power_mw_status"' in bloc, (
        "l'exemplaire de la page chiffres embarque `power_mw` sans `power_mw_status` : "
        "l'affichage rendrait « non sourcé » pour les puissances pourtant qualifiées"
    )


def test_le_corpus_servi_n_a_aucune_puissance_mesuree():
    """Le constat qui justifie tout le dispositif — et qui doit SE VOIR s'il change.

    Si une puissance mesurée apparaît un jour, ce test tombe, et c'est le bon moment pour
    relire la règle : `measured` est le seul état qui s'affiche sans qualificatif.
    """
    from engine.core import datacenter_paths  # import tardif : chemin de corpus

    cal = REPO_ROOT.parent / "smdc-newsroom" / "calibration"
    if not cal.is_dir():
        import pytest

        pytest.skip("corpus privé absent de cette copie")
    etats: dict[str, int] = {}
    for p in datacenter_paths(cal):
        ident = json.loads(p.read_text(encoding="utf-8")).get("identity") or {}
        if not isinstance(ident.get("power_mw"), (int, float)):
            continue
        etats[ident.get("power_mw_status") or "non_documente"] = (
            etats.get(ident.get("power_mw_status") or "non_documente", 0) + 1
        )
    assert etats, "aucune puissance trouvée dans le corpus servi — contrôle sur le vide"
    assert "measured" not in etats, (
        f"une puissance MESURÉE est apparue ({etats}) — relire la règle d'affichage : "
        "c'est le seul état servi sans qualificatif, et il ne l'avait jamais été"
    )


def test_la_provenance_et_le_champ_servi_disent_la_meme_chose():
    """Une source enregistrée qui n'atteint pas la page est pire qu'une source absente.

    🔴 TROUVÉ LE 2026-11-07, une heure après le dispositif. La filière WORLD a sourcé la
    puissance de Matador (dépôt SEC du 2025-08-06) et l'a écrite dans le `.provenance.json`
    avec `"status": "announced"` — mais pas dans `identity.power_mw_status`, le SEUL champ
    que la chaîne servie lit. Résultat : la page allait afficher « non sourcé » sur le
    chiffre le plus documenté du corpus, et l'afficher à cause de MON dispositif.

    C'est une liste tenue à deux endroits [[liste-a-deux-endroits-ment]], avec le piège en
    plus : le désaccord est INVISIBLE tant qu'on ne regarde qu'un côté. Le test confronte
    les deux fichiers, ce qui est la seule lecture qui le voit.
    """
    import pytest

    cal = REPO_ROOT.parent / "smdc-newsroom" / "calibration"
    if not cal.is_dir():
        pytest.skip("corpus privé absent de cette copie")
    from engine.core import datacenter_paths

    desaccords = []
    vus = 0
    for chemin in datacenter_paths(cal):
        fiche = json.loads(chemin.read_text(encoding="utf-8"))
        ident = fiche.get("identity") or {}
        if not isinstance(ident.get("power_mw"), (int, float)):
            continue
        prov = chemin.with_name(chemin.name.replace(".json", ".provenance.json"))
        if not prov.is_file():
            continue
        entree = (json.loads(prov.read_text(encoding="utf-8")) or {}).get("power_mw")
        if not isinstance(entree, dict):
            continue
        statut_source = entree.get("status")
        if not statut_source:
            continue
        vus += 1
        if ident.get("power_mw_status") != statut_source:
            desaccords.append(
                f"{fiche.get('id')} : la provenance dit « {statut_source} », "
                f"identity.power_mw_status dit « {ident.get('power_mw_status')} »"
            )
    assert vus, (
        "aucune fiche ne porte de provenance de puissance — ce contrôle passe sur le vide, "
        "et un contrôle vide ment [[gate-qui-depasse-son-mandat]]"
    )
    assert not desaccords, (
        "la source est enregistrée et la page servie ne la verra pas :\n  - "
        + "\n  - ".join(desaccords)
        + "\n→ écrire le statut dans `identity.power_mw_status`, le champ que lit la chaîne "
          "servie. Le `.provenance.json` documente, il n'affiche pas."
    )
