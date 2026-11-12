// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// LA VISITE EN VIDÉO — « 2-minute tour » (Franck, 2026-11-10).
//
// UNE seule vidéo, en ANGLAIS, pour tous les lecteurs (décision Franck du 2026-11-10 : le
// multilingue est abandonné — trop de chantier pour un gain incertain). Les sous-titres
// anglais sont INCRUSTÉS dans l'image. Seuls les libellés autour de la vidéo suivent la langue
// de la page, et ils disent honnêtement que la vidéo est en anglais.
//
// Hébergement : R2 (media.scoremydatacenter.org/video/), lecteur natif du navigateur — aucun
// cookie, aucun tiers. Les fichiers sont versionnés DANS LEUR NOM : une nouvelle coupe = un
// nouveau nom, jamais un écrasement (cache immutable d'un an côté R2).
//
// v3 (2026-11-11, GO Franck) : narrée par la voix de synthèse du début à la fin — plus
// d'image ni de voix de Franck sur la version SITE (la version jury reste sur YouTube).
// L'affiche (la carte) et l'extrait « agent » de la méthodologie ne changent pas.
// v5 (2026-11-12, GO Franck via mkg) : le fil « Start with why » — le maire et l'acceptabilité
// d'abord, puis la méthode (grilles de la profession complétées par les chiffres du
// territoire, agents IA, un humain qui vérifie), puis le produit (carte, mur satellite), et
// un appel final. 2:13. Elle a sa PAGE DE PARTAGE par langue (`VISITE_PARTAGE`) : un lien
// collé sur LinkedIn, X ou WhatsApp doit s'afficher avec l'affiche, pas comme un fichier .mp4.
import type { LangueDeclaree } from "./langues";

const MEDIA = "https://media.scoremydatacenter.org/video/";

export const VISITE_MEDIA = {
  tour: MEDIA + "tour-en-v5.mp4",
  tourPoster: MEDIA + "tour-poster.jpg",
  loop: MEDIA + "tour-loop.mp4",
  agent: MEDIA + "tour-agent-en.mp4",
  agentPoster: MEDIA + "tour-agent-poster.jpg",
  /** ISO 8601, pour le balisage VideoObject. */
  tourDuration: "PT2M13S",
  agentDuration: "PT21S",
  uploadDate: "2026-11-12",
} as const;

export const VISITE: Record<LangueDeclaree, {
  cta: string;
  sub: string;
  ficheLink: string;
  close: string;
  play: string;
  agentH2: string;
  agentLead: string;
  ldName: string;
  ldDescription: string;
  ldAgentName: string;
  ldAgentDescription: string;
}> = {
  en: {
    cta: "The 2-minute tour",
    sub: "Why we score data centers, and how — 2:13.",
    ficheLink: "New here? Take the 2-minute tour",
    close: "Close",
    play: "Play the 2-minute tour",
    agentH2: "Who does the work: AI agents read, a human checks",
    agentLead: "Rating thousands of sites one by one is no job for a human team alone. Here is how the work is split — told by one of the agents.",
    ldName: "ScoreMyDataCenter — the 2-minute tour",
    ldDescription: "Why social acceptance of data centers starts with the mayor and the residents, and how we measure it: the profession's own grids completed with local figures, AI agents that read the public record and a human who checks — then the map and the satellite wall of sites.",
    ldAgentName: "How ScoreMyDataCenter works: AI agents read, a human checks",
    ldAgentDescription: "Collector agents crawl public registries, a reader agent parses permits and filings, a verifier rejects anything implausible, and a human runs the final gate.",
  },
  fr: {
    cta: "La visite en 2 minutes",
    sub: "Pourquoi et comment nous notons les data centers — 2:13, en anglais sous-titré.",
    ficheLink: "Nouveau ici ? La visite en 2 minutes",
    close: "Fermer",
    play: "Lancer la visite en 2 minutes",
    agentH2: "Qui fait le travail : des agents IA lisent, un humain vérifie",
    agentLead: "Noter des milliers de sites un par un n'est pas à la portée d'une équipe humaine seule. Voici comment le travail est réparti — raconté par l'un des agents (en anglais sous-titré).",
    ldName: "ScoreMyDataCenter — la visite en 2 minutes",
    ldDescription: "Pourquoi l'acceptabilité d'un data center commence par le maire et les riverains, et comment nous la mesurons : les grilles de la profession complétées par les chiffres du territoire, des agents IA qui lisent les sources publiques et un humain qui vérifie — puis la carte et le mur satellite des sites.",
    ldAgentName: "Comment travaille ScoreMyDataCenter : des agents IA lisent, un humain vérifie",
    ldAgentDescription: "Des agents collecteurs parcourent les registres publics, un agent lecteur dépouille permis et dossiers, un vérificateur rejette l'invraisemblable, et un humain tient la dernière porte.",
  },
  nl: {
    cta: "De rondleiding in 2 minuten",
    sub: "Waarom en hoe we datacenters een cijfer geven — 2:13, in het Engels ondertiteld.",
    ficheLink: "Nieuw hier? Bekijk de rondleiding van 2 minuten",
    close: "Sluiten",
    play: "Start de rondleiding van 2 minuten",
    agentH2: "Wie doet het werk: AI-agenten lezen, een mens controleert",
    agentLead: "Duizenden locaties één voor één beoordelen is geen werk voor een menselijk team alleen. Zo is het werk verdeeld — verteld door een van de agenten (in het Engels ondertiteld).",
    ldName: "ScoreMyDataCenter — de rondleiding in 2 minuten",
    ldDescription: "Waarom de maatschappelijke aanvaarding van een datacenter begint bij de burgemeester en de omwonenden, en hoe we die meten: de rasters van de sector aangevuld met lokale cijfers, AI-agenten die openbare bronnen lezen en een mens die controleert — daarna de kaart en de satellietwand van locaties.",
    ldAgentName: "Hoe ScoreMyDataCenter werkt: AI-agenten lezen, een mens controleert",
    ldAgentDescription: "Verzamelagenten doorzoeken openbare registers, een leesagent ontleedt vergunningen en dossiers, een controleur weigert het onwaarschijnlijke, en een mens bewaakt de laatste poort.",
  },
};

