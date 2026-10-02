# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le COMPARATEUR : pour un site, les sites de son pays qui lui ressemblent le plus.

    make comparator                  # lit la projection en cache, écrit les artefacts
    make comparator-projection       # recalcule la projection UMAP (lourd, à froid)

PAR PAYS, et ce n'est pas un découpage de confort. Mesuré le 2026-10-01 : sur le corpus
entier, la rareté d'une fiche prédit celle de ses voisins à r=+0,795 — on croit comparer des
sites, on compare des niveaux de documentation. À l'intérieur d'un pays la corrélation
s'effondre (FR +0,16, DE +0,00, NL −0,29) : le confondant était le PAYS, qui pilote à la fois
la ressemblance réelle et notre couverture. Et le nombre de variables partagées passe de 5 à
11. Un pays est donc l'univers où la comparaison est à la fois loyale et riche.

SEUIL_PAYS : en dessous, pas de comparateur du tout. Une poignée de sites ne fait pas un
univers de comparaison, et un voisin « le plus proche » parmi huit n'est pas un comparable.

QUATRE DÉCISIONS, chacune payée par une mesure.

1. ON IMPUTE pour calculer. La doctrine « ne jamais transformer une absence en valeur »
   porte sur ce qu'on AFFICHE, pas sur ce qu'on calcule — les confondre m'a fait inventer
   une règle maison dont 47,8 % des liens étaient à sens unique, et qui rendait les fiches
   pauvres 3× moins souvent éligibles comme voisin. Or les projets contestés ou abandonnés
   sont souvent les moins documentés : la règle les effaçait là où ils comptent le plus.

2. FILTRE MUTUEL k=8. Un site n'est retenu que si l'ancre figure elle aussi parmi ses huit
   plus proches. Mesuré : rejette 20 % des voisins, 97 % des ancres gardent au moins un
   comparable, 83 % en gardent trois. À k=20 le filtre ne rejette plus que 5 % (décoratif),
   à k=5 il en rejette 36 % (il affame). La réciprocité garantit aussi la cohérence entre
   pages : si A cite B, B cite A.

3. ON NE PROMET PAS CINQ. On affiche ceux qui survivent — un, trois ou cinq. Compléter une
   liste pour tenir un chiffre rond, c'est inventer un comparable.

4. LE NOMBRE DE VARIABLES OBSERVÉES PARTAGÉES, jamais un pourcentage d'imputation. Cette
   métrique-là était à l'envers : elle donnait 0 % de confiance à deux fiches identiques sur
   onze variables, c'est-à-dire aux comparaisons les plus sûres qu'on ait.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.core import ARTIFACTS_DIR  # noqa: E402

CAL = Path(os.environ.get("NEWSROOM_CAL",
                          Path(__file__).resolve().parent.parent.parent / "smdc-newsroom" / "calibration"))
PROJ_DIR = CAL.parent / "comparator"          # la projection vit dans le newsroom, pas dans le build
OUT_DIR = ARTIFACTS_DIR / "comparator"

K_MUTUEL = 8
AFFICHES = 5
# SÉLECTIVITÉ : les voisins affichés doivent rester une MINORITÉ du pays. C'est ça, le critère —
# pas un nombre de fiches rond. Mesuré le 2026-10-02 : en Autriche (9 sites) « vos 5
# comparables » désignerait 56 % du pays et le filtre mutuel ne rejetterait rien, il serait
# décoratif. En France ils font 1,2 %. Au-delà de 15 %, on ne sélectionne plus, on énumère.
SELECTIVITE_MAX = 0.15
SEUIL_PAYS = int(np.ceil(AFFICHES / SELECTIVITE_MAX))   # 34 sites aujourd'hui
# Au-delà de ce tiers de l'étendue, une « famille » n'entoure plus rien : on ne la dessine pas.
DISPERSION_MAX = 0.33

# Paramètres de la projection, versionnés avec les artefacts : une projection qu'on ne sait
# pas rejouer n'est pas une mesure, c'est une image. n_neighbors bas privilégie la structure
# locale (familles détachées), min_dist bas resserre chaque famille.
UMAP_PARAMS = {"n_components": 2, "n_neighbors": 8, "min_dist": 0.03,
               "spread": 1.4, "random_state": 0}
DBSCAN_PARAMS = {"eps": 0.42, "min_samples": 5}

