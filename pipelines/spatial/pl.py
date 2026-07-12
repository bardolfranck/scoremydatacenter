# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Poland — the shared EU factory + two national feeds (grid capacity, Seveso).

The angle E1 carries alone stays the story — the Polish grid is the dirtiest in Europe (~650
gCO2/kWh, coal) while Warsaw is the fastest-growing EU hub. On top of the EU bricks, PL wires two
national signals that DO exist openly:
  * E2 — PSE's `bazamocy.pl` hosting-capacity map (per GPZ / HV substation, available MW by
    quarter) exposes real per-node connection capacity — the Polish Caparéseau, keyless via the
    ArcGIS usrsvcs proxy. We read the nearest substation's available MW → the shared E2 bands.
  * L3 — the EEA IED_SiteMap `has_seveso` flag is populated for Poland (204 sites in 2024), so the
    EU-wide Seveso brick is reliable here.
Income (L1) rides in provenance from the common Eurostat brick. E3 (connection-queue fill) is a
separate PSE layer (applicants) not yet aggregated per node → gap.
"""

import re

from .bands import e2_category
from .country import run_cli
from .eu_member import make_eu_member_spec
from .geo import arcgis_point_query
from .http import SourceUnavailable, haversine_m

# PSE bazamocy — GPZ (HV/MV substation) available-capacity layer, keyless via the ArcGIS proxy.
PSE_GPZ = ("https://utility.arcgis.com/usrsvcs/servers/bc280487545649ec988a4878a442ee74/"
           "rest/services/bazamocy_gpz/FeatureServer")
_GPZ_SEARCH_M = 40000  # a DC connects to its regional HV substation; 40 km covers the catchment


def _available_mw(attrs: dict, year: int) -> tuple[float | None, int | None]:
    """Latest-snapshot available connection MW for `year` from a GPZ record. Field shape:
    `rok{year}_za_{I|II|III|IV}_kw{snapshot_year}` = MW available in `year` per that snapshot."""
    best, best_snapshot = None, -1
    for key, val in attrs.items():
        if val is None:
            continue
        m = re.match(rf"rok{year}_za_\w+_kw(\d{{4}})$", key)
        if m and int(m.group(1)) > best_snapshot:
            best_snapshot, best = int(m.group(1)), val
    return best, (best_snapshot if best is not None else None)


def collect_e2_pse(lat: float, lon: float, accessed: str) -> dict | None:
    """E2 from the nearest PSE GPZ substation's available connection capacity (MW)."""
    try:
        feats = arcgis_point_query(PSE_GPZ, 0, lat, lon, _GPZ_SEARCH_M, geometry=True, record_count=300)
    except SourceUnavailable:
        return None
    feats = [f for f in feats if (f.get("geometry") or {}).get("x") is not None]
    if not feats:
        return None
    nearest = min(feats, key=lambda f: haversine_m(lat, lon, f["geometry"]["y"], f["geometry"]["x"]))
    a, g = nearest["attributes"], nearest["geometry"]
    dist_km = round(haversine_m(lat, lon, g["y"], g["x"]) / 1000, 1)
    year = int(accessed[:4])
    mw, snapshot = _available_mw(a, year)
    for ahead in range(1, 5):  # if the current year is blank, look at the next horizon reported
        if mw is not None:
            break
        year = int(accessed[:4]) + ahead
        mw, snapshot = _available_mw(a, year)
    if mw is None:
        return None
    return {
        "id": "E2", "status": "measured", "value": e2_category(mw),
        "source": {
            "title": f"PSE bazamocy.pl — nearest HV substation (GPZ) '{a.get('Nazwa')}' at "
                     f"{dist_km} km: {mw} MW available connection capacity for {year} "
                     f"(snapshot Q{snapshot}). Per-node capacity, mapped to the shared E2 bands",
            "url": "https://bazamocy.pl/", "accessed": accessed},
    }


PL_SPEC = make_eu_member_spec(
    "PL",
    l3_ied=True,  # EEA IED has_seveso is populated for Poland → the Seveso brick is reliable here
    extra_collectors=[(("E2",), lambda ctx, prov: [x] if (x := collect_e2_pse(
        ctx["lat"], ctx["lon"], ctx["accessed"])) else [])],
    extra_gaps={"E3": "not_collected — PSE publishes a connection-queue layer (applicants) but it "
                      "is not yet aggregated per substation (v1)"},
    summary={
        "fr": "BROUILLON PL — angle énergie (grille la plus sale d'Europe ~650 g/kWh) + capacité "
              "réseau PSE (E2) + Seveso EEA. À vérifier.",
        "en": "PL DRAFT — energy angle (Europe's dirtiest grid ~650 gCO2/kWh) + PSE grid capacity "
              "(E2) + EEA Seveso. Verify before use.",
    })


def collect(lat, lon, *, name, operator, power_mw, project_status, accessed):
    from .country import build_draft
    return build_draft(PL_SPEC, lat, lon, name=name, operator=operator, power_mw=power_mw,
                       project_status=project_status, accessed=accessed)


def main(argv=None):
    return run_cli(PL_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
