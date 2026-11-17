// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
// Routeur Worker : rejoue ce que faisait Cloudflare Pages Functions, SANS toucher aux
// handlers de functions/. Les deux hébergements coexistent jusqu'à la bascule : un seul
// jeu de handlers, deux façons de les servir.
//
// CE QUE PAGES FAISAIT (mesuré sur `wrangler pages dev`, pas deviné) :
//  - correspondance sur le chemin, insensible à la casse et à UNE barre finale
//    (/api/carte/site, /api/carte/site/ et /API/carte/site servent le handler) ;
//  - correspondance sur la MÉTHODE exacte : HEAD ne tombe pas dans onRequestGet ;
//  - tout ce qui ne correspond à aucune route (chemin inconnu, méthode sans handler) est
//    renvoyé au serveur de fichiers statiques via next() — d'où le 404.html pour
//    GET /api/nope et le 405 vide d'un POST sur une route GET.
// Ici ce `next()` est env.ASSETS.fetch(request).
//
// 🔴 LA REDIRECTION DE BARRE FINALE RESTE PERMANENTE. Pages répond 308 à /fr/dc/x (→ /fr/dc/x/),
// la couche de fichiers d'un Worker répond 307, sans réglage possible. Une 307 dit aux
// moteurs « provisoire, gardez l'ancienne adresse ». wrangler.worker.jsonc fait donc passer
// par ici les adresses sans barre ni extension, et `fichiers()` relaie leur 307 en 308.
// Nos propres redirections (`_redirects`) sont toutes en 301 : toute 307 venue des fichiers
// est une redirection de forme d'adresse.

import * as classement from "../functions/api/classement";
import * as carteRecherche from "../functions/api/carte/recherche";
import * as carteSite from "../functions/api/carte/site";
import * as carteVoisins from "../functions/api/carte/voisins";
import * as veilleSite from "../functions/api/veille/site";
import * as reportConfirm from "../functions/api/report/confirm";
import * as reportDownload from "../functions/api/report/download";
import * as reportSubscribe from "../functions/api/report/subscribe";
import * as reportUnsubscribe from "../functions/api/report/unsubscribe";

type Env = {
  ASSETS: Fetcher;
  DB: D1Database;
  REPORTS_BUCKET: R2Bucket;
  RESEND_API_KEY: string;
};

// Contexte identique à celui de Pages (EventContext), pour que les handlers n'y voient rien.
type Ctx = {
  request: Request;
  functionPath: string;
  waitUntil: (p: Promise<unknown>) => void;
  passThroughOnException: () => void;
  next: (input?: Request | string, init?: RequestInit) => Promise<Response>;
  env: Env;
  params: Record<string, string | string[]>;
  data: Record<string, unknown>;
};
type Handler = (ctx: Ctx) => Response | Promise<Response>;
type Methods = { onRequestGet?: unknown; onRequestPost?: unknown };

// Table statique chemin → handlers. Les chemins sont ceux de functions/, sans barre finale.
const ROUTES: Record<string, Methods> = {
  "/api/classement": classement,
  "/api/carte/recherche": carteRecherche,
  "/api/carte/site": carteSite,
  "/api/carte/voisins": carteVoisins,
  "/api/veille/site": veilleSite,
  "/api/report/confirm": reportConfirm,
  "/api/report/download": reportDownload,
  "/api/report/subscribe": reportSubscribe,
  "/api/report/unsubscribe": reportUnsubscribe,
};

const METHODES: Record<string, keyof Methods> = { GET: "onRequestGet", POST: "onRequestPost" };

async function fichiers(env: Env, request: Request): Promise<Response> {
  const r = await env.ASSETS.fetch(request);
  if (r.status !== 307) return r;
  return new Response(null, { status: 308, headers: r.headers });
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const { pathname } = new URL(request.url);
    // Pages : casse ignorée, une barre finale tolérée, pas plus.
    const cle = pathname.toLowerCase().replace(/(?<=.)\/$/, "");
    const handler = ROUTES[cle]?.[METHODES[request.method]] as Handler | undefined;

    // Pas de route pour ce couple chemin+méthode → fichiers statiques, comme next() sous Pages.
    if (!handler) return fichiers(env, request);

    return handler({
      request,
      functionPath: cle,
      waitUntil: (p) => ctx.waitUntil(p),
      passThroughOnException: () => ctx.passThroughOnException(),
      next: (input, init) => env.ASSETS.fetch(input ?? request, init),
      env,
      params: {},
      data: {},
    });
  },
};
