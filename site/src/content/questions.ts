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
  items: ChecklistItem[];
}
export interface Checklist {
  intro: string;
  groups: ChecklistGroup[];
  takeaway: string;
  printLabel: string;
  printHref: string;
  printTitle: string;
  printFooter: string;
}

export const CHECKLIST_FR: Checklist = {
  intro:
    "En réunion publique, en permanence ou en conseil municipal : ces questions se posent telles quelles. Elles suivent les cinq piliers de notre grille de notation.",
  groups: [
    {
      pillar: "Énergie",
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
  printLabel: "Version imprimable (une page)",
  printHref: "/fr/comprendre/one-pager",
  printTitle: "Les bonnes questions à poser sur un projet de data center",
  printFooter: "ScoreMyDataCenter — observatoire indépendant · scoremydatacenter.org · CC BY-SA 4.0",
};

export const CHECKLIST_EN: Checklist = {
  intro:
    "At a public meeting, at the counter or in a council session: these questions can be asked as they are. They follow the five pillars of our scoring grid.",
  groups: [
    {
      pillar: "Energy",
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
          q: "Is the water commitment in the permit filing, or only in the project's communications?",
          why: "Only what is written in the official filing is enforceable.",
        },
      ],
    },
    {
      pillar: "Land & biodiversity",
      items: [
        {
          q: "How much land will be artificialized, and on what kind of ground — brownfield, farmland, natural area?",
          why: "An industrial brownfield and farmland do not carry the same cost for the municipality.",
        },
        {
          q: "How does the project fit the municipality's land-sobriety objective (France's “zero net artificialization” target, 2021 Climate and Resilience Act)?",
          why: "Hectares consumed here will be missing elsewhere — housing, facilities, activity.",
        },
        {
          q: "Are protected or inventoried areas (Natura 2000, ZNIEFF — inventories of remarkable natural habitats) nearby, and what does the impact study say?",
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
          q: "What tax revenue, and for whom exactly — the municipality, the inter-municipal body, the department?",
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
          q: "Where can the full filing be consulted, and when is the public inquiry?",
          why: "Those dates open your rights — missing them closes remedies (see <a href='#rights'>Rights and timeline</a>).",
        },
      ],
    },
  ],
  takeaway:
    "An unanswered question is not a failure: note it, date it, ask again in writing. That is exactly what our grid does: what is not publicly documented shows up in the confidence level (high, medium or low) attached to every grade.",
  printLabel: "Printable version (one page)",
  printHref: "/understand/one-pager",
  printTitle: "The right questions to ask about a data center project",
  printFooter: "ScoreMyDataCenter — independent observatory · scoremydatacenter.org · CC BY-SA 4.0",
};
