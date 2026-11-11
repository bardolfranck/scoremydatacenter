// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La LECTURE ESG — un bloc par langue (i18n §13), lu par la méthodologie ET par la fiche.
// Une seule table : la correspondance pilier → thème ESRS n'existe qu'ici, la fiche et la
// méthode la lisent toutes les deux [[liste-a-deux-endroits-ment]].
//
// L'ANGLE, fil rouge de tout ce module : « L'ESG s'arrête aux murs du data center. Pas le
// risque. » Les lectures ESG d'un data center parlent de l'OPÉRATEUR (PUE, énergie verte) ;
// nous parlons du SITE (eau du bassin, sols, réseau, contestation locale). Ton neutre,
// explicatif, jamais vendeur.
//
// 🔴 VOCABULAIRE (règlement (UE) 2024/3005, lu sur le texte, 16-ESG/04) : JAMAIS « notation
// ESG », « score ESG », « ESG rating » — on se décrirait soi-même dans la définition d'un
// fournisseur soumis à agrément. `scripts/check_vocabulaire_esg.py` le refuse au départ.
//
// 🔴 LES ESRS BOUGENT. Le règlement délégué 2023/2772 est modifié par les ESRS SIMPLIFIÉES
// (paquet « Omnibus », acte délégué adopté par la Commission en juillet 2026, application à
// partir de l'exercice 2027). On cite donc les normes par THÈME (E1 climat et énergie, E3
// eau, E4 biodiversité et sols, S3 communautés), jamais par numéro d'exigence ni par un
// intitulé verbatim de 2023 présenté comme figé. Aucune affirmation de conformité ni de
// datapoint.
//
// 🔎 Tout ce qui n'est pas établi (l'étiquette UE A–G des data centers en préparation) reste
// au conditionnel. Rien de ce module ne touche la note : c'est une correspondance
// THÉMATIQUE, et l'IEF est informatif (engine/esg.py).

import type { LangueDeclaree } from "./langues";

/** Pilier → norme ESRS thématique. Le pilier « transparency_governance » n'y est PAS, et
 *  c'est voulu : G1 porte sur la conduite de l'ENTREPRISE, notre pilier sur ce que le PROJET
 *  rend public. Forcer le rapprochement ferait dire à la note ce qu'elle ne mesure pas. */
export const ESRS_PAR_PILIER: Record<string, "E1" | "E3" | "E4" | "S3"> = {
  energy: "E1",
  water: "E3",
  land_biodiversity: "E4",
  local_impact: "S3",
};

/** L'ancre de la section méthodologie — la même dans toutes les langues. La future page
 *  pilier ESG (FAQ, /fr/esg/ et /esg/) pourra y renvoyer ; le lien de la fiche passe par
 *  `lienEsg`, à repointer à UN endroit le jour où elle existe. */
export const ANCRE_ESG = "esg";

const GUIDE_URL = "https://www.ville-demain.com/le-guide-du-data-center-durable-et-acceptable-vers-un-nouveau-pacte-numerique-territorial/";
const TNFD_URL = "https://tnfd.global/";
const TAXO_URL = "https://eur-lex.europa.eu/eli/reg/2020/852/oj";
const SFDR_URL = "https://eur-lex.europa.eu/eli/reg/2019/2088/oj";
const EED_URL = "https://eur-lex.europa.eu/eli/dir/2023/1791/oj";
const ISO_URL = "https://www.iso.org/standard/63451.html";
const GHG_URL = "https://ghgprotocol.org/corporate-value-chain-scope-3-standard";

