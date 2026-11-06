// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La page « Les normes · où on se situe » — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
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
  // Le chemin de la page « Méthode » dans cette langue : un SLUG localisé, pas un mot.
  // Il était choisi par un `lang === "fr" ?` dans le composant — l'endroit où une langue
  // nouvelle ne va pas le chercher.
  methHref: "/fr/methodologie/",
  title: "Les normes — où nous nous situons — ScoreMyDataCenter",
  metaDescription: "Ce que la filière data center mesure déjà (PUE, ISO/IEC 30134, Green Grid, ETSI) — et la case vide que nous occupons : la première note d'acceptabilité indépendante, site par site.",
  tagline: "Observatoire indépendant",
  h1: "Les normes. Où nous nous situons.",
  intro:
    "<p>Nous ne débarquons pas en terrain vierge. La filière data center mesure ses performances depuis des années, avec un vocabulaire normé et des organismes qui font autorité. Cette page cartographie <strong>l'existant</strong> — les KPI officiels, les normes ISO — pour situer, par contraste, ce que nous apportons.</p><p class=\"meth-nerd\">🤓 Plus avancé que <a href=\"/fr/comprendre/\">Comprendre les data centers</a>, en amont de notre <a href=\"/fr/methodologie/\">Méthode</a>. C'est la marche du milieu : le terrain de jeu existant, avant notre note.</p>",

  mapH2: "La carte des normes",
  mapIntro: "<p>Qui fait autorité, et sur quoi. L'ossature mondiale, c'est <strong>ISO/IEC 30134</strong> (via le comité SC39) ; tout le reste gravite autour.</p>",
  mapCols: { org: "Organisme", role: "Rôle", scope: "Ce qu'il normalise" },
  mapRows: [
    { org: "ISO/IEC JTC1 SC39", role: "le comité international", scope: "la série <strong>ISO/IEC 30134</strong> = les KPI officiels du data center" },
    { org: "The Green Grid", role: "consortium industriel", scope: "a <em>inventé</em> le PUE (repris par l'ISO), plus CUE, WUE, et l'indice <strong>PI</strong>" },
    { org: "ETSI", role: "normalisation télécom (EU)", scope: "l'indice <strong>DCp</strong> (Data Center Performance), étiquette A→I" },
    { org: "Cenelec", role: "reprise européenne", scope: "transpose les normes ISO 30134 en Europe" },
    { org: "France Datacenter · Gimélec · AGIT", role: "filière française", scope: "le livre blanc des KPI (2017) : pédagogie, anti-greenwashing" },
    { org: "InfraNum", role: "fédération des infrastructures", scope: "guide 2025 : data centers de proximité, souveraineté" },
  ],

  kpiH2: "Les indicateurs officiels",
  kpiIntro: "<p>Le vocabulaire que tout le secteur partage. Presque tous mesurent une seule chose : <strong>l'efficacité de la machine</strong>.</p>",
  kpiCols: { kpi: "Indicateur", norm: "Norme", measure: "Ce qu'il mesure" },
  kpiRows: [
    { kpi: "PUE", norm: "ISO/IEC 30134-2", measure: "le rendement énergétique global de l'infrastructure. <em>L'indicateur roi</em> : 2,0 = moyenne du parc français, 1,28 = les plus récents." },
    { kpi: "REF", norm: "ISO/IEC 30134-3", measure: "la part d'énergie renouvelable consommée" },
    { kpi: "ITEEsv", norm: "ISO/IEC 30134-4 <em>(en cours)</em>", measure: "l'efficacité énergétique du parc de serveurs" },
    { kpi: "CUE", norm: "Green Grid", measure: "le carbone émis par unité d'énergie informatique" },
    { kpi: "WUE", norm: "Green Grid", measure: "l'<strong>eau</strong> consommée par unité d'énergie — mais côté machine, pas côté territoire" },
    { kpi: "ERF · COP · CER", norm: "ISO SC39 <em>(en cours)</em>", measure: "réutilisation de la chaleur, rendement du refroidissement" },
  ],

  lettersH2: "Des notes en lettres existent déjà — mais elles ne mesurent pas la même chose",
  lettersP: [
    "<p>La filière possède <strong>déjà</strong> des notes en lettres. Le <strong>PI</strong> (Performance Indicator, The Green Grid) classe un data center de <i class=\"gl gl-a\">A</i> à <strong>G</strong> ; le <strong>DCp</strong> (ETSI RGS/OEU-0011) le classe de <strong>A à I</strong> — comme l'étiquette énergie d'un réfrigérateur.</p>",
    "<p><strong>Mais</strong> ces lettres mesurent l'<strong>efficacité énergétique de l'infrastructure</strong> (PUE, chaleur fatale, renouvelable) ; elles sont <strong>auto-déclarées</strong> par l'exploitant, sur une machine <strong>anonyme</strong>. Personne n'attribue une lettre à l'<strong>acceptabilité</strong> — eau, sol, territoire, gouvernance — d'un site <strong>nommé et réel</strong>, de l'<strong>extérieur</strong>.</p>",
    "<p>Même alphabet, dimension radicalement différente. C'est exactement le vide que nous occupons.</p>",
  ],

  situateH2: "Où nous nous situons",
  situateP: "<p>Notre pilier Énergie parle <strong>exactement</strong> le langage normé du secteur — nous nous <em>adossons</em> aux normes, nous ne les contournons pas. Le <a href=\"/fr/methodologie/\"><i class=\"gl gl-a\">A</i> se prouve</a> d'ailleurs par un audit <strong>ISO/IEC 30134</strong> accrédité.</p>",
  alignCols: { ours: "Notre indicateur", theirs: "KPI officiel correspondant" },
  alignRows: [
    { ours: "Énergie · <strong>PUE</strong> (déclaratif, noté avec prudence)", theirs: "PUE — <strong>ISO/IEC 30134-2</strong>" },
    { ours: "Énergie · appro. réel (PPA, % EnR)", theirs: "REF — <strong>ISO/IEC 30134-3</strong>" },
    { ours: "Énergie · intensité carbone (RTE eCO2mix)", theirs: "proche <strong>CUE</strong> (Green Grid)" },
    { ours: "Eau · WUE / source d'eau réelle", theirs: "<strong>WUE</strong> (Green Grid)" },
    { ours: "Foncier · récupération de chaleur", theirs: "proche <strong>ERF</strong>" },
  ],
  beyondP: "<p>Et voici la différence, par construction. Les KPI officiels sont <strong>tous</strong> des indicateurs d'efficacité de l'infrastructure. <strong>Aucun</strong> ne mesure ce que nous notons dans <strong>quatre de nos cinq piliers</strong> :</p><ul><li><strong>Eau — le stress hydrique du territoire</strong> (pas la conso de la machine, mais la tension sur la ressource locale)</li><li><strong>Foncier &amp; biodiversité</strong> — sol artificialisé, zones protégées, continuités écologiques</li><li><strong>Impact local</strong> — capacité d'absorption de la commune, aléa Seveso, contestation observée, position des élus</li><li><strong>Transparence &amp; gouvernance</strong> — concertation, consentement, enquête publique</li></ul><p>La filière optimise la <strong>machine</strong>. Nous notons son <strong>acceptabilité dans le territoire</strong>.</p>",

  etatH2: "Ce que l'État examine, lui",
  etatIntro: "<p>Les KPI de la filière s'arrêtent à la machine — mais l'administration, elle, regarde déjà le territoire. En Île-de-France, où l'agrément de l'État est <strong>obligatoire au-delà de 5 000 m²</strong> de surface de plancher, la préfecture de région a publié le 1<sup>er</sup> juin 2026 une <a href=\"https://www.drieat.ile-de-france.developpement-durable.gouv.fr/IMG/pdf/fiche_repere_relative_aux_demandes_agrement_des_centres_de_donnees_juin_2026.pdf\">fiche repère</a> qui dit, noir sur blanc, ce qu'elle examine dans un dossier de centre de données. La liste recoupe nos piliers presque ligne pour ligne.</p>",
  etatCols: { theirs: "Ce que l'État francilien examine", ours: "Notre indicateur" },
  etatRows: [
    { theirs: "<strong>Implanter dans les sites d'activités existants</strong> et les friches — pas d'extension urbaine s'il existe une alternative déjà urbanisée <em>(SDRIF, orientations réglementaires 126, 102 et 85 ; trajectoire ZAN)</em>", ours: "Foncier · statut du sol (artificialisé / agricole / naturel)" },
    { theirs: "<strong>Au-delà de 40 MW de raccordement, attention renforcée</strong> dans les secteurs en forte tension électrique, afin de ne pas obérer la capacité du réseau à servir les autres besoins locaux", ours: "Énergie · capacité de raccordement et file d'attente du réseau" },
    { theirs: "<strong>20 % de l'électricité consommée récupérée en chaleur</strong> — niveau recommandé dans l'hyper-centre d'agglomération, à intégrer dès la conception du projet", ours: "Énergie · raccordabilité à un réseau de chaleur · récupération annoncée" },
    { theirs: "<strong>Vigilance particulière sur les zones de répartition des eaux</strong> — nappes de l'Albien, de Champigny et de Beauce, la Mauldre, une partie du Vexin, la Beuvronne, la Thérouanne et La Bassée — et limitation des prélèvements par le choix du refroidissement", ours: "Eau · stress hydrique du bassin · refroidissement et volume annoncé" },
    { theirs: "<strong>Avis des collectivités d'accueil</strong> — engagements attendus sur l'emploi, la formation et les équipements publics", ours: "Impact local · profil de la commune · position des élus" },
    { theirs: "<strong>PUE, WUE, ISO 14001 et ISO 50001</strong> — ainsi que le <em>European Code of Conduct for Data Centres</em> — pour justifier les performances annoncées", ours: "Énergie · PUE · Eau · WUE (voir le tableau ci-dessus)" },
  ],
  etatNote: "<p><strong>Ce que cela change pour nous — et ce que cela ne change pas.</strong> Ces critères ne sont ni des seuils de notation, ni du droit national : ce sont les points qu'une préfecture de région examine, dossier par dossier, pour <em>un</em> agrément. Ils ne produisent aucune lettre, aucune comparaison entre sites, et rien n'en est publié sous une forme que l'on puisse confronter.</p><p>C'est précisément la frontière. L'État instruit <strong>au cas par cas et à huis clos</strong> ; nous mesurons les mêmes dimensions <strong>de l'extérieur, selon la même grille, sur tout le corpus</strong> — et nous les publions. Nous notons ce que l'État regarde déjà : c'est le meilleur argument contre l'idée que ces dimensions seraient notre invention.</p>",

  closeP: "La filière écrit la règle dans ses livres blancs. Nous publions le score — en public, site par site — et nous citons ses normes pour être inattaquables, pas pour être adoubés.",

  ctaMethod: "Voir notre méthode →",
  backHref: "/fr/",
  backLabel: "← Retour à l'accueil",
};

