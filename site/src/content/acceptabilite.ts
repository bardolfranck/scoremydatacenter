// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La page de concept « L'acceptabilité des data centers » — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
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
  title: "L'acceptabilité des data centers — définition, enjeux, mesure | ScoreMyDataCenter",
  metaDescription: "Qu'est-ce que l'acceptabilité d'un data center ? Définition, les cinq dimensions (énergie, eau, foncier, impact local, transparence) et comment elle se mesure, projet par projet.",
  tagline: "Observatoire indépendant",
  h1: "L'acceptabilité des data centers",
  lead: "L'acceptabilité d'un data center, c'est le degré auquel un projet peut s'implanter sur un territoire sans que ses effets — sur l'énergie, l'eau, le foncier, le voisinage — n'excèdent ce que la collectivité est prête à accepter. Elle ne se décrète pas : elle se <strong>mesure</strong>, projet par projet.",

  sections: [
    { h2: "Pourquoi la question se pose maintenant",
      corps: "<p>La vague de projets liés à l'intelligence artificielle concentre, sur quelques territoires, des besoins en électricité, en eau de refroidissement et en foncier sans précédent. Un bâtiment qui demande cent mégawatts ne se discute pas comme un entrepôt : il engage le réseau électrique d'une région, parfois la ressource en eau d'un bassin, et il s'installe pour trente ans.</p><p>L'acceptabilité est devenue la question qui décide si un projet se fait, se déplace, ou s'enlise. Elle se joue rarement sur l'argument global — le climat, les données — et presque toujours sur du concret local : <em>qu'est-ce que ça change, ici ?</em></p>" },
  ],

  // « Cinq dimensions, qui sont nos cinq piliers de notation » — l'intitulé dit l'articulation :
  // ce sont les mêmes cinq axes qu'on retrouve, notés, sur chaque fiche.
  piliersH2: "Cinq dimensions, qui sont nos cinq piliers de notation",
  piliers: [
    { icone: "energy", titre: "Énergie",
      corps: "l'électricité <strong>prélevée par le site</strong>, et ce que le réseau local peut encore donner. Un poste déjà saturé ne se double pas d'un claquement de doigts : c'est souvent le raccordement, et non le bâtiment, qui fixe le calendrier d'un projet." },
    { icone: "water", titre: "Eau",
      corps: "le volume <strong>consommé</strong> pour refroidir et ce qui est <strong>rejeté</strong> — avec quel traitement, dans quel milieu. Un bassin déjà sous tension l'été ne lit pas un prélèvement comme un bassin abondant." },
    { icone: "land", titre: "Foncier et biodiversité",
      corps: "le terrain sur lequel le site s'implante. <strong>Une terre agricole ne porte pas le même coût qu'une friche industrielle réhabilitée</strong> : la seconde répare, la première retire. S'y ajoutent les espaces protégés et les continuités écologiques du voisinage immédiat." },
    { icone: "local", titre: "Impact local et capacité d'absorption",
      corps: "ce que le territoire peut encaisser. <strong>Un gigaprojet sur une commune rurale n'est pas la même chose qu'un centre de calcul en milieu urbain</strong> : même puissance, même bruit, mais pas le même nombre d'habitants pour l'absorber, ni le même tissu pour en profiter." },
    { icone: "transparency", titre: "Transparence et gouvernance",
      corps: "ce que le porteur publie, et comment il associe le territoire. Un dossier consultable et une concertation réelle ne font pas un bon projet, mais leur absence pèse — c'est le seul pilier qui parle de la <em>conduite</em> plutôt que des effets." },
  ],

  sectionsApres: [
    { h2: "Comment elle se mesure",
      corps: "<p>Nous attribuons à chaque projet <strong>deux notes de <span class='note-inline n-a'>A</span> à <span class='note-inline n-e'>E</span></strong> — une pour le <strong>site</strong>, le contexte qu'il subit et n'a pas choisi, une pour le <strong>projet et le processus</strong>, ce que l'opérateur décide. Chaque note est accompagnée d'un <strong>niveau de confiance</strong> qui dit sur combien d'éléments sourcés elle repose.</p><p>Une absence de donnée ne devient jamais un <span class='note-inline n-a'>A</span> : sous un seuil de couverture, nous écrivons « données insuffisantes » plutôt qu'une lettre. Sans cette règle, le site le moins transparent serait le mieux noté. Le détail du calcul est public : <a href='/fr/methodologie/'>la méthode</a>, et <a href='/fr/la-note-pas-a-pas/'>la note, pas à pas</a>.</p>" },
    { h2: "Les nuisances, l'autre moitié du sujet",
      corps: "<p>L'acceptabilité se décide aussi sur ce qui s'entend et se voit depuis la rue : le bruit de la ventilation, les essais de groupes électrogènes, les cuves de carburant, le trafic de chantier. Ces éléments ne sont pas des détails de dossier — ce sont les premiers motifs d'opposition relevés dans les avis environnementaux.</p><p>Nous les publions <strong>en faits, à côté de la note</strong> : voir <strong><a href='/fr/nuisances-data-center/'>les nuisances des data centers</a></strong>.</p>" },
    // ⚠️ NE PAS RETIRER : citer la série ISO/IEC 30134 est notre ancrage normatif — il dit ce
    // que nous mesurons ET ce que nous ne prétendons pas faire (pas d'ACV).
    { h2: "Un ancrage normatif, pas une opinion",
      corps: "<p>Nous mesurons des indicateurs <strong>normalisés</strong> — efficacité énergétique, usage de l'eau — dans l'esprit de la série <strong>ISO/IEC 30134</strong> sur les indicateurs de performance des data centers. Nous ne produisons <strong>pas</strong> d'analyse de cycle de vie : nous rendons comparables des faits sourcés. Voir <a href='/fr/normes/'>les normes et où nous nous situons</a>.</p>" },
    { h2: "Ce que l'acceptabilité n'est pas",
      corps: "<p>Ce n'est pas un avis pour ou contre les data centers. Un territoire peut accueillir un projet lourd dans de bonnes conditions, et un petit projet peut être mal placé. Nous ne disons pas s'il faut construire : nous disons <strong>ce que coûte cet endroit-là, pour ce projet-là</strong>, avec la même grille pour tous.</p><p>Voir <a href='/fr/carte/'>la carte des sites</a> et <a href='/fr/classement/'>le classement</a>.</p>" },
  ],

  details: [
    { resume: "En savoir plus — pourquoi deux notes, et pas une seule",
      corps: "<p>Un même projet mêle ce qu'il <strong>subit</strong> — un réseau saturé, un bassin en tension, une terre agricole — et ce qu'il <strong>choisit</strong> : son efficacité, son mode de refroidissement, sa transparence. Fondre les deux dans une lettre unique laisserait un dossier exemplaire racheter un terrain mal choisi, ou l'inverse.</p><p>D'où la séparation : un opérateur ne peut rien à la note de <strong>site</strong>, il est entièrement responsable de celle du <strong>projet</strong>. Et un élu qui compare deux implantations possibles regarde la première ; un riverain qui juge un exploitant regarde la seconde.</p>" },
    // L'acceptabilité vue par la finance durable : c'est le « S » de l'ESG. En repli « en
    // savoir plus », jamais en tête de page — le jargon ne doit pas précéder la définition.
    { resume: "En savoir plus — l'acceptabilité vue par un investisseur",
      corps: "<p>Pour un investisseur, un fonds d'infrastructure ou une banque, l'acceptabilité porte un autre nom : c'est le « S » de l'ESG, le risque social d'un actif. Un projet contesté, retardé ou refusé perd de sa valeur, et un recours peut décaler une mise en service. La finance durable demande de qualifier ces risques actif par actif — pour un data center, site par site.</p><p>Nos fiches en donnent la matière : des données ESG au niveau du site, sourcées, sous la même grille pour tous. Elles ne notent pas l'entreprise qui porte le projet. Voir <a href='/fr/normes/#esg'>les cadres ESG, et où nous nous situons</a>.</p>" },
    { resume: "En savoir plus — qui décide, en France",
      corps: "<p>Un projet de cette taille passe par un <strong>permis de construire</strong> délivré par la commune, souvent par une <strong>autorisation environnementale</strong> instruite par la préfecture, et par un <strong>raccordement</strong> négocié avec le gestionnaire de réseau. L'<strong>autorité environnementale</strong> rend un avis public sur l'étude d'impact, et le public est consulté.</p><p>Personne, dans cette chaîne, ne produit de note comparable d'un site à l'autre : chaque dossier est instruit seul, dans son département. C'est exactement le vide que cet observatoire occupe.</p>" },
  ],
};

