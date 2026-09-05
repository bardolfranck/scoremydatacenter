# Pré-enregistrement — La note SMDC comme indicateur avancé de l'opposition

**Statut : BROUILLON pour relecture standard SMDC (codeur-site) → décision de publication (Franck).**
**Une fois public + horodaté (tag git), CE DOCUMENT NE SE RÉÉCRIT PLUS** — c'est sa valeur : une
prédiction datée qu'aucun résultat futur ne peut faire passer pour réécrite après coup.

Rédigé le 2026-09-05 par agent-calibration-index-ML/R&D. T0 = snapshot immuable
`smdc-newsroom/validation/2026-09-05/baseline-scores-T0.json` (commit 0704a4b).

---

## 1. Hypothèse (directionnelle, fixée avant tout outcome)

**H1** : parmi les projets de data center en pipeline notés à T0, la probabilité de connaître un
événement de contestation documenté dans la fenêtre [T0, T0+18 mois] **décroît avec la note de
site** — un projet noté D ou E est significativement plus exposé qu'un projet noté A ou B.

**H0 (nulle, à réfuter)** : la note de site n'est pas associée à l'exposition à la contestation
(lift ≈ 1, IC contenant 1).

## 2. Ce qui rendrait H1 FAUSSE (falsifiabilité, dite d'avance)

- Lift D-E vs A-B ≤ 1, OU sa borne inférieure d'IC 95 % ≤ 1 → H1 rejetée.
- La note perd toute significativité une fois contrôlée par la taille et la densité (§6) → la note
  n'ajoute rien au-delà du trivial « gros projet en zone dense = contesté » → H1 non soutenue.
On publie le résultat **quel qu'il soit**. Un précurseur qui échoue à son propre test pré-enregistré
et le dit vaut plus qu'un précurseur affirmé sans test.

## 3. Population et exposition (gelées à T0)

- **Cohorte PRIMAIRE** : les projets en pipeline notés à T0 — statut `announced` ou `permitting`,
  note de site ∈ {A,B,C,D,E} (hors `en_attente`). **n = 55** au 2026-09-05
  (announced 49 + permitting 6). Distribution : B 4 · C 30 · D 19 · E 2.
- **Cohorte SECONDAIRE (exploratoire, rapportée à part)** : les DC `operational` notés (n ≈ 1349).
  La contestation d'un site opérationnel est un phénomène distinct (grief a posteriori ≠ opposition
  pré-construction) ; analysée séparément, jamais fusionnée au primaire.
- **Exposition = la note de SITE à T0**, immuable (le fichier T0 ne change pas). La note de
  projet/processus est EXCLUE de l'exposition (elle peut contenir des proxies procéduraux T1 →
  circularité ; cf. §5).

## 4. Outcome (défini de façon machine, collecté APRÈS T0)

- **Contesté = ≥ 1 fait de contestation documenté** détecté dans [T0, T0+18 mois] et lié au projet
  (join coord < 2 km ET concordance d'opérateur/nom au moment de la détection). `kind` déjà codé
  par la veille (`opposition` / `moratorium` / recours / refus / abandon).
- **Source = la veille GDELT/presse** tournant en continu (jamais le fichier T0). Une détection est
  valide si sa date de publication est **postérieure à T0**.
- **Regard intermédiaire** à T0+6 mois (rapporté, non concluant) ; **analyse principale** à
  T0+18 mois.

## 5. Non-circularité : la nuance L6/L7, dite avec précision et PROUVÉE mécaniquement

**Correction d'honnêteté (2026-09-05)** : une première rédaction affirmait « la note de site
n'utilise jamais la contestation ». C'est **faux en droit** — deux indicateurs du bloc `base`
(donc de la note de site) sont liés à la contestation : **L6 « niveau de contestation observé »**
(recours, pétitions, mobilisations ; poids ≈ 4 % de la note site) et **L7 « position des élus »**
(votes officiels ; ≈ 3 %). L'architecture *permet* donc à la contestation d'entrer dans la note de
site.

**Ce qui est vrai, vérifié et gelé** : sur les **1404 fiches du corpus T0, L6 et L7 sont
`missing` à 100 %** → contribution renormalisée à **exactement 0** dans toutes les notes de site du
snapshot. La note de site T0 est donc, EN FAIT, un score de territoire pur, sans aucun signal de
contestation. L'exposition (note T0) et l'outcome (contestation post-T0) sont indépendants **pour
ce corpus**.

**Rendu OPPOSABLE, pas seulement attesté** — deux gardes CI (`engine/tests/test_noncircularity.py`,
rejouées à chaque build) :
1. **A-21 comportemental** : injecter des faits de `contestation[]` fabriqués sur une fiche laisse
   sa note de site **identique au bit près** → la couche d'affichage ne score jamais.
2. **Fait empirique gelé** : L6 et L7 sont `missing` sur tout le corpus. **Si un run futur les
   remplit, ce test ÉCHOUE bruyamment** — forçant à réviser ce pré-enregistrement AVANT que la
   contestation ne contamine l'exposition. La non-circularité n'est donc pas une promesse, c'est un
   invariant que le build refuse de violer en silence.

*(Le snapshot T0 porte lui-même une note `non_circularity` en version courte « structural facts,
never contestation » : elle est empiriquement vraie pour T0 au sens ci-dessus ; le présent §5 + les
gardes en sont la version rigoureuse et exécutable.)*

## 6. Métriques et analyse (figées — aucun choix post-hoc)

**Deux tests CO-PRIMAIRES** (le lift seul reposerait sur le bras A-B = 4, trop fragile ; le test de
tendance utilise toutes les tranches et le double) :

1. **Co-primaire A — tendance (Cochran-Armitage)** sur A→E, unilatéral (contestation croissante de
   A vers E). Robuste au bras A-B mince. Seuil : **p < 0,05**.
2. **Co-primaire B — lift (risque relatif)** : `P(contesté|D∪E) / P(contesté|A∪B)`, avec
   **correction de continuité Haldane-Anscombe (+0,5)** — indispensable car un bras A-B à 0 contesté
   rendrait le lift indéfini — et IC 95 % bootstrap. Seuil : **lift ≥ 2 ET borne inférieure d'IC > 1**.
3. **Contrôle — régression logistique** : `contesté ~ note_site + log(power_mw) + densité_pop +
   pays`. La note apporte du signal si son odds-ratio reste significatif (IC excluant 1) toutes
   choses égales. Rapporté : OR + IC par variable.

**Succès pré-spécifié = les DEUX co-primaires atteints.**

**Code d'analyse GELÉ AU TAG** : le script `scripts/validation_precurseur.py` (qui calcule
exactement ce §6) est commité AU MOMENT du tag, avec ce document, et exécuté INCHANGÉ à l'échéance.
L'éditer après le tag est un degré de liberté post-hoc, interdit — le code figé fait partie de la
prédiction opposable. (Validé sur outcome synthétique : le calcul détecte bien un gradient injecté.)

