// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Le portrait d'un site : la page qui raconte ce que la fiche mesure — UNE SEULE FOIS, un bloc par langue (i18n §13 : un gabarit, un objet `t` par
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
  tagline: "Observatoire indépendant",
  kicker: "Portrait du site",
  // L'angle du titre (voir SitePortrait.astro) : trois mots qui disent ce que la page tient
  // vraiment, et dont le premier est un terme mesuré que nous ne portions nulle part.
  seoAngle: "bruit, eau, terrain",
  metaDescription: "{name}, {place} : le bruit en continu, l'eau, le terrain, et ce que le projet change pour la commune. Ce qu'il reste à faire écrire dans l'autorisation, et jusqu'à quand.",
  status: { announced: "annoncé", permitting: "en instruction", under_construction: "en chantier", operational: "en service", unknown: "non établi" },
  siteGrade: "Note du site",
  probable: "note probable",
  probableWindow: "note probable · fenêtre {w}",
  definitive: "note définitive",
  leadHelp: "Cette page dit la même chose que la fiche technique, dans l'ordre d'une décision à prendre : ce qui pèse, ce qui manque, et ce qu'il reste à demander pendant que c'est encore possible.",
  photoAlt: "Vue aérienne annotée de {name} : emprise, cours d'eau et distances",
  photoHint: "Survolez pour agrandir · cliquez pour l'image entière",
  photoOpen: "Ouvrir la vue aérienne en grand",
  pillarsTitle: "Les cinq piliers de la note",
  ofMeasures: "{n} mesure(s) sur {total}",
  pillarsNote: "Un pilier qui ne porte pas de lettre repose sur trop peu de mesures pour en défendre une. Nous publions le compte plutôt qu'une lettre indéfendable.",
  decisiveTitle: "Les points qui décideront",
  streetTitle: "Ce qui se vit depuis la rue",
  noiseTitle: "Le bruit — continu, jour et nuit",
  noiseBody: "Le refroidissement tourne en permanence et les groupes de secours sont testés régulièrement. Ce qui est encadré n'est pas une distance mais de combien le bruit monte chez le voisin.",
  noiseDistance: "La première habitation recensée est à {m} m du point de référence. C'est une distance à vol d'oiseau, jamais une mesure de bruit : l'étude acoustique du dossier reste à exiger, c'est elle qui fixe les valeurs opposables.",
  noiseNoDistance: "Nous n'avons ni distance à la première habitation, ni étude acoustique pour ce site. Les deux s'obtiennent : l'étude est une pièce du dossier.",
  fuelTitle: "Les groupes électrogènes et leur carburant",
  fuelBody: "Un site de cette nature garde des groupes de secours et les cuves qui les alimentent. Ce sont eux qu'on teste, qu'on sent, et qui déclenchent un encadrement propre. Leur nombre, leur carburant et le volume stocké figurent au dossier quand il existe.",
  healthDisclaimer: "Nous ne mesurons aucun effet sur la santé et nous ne prétendons pas le faire. Nous publions ce qui figure au dossier, et ce qui n'y figure pas.",
  unknownTitle: "Ce que nous n'avons pas mesuré",
  unknownNone: "Toutes les mesures de base de ce site sont renseignées.",
  verifiedAbsent: "vérifié absent du dossier lu",
  notCollected: "pas encore collecté par nous",
  unknownNote: "Ces manques sont les nôtres, pas ceux du porteur : ils disent où notre mesure s'arrête, et ils ne pénalisent pas le site.",
  procedureTitle: "Où en est la procédure",
  writeInTitle: "À faire écrire dans l'autorisation",
  writeInNote: "Les engagements qui ne figurent pas dans l'arrêté ne sont pas opposables : ce qui n'est pas écrit ne pourra pas être exigé plus tard.",
  technicalSheet: "Fiche technique du projet",
  technicalSheetSub: "les indicateurs un par un, leurs valeurs et leurs sources",
  print: "Imprimer",
  share: "Partager",
  shareMail: "Par courriel",
  copyLink: "Copier le lien",
  signal: "Signaler une erreur",
  signalSubject: "Correction ou réponse — portrait du site",
  howToRead: "Comment lire ce portrait. La lettre résume cinq piliers — énergie, eau, foncier, impact local, transparence. Chaque fait vient d'une source publique, citée sur la fiche technique.",
  sourcesOn: "Indicateurs, valeurs et sources :",
};

