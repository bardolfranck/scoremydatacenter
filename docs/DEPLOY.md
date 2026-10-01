<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter -->

# Déploiement de scoremydatacenter.org — le seul chemin

> **À lire par toute session/agent avant de dire « je pousse et ça sera en ligne ».**
> Ce fichier existe parce que le mode de déploiement vivait dans la mémoire d'une
> session et pas dans le repo : les agents frères volaient à l'aveugle (2026-07-20).

## La règle en une phrase

**Le déploiement est 100 % local, jamais la CI.** Une seule commande, depuis la
racine du repo, sur une machine qui a `../smdc-newsroom` (corpus privé) monté :

```
make deploy
```

## Ce que `make deploy` fait

1. `make build` → détecte `../smdc-newsroom/calibration`, donc `prod-artifacts`
   (`scripts/build_prod_artifacts.py`) : lit le **corpus réel** (479 DC, synthèses
   comprises), écrit les artefacts dans `site/public/data/`, patche les photos
   satellite depuis R2 (`~/.smdc/media.env`).
2. `npm run build --prefix site`.
3. `wrangler pages deploy dist` → Cloudflare Pages.

## Pourquoi la CI ne déploie pas

`ci.yml` ne checkoute **que** ce repo public + fixtures `zz-`. Elle n'a pas le
newsroom privé, donc elle ne peut PAS reconstruire la prod. Elle ne fait que les
tests. **Aucune étape `wrangler`/`pages` dans les workflows.** La prod ne bouge
jamais toute seule après un `git push`.

## Le piège data

`site/public/data/` est **gitignored** (le corpus réel n'est jamais commité).
Pousser code + data sur `origin/main` ne met **rien du corpus en ligne**. La
source de vérité du corpus (dont le champ `dc.synthesis`) est
`../smdc-newsroom` — **committe ton travail là**, et il passera en ligne au
prochain `make deploy` local qui le relit.

## Le piège du diagnostic : ne JAMAIS vérifier la prod sur une URL `/data/`

`prune-public-json` remplace, à chaque déploiement, **tous** les JSON de `dist/data/` par un
bouchon `{"gone": true}` — c'est la protection anti-pillage (un `curl` sur `scores.json`
siphonnait le corpus entier). Les deux `.geojson` que la carte charge au runtime sont les
seules exceptions.

**Donc `/data/actu/latest.json`, `/data/dc/{id}.json` et `/data/scores.json` sont vides EN
PRODUCTION, par construction, et le resteront.** Les voir vides n'est pas un symptôme : c'est
le comportement attendu. Le contenu réel est *inliné dans le HTML* au build.

**Où l'on vérifie vraiment :**

| ce qu'on veut vérifier | l'URL qui fait foi |
|---|---|
| le mur d'actualité | `https://scoremydatacenter.org/fr/actu/` |
| une fiche, sa note, sa carte | `https://scoremydatacenter.org/fr/dc/{id}/` |
| le corpus servi | le compte de `site/public/data/dc/*.json` **en local**, après build |

Coût de ce piège le 2026-09-30 : deux alertes « les news ne sont pas en prod » remontées
jusqu'à Franck, sur un mur qui était en ligne et correct depuis le matin. Le vrai incident de
la veille (picks écrasés par le cron) était réel, mais il a été diagnostiqué sur le bon
endroit — la page — et c'est ce qui l'a rendu réparable en dix minutes.

## Le piège branche : `make deploy` depuis une branche ne va PAS en prod

Cloudflare Pages décide **production ou préversion d'après la branche git courante**.
Depuis une branche autre que `main`, `make deploy` réussit, affiche « Deployment
complete », purge le cache — et n'a rien mis en ligne. Le seul indice est une ligne
`Deployment alias URL: https://<nom-de-branche>.scoremydatacenter.pages.dev` au milieu
de la sortie, facile à manquer.

**Donc : `git branch --show-current` avant tout `make deploy`, et `main` ou rien.**
Puis vérifier sur le domaine réel, jamais sur l'URL rendue par wrangler :

```
curl -s -o /dev/null -w '%{http_code}\n' https://scoremydatacenter.org/fr/dc/<une-fiche-du-lot>/
```

Incident du 2026-09-28 : lot de 16 fiches déployé depuis `geo-audit-probe`, annoncé
« complet » par wrangler, et 404 en production. Rattrapé avant d'être rapporté, parce
que la vérification sur le domaine réel faisait partie de la procédure.

## UN ARBRE DE TRAVAIL PAR AGENT — et `scoremydatacenter/` ne sert qu'à déployer

Plusieurs agents travaillent sur la même machine. Pendant longtemps ils partageaient le
MÊME répertoire git, et ça a coûté quatre incidents en une seule journée (2026-10-01) :

