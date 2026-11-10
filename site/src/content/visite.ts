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
import type { LangueDeclaree } from "./langues";

const MEDIA = "https://media.scoremydatacenter.org/video/";

export const VISITE_MEDIA = {
  tour: MEDIA + "tour-en.mp4",
  tourPoster: MEDIA + "tour-poster.jpg",
  loop: MEDIA + "tour-loop.mp4",
  agent: MEDIA + "tour-agent-en.mp4",
  agentPoster: MEDIA + "tour-agent-poster.jpg",
  /** ISO 8601, pour le balisage VideoObject. */
  tourDuration: "PT1M49S",
  agentDuration: "PT21S",
  uploadDate: "2026-11-10",
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
    sub: "Why we score data centers, and how — 1:49.",
    ficheLink: "New here? Take the 2-minute tour",
    close: "Close",
    play: "Play the 2-minute tour",
    agentH2: "Who does the work: AI agents read, a human checks",
    agentLead: "Rating thousands of sites one by one is no job for a human team alone. Here is how the work is split — told by one of the agents.",
    ldName: "ScoreMyDataCenter — the 2-minute tour",
    ldDescription: "Why an independent A–E score for data centers, and how it works: the map, a project fiche, its satellite view and the questions a mayor or a resident can ask.",
    ldAgentName: "How ScoreMyDataCenter works: AI agents read, a human checks",
    ldAgentDescription: "Collector agents crawl public registries, a reader agent parses permits and filings, a verifier rejects anything implausible, and a human runs the final gate.",
  },
  fr: {
    cta: "La visite en 2 minutes",
    sub: "Pourquoi et comment nous notons les data centers — 1:49, en anglais sous-titré.",
    ficheLink: "Nouveau ici ? La visite en 2 minutes",
    close: "Fermer",
    play: "Lancer la visite en 2 minutes",
    agentH2: "Qui fait le travail : des agents IA lisent, un humain vérifie",
    agentLead: "Noter des milliers de sites un par un n'est pas à la portée d'une équipe humaine seule. Voici comment le travail est réparti — raconté par l'un des agents (en anglais sous-titré).",
    ldName: "ScoreMyDataCenter — la visite en 2 minutes",
    ldDescription: "Pourquoi une note A–E indépendante des data centers, et comment elle fonctionne : la carte, une fiche projet, sa vue satellite et les questions qu'un élu ou un riverain peut poser.",
    ldAgentName: "Comment travaille ScoreMyDataCenter : des agents IA lisent, un humain vérifie",
    ldAgentDescription: "Des agents collecteurs parcourent les registres publics, un agent lecteur dépouille permis et dossiers, un vérificateur rejette l'invraisemblable, et un humain tient la dernière porte.",
  },
  nl: {
    cta: "De rondleiding in 2 minuten",
    sub: "Waarom en hoe we datacenters een score geven — 1:49, in het Engels ondertiteld.",
    ficheLink: "Nieuw hier? Bekijk de rondleiding van 2 minuten",
    close: "Sluiten",
    play: "Start de rondleiding van 2 minuten",
    agentH2: "Wie doet het werk: AI-agenten lezen, een mens controleert",
    agentLead: "Duizenden locaties één voor één beoordelen is geen werk voor een menselijk team alleen. Zo is het werk verdeeld — verteld door een van de agenten (in het Engels ondertiteld).",
    ldName: "ScoreMyDataCenter — de rondleiding in 2 minuten",
    ldDescription: "Waarom een onafhankelijke A–E-score voor datacenters, en hoe die werkt: de kaart, een projectfiche, het satellietbeeld en de vragen die een bestuurder of omwonende kan stellen.",
    ldAgentName: "Hoe ScoreMyDataCenter werkt: AI-agenten lezen, een mens controleert",
    ldAgentDescription: "Verzamelagenten doorzoeken openbare registers, een leesagent ontleedt vergunningen en dossiers, een controleur weigert het onwaarschijnlijke, en een mens bewaakt de laatste poort.",
  },
};