const EN: typeof FR = {
  title: "Data center acceptability — definition, issues, how it is measured | ScoreMyDataCenter",
  metaDescription: "What is data center acceptability? Definition, the five dimensions (energy, water, land, local impact, transparency) and how it is measured, project by project.",
  tagline: "Independent observatory",
  h1: "The acceptability of data centers",
  lead: "A data center's acceptability is the extent to which a project can be built on a territory without its effects — on energy, water, land and neighbours — exceeding what the community is willing to accept. It is not declared; it is <strong>measured</strong>, project by project.",

  sections: [
    { h2: "Why the question is being asked now",
      corps: "<p>The wave of AI-driven projects concentrates unprecedented demand for electricity, cooling water and land on a handful of territories. A building that asks for a hundred megawatts is not discussed like a warehouse: it commits a region's grid, sometimes a catchment's water, and it settles in for thirty years.</p><p>Acceptability has become the question that decides whether a project gets built, moved, or stalls. It rarely turns on the global argument — climate, data — and almost always on something local and concrete: <em>what does this change, here?</em></p>" },
  ],

  piliersH2: "Five dimensions, which are our five scoring pillars",
  piliers: [
    { icone: "energy", titre: "Energy",
      corps: "the electricity <strong>drawn by the site</strong>, and what the local grid can still give. A substation already at capacity is not duplicated overnight: it is often the grid connection, not the building, that sets a project's schedule." },
    { icone: "water", titre: "Water",
      corps: "the volume <strong>consumed</strong> for cooling and what is <strong>discharged</strong> — with what treatment, into what environment. A catchment already under summer stress does not read an abstraction the way an abundant one does." },
    { icone: "land", titre: "Land and biodiversity",
      corps: "the ground the site is built on. <strong>Farmland does not carry the same cost as a rehabilitated industrial brownfield</strong>: the second repairs, the first removes. Protected areas and the ecological corridors next door add to it." },
    { icone: "local", titre: "Local impact and absorption capacity",
      corps: "what the territory can take. <strong>A giga-project in a rural municipality is not the same thing as a compute centre in a city</strong>: same power, same noise, but not the same number of residents to absorb it, nor the same economic fabric to benefit from it." },
    { icone: "transparency", titre: "Transparency and governance",
      corps: "what the developer publishes, and how it involves the territory. A readable file and genuine consultation do not make a good project, but their absence weighs — it is the only pillar about <em>conduct</em> rather than effects." },
  ],

  sectionsApres: [
    { h2: "How it is measured",
      corps: "<p>We give every project <strong>two grades from <span class='note-inline n-a'>A</span> to <span class='note-inline n-e'>E</span></strong> — one for the <strong>site</strong>, the context it endures and did not choose, one for the <strong>project and process</strong>, what the operator decides. Each grade comes with a <strong>confidence level</strong> stating how many sourced elements it rests on.</p><p>Missing data never becomes an <span class='note-inline n-a'>A</span>: below a coverage threshold we write “insufficient data” instead of a letter. Without that rule, the least transparent site would be the best graded. The calculation is public: <a href='/methodology/'>the method</a> and <a href='/the-grade-step-by-step/'>the grade, step by step</a>.</p>" },
    { h2: "Nuisances, the other half of the subject",
      corps: "<p>Acceptability is also decided on what is heard and seen from the street: cooling noise, generator testing, fuel tanks, construction traffic. These are not file details — they are the first grounds for opposition we find in environmental opinions.</p><p>We publish them <strong>as facts, next to the grade</strong>: see <strong><a href='/data-center-nuisances/'>data center nuisances</a></strong>.</p>" },
    { h2: "A normative anchor, not an opinion",
      corps: "<p>We measure <strong>standardised</strong> indicators — energy efficiency, water usage — in the spirit of the <strong>ISO/IEC 30134</strong> series on data center performance indicators. We do <strong>not</strong> produce a life-cycle assessment: we make sourced facts comparable. See <a href='/standards/'>the standards and where we stand</a>.</p>" },
    { h2: "What acceptability is not",
      corps: "<p>It is not a verdict for or against data centers. A territory can host a heavy project under good conditions, and a small project can be badly placed. We do not say whether to build: we say <strong>what this particular place costs, for this particular project</strong>, with the same grid for everyone.</p><p>See <a href='/map/'>the map</a> and <a href='/ranking/'>the ranking</a>.</p>" },
  ],

  details: [
    { resume: "More — why two grades rather than one",
      corps: "<p>A project mixes what it <strong>endures</strong> — a saturated grid, a stressed catchment, farmland — with what it <strong>chooses</strong>: its efficiency, its cooling, its transparency. Merging both into a single letter would let an exemplary file buy off a badly chosen site, or the reverse.</p><p>Hence the split: an operator can do nothing about the <strong>site</strong> grade; it is entirely responsible for the <strong>project</strong> one. An elected official comparing two possible locations looks at the first; a resident judging an operator looks at the second.</p>" },
    { resume: "More — acceptability as an investor sees it",
      corps: "<p>For an investor, an infrastructure fund or a bank, acceptability goes by another name: it is the “S” in ESG, an asset's social risk. A project that is contested, delayed or refused loses value, and a legal challenge can push back its start of operations. Sustainable finance asks for these risks to be assessed asset by asset — for a data center, site by site.</p><p>Our fiches provide the material: site-level ESG data, sourced, on the same grid for everyone. They do not grade the company behind the project. See <a href='/standards/#esg'>ESG frameworks, and where we sit</a>.</p>" },
    { resume: "More — who decides, and where",
      corps: "<p>A project this size needs a <strong>building permit</strong> from the municipality, usually an <strong>environmental authorisation</strong> from the state services, and a <strong>grid connection</strong> negotiated with the network operator. An <strong>environmental authority</strong> issues a public opinion on the impact assessment, and the public is consulted.</p><p>Nobody in that chain produces a grade comparable from one site to the next: every file is examined alone, in its own district. That gap is exactly what this observatory fills.</p>" },
  ],
};


