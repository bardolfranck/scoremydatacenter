// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Blocks 2, 4, 5, 6, 7 of the pedagogy section — authored by the methodology
// lead (2026-07-06), every legal claim and figure verified at source before
// integration. Fixes applied at integration:
//  - Fouju ~90 ha (official public consultation) instead of the delivered 87
//  - Fiscalimmo (domain unreachable) replaced by service-public.fr for the
//    CFE/exemptions claim
//  - Légifrance URL for art. L.123-9 corrected (delivered id was a 404)
// Block 5 carries the lawyer-review flag (appeal deadlines) tracked in PLAN.

export interface RichPoint {
  icon?: "energy" | "water" | "land" | "local" | "transparency" | "noise" | "tax";
  lead: string;
  body: string;
}
export interface RichQA {
  q: string;
  a: string;
}
export interface RichLink {
  name: string;
  desc: string;
  url?: string;
}
export interface RichBlock {
  intro?: string;
  inFrance?: string;
  points?: RichPoint[];
  qas?: RichQA[];
  linkGroups?: { title: string; links: RichLink[] }[];
  closing?: string;
  takeaway?: string;
  sources?: { label: string; url: string }[];
}

export const RICH_FR: Record<string, RichBlock> = {
  commune: {
    intro:
      "Un data center ne se contente pas d'occuper un terrain : il s'installe dans les réseaux de la commune — l'eau, l'électricité, les routes — et dans son budget. Cinq points concrets.",
    points: [
      {
        icon: "energy",
        lead: "L'électricité.",
        body: "Les grands projets récents demandent 100 à 200 MW, l'équivalent de la consommation électrique de villes comme Le Mans ou Saint-Étienne<sup><a href='#src-commune-1'>1</a></sup>. Cette puissance passe par le réseau local : postes électriques, lignes, travaux.",
      },
      {
        icon: "water",
        lead: "L'eau.",
        body: "Certaines techniques de refroidissement consomment très peu d'eau, d'autres beaucoup : les data centers d'Amazon ont prélevé environ 9,5 milliards de litres dans le monde en 2025, premier chiffre annuel publié par l'entreprise<sup><a href='#src-commune-2'>2</a></sup>. Le sujet est pris au sérieux par la loi : depuis mai 2026, un permis de construire peut être refusé en raison de « tensions structurelles sur la ressource en eau » (loi n° 2026-403 du 26 mai 2026, art. 35)<sup><a href='#src-commune-3'>3</a></sup>.",
      },
      {
        icon: "noise",
        lead: "Le bruit.",
        body: "Le refroidissement fonctionne jour et nuit, et les générateurs de secours sont testés régulièrement. Les niveaux admis sont fixés par les autorisations du site — ils s'écrivent, donc se vérifient.",
      },
      {
        icon: "land",
        lead: "Le foncier et l'emploi.",
        body: "Un méga-projet peut occuper des dizaines d'hectares — environ 90 pour le Campus IA de Fouju<sup><a href='#src-commune-4'>4</a></sup>. Pour une emprise comparable, une plateforme logistique emploie typiquement 300 à 400 personnes, un data center autour de 15 à 20<sup><a href='#src-commune-5'>5</a></sup>.",
      },
      {
        icon: "tax",
        lead: "La fiscalité.",
        body: "Le site paie des impôts locaux (taxe foncière, cotisation foncière des entreprises, notamment), répartis entre commune, intercommunalité et autres collectivités — avec des exonérations possibles les premières années<sup><a href='#src-commune-6'>6</a></sup>. D'où la question à poser : quelles recettes, pour qui, à partir de quand ?",
      },
    ],
    takeaway:
      "Aucun de ces impacts n'est bon ou mauvais en soi : tout dépend du projet, du lieu et de ce qui est écrit dans le dossier. C'est exactement ce que les blocs suivants apprennent à lire.",
    sources: [
      { label: "RTE, « Les data centers en chiffres clés », 2026", url: "https://www.rte-france.com/bases-electricite/consommation-electricite/essor-data-centers-france" },
      { label: "Data Center Dynamics, 2026 (eau AWS)", url: "https://www.datacenterdynamics.com/en/news/amazon-data-centers-used-25bn-gallons-of-water-in-2025/" },
      { label: "Gossement Avocats, loi n° 2026-403, art. 35", url: "https://www.gossement-avocats.com/blog/centres-de-donnees-data-centers-ce-que-change-la-loi-de-simplification-de-la-vie-economique/" },
      { label: "Concertation publique Campus IA", url: "https://www.concertation-campus-ia.fr/fr/comprendre-le-projet" },
      { label: "AFP / Connaissance des énergies, juin 2026 (emplois)", url: "https://www.connaissancedesenergies.org/afp/data-centers-en-ile-de-france-des-installations-energivores-mais-avares-en-emplois-260601" },
      { label: "service-public.fr (CFE, exonérations)", url: "https://entreprendre.service-public.fr/vosdroits/F23547" },
    ],
  },

  "bon-projet": {
    intro:
      "Il n'existe pas de « bon opérateur » ou de « mauvais opérateur » qui se devinerait à la réputation. Il existe des <strong>choix de projet</strong>, qui se lisent dans le dossier — ou dont l'absence se remarque. En voici six, et où les vérifier.",
    points: [
      {
        lead: "Annoncer tôt.",
        body: "Le projet est présenté publiquement avant le dépôt du permis, pas découvert sur un panneau. Où vérifier : la date de la première communication publique comparée à la date de dépôt.",
      },
      {
        lead: "Écrire les engagements sur l'eau.",
        body: "La technique de refroidissement et la consommation annuelle figurent dans le dossier d'autorisation, pas seulement dans la plaquette. Où vérifier : le dossier consultable en préfecture ou en mairie.",
      },
      {
        lead: "Contractualiser la chaleur.",
        body: "La loi impose d'étudier la valorisation de la chaleur produite (code de l'énergie, art. L.236-2, issu de la loi du 30 avril 2025)<sup><a href='#src-bon-projet-1'>1</a></sup>. La différence se joue entre une étude de principe et un contrat signé avec un réseau de chaleur, une piscine, des serres. Où vérifier : demander si un contrat existe, et avec qui.",
      },
      {
        lead: "Choisir le terrain qui coûte le moins au territoire.",
        body: "Friche ou terrain déjà artificialisé plutôt que terres agricoles ou espaces naturels. Où vérifier : la nature du terrain, dans l'étude d'impact.",
      },
      {
        lead: "S'engager à publier les données en exploitation.",
        body: "Consommations d'électricité et d'eau, efficacité mesurée — la loi prévoit d'ailleurs une déclaration de performance pour les centres de données (code de l'énergie, art. L.236-1)<sup><a href='#src-bon-projet-1'>1</a></sup>. Où vérifier : ce que le dossier promet de rendre public, et à quel rythme.",
      },
      {
        lead: "Négocier des bénéfices locaux écrits.",
        body: "Conventions, fonds, aménagements : ce qui est signé engage, ce qui est évoqué en réunion non.",
      },
    ],
    takeaway:
      "Un « bon » projet n'est pas un projet sans impact : c'est un projet dont les impacts sont écrits, chiffrés et vérifiables. Notre grille note exactement cela : ce que le projet choisit, pas seulement ce qu'il subit.",
    sources: [
      { label: "Gossement Avocats, 2026 (code de l'énergie, art. L.236-1 et L.236-2 ; loi n° 2025-391 du 30 avril 2025)", url: "https://www.gossement-avocats.com/blog/centres-de-donnees-data-centers-ce-que-change-la-loi-de-simplification-de-la-vie-economique/" },
    ],
  },

  droits: {
    intro:
      "Un data center n'obtient pas une autorisation, mais plusieurs : un permis de construire, et le plus souvent une autorisation environnementale — le régime ICPE, qui encadre les installations industrielles<sup><a href='#src-droits-1'>1</a></sup>. Chacune a son calendrier, et chacune ouvre des droits au public.",
    points: [
      {
        lead: "Avant le dépôt : la concertation.",
        body: "Une concertation préalable, parfois avec un garant nommé par la CNDP (la Commission nationale du débat public), peut se tenir en amont. Attention : depuis un décret du 3 mars 2026, les data centers ne font plus partie des projets à saisine obligatoire de la CNDP<sup><a href='#src-droits-2'>2</a></sup> — la tenue d'une concertation dépend donc du porteur du projet ou de l'État. Si elle a lieu, c'est le moment où le projet peut encore changer le plus.",
      },
      {
        lead: "Pendant l'instruction : l'enquête publique.",
        body: "Pour les projets soumis à évaluation environnementale, elle dure au minimum 30 jours (code de l'environnement, art. L.123-9)<sup><a href='#src-droits-3'>3</a></sup>. Chacun — habitant ou non de la commune — peut déposer des observations écrites, en mairie ou en ligne. Elles sont versées au dossier et le commissaire enquêteur y répond dans son rapport.",
      },
      {
        lead: "Cas particulier depuis mai 2026.",
        body: "Un data center peut être qualifié par décret de « projet d'intérêt national majeur » : le permis est alors instruit par le préfet, et non par le maire. Même dans ce cas, le permis peut être refusé en raison de « tensions structurelles sur la ressource en eau » (loi n° 2026-403 du 26 mai 2026, art. 35)<sup><a href='#src-droits-1'>1</a></sup>.",
      },
      {
        lead: "Après l'autorisation : les recours.",
        body: "Les délais sont courts — en règle générale deux mois contre un permis de construire à compter de son affichage, quatre mois pour les tiers contre une autorisation environnementale à compter de sa publication. Passé ces délais, l'autorisation devient définitive.",
      },
    ],
    takeaway:
      "Le calendrier fait tout : la même question posée en concertation peut changer le projet, posée après l'autorisation elle ne change plus rien. D'où l'intérêt d'arriver tôt — avec la <a href='#questions'>checklist du bloc 3</a>.",
    sources: [
      { label: "Gossement Avocats, loi n° 2026-403, 2026", url: "https://www.gossement-avocats.com/blog/centres-de-donnees-data-centers-ce-que-change-la-loi-de-simplification-de-la-vie-economique/" },
      { label: "Actu-Environnement, décret du 3 mars 2026 (CNDP)", url: "https://www.actu-environnement.com/ae/news/cndp-projets-saisine-decret-data-centers-eolien-mer-raccordement-lignes-electrique-sous-marines-47625.php4" },
      { label: "Code de l'environnement, art. L.123-9", url: "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033038541" },
    ],
  },

  faq: {
    qas: [
      {
        q: "Un panneau d'enquête publique vient d'apparaître près de chez moi.",
        a: "Notez la date de fin : l'enquête dure au minimum 30 jours (voir <a href='#droits'>Droits et calendrier</a>). Vous pouvez déposer une observation écrite, en mairie ou en ligne, même sans habiter la commune. Une observation précise et factuelle pèse plus qu'une pétition de principe : appuyez-vous sur la <a href='#questions'>checklist du bloc 3</a>.",
      },
      {
        q: "Je suis élu, un cabinet vient de m'appeler pour un projet.",
        a: "Rien ne vous oblige à réagir à chaud. Demandez le dossier par écrit, avec trois chiffres : la puissance en mégawatts, la consommation d'eau prévue, le calendrier de dépôt. La <a href='#questions'>checklist du bloc 3</a> tient sur une page — apportez-la en réunion.",
      },
      {
        q: "Le projet est déjà autorisé. C'est trop tard ?",
        a: "Pour contester, les délais courent vite (voir <a href='#droits'>Droits et calendrier</a>). Mais il reste des leviers : demander la mise en place d'une instance de suivi, et la publication régulière des données d'exploitation promises au dossier.",
      },
      {
        q: "Qui contacter, concrètement ?",
        a: "La mairie ou l'intercommunalité pour l'urbanisme ; la préfecture pour le dossier d'autorisation environnementale ; le commissaire enquêteur pendant l'enquête publique ; et les collectifs déjà actifs près de chez vous (voir <a href='#aller-plus-loin'>Aller plus loin</a>).",
      },
      {
        q: "Comment savoir ce qui existe déjà autour de chez moi ?",
        a: "Les cartes publiques recensent les sites existants et les projets — voir <a href='#aller-plus-loin'>Aller plus loin</a>.",
      },
      {
        q: "Où consulter les données d'un projet ?",
        a: "Chaque fiche de data center affiche la note, et chaque indicateur renvoie à sa source publique par un lien cliquable (données ouvertes RTE, INSEE, avis d'autorité environnementale, décisions de justice…) : tout est revérifiable. Les documents officiels sont doublés d'une copie archivée pour rester consultables dans le temps ; les articles de presse sont liés, jamais recopiés. Ni la note ni sa justification ne sont jamais payantes.",
      },
    ],
  },

  "aller-plus-loin": {
    intro: "Pour creuser le sujet, des ressources ouvertes et gratuites — les mêmes que nous utilisons.",
    linkGroups: [
      {
        title: "Cartes et recensements",
        links: [
          { name: "DCWatch (Hubblo)", desc: "commun numérique de l'empreinte des data centers (PUE, WUE, CUE, surface, eau), données ODbL téléchargeables — carte : datacenters.hubblo.org", url: "https://dcwatch.hubblo.org" },
          { name: "Le nuage était sous nos pieds", desc: "carte participative des sites, projets et mobilisations en France, tenue par un collectif marseillais", url: "https://lenuageetaitsousnospieds.org" },
          { name: "Data Center Watch", desc: "suivi de la contestation des projets aux États-Unis", url: "https://www.datacenterwatch.org" },
        ],
      },
      {
        title: "Chiffres de référence",
        links: [
          { name: "RTE, « Les data centers en chiffres clés »", desc: "le panorama officiel français — puissances, raccordements, projections (mis à jour en 2026)", url: "https://www.rte-france.com/bases-electricite/consommation-electricite/essor-data-centers-france" },
          { name: "ADEME, « Prospective des consommations des data centers 2024-2060 »", desc: "les scénarios français à long terme", url: "https://librairie.ademe.fr/energies/8910-prospective-d-evolution-des-consommations-des-data-centers-a-court-moyen-et-long-terme-de-2024-a-2060.html" },
          { name: "AIE, « Energy and AI »", desc: "les data centers dans le système électrique mondial (2025, en anglais)", url: "https://www.iea.org/reports/energy-and-ai" },
        ],
      },
      {
        title: "Comprendre vos droits",
        links: [
          { name: "CNDP — debatpublic.fr", desc: "la participation du public, mode d'emploi", url: "https://www.debatpublic.fr" },
          { name: "Géorisques", desc: "retrouver les installations classées (ICPE) autour de chez vous", url: "https://www.georisques.gouv.fr" },
          { name: "Gossement Avocats (blog)", desc: "analyses juridiques à jour du droit des data centers", url: "https://www.gossement-avocats.com/blog/" },
        ],
      },
    ],
    closing:
      "Et pour comparer les projets entre eux : notre <a href='/fr/carte'>carte</a>, notre <a href='/fr/classement'>classement</a> et la <a href='/fr/#method'>méthode complète</a> — c'est tout l'objet de ce site.",
  },
};

