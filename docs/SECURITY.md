<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter -->

# Anti-pillage & posture de sécurité (doctrine A-28)

> Principe (P6) : la vérité est publique et gratuite à LIRE (HTML) ; le **bulk
> machine-lisible** est protégé — il sera vendu par l'API, jamais donné.
> On ne cache pas la donnée, on rend son **aspiration en masse** pénible.

## 1. Une seule porte machine — pas de JSON brut servi

- **Le site sert du HTML, jamais les fichiers de données bruts.** `make build`
  purge `site/dist/data/` : ne restent que les deux geojson que la carte charge
  au runtime (`map.geojson`, `watchlist.geojson`). Tout le bulk (scores.json =
  le corpus entier, `dc/*.json`, indices, stats, home_showcase, methodology,
  audit) — déjà **inliné dans le HTML** au build — est retiré du déployé
  (`prune-public-json`). Un `curl` ne peut plus « tout aspirer d'un coup ».
- **`map.geojson` réduit au plancher gratuit « Seau A »** : `id, name, operator,
  municipality, country, grade_site` (la LETTRE seule), `project_status`,
  `size_tier` (rang de taille grossier, pas la puissance MW), coordonnées
  **arrondies à ~1 km**. Retirés (vendus par l'API, « Seau B ») : note
  opérateur, scores par pilier, `power_mw` exact, citation, confiance, GPS
  précis. Gate CI : `engine/tests/test_public_data_floor.py` **casse le build**
  si un champ vendable ou du GPS précis réapparaît dans le geojson public.
- **`site/public/_headers`** force `Cache-Control: no-store` sur `/data/*.json` :
  si un fichier brut est un jour ré-exposé par erreur, il ne peut plus devenir
  un cache long (le piège des 7 jours vécu le 2026-07-22).

## 2. Cache — la purge de zone ne suffit pas

Une mise en ligne Cloudflare Pages **n'évince pas** le cache d'un fichier
*retiré* (ni « Purge Everything », ni la purge par URL ne l'atteignent : c'est
la couche d'assets Pages). Deux garde-fous :

- `make deploy` lance `purge-cache` (API Cloudflare) sur les `/data/*.json` si
  `~/.smdc/cloudflare.env` porte un token `Zone > Cache Purge : Edit` + la
  zone id. Sinon : skip avec avertissement.
- De toute façon **auto-guérison** : l'origine renvoyant 404 + `no-store`, tout
  cache résiduel expire et **ne peut plus se re-remplir**.

## 3. Bots & débit (activés dashboard 2026-07-22)

- **Bot Fight Mode** : ON (Security → Bots). Challenge automatique des robots.
- **Rate-limiting rule `anti-scrape`** (Security → WAF) :
  - Expression : `(http.request.uri.path contains "/dc/") or (starts_with(http.request.uri.path, "/data/"))`
  - Seuil : **10 requêtes / 10 s par IP** → **Block** (60 s).
  - **Prouvé en prod** : rafale de 30 requêtes → 10× `200` puis `429`.
  - Seuil « humain jamais, scraper mort » : un scraper des 1269 fiches fait des
    centaines de req/s (bloqué en <1 s) ; un humain reste sous 5/10 s. Ne PAS
    descendre sous 10 — le rate-limit est par IP, et une entreprise/université/4G
    partage une IP (NAT) + Astro précharge les liens au survol.

## 4. Ce qu'on assume (limites saines de l'ouverture)

Un scraper déterminé peut toujours reconstruire les **notes de base** en parsant
1269 pages HTML (lent, pénible, rate-limité) ou depuis `map.geojson`. C'est le
prix de la transparence, et c'est voulu : la valeur payante n'est pas
l'exclusivité des notes (publiques par principe), c'est le **dossier structuré
riche + le confort bulk/export/fraîcheur** vendu par l'API (Worker), seule porte
machine vers le Seau B.

## 5. Détecter un pillage

- **Cloudflare → Analytics & Logs → Traffic** : un pic de bande passante ou de
  requêtes concentré sur `/dc/*` ou `/data/*`, ou une IP/ASN qui explose.
- **GA4 est aveugle aux scrapers** (pas de JS, pas de consentement) — ne pas s'y fier.
- Logs bruts requête-par-requête = Logpush (Enterprise) — non disponible ici.

## TODO
- Révoquer le token cache-purge exposé le 2026-07-22 (format de fichier) et en
  recréer un propre dans `~/.smdc/cloudflare.env`.
- Le Worker/API (Seau B payant) — chantier séparé.
