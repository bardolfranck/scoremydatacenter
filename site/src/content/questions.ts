// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// "The right questions to ask" — block 3 of the pedagogy section, authored by
// the methodology lead (2026-07-06). Single source for the web block AND the
// printable one-pager: they can never diverge. FR is the authored original;
// EN is the translation.

export interface ChecklistItem {
  q: string;
  why: string;
}
export interface ChecklistGroup {
  pillar: string;
  icon: "energy" | "water" | "land" | "local" | "transparency";
  items: ChecklistItem[];
}
export interface Checklist {
  intro: string;
  groups: ChecklistGroup[];
  takeaway: string;
  printLabel: string;
  printHref: string;
  pdfLabel: string;
  pdfHref: string;
  printTitle: string;
  printFooter: string;
}

export const CHECKLIST_FR: Checklist = {
  intro:
    "En réunion publique, en permanence ou en conseil municipal : ces questions se posent telles quelles. Elles suivent les cinq piliers de notre grille de notation.",
  groups: [
    {
      pillar: "Énergie",
      icon: "energy",
      items: [
        {
          q: "Quelle puissance électrique demandez-vous au réseau, en mégawatts, et où en est la demande de raccordement ?",
          why: "La puissance raccordée dit la taille réelle du projet, mieux que la surface du bâtiment.",
        },
        {
          q: "La chaleur produite sera-t-elle récupérée — par qui, et avec quel contrat signé ?",
          why: "La récupération de chaleur est souvent annoncée, rarement contractualisée.",
        },
        {
          q: "Quelle efficacité énergétique (PUE, le rapport entre l'électricité totale consommée et celle qui alimente vraiment les serveurs) sera mesurée et publiée une fois le site en service ?",
          why: "Un chiffre promis avant construction n'engage à rien tant qu'il n'est pas mesuré et publié.",
        },
      ],
    },
    {
      pillar: "Eau",
      icon: "water",
      items: [
        {
          q: "Comment le site sera-t-il refroidi, et combien d'eau consommera-t-il par an, prélevée où — réseau potable, forage, rivière ?",
          why: "Selon la technique de refroidissement, la consommation d'eau va de quasi nulle à considérable.",
        },
        {
          q: "Que se passe-t-il en cas d'arrêté sécheresse : le site réduira-t-il ses prélèvements, et est-ce écrit ?",
          why: "Mieux vaut connaître la réponse avant la crise que pendant.",
        },
        {
          q: "L'engagement sur l'eau figure-t-il dans le dossier d'autorisation, ou seulement dans la communication du projet ?",
          why: "Seul ce qui est écrit dans le dossier officiel est opposable.",
        },
      ],
    },
    {
      pillar: "Foncier & biodiversité",
      icon: "land",
      items: [
        {
          q: "Quelle surface sera artificialisée, et sur quel type de terrain — friche, terres agricoles, espace naturel ?",
          why: "Une friche industrielle et des terres agricoles n'ont pas le même coût pour la commune.",
        },
        {
          q: "Comment le projet s'inscrit-il dans l'objectif de sobriété foncière de la commune (« zéro artificialisation nette », loi Climat et résilience, 2021) ?",
          why: "Les hectares consommés ici manqueront ailleurs — logements, équipements, activité.",
        },
        {
          q: "Des zones protégées ou inventoriées (Natura 2000, ZNIEFF — les inventaires de milieux naturels remarquables) sont-elles à proximité, et que dit l'étude d'impact ?",
          why: "La réponse se vérifie en ligne ; une hésitation est un signal.",
        },
        {
          q: "Qu'est-il prévu en fin de vie du site — démantèlement, remise en état — et qui paie ?",
          why: "Sans plan de fin de vie, un bâtiment de cette taille devient la charge de la commune.",
        },
      ],
    },
    {
      pillar: "Impact local",
      icon: "local",
      items: [
        {
          q: "Combien d'emplois permanents sur le site une fois construit — sans compter les emplois du chantier ?",
          why: "Les deux chiffres sont souvent mélangés, et celui du chantier est toujours plus flatteur.",
        },
        {
          q: "Quel niveau de bruit en limite de propriété, de jour et de nuit, et à quelle fréquence les générateurs de secours seront-ils testés ?",
          why: "Le bruit des installations de refroidissement est permanent, celui des essais est récurrent — les deux se mesurent et s'écrivent dans le dossier.",
        },
        {
          q: "Quelles recettes fiscales, pour qui exactement — la commune, l'intercommunalité, le département ?",
          why: "La retombée annoncée « pour le territoire » ne va pas forcément à votre commune.",
        },
        {
          q: "Pendant le chantier : combien de camions par jour, sur quelles routes, pendant combien de mois ?",
          why: "Le chantier dure des années ; c'est l'impact le plus immédiat pour les riverains.",
        },
      ],
    },
    {
      pillar: "Transparence & gouvernance",
      icon: "transparency",
      items: [
        {
          q: "Qui porte le projet : la société locale créée pour l'occasion, ou le groupe derrière elle — et qui répondra dans dix ans ?",
          why: "Les projets sont souvent portés par des sociétés dédiées ; l'interlocuteur d'aujourd'hui peut disparaître.",
        },
        {
          q: "Quelles données seront publiées pendant l'exploitation — électricité, eau, efficacité mesurées — et à quel rythme ?",
          why: "Un engagement de publication se vérifie ; une promesse orale, non.",
        },
        {
          q: "Une instance de suivi associant élus et riverains est-elle prévue, et avec quel rôle ?",
          why: "Le dialogue après la mise en service est le premier levier pour que les engagements soient tenus.",
        },
        {
          q: "Où le dossier complet est-il consultable, et quand se tient l'enquête publique ?",
          why: "Ces dates ouvrent vos droits — les manquer ferme des recours (voir <a href='#droits'>Droits et calendrier</a>).",
        },
      ],
    },
  ],
  takeaway:
    "Une question sans réponse n'est pas un échec : notez-la, datez-la, redemandez par écrit. C'est exactement ce que fait notre grille : ce qui n'est pas documenté publiquement se lit dans la confiance (haute, moyenne ou faible) qui accompagne chaque note.",
  printLabel: "Version imprimable",
  printHref: "/fr/comprendre/one-pager/",
  pdfLabel: "Télécharger le PDF (une page)",
  pdfHref: "/downloads/questions-data-center-fr.pdf",
  printTitle: "Les bonnes questions à poser sur un projet de data center",
  printFooter: "ScoreMyDataCenter — observatoire indépendant · scoremydatacenter.org · CC BY-SA 4.0",
};

