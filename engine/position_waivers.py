# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""DETTE DE POSITION — les paires de fiches qui occupent le MÊME POINT sans qu'on ait tranché.

Deux fiches à moins d'un mètre, c'est l'un de ces trois cas, et il faut dire lequel :
  · la MÊME installation saisie deux fois (un doublon public, le pire des trois) ;
  · deux halls d'un même campus (légitime) ;
  · deux opérateurs dans un même immeuble (légitime, et plus fréquent qu'on ne croit).

Rien ne les distingue depuis la coordonnée seule : il faut une source — adresse postale,
registre, relevé de terrain. C'est pourquoi le gate n'exige pas une absence de paires, mais
une ADJUDICATION : `position_adjudication` dans la provenance de l'une des deux fiches, avec
son verdict, sa base et sa source. Le patron a été posé par agent-data-pipeline-EU sur les
13 britanniques du 2026-10-02.

CETTE LISTE EST UNE DETTE, PAS UNE RÈGLE. Elle recense les paires déjà SERVIES au jour où le
gate a été câblé — trouvées parce que je retenais 13 fiches britanniques au nom d'un standard
que le reste du corpus n'avait jamais eu à respecter. Elle n'autorise rien de nouveau : toute
paire qui n'y figure pas est refusée. Elle doit DÉCROÎTRE, et le gate imprime son compte à
chaque passage pour qu'on ne l'oublie pas.

Au 2026-10-02 : 78 paires dans le corpus servi. 6 britanniques puis 38 autres hors-France
(agent-data-pipeline-EU, adjudication sur adresses PeeringDB) sont tranchées et passent au
mérite. RESTENT 34 : les 25 françaises (agent-data-pipeline-FR) et 9 suisses dont la position
est à corriger avant de trancher (géo de géocodeur probable : la paire disparaît une fois le
point posé sur le bâtiment — la trancher avant documenterait un artefact).

Quelques-unes, vérifiées à la main, ressemblent très fort à la même fiche deux fois :
  fr-celeste-marylin / fr-marilyn-celeste · fr-colt-paris-sw / fr-colt-paris-sw-dh10
  de-net-build-datacenter-saarwellingen / de-net-build-gmbh
Elles sont publiques aujourd'hui — `publication.status = "draft"` est servi en prod.
"""

from __future__ import annotations

# Clé : les deux identifiants TRIÉS. Valeur : la date du constat et ce qu'on en sait.
POSITION_WAIVERS: dict[tuple[str, str], str] = {
    ('ch-equinix-zh2',
     'ch-exa-infrastructure-zurich'): '2026-10-02 — même opérateur, jamais tranchée',
    ('ch-equinix-zh4',
     'ch-exa-infrastructure-zurich'): '2026-10-02 — même opérateur, jamais tranchée',
    ('ch-evok-dc01',
     'ch-evok-dc02'): '2026-10-02 — même opérateur, jamais tranchée',
    ('ch-green-datacenter-zurich-metro',
     'ch-stack-infrastucture-zurl1'): '2026-10-02 — même opérateur, jamais tranchée',
    ('ch-infomaniak-dii',
     'ch-infomaniak-diii'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-agarik-atos-4',
     'fr-agarik-atos-5'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-celeste-armor',
     'fr-etix-everywhere-nantes-1'): '2026-10-02 — opérateurs différents, jamais tranchée',
    ('fr-celeste-marylin',
     'fr-marilyn-celeste'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-cloud-hq-france-projet-cdg-1',
     'fr-cloud-hq-france-projet-cdg-2'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-colt-paris-sw',
     'fr-colt-paris-sw-dh10'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-colt-villebon-par-2',
     'fr-colt-villebon-par-3'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-colt-villebon-par-2',
     'fr-colt-villebon-par-4'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-colt-villebon-par-3',
     'fr-colt-villebon-par-4'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-digital-realty-les-ulis-dc1-et-2-par-13',
     'fr-digital-realty-les-ulis-projet-dc2'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-eolas-mangin-1',
     'fr-eolas-mangin-2'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-equinix-ibx-pa4',
     'fr-ibx-pa8x'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-etix-everywhere-nantes-2',
     'fr-sigma-carquefou'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-global-switch-paris-est',
     'fr-global-switch-paris-ouest'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-goodman-1-projet',
     'fr-goodman-2-projet'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-interxion-digital-reality-par3',
     'fr-interxion-digital-reality-par5'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-interxion-digital-reality-par8',
     'fr-interxion-par10'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-interxion-digital-reality-par8',
     'fr-interxion-par11'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-interxion-digital-reality-par8',
     'fr-interxion-par9'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-interxion-par10',
     'fr-interxion-par11'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-interxion-par10',
     'fr-interxion-par9'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-interxion-par11',
     'fr-interxion-par9'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-lcp-fr-dc1-projet',
     'fr-lcp-fr-dc2-projet'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-lcp-fr-dc1-projet',
     'fr-lcp-fr-dc3-projet'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-lcp-fr-dc2-projet',
     'fr-lcp-fr-dc3-projet'): '2026-10-02 — même opérateur, jamais tranchée',
    ('fr-th3-paris-magny',
     'fr-th3-paris-magny-2'): '2026-10-02 — même opérateur, jamais tranchée',
}