STATUT_FR = {
    "operational": "Site implanté", "construction": "En construction", "announced": "Annoncé",
    "permitting": "En autorisation", "permitted": "Autorisé", "planned": "Projet",
    "suspended": "Suspendu", "abandoned": "Abandonné", "litigation": "Contesté",
    "consultation": "En consultation", "study": "À l'étude", "decommissioned": "Fermé",
}
STATUT_EN = {
    "operational": "In operation", "construction": "Under construction", "announced": "Announced",
    "permitting": "In permitting", "permitted": "Permitted", "planned": "Planned",
    "suspended": "Suspended", "abandoned": "Abandoned", "litigation": "Contested",
    "consultation": "In consultation", "study": "Under study", "decommissioned": "Closed",
}


def _fiches() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((ARTIFACTS_DIR / "dc").glob("*.json"))]


def _matrice(fiches: list[dict]) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Les variables du score, normalisées, et le masque de ce qui est RÉELLEMENT observé.

    `announced` et `estimated` comptent comme observés : ils portent une valeur sourcée. Seul
    l'absent est absent — et il le restera dans l'affichage, quoi qu'on impute pour calculer.
    """
    obs = ("measured", "announced", "estimated")
    vals = [{x["id"]: x["score"] for x in f["indicators"]
             if x.get("status") in obs and isinstance(x.get("score"), (int, float))} for f in fiches]
    cols = sorted({k for v in vals for k in v})
    X = np.array([[v.get(k, np.nan) for k in cols] for v in vals], dtype=float)
    return cols, X, ~np.isnan(X)


def _distances(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.impute import KNNImputer
    mn, mx = np.nanmin(X, 0), np.nanmax(X, 0)
    Z = (X - mn) / np.where(mx > mn, mx - mn, 1)
    Zi = KNNImputer(n_neighbors=7, weights="distance").fit_transform(Z)
    D = np.sqrt(((Zi[:, None] - Zi[None, :]) ** 2).sum(-1))
    np.fill_diagonal(D, np.inf)
    return Z, D


def projection(pays: str, D: np.ndarray, force: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """La projection 2D et les familles, en CACHE dans le newsroom.

    UMAP tire numba et llvmlite : en faire une dépendance de `make deploy` reviendrait à
    rendre une mise en ligne otage d'une pile de calcul scientifique. La projection ne bouge
    pas d'un jour à l'autre — on la recalcule à froid, on la relit au build.
    """
    cache = PROJ_DIR / f"{pays}.json"
    if cache.is_file() and not force:
        d = json.loads(cache.read_text())
        if d.get("n") == len(D):
            return np.array(d["xy"], dtype=float), np.array(d["familles"], dtype=int)
        print(f"  {pays} : cache périmé ({d.get('n')} ≠ {len(D)}), projection recalculée")
    import umap
    from sklearn.cluster import DBSCAN
    Dp = np.where(np.isfinite(D), D, 0.0)
    xy = umap.UMAP(metric="precomputed", **UMAP_PARAMS).fit_transform(Dp)
    xy = (xy - xy.min(0)) / np.where(xy.max(0) > xy.min(0), xy.max(0) - xy.min(0), 1)
    # Arrondi AVANT d'écrire ET de renvoyer : sinon le calcul à chaud et la relecture à froid
    # ne donnent pas les mêmes artefacts, et le cache cesse d'être une reproduction fidèle.
    # Mesuré : 12 fichiers sur 12 différaient, sur les décimales.
    xy = np.round(xy, 5)
    lab = DBSCAN(metric="precomputed", **DBSCAN_PARAMS).fit_predict(Dp)
    PROJ_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"n": len(D), "umap": UMAP_PARAMS, "dbscan": DBSCAN_PARAMS,
                                 "xy": [[float(a), float(b)] for a, b in xy],
                                 "familles": [int(x) for x in lab]}, ensure_ascii=False))
    return xy, lab


def construire(pays: str, fiches: list[dict], libelles: dict, force: bool) -> dict:
    cols, X, P = _matrice(fiches)
    Z, D = _distances(X)
    xy, lab = projection(pays, D, force)
    n = len(fiches)
    ordre = np.argsort(D, 1)
    rang = np.empty_like(ordre)
    for i in range(n):
        rang[i, ordre[i]] = np.arange(n)
    # Une ressemblance sur une variable CONSTANTE n'apprend rien : l'intensité carbone du
    # réseau est la même pour tout un pays (écart-type mesuré 0,000 en France), donc
    # « ce qui les rapproche : l'intensité carbone » est vrai de n'importe quel couple.
    disp = {cols[c]: float(np.nanstd(Z[:, c])) for c in range(len(cols))}

    familles: dict[int, dict] = {}
    for f in sorted(set(lab.tolist()) - {-1}):
        idx = np.where(lab == f)[0]
        sub = np.where(np.isfinite(D[np.ix_(idx, idx)]), D[np.ix_(idx, idx)], 0.0)
        med = idx[int(np.argmin(sub.sum(1)))]          # médoïde : un site RÉEL représentatif
        etendue = max(np.ptp(xy[:, 0]), np.ptp(xy[:, 1])) or 1.0
        w, h = np.ptp(xy[idx, 0]), np.ptp(xy[idx, 1])
        familles[int(f)] = {
            "n": len(idx), "medoide": fiches[med]["id"],
            "medoide_commune": fiches[med].get("municipality"),
            # Une famille étalée ne se dessine pas : un cadre qui couvre un tiers du
            # graphique affirme « ces points sont ensemble » là où ils ne le sont pas.
            "compacte": bool(max(w, h) <= etendue * DISPERSION_MAX),
        }

    sites = []
    for i, f in enumerate(fiches):
        voisins = []
        for j in ordre[i]:
            if len(voisins) >= AFFICHES:
                break
            if rang[j, i] >= K_MUTUEL:            # pas réciproque : pas un comparable
                continue
            partagees = np.where(P[i] & P[j])[0]
            ecarts = sorted(((abs(Z[i, c] - Z[j, c]), cols[c]) for c in partagees), key=lambda t: t[0])
            info = [(d, k) for d, k in ecarts if disp[k] >= 0.10]
            indiscernables = bool(ecarts and ecarts[-1][0] < 1e-9)
            voisins.append({
                "id": fiches[j]["id"],
                "variables_partagees": int(len(partagees)),
                "rapprochent": [libelles.get(k, k) for _, k in info[:3]],
                # Rien ne « sépare » deux fiches dont toutes les valeurs observées coïncident.
                "separent": ([libelles.get(k, k) for d, k in info[-2:] if d > 1e-9][::-1]
                             if len(info) > 3 and not indiscernables else []),
                "indiscernables": indiscernables,
            })
        g = (f.get("grades") or {}).get("site", {})
        sites.append({
            "id": f["id"], "nom": f.get("name"), "commune": f.get("municipality"),
            "operateur": f.get("operator"), "statut": f.get("project_status"),
            "statut_fr": STATUT_FR.get(f.get("project_status"), f.get("project_status")),
            "statut_en": STATUT_EN.get(f.get("project_status"), f.get("project_status")),
            "note": g.get("grade"), "puissance_mw": f.get("power_mw"),
            "confiance": round((f.get("confidence") or {}).get("score", 0) * 100),
            "xy2": [round(float(xy[i, 0]), 4), round(float(xy[i, 1]), 4)],
            "famille": int(lab[i]), "comparables": voisins,
        })
    return {"pays": pays, "k_mutuel": K_MUTUEL, "affiches": AFFICHES,
            "umap": UMAP_PARAMS, "dbscan": DBSCAN_PARAMS,
            "familles": familles, "sites": sites}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--projection", action="store_true",
                    help="recalculer la projection UMAP (nécessite umap-learn)")
    args = ap.parse_args()

    meth = json.loads((ARTIFACTS_DIR / "methodology.json").read_text())
    libelles = {i["id"]: (i["label"]["fr"] if isinstance(i.get("label"), dict) else i["id"])
                for i in meth["indicators"]}
    fiches = _fiches()
    par_pays: dict[str, list[dict]] = {}
    for f in fiches:
        par_pays.setdefault(f.get("country") or "??", []).append(f)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index, total = [], 0
    for pays, lot in sorted(par_pays.items()):
        if len(lot) < SEUIL_PAYS:
            continue
        doc = construire(pays, lot, libelles, args.projection)
        (OUT_DIR / f"{pays}.json").write_text(json.dumps(doc, ensure_ascii=False))
        servis = sum(1 for s in doc["sites"] if s["comparables"])
        moy = np.mean([len(s["comparables"]) for s in doc["sites"]])
        index.append({"pays": pays, "sites": len(lot), "servis": servis,
                      "familles": len(doc["familles"])})
        total += len(lot)
        print(f"  {pays} : {len(lot):4} sites · {servis} servis ({servis * 100 // len(lot)} %) · "
              f"{moy:.1f} comparables en moyenne · {len(doc['familles'])} familles")
    (OUT_DIR / "index.json").write_text(json.dumps(
        {"seuil_pays": SEUIL_PAYS, "selectivite_max": SELECTIVITE_MAX, "pays": index},
        ensure_ascii=False))
    ecartes = sorted((p, len(l)) for p, l in par_pays.items() if len(l) < SEUIL_PAYS)
    print(f"comparator: {len(index)} pays, {total} sites · seuil {SEUIL_PAYS} sites "
          f"({AFFICHES} voisins <= {SELECTIVITE_MAX:.0%} du pays) · "
          f"écartés : {', '.join(f'{p} ({n})' for p, n in ecartes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