// LA PAGE DE PARTAGE — une par langue, déclarée aussi dans `config/routes.ts` (famille
// « video »). Les boutons sous la vidéo de l'accueil pointent ICI, jamais vers le .mp4 :
// c'est la page qui porte les balises d'aperçu (og:image = l'affiche, og:video).
export const VISITE_PARTAGE: Record<LangueDeclaree, {
  path: string;
  title: string;
  description: string;
  h1: string;
  lead: string;
  home: string;
  shareLabel: string;
  copy: string;
  copied: string;
  shareText: string;
}> = {
  en: {
    path: "/video/",
    title: "The 2-minute tour (video) — ScoreMyDataCenter",
    description: "Why social acceptance of data centers starts with the mayor and the residents, and how an independent observatory scores every site from public sources. 2:13.",
    h1: "ScoreMyDataCenter — the 2-minute tour",
    lead: "Why acceptance of a data center starts with the mayor and the residents, how we measure it from public sources, and what you can do with it. 2:13, English with burned-in subtitles.",
    home: "Visit the observatory",
    shareLabel: "Share this video",
    copy: "Copy link",
    copied: "Link copied",
    shareText: "Why social acceptance of data centers starts with the mayor — the 2-minute tour of ScoreMyDataCenter",
  },
  fr: {
    path: "/fr/video/",
    title: "La visite en 2 minutes (vidéo) — ScoreMyDataCenter",
    description: "Pourquoi l'acceptabilité d'un data center commence par le maire et les riverains, et comment un observatoire indépendant note chaque site à partir des sources publiques. 2:13.",
    h1: "ScoreMyDataCenter — la visite en 2 minutes",
    lead: "Pourquoi l'acceptabilité d'un data center commence par le maire et les riverains, comment nous la mesurons à partir des sources publiques, et ce que vous pouvez en faire. 2:13, en anglais sous-titré.",
    home: "Découvrir l'observatoire",
    shareLabel: "Partager cette vidéo",
    copy: "Copier le lien",
    copied: "Lien copié",
    shareText: "Pourquoi l'acceptabilité d'un data center commence par le maire — la visite de ScoreMyDataCenter en 2 minutes",
  },
  nl: {
    path: "/nl/video/",
    title: "De rondleiding in 2 minuten (video) — ScoreMyDataCenter",
    description: "Waarom de aanvaarding van een datacenter begint bij de burgemeester en de omwonenden, en hoe een onafhankelijk observatorium elke locatie beoordeelt op basis van openbare bronnen. 2:13.",
    h1: "ScoreMyDataCenter — de rondleiding in 2 minuten",
    lead: "Waarom de aanvaarding van een datacenter begint bij de burgemeester en de omwonenden, hoe we die meten op basis van openbare bronnen, en wat u ermee kunt doen. 2:13, in het Engels ondertiteld.",
    home: "Ontdek het observatorium",
    shareLabel: "Deel deze video",
    copy: "Link kopiëren",
    copied: "Link gekopieerd",
    shareText: "Waarom de aanvaarding van een datacenter begint bij de burgemeester — de rondleiding van ScoreMyDataCenter in 2 minuten",
  },
};
