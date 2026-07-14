-- SPDX-License-Identifier: AGPL-3.0-or-later
-- Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
-- https://scoremydatacenter.org · independent data center acceptability-risk score
--
-- GDELT press detection, CONTESTATION variant — the BigQuery route (A-23).
-- The DOC API is hard-throttled (429/slow-walk on any sustained use); this SQL runs as a
-- BigQuery Scheduled Query on the public `gdelt-bq` dataset and exports JSONL to a private
-- GCS bucket. Our reader (pipelines/press/signal.py: fetch_gdelt_bq) consumes the export —
-- no cloud dependency in our code, no rate limit, the SQL is reviewed in git like any parser.
--
-- DETECTION only (A-21): output rows are triage leads for the human gate, never a score input.
-- Always partition-bounded (last 8 days for a daily schedule) — an unbounded scan of gkg eats
-- the whole free quota in one run.
--
-- v1 recall-oriented: URL slug carries a data-center term in any of 11 languages
-- (en/fr/de/nl/es/it + pt/pl/fi/no/sv-da via datacenter/datasenter/datakeskus/datahall/centrum-danych) AND the GKG
-- themes carry an opposition/decision signal. Precision is the reviewer's job (recall THEN
-- precision, same doctrine as voie A). Tune terms per country as real noise arrives.

WITH hits AS (
  SELECT
    DocumentIdentifier AS url,
    SourceCommonName   AS domain,
    DATE               AS seendate,
    V2Locations        AS locations,
    V2Themes           AS themes,
    IFNULL(TranslationInfo, '') AS translation_info,
    V2Organizations    AS organizations
  FROM `gdelt-bq.gdeltv2.gkg_partitioned`
  WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 8 DAY)
    -- a data-center term in the URL slug (en/fr/de/nl/es/it) — cheap and language-robust
    AND REGEXP_CONTAINS(LOWER(DocumentIdentifier),
        r'data-?cent(er|re)|datacenter|rechenzentrum|centre-de-donnees|centro-de-datos|centro-dati|datacentrum|centro-de-dados|centrum-danych|datakeskus|datasenter|datahall')
    -- an opposition / public-decision signal in the GKG themes
    AND REGEXP_CONTAINS(V2Themes,
        r'PROTEST|OPPOSITION|MORATORIUM|SELF_IDENTIFIED_ENVIRON_DISASTER|WB_2432|LEGISLATION|GENERAL_GOVERNMENT|ENV_')
    -- at least one mentioned location in Europe (project country, not outlet country):
    -- V2Locations format is type#name#countrycode#...; FR/BE/CH/LU/DE/NL/IE/GB/ES/IT/PT/AT/DK/SE/FI/NO/PL
    AND REGEXP_CONTAINS(V2Locations,
        r'#(FR|BE|SZ|LU|GM|NL|EI|UK|SP|IT|PO|AU|DA|SW|FI|NO|PL)#')
)
SELECT url, domain, seendate, locations, themes, translation_info, organizations
FROM hits
-- one row per url (gkg re-processes updated pages)
QUALIFY ROW_NUMBER() OVER (PARTITION BY url ORDER BY seendate DESC) = 1
LIMIT 2000