const FR = {
  lienEsg: "/fr/methodologie/#esg",
  // ── Thèmes ESRS (par thème, jamais l'intitulé verbatim d'une version figée).
  normes: {
    E1: "climat et énergie",
    E3: "eau",
    E4: "biodiversité et sols",
    S3: "communautés touchées par l'activité",
  },
  // ── Méthodologie
  methH2: "La note et les cadres ESG",
  methAccroche: "L'ESG s'arrête souvent aux murs du data center. Pas le risque.",
  methIntro: "<p>Les lectures ESG d'un data center portent presque toujours sur l'<strong>opérateur</strong> : l'efficacité de ses installations (PUE), la part d'énergie renouvelable, ses rapports de durabilité. Le risque, lui, tient aussi au <strong>lieu</strong> : l'eau du bassin, le sol sur lequel on construit, la capacité du réseau électrique, l'accueil fait au projet par ceux qui vivent autour. C'est ce que mesure notre note. Elle s'adresse aussi à ceux qui doivent qualifier un site <strong>sur dossier, sans visite</strong> : investisseurs, fonds d'infrastructure, conseils en reporting de durabilité, analystes.</p>",
  methEsrsH3: "Correspondance avec les normes européennes de reporting (ESRS)",
  methEsrsIntro: "<p>La directive CSRD impose aux grandes entreprises un rapport de durabilité dont le contenu est fixé par les normes ESRS. Ces normes ont été simplifiées en 2026 (paquet « Omnibus » ; acte délégué adopté par la Commission en juillet 2026, appliqué à partir de l'exercice 2027). Nous citons donc leurs <strong>thèmes</strong>, pas leurs exigences détaillées, qui changent. Le tableau dit où chaque pilier recoupe un thème. C'est une <strong>correspondance thématique, pas une conformité</strong> : une note de site ne remplace pas le reporting d'une entreprise, et nous ne notons pas d'entreprise.</p>",
  methColPilier: "Notre pilier",
  methColNorme: "Thème ESRS",
  methColQuoi: "Ce que le pilier y apporte",
  methApport: {
    energy: "Carbone du réseau électrique et efficacité énergétique du site.",
    water: "Tension sur l'eau du bassin, prélèvements et mode de refroidissement.",
    land_biodiversity: "État du sol avant le projet (artificialisé, agricole, naturel), emprise, proximité d'espaces protégés.",
    local_impact: "Ce que le projet fait au territoire et à ceux qui y vivent : voisinage, risques industriels, capacité d'accueil.",
  },
  methSansNorme: "<p><strong>Transparence &amp; gouvernance n'a pas de correspondance.</strong> La norme ESRS G1 porte sur la conduite de l'entreprise ; notre pilier mesure ce que le <strong>projet</strong> rend public. Forcer le rapprochement ferait dire à la note ce qu'elle ne mesure pas.</p>",
  methCadresH3: "Où se situe la note parmi les autres cadres",
  methCadres: [
    `<strong>TNFD</strong> (<a href="${TNFD_URL}" target="_blank" rel="noopener">Taskforce on Nature-related Financial Disclosures</a>). Son approche « LEAP » commence par <em>Locate</em> : localiser les actifs et ce qui les relie à la nature autour d'eux. C'est le cadre le plus proche de notre lecture par le lieu.`,
    `<strong>Taxonomie européenne</strong> (<a href="${TAXO_URL}" target="_blank" rel="noopener">règlement (UE) 2020/852</a>). Une activité durable ne doit pas causer de préjudice important aux autres objectifs environnementaux, dont l'eau et la biodiversité (principe « DNSH »). Nos données de site peuvent éclairer cette analyse ; elles ne disent pas si un actif est aligné, et nous ne reprenons aucun seuil du texte.`,
    `<strong>SFDR</strong> (<a href="${SFDR_URL}" target="_blank" rel="noopener">règlement (UE) 2019/2088</a>). Les acteurs financiers publient les principales incidences négatives de leurs investissements. Un fonds qui détient des data centers doit qualifier ces incidences actif par actif.`,
    `<strong>Directive efficacité énergétique, article 12</strong> (<a href="${EED_URL}" target="_blank" rel="noopener">directive (UE) 2023/1791</a>). Les data centers d'au moins 500 kW déclarent chaque année leurs indicateurs (énergie, eau, chaleur, renouvelables) dans une base européenne. La Commission prépare aussi une étiquette européenne des data centers, qui porterait sur la <strong>machine</strong> (efficacité énergétique, eau). Nous notons le <strong>lieu</strong> : les deux lectures seraient complémentaires.`,
    `<strong>ISO/IEC 30134</strong> (<a href="${ISO_URL}" target="_blank" rel="noopener">indicateurs de performance des data centers</a> : PUE, WUE, REF…). Nous les reprenons tels quels quand un opérateur les publie.`,
    `<strong>GHG Protocol, scope 3</strong> (<a href="${GHG_URL}" target="_blank" rel="noopener">chaîne de valeur</a>). Les émissions d'un data center loué entrent dans le scope 3 de ses clients : le lieu où sont hébergées leurs données fait partie de leur bilan.`,
  ],
  methIdxH3: "Indicateurs territoriaux : IPH, ICE, IEF",
  methIdxIntro: `<p>Le <a href="${GUIDE_URL}" target="_blank" rel="noopener">Guide du Data Center Durable et Acceptable</a> (Ville de Demain) propose trois indices pour mesurer l'insertion d'un data center dans son territoire, là où les indicateurs d'efficacité s'arrêtent aux murs du bâtiment. Voici ce que nous en affichons, et pourquoi. <strong>Aucun n'entre dans la note.</strong></p>`,
  methIdx: [
    "<strong>IPH — indice de pression hydrique.</strong> Il multiplie la consommation d'eau du site (WUE) par un coefficient de tension sur la ressource : 3 en zone de répartition des eaux, 2 en tension saisonnière, 1 sinon. <strong>Pas encore affiché.</strong> Notre indicateur de stress hydrique relève, pour la France, l'état des arrêtés sécheresse à une date donnée : il ne dit ni si le site est en zone de répartition des eaux, ni combien de jours par an une restriction dure. En tirer le coefficient reviendrait à le fabriquer. Le WUE, lui, n'est presque jamais publié.",
    "<strong>ICE — indice de circularité énergétique.</strong> Il combine la part de chaleur récupérée et la température à laquelle elle est livrée. <strong>Non affiché</strong> : la température de livraison n'est quasiment jamais publique.",
    "<strong>IEF — indice d'efficacité foncière.</strong> La puissance par m² d'emprise, doublée quand le site réutilise un sol déjà artificialisé. <strong>Affiché sur la fiche</strong> seulement quand trois faits sont connus : la puissance (mesurée, ou annoncée par l'opérateur — jamais estimée par nous), l'emprise totale du site (sourcée) et l'état du sol. Sinon, rien : pas de valeur approchée. L'indice favorise les grands sites denses, qui pèsent davantage sur le réseau et le territoire ; c'est une raison de plus pour qu'il reste hors note.",
  ],
  // ── Fiche
  ficheKicker: "Lecture ESG",
  ficheIntro: "Les piliers notés de ce site recoupent ces thèmes des normes européennes de reporting de durabilité (ESRS) :",
  ficheAucun: "Aucun pilier de ce site n'est encore noté : la correspondance avec les thèmes ESRS s'affichera avec les sous-notes.",
  ficheReserve: "Correspondance thématique, pas une conformité : la note porte sur le site, pas sur l'entreprise.",
  ficheLien: "Ce que l'ESG ne voit pas, et comment nous faisons cette correspondance →",
  iefTitre: "Indice d'efficacité foncière (IEF)",
  iefUnite: "kW/m² pondérés",
  iefInfo: "Indicatif, il ne compte pas dans la note.",
  iefTip: "Indice d'efficacité foncière (IEF), proposé par le Guide du Data Center Durable et Acceptable (Ville de Demain) : puissance par m² d'emprise, doublée si le site réutilise un sol déjà artificialisé. Plus il est élevé, plus le projet est compact et économe en terres. Limites : nous utilisons la puissance annoncée, pas la puissance informatique installée, l'emprise totale du site (voiries et parkings compris) et un indicateur de sol oui/non au lieu d'une part de surface ; l'indice favorise aussi les grands sites denses, qui pèsent davantage sur le réseau et le territoire. Indicatif, il ne compte pas dans la note.",
  iefEntrees: "{mw} MW {statut} · {ha} ha d'emprise · sol {sol}",
  iefStatut: { measured: "mesurés", announced: "annoncés" } as Record<string, string>,
  iefSol: { artificialized: "déjà artificialisé", agricultural: "agricole", natural_or_enaf: "naturel" } as Record<string, string>,
  iefSource: "source de l'emprise",
};

