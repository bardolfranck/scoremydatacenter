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
