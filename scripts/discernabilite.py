# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""DISCERNABILITÉ — combien de sites restent indistinguables, et ce qu'une variable y change.

    uv run python scripts/discernabilite.py --pays FR
    uv run python scripts/discernabilite.py --pays FR --gains          # classement des variables
    uv run python scripts/discernabilite.py --pays FR --binning L2     # coût du découpage en bandes

POURQUOI UNE SEULE DÉFINITION. Trois consommateurs posent la même question avec des mots
différents — le comparateur (« ces deux sites se ressemblent-ils vraiment ? »), la collecte
(« quelle variable vaut la peine d'être câblée ? ») et la calibration (« que coûte une
bande ? »). S'ils la mesurent chacun à leur façon, leurs chiffres ne se comparent pas et la
discussion devient une affaire d'opinion. Ici, une fonction.

LA MESURE. Part des fiches d'un pays qui partagent leur PROFIL — le n-uplet de leurs valeurs
observées — avec au moins une autre fiche. 100 % = personne n'est distinguable ; 0 % = chaque
site est unique. C'est volontairement plus brutal que le taux de liens « indiscernables » du
comparateur : on ne regarde pas les cinq plus proches, on regarde l'égalité stricte. Les deux
bougent ensemble ; celle-ci ne dépend d'aucun paramètre (ni k, ni imputation, ni distance).

CE QU'ELLE A DÉJÀ ÉTABLI (corpus 2026-10-03) :
  · ajouter une variable CATÉGORIELLE rapporte peu — E3 9 points, W3 6, E2 5, L1 5, L3 2 ;
  · ajouter une variable CONTINUE rapporte beaucoup — L2 46 points ;
  · et la même variable continue, découpée en 4 bandes, ne rapporte plus que 6 points.
    Quarante points séparent une distance de sa case. C'est l'argument qui vaut pour F1,
    calculé en mètres partout et publié en quatre classes.

LIMITE À GARDER EN TÊTE. Un gain mesuré sur la France ne se transporte pas tel quel : il
dépend de la DISTRIBUTION de la variable dans le pays visé. W2 vaut 42 % de concentration en
France et 78 % au Royaume-Uni — la même variable, trois fois moins séparatrice. Mesurer le
pays visé, ou à défaut annoncer le chiffre comme une borne haute.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.core import ARTIFACTS_DIR  # noqa: E402

OBSERVE = ("measured", "announced", "estimated")


def profils(pays: str, artifacts: Path = None) -> list[dict]:
    """Les valeurs OBSERVÉES de chaque fiche d'un pays. Une absence n'est pas une valeur."""
    d = (artifacts or ARTIFACTS_DIR) / "dc"
    out = []
    for p in sorted(d.glob(f"{pays.lower()}-*.json")):
        fiche = json.loads(p.read_text())
        out.append({i["id"]: i.get("value") for i in fiche.get("indicators", [])
                    if i.get("status") in OBSERVE and i.get("value") is not None})
    return out


def part_partagee(fiches: list[dict], variables: list[str]) -> float:
    """% des fiches dont le profil n'est pas unique sur ce jeu de variables."""
    if not fiches:
        return 0.0
    compte = collections.Counter(tuple(f.get(v) for v in variables) for f in fiches)
    uniques = sum(1 for n in compte.values() if n == 1)
    return 100 * (len(fiches) - uniques) / len(fiches)


def variables_observees(fiches: list[dict], minimum: int = 20) -> list[str]:
    """Les variables assez présentes pour peser — sous le plancher, le gain n'est pas lisible."""
    c = collections.Counter(k for f in fiches for k in f)
    return sorted(k for k, n in c.items() if n >= minimum)


def gains(fiches: list[dict], socle: list[str]) -> list[tuple[str, float, float]]:
    """(variable, part avec elle, points gagnés) — ce que CHAQUE variable ajouterait au socle."""
    base = part_partagee(fiches, socle)
    out = []
    for v in variables_observees(fiches):
        if v in socle:
            continue
        avec = part_partagee(fiches, socle + [v])
        out.append((v, avec, base - avec))
    return sorted(out, key=lambda t: -t[2])


def cout_du_binning(fiches: list[dict], socle: list[str], variable: str, bandes: int = 4) -> dict:
    """Ce que coûte de publier une variable CONTINUE en classes plutôt qu'en valeur.

    Les bornes sont des quantiles : on compare la variable à elle-même, pas à un découpage
    métier. Le but n'est pas de proposer des bandes, c'est de chiffrer la perte.
    """
    import numpy as np
    vals = sorted(float(f[variable]) for f in fiches if isinstance(f.get(variable), (int, float)))
    if len(vals) < bandes * 2:
        return {"erreur": f"{variable} : {len(vals)} valeurs numériques, trop peu pour {bandes} bandes"}
    bornes = np.quantile(vals, [i / bandes for i in range(1, bandes)])
    cle = f"{variable}__bande"
    for f in fiches:
        v = f.get(variable)
        f[cle] = None if not isinstance(v, (int, float)) else int(np.searchsorted(bornes, v))
    base = part_partagee(fiches, socle)
    return {"base": base,
            "continu": part_partagee(fiches, socle + [variable]),
            "en_bandes": part_partagee(fiches, socle + [cle]),
            "n_valeurs": len(vals), "n_fiches": len(fiches)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pays", required=True, help="code ISO, ex. FR, GB, DE")
    ap.add_argument("--socle", default="", help="variables du socle, séparées par des virgules "
                                                "(défaut : toutes celles du pays)")
    ap.add_argument("--gains", action="store_true", help="classer les variables par points gagnés")
    ap.add_argument("--binning", metavar="VAR", help="chiffrer le coût du découpage de VAR en bandes")
    ap.add_argument("--artifacts", type=Path, default=None)
    args = ap.parse_args(argv)

    fiches = profils(args.pays, args.artifacts)
    if not fiches:
        print(f"aucune fiche pour {args.pays}", file=sys.stderr)
        return 1
    socle = [v.strip() for v in args.socle.split(",") if v.strip()] or variables_observees(fiches)

    print(f"{args.pays.upper()} — {len(fiches)} fiches · socle de {len(socle)} variables : "
          f"{', '.join(socle)}")
    print(f"  profils partagés : {part_partagee(fiches, socle):.0f} %\n")

    if args.gains:
        print("  gain d'UNE variable de plus :")
        for v, avec, pts in gains(fiches, socle):
            print(f"     + {v:4} → {avec:5.0f} %   ({pts:+5.0f} pts)")
    if args.binning:
        r = cout_du_binning(fiches, socle, args.binning)
        if "erreur" in r:
            print("  " + r["erreur"]); return 1
        print(f"  {args.binning} sur {r['n_valeurs']}/{r['n_fiches']} fiches")
        print(f"     socle seul        {r['base']:5.0f} %")
        print(f"     + en 4 bandes     {r['en_bandes']:5.0f} %   ({r['base']-r['en_bandes']:+.0f} pts)")
        print(f"     + en continu      {r['continu']:5.0f} %   ({r['base']-r['continu']:+.0f} pts)")
        print(f"     coût du découpage : {r['en_bandes']-r['continu']:.0f} points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