1. une branche a embarqué le commit d'un autre agent sans que son auteur le voie ;
2. une branche s'est créée sur un commit non mergé d'un tiers — la construire dessus
   aurait **annulé une demi-journée de travail** déjà mergé ;
3. un `main` local périmé a fait disparaître un module de l'arbre, au milieu d'un run ;
4. une branche a été remise à `origin/main` pendant que son auteur y travaillait ; son
   commit n'a survécu que comme objet git orphelin, poussé à la main.

Trois des quatre n'ont été rattrapés que parce que quelqu'un a pensé à lire `git log` avant
de commencer. **C'est un garde-fou humain, pas une protection.**

### La règle

- **`scoremydatacenter/` reste sur `main` et ne sert QU'AU DÉPLOIEMENT.** Personne n'y
  travaille, personne n'y crée de branche.
- **Chaque agent travaille dans son propre arbre**, créé au niveau des dépôts frères :

```
git worktree add --detach ../.wt-<nom-agent> main
```

Le `..` compte : les arbres vivent à côté de `scoremydatacenter/` et de `smdc-newsroom/`,
donc `../smdc-newsroom` continue de résoudre — le moteur, le pipeline et le build y
fonctionnent à l'identique. Un arbre placé ailleurs casserait silencieusement tout ce qui
lit le corpus privé.

### Pourquoi le déploiement reste dans le répertoire d'origine

Cloudflare Pages décide **production ou préversion d'après la branche git courante** (voir
le piège branche plus bas). Un arbre en `HEAD` détaché ne porte pas le nom `main` : un
`make deploy` lancé depuis un arbre de travail publierait une préversion en silence, et
tout aurait l'air d'avoir réussi. Le seul endroit où `main` est réellement sorti, c'est
`scoremydatacenter/` — et c'est donc le seul endroit d'où l'on déploie.

## Prérequis machine (celle qui déploie)

- `../smdc-newsroom` monté (corpus + calibration).
- `~/.smdc/media.env` (clés R2 — secret HORS repos, chmod 600) pour les photos sat.
  Sans lui : deploy OK, photos sat non régénérées (non bloquant).
- `wrangler` authentifié sur le projet Cloudflare Pages `scoremydatacenter`.

Une session sans ces trois éléments **ne peut pas** déployer — elle push, un
mainteneur avec le montage lance `make deploy`.

## ⚠️ UN SEUL run à la fois — le pipeline média n'est PAS concurrency-safe

Toutes les sessions (agents inclus) tournent sur **la même machine** et partagent
`~/.smdc/media.env`. Donc **n'importe quelle** session lançant `make deploy`,
`make prod-artifacts` ou `make build` déclenche `media-sat --upload` avec les
mêmes creds R2. Deux runs simultanés se battent sur R2 et sur les tuiles Esri →
`ConnectionReset`, uploads échoués, photos manquantes (vécu le 2026-07-21 :
un `make prod-artifacts` lancé par un autre agent en parallèle du deploy).

Règle : **une seule** de ces commandes tourne à un instant donné. Avant de lancer,
vérifie qu'aucun run média n'est en cours :

```
pgrep -fl "satellite|prod-artifacts" || echo "safe"
```

La reprise est sûre : le manifest `.media-sat/uploaded.txt` (append-on-succès)
fait sauter les photos déjà sur R2, donc relancer après un run interrompu ne
regénère que ce qui manque. **Répartition** : la moisson du corpus (scores,
synthèses → newsroom) et la génération média + `make deploy` (→ R2 + Cloudflare)
sont deux lanes distinctes ; elles ne doivent pas tourner en même temps.

## Gate qui casse le deploy

**Gate 7 (prose)** : `build_artifacts` lève une `GateError` si une synthèse cite
une lettre A–E dans son texte. La lettre appartient au badge, la prose porte le
*pourquoi*. Une synthèse fautive **bloque tout le déploiement**.

## Statut juridique (au 2026-07-20) — pas de verrou de publication

- **A-24 = droit de réponse, RETIRÉ** à la revue juridique du 2026-07-15. Les
  notes se publient directement. Ce n'est **pas** un verrou « ne pas publier ».
- Les fiches **D/E réelles sont déjà publiques** (noindex levé le 2026-07-16). Une
  synthèse par-dessus une fiche D/E déjà en ligne ne franchit aucune ligne neuve.
- **Seul TODO avocat ouvert** : ToS Esri sur l'imagerie satellite (`7-juridique`).
  Non bloquant pour les fiches/synthèses — l'imagerie est déjà en prod, créditée.

Toute note « verrou avocat / NE PAS PUBLIER » plus ancienne est **obsolète**.
