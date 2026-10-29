// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// La page de concept « Les nuisances » — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
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

import type { Langue } from "./langues";

// Les deux URL citées par la prose, UNE fois : chaque page en portait sa copie. Ce sont des
// adresses, pas des mots — elles ne se traduisent pas, et les deux langues citent les mêmes
// instances françaises (c'est de l'autorité environnementale FRANÇAISE que parle la page).
const AE = "https://www.igedd.developpement-durable.gouv.fr/l-autorite-environnementale-r145.html";
const MRAE = "https://www.mrae.developpement-durable.gouv.fr/";

const FR = {
  // 🔴 LE TITRE MENAIT AVEC LE MOT QUI N'EST PAS CHERCHÉ (Search Console, 28 j au 2026-10-26).
  // Cette page récolte 32 impressions et 0 clic, et la liste ENTIÈRE de ses requêtes parle de
  // bruit : « réduction du bruit data center », « acoustique data center », « bruit data
  // center », « insonorisation data center », « data centre generator noise control »…
  // AUCUNE ne contient « nuisance ». Mesuré le même jour sur Trends : « data center nuisance »
  // vaut 1 au mondial et 0 en France comme aux États-Unis — c'est un mot, pas une requête ;
  // « data center noise » vaut 37 et 34. « Nuisances » reste notre réflexe de langue, pas
  // celui du lecteur : il dit bruit, acoustique, insonorisation.
  // L'URL ne bouge pas — elle est indexée, et le titre pèse bien plus qu'un slug.
  title: "Le bruit d'un data center — combien, à quelle distance, ce qui est écrit",
  metaDescription: "Le bruit d'un data center : refroidissement en continu, groupes électrogènes à l'essai, cuves de carburant, eau prélevée. Combien, à quelle distance, et ce que les avis environnementaux documentent vraiment.",
  tagline: "Observatoire indépendant",
  h1: "Les nuisances des data centers",
  lead: `Un data center se discute souvent sur son bilan global — l'électricité, le climat. Ce qui se vit depuis la rue est plus concret : du <strong>bruit</strong> en continu, des <strong>groupes électrogènes</strong> mis à l'essai, des <strong>cuves de carburant</strong>, de l'<strong>eau</strong> prélevée puis rejetée. Sur les 41 avis de l'<a href="${AE}" target="_blank" rel="noopener">autorité environnementale</a> que nous avons dépouillés, ce sont les groupes électrogènes qui reviennent le plus souvent, devant les cuves de carburant et le bruit.`,

  questionsH2: "Les questions que l'on nous pose",
  // Ces deux questions sont, mot pour mot, celles que Google remonte le plus autour des data
  // centers. La page y répondait déjà en prose ; elle les pose désormais.
  //
  // 🔴 ON NE PUBLIE PAS DE « DISTANCE DE SÉCURITÉ ». Aucun texte n'en fixe, nous ne sommes pas
  // une autorité sanitaire, et un chiffre inventé ici serait repris en réunion publique. On
  // répond donc par ce qui est RÉELLEMENT encadré — l'émergence sonore — et par ce que nous
  // mesurons nous-mêmes, en le disant.
  questions: [
    {
      q: "À quelle distance d'un data center peut-on vivre tranquille&nbsp;?",
      r: `<p>Il n'existe <strong>aucune distance réglementaire</strong> entre un data center et les habitations. Ce que la réglementation encadre, ce n'est pas l'éloignement mais l'<strong>émergence</strong> : de combien le bruit monte chez le voisin quand l'installation fonctionne. L'arrêté du 23 janvier 1997 admet en général <strong>+5&nbsp;dB(A) le jour et +3&nbsp;dB(A) la nuit</strong>.</p>
      <p>La conséquence est contre-intuitive : <strong>la même machine n'a pas le même effet partout</strong>. Une campagne qui descend à 30&nbsp;dB(A) la nuit ne laisse presque aucune marge, là où une zone industrielle l'absorbe. Deux maisons à distance égale de deux sites identiques ne vivent donc pas la même chose.</p>
      <p>C'est pourquoi nous publions la <strong>distance aux premières habitations</strong> sur chaque fiche quand nous l'avons : c'est le seul paramètre que personne ne peut corriger après coup, et il se lit avec le reste du dossier. <a href='/fr/carte/'>Cherchez le site près de chez vous sur la carte</a>.</p>` },
    {
      q: "Vivre près d'un data center, est-ce risqué pour la santé&nbsp;?",
      r: `<p>Nous ne sommes pas une autorité sanitaire et <strong>nous ne mesurons aucun effet sur la santé</strong> — l'affirmer ou le nier serait également malhonnête. Ce que nous pouvons dire tient aux faits versés aux dossiers.</p>
      <p>Ce qui revient le plus souvent dans les avis d'autorité environnementale que nous avons dépouillés : les <strong>groupes électrogènes</strong>, les <strong>cuves de carburant</strong> et le <strong>bruit</strong>. Le bruit nocturne est le sujet le plus constant, parce qu'il est continu et qu'il n'a pas de répit — c'est ce qui distingue un data center d'un chantier ou d'une route.</p>
      <p>Nous publions ces éléments <strong>à côté de la note, jamais dedans</strong>, et nous disons sur quoi ils reposent. Pour comprendre à quel moment ces questions se posent dans une procédure, voir <a href='/fr/comprendre#droits'>Droits et calendrier</a>.</p>` },
  ],

  // 🔴 LES DEUX COMPTES SE DÉRIVENT DU CORPUS, ils ne se recopient pas : la page a publié
  // « 1 565 sites » — l'effectif EUROPE d'une version périmée — et donnait du même coup une
  // couverture de la distance deux fois trop flatteuse. Et un compte qui MANQUE ne se
  // remplace pas : les accesseurs rendent `null`, pas 0, et c'est la variante SANS chiffre
  // qui sort. Publier « 0 sites » transformerait une lecture ratée en mesure.
  mesure: {
    avec: `Notre corpus compte <strong>{sites} sites</strong>. Une mesure de <strong>distance aux premières habitations</strong> est disponible sur <strong>{habitations}</strong> d'entre eux — c'est le seul indicateur d'exposition que nous calculons nous-mêmes, partout de la même façon.`,
    sans: `La <strong>distance aux premières habitations</strong> est le seul indicateur d'exposition que nous calculons nous-mêmes, partout de la même façon ; nous la publions sur chaque fiche où nous l'avons.`,
  },
  // Le format de nombre est une propriété de la LANGUE (espace insécable et virgule en
  // français, virgule des milliers en anglais) : il vit dans la table, pas dans la page.
  locale: "fr-FR",
  sections: [
    // ORDRE VOULU : groupes → cuves (et le carburant DANS les cuves) → eau → électricité.
    // Le carburant n'a pas de sens avant qu'on ait dit à quoi il sert.
    { icone: "noise", h2: "Le bruit, la nuisance de tous les jours",
      corps: `<p>Un data center ne s'arrête jamais : il évacue en permanence la chaleur de ses machines. Le bruit ne vient donc pas du bâtiment mais de ce qui est posé dessus et autour — <strong>ventilateurs, aérorefroidisseurs, groupes froids</strong> — et il est <strong>continu, jour et nuit</strong>. C'est ce qui le distingue d'un chantier ou d'une route : il n'y a pas de creux.</p>
      <p>Trois choses comptent plus que le niveau brut :</p>
      <ul>
        <li><strong>L'écart avec le bruit de fond</strong>, et non le décibel absolu. La réglementation des installations classées raisonne en « émergence » : l'arrêté du 23 janvier 1997 admet en général <strong>+5 dB(A) le jour et +3 dB(A) la nuit</strong> chez le voisin, avec un plafond en limite de site de l'ordre de 70 dB(A) le jour et 60 dB(A) la nuit. Conséquence directe : une campagne où la nuit descend à 30 dB(A) ne laisse presque aucune marge, alors que la même machine disparaît dans un quartier d'activités. <strong>Le même équipement n'est pas acceptable partout.</strong></li>
        <li><strong>La distance aux premières habitations.</strong> C'est le seul paramètre que personne ne peut corriger après coup, et c'est pour cette raison que nous le mesurons site par site.</li>
        <li><strong>La tonalité.</strong> Un sifflement ou un ronronnement sur une fréquence marquée se remarque à niveau égal bien plus qu'un souffle diffus ; la réglementation le traite d'ailleurs à part.</li>
      </ul>
      <p>La technologie de refroidissement change la donne : un site refroidi à l'air sèche sur de grands bancs de ventilateurs, qui <strong>accélèrent justement pendant les canicules</strong> — au moment où les fenêtres sont ouvertes. Un site adiabatique ou à eau souffle moins fort, mais consomme de l'eau. Le refroidissement liquide au plus près des puces réduit encore les ventilateurs. <strong>Il n'existe pas de choix sans contrepartie</strong> : le bruit, l'eau et l'électricité s'échangent entre eux.</p>` },

    { icone: "engine", h2: "Les groupes électrogènes de secours : pourquoi c'est une nuisance",
      corps: `<p>Ces moteurs ne produisent rien en temps normal. Ils existent pour que le site survive à une coupure du réseau — et un data center dimensionne sa flotte pour tenir <strong>la totalité</strong> de sa charge, refroidissement compris, avec de la redondance. En ordre de grandeur, un site de plusieurs dizaines de mégawatts aligne donc <strong>plusieurs dizaines de moteurs</strong> de la taille de ceux d'un navire. C'est une centrale électrique de secours, posée en lisière de ville.</p>
      <p>Le voisinage ne les entend pas lors des pannes, qui sont rares. Il les entend lors des <strong>essais périodiques</strong>, obligatoires pour garantir qu'ils démarreront : typiquement un essai par mois et par machine, plus un essai en charge plus long une fois par an. Un site qui aligne trente moteurs a donc des essais <strong>très régulièrement</strong>, et c'est de loin le premier motif de crispation dans les dossiers que nous lisons.</p>
      <p>À partir de quand est-ce « beaucoup » ? Deux repères plutôt qu'un chiffre : la <strong>puissance cumulée</strong> de la flotte — au-delà d'un certain seuil thermique, elle fait basculer l'installation dans un régime d'autorisation plus exigeant au titre des installations classées — et le <strong>rapport entre cette puissance et la taille de la commune</strong>. C'est ce second rapport qui explique qu'un même projet passe sans bruit dans une zone industrielle et bloque ailleurs.</p>` },

    { icone: "fuel", h2: "Les cuves de carburant : la quantité avant la matière",
      corps: `<p>Qui dit groupes dit réserve : les moteurs doivent pouvoir tourner plusieurs heures, parfois plusieurs jours, sans livraison. Un dossier déclare donc un <strong>volume de stockage</strong>, et c'est ce volume que nous relevons.</p>
      <p>Le carburant déclaré varie : certains avis déclarent de l'huile végétale hydrotraitée, d'autres du fioul ou du gazole.</p>
      <p>Et alors ? La matière compte moins que trois choses :</p>
      <ul>
        <li><strong>La quantité stockée.</strong> C'est elle qui mesure le risque : quelques mètres cubes et plusieurs centaines ne se gèrent pas de la même façon, et ce sont des seuils de volume — pas la nature du produit — qui déclenchent les obligations les plus lourdes.</li>
        <li><strong>Le confinement.</strong> Cuves à double paroi, bassins de rétention capables de retenir à la fois le carburant et les eaux d'extinction d'un incendie : c'est là que se joue l'essentiel. Un déversement non retenu à proximité d'un captage d'eau potable ou d'un cours d'eau est le scénario qui inquiète les services instructeurs.</li>
        <li><strong>Ce qui sort à l'échappement pendant les essais.</strong> Oxydes d'azote et particules, à hauteur de toiture, aux heures ouvrées.</li>
      </ul>
      <p>Qu'est-ce qui est vertueux, alors ? <strong>Moins de volume, mieux confiné</strong>, et un carburant moins émetteur. L'huile végétale hydrotraitée réduit nettement les émissions et n'est pas d'origine fossile — mais elle brûle et se stocke dans les mêmes cuves : elle améliore le bilan, elle ne supprime pas le risque.</p>` },

    { icone: "water", h2: "L'eau : le volume, mais aussi le rejet",
      corps: `<p>Refroidir avec de l'eau coûte beaucoup moins d'électricité que refroidir à l'air — c'est le même arbitrage que plus haut, vu de l'autre côté. Deux questions se posent alors : <strong>combien</strong> est prélevé, et <strong>sur quelle ressource</strong>. Un volume modeste pris sur un bassin déjà en tension l'été pèse plus qu'un volume important pris ailleurs.</p>
      <p>Le rejet est la moitié oubliée du sujet : l'eau repart <strong>plus chaude</strong>, plus concentrée en sels, et traitée contre l'entartrage et les légionelles. La question pour une commune n'est donc pas seulement « combien », mais « <strong>vers où, à quelle température, avec quel traitement</strong> ».</p>` },

    { icone: "energy", h2: "L'électricité : la nuisance qu'on ne voit pas",
      corps: `<p>Elle ne s'entend ni ne se sent, mais c'est souvent elle qui décide. Un raccordement de forte puissance consomme une capacité de réseau que les autres usages du territoire — industrie, logement, transport — n'auront plus avant des années, et sa file d'attente se compte en années. C'est aussi ce qui rend la flotte de groupes aussi grosse : plus le site est puissant, plus son secours est imposant.</p>` },

    { icone: "hidden", h2: "Le « caché »",
      corps: `<p>Un exploitant se présente par son efficacité énergétique. Il met rarement en avant ses groupes électrogènes, ses cuves ou la modélisation acoustique que l'autorité environnementale lui demande. <strong>L'écart entre une plaquette de communication et le contenu d'un dossier d'évaluation est, en soi, une information</strong> — et c'est le matériau de cette page.</p>` },

    { icone: "hazard", h2: "Quand le site porte lui-même un risque",
      corps: `<p>Certains projets stockent sur place du carburant en quantité, des batteries lithium-ion, voire de l'hydrogène. Le site <strong>porte</strong> alors un aléa, au lieu de seulement le subir — ce n'est plus une nuisance, c'est un risque, et il se traite dans l'étude de dangers. Nous publions ces éléments <strong>en information, à côté de la note</strong>, tant que la couverture ne permet pas de les noter sans fausser la comparaison entre sites.</p>` },

    { icone: "measure", h2: "Où en est la mesure, chez nous",
      corps: `<p>{mesure} Le détail des nuisances, lui, vient des <strong>41 avis environnementaux dépouillés</strong> : les projets passés en évaluation, <strong>pas l'ensemble du parc</strong>. Ces faits sont publiés <strong>à côté de la note, pas dedans</strong>.</p>
      <p>Voir <a href='/fr/acceptabilite-data-center/'>l'acceptabilité des data centers</a>, <a href='/fr/carte/'>la carte des sites</a> et <a href='/fr/methodologie/'>la méthode</a>.</p>` },
  ],

  details: [
    { resume: "En savoir plus — l'autorité environnementale, ça vaut quoi ?",
      corps: `<p>Pour les projets de cette taille, le porteur doit produire une <strong>étude d'impact</strong>. Un organisme distinct du service qui délivrera l'autorisation l'examine et rend un <strong>avis public</strong> : c'est l'<a href="${AE}" target="_blank" rel="noopener">autorité environnementale</a>, le plus souvent, en région, une <a href="${MRAE}" target="_blank" rel="noopener">mission régionale d'autorité environnementale (MRAe)</a>.</p>
      <p>Ce que cet avis <strong>est</strong> : une expertise sur la <em>qualité du dossier</em> et sur la façon dont le projet prend en compte l'environnement, assortie de recommandations. Ce qu'il <strong>n'est pas</strong> : une autorisation, ni un refus. L'avis ne décide pas du projet.</p>
      <p>Pour autant il n'est pas décoratif. Le porteur doit y <strong>répondre par écrit</strong>, et son avis comme sa réponse sont <strong>joints au dossier soumis au public</strong> ; l'autorité qui délivre le permis doit motiver sa décision au regard de ces éléments. En pratique, un avis qui pointe une lacune oblige à compléter le dossier, et sert d'appui aux élus et aux riverains pendant la consultation. <strong>C'est le document le plus utile à lire avant de se faire une opinion sur un projet</strong> — et c'est notre matière première.</p>` },

    { resume: "En savoir plus — comment le bruit d'un projet est évalué",
      corps: `<p>Avant travaux, un acousticien mesure le <strong>bruit de fond existant</strong>, de jour et de nuit, aux habitations les plus proches. Il modélise ensuite le site en fonctionnement et compare : ce qui est jugé, c'est l'<strong>écart</strong> entre les deux, pas le niveau de la machine. Des engagements sont pris en conséquence — écrans, capotages, ventilateurs à vitesse réduite la nuit, bridage des essais de groupes en soirée — et une <strong>campagne de contrôle après mise en service</strong> est en principe demandée.</p>
      <p>Deux failles classiques, visibles à la lecture des avis : un bruit de fond mesuré hors saison ou un jour mal choisi, qui gonfle la marge disponible ; et une modélisation faite à puissance de ventilation nominale, alors que les pointes réelles arrivent en canicule. D'où l'intérêt des <strong>mesures après mise en service</strong>, et de la distance aux habitations : elle, au moins, ne se renégocie pas.</p>` },
  ],
};