export const RICH_EN: Record<string, RichBlock> = {
  municipality: {
    intro:
      "A data center does not just occupy a plot: it settles into the municipality's networks — water, electricity, roads — and into its budget. Five concrete points.",
    points: [
      {
        icon: "energy",
        lead: "Electricity.",
        body: "Recent large projects request 100 to 200 MW, the equivalent of the electricity consumption of cities like Le Mans or Saint-Étienne<sup><a href='#src-municipality-1'>1</a></sup>. That power flows through the local grid: substations, lines, works.",
      },
      {
        icon: "water",
        lead: "Water.",
        body: "Some cooling techniques use very little water, others a lot: Amazon's data centers withdrew about 9.5 billion liters worldwide in 2025, the first annual figure the company has published<sup><a href='#src-municipality-2'>2</a></sup>. The law takes the matter seriously: since May 2026, a building permit can be refused in France over “structural tensions on the water resource” (law no. 2026-403 of May 26, 2026, art. 35)<sup><a href='#src-municipality-3'>3</a></sup>.",
      },
      {
        icon: "noise",
        lead: "Noise.",
        body: "Cooling runs day and night, and backup generators are tested regularly. Permitted levels are set by the site's authorizations — they are written down, so they can be checked.",
      },
      {
        icon: "land",
        lead: "Land and jobs.",
        body: "A mega-project can occupy dozens of hectares — about 90 for the Fouju AI Campus<sup><a href='#src-municipality-4'>4</a></sup>. For a comparable footprint, a logistics platform typically employs 300 to 400 people, a data center around 15 to 20<sup><a href='#src-municipality-5'>5</a></sup>.",
      },
      {
        icon: "tax",
        lead: "Tax revenue.",
        body: "The site pays local taxes (property tax and the local business levy, among others), split between the municipality, the inter-municipal body and other authorities — with possible exemptions in the first years<sup><a href='#src-municipality-6'>6</a></sup>. Hence the question to ask: what revenue, for whom, starting when?",
      },
    ],
    takeaway:
      "None of these impacts is good or bad in itself: it all depends on the project, the place, and what is written in the filing. That is exactly what the next blocks teach you to read.",
    sources: [
      { label: "RTE, “Data centers in key figures”, 2026", url: "https://www.rte-france.com/bases-electricite/consommation-electricite/essor-data-centers-france" },
      { label: "Data Center Dynamics, 2026 (AWS water)", url: "https://www.datacenterdynamics.com/en/news/amazon-data-centers-used-25bn-gallons-of-water-in-2025/" },
      { label: "Gossement Avocats, law no. 2026-403, art. 35", url: "https://www.gossement-avocats.com/blog/centres-de-donnees-data-centers-ce-que-change-la-loi-de-simplification-de-la-vie-economique/" },
      { label: "Campus IA public consultation", url: "https://www.concertation-campus-ia.fr/fr/comprendre-le-projet" },
      { label: "AFP / Connaissance des énergies, June 2026 (jobs)", url: "https://www.connaissancedesenergies.org/afp/data-centers-en-ile-de-france-des-installations-energivores-mais-avares-en-emplois-260601" },
      { label: "service-public.fr (CFE, exemptions)", url: "https://entreprendre.service-public.fr/vosdroits/F23547" },
    ],
  },

  "good-project": {
    intro:
      "There is no “good operator” or “bad operator” to be guessed from reputation. There are <strong>project choices</strong>, which can be read in the filing — or whose absence is telling. Here are six, and where to check them.",
    points: [
      {
        lead: "Announce early.",
        body: "The project is presented publicly before the permit is filed, not discovered on a notice board. Where to check: the date of the first public communication against the filing date.",
      },
      {
        lead: "Put water commitments in writing.",
        body: "The cooling technique and annual consumption are in the permitting documents, not only in the brochure. Where to check: the permitting file, available from the local authority.",
      },
      {
        lead: "Put heat recovery under contract.",
        body: "The difference lies between a paper study and a signed contract with a heat network, a swimming pool, greenhouses. Where to check: ask whether a contract exists, and with whom.",
      },
      {
        lead: "Pick the land that costs the territory least.",
        body: "Brownfield or already-artificialized land rather than farmland or natural areas. Where to check: the nature of the land, in the impact study.",
      },
      {
        lead: "Commit to publishing operating data.",
        body: "Electricity and water consumption, measured efficiency. Where to check: what the permitting documents promise to make public, and how often.",
      },
      {
        lead: "Negotiate written local benefits.",
        body: "Agreements, funds, facilities: what is signed binds; what is mentioned in a meeting does not.",
      },
    ],
    inFrance:
      "The law backs two of these levers: operators must study reusing the heat produced (energy code, art. L.236-2, from the law of April 30, 2025) and file a performance declaration for data centers (energy code, art. L.236-1)<sup><a href='#src-good-project-1'>1</a></sup>.",
    takeaway:
      "A “good” project is not a project without impacts: it is a project whose impacts are written, quantified and verifiable. Our grid scores exactly that: what the project chooses, not only what it endures.",
    sources: [
      { label: "Gossement Avocats, 2026 (energy code, art. L.236-1 and L.236-2; law no. 2025-391 of April 30, 2025)", url: "https://www.gossement-avocats.com/blog/centres-de-donnees-data-centers-ce-que-change-la-loi-de-simplification-de-la-vie-economique/" },
    ],
  },

  rights: {
    intro:
      "A data center does not get one authorization but several: a building permit and, most often, an environmental authorization — the French ICPE regime, which governs industrial installations<sup><a href='#src-rights-1'>1</a></sup>. Each has its calendar, and each opens rights to the public.",
    points: [
      {
        lead: "Before filing: the public consultation.",
        body: "A prior consultation, sometimes with a guarantor appointed by the CNDP (France's national commission for public debate), may be held upstream. Note: since a decree of March 3, 2026, data centers are no longer among the projects requiring mandatory CNDP referral<sup><a href='#src-rights-2'>2</a></sup> — whether a consultation happens now depends on the developer or the State. When it does happen, it is the moment the project can still change the most.",
      },
      {
        lead: "During review: the public inquiry.",
        body: "For projects subject to environmental assessment it lasts at least 30 days (environment code, art. L.123-9)<sup><a href='#src-rights-3'>3</a></sup>. Anyone — resident of the municipality or not — can file written observations, at the town hall or online. They join the file and the inquiry commissioner responds to them in the report.",
      },
      {
        lead: "A special case since May 2026.",
        body: "A data center can be designated by decree a “project of major national interest”: the permit is then processed by the préfet, not the mayor. Even then, the permit can be refused over “structural tensions on the water resource” (law no. 2026-403 of May 26, 2026, art. 35)<sup><a href='#src-rights-1'>1</a></sup>.",
      },
      {
        lead: "After authorization: appeals.",
        body: "Deadlines are short — as a general rule two months against a building permit from its posting, four months for third parties against an environmental authorization from its publication. Past those deadlines, the authorization becomes final.",
      },
    ],
    takeaway:
      "The calendar is everything: the same question asked during the consultation can change the project; asked after authorization, it changes nothing. Hence the point of arriving early — with the <a href='#questions'>block-3 checklist</a>.",
    sources: [
      { label: "Gossement Avocats, law no. 2026-403, 2026", url: "https://www.gossement-avocats.com/blog/centres-de-donnees-data-centers-ce-que-change-la-loi-de-simplification-de-la-vie-economique/" },
      { label: "Actu-Environnement, decree of March 3, 2026 (CNDP)", url: "https://www.actu-environnement.com/ae/news/cndp-projets-saisine-decret-data-centers-eolien-mer-raccordement-lignes-electrique-sous-marines-47625.php4" },
      { label: "Environment code, art. L.123-9", url: "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033038541" },
    ],
  },

  faq: {
    qas: [
      {
        q: "A public-inquiry notice just appeared near my home.",
        a: "Note the end date: the inquiry lasts at least 30 days (see <a href='#rights'>Rights and timeline</a>). You can file a written observation, at the town hall or online, even if you do not live in the municipality. A precise, factual observation carries more weight than a petition of principle: lean on the <a href='#questions'>block-3 checklist</a>.",
      },
      {
        q: "I am a local official; a firm just called me about a project.",
        a: "Nothing obliges you to react on the spot. Ask for the file in writing, with three figures: power in megawatts, planned water consumption, filing calendar. The <a href='#questions'>block-3 checklist</a> fits on one page — bring it to the meeting.",
      },
      {
        q: "The project is already authorized. Is it too late?",
        a: "To contest it, deadlines run fast (see <a href='#rights'>Rights and timeline</a>). But levers remain: ask for a monitoring body to be set up, and for regular publication of the operating data promised in the filing.",
      },
      {
        q: "Whom to contact, concretely?",
        a: "The town hall or inter-municipal body for planning; the prefecture for the environmental authorization file; the inquiry commissioner during the public inquiry; and the groups already active near you (see <a href='#further'>Going further</a>).",
      },
      {
        q: "How do I know what already exists around me?",
        a: "Public maps list existing sites and projects — see <a href='#further'>Going further</a>.",
      },
      {
        q: "Where can I consult a project's data?",
        a: "Every data-center page shows the score, and each indicator links to its public source (open data from RTE, INSEE, environmental-authority opinions, court decisions…): all of it is re-checkable. Official documents are mirrored by an archived copy so they stay reachable over time; press articles are linked, never reproduced. Neither the score nor its justification is ever behind a paywall.",
      },
    ],
  },

  further: {
    intro: "To dig deeper, open and free resources — the same ones we use.",
    linkGroups: [
      {
        title: "Maps and inventories",
        links: [
          { name: "DCWatch (Hubblo)", desc: "digital common for data centre footprints (PUE, WUE, CUE, land, water), downloadable ODbL data — map: datacenters.hubblo.org", url: "https://dcwatch.hubblo.org" },
          { name: "Le nuage était sous nos pieds", desc: "participatory map of sites, projects and mobilizations in France, maintained by a Marseille collective", url: "https://lenuageetaitsousnospieds.org" },
          { name: "Data Center Watch", desc: "tracking of project opposition in the United States", url: "https://www.datacenterwatch.org" },
        ],
      },
      {
        title: "Reference figures",
        links: [
          { name: "RTE, “Data centers in key figures”", desc: "the official French panorama — power, connections, projections (updated 2026)", url: "https://www.rte-france.com/bases-electricite/consommation-electricite/essor-data-centers-france" },
          { name: "ADEME, “Data center consumption outlook 2024-2060”", desc: "the French long-term scenarios", url: "https://librairie.ademe.fr/energies/8910-prospective-d-evolution-des-consommations-des-data-centers-a-court-moyen-et-long-terme-de-2024-a-2060.html" },
          { name: "IEA, “Energy and AI”", desc: "data centers in the world's power system (2025)", url: "https://www.iea.org/reports/energy-and-ai" },
        ],
      },
      {
        title: "Understanding your rights",
        links: [
          { name: "CNDP — debatpublic.fr", desc: "public participation, how it works", url: "https://www.debatpublic.fr" },
          { name: "Géorisques", desc: "find the classified industrial installations (ICPE) around you", url: "https://www.georisques.gouv.fr" },
          { name: "Gossement Avocats (blog)", desc: "up-to-date legal analysis of data center law", url: "https://www.gossement-avocats.com/blog/" },
        ],
      },
    ],
    closing:
      "And to compare projects with each other: our <a href='/fr/carte'>map</a>, our <a href='/fr/classement'>ranking</a> and the <a href='/#method'>full method</a> — that is what this site is for.",
  },
};