const EN: typeof FR = {
  lienEsg: "/methodology/#esg",
  normes: {
    E1: "climate and energy",
    E3: "water",
    E4: "biodiversity and land",
    S3: "communities affected by the activity",
  },
  methH2: "The grade and ESG frameworks",
  methAccroche: "ESG often stops at the data center's walls. Risk does not.",
  methIntro: "<p>ESG readings of a data center are almost always about the <strong>operator</strong>: how efficient its facilities are (PUE), its share of renewable energy, its sustainability reports. Risk, though, also lies in the <strong>place</strong>: the water basin, the land being built on, the capacity of the power grid, how the people living around it receive the project. That is what our grade measures. It is also meant for those who must assess a site <strong>on file, without a visit</strong>: investors, infrastructure funds, sustainability-reporting advisers, analysts.</p>",
  methEsrsH3: "Mapping to the European reporting standards (ESRS)",
  methEsrsIntro: "<p>The CSRD requires large companies to publish a sustainability report whose content is set by the ESRS. These standards were simplified in 2026 (the “Omnibus” package; delegated act adopted by the Commission in July 2026, applying from financial year 2027). We therefore cite their <strong>topics</strong>, not their detailed requirements, which change. The table shows where each pillar overlaps a topic. It is a <strong>topic mapping, not compliance</strong>: a site grade does not replace a company's reporting, and we do not grade companies.</p>",
  methColPilier: "Our pillar",
  methColNorme: "ESRS topic",
  methColQuoi: "What the pillar contributes",
  methApport: {
    energy: "Grid carbon and the site's energy efficiency.",
    water: "Water stress in the basin, withdrawals and cooling method.",
    land_biodiversity: "Land status before the project (sealed, farmland, natural), footprint, proximity to protected areas.",
    local_impact: "What the project does to the territory and to the people who live there: neighbourhood, industrial hazards, hosting capacity.",
  },
  methSansNorme: "<p><strong>Transparency &amp; governance has no counterpart.</strong> ESRS G1 is about how the company conducts its business; our pillar measures what the <strong>project</strong> makes public. Forcing the match would make the grade claim what it does not measure.</p>",
  methCadresH3: "Where the grade sits among other frameworks",
  methCadres: [
    `<strong>TNFD</strong> (<a href="${TNFD_URL}" target="_blank" rel="noopener">Taskforce on Nature-related Financial Disclosures</a>). Its “LEAP” approach starts with <em>Locate</em>: locating assets and what ties them to the nature around them. It is the framework closest to our place-based reading.`,
    `<strong>EU Taxonomy</strong> (<a href="${TAXO_URL}" target="_blank" rel="noopener">Regulation (EU) 2020/852</a>). A sustainable activity must do no significant harm to the other environmental objectives, water and biodiversity among them (the “DNSH” principle). Our site data can inform that analysis; it does not say whether an asset is aligned, and we do not reuse any threshold from the text.`,
    `<strong>SFDR</strong> (<a href="${SFDR_URL}" target="_blank" rel="noopener">Regulation (EU) 2019/2088</a>). Financial market participants disclose the principal adverse impacts of their investments. A fund holding data centers has to assess those impacts asset by asset.`,
    `<strong>Energy Efficiency Directive, Article 12</strong> (<a href="${EED_URL}" target="_blank" rel="noopener">Directive (EU) 2023/1791</a>). Data centers of at least 500 kW report their indicators every year (energy, water, heat, renewables) to a European database. The Commission is also preparing an EU data center label, which would rate the <strong>machine</strong> (energy efficiency, water). We grade the <strong>place</strong>: the two readings would be complementary.`,
    `<strong>ISO/IEC 30134</strong> (<a href="${ISO_URL}" target="_blank" rel="noopener">data center key performance indicators</a>: PUE, WUE, REF…). We take them as they are when an operator publishes them.`,
    `<strong>GHG Protocol, Scope 3</strong> (<a href="${GHG_URL}" target="_blank" rel="noopener">value chain</a>). The emissions of a leased data center fall within its customers' Scope 3: where their data is hosted is part of their footprint.`,
  ],
  methIdxH3: "Territorial indicators: IPH, ICE, IEF",
  methIdxIntro: `<p>The French <a href="${GUIDE_URL}" target="_blank" rel="noopener">Guide du Data Center Durable et Acceptable</a> (Ville de Demain) proposes three indices to measure how a data center fits into its territory, where efficiency indicators stop at the building's walls. Here is what we show of them, and why. <strong>None of them is part of the grade.</strong></p>`,
  methIdx: [
    "<strong>IPH — water pressure index.</strong> It multiplies the site's water use (WUE) by a coefficient of pressure on the resource: 3 in a water allocation zone, 2 under seasonal tension, 1 otherwise. <strong>Not shown yet.</strong> For France, our water-stress indicator records the status of drought orders on a given date: it says neither whether the site lies in a water allocation zone nor how many days a year a restriction lasts. Deriving the coefficient from it would mean making it up. As for WUE, it is almost never published.",
    "<strong>ICE — energy circularity index.</strong> It combines the share of heat recovered and the temperature at which it is delivered. <strong>Not shown</strong>: the delivery temperature is almost never public.",
    "<strong>IEF — land efficiency index.</strong> Power per m² of footprint, doubled when the site reuses already-sealed land. <strong>Shown on the fiche</strong> only when three facts are known: the power (measured, or announced by the operator — never estimated by us), the site's total footprint (sourced) and the land status. Otherwise, nothing: no approximate value. The index favours large dense sites, which weigh more on the grid and the territory — one more reason to keep it out of the grade.",
  ],
  ficheKicker: "ESG reading",
  ficheIntro: "The graded pillars of this site overlap these topics of the European Sustainability Reporting Standards (ESRS):",
  ficheAucun: "No pillar of this site is graded yet: the mapping to the ESRS topics will appear with the sub-grades.",
  ficheReserve: "A topic mapping, not compliance: the grade is about the site, not the company.",
  ficheLien: "What ESG does not see, and how we build this mapping →",
  iefTitre: "Land Efficiency Index (IEF)",
  iefUnite: "weighted kW/m²",
  iefInfo: "Informative only, not part of the grade.",
  iefTip: "Land Efficiency Index (IEF), proposed by the French 'Guide du Data Center Durable et Acceptable' (Ville de Demain): power per m² of footprint, doubled when the site reuses already-sealed land. The higher it is, the more compact and land-saving the project. Limitations: we use announced power, not installed IT power, the site's total footprint (roads and parking included) and a yes/no soil flag instead of a surface share; the index also favours large dense sites, which weigh more on the grid and the territory. Informative only, not part of the grade.",
  iefEntrees: "{mw} MW {statut} · {ha} ha footprint · {sol} land",
  iefStatut: { measured: "measured", announced: "announced" },
  iefSol: { artificialized: "already sealed", agricultural: "farm", natural_or_enaf: "natural" },
  iefSource: "footprint source",
};

