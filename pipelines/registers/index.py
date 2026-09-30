# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""L'INDEX des registres d'évaluation environnementale : région → dossiers → lien PDF.

Chaîne (cadrage Franck 2026-09-30) : REGISTRE (index) → LIEN PDF → AVIS MRAe (contenu).
Ce module ne fait que le premier maillon. Il interroge le service WFS geo-ide d'une DREAL
et rend les dossiers dont l'intitulé désigne un centre de données, avec leur `doc_url`.

Ce qu'on a mesuré sur le service, et qui explique le code :
  · il exige VERSION=1.1.0 et REFUSE OUTPUTFORMAT=geojson — il ne rend que du GML ;
  · le filtre SERVEUR `PropertyIsLike` sur `intitule` FONCTIONNE : on ne rapatrie pas
    les 3 851 dossiers d'une région pour en garder douze ;
  · CHAQUE RÉGION A SON SCHÉMA. L'Île-de-France expose `intitule`/`petitionna`/`doc_url`,
    PACA expose `PROJET`/`LOCALITE`/`LIEN_AVIS`. D'où une spec DÉCLARATIVE par région
    plutôt qu'un adaptateur écrit à la main par région — même doctrine que les specs pays
    du moteur (« penser commun, décliner en déclaratif »).

Licence : jeux « avis de l'autorité environnementale » en Licence Ouverte v2 (réutilisation
commerciale autorisée, attribution). On extrait les faits et on LIE le PDF ; on ne le
réhéberge pas — ses annexes contiennent l'étude d'impact du pétitionnaire.
"""

from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

WXS = "https://ogc.geo-ide.developpement-durable.gouv.fr/wxs"
UA = "ScoreMyDataCenter/1.0 (+https://scoremydatacenter.org)"
TIMEOUT = 180


@dataclass(frozen=True)
class RegionSpec:
    """Tout ce qui change d'une région à l'autre. Rien d'autre ne doit être spécialisé."""

    code: str
    label: str
    mapfile: str
    typename: str
    # nom du champ dans CETTE région -> nom commun. Le dénominateur commun mesuré sur
    # trois régions est : commune + intitulé + date + LIEN PDF.
    fields: dict[str, str]
    search_field: str

    def url(self) -> str:
        return f"{WXS}?map={self.mapfile}"


REGIONS: dict[str, RegionSpec] = {
    "IDF": RegionSpec(
        code="IDF",
        label="DRIEAT Île-de-France",
        mapfile="/opt/data/stack/mapfiles/1.4/org_3954051/310e4070-6f2b-48bd-863e-c29db428867e.internet.map",
        typename="ms:L_AE_PR_S_R11",
        fields={
            "intitule": "intitule", "commune": "commune", "code_insee": "insee",
            "departemen": "departement", "petitionna": "petitionnaire",
            "procedure": "procedure", "statut": "statut",
            "date_recep": "date_reception", "date_final": "date_avis",
            "numero": "numero_avis", "doc_url": "doc_url",
        },
        search_field="intitule",
    ),
    "PACA": RegionSpec(
        code="PACA",
        label="DREAL Provence-Alpes-Côte d'Azur",
        mapfile="/opt/data/stack/mapfiles/1.4/org_38174/03f86b13-46c1-4a94-98fd-0060f3ebf4d6.internet.map",
        typename="ms:Avis_Projet_commune",
        # Le plus pauvre des quatre : ni pétitionnaire, ni INSEE, ni procédure. C'est LE
        # dénominateur commun mesuré — commune + intitulé + date + lien PDF — et rien de plus.
        fields={
            "PROJET": "intitule", "LOCALITE": "commune",
            "DATE_PUBLI": "date_avis", "LIEN_AVIS": "doc_url", "id": "numero_avis",
        },
        search_field="PROJET",
    ),
    "GE": RegionSpec(
        code="GE",
        label="DREAL Grand Est",
        mapfile="/opt/data/stack/mapfiles/1.4/org_5443264/2f20595a-e699-4701-af4b-0f35a8f5fa5d.internet.map",
        typename="ms:LocalisantAvisAeProjet_P_R44",
        fields={
            "intitule": "intitule", "nom_com": "commune", "insee_com": "insee",
            "dept": "departement", "petition": "petitionnaire", "categorie": "procedure",
            "statut": "statut", "date_final": "date_avis", "numero": "numero_avis",
            "lien_pdf": "doc_url",
        },
        search_field="intitule",
    ),
    "NORM": RegionSpec(
        code="NORM",
        label="DREAL Normandie",
        mapfile="/opt/data/stack/mapfiles/1.4/org_4930752/40a3a8bb-7675-4795-9e02-f1b37d8f5347.internet.map",
        typename="ms:drealnorm_aepr_s_r28",
        fields={
            "intitule": "intitule", "petit": "petitionnaire", "statut": "statut",
            "categorie": "procedure", "date_lim": "date_reception",
            "cd_garance": "numero_avis", "url_avis": "doc_url",
        },
        search_field="intitule",
    ),
}

