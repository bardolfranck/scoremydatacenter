# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Repositionnement d'une fiche SERVIE : corriger sa COORDONNÉE puis re-mesurer UNIQUEMENT ce
qui dépend du point, en conservant tout le reste. Cas d'usage : une fiche dont la coordonnée
était un géocode de commune (centroïde fabriqué, cf. pipelines.geo_audit.centroid_check) et
qu'on recale sur le vrai site.

Pourquoi PAS une ré-onboard complète (build_draft seul) : repartir de zéro EFFACE tout ce que
le pipeline ne reproduit pas — synthèse rédigée, indicateurs saisis à la main (F3, L2, T1, T2),
réponse opérateur. Le repositionnement part de la fiche servie (deepcopy) et n'écrase QUE les
indicateurs fonction du point.

Ce qui est re-mesuré vs conservé :
  · re-mesuré  = collecteurs du SPEC MOINS les nationaux  (W1, F1, L3, W3, L1, W2, F2, E2, E3)
                 + E6 (point-dépendant mais hors collect(), module heat_network, dépend FCU) ;
  · conservé   = nationaux du SPEC (E1, par date — identique partout), champs saisis à la main,
                 indicateurs non collectés, synthèse, publication, score_history.
L'ensemble « national » est LU dans le SPEC (country.national_indicators), jamais recensé ici :
l'information vit à côté du collecteur. Même raisonnement que l'accesseur du périmètre du corpus.