export const CHECKLIST_EN: Checklist = {
  intro:
    "At a public meeting, at the counter or in a council session: these questions can be asked as they are. They follow the five pillars of our scoring grid.",
  groups: [
    {
      pillar: "Energy",
      icon: "energy",
      items: [
        {
          q: "How much grid power are you requesting, in megawatts, and where does the connection request stand?",
          why: "Connected power tells the real size of the project better than the building's footprint.",
        },
        {
          q: "Will the heat produced be recovered — by whom, and under what signed contract?",
          why: "Heat recovery is often announced, rarely contracted.",
        },
        {
          q: "What energy efficiency (PUE — the ratio of total electricity consumed to the share that actually powers the servers) will be measured and published once the site operates?",
          why: "A figure promised before construction commits to nothing until it is measured and published.",
        },
      ],
    },
    {
      pillar: "Water",
      icon: "water",
      items: [
        {
          q: "How will the site be cooled, and how much water will it use per year, drawn from where — drinking network, borehole, river?",
          why: "Depending on the cooling technique, water use ranges from near zero to considerable.",
        },
        {
          q: "What happens under a drought order: will the site reduce its withdrawals, and is that in writing?",
          why: "Better to know the answer before the crisis than during it.",
        },
        {
          q: "Is the water commitment in the permitting documents, or only in the project's communications?",
          why: "Only what is written in the official permitting documents is enforceable.",
        },
      ],
    },
    {
      pillar: "Land & biodiversity",
      icon: "land",
      items: [
        {
          q: "How much land will be artificialized, and on what kind of ground — brownfield, farmland, natural area?",
          why: "An industrial brownfield and farmland do not carry the same cost for the municipality.",
        },
        {
          q: "How does the project fit the local land-sobriety or no-net-land-take objectives (in France: the “zero net artificialization” target, 2021 Climate and Resilience Act)?",
          why: "Hectares consumed here will be missing elsewhere — housing, facilities, activity.",
        },
        {
          q: "Are protected or inventoried natural areas nearby (in France: Natura 2000, ZNIEFF), and what does the impact study say?",
          why: "The answer can be checked online; hesitation is a signal.",
        },
        {
          q: "What is planned for the site's end of life — dismantling, restoration — and who pays?",
          why: "Without an end-of-life plan, a building this size becomes the municipality's burden.",
        },
      ],
    },
    {
      pillar: "Local impact",
      icon: "local",
      items: [
        {
          q: "How many permanent on-site jobs once built — not counting construction jobs?",
          why: "The two figures are often blended, and the construction one always flatters.",
        },
        {
          q: "What noise level at the property line, day and night, and how often will the backup generators be tested?",
          why: "Cooling noise is permanent, testing noise is recurring — both can be measured and written into the filing.",
        },
        {
          q: "What tax revenue, and for whom exactly — your municipality, or a wider authority?",
          why: "Revenue announced “for the territory” does not necessarily reach your municipality.",
        },
        {
          q: "During construction: how many trucks per day, on which roads, for how many months?",
          why: "Construction lasts years; it is the most immediate impact for residents.",
        },
      ],
    },
    {
      pillar: "Transparency & governance",
      icon: "transparency",
      items: [
        {
          q: "Who carries the project: the local company created for the occasion, or the group behind it — and who will answer in ten years?",
          why: "Projects are often carried by dedicated entities; today's contact may disappear.",
        },
        {
          q: "What data will be published during operation — measured electricity, water, efficiency — and how often?",
          why: "A publication commitment can be verified; a spoken promise cannot.",
        },
        {
          q: "Is a monitoring body bringing together officials and residents planned, and with what role?",
          why: "Dialogue after commissioning is the first lever for commitments to be kept.",
        },
        {
          q: "Where can the full permitting documents be consulted, and when does the public get to weigh in?",
          why: "Those dates open your rights — missing them closes remedies (see <a href='#rights'>Rights and timeline — France</a>).",
        },
      ],
    },
  ],
  takeaway:
    "An unanswered question is not a failure: note it, date it, ask again in writing. That is exactly what our grid does: what is not publicly documented shows up in the confidence level (high, medium or low) attached to every grade.",
  printLabel: "Printable version",
  printHref: "/understand/one-pager/",
  pdfLabel: "Download the PDF (one page)",
  pdfHref: "/downloads/questions-data-center-en.pdf",
  printTitle: "The right questions to ask about a data center project",
  printFooter: "ScoreMyDataCenter — independent observatory · scoremydatacenter.org · CC BY-SA 4.0",
};