// ── NÉERLANDAIS — EN PRÉPARATION, PAS ENCORE SERVI (voir `content/langues.ts`).
// ⚠️ Les valeurs ci-dessous sont encore LE TEXTE FRANÇAIS, copié tel quel. Elles sont là
// pour qu'un traducteur natif ait la source sous les yeux, à sa place dans la structure.
// Elles NE DOIVENT PAS partir en ligne : `nl` n'est pas dans `LANGUES_VIVANTES`, et
// `test_une_langue_ne_devient_vivante_que_traduite` refuse de l'y faire entrer tant que
// ses valeurs sont celles du français.
const NL: typeof FR = {
  title: "De maatschappelijke acceptatie van datacenters — definitie, inzet, meting | ScoreMyDataCenter",
  metaDescription: "Wat is de maatschappelijke acceptatie van een datacenter? Definitie, de vijf dimensies (energie, water, bodem, lokale impact, transparantie) en hoe ze wordt gemeten, project voor project.",
  tagline: "Onafhankelijk observatorium",
  h1: "De maatschappelijke acceptatie van datacenters",
  lead: "De maatschappelijke acceptatie van een datacenter is de mate waarin een project zich op een plek kan vestigen zonder dat de effecten — op energie, water, bodem, omwonenden — overschrijden wat de gemeenschap bereid is te dragen. Ze wordt niet afgekondigd: ze wordt <strong>gemeten</strong>, project voor project.",

  sections: [
    { h2: "Waarom de vraag nú speelt",
      corps: "<p>De golf van projecten rond kunstmatige intelligentie concentreert op een handvol plekken een ongekende vraag naar elektriciteit, koelwater en grond. Een gebouw dat honderd megawatt vraagt, bespreek je niet als een distributiecentrum: het legt beslag op het elektriciteitsnet van een regio, soms op het water van een stroomgebied, en het blijft dertig jaar staan.</p><p>Maatschappelijke acceptatie is de vraag geworden die beslist of een project doorgaat, verhuist of vastloopt. Ze wordt zelden beslecht met het grote, mondiale argument — het klimaat, de data — en bijna altijd op iets lokaals en concreets: <em>wat verandert dit, hier?</em></p>" },
  ],

  piliersH2: "Vijf dimensies — en het zijn onze vijf beoordelingspijlers",
  piliers: [
    { icone: "energy", titre: "Energie",
      corps: "de elektriciteit die <strong>de site afneemt</strong>, en wat het lokale net nog kan geven. Een vol onderstation verdubbel je niet met een vingerknip: vaak bepaalt de netaansluiting, niet het gebouw, het tijdpad van een project." },
    { icone: "water", titre: "Water",
      corps: "het volume dat voor koeling wordt <strong>verbruikt</strong> en wat wordt <strong>geloosd</strong> — met welke zuivering, in welk milieu. Een stroomgebied dat ’s zomers al onder druk staat, weegt een onttrekking zwaarder dan een waterrijk gebied." },
    { icone: "land", titre: "Bodem en biodiversiteit",
      corps: "de grond waarop de site zich vestigt. <strong>Landbouwgrond kost niet hetzelfde als een opnieuw benut industrieterrein</strong>: het tweede herstelt iets, het eerste neemt iets weg. Daarbij komen de beschermde gebieden en de ecologische verbindingen in de directe omgeving." },
    { icone: "local", titre: "Lokale impact en absorptievermogen",
      corps: "wat het gebied kan dragen. <strong>Een gigaproject in een plattelandsgemeente is iets anders dan een rekencentrum in de stad</strong>: zelfde vermogen, zelfde geluid, maar niet hetzelfde aantal inwoners om het te dragen, en niet hetzelfde economische weefsel om ervan te profiteren." },
    { icone: "transparency", titre: "Transparantie en governance",
      corps: "wat de initiatiefnemer publiceert, en hoe hij de omgeving betrekt. Een raadpleegbaar dossier en echt overleg maken nog geen goed project, maar hun afwezigheid weegt — het is de enige pijler die over het <em>gedrag</em> gaat in plaats van over de effecten." },
  ],

  sectionsApres: [
    { h2: "Hoe ze wordt gemeten",
      corps: "<p>We kennen elk project <strong>twee cijfers van <span class='note-inline n-a'>A</span> tot <span class='note-inline n-e'>E</span></strong> toe — één voor de <strong>site</strong>, de context die het ondergaat en niet heeft gekozen, één voor <strong>project en proces</strong>, wat de exploitant beslist. Elk cijfer gaat vergezeld van een <strong>vertrouwensniveau</strong> dat zegt op hoeveel gedocumenteerde elementen het steunt.</p><p>Ontbrekende gegevens worden nooit een <span class='note-inline n-a'>A</span>: onder een dekkingsdrempel schrijven we ‘onvoldoende gegevens’ in plaats van een letter. Zonder die regel zou de minst transparante site het best beoordeeld zijn. De berekening is openbaar: <a href='/nl/methodologie/'>de methode</a>, en <a href='/the-grade-step-by-step/'>het cijfer, stap voor stap</a>.</p>" },
    { h2: "Hinder, de andere helft van het verhaal",
      corps: "<p>Maatschappelijke acceptatie wordt ook beslist op wat u vanaf de straat hoort en ziet: het geluid van de koeling, het testen van noodaggregaten, de brandstoftanks, het bouwverkeer. Dat zijn geen dossierdetails — het zijn de eerste bezwaargronden die we in milieuadviezen aantreffen.</p><p>We publiceren ze <strong>als feiten, naast het cijfer</strong>: zie <strong><a href='/nl/hinder-datacenter/'>de hinder van datacenters</a></strong>.</p>" },
    { h2: "Een normatieve verankering, geen mening",
      corps: "<p>We meten <strong>genormaliseerde</strong> indicatoren — energie-efficiëntie, watergebruik — in de geest van de reeks <strong>ISO/IEC 30134</strong> over prestatie-indicatoren voor datacenters. We voeren <strong>geen</strong> levenscyclusanalyse uit: we maken gedocumenteerde feiten vergelijkbaar. Zie <a href='/nl/normen/'>de normen, en waar wij staan</a>.</p>" },
    { h2: "Wat maatschappelijke acceptatie niet is",
      corps: "<p>Het is geen oordeel vóór of tegen datacenters. Een gebied kan een zwaar project onder goede voorwaarden ontvangen, en een klein project kan slecht liggen. We zeggen niet óf er gebouwd moet worden: we zeggen <strong>wat déze plek kost, voor dít project</strong>, met dezelfde meetlat voor iedereen.</p><p>Zie <a href='/nl/kaart/'>de kaart van de sites</a> en <a href='/nl/ranglijst/'>de ranglijst</a>.</p>" },
  ],

  details: [
    { resume: "Meer weten — waarom twee cijfers, en niet één",
      corps: "<p>Eén en hetzelfde project mengt wat het <strong>ondergaat</strong> — een vol net, een stroomgebied onder druk, landbouwgrond — met wat het <strong>kiest</strong>: zijn efficiëntie, zijn koeling, zijn transparantie. Beide in één letter samenvoegen zou een voorbeeldig dossier een slecht gekozen terrein laten goedmaken, of omgekeerd.</p><p>Vandaar de scheiding: aan het cijfer van de <strong>site</strong> kan een exploitant niets doen, voor dat van het <strong>project</strong> is hij volledig verantwoordelijk. Een bestuurder die twee mogelijke locaties vergelijkt, kijkt naar het eerste; een omwonende die een exploitant beoordeelt, kijkt naar het tweede.</p>" },
    { resume: "Meer weten — maatschappelijke acceptatie door de ogen van een belegger",
      corps: "<p>Voor een belegger, een infrastructuurfonds of een bank heeft maatschappelijke acceptatie een andere naam: het is de „S” van ESG, het sociale risico van een activum. Een project dat wordt aangevochten, vertraagd of geweigerd verliest waarde, en een beroepsprocedure kan de ingebruikname uitstellen. Duurzame financiering vraagt om die risico's per activum te beoordelen — voor een datacenter: per site.</p><p>Onze fiches leveren daarvoor het materiaal: ESG-gegevens per site, met bronnen, met dezelfde meetlat voor iedereen. Ze beoordelen niet de onderneming achter het project. Zie <a href='/nl/normen/#esg'>ESG-kaders, en waar wij staan</a>.</p>" },
    { resume: "Meer weten — wie beslist, en waar",
      corps: "<p>Een project van deze omvang vraagt een <strong>omgevingsvergunning</strong> — of, waar bouw en milieu gescheiden blijven zoals in Frankrijk, afzonderlijke vergunningen — van het <strong>bevoegd gezag</strong>, en een <strong>netaansluiting</strong> die met de netbeheerder wordt onderhandeld. Een onafhankelijke instantie brengt een openbaar advies uit over het <strong>milieueffectrapport (MER)</strong>, en het publiek wordt geraadpleegd.</p><p>Niemand in die keten produceert een cijfer dat van site tot site vergelijkbaar is: elk dossier wordt op zichzelf beoordeeld, in de eigen regio. Precies dat gat vult dit observatorium.</p>" },
  ],
};

/** La table servie au gabarit : `ACCEPTABILITE[lang]`. */
export const ACCEPTABILITE: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
