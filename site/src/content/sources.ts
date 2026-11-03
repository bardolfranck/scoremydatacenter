// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La page « Sources & licences » — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
// langue, « duplicated pages is how EN silently diverged »).
//
// 🔴 Cette copie vivait en littéral DANS CHACUNE des deux pages. Les clés y étaient à parité
// le jour du comptage — tenues à la main, sans rien qui les tienne demain. Ici il n'y a qu'un
// endroit, et la parité est VÉRIFIÉE par `engine/tests/test_i18n_parity.py`.
//
// 🔴 Le type ne garde RIEN au build : `site/package.json` lance `astro build` SANS
// `astro check`, donc une clé manquante ne casse pas la construction — elle rend `undefined`
// dans la page, en silence. Le garde qui mord est le test pytest, que `make deploy` lance
// AVANT le build. Ne pas confondre les deux.

import type { Langue, LangueDeclaree } from "./langues";

const FR = {
  title: "Sources & licences — ScoreMyDataCenter",
  metaDescription: "Toutes les données qui alimentent nos notes, fiches et indices : la source, ce qu'elle alimente, sa licence. Méthode ouverte — la réponse publique à « quelles données utilisez-vous ? ».",
  tagline: "Observatoire indépendant",
  h1: "Sources & licences",
  intro:
    "<p>Notre méthode est ouverte. Voici <strong>chaque source</strong> qui alimente une note, une fiche ou un indice pays — ce qu'elle apporte, et sous quelle licence. C'est la réponse, publique et complète, à « quelles données utilisez-vous ? ».</p>",
  boundaryTitle: "Ce qu'on publie, et où s'arrête la ligne",
  boundaryBody:
    "<p>Ce registre liste nos sources au niveau de chaque <strong>pilier et indicateur</strong>. C'est la couche ouverte.</p><p>La provenance valeur-par-valeur d'un site précis (quelle source pour quel chiffre, mesuré ou estimé) est notre <strong>couche opérationnelle</strong>. La compilation, l'export et la fraîcheur en masse sont le <strong>produit</strong> (notre API).</p>",
  cols: { source: "Source", feeds: "Ce qu'elle alimente", license: "Licence" },
  groups: [
    { title: "Identité & localisation du site", rows: [
      { source: "DCWatch (Hubblo)", url: "https://dcwatch.hubblo.org", feeds: "Un des points de départ du corpus : nom, opérateur, coordonnées, puissance annoncée, statut du projet — que notre pipeline re-dérive et vérifie ensuite.", license: "<strong>ODbL</strong>" },
      { source: "Carte DCmag", url: "https://carte.dcmag.fr", feeds: "Localisation et statut des projets annoncés (projet ou site en service), recoupés fiche par fiche.", license: "Carte publique" },
      { source: "PeeringDB", url: "https://www.peeringdb.com", feeds: "Vérification hebdomadaire du statut « en service » : réseaux interconnectés dans le bâtiment.", license: "Données publiques PeeringDB" },
      { source: "Répertoire SIRENE (INSEE)", url: "https://annuaire-entreprises.data.gouv.fr", feeds: "Identification de l'opérateur quand elle manque (registre des entreprises).", license: "Licence Ouverte" },
      { source: "geo.api.gouv.fr", url: "https://geo.api.gouv.fr", feeds: "Commune et département (re-dérivés des coordonnées).", license: "Licence Ouverte" },
      { source: "OpenStreetMap · OpenFreeMap", url: "https://www.openstreetmap.org/copyright", feeds: "Fond de carte.", license: "<strong>ODbL</strong>" },
      { source: "Esri World Imagery", url: "https://www.esri.com", feeds: "Photographie satellite des fiches.", license: "© Esri (attribution sur l'image)" },
    ]},
    { title: "Pilier Énergie", rows: [
      { source: "RTE — eCO2mix", url: "https://www.rte-france.com/eco2mix", feeds: "Intensité carbone du mix électrique régional.", license: "Licence Ouverte" },
      { source: "RTE — Caparéseau · S3REnR", url: "https://www.capareseau.fr", feeds: "Capacité et proximité de raccordement.", license: "Licence Ouverte" },
      { source: "RTE · ODRÉ", url: "https://odre.opendatasoft.com", feeds: "Congestion et file d'attente réseau.", license: "Licence Ouverte" },
      { source: "Dossiers ICPE · presse", feeds: "PUE annoncé (déclaratif, noté avec prudence).", license: "Documents publics" },
    ]},
    { title: "Pilier Eau", rows: [
      { source: "ZRE (arrêtés préfectoraux) · Propluvia", url: "https://propluvia.developpement-durable.gouv.fr", feeds: "Stress hydrique et restrictions de la zone.", license: "Réglementaire / Licence Ouverte" },
      { source: "Hub'Eau", url: "https://hubeau.eaufrance.fr", feeds: "État de la masse d'eau.", license: "Licence Ouverte" },
      { source: "BNPE · Hub'Eau", url: "https://bnpe.eaufrance.fr", feeds: "Pression de prélèvement du bassin.", license: "Licence Ouverte" },
      { source: "Dossiers ICPE", feeds: "Refroidissement et volume d'eau annoncé.", license: "Documents publics" },
    ]},
    { title: "Pilier Foncier & biodiversité", rows: [
      { source: "INPN · Natura 2000 · ZNIEFF", url: "https://inpn.mnhn.fr", feeds: "Recouvrement et distance aux zones protégées.", license: "Licence Ouverte" },
      { source: "Cerema · RPG", url: "https://www.cerema.fr", feeds: "Statut du sol (artificialisé, agricole, naturel).", license: "Licence Ouverte" },
      { source: "SRADDET · INPN (TVB)", feeds: "Continuités écologiques (trame verte et bleue).", license: "Données publiques régionales" },
      { source: "Permis · dossiers ICPE", feeds: "Surface au sol du projet.", license: "Documents publics" },
    ]},
    { title: "Pilier Impact local", rows: [
      { source: "INSEE", url: "https://www.insee.fr", feeds: "Profil socio-économique et capacité d'absorption de la commune.", license: "Licence Ouverte" },
      { source: "Géorisques", url: "https://www.georisques.gouv.fr", feeds: "Aléa technologique / Seveso environnant.", license: "Licence Ouverte" },
      { source: "Presse · communiqués · délibérations", feeds: "Emplois et retombées annoncés, contestation observée, position des élus — <strong>faits sourcés, jamais l'article republié</strong>.", license: "Liens + extraits courts" },
    ]},
    { title: "Transparence & gouvernance", rows: [
      { source: "Enquêtes publiques · concertation", feeds: "Consentement et gouvernance du projet.", license: "Documents publics" },
    ]},
    { title: "Vérification & couverture hors-France", rows: [
      { source: "Registres EED / RVO (Pays-Bas)", feeds: "Puissances-vérité et source de vérification (les premières notes A d'Europe).", license: "Registre ouvert" },
      { source: "Eurostat (NUTS)", url: "https://ec.europa.eu/eurostat", feeds: "Pont revenu / usage des sols pour les pays hors-France.", license: "Réutilisation libre (Eurostat)" },
      { source: "datacentertracker.org", url: "https://www.datacentertracker.org", feeds: "Cas nord-américains.", license: "<strong>CC BY</strong>" },
      { source: "GDELT", url: "https://www.gdeltproject.org", feeds: "Filet de découverte des contestations (veille, précision au tri éditorial).", license: "Domaine public" },
    ]},
  ],
  closeP: "Une note ne repose que sur des <strong>faits sourcés</strong>. Chaque valeur d'une fiche renvoie à son origine ; sous 40 % de couverture documentaire, nous écrivons « données insuffisantes » plutôt que de noter l'inconnu.",
  methodHref: "/fr/methodologie/",
  ctaMethod: "Voir notre méthode →",
  backHref: "/fr/",
  backLabel: "← Retour à l'accueil",
};

