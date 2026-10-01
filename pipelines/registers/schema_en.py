# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Le VOCABULAIRE PUBLIC du JSON des registres : clés en anglais, libellés localisés.

Décision Franck, 2026-10-01 : « les champs du JSON doivent être en anglais, en prévision de
l'API ». Le corps du moteur reste en français — c'est la langue de l'équipe et des sources —
mais ce qui FRANCHIT la frontière du produit est en anglais, une fois pour toutes.

TROIS RÈGLES DE NOMMAGE, et elles ne sont pas cosmétiques :

1. **L'unité est dans le nom.** `grid_connection_voltage_kv`, pas `voltage`. Un consommateur
   d'API qui lit `voltage: 225` ne sait pas s'il tient des volts ou des kilovolts, et il
   finira par le deviner. Trois des faux qu'on a corrigés cette semaine étaient des
   confusions d'unité ; le nom est la première défense.

2. **Le périmètre est dans le nom.** `backup_generator_total_installed_power_mw` ne peut
   pas être confondu avec la puissance du site. C'est l'erreur que l'extraction indépendante a elle
   aussi signalée : 405 MW de secours pris pour la puissance du projet.

3. **Ce qui est DÉCLARÉ le dit.** `reported_data_hall_power_mw` plutôt que `it_power_mw` :
   l'avis de Tremblay emploie le même chiffre — 105 MW — pour la puissance des salles
   informatiques (p. 10) et pour le raccordement au réseau (p. 14). Le document ne permet
   pas de trancher, donc le nom ne tranche pas non plus. `it_power_mw` reste disponible
   pour le jour où une source le dira vraiment.

