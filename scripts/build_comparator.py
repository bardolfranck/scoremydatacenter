# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le COMPARATEUR : pour un site, les sites de son pays qui lui ressemblent le plus.

    make comparator                  # lit la projection en cache, écrit les artefacts
    make comparator-projection       # redessine les pays dont le compte a bougé (à froid)

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
AFFICHES_MAX = 5

# SÉLECTIVITÉ : les voisins affichés doivent rester une MINORITÉ du pays — c'est ça, le critère,
# pas un nombre de fiches rond. Mesuré le 2026-10-02 : en France les 5 voisins font 1,2 % du
# pays ; en Autriche (9 sites) ils en feraient 56 %, et le filtre mutuel n'y rejette RIEN (0 %
# contre 20 % en France) — il deviendrait décoratif. Au-delà de 15 %, on n'élit plus, on énumère.
#
# Mais un seuil binaire excluait la Grande-Bretagne, gros marché européen, pour un motif qui
# n'est pas statistique : nous n'y documentons que 14 sites. Un pays absent du comparateur est
# un TROU DE COLLECTE, pas un pays sans data centers — le cacher, c'est faire passer notre
# lacune pour une propriété du territoire. Alors on ADAPTE le nombre affiché à la taille du
# pays : la sélectivité reste constante, et les petits corpus donnent des listes courtes qui
# disent leur propre maigreur.
SELECTIVITE_MAX = 0.15
AFFICHES_MIN = 2                    # en dessous de deux voisins, ce n'est plus une comparaison
SEUIL_PAYS = int(np.ceil(AFFICHES_MIN / SELECTIVITE_MAX))   # 14 sites aujourd'hui

# Pays EN VEILLE — notes retirées du public (doctrine Franck, gate A-26). Exclusion de POLICE,
# pas de statistique : elle ne se déduit d'aucune mesure et ne doit pas dépendre d'un seuil.
# Garder aligné avec smdc-api/src/veille.js.
PAYS_EN_VEILLE = {"IL"}
# Au-delà de ce tiers de l'étendue, une « famille » n'entoure plus rien : on ne la dessine pas.
DISPERSION_MAX = 0.33

# Paramètres de la projection, versionnés avec les artefacts. n_neighbors bas privilégie la
# structure locale (familles détachées), min_dist bas resserre chaque famille.
#
# ET LA PROJECTION N'EST PAS REJOUABLE À L'IDENTIQUE, random_state=0 ou pas. Mesuré le
# 2026-10-02, deux runs consécutifs sur le même corpus : 3 pays sur 13 ressortent avec une
# autre disposition (déplacement médian jusqu'à 0,9 sur une étendue normalisée à 1 — soit
# une carte retournée). Ce qui EST stable, et c'est là que vit l'information : les familles
# DBSCAN (identiques 13 fois sur 13) et les listes de voisins, qui ne passent pas par UMAP.
# Le dessin illustre une structure mesurée ailleurs ; il n'est pas lui-même la mesure. D'où
# le cache, qui est l'autorité : on ne le rejoue que pour un pays dont le compte a bougé.
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


def _positions() -> dict[str, list[float]]:
    """Les positions PUBLIQUES, arrondies au centième de degré par l'anti-pillage.

    On ne lit jamais celles du newsroom pour la carte : elles sont au mètre, et la protection
    qui les arrondit avant publication n'aurait plus de sens si le comparateur les republiait.
    Un kilomètre suffit largement à situer un point sur une carte de pays.
    """
    geo = json.loads((ARTIFACTS_DIR / "map.geojson").read_text())
    return {f["properties"]["id"]: f["geometry"]["coordinates"] for f in geo["features"]}


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