const NL: typeof FR = {
  lienEsg: "/nl/methodologie/#esg",
  normes: {
    E1: "klimaat en energie",
    E3: "water",
    E4: "biodiversiteit en bodem",
    S3: "gemeenschappen die door de activiteit worden getroffen",
  },
  methH2: "Het cijfer en de ESG-kaders",
  methAccroche: "ESG houdt vaak op bij de muren van het datacenter. Het risico niet.",
  methIntro: "<p>ESG-analyses van een datacenter gaan bijna altijd over de <strong>exploitant</strong>: hoe efficiënt zijn installaties zijn (PUE), het aandeel hernieuwbare energie, zijn duurzaamheidsverslagen. Het risico zit echter ook in de <strong>plek</strong>: het stroomgebied, de grond waarop gebouwd wordt, de capaciteit van het elektriciteitsnet, hoe omwonenden het project ontvangen. Dat meet ons cijfer. Het is ook bedoeld voor wie een site <strong>op dossier, zonder bezoek</strong> moet beoordelen: beleggers, infrastructuurfondsen, adviseurs in duurzaamheidsrapportage, analisten.</p>",
  methEsrsH3: "Aansluiting op de Europese rapportagestandaarden (ESRS)",
  methEsrsIntro: "<p>De CSRD verplicht grote ondernemingen tot een duurzaamheidsverslag waarvan de inhoud wordt bepaald door de ESRS. Die standaarden zijn in 2026 vereenvoudigd (het ‘Omnibus’-pakket; gedelegeerde handeling door de Commissie vastgesteld in juli 2026, van toepassing vanaf boekjaar 2027). We noemen daarom hun <strong>thema's</strong>, niet hun gedetailleerde vereisten, die veranderen. De tabel toont waar elke pijler een thema raakt. Het is een <strong>thematische aansluiting, geen conformiteit</strong>: een cijfer voor een site vervangt de rapportage van een onderneming niet, en wij beoordelen geen ondernemingen.</p>",
  methColPilier: "Onze pijler",
  methColNorme: "ESRS-thema",
  methColQuoi: "Wat de pijler bijdraagt",
  methApport: {
    energy: "Koolstof van het elektriciteitsnet en energie-efficiëntie van de site.",
    water: "Waterstress in het stroomgebied, onttrekkingen en koelwijze.",
    land_biodiversity: "Toestand van de grond vóór het project (verhard, landbouw, natuur), terreinbeslag, nabijheid van beschermde gebieden.",
    local_impact: "Wat het project doet met het gebied en met wie er woont: omgeving, industriële risico's, opvangcapaciteit.",
  },
  methSansNorme: "<p><strong>Transparantie &amp; governance heeft geen tegenhanger.</strong> ESRS G1 gaat over het zakelijk gedrag van de onderneming; onze pijler meet wat het <strong>project</strong> openbaar maakt. De koppeling forceren zou het cijfer iets laten beweren wat het niet meet.</p>",
  methCadresH3: "Waar het cijfer staat tussen de andere kaders",
  methCadres: [
    `<strong>TNFD</strong> (<a href="${TNFD_URL}" target="_blank" rel="noopener">Taskforce on Nature-related Financial Disclosures</a>). De ‘LEAP’-aanpak begint met <em>Locate</em>: activa lokaliseren en vastleggen wat ze met de natuur eromheen verbindt. Het is het kader dat het dichtst bij onze benadering vanuit de plek ligt.`,
    `<strong>EU-taxonomie</strong> (<a href="${TAXO_URL}" target="_blank" rel="noopener">verordening (EU) 2020/852</a>). Een duurzame activiteit mag geen ernstige schade toebrengen aan de andere milieudoelstellingen, waaronder water en biodiversiteit (het ‘DNSH’-beginsel). Onze gegevens per site kunnen die analyse onderbouwen; ze zeggen niet of een activum is afgestemd, en we nemen geen enkele drempel uit de tekst over.`,
    `<strong>SFDR</strong> (<a href="${SFDR_URL}" target="_blank" rel="noopener">verordening (EU) 2019/2088</a>). Financiëlemarktdeelnemers publiceren de belangrijkste ongunstige effecten van hun beleggingen. Een fonds met datacenters in portefeuille moet die effecten per activum beoordelen.`,
    `<strong>Richtlijn energie-efficiëntie, artikel 12</strong> (<a href="${EED_URL}" target="_blank" rel="noopener">richtlijn (EU) 2023/1791</a>). Datacenters van minstens 500 kW rapporteren jaarlijks hun indicatoren (energie, water, warmte, hernieuwbare energie) aan een Europese databank. De Commissie bereidt ook een Europees label voor datacenters voor, dat de <strong>machine</strong> zou beoordelen (energie-efficiëntie, water). Wij beoordelen de <strong>plek</strong>: beide blikken zouden elkaar aanvullen.`,
    `<strong>ISO/IEC 30134</strong> (<a href="${ISO_URL}" target="_blank" rel="noopener">prestatie-indicatoren voor datacenters</a>: PUE, WUE, REF…). We nemen ze ongewijzigd over wanneer een exploitant ze publiceert.`,
    `<strong>GHG Protocol, scope 3</strong> (<a href="${GHG_URL}" target="_blank" rel="noopener">waardeketen</a>). De uitstoot van een gehuurd datacenter valt onder scope 3 van zijn klanten: waar hun gegevens worden gehost, hoort bij hun voetafdruk.`,
  ],
  methIdxH3: "Territoriale indicatoren: IPH, ICE, IEF",
  methIdxIntro: `<p>De Franse <a href="${GUIDE_URL}" target="_blank" rel="noopener">Guide du Data Center Durable et Acceptable</a> (Ville de Demain) stelt drie indexen voor om te meten hoe een datacenter in zijn gebied past, waar efficiëntie-indicatoren ophouden bij de muren van het gebouw. Dit tonen we ervan, en waarom. <strong>Geen ervan telt mee in het cijfer.</strong></p>`,
  methIdx: [
    "<strong>IPH — waterdrukindex.</strong> Hij vermenigvuldigt het waterverbruik van de site (WUE) met een coëfficiënt voor de druk op de bron: 3 in een Franse ‘zone de répartition des eaux’ (structureel watertekort), 2 bij seizoensgebonden spanning, anders 1. <strong>Nog niet getoond.</strong> Voor Frankrijk legt onze waterstress-indicator de stand van de droogtebesluiten op één datum vast: hij zegt niet of de site in zo'n zone ligt, en ook niet hoeveel dagen per jaar een beperking duurt. De coëfficiënt daaruit afleiden zou neerkomen op verzinnen. De WUE wordt bovendien bijna nooit gepubliceerd.",
    "<strong>ICE — index voor energiecirculariteit.</strong> Hij combineert het aandeel teruggewonnen warmte met de temperatuur waarop die wordt geleverd. <strong>Niet getoond</strong>: de levertemperatuur is bijna nooit openbaar.",
    "<strong>IEF — index voor grondefficiëntie.</strong> Het vermogen per m² terreinbeslag, verdubbeld wanneer de site al verharde grond hergebruikt. <strong>Getoond op de fiche</strong> alleen wanneer drie feiten bekend zijn: het vermogen (gemeten, of aangekondigd door de exploitant — nooit door ons geschat), het totale terreinbeslag van de site (met bron) en de toestand van de grond. Anders niets: geen benaderde waarde. De index bevoordeelt grote, dichte sites, die zwaarder op het net en het gebied wegen — nog een reden om hem buiten het cijfer te houden.",
  ],
  ficheKicker: "ESG-leeswijzer",
  ficheIntro: "De beoordeelde pijlers van deze site raken deze thema's van de Europese standaarden voor duurzaamheidsrapportage (ESRS):",
  ficheAucun: "Nog geen enkele pijler van deze site heeft een cijfer: de aansluiting op de ESRS-thema's verschijnt samen met de deelcijfers.",
  ficheReserve: "Een thematische aansluiting, geen conformiteit: het cijfer gaat over de site, niet over de onderneming.",
  ficheLien: "Wat ESG niet ziet, en hoe we deze aansluiting maken →",
  iefTitre: "Index voor grondefficiëntie (IEF)",
  iefUnite: "gewogen kW/m²",
  iefInfo: "Indicatief, telt niet mee in het cijfer.",
  iefTip: "Index voor grondefficiëntie (IEF), voorgesteld door de Franse ‘Guide du Data Center Durable et Acceptable’ (Ville de Demain): vermogen per m² terreinbeslag, verdubbeld als de site al verharde grond hergebruikt. Hoe hoger, hoe compacter en zuiniger met grond het project is. Beperkingen: we gebruiken het aangekondigde vermogen, niet het geïnstalleerde IT-vermogen, het totale terreinbeslag van de site (wegen en parkeerterreinen inbegrepen) en een ja/nee-gegeven over de grond in plaats van een oppervlakteaandeel; de index bevoordeelt bovendien grote, dichte sites, die zwaarder op het net en het gebied wegen. Indicatief, telt niet mee in het cijfer.",
  iefEntrees: "{mw} MW {statut} · {ha} ha terreinbeslag · grond {sol}",
  iefStatut: { measured: "gemeten", announced: "aangekondigd" },
  iefSol: { artificialized: "al verhard", agricultural: "landbouw", natural_or_enaf: "natuur" },
  iefSource: "bron terreinbeslag",
};

/** La copie de la lecture ESG : `ESG[lang]`. */
export const ESG: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