const EN: typeof FR = {
  // See fr/nuisances-data-center.astro: every query this page earns is about noise, not one
  // contains "nuisance". The word leads the title now; the URL stays, it is indexed.
  title: "Data center noise — how loud, how close, and what the permit says",
  metaDescription: "Data center noise: cooling that never stops, backup generators under test, fuel tanks, water abstracted. How loud, how close, and what environmental assessments actually document.",
  tagline: "Independent observatory",
  h1: "Data center nuisances",
  lead: `A data center is usually argued over its global balance sheet — electricity, climate. What is experienced from the street is more concrete: continuous <strong>noise</strong>, <strong>backup generators</strong> under test, <strong>fuel tanks</strong>, <strong>water</strong> abstracted and discharged. Across the 41 French <a href="${AE}" target="_blank" rel="noopener">environmental authority</a> opinions we reviewed, backup generators come up most often, ahead of fuel tanks and noise.`,

  questionsH2: "The questions people ask us",
  questions: [
    {
      q: "How far away from a data center is considered safe?",
      r: `<p>There is <strong>no regulated distance</strong> between a data center and homes. What the rules govern is not separation but <strong>emergence</strong>: how much the noise rises at the neighbour's when the plant runs. The French order of 23 January 1997 generally allows <strong>+5&nbsp;dB(A) by day and +3&nbsp;dB(A) at night</strong>.</p>
      <p>The consequence runs against intuition: <strong>the same machine does not have the same effect everywhere</strong>. Countryside that drops to 30&nbsp;dB(A) at night leaves almost no headroom, while an industrial district absorbs it. Two houses the same distance from two identical sites do not live the same life.</p>
      <p>That is why we publish the <strong>distance to the nearest dwellings</strong> on each fiche where we have it: it is the one parameter nobody can fix afterwards, and it should be read alongside the rest of the file. <a href='/map/'>Find the site near you on the map</a>.</p>` },
    {
      q: "Are there health risks to living near a data center?",
      r: `<p>We are not a health authority and <strong>we measure no health effect</strong> — asserting one, or denying it, would be equally dishonest. What we can say rests on the facts filed in the dossiers.</p>
      <p>What comes up most often in the environmental-authority opinions we reviewed: <strong>backup generators</strong>, <strong>fuel tanks</strong> and <strong>noise</strong>. Night-time noise is the most constant subject, because it is continuous and has no lull — that is what sets a data center apart from a building site or a road.</p>
      <p>We publish these facts <strong>next to the grade, never inside it</strong>, and we say what they rest on. To see when these questions can still change a project, read <a href='/fr/comprendre#droits'>Rights and calendar</a> (in French).</p>` },
  ],

  mesure: {
    avec: `Our corpus holds <strong>{sites} sites</strong>. A <strong>distance to the nearest dwellings</strong> is available for <strong>{habitations}</strong> of them — the one exposure indicator we compute ourselves, the same way everywhere.`,
    sans: `The <strong>distance to the nearest dwellings</strong> is the one exposure indicator we compute ourselves, the same way everywhere; we publish it on every fiche where we have it.`,
  },
  locale: "en-GB",
  sections: [
    { icone: "noise", h2: "Noise, the everyday nuisance",
      corps: `<p>A data center never stops: it continuously evacuates the heat of its machines. The noise therefore comes not from the building but from what sits on and around it — <strong>fans, dry coolers, chillers</strong> — and it is <strong>continuous, day and night</strong>. That is what sets it apart from a building site or a road: there is no lull.</p>
      <p>Three things matter more than the raw level:</p>
      <ul>
        <li><strong>The gap with background noise</strong>, not the absolute decibel. French regulation for classified installations reasons in terms of “emergence”: the order of 23 January 1997 generally allows <strong>+5 dB(A) by day and +3 dB(A) at night</strong> at the neighbour's, with a site-boundary ceiling of around 70 dB(A) by day and 60 dB(A) at night. The direct consequence: countryside that drops to 30 dB(A) at night leaves almost no headroom, while the same machine disappears into an industrial district. <strong>The same equipment is not acceptable everywhere.</strong></li>
        <li><strong>The distance to the nearest dwellings.</strong> It is the one parameter nobody can fix afterwards, which is why we measure it site by site.</li>
        <li><strong>Tonality.</strong> A whine or a hum on a marked frequency is noticed far more than a diffuse rush at the same level; regulation treats it separately for that reason.</li>
      </ul>
      <p>Cooling technology changes the picture: an air-cooled site relies on large fan banks that <strong>speed up precisely during heatwaves</strong> — when windows are open. An adiabatic or water-cooled site blows less hard, but consumes water. Liquid cooling at the chip reduces fans further. <strong>There is no choice without a trade-off</strong>: noise, water and electricity are exchanged against one another.</p>` },

    { icone: "engine", h2: "Backup generators: why they count as a nuisance",
      corps: `<p>These engines produce nothing in normal operation. They exist so the site survives a grid outage — and a data center sizes its fleet to carry <strong>its entire</strong> load, cooling included, with redundancy on top. As an order of magnitude, a site of several tens of megawatts therefore lines up <strong>several dozen engines</strong> the size of a ship's. It is a backup power station, parked at the edge of town.</p>
      <p>Neighbours do not hear them during outages, which are rare. They hear them during the <strong>periodic tests</strong> that are required to guarantee the engines will start: typically one test per month per machine, plus a longer load test once a year. A site with thirty engines therefore runs tests <strong>very regularly</strong>, and that is by far the first source of friction in the files we read.</p>
      <p>From what point is it “a lot”? Two markers rather than a figure: the fleet's <strong>aggregate power</strong> — beyond a certain thermal threshold it moves the installation into a more demanding authorisation regime for classified installations — and the <strong>ratio between that power and the size of the municipality</strong>. It is the second ratio that explains why the same project passes unnoticed in an industrial zone and stalls elsewhere.</p>` },

    { icone: "fuel", h2: "Fuel tanks: quantity before substance",
      corps: `<p>Generators mean reserves: the engines must run for hours, sometimes days, without a delivery. A file therefore declares a <strong>storage volume</strong>, and that volume is what we record.</p>
      <p>The declared fuel varies: some opinions declare hydrotreated vegetable oil, others heating oil or diesel.</p>
      <p>So what? The substance matters less than three things:</p>
      <ul>
        <li><strong>The quantity stored.</strong> That is what measures the risk: a few cubic metres and several hundred are not managed the same way, and it is volume thresholds — not the nature of the product — that trigger the heaviest obligations.</li>
        <li><strong>Containment.</strong> Double-skinned tanks, retention bunds able to hold both the fuel and the water used to fight a fire: that is where most of it is decided. An uncontained spill near a drinking-water catchment or a watercourse is the scenario that worries the authorities.</li>
        <li><strong>What comes out of the exhaust during tests.</strong> Nitrogen oxides and particulates, at roof height, during working hours.</li>
      </ul>
      <p>So what is virtuous? <strong>Less volume, better contained</strong>, and a cleaner fuel. Hydrotreated vegetable oil clearly reduces emissions and is not fossil — but it burns, and it is stored in the same tanks: it improves the balance, it does not remove the risk.</p>` },

    { icone: "water", h2: "Water: the volume, but also the discharge",
      corps: `<p>Cooling with water costs far less electricity than cooling with air — the same trade-off as above, seen from the other side. Two questions follow: <strong>how much</strong> is abstracted, and <strong>from which resource</strong>. A modest volume taken from a catchment already stressed in summer weighs more than a large volume taken elsewhere.</p>
      <p>Discharge is the forgotten half: the water leaves <strong>warmer</strong>, more concentrated in salts, and treated against scaling and legionella. For a municipality the question is not only “how much”, but “<strong>to where, at what temperature, with what treatment</strong>”.</p>` },

    { icone: "energy", h2: "Electricity: the nuisance you cannot see",
      corps: `<p>It is neither heard nor smelt, yet it often decides. A high-power connection consumes grid capacity that the territory's other uses — industry, housing, transport — will not have for years, and its queue is counted in years. It is also what makes the generator fleet so large: the more powerful the site, the more imposing its backup.</p>` },

    { icone: "hidden", h2: "The “hidden” part",
      corps: `<p>An operator presents itself through its energy efficiency. It rarely highlights its generators, its tanks or the acoustic modelling the environmental authority requires of it. <strong>The gap between a communication brochure and the content of an assessment file is, in itself, information</strong> — and it is the raw material of this page.</p>` },

    { icone: "hazard", h2: "When the site itself carries a hazard",
      corps: `<p>Some projects store fuel in quantity on site, lithium-ion batteries, sometimes hydrogen. The site then <strong>carries</strong> a hazard instead of merely enduring one — that is no longer a nuisance but a risk, handled in the hazard study. We publish these elements <strong>as information, next to the grade</strong>, for as long as coverage does not allow grading them without distorting comparison between sites.</p>` },

    { icone: "measure", h2: "Where our measurement stands",
      corps: `<p>{mesure} The nuisance detail comes from the <strong>41 environmental opinions reviewed</strong>: projects that went through assessment, <strong>not the whole estate</strong>. These facts are published <strong>next to the grade, not inside it</strong>.</p>
      <p>See <a href='/acceptability-of-data-centers/'>data center acceptability</a>, <a href='/map/'>the map</a> and <a href='/methodology/'>the method</a>.</p>` },
  ],

  details: [
    { resume: "More — what is an environmental authority opinion worth?",
      corps: `<p>For projects of this size the developer must produce an <strong>impact assessment</strong>. A body separate from the service that will grant the permit examines it and issues a <strong>public opinion</strong>: in France, the <a href="${AE}" target="_blank" rel="noopener">environmental authority</a>, most often a regional <a href="${MRAE}" target="_blank" rel="noopener">mission (MRAe)</a>.</p>
      <p>What that opinion <strong>is</strong>: an expert view on the <em>quality of the file</em> and on how the project accounts for the environment, with recommendations. What it <strong>is not</strong>: an authorisation, nor a refusal. The opinion does not decide the project.</p>
      <p>It is not decorative either. The developer must <strong>answer it in writing</strong>, and both opinion and answer are <strong>attached to the file put to public consultation</strong>; the permitting authority must justify its decision in their light. In practice an opinion that points to a gap forces the file to be completed, and gives elected officials and residents something solid to stand on. <strong>It is the single most useful document to read before forming a view on a project</strong> — and it is our raw material.</p>` },

    { resume: "More — how a project's noise is assessed",
      corps: `<p>Before construction, an acoustician measures the <strong>existing background noise</strong>, by day and by night, at the nearest dwellings. The site in operation is then modelled and compared: what is judged is the <strong>gap</strong> between the two, not the machine's own level. Commitments follow — screens, enclosures, fans slowed at night, generator tests barred in the evening — and a <strong>verification campaign after commissioning</strong> is normally required.</p>
      <p>Two classic weaknesses, visible when reading the opinions: background noise measured out of season or on a poorly chosen day, which inflates the available headroom; and modelling done at nominal fan power when the real peaks arrive in a heatwave. Hence the value of <strong>post-commissioning measurements</strong> — and of distance to dwellings, which at least cannot be renegotiated.</p>` },
  ],
};

/** La table servie au gabarit : `NUISANCES[lang]`. */
export const NUISANCES: Record<Langue, typeof FR> = { fr: FR, en: EN };

/**
 * La table avec sa phrase de mesure remplie — `nuisances(lang, sites, habitations)`.
 *
 * Les deux comptes viennent du corpus (accesseurs de `config/stats`) et valent `null` quand
 * le build n'a pas de corpus : la variante SANS chiffre sort alors, et la page reste juste.
 * Le remplacement traverse `sections` sans savoir laquelle porte le trou — sur une chaîne
 * qui ne le contient pas, c'est un passage à vide.
 */
export function nuisances(lang: Langue, sites: number | null, habitations: number | null) {
  const t = NUISANCES[lang];
  const phrase =
    sites !== null && habitations !== null
      ? t.mesure.avec
          .replace("{sites}", sites.toLocaleString(t.locale))
          .replace("{habitations}", habitations.toLocaleString(t.locale))
      : t.mesure.sans;
  return {
    ...t,
    sections: t.sections.map((s) => ({ ...s, corps: s.corps.replace("{mesure}", phrase) })),
  };
}
