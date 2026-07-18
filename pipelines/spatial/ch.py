# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Switzerland — EEA-cooperating non-EU country on the shared factory, natura=False.

Switzerland is EFTA (not EU, not EEA-agreement) but IS an EEA-32 member country of the
European Environment Agency: Corine covers it, CDDA (nationally designated protected
areas) includes it, and energy-charts serves the `ch` zone (~50 gCO2/kWh, hydro-dominated
with nuclear). Natura 2000 does not apply (Emerald Network) — F1 rides the CDDA brick,
same recovery as Norway. Not bound by the Water Framework Directive: if WISE returns no
water body, W2 stays an honest gap rather than a guess. Grid capacity (E2/E3, Swissgrid),
abstraction volumes (W3) and the OPAM major-accident register (L3, the Seveso analogue)
are national feeds not wired in v1 — declared gaps, never zeros.
"""

import math
import urllib.parse

from . import eu
from .country import run_cli
from .eu_member import make_eu_member_spec
from .http import SourceUnavailable, get_json

# --- F2 · national LEGAL zoning (ARE building-zone plan) via the geo.admin.ch identify API -------
# Switzerland's one great asset here: a single keyless identify endpoint over 896 federal layers.
# `ch.are.bauzonen` is the harmonised national building-zone plan — parcel-level LEGAL zoning, so
# strictly better evidence than Corine's 25 ha land cover. Same doctrine as FR/BE/NL: national
# zoning first, Corine as fallback AND cross-check. Probed live 2026-07-19.
GEOADMIN = "https://api3.geo.admin.ch/rest/services/all/MapServer/identify"
BAUZONEN = "ch.are.bauzonen"
_EXTENT_HALF_M = 5000.0   # the map window we declare to the API…
_IMAGE_PX = 500           # …and its pixel size — because `tolerance` is expressed in PIXELS


def geoadmin_identify(lat: float, lon: float, layer: str, radius_m: float = 0) -> list[dict]:
    """Point-query any geo.admin.ch layer, keyless.

    The API's `tolerance` is in PIXELS, not metres, so a metre radius only means something once
    `mapExtent` and `imageDisplay` fix the scale: a 10 km window over 500 px = 20 m/px, hence
    radius_m/20. radius_m=0 is a true point-in-polygon test.
    """
    dlat = _EXTENT_HALF_M / 111320.0
    dlon = _EXTENT_HALF_M / (111320.0 * math.cos(math.radians(lat)))
    params = {
        "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "sr": 4326,
        "layers": f"all:{layer}", "returnGeometry": "false", "lang": "fr",
        "tolerance": int(round(radius_m / (2 * _EXTENT_HALF_M / _IMAGE_PX))),
        "mapExtent": f"{lon-dlon},{lat-dlat},{lon+dlon},{lat+dlat}",
        "imageDisplay": f"{_IMAGE_PX},{_IMAGE_PX},96",
    }
    try:
        return get_json(f"{GEOADMIN}?{urllib.parse.urlencode(params)}").get("results") or []
    except SourceUnavailable:
        return []


def collect_f2(lat: float, lon: float, accessed: str) -> tuple[dict | None, dict]:
    """F2 from the building-zone plan; Corine as fallback and cross-check.

    Every bauzonen category is by definition land designated for construction, so a hit is
    `artificialized` — the zone label rides in the source so a reviewer sees WHICH kind. A miss is
    informative rather than empty: the site sits OUTSIDE the building zone, which is the higher
    land-take conflict, and Corine then says what the ground actually is.
    """
    hits = geoadmin_identify(lat, lon, BAUZONEN, 0)
    a = hits[0].get("attributes", {}) if hits else {}
    zone = a.get("ch_bez_f") or a.get("ch_bez_d")
    clc_code, clc_cat = eu.corine_at_point(lat, lon)
    crosscheck = {
        "primary": "artificialized" if zone else None,
        "primary_source": f"bauzonen '{zone}' ({a.get('name')}, {a.get('kt_kz')})" if zone else None,
        "land_cover": clc_cat, "clc_code": clc_code,
        "agree": (clc_cat == "artificialized") if zone and clc_cat else None,
        "in_building_zone": bool(zone),
    }
    if zone:
        return {"id": "F2", "status": "measured", "value": "artificialized",
                "source": {"title": f"ARE ch.are.bauzonen — zone à bâtir « {zone} » "
                                    f"({a.get('name')}, {a.get('kt_kz')}) au point ; zonage légal "
                                    f"parcellaire. Recoupement Corine : {clc_cat or 'indisponible'}",
                           "url": "https://map.geo.admin.ch/", "accessed": accessed}}, crosscheck
    if clc_cat is None:
        return None, crosscheck
    return {"id": "F2", "status": "measured", "value": clc_cat,
            "source": {"title": f"Corine Land Cover 2018 (EEA) — code CLC {clc_code} au point. Le "
                                f"site est HORS zone à bâtir (ARE ne renvoie aucun polygone) — "
                                f"repli sur l'occupation du sol",
                       "url": eu.EEA_CORINE, "accessed": accessed}}, crosscheck


def _f2(ctx, prov):
    ind, crosscheck = collect_f2(ctx["lat"], ctx["lon"], ctx["accessed"])
    prov["f2_crosscheck"] = crosscheck
    return [ind] if ind else []


CH_SPEC = make_eu_member_spec("CH", natura=False, f1_cdda=True, f2=_f2, extra_gaps={
    "E2": "missing — Swissgrid publishes no nodal hosting capacity and there is no ElCom "
          "equivalent; probed 2026-07-19, the data is not public rather than merely unwired",
    "E3": "missing — no locational congestion published by Swissgrid",
    "W3": "not_collected — ch.bafu.wasser-entnahme returns abstraction POINTS without volumes "
          "(same shape as Luxembourg); a point cannot feed a volume band",
    "L3": "not_collected — no national OPAM register; establishments are cantonal (open WFS "
          "confirmed for UR/SZ/SH/BS/AG only), federal layers carry sectoral corridors only",
}, summary={
    "fr": "BROUILLON CH (EEA-32) — zonage légal parcellaire ARE, aires protégées CDDA, grille hydro-nucléaire très propre. Pas d'obligation EED donc pas de rail de vérification tiers : le A reste réservé. À vérifier.",
    "en": "CH DRAFT (EEA-32) — parcel-level ARE legal zoning, CDDA protected areas, very clean hydro-nuclear grid. No EED duty, hence no third-party verification rail: the A stays reserved. Verify before use.",
})


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(CH_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(CH_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
