// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
// https://scoremydatacenter.org · independent data center acceptability-risk score
//
// Un Durable Object PAR IP (idFromName(ip)) : le seul endroit où un compteur par IP est
// exact. Le cache ou KV ne le sont pas (KV : écritures limitées, cohérence à terme — deux
// requêtes simultanées compteraient pour une). L'état tient en quelques centaines
// d'horodatages ; la décision est dans garde.ts (pure, testée).
import { DurableObject } from "cloudflare:workers";
import { ETAT_VIDE, decider, type Etat } from "./garde";

export class GardeIp extends DurableObject {
  async verifier(budget: "fiche" | "carte", maintenant: number): Promise<{ ok: boolean; reessayerDans: number }> {
    const etat = (await this.ctx.storage.get<Etat>("e")) ?? ETAT_VIDE;
    const v = decider(etat, budget, maintenant);
    await this.ctx.storage.put("e", v.etat);
    return { ok: v.ok, reessayerDans: v.ok ? 0 : v.reessayerDans };
  }
}
