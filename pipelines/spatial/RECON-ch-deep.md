# Switzerland — deep recon (2026-07-19)

Sonde de faisabilité pour le chantier pays n°2 (54 DC au corpus, **3,4/9 indicateurs**, zéro label
de puissance). Même format que [`RECON-de-deep.md`](./RECON-de-deep.md) : on chiffre avant de
construire, et un « ça n'existe pas publiquement » est un résultat, pas un échec.

**Contexte structurant : la Suisse n'est pas dans l'UE.** La directive efficacité énergétique
(UE) 2023/1791 — donc l'obligation de déclaration data center qui nous a donné le registre RVO
néerlandais — **ne s'applique pas**. Il n'existe aucun équivalent suisse.

---

## 1. Verdict : 3,4/9 → ~7/9, concentré dans UN seul build

**La trouvaille : `geo.admin.ch` est un point-query keyless unique qui remplit quatre indicateurs
d'un coup.** C'est le meilleur géoportail national rencontré sur ce projet.

```
https://api3.geo.admin.ch/rest/services/all/MapServer/identify
  ?geometry=<E>,<N>&geometryType=esriGeometryPoint&sr=2056
  &layers=all:<layerId>&tolerance=<px>&mapExtent=…&imageDisplay=…&returnGeometry=false
```

Keyless, LV95 (EPSG:2056) ou 4326. **`tolerance` est en PIXELS** — il faut piloter `mapExtent` /
`imageDisplay` pour contrôler la conversion px→m (`tolerance=0` = point-dans-polygone ;
`tolerance=250` sur une emprise 10 km / 500 px = tampon 5 km). Catalogue : `.../layersConfig`
→ **896 couches**. Un adaptateur + une spec de couches déclarative, exactement notre architecture.

| Ind. | Source | Couche / endpoint | Statut | Gain |
|---|---|---|---|---|
| **E1** | Fraunhofer energy-charts | `?country=ch` — **testé**, ~12 gCO₂/kWh (hydro+nucléaire) | OPEN keyless | 54/54 |
| **W1** | WRI Aqueduct (déjà global) | — | OPEN keyless | 54/54 |
| **W2** | BAFU NAWA | `ch.bafu.gewaesserschutz-chemischer_zustand_nitrat`, `…biologischer_zustand_makrozoobenthos` (+ phosphate, ammonium, diatomées, poissons, macrophytes) | OPEN keyless — **testé** | 54/54 |
| **W3** | BAFU | `ch.bafu.wasser-entnahme` + `ch.bafu.wasser-rueckgabe` | OPEN keyless — **testé** (retourne `ZH-015 / Limmat` + fiche PDF) | 54/54 |
| **F1** | BAFU inventaires fédéraux | `bundesinventare-bln`, `-auen`, `-flachmoore`, `-hochmoore`, `-moorlandschaften`, `-trockenwiesen`, `-vogelreservate`, `schutzgebiete-smaragd` (Emerald), `-ramsar` | OPEN keyless — **plus riche que CDDA** | 54/54 |
| **F2** | ARE | `ch.are.bauzonen` — zones à bâtir harmonisées nationales | OPEN keyless — **testé** (Glattbrugg → `Zürich, ZH, Wohnzonen`) — **strictement meilleur que Corine** | 54/54 |
| **L1** | BFS / ESTV | pas d'équivalent NUTS2 ; XLSX **au canton**, CSV communal pour ZH/BL/BS seulement | PORTAL / partiel | 54/54 mais **granularité canton** |
| **L3** | OPAM | **pas de registre national.** Fédéral = seulement couloirs sectoriels (rail/route/pipeline/aérodromes). Établissements = **cantonal** : WFS ouverts confirmés UR, SZ, SH, BS, AG | PORTAL, fragmenté | ~30-50 % |
| **E2** | Swissgrid | rien de nodal — XLSX agrégé national uniquement | **NONE** | 0 |
| **E3** | Swissgrid / ElCom | aucune donnée locationnelle ; `api.swissgrid.ch` n'existe pas | **NONE** | 0 |

