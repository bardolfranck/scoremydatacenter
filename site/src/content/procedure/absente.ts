// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// CE QU'ON ÉCRIT QUAND ON N'A PAS LU LA JURIDICTION.
//
// 🔴 « À déterminer » est un aveu, pas une information. Ça dit au lecteur que NOUS avons un
// travail en retard — ce qui ne l'avance en rien, et ce qui, pire, laisse croire qu'il n'y a
// rien à faire tant que nous n'aurons pas fini. C'est faux : il reste beaucoup de vrai à dire
// sans avoir lu l'article.
//
// La règle : un trou se remplit par CE QU'ON SAIT QUAND MÊME, et par la question que le
// lecteur peut poser à notre place. Trois couches :
//   1. LE CADRE — qui décide. Vrai par construction du pays, pas par lecture du texte.
//      « Aux États-Unis, c'est la commune ou le comté qui autorise » ne demande aucun article.
//   2. LE LEVIER QUI EXISTE PARTOUT — les cinquante États ont une loi d'accès aux documents,
//      les vingt-sept de l'Union ont le socle des directives. Le levier est certain ; seul son
//      délai manque.
//   3. LA QUESTION RETOURNÉE — au lieu de taire le chiffre, on apprend au lecteur à l'exiger :
//      « demandez le document ET le délai légal dans la même lettre ». Notre lacune devient sa
//      première question, et l'administration est tenue de répondre aux deux.
//
// Même doctrine que la note creuse et que « l'absence ressemble à zéro » : on publie ce qu'on
// sait, on nomme ce qu'on ignore, et on ne laisse jamais un blanc se lire comme un néant.

import type { Prose } from "./types";

export interface ProcedureAbsente {
  /** Ce qui reste vrai sans avoir lu le texte. */
  cadre: Prose;
  /** Le levier dont l'existence est certaine, délai mis à part. */
  levier: Prose;
  /** La question que le lecteur pose à notre place. */
  question: Prose;
}

const ETATS_UNIS: ProcedureAbsente = {
  cadre: {
    fr: "Aucun permis fédéral ne porte sur un data center : c'est la commune ou le comté qui zone le terrain qui autorise. C'est vrai dans les cinquante États, et c'est là que se prennent les décisions qui comptent.",
    en: "No federal permit covers a data centre: the town or county that zones the land is the one that authorises it. That holds in all fifty states, and that is where the decisions that matter are taken.",
    nl: "Geen enkele federale vergunning dekt een datacenter: de toestemming komt van de gemeente of de county die de bestemming van de grond bepaalt. Dat geldt in alle vijftig staten, en daar vallen de beslissingen die ertoe doen.",
  },
  levier: {
    fr: "Chaque État a une loi d'accès aux documents publics. Elle vous donne le droit d'exiger par écrit l'étude d'impact, la demande d'aide fiscale, l'étude acoustique — tout ce que détient la commune, le comté ou l'agence de développement.",
    en: "Every state has a public-records law. It gives you the right to demand, in writing, the impact study, the tax-assistance application, the acoustic study — anything held by the town, the county or the development agency.",
    nl: "Elke staat heeft een openbaarheidswet. Die geeft u het recht om schriftelijk het milieueffectrapport, de aanvraag voor belastingvoordeel, het akoestisch onderzoek op te eisen — alles wat de gemeente, de county of het ontwikkelingsagentschap in handen heeft.",
  },
  question: {
    fr: "Nous n'avons pas encore lu le délai de réponse propre à cet État : il va de trois jours ouvrés dans certains à trente dans d'autres, et cinq États n'en fixent aucun. Posez donc les deux questions dans la même lettre — le document, et sous quel délai la loi de l'État oblige à répondre. L'administration doit répondre aux deux.",
    en: "We have not yet read this state's own response deadline: it runs from three business days in some to thirty in others, and five states set none at all. So ask both questions in the same letter — the record, and the deadline the state's law imposes. The agency owes you an answer on both.",
    nl: "De antwoordtermijn van deze staat hebben we nog niet gelezen: hij loopt van drie werkdagen in de ene staat tot dertig in de andere, en vijf staten leggen er geen vast. Stel de twee vragen daarom in dezelfde brief — het document, én binnen welke termijn de wet van de staat tot een antwoord verplicht. De overheid moet ze alle twee beantwoorden.",
  },
};