# Un centre de données s'écrit de dix façons dans ces registres : « data center »,
# « datacenter », « datacenteur » (sic, Argenteuil), « centre d'hébergement de données
# informatiques », « centres de données ». On cherche donc les RACINES, pas les libellés.
DC_PATTERNS = ("*data*", "*données*", "*donnees*")
# … et on retire ce que ces racines ramassent à tort (« données » est un mot courant).
NOT_A_DC = re.compile(r"traitement des donn[ée]es personnelles|base de donn[ée]es (?:publique|nationale)", re.I)
# Le trait d'union compte : « DATA-CENTER » est l'orthographe habituelle en PACA, et un motif
# qui ne tolère que l'espace écartait silencieusement trois dossiers sur cinq (calibration).
IS_A_DC = re.compile(r"data[\s\-–]*cent|datacent|centre[s]?\s+(?:d['’]h[ée]bergement\s+)?de\s+donn[ée]es|"
                     r"h[ée]bergement\s+de\s+donn[ée]es|big[\s\-]*data", re.I)


def _like(field_name: str, pattern: str) -> str:
    # matchCase="false" est INDISPENSABLE et c'est un piège silencieux : le filtre est
    # sensible à la casse par défaut, et PACA saisit ses intitulés en CAPITALES
    # (« PROJET DE CONSTRUCTION D'UN DATA-CENTER … »). Sans cet attribut, la requête
    # réussit et rend ZÉRO résultat — une région entière disparaît sans la moindre erreur.
    # Constaté à la calibration : 0 dossier en PACA, Grand Est et Normandie ; 5 en PACA
    # une fois l'attribut posé.
    return ('<PropertyIsLike wildCard="*" singleChar="." escapeChar="!" matchCase="false">'
            f"<PropertyName>{field_name}</PropertyName><Literal>{pattern}</Literal>"
            "</PropertyIsLike>")


def _filter_xml(spec: RegionSpec) -> str:
    clauses = "".join(_like(spec.search_field, p) for p in DC_PATTERNS)
    return f'<Filter xmlns="http://www.opengis.net/ogc"><Or>{clauses}</Or></Filter>'


def _get(url: str, params: dict[str, str]) -> str:
    req = urllib.request.Request(url + "&" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace")


def _text(node: str, tag: str) -> str:
    m = re.search(rf"<ms:{tag}>(.*?)</ms:{tag}>", node, re.S)
    if not m:
        return ""
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()


def _centroid(node: str) -> tuple[float, float] | None:
    """Le registre porte la géométrie du dossier — c'est ce qui permet de RACCROCHER un
    avis à une fiche du corpus sans se fier au nom. On ne rend qu'un point indicatif."""
    m = re.search(r"<gml:posList[^>]*>(.*?)</gml:posList>|<gml:pos[^>]*>(.*?)</gml:pos>", node, re.S)
    if not m:
        return None
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", m.group(1) or m.group(2) or "")]
    if len(nums) < 2:
        return None
    lats, lons = nums[0::2], nums[1::2]
    return (sum(lats) / len(lats), sum(lons) / len(lons))


@dataclass
class Dossier:
    region: str
    intitule: str = ""
    commune: str = ""
    insee: str = ""
    departement: str = ""
    petitionnaire: str = ""
    procedure: str = ""
    statut: str = ""
    date_reception: str = ""
    date_avis: str = ""
    numero_avis: str = ""
    doc_url: str = ""
    centroid: tuple[float, float] | None = None
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if v not in ("", None, [])}
        if self.centroid:
            d["centroid"] = {"lat": round(self.centroid[0], 6), "lon": round(self.centroid[1], 6)}
        return d


def fetch(region: str) -> list[Dossier]:
    """Les dossiers « centre de données » d'une région, filtrés CÔTÉ SERVEUR."""
    spec = REGIONS[region]
    # SRSNAME : le service rend du Lambert-93 par défaut. On demande le WGS84 AU SERVEUR
    # plutôt que de reprojeter nous-mêmes — une reprojection maison est exactement le genre
    # de calcul silencieux qui a déjà produit des coordonnées fabriquées dans ce projet.
    # En WFS 1.1.0 avec un CRS en urn:, l'ordre des axes est lat,lon (et non lon,lat).
    gml = _get(spec.url(), {
        "SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature",
        "TYPENAME": spec.typename, "FILTER": _filter_xml(spec),
        "SRSNAME": "urn:ogc:def:crs:EPSG::4326",
    })
    tag = spec.typename.split(":")[-1]
    nodes = re.findall(rf"<ms:{tag}[ >].*?</ms:{tag}>", gml, re.S)
    out: list[Dossier] = []
    for node in nodes:
        d = Dossier(region=spec.code)
        for raw, common in spec.fields.items():
            setattr(d, common, _text(node, raw))
        d.centroid = _centroid(node)
        # Le filtre serveur est LARGE par construction (on cherche des racines). Le tri fin
        # se fait ici, et il est explicite : un dossier écarté doit pouvoir être expliqué.
        if NOT_A_DC.search(d.intitule) or not IS_A_DC.search(d.intitule):
            continue
        if not d.doc_url:
            d.warnings.append("pas de lien PDF dans le registre — avis non joignable par l'index")
        out.append(d)
    return out
