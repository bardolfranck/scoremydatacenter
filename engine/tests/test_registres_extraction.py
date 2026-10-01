# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Faux d'extraction trouvés À L'ÉCHELLE sur les avis MRAe — un test par CLASSE, portant la
PHRASE FAUTIVE RÉELLE (pas une phrase inventée).

Un correctif sans son test est une rustine ; avec la phrase réelle, c'est un invariant qui
résiste à la prochaine refonte des motifs. Chaque faux est rejeté PARCE QUE la phrase ne dit
pas ce que le champ affirme — jamais parce que la valeur « a l'air » fausse. Et la phrase+page
sert autant à INNOCENTER (voir les deux cas blanchis en fin de fichier) qu'à accuser.

Méthode de découverte (contrôle à l'échelle sur 43 avis) : médiane/min/max de chaque champ
chiffré — un extrême absurde est le symptôme.
"""

from pipelines.registers import avis


def _vals(sentence: str) -> dict[str, object]:
    """Les faits extraits d'UNE phrase : {indicateur: valeur}. Multi-valeurs → liste."""
    a = avis.extract_from_pages([sentence], "https://example.test/avis.pdf")
    out: dict[str, object] = {}
    for f in a.facts:
        if f.field_id in out:
            cur = out[f.field_id]
            out[f.field_id] = cur + [f.value] if isinstance(cur, list) else [cur, f.value]
        else:
            out[f.field_id] = f.value
    return out


# ── CLASSE A — un SEUIL réglementaire ou une DÉFINITION n'est pas une mesure ────────────────

def test_classe_a_seuil_icpe_pas_une_parcelle():
    # Meudon : le « 1 ha » est le seuil de la rubrique ICPE 2.1.5.0, pas la parcelle.
    faux = ("Rubrique Intitulé de la rubrique Caractéristique de l’installation 2.1.5.0 Rejet "
            "d’eaux pluviales dans les eaux douces superficielles ou sur le sol ou dans le "
            "sous-sol, la surface totale du projet, augmentée de la surface correspondant à la "
            "partie du bassin naturel dont les écoulements sont interceptés par le projet, "
            "étant supérieure à 1 ha mais inférieure à 20 ha.")
    assert "parcelle_ha" not in _vals(faux)
    # garde anti-sur-correction : une vraie parcelle passe toujours (Tremblay).
    vrai = ("Ce projet s’implante dans la zone d’activités de Tremblay-Charles-de-Gaulle, sur "
            "une parcelle de 5,35 ha, occupée actuellement par des bâtiments logistiques.")
    assert _vals(vrai).get("parcelle_ha") == 5.35


def test_classe_a_definition_du_pue_pas_une_valeur():
    # Bailly-Romainvilliers : « proche de 1 » est la définition du PUE, pas le PUE du projet.
    faux = ("Plus l’indice « PUE » est proche de 1 et plus la performance énergétique du "
            "data-center est importante.")
    assert "pue" not in _vals(faux)
    # garde : un PUE réellement annoncé passe toujours (Magny-les-Hameaux).
    vrai = ("Concernant le site actuel TH3, le PUE est passé de 1,8 en 2018 à 1,67 en 2021 "
            "principalement en raison de l’optimisation des installations.")
    assert _vals(vrai).get("pue") == 1.8


# ── CLASSE B — bon nombre, mauvais objet ────────────────────────────────────────────────────

def test_classe_b_hauteur_ecran_acoustique_pas_du_batiment():
    # Les Ulis : 5 m est la hauteur d'un écran acoustique, pas d'un bâtiment.
    faux = ("Elles concluent que les niveaux sonores réglementaires seront respectés, sous "
            "réserve de la mise en œuvre de préconisations, parmi lesquelles la réalisation "
            "d’un écran acoustique d’une hauteur de 5 mètres en toiture du bâtiment DH10+.")
    assert "hauteur_m" not in _vals(faux)
    # garde : une vraie hauteur de bâtiment passe (Villebon-sur-Yvette).
    vrai = ("• la hauteur maximale des bâtiments, qui ne peut excéder 18 m à l’acrotère.")
    assert _vals(vrai).get("hauteur_m") == 18.0


def test_classe_b_volume_eaux_pluviales_pas_du_fioul():
    # Rungis : 220 m³ est un volume d'eaux pluviales infiltrées, pas de carburant.
    faux = ("Le volume de gestion de ces eaux traitées par infiltration sera de 220 m3, pour "
            "des pluies décennales, le volume total des pluies infiltrées sera de 785 m3.")
    assert "cuves_volume_total_m3" not in _vals(faux)
    # garde : un vrai volume total de fioul passe (Marcoussis, 45 cuves).
    vrai = "• 45 cuves de fioul domestique enterrées, représentant un volume total de 2 260 m3;"
    assert _vals(vrai).get("cuves_volume_total_m3") == 2260.0


def test_classe_b_eau_extinction_horaire_pas_conso_annuelle():
    # Ferrières-en-Brie : 60 m³/HEURE d'eau d'extinction incendie, pas une conso annuelle.
    faux = "Les besoins en eau d’extinction sont estimés à 60m3/heure."
    assert "eau_m3_an" not in _vals(faux)
    # garde : une vraie conso annuelle passe (phrase « par an »).
    vrai = ("L’humidification des salles sera réalisée via un système de refroidissement "
            "adiabatique, consommation d’eau estimée à 314 m3 par an.")
    assert _vals(vrai).get("eau_m3_an") == 314.0


# ── CLASSE C — un total de SITE ou de projet MIXTE n'est pas la tranche décrite ──────────────

def test_classe_c_agregat_de_site_refuse():
    # Marcoussis : 151 GE et 87 cuves sont les totaux des 23 data centers du site, pas de
    # l'extension examinée. On ne répartit pas au prorata — les comptes restent vides.
    faux = ("Avec cette nouvelle extension, vingt-trois data centers au total seront en "
            "capacité de fonctionner sur le site qui comprendra 151 groupes électrogènes et "
            "87 cuves enterrées pouvant stocker 3 880 m3 de fioul afin d’assurer un "
            "fonctionnement des serveurs informatiques en continu.")
    v = _vals(faux)
    assert "groupes_nombre" not in v
    assert "cuves_nombre" not in v
    # garde : un vrai compte de projet passe (Tremblay, 54 GE).
    vrai = ("Afin d’assurer un fonctionnement en continu du centre de données en cas de "
            "défaillance du réseau électrique, 54 groupes électrogènes sont prévus.")
    assert _vals(vrai).get("groupes_nombre") == 54.0


def test_classe_c_emplois_projet_mixte_refuses():
    # Courbevoie « Village Delage » : 8 000 emplois sont ceux d'un projet urbain mixte
    # (logements + équipements + activités), pas du data center.
    faux = ("Sur un site d’environ quinze hectares initialement à vocation industrielle, et "
            "après démolition de l’existant, le projet « Village Delage » prévoit la "
            "construction de 80 000 m2 de logements, 20 000 m2 d’équipements publics (groupe "
            "scolaire, crèche, gymnase, locaux culturels ou associatifs) et de commerces de "
            "proximité, 200 000 m2 d’activités (environ 8 000 emplois), ainsi qu’un parc "
            "urbain d’un hectare.")
    assert "emplois_effectif" not in _vals(faux)


# ── CLASSE D — confusion d'unité : t éq. CO2 ≠ tonnes de frigorigène ─────────────────────────

def test_classe_d_teqco2_pas_une_masse_de_frigorigene():
    # Aulnay : « 500 t eq. » est un équivalent CARBONE, pas 500 tonnes de fluide frigorigène.
    # On le rejette de ce champ sans le router d'office vers ges_teqco2 (ce serait interpréter).
    faux = ("À cela, il faut ajouter les fuites de fluide frigorigène à hauteur d’environ "
            "500 t eq.")
    assert "fuites_frigorigenes_t" not in _vals(faux)


# ── Les deux cas BLANCHIS : la phrase+page innocente autant qu'elle accuse ───────────────────

def test_cas_blanchis_restent_captes():
    # Argenteuil : « 30 emplois directs » est le vrai effectif, même dans une phrase sur le
    # stationnement — la valeur est juste, elle ne doit PAS tomber avec le correctif classe C.
    argenteuil = ("• justifier de la création de 147 places de stationnement pour toute ou "
                  "partie imperméabilisées alors que le projet prévoit 30 emplois directs et "
                  "que d’autres modes d’accès que la voiture particulière sont à envisager.")
    assert _vals(argenteuil).get("emplois_effectif") == 30.0
    # Lisses : « une puissance de 240 MW en phase finale » est réelle (gros projet 2 bâtiments).
    lisses = ("Deux bâtiments de 33 000 m2, 48 salles informatiques et une puissance de "
              "240 MW en phase finale.")
    assert _vals(lisses).get("puissance_it_mw") == 240.0


# ── REVALIDATION : ne retirer QUE le positivement rejeté, jamais un silence ──────────────────

def test_revalidation_retire_le_rejete():
    # Un fait dont la phrase déclenche une règle de rejet EST retiré (motif renvoyé).
    meudon = ("Rubrique Intitulé de la rubrique Caractéristique de l’installation 2.1.5.0 Rejet "
              "d’eaux pluviales dans les eaux douces superficielles, la surface totale du projet "
              "étant supérieure à 1 ha mais inférieure à 20 ha.")
    assert avis.rejection_reason("parcelle_ha", 1.0, meudon) is not None
    # Une valeur hors borne physique est positivement rejetée.
    assert avis.rejection_reason("groupes_nombre", 999.0, "999 groupes électrogènes.") is not None
    # Un champ retiré du schéma est positivement rejeté. (`bruit_nuit_dba` a été remplacé par
    # `bruit_bandes`. L'exemple était auparavant `puissance_site_mw` — rouvert depuis, parce
    # que l'étalon a démenti le 0/43 sur lequel je l'avais supprimé : « la puissance électrique
    # appelée (80 MW) », avis Interxion MRS4. Un champ vide n'était pas une notion absente.)
    assert avis.rejection_reason("bruit_nuit_dba", 54.5, "54,5 dB(A) en période nocturne.") is not None


def test_revalidation_garde_le_legitime_et_le_silence():
    # Un fait légitime dont la phrase ne déclenche aucun rejet est GARDÉ.
    vrai = ("Ce projet s’implante sur une parcelle de 5,35 ha, occupée par des bâtiments "
            "logistiques.")
    assert avis.rejection_reason("parcelle_ha", 5.35, vrai) is None
    # Et surtout : un fait qu'un rejeu ne reproduirait PAS, mais qu'aucune règle ne rejette,
    # reste en place — la non-reproduction est un silence, pas une preuve (règle du chef).
    silence = "L’autonomie électrique du site est de 72 heures."
    assert avis.rejection_reason("autonomie_heures", 72.0, silence) is None


# ── Couche texte POLLUÉE (U+200D à la place des espaces) : signalée, pas extraite en silence ──

def test_couche_texte_polluee_zwj_signalee_pas_extraite():
    normal = "Les niveaux acoustiques en limite de propriété sont de 60 dB(A) de jour. " * 60
    a = avis.extract_from_pages([normal], "https://example.test/a.pdf")
    assert a.has_text_layer is True          # texte sain (~14 % d'espaces) : extrait normalement
    assert a.facts

    # mêmes mots, espaces remplacés par des jointures invisibles (le piège de Bonneuil)
    pollue = normal.replace(" ", "‍")
    b = avis.extract_from_pages([pollue], "https://example.test/a.pdf")
    assert b.has_text_layer is False         # SIGNALÉ comme un scan…
    assert b.facts == []                     # …et PAS extrait en silence (plutôt 0 que « 10/20 »)
    assert "POLLU" in (b.warnings[0] if b.warnings else "")


# ── CLASSE E — le FAUX NÉGATIF : un champ vide ne proteste pas ───────────────────────────────
# Trouvés en confrontant notre extraction à une lecture indépendante du même avis (Tremblay,
# 2026-10-01). Les quatre classes précédentes corrigeaient des faits FAUX ; celles-ci corrigent
# des faits MANQUANTS, qui ne se voient pas : un champ absent ressemble à une absence réelle.

def test_classe_e_point_d_abreviation_ne_coupe_pas_la_phrase():
    """« (p. 171) » au milieu d'une phrase la coupait en deux, et le second morceau perdait
    l'ancre « PUE » — donc la valeur du projet était perdue en silence."""
    vrai = ("Il est rappelé que le PUE moyen des centres de données en France est de 1,6 "
            "(p. 171) et que celui attendu pour le projet est estimé à 1,3, ce qui est "
            "vertueux d’après le dossier.")
    assert _vals(vrai).get("pue") == 1.3, "la valeur du PROJET, pas la moyenne nationale"
    # la tournure simple continue de passer (Magny)
    simple = "Concernant le site actuel TH3, le PUE est passé de 1,8 en 2018 à 1,67 en 2021."
    assert _vals(simple).get("pue") == 1.8
    # et la définition reste rejetée (Bailly-Romainvilliers)
    defi = "Plus l’indice « PUE » est proche de 1 et plus la performance énergétique est importante."
    assert "pue" not in _vals(defi)


def test_classe_e_distance_ecrite_en_toutes_lettres():
    """« à quinze mètres de l'installation » : un motif qui n'accepte que les chiffres perd
    ce qui est sans doute le fait le plus parlant du corpus pour un élu local."""
    vrai = ("Cette démonstration est d’autant plus indispensable qu’un établissement scolaire "
            "est situé à quinze mètres de l’installation et que des établissements sensibles "
            "sont implantés à proximité.")
    assert _vals(vrai).get("etablissement_sensible_distance_m") == 15.0


# ── Contrat public : aucun identifiant français ne doit atteindre l'API ──────────────────────
def test_tous_les_indicateurs_ont_un_nom_public_anglais():
    """Un identifiant français qui atteindrait l'API serait une fuite de vocabulaire interne
    dans un contrat public — et il y resterait, puisque les consommateurs s'y adossent.

    Décision Franck du 2026-10-01 : les clés du JSON sont en anglais, en prévision de l'API.
    Ce test est là pour que l'ajout d'un champ sans sa traduction échoue au lieu de passer.
    """
    from pipelines.registers.avis import FIELDS
    from pipelines.registers.schema_en import INDICATORS, unknown_indicators

    ids = {f.id for f in FIELDS}
    assert unknown_indicators(ids) == [], "indicateur sans nom public anglais"
    assert sorted(set(INDICATORS) - ids) == [], "traduction orpheline (champ supprimé ?)"
    noms = list(INDICATORS.values())
    collisions = sorted({n for n in noms if noms.count(n) > 1})
    assert collisions == [], f"deux indicateurs partagent un nom public : {collisions}"


def test_classe_e_couche_texte_polluee_est_reparee_pas_rejetee():
    """Des caractères de largeur nulle à la place des espaces : on RÉPARE avant de juger.

    L'avis de Bonneuil (34 pages) portait 57 516 caractères invisibles et 2,9 % d'espaces,
    contre 13,9 à 14,6 % sur les treize autres avis de l'étalon. Mots soudés, ancres mortes,
    dix faits au lieu de quarante — et aucun signal. Le réflexe était de le signaler comme
    illisible ; c'était jeter quarante faits justes à cause d'un défaut d'export.

    La détection de pollution garde son rôle : elle attrape ce qui RÉSISTE à la réparation.
    """
    pollue = ("Le​projet​prévoit​54​groupes​électrogènes​pour​"
              "assurer​un​fonctionnement​en​continu​du​centre​"
              "de​données.")
    assert _vals(pollue).get("groupes_nombre") == 54.0, (
        "un texte dont les espaces sont des caractères invisibles doit être réparé, pas perdu"
    )
