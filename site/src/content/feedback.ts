// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Le bandeau « votre avis » — un bloc par langue (i18n §13).
//
// 🔴 Sa copie vivait dans un TERNAIRE du composant, et ce composant sert DEUX surfaces :
// l'accueil et la revue de la bibliothèque. Une langue nouvelle aurait eu à l'insérer dans
// une expression, au milieu d'un formulaire, au lieu de la déclarer dans une table.
//
// ⚠️ CE BANDEAU EST UN FORMULAIRE PUBLIC : ses libellés de consentement engagent. La phrase
// de consentement a un jumeau côté valeur envoyée (`CONSENT_VALUE` dans le composant) —
// traduire l'un sans l'autre enverrait un consentement qui ne dit pas ce que la case dit.
//
// 🔴 Le type ne garde RIEN au build (`astro build` sans `astro check`) : le garde qui mord
// est `engine/tests/test_i18n_parity.py`.

import type { Langue, LangueDeclaree } from "./langues";

const FR = {
  kicker: "Votre avis",
  title: "Notre travail vous est utile ? Dites-le. Il manque quelque chose ? Dites-le aussi.",
  usefulLabel: "Qu'est-ce qui vous est utile dans ScoreMyDataCenter ?",
  usefulHint: "La carte, une note, la méthode, un rapport… dites-le avec vos mots.",
  missingLabel: "Et qu'est-ce qui vous manque ?",
  missingHint: "facultatif",
  nameLabel: "Votre nom et votre fonction",
  namePlaceholder: "Ex. : Marie Dupont, élue municipale",
  consentLabel: "J'accepte que ce témoignage soit publié avec mon nom et ma fonction.",
  consentNote: "Sans cette case, votre message nous parvient quand même — il reste privé.",
  submit: "Envoyer",
  thanks: "Merci ! Votre avis est bien parti — nous lisons tout.",
  error: "L'envoi a échoué. Réessayez, ou écrivez-nous : contact@scoremydatacenter.org",
};

const EN: typeof FR = {
  kicker: "Your feedback",
  title: "Is our work useful to you? Say it. Is something missing? Say that too.",
  usefulLabel: "What do you find useful in ScoreMyDataCenter?",
  usefulHint: "The map, a grade, the method, a report… in your own words.",
  missingLabel: "And what's missing?",
  missingHint: "optional",
  nameLabel: "Your name and role",
  namePlaceholder: "E.g.: Marie Dupont, city councillor",
  consentLabel: "I agree that this testimonial may be published with my name and role.",
  consentNote: "Without this box your message still reaches us — it just stays private.",
  submit: "Send",
  thanks: "Thank you! Your feedback is on its way — we read everything.",
  error: "Sending failed. Try again, or write to us: contact@scoremydatacenter.org",
};


// ── NÉERLANDAIS — EN PRÉPARATION, PAS ENCORE SERVI (voir `content/langues.ts`).
// ⚠️ Les valeurs ci-dessous sont encore LE TEXTE FRANÇAIS, copié tel quel. Elles sont là
// pour qu'un traducteur natif ait la source sous les yeux, à sa place dans la structure.
// Elles NE DOIVENT PAS partir en ligne : `nl` n'est pas dans `LANGUES_VIVANTES`, et
// `test_une_langue_ne_devient_vivante_que_traduite` refuse de l'y faire entrer tant que
// ses valeurs sont celles du français.
const NL: typeof FR = {
  kicker: "Uw mening",
  title: "Is ons werk u van nut? Zeg het. Ontbreekt er iets? Zeg het ook.",
  usefulLabel: "Wat heeft u aan ScoreMyDataCenter?",
  usefulHint: "De kaart, een cijfer, de methode, een rapport… zeg het in uw eigen woorden.",
  missingLabel: "En wat mist u?",
  missingHint: "optioneel",
  nameLabel: "Uw naam en functie",
  namePlaceholder: "Bijv.: Anna de Vries, gemeenteraadslid",
  consentLabel: "Ik ga ermee akkoord dat deze reactie met mijn naam en functie wordt gepubliceerd.",
  consentNote: "Zonder dit vinkje bereikt uw bericht ons ook — het blijft dan privé.",
  submit: "Versturen",
  thanks: "Dank u! Uw bericht is verzonden — we lezen alles.",
  error: "Versturen is mislukt. Probeer het opnieuw, of schrijf ons: contact@scoremydatacenter.org",
};

/** La copie du bandeau d'avis : `FEEDBACK[lang]`. */
export const FEEDBACK: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