Corine et CDDA **restent valides** pour la CH (membre EEA-39, CLC 2018 produit par le WSL sous
contrat AEE) — mais `ch.are.bauzonen` (parcellaire) et les inventaires BAFU les battent. Les garder
comme repli pan-européen pour que le squelette reste commun.

## 2. Le rail de vérification tiers : résultat NÉGATIF

**La SDEA n'a pas de registre public.** `label.sdea.ch` est un mur d'inscription ; `sdea.ch`
n'affiche que cinq logos (Digital Realty, HPE, Portus, SIX, Swisscom) — aucun nom d'installation,
aucun niveau, aucun PUE. Les certifications ne sortent que par **communiqué de presse** : Digital
Realty Glattbrugg ZUR1/2/3 (Gold+, campus 45 MW), ZUR2 (Platinum Plus), Portus Luxembourg. Soit
**~5-10 installations nommées, non machine-readable, majoritairement pas en Suisse**.

Écartés aussi : opendata.swiss (1 résultat agrégé pour `grossverbraucher`), EnAW (aucune liste
nommée de participants).

**Conséquence assumée : le plafond A-25 reste posé sur les 54 sites suisses.** Et c'est le point
éditorial le plus fort de cette sonde : **ce plafond n'est pas un trou de notre pipeline, c'est une
propriété de la régulation suisse.** Un data center néerlandais peut atteindre A parce que son
régulateur publie ; un suisse ne le peut pas parce que le droit suisse ne l'exige pas. L'écart de
note est un **écart de transparence**, pas un écart de performance — et c'est exactement la thèse de
l'observatoire.

Le plus proche d'un rail tiers est l'**API de la Feuille officielle** (keyless, nationale, tous
cantons) : `https://www.amtsblattportal.ch/api/v1/publications?publicationStates=PUBLISHED&keyword=Rechenzentrum`
(147 occurrences ; `keyword=` marche, `query=` est silencieusement ignoré → 2,79 M non filtrés).
Elle prouve l'**autorisation de construire**, pas l'exploitation.

## 3. Labels de puissance : proches de zéro

| Rang | Source | Fiabilité | Couverture |
|---|---|---|---|
| 1 | Communiqués SDEA | haute (porte de vrais MW : 45 MW Glattbrugg) | ~3 sites, manuel, non répétable |
| 2 | Permis de construire cantonaux (ZH : CSV 20 607 lignes) | officielle, auditable | **3 lignes** matchent `Rechenzentrum` ; MW rarement indiqué |
| 3 | Amtsblattportal | officielle | même donnée, pire rapport signal/bruit |
| 4 | Publications réseau | — | rien par site |
| 5 | Sites opérateurs / presse | faible comme preuve tierce | volume mais basse confiance |

**Attendu réaliste : 3 à 6 labels sur 54**, tous de presse.

## 4. Chiffrage

| Lot | Coût | Gain |
|---|---|---|
| Adaptateur `geoadmin_identify` + spec de couches déclarative → F1, F2, W2, W3 | **~1 j** | **+3,5** |
| L1 au canton (XLSX BFS/ESTV, 26 unités) | ~½ j | +0,5 — **granularité plus grossière, à déclarer dans l'artefact, pas à faire passer pour de la parité** |
| L3 par fédération de 5-6 WFS cantonaux | 1-2 j | +0,3 — **mauvais rapport effort/rendement** ; les couloirs MAO fédéraux sont keyless et peuvent servir de proxy partiel explicite |

## 5. Le plafond honnête — ce qui ne pourra PAS être rempli

- **E2 et E3.** Swissgrid ne publie ni capacité nodale ni congestion locationnelle, et il n'existe
  pas d'équivalent ElCom. **Ce n'est pas un problème de recherche : la donnée n'est pas publique.**
  À marquer *structurellement indisponible* pour la CH plutôt qu'à proxyfier — sauf à assumer
  publiquement « distance à un couloir Sachplan » comme proxy explicitement étiqueté.
- **Labels de puissance et rail tiers.** Sans obligation type EED et avec la SDEA derrière un login,
  aucune source répétable. Le plafond est correct et doit être **présenté comme une propriété de la
  régulation suisse**, pas comme une lacune de notre pipeline.