const EN: typeof FR = {
  // Le chemin de la page « Méthode » dans cette langue : un SLUG localisé, pas un mot.
  // Il était choisi par un `lang === "fr" ?` dans le composant — l'endroit où une langue
  // nouvelle ne va pas le chercher.
  methHref: "/methodology/",
  title: "The standards — where we sit — ScoreMyDataCenter",
  metaDescription: "What the data center industry already measures (PUE, ISO/IEC 30134, Green Grid, ETSI) — and the empty seat we take: the first independent acceptability score, site by site.",
  tagline: "Independent observatory",
  h1: "The standards. Where we sit.",
  intro:
    "<p>We are not landing on empty ground. The data center industry has measured its performance for years, with a normalized vocabulary and authoritative bodies. This page maps <strong>what already exists</strong> — the official KPIs, the ISO standards — to situate, by contrast, what we add.</p><p class=\"meth-nerd\">🤓 More advanced than <a href=\"/understand/\">Understanding data centers</a>, upstream of our <a href=\"/methodology/\">Method</a>. It is the middle rung: the existing playing field, before our grade.</p>",

  mapH2: "The map of standards",
  mapIntro: "<p>Who sets authority, and over what. The global backbone is <strong>ISO/IEC 30134</strong> (via the SC39 committee); everything else orbits it.</p>",
  mapCols: { org: "Body", role: "Role", scope: "What it standardizes" },
  mapRows: [
    { org: "ISO/IEC JTC1 SC39", role: "the international committee", scope: "the <strong>ISO/IEC 30134</strong> series = the official data center KPIs" },
    { org: "The Green Grid", role: "industry consortium", scope: "<em>invented</em> the PUE (later adopted by ISO), plus CUE, WUE, and the <strong>PI</strong> index" },
    { org: "ETSI", role: "telecom standards (EU)", scope: "the <strong>DCp</strong> index (Data Center Performance), an A→I label" },
    { org: "Cenelec", role: "European adoption", scope: "transposes the ISO 30134 standards into Europe" },
    { org: "France Datacenter · Gimélec · AGIT", role: "French industry", scope: "the KPI white paper (2017): pedagogy, anti-greenwashing" },
    { org: "InfraNum", role: "infrastructure federation", scope: "2025 guide: proximity data centers, sovereignty" },
  ],

  kpiH2: "The official indicators",
  kpiIntro: "<p>The vocabulary the whole sector shares. Almost all of them measure one thing: <strong>the efficiency of the machine</strong>.</p>",
  kpiCols: { kpi: "Indicator", norm: "Standard", measure: "What it measures" },
  kpiRows: [
    { kpi: "PUE", norm: "ISO/IEC 30134-2", measure: "the overall energy efficiency of the infrastructure. <em>The flagship metric</em>: 2.0 = the French average, 1.28 = the most recent sites." },
    { kpi: "REF", norm: "ISO/IEC 30134-3", measure: "the share of renewable energy consumed" },
    { kpi: "ITEEsv", norm: "ISO/IEC 30134-4 <em>(in progress)</em>", measure: "the energy efficiency of the server fleet" },
    { kpi: "CUE", norm: "Green Grid", measure: "the carbon emitted per unit of IT energy" },
    { kpi: "WUE", norm: "Green Grid", measure: "the <strong>water</strong> consumed per unit of energy — but machine-side, not territory-side" },
    { kpi: "ERF · COP · CER", norm: "ISO SC39 <em>(in progress)</em>", measure: "waste-heat reuse, cooling efficiency" },
  ],

  lettersH2: "Letter grades already exist — but they don't measure the same thing",
  lettersP: [
    "<p>The industry <strong>already</strong> has letter grades. The <strong>PI</strong> (Performance Indicator, The Green Grid) rates a data center from <i class=\"gl gl-a\">A</i> to <strong>G</strong>; the <strong>DCp</strong> (ETSI RGS/OEU-0011) rates it from <strong>A to I</strong> — like the energy label on a fridge.</p>",
    "<p><strong>But</strong> those letters measure the <strong>energy efficiency of the infrastructure</strong> (PUE, waste-heat reuse, renewables); they are <strong>self-declared</strong> by the operator, on an <strong>anonymous</strong> machine. No one puts a letter on the <strong>acceptability</strong> — water, land, territory, governance — of a <strong>named, real</strong> site, from the <strong>outside</strong>.</p>",
    "<p>Same alphabet, radically different dimension. That is precisely the gap we fill.</p>",
  ],

  situateH2: "Where we sit",
  situateP: "<p>Our Energy pillar speaks <strong>exactly</strong> the sector's standardized language — we <em>lean on</em> the standards, we do not bypass them. The <a href=\"/methodology/\"><i class=\"gl gl-a\">A</i> is proven</a>, in fact, by an accredited <strong>ISO/IEC 30134</strong> audit.</p>",
  alignCols: { ours: "Our indicator", theirs: "Matching official KPI" },
  alignRows: [
    { ours: "Energy · <strong>PUE</strong> (declared, graded with caution)", theirs: "PUE — <strong>ISO/IEC 30134-2</strong>" },
    { ours: "Energy · real supply (PPA, % renewables)", theirs: "REF — <strong>ISO/IEC 30134-3</strong>" },
    { ours: "Energy · carbon intensity (RTE eCO2mix)", theirs: "close to <strong>CUE</strong> (Green Grid)" },
    { ours: "Water · WUE / real water source", theirs: "<strong>WUE</strong> (Green Grid)" },
    { ours: "Land · waste-heat reuse", theirs: "close to <strong>ERF</strong>" },
  ],
  beyondP: "<p>And here is the difference, by design. The official KPIs are <strong>all</strong> infrastructure-efficiency metrics. <strong>None</strong> measures what we grade across <strong>four of our five pillars</strong>:</p><ul><li><strong>Water — the water stress of the territory</strong> (not the machine's consumption, but the strain on the local resource)</li><li><strong>Land &amp; biodiversity</strong> — artificialized soil, protected areas, ecological corridors</li><li><strong>Local impact</strong> — the town's absorption capacity, Seveso hazard, observed opposition, elected officials' stance</li><li><strong>Transparency &amp; governance</strong> — consultation, consent, public inquiry</li></ul><p>The industry optimizes the <strong>machine</strong>. We grade its <strong>acceptability within the territory</strong>.</p>",

  etatH2: "What the state itself examines",
  etatIntro: "<p>Industry KPIs stop at the machine — but public authorities already look at the territory. In the Île-de-France region, where a state approval is <strong>mandatory above 5,000 m²</strong> of floor area, the regional prefecture published a <a href=\"https://www.drieat.ile-de-france.developpement-durable.gouv.fr/IMG/pdf/fiche_repere_relative_aux_demandes_agrement_des_centres_de_donnees_juin_2026.pdf\">guidance note</a> on 1 June 2026 setting out, in writing, what it examines in a data-center file. The list maps onto our pillars almost line for line.</p>",
  etatCols: { theirs: "What the Île-de-France authorities examine", ours: "Our indicator" },
  etatRows: [
    { theirs: "<strong>Build on existing business sites and brownfield land</strong> — no urban extension where an already-urbanised alternative exists <em>(regional plan, orientations 126, 102 and 85; net-zero-artificialisation trajectory)</em>", ours: "Land · soil status (artificialised / farmland / natural)" },
    { theirs: "<strong>Above 40 MW of grid connection, heightened scrutiny</strong> in areas under electrical strain, so the grid keeps capacity for other local needs", ours: "Energy · grid connection capacity and queue" },
    { theirs: "<strong>20% of the electricity consumed recovered as heat</strong> — the level recommended in the dense urban core, to be designed in from the start", ours: "Energy · district-heating connectability · announced heat recovery" },
    { theirs: "<strong>Particular vigilance over designated water-allocation zones</strong> — the Albien, Champigny and Beauce aquifers, la Mauldre, part of le Vexin, la Beuvronne, la Thérouanne and La Bassée — and abstraction limited through the cooling design", ours: "Water · basin water stress · cooling and announced volume" },
    { theirs: "<strong>Opinion of the host local authorities</strong> — commitments expected on jobs, training and public facilities", ours: "Local impact · municipality profile · position of elected officials" },
    { theirs: "<strong>PUE, WUE, ISO 14001 and ISO 50001</strong> — plus the <em>European Code of Conduct for Data Centres</em> — to evidence the performance claimed", ours: "Energy · PUE · Water · WUE (see the table above)" },
  ],
  etatNote: "<p><strong>What this changes for us — and what it does not.</strong> These criteria are neither scoring thresholds nor national law: they are the points one French regional prefecture examines, file by file, for <em>one</em> approval. They produce no letter, no comparison between sites, and nothing is published in a form anyone could check one site against another.</p><p>That is exactly the boundary. The state assesses <strong>case by case and behind closed doors</strong>; we measure the same dimensions <strong>from the outside, on one grid, across the whole corpus</strong> — and we publish them. We grade what the state already looks at: the best answer to anyone claiming these dimensions are our invention.</p>",

  closeP: "The industry writes the rule in its white papers. We publish the score — in public, site by site — and we cite its standards to be unassailable, not to be endorsed.",

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
  // Slug localisé : reste /nl/ tant que les pages NL n'existent pas (remap harnais).
  methHref: "/nl/methodologie/",
  title: "De normen — waar wij staan — ScoreMyDataCenter",
  metaDescription: "Wat de datacentersector al meet (PUE, ISO/IEC 30134, Green Grid, ETSI) — en de lege stoel die wij innemen: het eerste onafhankelijke cijfer voor maatschappelijke acceptatie, site per site.",
  tagline: "Onafhankelijk observatorium",
  h1: "De normen. Waar wij staan.",
  intro:
    "<p>We betreden geen onontgonnen terrein. De datacentersector meet zijn prestaties al jaren, met een genormeerd vocabulaire en gezaghebbende instanties. Deze pagina brengt <strong>het bestaande</strong> in kaart — de officiële KPI's, de ISO-normen — om daartegen af te zetten wat wij toevoegen.</p><p class=\"meth-nerd\">🤓 Verder dan <a href=\"/nl/datacenters-begrijpen/\">Datacenters begrijpen</a>, vóór onze <a href=\"/nl/methodologie/\">Methode</a>. Dit is de middelste trede: het bestaande speelveld, vóór ons cijfer.</p>",

  mapH2: "De kaart van de normen",
  mapIntro: "<p>Wie gezag heeft, en waarover. De wereldwijde ruggengraat is <strong>ISO/IEC 30134</strong> (via comité SC39); de rest draait eromheen.</p>",
  mapCols: { org: "Instantie", role: "Rol", scope: "Wat ze normeert" },
  mapRows: [
    { org: "ISO/IEC JTC1 SC39", role: "het internationale comité", scope: "de reeks <strong>ISO/IEC 30134</strong> = de officiële KPI's van het datacenter" },
    { org: "The Green Grid", role: "industrieel consortium", scope: "heeft de PUE <em>uitgevonden</em> (overgenomen door ISO), plus CUE, WUE en de index <strong>PI</strong>" },
    { org: "ETSI", role: "telecomnormalisatie (EU)", scope: "de index <strong>DCp</strong> (Data Center Performance), label A→I" },
    { org: "Cenelec", role: "Europese omzetting", scope: "zet de ISO 30134-normen om voor Europa" },
    { org: "France Datacenter · Gimélec · AGIT", role: "de Franse sector", scope: "het witboek van de KPI's (2017): voorlichting, anti-greenwashing" },
    { org: "InfraNum", role: "federatie van infrastructuren", scope: "gids 2025: regionale datacenters, soevereiniteit" },
  ],

  kpiH2: "De officiële indicatoren",
  kpiIntro: "<p>Het vocabulaire dat de hele sector deelt. Bijna allemaal meten ze één ding: <strong>de efficiëntie van de machine</strong>.</p>",
  kpiCols: { kpi: "Indicator", norm: "Norm", measure: "Wat hij meet" },
  kpiRows: [
    { kpi: "PUE", norm: "ISO/IEC 30134-2", measure: "het totale energierendement van de infrastructuur. <em>De koning onder de indicatoren</em>: 2,0 = gemiddelde van het Franse datacenterpark, 1,28 = de nieuwste sites." },
    { kpi: "REF", norm: "ISO/IEC 30134-3", measure: "het aandeel verbruikte hernieuwbare energie" },
    { kpi: "ITEEsv", norm: "ISO/IEC 30134-4 <em>(in voorbereiding)</em>", measure: "de energie-efficiëntie van het serverpark" },
    { kpi: "CUE", norm: "Green Grid", measure: "de uitgestoten koolstof per eenheid IT-energie" },
    { kpi: "WUE", norm: "Green Grid", measure: "het <strong>water</strong> per eenheid energie — maar aan de machinekant, niet aan de gebiedskant" },
    { kpi: "ERF · COP · CER", norm: "ISO SC39 <em>(in voorbereiding)</em>", measure: "hergebruik van warmte, rendement van de koeling" },
  ],

  lettersH2: "Letterscores bestaan al — maar ze meten niet hetzelfde",
  lettersP: [
    "<p>De sector heeft <strong>al</strong> letters. De <strong>PI</strong> (Performance Indicator, The Green Grid) deelt een datacenter in van <i class=\"gl gl-a\">A</i> tot <strong>G</strong>; de <strong>DCp</strong> (ETSI RGS/OEU-0011) van <strong>A tot I</strong> — zoals het energielabel van een koelkast.</p>",
    "<p><strong>Maar</strong> die letters meten de <strong>energie-efficiëntie van de infrastructuur</strong> (PUE, restwarmte, hernieuwbaar); ze zijn <strong>zelfgerapporteerd</strong> door de exploitant, voor een <strong>anonieme</strong> machine. Niemand geeft een letter aan de <strong>maatschappelijke acceptatie</strong> — water, bodem, gebied, governance — van een <strong>met naam en toenaam genoemde, echte</strong> site, <strong>van buitenaf</strong>.</p>",
    "<p>Zelfde alfabet, radicaal andere dimensie. Precies dat gat vullen wij.</p>",
  ],

  situateH2: "Waar wij staan",
  situateP: "<p>Onze pijler Energie spreekt <strong>exact</strong> de genormeerde taal van de sector — we <em>leunen op</em> de normen, we omzeilen ze niet. De <a href=\"/nl/methodologie/\"><i class=\"gl gl-a\">A</i> bewijs je</a> trouwens met een geaccrediteerde <strong>ISO/IEC 30134</strong>-audit.</p>",
  alignCols: { ours: "Onze indicator", theirs: "Bijbehorende officiële KPI" },
  alignRows: [
    { ours: "Energie · <strong>PUE</strong> (declaratief, met voorzichtigheid beoordeeld)", theirs: "PUE — <strong>ISO/IEC 30134-2</strong>" },
    { ours: "Energie · reële levering (PPA, % hernieuwbaar)", theirs: "REF — <strong>ISO/IEC 30134-3</strong>" },
    { ours: "Energie · koolstofintensiteit (RTE eCO2mix)", theirs: "dicht bij <strong>CUE</strong> (Green Grid)" },
    { ours: "Water · WUE / reële waterbron", theirs: "<strong>WUE</strong> (Green Grid)" },
    { ours: "Bodem · warmteterugwinning", theirs: "dicht bij <strong>ERF</strong>" },
  ],
  beyondP: "<p>En hier zit het verschil, door constructie. De officiële KPI's zijn <strong>allemaal</strong> efficiëntie-indicatoren van de infrastructuur. <strong>Geen enkele</strong> meet wat wij in <strong>vier van onze vijf pijlers</strong> beoordelen:</p><ul><li><strong>Water — de waterstress van het gebied</strong> (niet het verbruik van de machine, maar de druk op de lokale voorraad)</li><li><strong>Bodem &amp; biodiversiteit</strong> — verharde grond, beschermde gebieden, ecologische verbindingen</li><li><strong>Lokale impact</strong> — absorptievermogen van de gemeente, Seveso-risico in de buurt, waargenomen verzet, standpunt van de bestuurders</li><li><strong>Transparantie &amp; governance</strong> — overleg, instemming, inspraak</li></ul><p>De sector optimaliseert de <strong>machine</strong>. Wij beoordelen zijn <strong>acceptatie in het gebied</strong>.</p>",

  etatH2: "Wat de Franse staat zelf bekijkt",
  etatIntro: "<p>De KPI's van de sector stoppen bij de machine — maar de Franse administratie kijkt al naar het gebied. In Île-de-France, waar boven <strong>5.000 m²</strong> vloeroppervlak de goedkeuring van de staat <strong>verplicht</strong> is, publiceerde de regionale prefectuur op 1 juni 2026 een <a href=\"https://www.drieat.ile-de-france.developpement-durable.gouv.fr/IMG/pdf/fiche_repere_relative_aux_demandes_agrement_des_centres_de_donnees_juin_2026.pdf\">referentiefiche</a> die zwart op wit zegt wat ze in een datacenterdossier onderzoekt. De lijst valt bijna regel voor regel samen met onze pijlers.</p>",
  etatCols: { theirs: "Wat de staat in Île-de-France onderzoekt", ours: "Onze indicator" },
  etatRows: [
    { theirs: "<strong>Vestigen op bestaande bedrijventerreinen</strong> en brownfields — geen stadsuitbreiding zolang er een al verhard alternatief bestaat <em>(SDRIF, reglementaire oriëntaties 126, 102 en 85; ZAN-traject)</em>", ours: "Bodem · status van de grond (verhard / landbouw / natuur)" },
    { theirs: "<strong>Boven 40 MW aansluitvermogen verscherpte aandacht</strong> in gebieden waar het net al zwaar onder druk staat, om de capaciteit van het net voor de andere lokale behoeften niet op het spel te zetten", ours: "Energie · aansluitcapaciteit en wachtrij van het net" },
    { theirs: "<strong>20% van de verbruikte elektriciteit teruggewonnen als warmte</strong> — aanbevolen niveau in het hart van de agglomeratie, mee te nemen vanaf het ontwerp van het project", ours: "Energie · aansluitbaarheid op een warmtenet · aangekondigde terugwinning" },
    { theirs: "<strong>Bijzondere waakzaamheid in waterverdelingszones (ZRE)</strong> — de grondwaterlagen van Albien, Champigny en Beauce, de Mauldre, een deel van de Vexin, de Beuvronne, de Thérouanne en La Bassée — en beperking van de onttrekkingen via de keuze van de koeling", ours: "Water · waterstress van het stroomgebied · koeling en aangekondigd volume" },
    { theirs: "<strong>Advies van de betrokken gemeenten</strong> — verwachte toezeggingen over werkgelegenheid, opleiding en publieke voorzieningen", ours: "Lokale impact · profiel van de gemeente · standpunt van de bestuurders" },
    { theirs: "<strong>PUE, WUE, ISO 14001 en ISO 50001</strong> — plus de <em>European Code of Conduct for Data Centres</em> — om de aangekondigde prestaties te onderbouwen", ours: "Energie · PUE · Water · WUE (zie de tabel hierboven)" },
  ],
  etatNote: "<p><strong>Wat dit voor ons verandert — en wat niet.</strong> Deze criteria zijn geen beoordelingsdrempels en geen nationaal recht: het zijn de punten die een regionale prefectuur, dossier per dossier, onderzoekt voor <em>één</em> goedkeuring. Ze leveren geen letter op, geen vergelijking tussen sites, en niets ervan wordt gepubliceerd in een vorm die zich laat toetsen.</p><p>Precies daar ligt de grens. De staat behandelt <strong>van geval tot geval en achter gesloten deuren</strong>; wij meten dezelfde dimensies <strong>van buitenaf, met dezelfde meetlat, over het hele corpus</strong> — en we publiceren ze. Wij beoordelen wat de staat al bekijkt: het beste argument tegen het idee dat deze dimensies onze uitvinding zouden zijn.</p>",

  closeP: "De sector schrijft de regel in zijn witboeken. Wij publiceren het cijfer — openbaar, site per site — en we citeren zijn normen om onaantastbaar te zijn, niet om een ridderslag te krijgen.",

  ctaMethod: "Bekijk onze methode →",
  backHref: "/nl/",
  backLabel: "← Terug naar de startpagina",
};

/** La table servie au gabarit : `NORMES[lang]`. */
export const NORMES: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