const EN: typeof FR = {
  tagline: "Independent observatory",
  kicker: "Site portrait",
  // See fr/dc/[id]/portrait.astro: the title angle, led by a measured term.
  seoAngle: "noise, water, land",
  metaDescription: "{name}, {place}: how loud, how close, the water, the land, and what the project changes for the community. What to get written into the permit, and until when.",
  status: { announced: "announced", permitting: "under review", under_construction: "under construction", operational: "operating", unknown: "not established" },
  siteGrade: "Site grade",
  probable: "probable grade",
  probableWindow: "probable grade · window {w}",
  definitive: "settled grade",
  leadHelp: "This page says the same thing as the technical sheet, in the order of a decision to take: what weighs, what is missing, and what is still worth asking for while it can still be asked.",
  photoAlt: "Annotated aerial view of {name}: footprint, watercourse and distances",
  photoHint: "Hover to magnify · click for the full image",
  photoOpen: "Open the aerial view full size",
  pillarsTitle: "The five pillars behind the grade",
  ofMeasures: "{n} of {total} measures",
  pillarsNote: "A pillar with no letter rests on too few measures to defend one. We publish the count rather than a letter we could not stand behind.",
  decisiveTitle: "The points that will decide",
  streetTitle: "What this looks like from the street",
  noiseTitle: "Noise — continuous, day and night",
  noiseBody: "Cooling runs permanently and standby generators are tested on a schedule. What is regulated is not a distance but how far the noise rises at the neighbour's.",
  noiseDistance: "The nearest recorded dwelling is {m} m from the reference point. That is a straight-line distance, never a noise measurement: the acoustic study in the file is still to be demanded — it is the one that sets enforceable values.",
  noiseNoDistance: "We hold neither a nearest-dwelling distance nor an acoustic study for this site. Both are obtainable: the study is a document in the file.",
  fuelTitle: "Standby generators and their fuel",
  fuelBody: "A facility like this keeps standby generators and the tanks that feed them. They are what gets tested, what gets smelled, and what triggers its own permitting. Their number, their fuel and the volume stored are in the file where one exists.",
  healthDisclaimer: "We measure no health effect and we do not claim to. We publish what is in the file, and what is not.",
  unknownTitle: "What we have not measured",
  unknownNone: "Every base measure for this site is filled in.",
  verifiedAbsent: "verified absent from the file we read",
  notCollected: "not yet collected by us",
  unknownNote: "These gaps are ours, not the developer's: they say where our measurement stops, and they do not penalise the site.",
  procedureTitle: "Where the procedure stands",
  writeInTitle: "What to get written into the approval",
  writeInNote: "Commitments that are not in the approval cannot be enforced: what is not written cannot be demanded later.",
  technicalSheet: "Technical sheet",
  technicalSheetSub: "the measures one by one, their values and their sources",
  print: "Print",
  share: "Share",
  shareMail: "By email",
  copyLink: "Copy the link",
  signal: "Report an error",
  signalSubject: "Correction or response — site portrait",
  howToRead: "How to read this portrait. The letter summarises five pillars — energy, water, land, local impact, openness. Every fact comes from a public source, cited on the technical sheet.",
  sourcesOn: "Measures, values and sources:",
};


