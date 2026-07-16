// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// "Qui sommes-nous" texts — single source for the home #about section AND the
// dedicated /fr/qui-sommes-nous page (i18n §13: one block per language, no drift).

export const FR_ABOUT = {
  aboutTitle: "Qui sommes-nous ?",
  aboutPhotoAlt: "Franck Bardol, fondateur de ScoreMyDataCenter",
  aboutPhotoCaption: "Franck Bardol, fondateur de ScoreMyDataCenter",
  aboutLinkedinUrl: "https://www.linkedin.com/in/franckbardol/",
  ia: {
    heading: "L'IA au service de la méthode, pas à la place de l'humain.",
    sub: "Parce que <strong class=\"hero-red\">noter tous les data centers d'Europe ne s'improvise pas</strong>. Une architecture d'agents spécialisés pour traiter des dizaines de milliers de sources afin de noter chaque data center avec rigueur — sous contrôle humain.",
    steps: [
      { icon: "collect", title: "Collecter", body: "Les agents repèrent les sources publiques utiles : dossiers réglementaires, données institutionnelles, documents opérateurs, cartes, décisions locales et articles de presse." },
      { icon: "structure", title: "Structurer", body: "Ils transforment ces sources hétérogènes en données comparables : puissance, eau, foncier, réseau, concertation, transparence, statut du projet." },
      { icon: "verify", title: "Vérifier", body: "Ils croisent les informations, signalent les contradictions, identifient les données manquantes et conservent la source de chaque fait." },
      { icon: "compute", title: "Calculer", body: "Ils appliquent la même méthode à chaque projet, recalculent les notes et vérifient que les seuils, règles et garde-fous sont respectés." },
      { icon: "watch", title: "Surveiller", body: "Ils détectent les changements : nouvelle autorisation, recours, modification du projet, publication d'un chiffre, évolution du réseau ou du contexte local." },
      { icon: "publish", title: "Préparer la publication", body: "Ils produisent une première synthèse factuelle et signalent les formulations fragiles. La validation finale, les arbitrages et la publication restent sous ma responsabilité." },
    ],
    humanTitle: "Responsabilité humaine",
    humanBody: "Je définis la stratégie, les méthodes, les pondérations ESG et les règles de publication. J'arbitre les cas complexes, tranche les désaccords, orchestre les agents IA spécialisés et assume chaque note publiée. Les agents proposent, l'humain tranche.",
    closing: "<strong>L'IA permet de travailler à l'échelle du corpus. La méthode, les arbitrages et la responsabilité restent humains.</strong>",
    closingCta: "Comprendre notre méthode",
  },
  teamCta: "Envie d'en être ? Contribuez sur GitHub ↗",
  teamCtaUrl: "https://github.com/bardolfranck/scoremydatacenter",
  aboutHeadline: "Un observatoire indépendant.<br>Conçu et dirigé par un expert.",
  founderLine: "ScoreMyDataCenter est l'œuvre de <strong>Franck Bardol</strong>. À l'intersection de l'infrastructure IA, de l'éthique et de la décision publique.",
  founderHeading: "Le fondateur",
  aboutPledges: [
    { icon: "verify", text: "<strong>Indépendant</strong> : aucun financement opérateur, aucun conflit d'intérêt." },
    { icon: "publish", text: "<strong>Public</strong> : méthode, sources et notes accessibles à tous." },
    { icon: "human", text: "<strong>Ouvert</strong> : corrections et réponses possibles pour chaque projet noté." },
  ],
  founderFacts: [
    { icon: "gradcap", text: "Professeur associé (Université de Genève, entre autres) · expert indépendant en IA auprès de la <strong>Commission européenne</strong>" },
    { icon: "users", text: "Distingué parmi les <a href=\"https://www.usinenouvelle.com/article/portraits-les-mediateurs-de-l-ia.N650229\" target=\"_blank\" rel=\"noopener\">100 experts français de l'IA</a> · participation à la rédaction du <strong>rapport Villani</strong> sur la stratégie IA de la France" },
    { icon: "chartup", text: "Première carrière en banque d'investissement, responsable de la recherche quantitative : <strong>construire des scores rigoureux et opposables est son métier d'origine</strong>" },
    { icon: "book", text: "Auteur de <a href=\"https://www.lgdj.fr/concevoir-une-ia-responsable-9782297287678.html\" target=\"_blank\" rel=\"noopener\">« Concevoir une IA responsable — Pourquoi ce n'est jamais “juste un outil” ? Manuel d'éthique de terrain »</a> (LGDJ), <a href=\"https://www.amazon.fr/High-performance-Algorithmic-Trading-Machine-Learning/dp/9365893895\" target=\"_blank\" rel=\"noopener\">« High-Performance Algorithmic Trading using AI »</a> et <a href=\"https://www.amazon.fr/Baby-Sitters-lIA-syndrome-Reprenez-attention-ebook/dp/B0GX34RW3P\" target=\"_blank\" rel=\"noopener\">« Les Baby-Sitters de l'IA »</a>" },
    { icon: "bank", text: "Fondateur du <a href=\"https://www.meetup.com/paris-machine-learning-applications-group/\" target=\"_blank\" rel=\"noopener\">Paris Machine Learning</a> (8 500 experts en IA) · plus de 50 000 professionnels formés sur LinkedIn Learning" },
  ],
  expertiseKicker: "Une expertise au service du débat public",
  expertise: [
    { icon: "users", title: "10+ ans", body: "en IA, données et modélisation quantitative" },
    { icon: "bank", title: "Entreprises & institutions", body: "Projets IA pour la Banque de France, Thales, Airbus, General Electric, Bouygues Colas, SNCF, Saint-Gobain, STMicroelectronics, le projet de fusion nucléaire ITER/CEA, Vinci, GlaxoSmithKline, le Centre National d'Études Spatiales, des PME-PMI…" },
    { icon: "book", title: "Formation & transmission", body: "cours, conférences, keynotes, MOOCs LinkedIn Learning (50 000+ professionnels formés à l'IA)" },
    { icon: "certificate", title: "Éthique & responsabilité", body: "Master IA et machine learning (Université Paris 6 – CNAM), Management (Université de Genève), Modélisation statistique (Université Paris Nanterre) et Certificat en Éthique Philosophique (Université de Genève)" },
  ],
  strengthsTitle: "Ce qui fait la force de ScoreMyDataCenter",
  strengths: [
    "Un corpus exhaustif et actualisé en continu",
    "Une méthode unique, publique et versionnée",
    "Des notes expliquées, sourcées et contestables",
    "Un observatoire construit pour durer",
  ],
};

