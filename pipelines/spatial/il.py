# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Israel (IL) — hand-written spec (GO Franck 2026-08-02, RECON-il.md is the source study).

First scored country OUTSIDE the EU/EEA commons — built on the world bricks (Ember E1, global
LULC F2, Aqueduct W1) plus three national finds:

- **Backbone**: local-authority jurisdiction polygons (point-in-polygon, `CR_LAMAS` = CBS
  locality symbol — the FR-INSEE analogue) + CKAN population join; nearest CBS settlement
  point only as a flagged fallback.
- **F1**: the national INPA reserves/parks layer (1 427 polygons) on ArcGIS Online — a PUBLIC
  MIRROR of the INPA layer (all official state GIS backends sit behind WAF/geo-fencing;
  documented as secondary provenance, same ring logic as Natura/CDDA).
- **L1**: the official CBS socio-economic cluster (aschkol 1-10) via the data.gov.il CKAN
  DataStore, joined by locality symbol — RAW to provenance only (bands are a methodology-lead
  decision, the same refusal as FR/BE/NL).

L3 is wired: the MoEP geolocated registry × toxics permits (join validated 500/500), plane
distances in the registry's own ITM metric (empirical Israel-1993 datum correction, residual
<1 m). Walls, documented (RECON-il.md): Noga grid data (WAF → E2/E3 not_collected — and the
grid IS the Israeli siting story, like Ireland); W2/W3 (no machine path found). W1 follows
the EXPORTABLE water-regime procedure (doctrine 2026-08-01): jurisdiction regime
desal_dominant declared+sourced, site water_source on evidence only, caveat + pre-declared
contradictoire lever — score untouched (calibration decision = Franck, v0.1.0 freeze).
"""

import json

from . import eu, world
from .cache import CACHE_DIR
from .http import SourceUnavailable, get_json, haversine_m

# Local-authority jurisdiction polygons (AGOL, keyless) — point-in-polygon backbone, FR-grade:
# carries Muni_Eng/Muni_Heb + CR_LAMAS (the CBS locality symbol) + district (Machoz).
JURISDICTIONS = ("https://services1.arcgis.com/hWUp5lYOh3Fi9WoQ/arcgis/rest/services/"
                 "GvulotShputRashuyotVaadim/FeatureServer")
# CBS settlement points + population (AGOL, keyless; layer 1) — nearest-point FALLBACK only
# (a point can sit outside every jurisdiction polygon: unincorporated/industrial edge cases).
SETL_POP = ("https://services2.arcgis.com/xMRYm7cNgdR5RN6F/arcgis/rest/services/"
            "Setl_Pop_2023/FeatureServer")
# Population per locality (CKAN DataStore, joined by locality symbol like the aschkol)
POPULATION_RESOURCE = "b8112650-a2f8-41f2-9c05-a9b9483fb4c0"
POPULATION_HUMAN_URL = "https://data.gov.il/dataset/residents_in_israel_by_communities_and_age_groups"
# CBS socio-economic index 2021 per local authority (AGOL, keyless; SemelFixed = CBS symbol,
# CLUSTER_2021/2019 + INDEX_VALUE + RANK) — the official aschkol, spatially published.
SOEC_2021 = ("https://services2.arcgis.com/xMRYm7cNgdR5RN6F/arcgis/rest/services/"
             "SOEC_Rashut_2021/FeatureServer")
SOEC_HUMAN_URL = "https://www.cbs.gov.il/he/publications/Pages/2023/socio-2021.aspx"
# INPA nature reserves & national parks — public AGOL mirror (official backends are walled)
INPA_RESERVES = ("https://services-eu1.arcgis.com/KNPlb4ohpBXwPAVq/arcgis/rest/services/"
                 "%D7%A9%D7%9E%D7%95%D7%A8%D7%95%D7%AA_%D7%98%D7%91%D7%A2_%D7%95%D7%92%D7%A0"
                 "%D7%99%D7%9D_%D7%9C%D7%90%D7%95%D7%9E%D7%99%D7%99%D7%9D/FeatureServer")
INPA_HUMAN_URL = "https://www.parks.org.il/"
# data.gov.il CKAN DataStore template (the anti-bot wall only blocks file downloads;
# the DataStore API is the sanctioned machine path, see RECON-il.md)
CKAN_DATASTORE = ("https://data.gov.il/api/3/action/datastore_search"
                  "?resource_id={rid}&limit=3000")

_SETTLEMENT_BUFFERS_M = (3000, 8000, 15000)


def fetch_locality(lat: float, lon: float) -> dict:
    """IL backbone — the local authority the point SITS IN (jurisdiction polygon, CR_LAMAS =
    CBS locality symbol), FR-commune-grade. Nearest CBS settlement point is only the fallback
    for points outside every jurisdiction (unincorporated/industrial edges) — flagged as such
    (an approximation must never look like an administrative fact)."""
    from .geo import arcgis_point_query

    feats = arcgis_point_query(JURISDICTIONS, 0, lat, lon, 1)
    if feats:
        a = feats[0]["attributes"]
        code = (a.get("CR_LAMAS") or a.get("CR_PNIM") or "").strip() or None
        return {
            "code": int(code) if code and code.isdigit() else None,
            "name": (a.get("Muni_Eng") or a.get("Muni_Heb") or "").strip(),
            "name_he": (a.get("Muni_Heb") or "").strip(),
            "district": (a.get("Machoz") or "").strip(),
            "population": _population_by_locality().get(int(code)) if code and code.isdigit() else None,
            "backbone": "jurisdiction_polygon",
        }
    for radius in _SETTLEMENT_BUFFERS_M:
        pts = arcgis_point_query(SETL_POP, 1, lat, lon, radius, geometry=True, record_count=50)
        best, best_d = None, None
        for f in pts:
            g = f.get("geometry") or {}
            if g.get("x") is None:
                continue
            d = haversine_m(lat, lon, g["y"], g["x"])
            if best is None or d < best_d:
                best, best_d = f["attributes"], d
        if best:
            return {
                "code": best.get("SETL_CODE"),
                "name": (best.get("ENG_NAME") or best.get("HEB_NAME") or "").strip(),
                "name_he": (best.get("HEB_NAME") or "").strip(),
                "district": None,
                "population": best.get("Population_size___Israeli_local"),
                "backbone": f"nearest_settlement_point_{round(best_d)}m",
            }
    raise SourceUnavailable(f"no jurisdiction/settlement within {_SETTLEMENT_BUFFERS_M[-1]} m")


_population_memo: dict | None = None


def _population_by_locality() -> dict[int, int]:
    """{locality_symbol: total population} — CKAN DataStore, cached on disk once."""
    global _population_memo
    if _population_memo is not None:
        return _population_memo
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / "il_population_by_locality.json"
    if dest.exists() and dest.stat().st_size > 0:
        records = json.loads(dest.read_text())
    else:
        data = get_json(CKAN_DATASTORE.format(rid=POPULATION_RESOURCE))
        if not data.get("success"):
            raise SourceUnavailable("data.gov.il datastore_search failed for population")
        records = data["result"]["records"]
        dest.write_text(json.dumps(records, ensure_ascii=False))
    out = {}
    for r in records:
        sym, tot = r.get("סמל_ישוב"), r.get("סהכ")
        if sym and tot:
            try:
                out[int(sym)] = int(tot)
            except (TypeError, ValueError):
                continue
    _population_memo = out
    return out


_soec_memo: dict[int, dict | None] = {}


def soec_for_locality(code: int) -> dict | None:
    """Official CBS 2021 socio-economic index for a local authority (cluster 1-10, rank,
    index value) — attribute query on the spatially published layer, keyed by the SAME CBS
    symbol as the jurisdiction backbone (no cross-registry code mismatch)."""
    if code in _soec_memo:
        return _soec_memo[code]
    try:
        data = get_json(f"{SOEC_2021}/1/query", {
            "f": "json", "where": f"SemelFixed={int(code)}",
            "outFields": "CLUSTER_2021,CLUSTER_2019,INDEX_VALUE_2021,RANK_2021,Local_Auth",
            "returnGeometry": "false"})
        feats = data.get("features") or []
        a = feats[0]["attributes"] if feats else None
        out = None if a is None else {
            "cluster_2021": a.get("CLUSTER_2021"), "cluster_2019": a.get("CLUSTER_2019"),
            "index_value_2021": a.get("INDEX_VALUE_2021"), "rank_2021": a.get("RANK_2021"),
        }
    except SourceUnavailable:
        out = None
    _soec_memo[code] = out
    return out


# Jurisdiction water-supply regime (exportable W1 procedure — doctrine 2026-08-01):
# Israel's municipal/domestic supply is predominantly desalinated (5 Mediterranean plants;
# ~80%+ of domestic consumption) — declared ONCE here, sourced; the Gulf declares its own.
IL_WATER_REGIME = "desal_dominant"
IL_WATER_REGIME_SOURCE = {
    "title": "Israel Water Authority / FAO AQUASTAT — desalinated water is the dominant share "
             "of Israel's municipal supply (~80%+ of domestic consumption)",
    "url": "https://www.fao.org/aquastat/en/countries-and-basins/country-profiles/country/ISR",
    "accessed": "2026-08-02",
}


def _w1_desal(ctx, prov):
    frag = eu.collect_w1_aqueduct(ctx["lat"], ctx["lon"], ctx["accessed"])
    frag = world.apply_w1_regime(frag, prov, regime=IL_WATER_REGIME,
                                 regime_source=IL_WATER_REGIME_SOURCE,
                                 water_source="undisclosed")
    return [frag] if frag else []


def _f1_inpa(ctx, prov):
    frag = eu.natura_rings(
        ctx["lat"], ctx["lon"], ctx["accessed"],
        service_url=INPA_RESERVES, layer=0,
        site_attr=("PARK_ENG_N", "ENG_NAME", "NAME"),
        title="INPA nature reserves & national parks (public ArcGIS mirror of the national "
              "layer; official GIS backends are walled) — overlap by distance ring",
        url=INPA_HUMAN_URL)
    return [frag] if frag else []


def _e1_ember(ctx, prov):
    frag = world.collect_e1_ember("ISR", ctx["accessed"])
    return [frag] if frag else []


def _l1_raw(ctx, prov):
    """Aschkol RAW to provenance only — bands are a methodology-lead decision (FR/BE/NL rule)."""
    commune = ctx.get("commune") or {}
    code = commune.get("code")
    soec = soec_for_locality(int(code)) if code is not None else None
    prov["l1_soec"] = {
        "locality_symbol": code, **(soec or {"note_missing": "no SOEC row for this symbol"}),
        "source": {"title": "CBS socio-economic index of local authorities 2021 (cluster 1-10, "
                            "rank, index value) — spatially published layer, keyed by CBS symbol",
                   "url": SOEC_HUMAN_URL, "accessed": ctx["accessed"]},
        "note": "raw to provenance; bands are a methodology-lead decision",
    }
    return []


# --- L3 · hazardous-substance sites (MoEP registry × toxics permits) --------------------------
# The geolocated environmental registry (25 758 sites, ITM/EPSG:2039 coordinates) joined with the
# toxics-permit resource — join VALIDATED live 2026-08-02: Mifal_Key ↔ Mispar_Mezahe, 500/500.
MOEP_REGISTRY_RESOURCE = "88d1883c-3b7a-4580-9be9-6d54659666c3"
MOEP_PERMITS_RESOURCE = "e9ecedbd-8f93-437e-9a2f-4ff908daf210"
MOEP_HUMAN_URL = "https://www.gov.il/he/departments/ministry_of_environmental_protection"

# WGS84 → Israeli TM Grid (EPSG:2039) — standard Transverse Mercator forward, stdlib only.
# Validated against the CBS settlement layer's own ITM/WGS84 coordinate pairs (see tests).
_ITM_A = 6378137.0
_ITM_F = 1 / 298.257222101          # GRS80
_ITM_K0 = 1.0000067
_ITM_LAT0 = 31.7343936111111
_ITM_LON0 = 35.2045169444444
_ITM_FE = 219529.584
_ITM_FN = 626907.390
# EPSG:2039 sits on the Israel 1993 datum, not WGS84 — the missing Helmert shift shows up as a
# near-constant plane offset. Derived empirically against 40 CBS settlement pairs spread across
# the country (own ITM attrs vs own WGS84 geometry): mean (-65.86, -40.33) m, stdev
# (0.12, 0.36) m, max residual 0.8 m after correction — far inside the 2/5 km L3 bands.
_ITM_DATUM_DX = -65.86
_ITM_DATUM_DY = -40.33


def _tm_meridian_arc(lat_rad: float) -> float:
    import math
    e2 = _ITM_F * (2 - _ITM_F)
    return _ITM_A * ((1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * lat_rad
                     - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * lat_rad)
                     + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * lat_rad)
                     - (35 * e2**3 / 3072) * math.sin(6 * lat_rad))


def wgs84_to_itm(lat: float, lon: float) -> tuple[float, float]:
    """(easting, northing) in EPSG:2039 — lets L3 distances be computed in the registry's own
    metric plane (no inverse transform of 25k rows)."""
    import math
    e2 = _ITM_F * (2 - _ITM_F)
    ep2 = e2 / (1 - e2)
    phi = math.radians(lat)
    lam = math.radians(lon - _ITM_LON0)
    n = _ITM_A / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    c = ep2 * math.cos(phi) ** 2
    a_ = lam * math.cos(phi)
    m = _tm_meridian_arc(phi)
    m0 = _tm_meridian_arc(math.radians(_ITM_LAT0))
    x = _ITM_K0 * n * (a_ + (1 - t + c) * a_**3 / 6
                       + (5 - 18 * t + t**2 + 72 * c - 58 * ep2) * a_**5 / 120) + _ITM_FE
    y = _ITM_K0 * (m - m0 + n * math.tan(phi) * (a_**2 / 2
                   + (5 - t + 9 * c + 4 * c**2) * a_**4 / 24
                   + (61 - 58 * t + t**2 + 600 * c - 330 * ep2) * a_**6 / 720)) + _ITM_FN
    return x + _ITM_DATUM_DX, y + _ITM_DATUM_DY


_moep_memo: list | None = None


def moep_toxic_sites() -> list[tuple[float, float]]:
    """ITM (x, y) of every registry site holding a toxics permit ('רעלים') — cached on disk."""
    global _moep_memo
    if _moep_memo is not None:
        return _moep_memo
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / "il_moep_toxic_sites.json"
    if dest.exists() and dest.stat().st_size > 0:
        _moep_memo = [tuple(p) for p in json.loads(dest.read_text())]
        return _moep_memo
    permits = get_json(CKAN_DATASTORE.format(rid=MOEP_PERMITS_RESOURCE).replace("limit=3000", "limit=30000"))
    if not permits.get("success"):
        raise SourceUnavailable("MoEP permits datastore failed")
    toxic_keys = {r.get("Mifal_Key") for r in permits["result"]["records"]
                  if "רעלים" in (r.get("Heter_Name") or "")}
    registry = get_json(CKAN_DATASTORE.format(rid=MOEP_REGISTRY_RESOURCE).replace("limit=3000", "limit=30000"))
    if not registry.get("success"):
        raise SourceUnavailable("MoEP registry datastore failed")
    pts = []
    for r in registry["result"]["records"]:
        if r.get("Mispar_Mezahe") in toxic_keys:
            x, y = r.get("Nekudat_Tsiun_X"), r.get("Nekudat_Tsiun_Y")
            try:
                pts.append((float(x), float(y)))
            except (TypeError, ValueError):
                continue
    dest.write_text(json.dumps(pts))
    _moep_memo = pts
    return pts


def _l3_moep(ctx, prov):
    """L3 via the MoEP toxics-permit sites — plane distances in the registry's own ITM metric.
    Permit tier is not published (upper_tier=None): the shared l3_value stays band-safe — an
    unknown-tier site inside 2 km makes the band undecidable (pads to not_collected, we never
    guess a hazard class)."""
    from .bands import l3_value

    try:
        sites = moep_toxic_sites()
    except SourceUnavailable:
        return []
    x0, y0 = wgs84_to_itm(ctx["lat"], ctx["lon"])
    near = []
    for x, y in sites:
        d_km = ((x - x0) ** 2 + (y - y0) ** 2) ** 0.5 / 1000.0
        if d_km <= 5.0:
            near.append({"upper_tier": None, "dist_km": d_km})
    value = l3_value(near)
    # Site-level FACT either way (the doc-thinness reducer): the toxics-permit class is much
    # broader than Seveso (labs, cosmetics…) and carries no severity tier — a count is honest
    # context, a hazard class would be a guess.
    prov["l3_moep_context"] = {
        "toxics_permit_sites_within_2km": sum(1 for s in near if s["dist_km"] <= 2.0),
        "toxics_permit_sites_within_5km": len(near),
        "note": "MoEP toxics permits (רעלים) are far broader than the Seveso class and publish "
                "no severity tier — counts are context, never a hazard verdict",
        "source": {"title": "MoEP environmental registry × toxics permits (join validated)",
                   "url": MOEP_HUMAN_URL, "accessed": ctx["accessed"]},
    }
    if value is None:
        prov["l3_note"] = ("toxics-permit site within 2 km with unpublished tier — band "
                           "undecidable, we never guess a hazard class")
        return []
    return [{"id": "L3", "status": "measured", "value": value,
             "source": {"title": f"MoEP environmental registry × toxics permits ('רעלים') — "
                                 f"{len(near)} permitted site(s) within 5 km (join "
                                 "Mifal_Key↔Mispar_Mezahe, ITM plane distances)",
                        "url": MOEP_HUMAN_URL, "accessed": ctx["accessed"]}}]


IL_SPEC = {
    "iso": "IL",
    "generator": "pipelines.spatial.il v1",
    "summary": {
        "fr": "BROUILLON IL v1 (Ember, Aqueduct+caveat dessalement, INPA, LULC monde, aschkol "
              "CBS en provenance) — à vérifier.",
        "en": "IL DRAFT v1 (Ember, Aqueduct+desalination caveat, INPA, world LULC, CBS aschkol "
              "raw in provenance) — verify before use.",
    },
    "fetch_commune": fetch_locality,
    "identity_fields": lambda c: {"municipality": c.get("name") or "UNKNOWN — to fill"},
    "collectors": [
        (("E1",), _e1_ember),
        (("W1",), _w1_desal),
        (("F1",), _f1_inpa),
        (("F2",), world.collect_f2_global_landcover),
        (("L3",), _l3_moep),
        ((), _l1_raw),                      # provenance-only, declares no indicator id
    ],
    "collectable_gaps": frozenset({"E2", "E3", "W2", "W3", "L1"}),
    "provenance_commune": lambda c: {"locality_symbol": c.get("code"),
                                     "locality_name_he": c.get("name_he"),
                                     "district": c.get("district"),
                                     "population": c.get("population"),
                                     "backbone": c.get("backbone")},
    "provenance_extra": lambda ctx, prov: {
        "known_gaps": {
            "E2": "not_collected — Noga (grid operator) is WAF/geo-fenced (RECON-il): no open "
                  "hosting-capacity feed. The grid IS the Israeli siting story (Ireland pattern)",
            "E3": "not_collected — same wall (Noga)",
            "W2": "not_collected — no machine path found (Water Authority portal/PDF)",
            "W3": "not_collected — same",
            "L1": "not_collected — official CBS 2021 index RAW in provenance (l1_soec); bands = methodology lead",
        },
        "f2_crosscheck": prov.get("f2_crosscheck"),
        "l1_soec": prov.get("l1_soec"),
        "w1_water_regime": prov.get("w1_water_regime"),
        "l3_note": prov.get("l3_note"),
        "l3_moep_context": prov.get("l3_moep_context"),
    },
    "manual_still_required": ["F3", "L2", "T1", "T2", "E2", "E3", "W2", "W3"],
}