def projection(pays: str, D: np.ndarray, froid: bool = False,
               force: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """La projection 2D et les familles, en CACHE dans le newsroom.

    UMAP tire numba et llvmlite : en faire une dépendance de `make deploy` reviendrait à
    rendre une mise en ligne otage d'une pile de calcul scientifique. La projection ne bouge
    pas d'un jour à l'autre — on la recalcule à froid, on la relit au build.

    `froid` AUTORISE le recalcul (chemin `make comparator-projection`), il ne l'impose pas :
    seuls les pays dont le compte a bougé repassent par UMAP. Sans ça, rejouer la projection
    pour UN pays redessinait les douze autres — et comme le dessin n'est pas rejouable à
    l'identique, ça remplaçait douze cartes relues et validées sans qu'aucune donnée ait
    changé. `force` est là pour le jour où on décide vraiment de tout refaire.
    """
    cache = PROJ_DIR / f"{pays}.json"
    if cache.is_file() and not force:
        d = json.loads(cache.read_text())
        if d.get("n") == len(D):
            return np.array(d["xy"], dtype=float), np.array(d["familles"], dtype=int)
        quoi = f"cache périmé ({d.get('n')} ≠ {len(D)})"
    else:
        quoi = "aucun cache" if not cache.is_file() else "recalcul demandé"
    if not froid:
        # Le chemin CHAUD ne calcule jamais : il échouerait de toute façon sur l'import, mais
        # sur un ModuleNotFoundError illisible. Mieux vaut nommer le pays et la commande.
        raise SystemExit(f"comparator: {pays} — {quoi}. Le build ne recalcule pas la "
                         f"projection : lancer `make comparator-projection` d'abord.")
    print(f"  {pays} : {quoi}, projection recalculée")
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


def construire(pays: str, fiches: list[dict], libelles: dict, froid: bool, force: bool,
               positions: dict[str, list[float]]) -> dict:
    # Combien de voisins ce pays peut-il porter sans que la liste cesse d'être une sélection ?
    affiches = max(AFFICHES_MIN, min(AFFICHES_MAX, int(len(fiches) * SELECTIVITE_MAX)))
    cols, X, P = _matrice(fiches)
    Z, D = _distances(X)
    xy, lab = projection(pays, D, froid, force)
    n = len(fiches)
    ordre = np.argsort(D, 1)
    # SEUIL DE RÉCIPROCITÉ PAR LA VALEUR, et surtout pas par le rang dans un tri.
    #
    # Quand des sites sont à distance EXACTEMENT nulle — fréquent là où nous ne documentons
    # que quatre variables territoriales : seize data centers londoniens partagent les mêmes
    # valeurs — `argsort` doit départager des ex æquo, et il le fait par ordre d'indice, donc
    # par ordre alphabétique. Avec seize candidats pour huit places, les derniers de l'alphabet
    # ne figuraient dans le top-8 de personne : réciprocité jamais satisfaite, AUCUN comparable.
    # Quatre fiches Digital Realty (LHR17, 19, 20, 21) étaient dans ce cas, pour la seule
    # raison que leur nom commence par une lettre tardive.
    #
    # On compare donc chaque distance au k-ième plus petit ÉCART, bornes comprises : tous les
    # ex æquo sont dedans ou tous dehors, et la relation redevient symétrique par construction.
    kth = np.partition(D, min(K_MUTUEL, n - 1) - 1, axis=1)[:, min(K_MUTUEL, n - 1) - 1]
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
            if len(voisins) >= affiches:
                break
            if D[j, i] > kth[j] + 1e-12:          # pas réciproque : pas un comparable
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
            "xy": positions.get(f["id"]),
            "xy2": [round(float(xy[i, 0]), 4), round(float(xy[i, 1]), 4)],
            "famille": int(lab[i]), "comparables": voisins,
        })
    # LARGEUR DE DOCUMENTATION du pays : la médiane des variables communes à un rapprochement.
    # C'est ce nombre qui dit au lecteur la finesse de la sélection qu'il obtient — 11 en
    # France, 4 au Royaume-Uni. On publie ce chiffre et RIEN DE PLUS : le détail de quels
    # indicateurs manquent où serait une carte de nos lacunes, utile surtout à qui voudrait
    # nous copier ou nous attaquer. Dire la finesse sans détailler la faiblesse.
    vp = [v["variables_partagees"] for s_ in sites for v in s_["comparables"]]
    return {"pays": pays, "k_mutuel": K_MUTUEL, "affiches": affiches,
            "selectivite": round(affiches / len(fiches), 3),
            "variables_medianes": int(np.median(vp)) if vp else 0,
            "umap": UMAP_PARAMS, "dbscan": DBSCAN_PARAMS,
            "familles": familles, "sites": sites}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--projection", action="store_true",
                    help="autoriser le recalcul UMAP des pays dont le cache a bougé "
                         "(nécessite umap-learn : `make comparator-projection`)")
    ap.add_argument("--force", action="store_true",
                    help="tout redessiner, y compris les pays inchangés — la projection "
                         "n'étant pas rejouable à l'identique, c'est une décision, pas une "
                         "précaution")
    args = ap.parse_args()

    meth = json.loads((ARTIFACTS_DIR / "methodology.json").read_text())
    libelles = {i["id"]: (i["label"]["fr"] if isinstance(i.get("label"), dict) else i["id"])
                for i in meth["indicators"]}
    fiches = _fiches()
    positions = _positions()
    par_pays: dict[str, list[dict]] = {}
    for f in fiches:
        par_pays.setdefault(f.get("country") or "??", []).append(f)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index, total = [], 0
    minces = []
    for pays, lot in sorted(par_pays.items()):
        if pays in PAYS_EN_VEILLE:
            continue
        if len(lot) < SEUIL_PAYS:
            # On le DIT au lieu de l'escamoter : la page nommera le pays et son compte, pour
            # qu'un lecteur distingue « nous n'avons pas encore collecté ici » de « il n'y a
            # rien ici ». C'est aussi ce qui tire la collecte.
            minces.append({"pays": pays, "sites": len(lot)})
            continue
        doc = construire(pays, lot, libelles, args.projection or args.force, args.force,
                         positions)
        (OUT_DIR / f"{pays}.json").write_text(json.dumps(doc, ensure_ascii=False))
        servis = sum(1 for s in doc["sites"] if s["comparables"])
        moy = np.mean([len(s["comparables"]) for s in doc["sites"]])
        index.append({"pays": pays, "sites": len(lot), "servis": servis,
                      "affiches": doc["affiches"], "selectivite": doc["selectivite"],
                      "variables_medianes": doc["variables_medianes"],
                      "familles": len(doc["familles"])})
        total += len(lot)
        print(f"  {pays} : {len(lot):4} sites · {servis} servis ({servis * 100 // len(lot)} %) · "
              f"jusqu'à {doc['affiches']} voisins ({doc['selectivite']:.1%} du pays) · "
              f"{moy:.1f} en moyenne · {doc['variables_medianes']} variables communes · "
              f"{len(doc['familles'])} familles")
    (OUT_DIR / "index.json").write_text(json.dumps(
        {"seuil_pays": SEUIL_PAYS, "selectivite_max": SELECTIVITE_MAX,
         "pays": index, "corpus_trop_mince": sorted(minces, key=lambda d: -d["sites"])},
        ensure_ascii=False))
    print(f"comparator: {len(index)} pays, {total} sites · seuil {SEUIL_PAYS} sites "
          f"({AFFICHES_MIN} voisins minimum <= {SELECTIVITE_MAX:.0%} du pays)")
    if minces:
        print("  corpus trop mince, SIGNALÉ sur le site (trou de collecte, pas absence de sites) : "
              + ", ".join(f"{m['pays']} ({m['sites']})" for m in minces))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
