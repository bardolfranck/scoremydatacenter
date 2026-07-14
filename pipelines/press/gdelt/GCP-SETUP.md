# GDELT via BigQuery — la config GCP en 3 gestes (une seule fois)

**Pourquoi** (A-23) : l'API DOC de GDELT est bridée (1 req/5 s, pénalités prolongées par IP —
vécu deux fois). BigQuery lit le même corpus **en bulk, sans rate-limit, gratuitement** dans
le quota mensuel (1 To de scan offert ; notre requête bornée à 8 jours scanne quelques Go).
Le SQL est versionné ici (`query.sql`), le lourd tourne chez GCP, notre code ne fait que lire
un fichier — aucune dépendance cloud dans le repo.

```
GCP (planifié) : query.sql → BigQuery (gdelt-bq public) → export JSONL → bucket GCS
Nous           : make refresh-signal GDELT_BQ=<url-ou-fichier> → review → gate → carte
```

## Geste 1 — le bucket (2 min)

Console GCP → Cloud Storage → **Create bucket** :
- nom : `smdc-gdelt` (région `europe-west1`, classe Standard) ;
- accès **privé** (uniform), pas d'accès public.

## Geste 2 — la requête planifiée (5 min)

Console GCP → BigQuery → onglet **Scheduled queries** → **Create** :
1. Colle le contenu de [`query.sql`](query.sql) (le dataset `gdelt-bq` est public — rien à installer).
2. Planification : **tous les jours à 06:00 Europe/Paris** (la requête couvre 8 jours → tolère les trous).
3. Destination : table `smdc.gdelt_hits` (**overwrite**), dataset dans ton projet, région EU.
4. Ajoute une seconde étape d'export — le plus simple est de cocher, dans la scheduled query,
   « export to GCS » si proposé, sinon planifie la variante EXPORT :
   ```sql
   EXPORT DATA OPTIONS(
     uri='gs://smdc-gdelt/gdelt_hits-*.json',
     format='JSON', overwrite=true
   ) AS
   -- (coller ici le SELECT complet de query.sql)
   ```

## Geste 3 — l'accès lecture (3 min)

Console GCP → IAM → **Service account** `smdc-reader` :
- rôle : `Storage Object Viewer` sur le bucket `smdc-gdelt` **uniquement** ;
- crée une clé JSON → stocke-la en **secret GitHub Actions** (`GCP_SMDC_READER`), jamais dans le repo.

Pour un usage manuel immédiat sans clé : génère une **URL signée** (bouton « … » sur l'objet →
Sign URL, validité 7 j) et passe-la au reader.

## Côté repo (déjà câblé — rien à faire)

```bash
# avec une URL signée ou un fichier local téléchargé :
uv run python -m pipelines.press.collect_signal --gdelt-bq 'https://storage.googleapis.com/…' \
    --out ../smdc-newsroom/drafts/watchlist
```

Le lecteur `signal.fetch_gdelt_bq()` produit des records `kind:"article"` identiques au feed
DOC : le reste du workflow (review LLM → gate humain → géocodage → carte) **ne bouge pas**.
DÉTECTION seulement (A-21) : ces articles sont des pistes de triage, jamais un intrant de score.

**Anti-piège quota** : ne jamais retirer la borne `_PARTITIONTIME` du SQL — un scan non borné
de `gkg_partitioned` consomme le To gratuit en une exécution.