const EN: typeof FR = {
  title: "Sources & licenses — ScoreMyDataCenter",
  metaDescription: "Every dataset feeding our grades, fiches and country indices: the source, what it feeds, its license. Open method — the public answer to \"what data do you use?\".",
  tagline: "Independent observatory",
  h1: "Sources & licenses",
  intro:
    "<p>Our method is open. Here is <strong>every source</strong> that feeds a grade, a fiche or a country index — what it brings, and under which license. This is the public, complete answer to \"what data do you use?\".</p>",
  boundaryTitle: "What we publish, and where the line is",
  boundaryBody:
    "<p>This register lists our sources at the level of each <strong>pillar and indicator</strong>. That is the open layer.</p><p>The value-by-value provenance of a specific site (which source for which figure, measured or estimated) is our <strong>operational layer</strong>. Bulk compilation, export and freshness are the <strong>product</strong> (our API).</p>",
  cols: { source: "Source", feeds: "What it feeds", license: "License" },
  groups: [
    { title: "Site identity & location", rows: [
      { source: "DCWatch (Hubblo)", url: "https://dcwatch.hubblo.org", feeds: "One of the corpus's starting points: name, operator, coordinates, announced power, project status — which our pipeline then re-derives and verifies.", license: "<strong>ODbL</strong>" },
      { source: "DCmag map", url: "https://carte.dcmag.fr", feeds: "Location and status of announced projects (project or site in service), cross-checked fiche by fiche.", license: "Public map" },
      { source: "PeeringDB", url: "https://www.peeringdb.com", feeds: "Weekly check of the « operational » status: networks interconnecting in the building.", license: "PeeringDB public data" },
      { source: "SIRENE register (INSEE)", url: "https://annuaire-entreprises.data.gouv.fr", feeds: "Operator identification when it is missing (French company register).", license: "Licence Ouverte" },
      { source: "geo.api.gouv.fr", url: "https://geo.api.gouv.fr", feeds: "Municipality and department (re-derived from coordinates).", license: "Licence Ouverte" },
      { source: "OpenStreetMap · OpenFreeMap", url: "https://www.openstreetmap.org/copyright", feeds: "Base map.", license: "<strong>ODbL</strong>" },
      { source: "Esri World Imagery", url: "https://www.esri.com", feeds: "Satellite imagery on the fiches.", license: "© Esri (credited on the image)" },
    ]},
    { title: "Energy pillar", rows: [
      { source: "RTE — eCO2mix", url: "https://www.rte-france.com/eco2mix", feeds: "Carbon intensity of the regional electricity mix.", license: "Licence Ouverte" },
      { source: "RTE — Caparéseau · S3REnR", url: "https://www.capareseau.fr", feeds: "Grid connection capacity and proximity.", license: "Licence Ouverte" },
      { source: "RTE · ODRÉ", url: "https://odre.opendatasoft.com", feeds: "Grid congestion and connection queue.", license: "Licence Ouverte" },
      { source: "ICPE files · press", feeds: "Announced PUE (declared, graded with caution).", license: "Public documents" },
    ]},
    { title: "Water pillar", rows: [
      { source: "ZRE (prefectoral orders) · Propluvia", url: "https://propluvia.developpement-durable.gouv.fr", feeds: "Water stress and restrictions in the area.", license: "Regulatory / Licence Ouverte" },
      { source: "Hub'Eau", url: "https://hubeau.eaufrance.fr", feeds: "Status of the water body.", license: "Licence Ouverte" },
      { source: "BNPE · Hub'Eau", url: "https://bnpe.eaufrance.fr", feeds: "Abstraction pressure on the basin.", license: "Licence Ouverte" },
      { source: "ICPE files", feeds: "Cooling and announced water volume.", license: "Public documents" },
    ]},
    { title: "Land & biodiversity pillar", rows: [
      { source: "INPN · Natura 2000 · ZNIEFF", url: "https://inpn.mnhn.fr", feeds: "Overlap with and distance to protected areas.", license: "Licence Ouverte" },
      { source: "Cerema · RPG", url: "https://www.cerema.fr", feeds: "Soil status (artificialized, farm, natural).", license: "Licence Ouverte" },
      { source: "SRADDET · INPN (green & blue network)", feeds: "Ecological corridors.", license: "Public regional data" },
      { source: "Permits · ICPE files", feeds: "Project footprint on the ground.", license: "Public documents" },
    ]},
    { title: "Local impact pillar", rows: [
      { source: "INSEE", url: "https://www.insee.fr", feeds: "Socio-economic profile and absorption capacity of the town.", license: "Licence Ouverte" },
      { source: "Géorisques", url: "https://www.georisques.gouv.fr", feeds: "Technological / Seveso hazard nearby.", license: "Licence Ouverte" },
      { source: "Press · statements · council minutes", feeds: "Announced jobs and revenue, observed opposition, elected officials' stance — <strong>sourced facts, never the article republished</strong>.", license: "Links + short excerpts" },
    ]},
    { title: "Transparency & governance", rows: [
      { source: "Public inquiries · consultation", feeds: "Consent and governance of the project.", license: "Public documents" },
    ]},
    { title: "Verification & coverage beyond France", rows: [
      { source: "EED / RVO registers (Netherlands)", feeds: "Ground-truth powers and verification source (Europe's first A grades).", license: "Open registry" },
      { source: "Eurostat (NUTS)", url: "https://ec.europa.eu/eurostat", feeds: "Income / land-use bridge for countries beyond France.", license: "Free reuse (Eurostat)" },
      { source: "datacentertracker.org", url: "https://www.datacentertracker.org", feeds: "North-American cases.", license: "<strong>CC BY</strong>" },
      { source: "GDELT", url: "https://www.gdeltproject.org", feeds: "Discovery net for opposition (monitoring; precision at editorial triage).", license: "Public domain" },
    ]},
  ],
  closeP: "A grade rests on <strong>sourced facts</strong> only. Every value on a fiche links back to its origin; below 40% documentation coverage we write \"insufficient data\" rather than grade the unknown.",
  methodHref: "/methodology/",
  ctaMethod: "See our method →",
  backHref: "/",
  backLabel: "← Back to the home page",
};