// ── NÉERLANDAIS — EN PRÉPARATION, PAS ENCORE SERVI (voir `content/langues.ts`).
// ⚠️ Les valeurs ci-dessous sont encore LE TEXTE FRANÇAIS, copié tel quel. Elles sont là
// pour qu'un traducteur natif ait la source sous les yeux, à sa place dans la structure.
// Elles NE DOIVENT PAS partir en ligne : `nl` n'est pas dans `LANGUES_VIVANTES`, et
// `test_une_langue_ne_devient_vivante_que_traduite` refuse de l'y faire entrer tant que
// ses valeurs sont celles du français.
const NL: typeof FR = {
  tagline: "Onafhankelijk observatorium",
  kicker: "Portret van de site",
  // L'angle du titre : trois mots mesurés (cf. SitePortrait.astro).
  seoAngle: "geluid, water, grond",
  metaDescription: "{name}, {place}: het continue geluid, het water, de grond, en wat het project verandert voor de gemeente. Wat er nog in de vergunning moet komen, en tot wanneer.",
  status: { announced: "aangekondigd", permitting: "in behandeling", under_construction: "in aanbouw", operational: "in bedrijf", unknown: "niet vastgesteld" },
  siteGrade: "Cijfer van de site",
  probable: "waarschijnlijk cijfer",
  probableWindow: "waarschijnlijk cijfer · venster {w}",
  definitive: "definitief cijfer",
  leadHelp: "Deze pagina zegt hetzelfde als de technische fiche, in de volgorde van een beslissing die genomen moet worden: wat weegt, wat ontbreekt, en wat er nog te vragen valt zolang het nog kan.",
  photoAlt: "Geannoteerd luchtbeeld van {name}: terreinomtrek, waterloop en afstanden",
  photoHint: "Beweeg eroverheen om te vergroten · klik voor het volledige beeld",
  photoOpen: "Open het luchtbeeld op volle grootte",
  pillarsTitle: "De vijf pijlers achter het cijfer",
  ofMeasures: "{n} van de {total} metingen",
  pillarsNote: "Een pijler zonder letter steunt op te weinig metingen om er één te verdedigen. We publiceren het aantal in plaats van een letter die we niet kunnen waarmaken.",
  decisiveTitle: "De punten die de doorslag geven",
  streetTitle: "Hoe dit eruitziet vanaf de straat",
  noiseTitle: "Geluid — continu, dag en nacht",
  noiseBody: "De koeling draait permanent en de noodaggregaten worden volgens schema getest. Wat gereglementeerd is, is geen afstand maar hoeveel het geluid bij de buren stijgt.",
  noiseDistance: "De dichtstbijzijnde geregistreerde woning staat op {m} m van het referentiepunt. Dat is een afstand in vogelvlucht, nooit een geluidsmeting: het akoestisch onderzoek uit het dossier moet nog worden opgeëist — dát legt de afdwingbare waarden vast.",
  noiseNoDistance: "We hebben voor deze site geen afstand tot de dichtstbijzijnde woning en geen akoestisch onderzoek. Beide zijn te verkrijgen: het onderzoek is een stuk uit het dossier.",
  fuelTitle: "De noodaggregaten en hun brandstof",
  fuelBody: "Een site als deze houdt noodaggregaten aan, en de tanks die ze voeden. Zíj zijn het die getest worden, die je ruikt, en die hun eigen regels meebrengen. Hun aantal, hun brandstof en het opgeslagen volume staan in het dossier, waar dat bestaat.",
  healthDisclaimer: "We meten geen enkel gezondheidseffect en we beweren niet dat we dat doen. We publiceren wat in het dossier staat, en wat er niet in staat.",
  unknownTitle: "Wat we niet hebben gemeten",
  unknownNone: "Alle basismetingen van deze site zijn ingevuld.",
  verifiedAbsent: "geverifieerd afwezig in het gelezen dossier",
  notCollected: "nog niet door ons verzameld",
  unknownNote: "Deze gaten zijn de onze, niet die van de initiatiefnemer: ze zeggen waar onze meting ophoudt, en ze benadelen de site niet.",
  procedureTitle: "Waar de procedure staat",
  writeInTitle: "Wat in de vergunning moet komen",
  writeInNote: "Toezeggingen die niet in het besluit staan, zijn niet afdwingbaar: wat niet geschreven is, kan later niet worden geëist.",
  technicalSheet: "Technische fiche van het project",
  technicalSheetSub: "de indicatoren één voor één, hun waarden en hun bronnen",
  print: "Afdrukken",
  share: "Delen",
  shareMail: "Per e-mail",
  copyLink: "Link kopiëren",
  signal: "Een fout melden",
  signalSubject: "Correctie of reactie — portret van de site",
  howToRead: "Hoe u dit portret leest. De letter vat vijf pijlers samen — energie, water, bodem, lokale impact, transparantie. Elk feit komt uit een publieke bron, geciteerd op de technische fiche.",
  sourcesOn: "Indicatoren, waarden en bronnen:",
};

/** La table servie au gabarit : `PORTRAIT[lang]`. */
export const PORTRAIT: Record<LangueDeclaree, typeof FR> = { fr: FR, en: EN, nl: NL };