Garde-fou fail-loud : les clés racine ET les id d'indicateurs de la fiche servie doivent être
INCLUS dans ceux du résultat — un repositionnement ne perd jamais rien. Une fiche jamais
re-mesurée ne doit pas ressembler à une fiche saine : si E6 était mesuré et que FCU manque, on
REFUSE (conserver « eloigne » décrirait l'ancien point — ce serait un mensonge).

score_history N'est PAS écrit ici : le schéma le réserve au moteur (grades/confidence requis).
La provenance du recalage se consigne dans calibration/coordinate-provenance/, là où vit la
vérité géo. Le prochain scoring écrira l'entrée score_history.

Sortie dans _held-fr-repos/{id}.json (zone de transit) : agent-codeur-site déplace la fiche
validée dans calibration/datacenters/. On ne touche JAMAIS le corpus servi directement.

Commande (lançable telle quelle) :
  SMDC_FCU_DIR=/chemin/fcu python -m pipelines.spatial.reposition \
      --id fr-mengine --lat 48.9426452 --lon 2.1844594 --newsroom ../smdc-newsroom
"""
from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import os
import sys
from pathlib import Path

from engine.core import datacenter_paths

from . import heat_network
from .collect import FR_SPEC
from .country import build_draft, national_indicators

HELD_DIR = "_held-fr-repos"
# Champs d'identité « vérité servie » qu'un déplacement ne doit PAS écraser. Tout le reste de
# fragment["identity"] est dérivé de la commune (municipality, admin_area…) et suit le point.
_IDENTITE_CONSERVEE = {"name", "operator", "summary", "project_status", "country", "coordinates"}


def _collector_ids(spec: dict) -> set:
    ids: set = set()
    for declared, _fn in spec["collectors"]:
        ids.update(declared)
    return ids


def _data_dir(newsroom) -> Path:
    """Dossier que datacenter_paths globe (il cherche `datacenters*/`). Dans le newsroom c'est
    `calibration/` ; on accepte aussi qu'on pointe directement ce dossier."""
    root = Path(newsroom)
    return root / "calibration" if (root / "calibration").is_dir() else root


def fiche_servie(dc_id: str, newsroom) -> tuple[Path, dict]:
    """Retrouve la fiche servie dans le corpus (accesseur du moteur, pas de glob maison)."""
    for p in datacenter_paths(_data_dir(newsroom)):
        if p.stem == dc_id:
            return p, json.loads(p.read_text())
    raise SystemExit(f"fiche servie introuvable dans le corpus servi : {dc_id}")


def reposition(dc_id: str, lat: float, lon: float, *, newsroom, accessed: str,
               spec: dict = FR_SPEC, fcu_dir=None) -> tuple[dict, dict]:
    """Renvoie (fiche_repositionnée, rapport). Ne touche ni le disque ni le réseau au-delà de
    la re-mesure (build_draft appelle l'API commune ; E6 lit FCU en local)."""
    _src_path, servie = fiche_servie(dc_id, newsroom)
    resultat = copy.deepcopy(servie)
    ident = servie["identity"]

    # 1) re-mesure au NOUVEAU point (collecteurs spatiaux). Nom/opérateur/statut = vérité servie.
    fragment, _prov, skipped = build_draft(
        spec, lat, lon,
        name=ident["name"], operator=ident["operator"], power_mw=None,
        project_status=ident["project_status"], accessed=accessed,
    )
    frais = {i["id"]: i for i in fragment["indicators"]}

    # 2) ensemble à re-mesurer = collecteurs − nationaux (LU dans le SPEC, jamais en dur)
    nationaux = national_indicators(spec)
    a_remesurer = _collector_ids(spec) - nationaux

    inds = {i["id"]: i for i in resultat["indicators"]}
    remesures: list[str] = []
    for iid in sorted(a_remesurer):
        if iid in frais:
            inds[iid] = frais[iid]
            remesures.append(iid)

    # 3) E6 : point-dépendant mais hors collect() (heat_network, dépend FCU). S'il était mesuré,
    #    il DOIT être re-mesuré — conserver sa valeur décrirait l'ancien point. Sans FCU : refus.
    e6_mesure = inds.get("E6", {}).get("status") == "measured"
    if e6_mesure and not fcu_dir:
        raise SystemExit(
            "E6 est mesuré sur la fiche : repositionnement impossible sans FCU "
            "(--fcu <dir> ou $SMDC_FCU_DIR, voir " + heat_network.FCU_URL + "). "
            "Conserver la valeur E6 décrirait l'ancien point."
        )
    if fcu_dir:
        fcu = heat_network.load_fcu(Path(fcu_dir))
        inds["E6"] = heat_network.e6_at(lat, lon, fcu, accessed)
        remesures.append("E6")

    # reconstruit la liste en conservant l'ORDRE servi, nouveaux id éventuels en fin
    ordre = [i["id"] for i in servie["indicators"]]
    resultat["indicators"] = ([inds[i] for i in ordre]
                              + [inds[i] for i in inds if i not in ordre])

    # 4) identité : coordonnée + champs dérivés de la commune (la commune change à 400 km).
    #    On dérive les clés commune-dépendantes du fragment, on ne les code pas en dur.
    resultat["identity"]["coordinates"] = {"lat": lat, "lon": lon}
    commune_keys = set(fragment["identity"]) - _IDENTITE_CONSERVEE
    for k in commune_keys:
        resultat["identity"][k] = fragment["identity"][k]

    # 5) garde-fou fail-loud : rien perdu (clés racine ⊆, id indicateurs ⊆)
    assert set(servie) <= set(resultat), \
        f"clé racine perdue au repositionnement : {set(servie) - set(resultat)}"
    src_ids = {i["id"] for i in servie["indicators"]}
    res_ids = {i["id"] for i in resultat["indicators"]}
    assert src_ids <= res_ids, f"indicateur perdu au repositionnement : {src_ids - res_ids}"

    serv_by = {i["id"]: i for i in servie["indicators"]}
    res_by = {i["id"]: i for i in resultat["indicators"]}
    _mes = lambda i: bool(i) and i.get("status") == "measured"
    # RÉTROGRADÉS : mesuré sur la fiche servie, plus mesuré après recalage (collecteur revenu
    # vide à la nouvelle commune/point). C'est honnête — l'ancienne valeur décrivait l'autre
    # lieu — mais ça PERD une mesure : à relire par un humain avant publication.
    retrogradees = sorted(iid for iid in src_ids if _mes(serv_by[iid]) and not _mes(res_by[iid]))
    rapport = {
        "id": dc_id,
        "de": {"coord": ident["coordinates"],
               "commune": ident.get("municipality"), "dept": ident.get("admin_area")},
        "vers": {"coord": {"lat": lat, "lon": lon},
                 "commune": resultat["identity"].get("municipality"),
                 "dept": resultat["identity"].get("admin_area")},
        "remesurees_avec_valeur": sorted(iid for iid in remesures if _mes(res_by.get(iid))),
        "retrogradees": retrogradees,
        "conserves_nationaux": sorted(nationaux),
        "collecteurs_revenus_vides": sorted(skipped),
        "valeurs_changees": sorted(
            iid for iid in src_ids
            if serv_by[iid].get("value") != res_by[iid].get("value")
        ),
        "cles_racine_identiques": set(servie) == set(resultat),
        "ids_indicateurs_identiques": src_ids == res_ids,
    }
    return resultat, rapport


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Repositionne une fiche servie sur sa vraie coordonnée.")
    ap.add_argument("--id", required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--newsroom", required=True, help="racine du dépôt newsroom (corpus servi)")
    ap.add_argument("--accessed", default=_dt.date.today().isoformat())
    ap.add_argument("--fcu", default=None, help="dossier FCU (sinon $SMDC_FCU_DIR) pour re-mesurer E6")
    ap.add_argument("--out-dir", default=None, help=f"défaut : <newsroom>/{HELD_DIR}")
    a = ap.parse_args(argv)

    fcu_dir = a.fcu or os.environ.get("SMDC_FCU_DIR")  # FCU optionnel : requis seulement si E6 mesuré
    resultat, rapport = reposition(a.id, a.lat, a.lon, newsroom=a.newsroom,
                                   accessed=a.accessed, fcu_dir=fcu_dir)
    out_dir = Path(a.out_dir) if a.out_dir else Path(a.newsroom) / HELD_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{a.id}.json"
    out.write_text(json.dumps(resultat, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(rapport, ensure_ascii=False, indent=2))
    print(f"→ {out} (zone de transit ; agent-codeur-site déplace dans calibration/datacenters/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