// ── NÉERLANDAIS — EN PRÉPARATION, PAS ENCORE SERVI (voir `content/langues.ts`).
// ⚠️ Les valeurs ci-dessous sont encore LE TEXTE FRANÇAIS, copié tel quel. Elles sont là
// pour qu'un traducteur natif ait la source sous les yeux, à sa place dans la structure.
// Elles NE DOIVENT PAS partir en ligne : `nl` n'est pas dans `LANGUES_VIVANTES`, et
// `test_une_langue_ne_devient_vivante_que_traduite` refuse de l'y faire entrer tant que
// ses valeurs sont celles du français.
const NL: typeof FR = {
  title: "Bronnen & licenties — ScoreMyDataCenter",
  metaDescription: "Alle gegevens achter onze cijfers, fiches en indexen: de bron, wat ze voedt, haar licentie. Open methode — het publieke antwoord op ‘welke gegevens gebruiken jullie?’.",
  tagline: "Onafhankelijk observatorium",
  h1: "Bronnen & licenties",
  intro:
    "<p>Onze methode is open. Dit is <strong>elke bron</strong> die een cijfer, een fiche of een landenindex voedt — wat ze aanlevert, en onder welke licentie. Het publieke, volledige antwoord op ‘welke gegevens gebruiken jullie?’.</p>",
  boundaryTitle: "Wat we publiceren, en waar de grens ligt",
  boundaryBody:
    "<p>Dit register noemt onze bronnen op het niveau van elke <strong>pijler en indicator</strong>. Dat is de open laag.</p><p>De herkomst per waarde van één specifieke site (welke bron voor welk getal, gemeten of geschat) is onze <strong>operationele laag</strong>. Bundeling, export en actualiteit in bulk zijn het <strong>product</strong> (onze API).</p>",
  cols: { source: "Bron", feeds: "Wat ze voedt", license: "Licentie" },
  groups: [
    { title: "Identiteit & locatie van de site", rows: [
      { source: "DCWatch (Hubblo)", url: "https://dcwatch.hubblo.org", feeds: "Een van de vertrekpunten van het corpus: naam, exploitant, coördinaten, aangekondigd vermogen, projectstatus — die onze pipeline daarna opnieuw afleidt en verifieert.", license: "<strong>ODbL</strong>" },
      { source: "DCmag-kaart", url: "https://carte.dcmag.fr", feeds: "Locatie en status van aangekondigde projecten (project of site in bedrijf), fiche voor fiche tegen elkaar gelegd.", license: "Publieke kaart" },
      { source: "PeeringDB", url: "https://www.peeringdb.com", feeds: "Wekelijkse controle van de status ‘in bedrijf’: netwerken die in het gebouw op elkaar aansluiten.", license: "Publieke PeeringDB-gegevens" },
      { source: "SIRENE-register (INSEE)", url: "https://annuaire-entreprises.data.gouv.fr", feeds: "Identificatie van de exploitant wanneer die ontbreekt (Frans ondernemingsregister).", license: "Licence Ouverte" },
      { source: "geo.api.gouv.fr", url: "https://geo.api.gouv.fr", feeds: "Gemeente en departement (opnieuw afgeleid uit de coördinaten).", license: "Licence Ouverte" },
      { source: "OpenStreetMap · OpenFreeMap", url: "https://www.openstreetmap.org/copyright", feeds: "Basiskaart.", license: "<strong>ODbL</strong>" },
      { source: "Esri World Imagery", url: "https://www.esri.com", feeds: "Satellietbeeld op de fiches.", license: "© Esri (vermelding op het beeld)" },
    ]},
    { title: "Pijler Energie", rows: [
      { source: "RTE — eCO2mix", url: "https://www.rte-france.com/eco2mix", feeds: "Koolstofintensiteit van de regionale elektriciteitsmix.", license: "Licence Ouverte" },
      { source: "RTE — Caparéseau · S3REnR", url: "https://www.capareseau.fr", feeds: "Aansluitcapaciteit en -nabijheid.", license: "Licence Ouverte" },
      { source: "RTE · ODRÉ", url: "https://odre.opendatasoft.com", feeds: "Netcongestie en wachtrij voor aansluiting.", license: "Licence Ouverte" },
      { source: "ICPE-dossiers · pers", feeds: "Aangekondigde PUE (declaratief, met voorzichtigheid beoordeeld).", license: "Publieke documenten" },
    ]},
    { title: "Pijler Water", rows: [
      { source: "ZRE (prefectorale besluiten) · Propluvia", url: "https://propluvia.developpement-durable.gouv.fr", feeds: "Waterstress en beperkingen in de zone.", license: "Regelgevend / Licence Ouverte" },
      { source: "Hub'Eau", url: "https://hubeau.eaufrance.fr", feeds: "Toestand van het waterlichaam.", license: "Licence Ouverte" },
      { source: "BNPE · Hub'Eau", url: "https://bnpe.eaufrance.fr", feeds: "Onttrekkingsdruk op het stroomgebied.", license: "Licence Ouverte" },
      { source: "ICPE-dossiers", feeds: "Koeling en aangekondigd watervolume.", license: "Publieke documenten" },
    ]},
    { title: "Pijler Bodem & biodiversiteit", rows: [
      { source: "INPN · Natura 2000 · ZNIEFF", url: "https://inpn.mnhn.fr", feeds: "Overlap met en afstand tot beschermde gebieden.", license: "Licence Ouverte" },
      { source: "Cerema · RPG", url: "https://www.cerema.fr", feeds: "Status van de grond (verhard, landbouw, natuur).", license: "Licence Ouverte" },
      { source: "SRADDET · INPN (TVB)", feeds: "Ecologische verbindingen (groenblauwe dooradering).", license: "Publieke regionale gegevens" },
      { source: "Vergunningen · ICPE-dossiers", feeds: "Grondoppervlak van het project.", license: "Publieke documenten" },
    ]},
    { title: "Pijler Lokale impact", rows: [
      { source: "INSEE", url: "https://www.insee.fr", feeds: "Sociaal-economisch profiel en absorptievermogen van de gemeente.", license: "Licence Ouverte" },
      { source: "Géorisques", url: "https://www.georisques.gouv.fr", feeds: "Technologisch / Seveso-risico in de omgeving.", license: "Licence Ouverte" },
      { source: "Pers · persberichten · raadsnotulen", feeds: "Aangekondigde banen en baten, waargenomen verzet, standpunt van de bestuurders — <strong>gedocumenteerde feiten; we publiceren nooit het artikel zelf opnieuw</strong>.", license: "Links + korte citaten" },
    ]},
    { title: "Transparantie & governance", rows: [
      { source: "Inspraak · overleg", feeds: "Instemming en governance van het project.", license: "Publieke documenten" },
    ]},
    { title: "Verificatie & dekking buiten Frankrijk", rows: [
      { source: "EED- / RVO-registers (Nederland)", feeds: "Werkelijke vermogens en verificatiebron (de eerste A's van Europa).", license: "Open register" },
      { source: "Eurostat (NUTS)", url: "https://ec.europa.eu/eurostat", feeds: "Koppeling voor inkomen / landgebruik voor landen buiten Frankrijk.", license: "Vrij hergebruik (Eurostat)" },
      { source: "datacentertracker.org", url: "https://www.datacentertracker.org", feeds: "Noord-Amerikaanse gevallen.", license: "<strong>CC BY</strong>" },
      { source: "GDELT", url: "https://www.gdeltproject.org", feeds: "Vangnet voor het ontdekken van verzet (monitoring; precisie bij de redactionele selectie).", license: "Publiek domein" },
    ]},
  ],
  closeP: "Een cijfer steunt uitsluitend op <strong>gedocumenteerde feiten</strong>. Elke waarde op een fiche verwijst naar haar herkomst; onder 40% documentaire dekking schrijven we ‘onvoldoende gegevens’ in plaats van het onbekende te beoordelen.",
  methodHref: "/fr/methodologie/",
  ctaMethod: "Bekijk onze methode →",
  backHref: "/fr/",
  backLabel: "← Terug naar de startpagina",
};

/** La table servie au gabarit : `SOURCES[lang]`. */
export const SOURCES: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