## 7. Puissance — la limite, énoncée d'avance (le vrai sujet)

À T0, seuls **55 projets pipeline** sont notés, dont **4 en A-B** et **21 en D-E**. Conséquences
honnêtes :
- Le bras « bonne note » (A-B = 4) est **trop mince** pour tester rigoureusement « une bonne note
  prédit PEU d'opposition ». Le test a de la puissance surtout sur le versant « mauvaise note → plus
  d'opposition ».
- Avec n=55 et des taux de base d'opposition modestes, un lift même réel peut ne pas atteindre la
  significativité. **Un résultat non concluant à T0+18 mois ne réfutera pas H1 — il dira "pas encore
  assez de matière".**
- **Implication stratégique (remontée à Franck)** : la valeur du test grandit avec le nombre de
  **projets annoncés européens notés** dans le corpus. La validation devient une raison forte de
  prioriser l'onboarding pipeline (veille + pilote DCmag). Ré-estimer la puissance à chaque revue.
- **Biais d'ascertainment de l'outcome** : la détection dépend du *recall* de la veille et de la
  qualité du join (coord < 2 km + opérateur). Une contestation ratée = faux négatif → **biais VERS
  LE NUL**. Conséquence assumée : le test est **conservateur** — une association réelle peut être
  sous-estimée, et un résultat positif est d'autant plus crédible qu'il survit à ce biais.

## 8. Ce qui est publiable AVANT l'échéance (rétrospectif honnête)

Un seul énoncé rétrospectif tient : le **constat de couverture** — « sur les projets européens
contestés recensés, X portent une note ; la contestation recensée est aujourd'hui à 95 % US et vit
dans une couche séparée (watchlist, A-19) ». C'est un fait, pas une corrélation. Aucune régression
rétrospective ne sera publiée (overlap ≈ 1, cf. `validation-precurseur-overlap-niveau1.md`).

## 9. Intégrité et vérifiabilité (empreintes gelées au tag)

Le baseline T0 vit dans le repo **privé** (données nominatives, A-11) : un lecteur public ne peut
pas en vérifier le commit. On grave donc ici son **empreinte sha256** — publique, ne divulguant
rien — pour prouver plus tard que ni le baseline ni le code d'analyse n'ont bougé après le tag :

| Objet | sha256 | Emplacement |
|---|---|---|
| `baseline-scores-T0.json` (exposition gelée) | `13df55db6afc2327ba84a44818085a955d0d06ad4c1b9fe6781d1855f5152a31` | newsroom privé, `validation/2026-09-05/` |
| `scripts/validation_precurseur.py` (analyse golden) | `2bb055327b71438fc9bef843e9c61166096e4fe95347eaf41bcf685b0b8c248c` | repo **public**, commit `3b27470` |

Empreintes recalculées indépendamment (session calibration, 2026-09-05) — concordantes.
Vérification tierce : `shasum -a 256 <fichier>` doit redonner exactement ces valeurs. À l'échéance,
l'analyse est exécutée sur un baseline dont l'empreinte est cette valeur, avec un script dont
l'empreinte est cette valeur — sinon le résultat n'est pas recevable.

---

*Décision de rendre ce pré-enregistrement public (tag git horodaté dans le repo **public**
`scoremydatacenter`, aux côtés du script d'analyse) = Franck, sur relecture du codeur-site. Tant
qu'il n'est pas taggé, il reste amendable ; après, il est gelé — document ET empreintes.*