// ── NÉERLANDAIS — rédigé après la passe native. Le one-pager NL et son PDF
// n'existent pas encore : printHref/pdfHref sont des slugs PROPOSÉS (harnais).
export const CHECKLIST_NL: Checklist = {
  intro:
    "Op een publieksbijeenkomst, op het spreekuur of in de gemeenteraad: deze vragen kunnen zo worden gesteld. Ze volgen de vijf pijlers van onze meetlat.",
  groups: [
    {
      pillar: "Energie",
      icon: "energy",
      items: [
        {
          q: "Welk elektrisch vermogen vraagt u aan het net, in megawatt, en hoever staat de aansluitaanvraag?",
          why: "Het aansluitvermogen zegt meer over de echte omvang van het project dan de oppervlakte van het gebouw.",
        },
        {
          q: "Wordt de geproduceerde warmte teruggewonnen — door wie, en met welk getekend contract?",
          why: "Warmteterugwinning wordt vaak aangekondigd, zelden gecontracteerd.",
        },
        {
          q: "Welke energie-efficiëntie (PUE, de verhouding tussen alle verbruikte elektriciteit en wat werkelijk de servers voedt) wordt gemeten en gepubliceerd zodra de site draait?",
          why: "Een getal dat vóór de bouw wordt beloofd, bindt tot niets zolang het niet gemeten en gepubliceerd is.",
        },
      ],
    },
    {
      pillar: "Water",
      icon: "water",
      items: [
        {
          q: "Hoe wordt de site gekoeld, en hoeveel water verbruikt hij per jaar, onttrokken waar — drinkwaternet, boring, rivier?",
          why: "Afhankelijk van de koeltechniek loopt het waterverbruik van bijna nul tot aanzienlijk.",
        },
        {
          q: "Wat gebeurt er bij een droogtebesluit: vermindert de site zijn onttrekkingen, en staat dat op papier?",
          why: "Beter het antwoord kennen vóór de crisis dan erin.",
        },
        {
          q: "Staat de watertoezegging in het vergunningsdossier, of alleen in de communicatie van het project?",
          why: "Alleen wat in het officiële dossier staat, is afdwingbaar.",
        },
      ],
    },
    {
      pillar: "Bodem & biodiversiteit",
      icon: "land",
      items: [
        {
          q: "Welke oppervlakte wordt verhard, en op welk soort terrein — brownfield, landbouwgrond, natuur?",
          why: "Een oud industrieterrein en landbouwgrond kosten de gemeente niet hetzelfde.",
        },
        {
          q: "Hoe past het project in de doelstelling van zuinig grondgebruik van de gemeente (‘zéro artificialisation nette’, Franse klimaatwet van 2021)?",
          why: "De hectaren die hier opgaan, ontbreken elders — woningen, voorzieningen, bedrijvigheid.",
        },
        {
          q: "Liggen er beschermde of geïnventariseerde gebieden in de buurt (Natura 2000, ZNIEFF — de Franse inventarissen van waardevolle natuur), en wat zegt het milieueffectrapport?",
          why: "Het antwoord is online te controleren; aarzeling is een signaal.",
        },
        {
          q: "Wat is er voorzien voor het einde van de levensduur — ontmanteling, herstel van het terrein — en wie betaalt?",
          why: "Zonder plan voor het einde wordt een gebouw van deze omvang de last van de gemeente.",
        },
      ],
    },
    {
      pillar: "Lokale impact",
      icon: "local",
      items: [
        {
          q: "Hoeveel vaste banen op de site zodra hij gebouwd is — de bouwbanen niet meegeteld?",
          why: "De twee getallen worden vaak vermengd, en dat van de bouw oogt altijd gunstiger.",
        },
        {
          q: "Welk geluidsniveau aan de terreingrens, overdag en ’s nachts, en hoe vaak worden de noodstroomaggregaten getest?",
          why: "Het geluid van de koeling is permanent, dat van de proeven keert terug — beide zijn te meten en horen in het dossier.",
        },
        {
          q: "Welke belastinginkomsten, en voor wie precies — de gemeente, het intergemeentelijk verband, het departement?",
          why: "De opbrengst die ‘voor de streek’ wordt aangekondigd, gaat niet vanzelf naar uw gemeente.",
        },
        {
          q: "Tijdens de bouw: hoeveel vrachtwagens per dag, over welke wegen, hoeveel maanden lang?",
          why: "De bouw duurt jaren; het is de meest directe impact voor omwonenden.",
        },
      ],
    },
    {
      pillar: "Transparantie & governance",
      icon: "transparency",
      items: [
        {
          q: "Wie draagt het project: de lokale vennootschap die ervoor is opgericht, of de groep erachter — en wie geeft over tien jaar antwoord?",
          why: "Projecten worden vaak gedragen door speciaal opgerichte vennootschappen; de gesprekspartner van vandaag kan verdwijnen.",
        },
        {
          q: "Welke gegevens worden tijdens de exploitatie gepubliceerd — gemeten elektriciteit, water, efficiëntie — en hoe vaak?",
          why: "Een publicatietoezegging is te controleren; een mondelinge belofte niet.",
        },
        {
          q: "Komt er een opvolgingscommissie met bestuurders en omwonenden, en met welke rol?",
          why: "De dialoog na de ingebruikname is de eerste hefboom om toezeggingen gestand te doen.",
        },
        {
          q: "Waar is het volledige dossier in te zien, en wanneer loopt de inspraak?",
          why: "Die datums openen uw rechten — wie ze mist, sluit beroepswegen af (zie <a href='#rechten'>Rechten en tijdpad</a>).",
        },
      ],
    },
  ],
  takeaway:
    "Een vraag zonder antwoord is geen mislukking: noteer haar, dateer haar, stel haar opnieuw, schriftelijk. Precies dat doet onze meetlat: wat niet publiek gedocumenteerd is, leest u af aan het vertrouwen (hoog, gemiddeld of laag) dat elk cijfer vergezelt.",
  printLabel: "Printversie",
  printHref: "/nl/datacenters-begrijpen/one-pager/",
  pdfLabel: "Download de pdf (één pagina)",
  pdfHref: "/downloads/questions-data-center-nl.pdf",
  printTitle: "De juiste vragen bij een datacenterproject",
  printFooter: "ScoreMyDataCenter — onafhankelijk observatorium · scoremydatacenter.org · CC BY-SA 4.0",
};