Les libellés humains ne disparaissent pas : ils deviennent `label: {fr, en}`, comme partout
ailleurs dans le moteur (`methodology.json`).
"""

from __future__ import annotations

# ── Clés d'enveloppe ────────────────────────────────────────────────────────────────────────
ENVELOPE: dict[str, str] = {
    "source": "source",
    "doc_url": "doc_url",
    "registre": "register",
    "region": "region",
    "licence": "licence",
    "pdf": "pdf",
    "pages": "pages",
    "caracteres": "characters",
    "couche_texte": "text_layer",
    "ocr": "ocr",
    "sha256": "sha256",
    "origine": "origin",
    "region_detectee": "region_detected",
    "sources_alternatives": "alternative_sources",
    "procedure": "procedure",
    "intitule": "title",
    "commune": "municipality",
    "insee": "insee_code",
    "departement": "department",
    "petitionnaire": "applicant",
    "statut": "status",
    "date_reception": "received_on",
    "date_avis": "opinion_date",
    "numero_avis": "opinion_number",
    "centroid": "centroid",
    "installation": "installation",
    "faits": "facts",
    "recommandations_autorite": "authority_recommendations",
    "avertissements": "warnings",
    "texte": "text",
    "credit": "credit",
    # dans un fait
    "indicateur": "indicator",
    "libelle": "label",
    "theme": "theme",
    "valeur": "value",
    "unite": "unit",
    "phrase": "evidence_excerpt",
    "page": "page_pdf",
    # traces d'opérations
    "revalidation": "revalidation",
    "derivation_bruit": "noise_derivation",
    "dedup": "deduplication",
}

# ── Thèmes ──────────────────────────────────────────────────────────────────────────────────
THEMES: dict[str, str] = {
    "energie": "energy",
    "secours": "backup_power",
    "bruit": "noise",
    "chaleur": "waste_heat",
    "eau": "water",
    "foncier": "land",
    "climat": "climate",
    "air": "air",
    "voisinage": "neighbourhood",
    "biodiversite": "biodiversity",
    "sols": "soil",
    "risques": "hazards",
    "emploi": "employment",
    "procedure": "regulatory",
}

# ── Indicateurs ─────────────────────────────────────────────────────────────────────────────
INDICATORS: dict[str, str] = {
    # énergie
    "puissance_it_mw": "reported_data_hall_electrical_power_mw",
    "puissance_site_mw": "reported_site_power_demand_mw",
    "consommation_gwh_an": "annual_electricity_consumption_gwh",
    "pue": "reported_pue",
    "raccordement_kv": "grid_connection_voltage_kv",
    # secours au fioul
    "groupes_nombre": "backup_generator_count",
    "groupes_puissance_unitaire_mw": "backup_generator_unit_power_mw",
    "groupes_puissance_totale_mw": "backup_generator_total_installed_power_mw",
    "groupes_carburant": "backup_generator_fuel",
    "cuves_nombre": "fuel_tank_count",
    "cuves_volume_unitaire_m3": "fuel_tank_unit_volume_m3",
    "cuves_volume_total_m3": "fuel_storage_total_volume_m3",
    "cuves_enterrees": "fuel_tanks_buried",
    "autonomie_heures": "backup_autonomy_hours",
    "essais_groupes": "generator_periodic_testing",
    # bruit
    "bruit_bandes": "noise_levels_by_point",
    "bruit_emergence_bandes": "noise_emergence_by_period",
    "bruit_niveau_dba": "noise_level_dba",
    "bruit_emergence_dba": "noise_emergence_dba",
    "bruit_emergence": "noise_emergence_mentioned",
    "bruit_point_mesure": "noise_measurement_points",
    "bruit_zer": "noise_regulated_zones",
    # chaleur fatale
    "chaleur_fatale_mw_th": "waste_heat_mw_thermal",
    "chaleur_valorisation": "waste_heat_recovery_status",
    "reseau_chaleur_distance": "district_heating_distance_m",
    # eau
    "eau_m3_an": "annual_water_consumption_m3",
    "refroidissement_type": "cooling_technology",
    "rejets_aqueux": "water_discharge_mentioned",
    "eaux_pluviales": "stormwater_management_mentioned",
    # foncier
    "parcelle_ha": "site_area_ha",
    "emprise_sol_m2": "building_footprint_m2",
    "surface_plancher_m2": "gross_floor_area_m2",
    "surface_salles_m2": "data_hall_area_m2",
    "surface_locaux_techniques_m2": "technical_rooms_area_m2",
    "hauteur_m": "building_height_m",
    "artificialisation": "land_take_mentioned",
    # climat et air
    "ges_teqco2": "ghg_emissions_tco2e",
    "fluides_frigorigenes": "refrigerants_mentioned",
    "fuites_frigorigenes_t": "refrigerant_leakage_t",
    "nox": "air_pollutants_mentioned",
    "qualite_air_campagne": "air_quality_survey_mentioned",
    # voisinage
    "habitations_distance_m": "nearest_dwellings_distance_m",
    "etablissement_sensible_distance_m": "nearest_sensitive_receptor_distance_m",
    "etablissements_sensibles": "sensitive_sites_mentioned",
    "trafic_pl": "hgv_traffic_mentioned",
    # biodiversité et sols
    "natura2000": "protected_areas_mentioned",
    "zones_humides": "wetlands_mentioned",
    "especes_protegees": "protected_species_mentioned",
    "pollution_sols": "soil_contamination_mentioned",
    "pfas": "pfas_mentioned",
    # risques et procédure
    "incendie": "fire_risk_mentioned",
    "icpe_rubriques": "icpe_categories",
    # emploi
    "emplois_effectif": "reported_onsite_operational_headcount",
    "emplois_mention": "employment_mentioned",
}

# ── Valeurs d'énumération ───────────────────────────────────────────────────────────────────
# Les valeurs d'enum FRANCHISSENT aussi la frontière : « étude » dans une API anglophone est
# aussi opaque qu'une clé française.
ENUM_VALUES: dict[str, str] = {
    "huile végétale hydrotraitée (HVO)": "hvo",
    "fioul domestique": "domestic_fuel_oil",
    "gazole non routier": "non_road_diesel",
    "fioul/gazole": "fuel_oil_or_diesel",
    "contrat/raccordement": "contracted",
    "étude": "under_study",
    "aucune": "none",
    "adiabatique (consommateur d'eau)": "adiabatic",
    "free-cooling / air": "free_cooling",
    "circuit fermé": "closed_loop",
}


def unknown_indicators(field_ids) -> list[str]:
    """Les identifiants qui n'ont pas de traduction — un champ ajouté sans passer ici.

    Un identifiant français qui atteindrait l'API serait une fuite de vocabulaire interne
    dans un contrat public, et il y resterait : les consommateurs s'y adossent. Ce contrôle
    est fait pour être appelé par un test, pas par un humain attentif.
    """
    return sorted(set(field_ids) - set(INDICATORS))


# ────────────────────────────────────────────────────────────────────────────────────────────
# CONTRAT v0.1 — les trois vocabulaires qui manquaient
#
# Issus d'une revue contradictoire avec une extraction indépendante (2026-10-01). Déclarés ici
# AVANT d'être câblés : un contrat public se fige d'abord et se remplit ensuite, l'inverse
# oblige à renommer après publication.
# ────────────────────────────────────────────────────────────────────────────────────────────

# 1. TROIS DIMENSIONS ORTHOGONALES, et non quatre statuts exclusifs.
#    Mon premier jet mélangeait les plans : `reported` / `authority_assessment` /
#    `gap_identified` / `derived` ne s'excluent pas. Une LACUNE est presque toujours une
#    appréciation de l'autorité ; une valeur DÉRIVÉE décrit une transformation, pas un
#    locuteur. Trois axes indépendants, chacun répondant à une question distincte.

ASSERTION_ORIGIN = (
    "project_file",             # le dossier du maître d'ouvrage, rapporté par l'avis
    "environmental_authority",  # l'autorité parle en son nom propre
    "extractor",                # nous — et seulement pour une transformation, jamais un fait
    "unknown",                  # locuteur ambigu : on ne force pas, on le dit
)

CLAIM_TYPE = (
    "measurement",      # une mesure réalisée (campagne acoustique, piézomètre)
    "estimate",         # une prévision (consommation attendue, PUE visé)
    "commitment",       # un engagement pris (mesure ERC, raccordement contractualisé)
    "assessment",       # une appréciation de l'autorité
    "gap",              # une information manquante, relevée comme telle
    "recommendation",   # une recommandation formelle
)

TRANSFORMATION = (
    "verbatim",     # la valeur telle qu'écrite
    "normalized",   # même grandeur, unité ou format canonique
    "derived",      # calculée à partir d'autres faits — formule et sources obligatoires
)

# 2. LES ÉTATS D'ABSENCE. C'est le vocabulaire le plus important du contrat, et il vient de
#    l'erreur la plus coûteuse de la semaine : une panne du moteur de recherche lue comme
#    « cette région n'a pas d'avis ». Sans ces états, l'API transforme nos propres pannes en
#    information sur le projet. Un champ vide doit TOUJOURS dire pourquoi il est vide.

ABSENCE_STATE = (
    "not_disclosed",            # le document existe, il ne donne pas l'information
    "not_found_after_review",   # relu exhaustivement, l'information n'y est pas
    "not_extracted",            # notre extracteur ne sait pas la lire — notre limite, pas la sienne
    "source_unavailable",       # le document n'a pas pu être atteint
    "unreadable",               # atteint mais sans couche texte exploitable
    "not_applicable",           # la notion n'existe pas pour ce projet
    "not_reviewed",             # pas encore examiné
)

# 3. CHAMPS RÉSERVÉS — nommés maintenant, construits ensuite.
#    `sensitive_receptors` remplacera `nearest_sensitive_receptor_distance_m` : un scalaire ne
#    peut pas porter « un lycée à 15 m de l'INSTALLATION » et « des habitations à 200 m du
#    SITE » — deux objets, deux références de mesure. L'avis de Tremblay donne les deux, et
#    les fondre en un seul nombre serait exactement l'erreur qu'on reproche aux autres.
RESERVED: dict[str, str] = {
    "sensitive_receptors": (
        "collection [{type, name, distance_m, distance_reference}] — remplace le scalaire "
        "nearest_sensitive_receptor_distance_m ; distance_reference ∈ {installation, project_site}"
    ),
    "qualifier": (
        "nuance portée par la source et jamais effacée : approximately, maximum_scenario, "
        "planned, estimated — « environ 90 personnes » n'est pas « 90 emplois »"
    ),
    "it_power_mw": (
        "réservé : aucune source ne l'a encore établi sans ambiguïté. L'avis de Tremblay "
        "emploie le même 105 MW pour les salles informatiques et pour le raccordement."
    ),
}
