# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Sweden — the shared EU factory + Svenska kraftnät's county capacity map (E2/E3) + income.

The clean-grid end of the spectrum: E1 ~23 gCO2/kWh (hydro + nuclear) — the opposite of Poland;
cheap green power + cold climate is why the hyperscalers went north (Meta Luleå, AWS eu-north-1).
The national deepening is Svenska kraftnät's `kapacitetskartan`: a keyless per-county (län) feed of
indicative available OFFTAKE capacity (E2) and applied-for capacity (the connection queue → E3).
That queue is the Swedish story in one number — northern Sweden's grid is thousands of MW
oversubscribed by the green-industry rush. Income (L1) rides in provenance from Eurostat. Seveso
(L3) stays a gap: the EEA IED `has_seveso` flag is not populated for Sweden (0 sites), so a "none"
reading would be a false negative — MSB's national register is the source (v1).
"""

from .bands import e2_category, e3_category
from .country import run_cli
from .eu_member import make_eu_member_spec
from .geo import arcgis_point_query
from .http import SourceUnavailable

# Svenska kraftnät kapacitetskartan — per-county (21 län) capacity polygons, keyless.
SVK_CAPACITY = ("https://services2.arcgis.com/L8WLzcxhwLqd80Jx/arcgis/rest/services/"
                "kapacitetsdata_vy/FeatureServer")


def _latest(attrs: dict, prefix: str) -> float | None:
    """Newest-year non-null value among fields sharing a prefix (field names carry the year)."""
    for key in sorted((k for k in attrs if k.startswith(prefix)), reverse=True):
        if attrs[key] is not None:
            return attrs[key]
    return None


def collect_grid_se(lat: float, lon: float, accessed: str) -> list[dict]:
    """E2 (available offtake capacity) + E3 (connection-queue oversubscription) for the county the
    point falls in. E3 is provisional: fill = applied / (applied + available), i.e. the share of
    demanded offtake capacity that is already queued — mapped to the shared E3 bands."""
    try:
        feats = arcgis_point_query(SVK_CAPACITY, 0, lat, lon, 1, record_count=5)
    except SourceUnavailable:
        return []
    if not feats:
        return []
    a = feats[0]["attributes"]
    lan = a.get("lansnamn") or a.get("Län") or "county"
    available = _latest(a, "Indikativt_tillgänglig_kapacitet_uttag")
    applied = _latest(a, "Ansökt_kapacitet_uttag")
    out = []
    if available is not None:
        out.append({
            "id": "E2", "status": "measured", "value": e2_category(available),
            "source": {
                "title": f"Svenska kraftnät kapacitetskartan — {lan}: {available} MW indicative "
                         f"available offtake capacity. Per-county grid capacity → shared E2 bands",
                "url": "https://karta.svk.se/", "accessed": accessed},
        })
        if applied is not None and applied + available > 0:
            fill = round(applied / (applied + available) * 100, 1)
            out.append({
                "id": "E3", "status": "measured", "value": e3_category(fill),
                "source": {
                    "title": f"Svenska kraftnät kapacitetskartan — {lan}: {applied} MW applied-for "
                             f"vs {available} MW available offtake ({fill}% of demanded capacity "
                             f"queued). Provisional oversubscription mapping to the shared E3 bands",
                    "url": "https://karta.svk.se/", "accessed": accessed},
            })
    return out


SE_SPEC = make_eu_member_spec(
    "SE",
    extra_collectors=[(("E2", "E3"), lambda ctx, prov: collect_grid_se(
        ctx["lat"], ctx["lon"], ctx["accessed"]))],
    summary={
        "fr": "BROUILLON SE — grille très propre (~23 g/kWh) + capacité réseau Svenska kraftnät "
              "par comté (E2/E3, la file d'attente du nord) + revenu Eurostat. À vérifier.",
        "en": "SE DRAFT — very clean grid (~23 gCO2/kWh) + Svenska kraftnät county grid capacity "
              "(E2/E3, the northern queue) + Eurostat income. Verify before use.",
    })


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(SE_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(SE_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