export const EN_ABOUT = {
  aboutTitle: "Who we are",
  aboutPhotoAlt: "Franck Bardol, founder of ScoreMyDataCenter",
  aboutPhotoCaption: "Franck Bardol, founder of ScoreMyDataCenter",
  aboutLinkedinUrl: "https://www.linkedin.com/in/franckbardol/",
  ia: {
    heading: "AI in service of the method, not in place of the human.",
    sub: "Because <strong class=\"hero-red\">grading every data center in Europe is not something you improvise</strong>. An architecture of specialised agents processes tens of thousands of sources to grade each data center rigorously — under human control.",
    steps: [
      { icon: "collect", title: "Collect", body: "The agents locate the useful public sources: regulatory files, institutional data, operator documents, maps, local decisions and press articles." },
      { icon: "structure", title: "Structure", body: "They turn these heterogeneous sources into comparable data: power, water, land, grid, consultation, transparency, project status." },
      { icon: "verify", title: "Verify", body: "They cross-check information, flag contradictions, identify missing data and keep the source of every fact." },
      { icon: "compute", title: "Compute", body: "They apply the same method to every project, recompute the grades and check that thresholds, rules and guardrails are respected." },
      { icon: "watch", title: "Monitor", body: "They detect changes: a new authorisation, an appeal, a project modification, a published figure, an evolution of the grid or the local context." },
      { icon: "publish", title: "Prepare publication", body: "They produce a first factual synthesis and flag fragile wording. Final validation, arbitration and publication remain my responsibility." },
    ],
    humanTitle: "Human responsibility",
    humanBody: "I define the strategy, the methods, the ESG weightings and the publication rules. I arbitrate complex cases, settle disagreements, orchestrate the specialised AI agents and stand behind every published grade. Agents propose, the human decides.",
    closing: "<strong>AI makes it possible to work at the scale of the corpus. The method, the arbitration and the responsibility remain human.</strong>",
    closingCta: "Understand our method",
  },
  teamCta: "Want in? Contribute on GitHub ↗",
  teamCtaUrl: "https://github.com/bardolfranck/scoremydatacenter",
  aboutHeadline: "An independent observatory.<br>Designed and led by an expert.",
  founderLine: "ScoreMyDataCenter is the work of <strong>Franck Bardol</strong>. At the intersection of AI infrastructure, ethics and public decision-making.",
  founderHeading: "The founder",
  aboutPledges: [
    { icon: "verify", text: "<strong>Independent</strong>: no operator funding, no conflict of interest." },
    { icon: "publish", text: "<strong>Public</strong>: method, sources and grades accessible to all." },
    { icon: "human", text: "<strong>Open</strong>: corrections and responses possible for every scored project." },
  ],
  founderFacts: [
    { icon: "gradcap", text: "Associate professor (University of Geneva, among others) · independent AI expert advising the <strong>European Commission</strong>" },
    { icon: "users", text: "Recognized among <a href=\"https://www.usinenouvelle.com/article/portraits-les-mediateurs-de-l-ia.N650229\" target=\"_blank\" rel=\"noopener\">France's top 100 AI experts</a> · contributor to the <strong>Villani report</strong> on France's national AI strategy" },
    { icon: "chartup", text: "First career in investment banking as head of quantitative research: <strong>building rigorous, defensible scores is his original trade</strong>" },
    { icon: "book", text: "Author of <a href=\"https://www.lgdj.fr/concevoir-une-ia-responsable-9782297287678.html\" target=\"_blank\" rel=\"noopener\">“Concevoir une IA responsable — Pourquoi ce n'est jamais ‘juste un outil’ ? Manuel d'éthique de terrain”</a> (LGDJ), <a href=\"https://www.amazon.fr/High-performance-Algorithmic-Trading-Machine-Learning/dp/9365893895\" target=\"_blank\" rel=\"noopener\">“High-Performance Algorithmic Trading using AI”</a> and <a href=\"https://www.amazon.fr/Baby-Sitters-lIA-syndrome-Reprenez-attention-ebook/dp/B0GX34RW3P\" target=\"_blank\" rel=\"noopener\">“Les Baby-Sitters de l'IA”</a>" },
    { icon: "bank", text: "Founder of <a href=\"https://www.meetup.com/paris-machine-learning-applications-group/\" target=\"_blank\" rel=\"noopener\">Paris Machine Learning</a> (8,500 AI experts) · 50,000+ professionals trained on LinkedIn Learning" },
  ],
  expertiseKicker: "Expertise in service of the public debate",
  expertise: [
    { icon: "users", title: "10+ years", body: "in AI, data and quantitative modelling" },
    { icon: "bank", title: "Companies & institutions", body: "AI projects for Banque de France, Thales, Airbus, General Electric, Bouygues Colas, SNCF, Saint-Gobain, STMicroelectronics, the ITER/CEA nuclear-fusion project, Vinci, GlaxoSmithKline, the French space agency CNES, SMEs…" },
    { icon: "book", title: "Teaching & transmission", body: "courses, conferences, keynotes, LinkedIn Learning MOOCs (50,000+ professionals trained in AI)" },
    { icon: "certificate", title: "Ethics & responsibility", body: "MSc in AI and machine learning (Université Paris 6 – CNAM), Management (University of Geneva), statistical modelling (Université Paris Nanterre) and a Certificate in Philosophical Ethics (University of Geneva)" },
  ],
  strengthsTitle: "What makes ScoreMyDataCenter strong",
  strengths: [
    "An exhaustive corpus, continuously updated",
    "A single method, public and versioned",
    "Grades that are explained, sourced and contestable",
    "An observatory built to last",
  ],
};