const UNION_EUROPEENNE: ProcedureAbsente = {
  cadre: {
    fr: "L'autorisation est délivrée par l'autorité désignée par ce pays — le plus souvent la commune pour l'urbanisme, une autorité régionale ou nationale pour l'environnement.",
    en: "The permit is issued by the authority this country designates — usually the municipality for planning, a regional or national authority for the environment.",
    nl: "De vergunning wordt verleend door de autoriteit die dit land daarvoor heeft aangewezen — meestal de gemeente voor de ruimtelijke ordening, een regionale of nationale autoriteit voor het milieu.",
  },
  levier: {
    fr: "Le socle européen s'applique quoi qu'il arrive : au moins trente jours pour se prononcer sur l'étude d'impact, publication de la décision ET de ses motifs, accès au juge, et toute information environnementale communicable sur demande sous un mois.",
    en: "The European floor applies regardless: at least thirty days to comment on the impact assessment, publication of the decision AND its reasons, access to a court, and any environmental information available on request within one month.",
    nl: "De Europese ondergrens geldt hoe dan ook: ten minste dertig dagen om zich over het milieueffectrapport uit te spreken, publicatie van het besluit ÉN van de motivering, toegang tot de rechter, en alle milieu-informatie op verzoek binnen een maand.",
  },
  question: {
    fr: "Ce que nous n'avons pas encore lu, c'est le délai national de recours — celui qui, une fois l'autorisation délivrée, ne se rattrape pas. Aucune directive ne le fixe : il va de trois semaines en Suède à deux mois en France et en Espagne. Demandez-le à l'autorité qui délivre l'autorisation, et faites-le avant qu'elle ne la délivre.",
    en: "What we have not yet read is the national appeal deadline — the one that, once the permit is granted, does not come back. No directive sets it: it runs from three weeks in Sweden to two months in France and Spain. Ask the issuing authority for it, and ask before they grant.",
    nl: "Wat we nog niet hebben gelezen, is de nationale beroepstermijn — de termijn die, zodra de vergunning is verleend, niet meer in te halen is. Geen enkele richtlijn legt hem vast: hij loopt van drie weken in Zweden tot twee maanden in Frankrijk en Spanje. Vraag hem op bij de autoriteit die de vergunning verleent — en doe dat vóór ze haar verleent.",
  },
};

const HORS_SOCLE: ProcedureAbsente = {
  cadre: {
    fr: "L'autorisation relève du droit de ce pays, que nous n'avons pas encore lu.",
    en: "The permit falls under this country's own law, which we have not yet read.",
    nl: "De vergunning valt onder het recht van dit land, dat we nog niet hebben gelezen.",
  },
  levier: {
    fr: "Les indicateurs de la fiche technique, eux, sont mesurés de la même façon partout : ils se comparent à n'importe quel autre site du corpus, quel que soit le droit applicable.",
    en: "The measures on the technical sheet, however, are taken the same way everywhere: they compare with any other site in the corpus, whatever law applies.",
    nl: "De indicatoren van de technische fiche worden daarentegen overal op dezelfde manier gemeten: ze laten zich vergelijken met elke andere site in het corpus, welk recht er ook geldt.",
  },
  question: {
    fr: "Demandez à l'autorité qui instruit le dossier deux choses : où le dossier est consultable, et jusqu'à quelle date une observation peut y être versée.",
    en: "Ask the authority handling the file two things: where the file can be consulted, and until when an observation can be added to it.",
    nl: "Vraag de autoriteit die het dossier behandelt twee dingen: waar het dossier in te zien is, en tot welke datum een opmerking erin kan worden ingebracht.",
  },
};

/**
 * Le message à servir quand `resolveProcedure` ne rend rien. Jamais vide, jamais un
 * « à déterminer » : le cadre reste vrai, le levier reste certain, et la question se pose.
 */
export function procedureAbsente(country: string | null | undefined): ProcedureAbsente {
  if (country === "US") return ETATS_UNIS;
  const UE = new Set(["FR", "DE", "NL", "ES", "IT", "PL", "SE", "DK", "FI", "BE",
                      "IE", "LU", "PT", "AT", "GB"]);
  // Le Royaume-Uni n'est plus membre, mais sa loi d'urbanisme et son règlement
  // d'information environnementale portent encore le même socle : le lecteur y retrouve les
  // mêmes leviers, et c'est de cela qu'on lui parle, pas d'appartenance.
  return UE.has(country ?? "") ? UNION_EUROPEENNE : HORS_SOCLE;
}
