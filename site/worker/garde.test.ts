// SPDX-License-Identifier: AGPL-3.0-or-later
// Garde anti-aspiration — `node --test site/worker/garde.test.ts` (aussi lancé par
// engine/tests/test_garde_worker.py, donc par `make test` avant chaque déploiement).
import { test } from "node:test";
import assert from "node:assert/strict";
import { ETAT_VIDE, HEURE, JOUR, MINUTE, budgetDe, decider, dureeBlocage, moteurVerifie, type Etat } from "./garde.ts";

function serie(n: number, budget: "fiche" | "carte", depart: number, pas: number, etat: Etat = ETAT_VIDE) {
  let e = etat;
  const verdicts = [];
  for (let i = 0; i < n; i++) {
    const v = decider(e, budget, depart + i * pas);
    e = v.etat;
    verdicts.push(v.ok);
  }
  return { e, verdicts };
}

test("un lecteur ordinaire (15 fiches dans l'heure) ne voit jamais le mur", () => {
  const { verdicts } = serie(15, "fiche", 0, 3 * MINUTE);
  assert.ok(verdicts.every(Boolean));
});

test("la 21e fiche de l'heure est refusée, 30 minutes", () => {
  const { e, verdicts } = serie(20, "fiche", 0, 10_000);
  assert.ok(verdicts.every(Boolean));
  const v = decider(e, "fiche", 20 * 10_000);
  assert.equal(v.ok, false);
  assert.equal(!v.ok && v.reessayerDans, 30 * MINUTE);
});

test("la 51e fiche de la journée est refusée même à rythme lent", () => {
  const { e, verdicts } = serie(50, "fiche", 0, 4 * MINUTE); // 15/h, 50 en 3 h 20
  assert.ok(verdicts.every(Boolean));
  assert.equal(decider(e, "fiche", 50 * 4 * MINUTE).ok, false);
});

test("le blocage double à chaque récidive, plafonné à 7 jours", () => {
  assert.deepEqual([1, 2, 3, 4, 5].map(dureeBlocage), [30, 60, 120, 240, 480].map((m) => m * MINUTE));
  assert.equal(dureeBlocage(30), 7 * JOUR);
  // L'aspirateur qui revient dès la levée du blocage récidive aussitôt (quota du jour plein).
  // 50 fiches à 15/h (sous le plafond horaire) : le quota du JOUR est plein, sans récidive.
  let { e, verdicts } = serie(50, "fiche", 0, 4 * MINUTE);
  assert.ok(verdicts.every(Boolean));
  let t = 50 * 4 * MINUTE;
  const durees = [];
  for (let i = 0; i < 4; i++) {
    const v = decider(e, "fiche", t);
    assert.equal(v.ok, false);
    if (!v.ok) { durees.push(v.reessayerDans); t += v.reessayerDans; }
    e = v.etat;
  }
  assert.deepEqual(durees, [30, 60, 120, 240].map((m) => m * MINUTE));
});

test("pendant un blocage, chaque requête est refusée sans l'allonger", () => {
  const { e } = serie(21, "fiche", 0, 1000);
  const v1 = decider(e, "fiche", 25_000);
  const v2 = decider(v1.etat, "fiche", 26_000);
  assert.equal(v2.ok, false);
  assert.equal(v2.etat.recidives, 1);
});

test("7 jours sans récidive remettent le compteur à zéro", () => {
  const { e } = serie(21, "fiche", 0, 1000); // récidive 1
  const v = decider(e, "fiche", 8 * JOUR);
  assert.equal(v.ok, true);
  assert.equal(v.etat.recidives, 0);
});

test("la carte a son propre budget : cliquer 40 marqueurs ne bloque pas les fiches", () => {
  let { e, verdicts } = serie(40, "carte", 0, 30_000);
  assert.ok(verdicts.every(Boolean));
  assert.equal(decider(e, "fiche", 40 * 30_000).ok, true);
  ({ e } = serie(60, "carte", HEURE * 2, 1000));
  assert.equal(decider(e, "carte", HEURE * 2 + 61_000).ok, false);
});

test("seules les fiches et le détail carte sont comptés", () => {
  assert.equal(budgetDe("GET", "/fr/dc/fr-data4-campus-paris-saclay/"), "fiche");
  assert.equal(budgetDe("GET", "/dc/us-sharka/"), "fiche");
  assert.equal(budgetDe("GET", "/nl/dc/nl-ecoracks/portrait/"), "fiche");
  assert.equal(budgetDe("GET", "/api/carte/site"), "carte");
  assert.equal(budgetDe("GET", "/api/veille/site/"), "carte");
  for (const p of ["/", "/fr/", "/fr/carte/", "/fr/methodologie/", "/fr/dc/", "/api/carte/voisins", "/fr/dc/x"]) {
    assert.equal(budgetDe("GET", p), null, p);
  }
  assert.equal(budgetDe("HEAD", "/fr/dc/x/"), null);
});

test("un moteur se prouve, il ne se déclare pas", () => {
  assert.ok(moteurVerifie("Mozilla/5.0 (compatible; Googlebot/2.1)", { asn: 15169 }));
  assert.ok(moteurVerifie("bingbot/2.0", { asn: 8075 }));
  assert.ok(moteurVerifie("x", { verifiedBotCategory: "Search Engine Crawler" }));
  assert.equal(moteurVerifie("Mozilla/5.0 (compatible; Googlebot/2.1)", { asn: 14061 }), false);
  assert.equal(moteurVerifie("python-requests/2.31", { asn: 15169 }), false);
});
