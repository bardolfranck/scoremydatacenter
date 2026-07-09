# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Elia (Belgian TSO) — grid carbon intensity (E1) and hosting capacity (E2).

E1 — Open Data dataset ods192 (CO2 intensity, historical). Unlike France's flat nuclear
baseline, the Belgian grid swings 60–250 gCO2e/kWh intraday, so a snapshot would be a lottery:
we take the 12-month mean (production-based), a deliberate, flagged divergence from the FR
snapshot procedure.

E2 — the Hosting Capacity Map: a no-auth xlsx feed with ~385 substations × WGS84 coords ×
available MW *for load* at 4 flexibility levels × 2 horizons. Strictly richer than Caparéseau.
We take the nearest substation, horizon 2027, Load 0% flex (most conservative), and band it with
the same provisional cutoffs as the FR pipeline (band parity).

E3 — Elia publishes no per-substation connection queue (no Caparéseau fill-rate twin): the
indicator stays "missing" in Belgium, documented in provenance. Headroom is already E2's signal.
"""

import re
import zipfile
from xml.etree import ElementTree as ET

from ..cache import cached_path
from ..capareseau import _e2_category
from ..http import SourceUnavailable, haversine_m

_ODS192 = "https://opendata.elia.be/api/explore/v2.1/catalog/datasets/ods192/records"
_HCM_URL = "https://griddata.elia.be/eliabecontrols.prod/interface/HostingCapacityMap/v2/download"
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _source(title: str, url: str, accessed: str) -> dict:
    return {"title": title, "url": url, "accessed": accessed}


# --- E1 · grid carbon intensity (national, 12-month mean) ------------------------------------

def collect_e1(accessed: str) -> dict | None:
    from ..http import get_json
    from datetime import date, timedelta
    since = (date.fromisoformat(accessed) - timedelta(days=365)).isoformat()
    try:
        data = get_json(_ODS192, {
            "select": "avg(production) as avg_prod, avg(consumption) as avg_cons",
            "where": f'datetime >= "{since}"',
            "limit": 1,
        })
    except SourceUnavailable:
        return None
    rows = data.get("results") or []
    if not rows or rows[0].get("avg_prod") is None:
        return None
    mean = round(float(rows[0]["avg_prod"]), 2)
    cons = rows[0].get("avg_cons")
    cons_txt = f"; consumption-based {round(float(cons), 2)}" if cons is not None else ""
    return {
        "id": "E1",
        "status": "measured",
        "value": mean,
        "source": _source(
            f"Elia Open Data ods192 — Belgian grid CO2 intensity, production-based, "
            f"12-month mean since {since} ({mean} gCO2/kWh{cons_txt}). Snapshot too volatile "
            f"in BE (60-250 g/kWh intraday), mean used instead — divergence from FR snapshot "
            f"procedure, flagged",
            "https://opendata.elia.be/explore/dataset/ods192/",
            accessed),
    }


# --- E2 · grid connection capacity (Hosting Capacity Map xlsx) --------------------------------

def _parse_sheet(z: zipfile.ZipFile, sheet_file: str) -> list[dict]:
    """Rows of one worksheet as {column_letter: value}, handling inline strings."""
    root = ET.fromstring(z.read(sheet_file))
    rows = []
    for row in root.iter(_NS + "row"):
        vals: dict = {}
        for c in row:
            ref = c.attrib.get("r", "")
            m = re.match(r"([A-Z]+)", ref)
            if not m:
                continue
            col = m.group(1)
            if c.attrib.get("t") == "inlineStr":
                t = c.find(_NS + "is/" + _NS + "t")
                vals[col] = t.text if t is not None else None
            else:
                v = c.find(_NS + "v")
                if v is not None:
                    vals[col] = float(v.text)
        rows.append(vals)
    return rows


def load_substations(horizon: str = "2027") -> list[dict]:
    """[{substation, voltage_kv, lat, lon, load_0flex_mw, load_20flex_mw}] for one horizon.

    Columns (frozen by Elia's export, guarded in tests): A site, B substation, C voltage,
    D longitude, E latitude, F Load_0%_flex … I Load_20%_flex.
    """
    path = cached_path(_HCM_URL, "elia_hosting_capacity_map.xlsx")
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = {s.attrib["name"]: i + 1 for i, s in enumerate(wb.iter(_NS + "sheet"))}
        idx = sheets.get(horizon) or min(sheets.values())
        rows = _parse_sheet(z, f"xl/worksheets/sheet{idx}.xml")
    out = []
    for r in rows:
        if isinstance(r.get("D"), float) and isinstance(r.get("E"), float):
            out.append({
                "substation": r.get("B"), "voltage_kv": r.get("C"),
                "lat": r["E"], "lon": r["D"],
                "load_0flex_mw": r.get("F"), "load_20flex_mw": r.get("I"),
            })
    if not out:
        raise SourceUnavailable("Elia hosting capacity map parsed to zero substations")
    return out


def collect_grid_capacity(lat: float, lon: float, accessed: str) -> list[dict]:
    """E2 from the nearest Elia substation (E3 has no Belgian public source — see module doc)."""
    try:
        subs = load_substations()
    except SourceUnavailable:
        return []
    best = min(subs, key=lambda s: haversine_m(lat, lon, s["lat"], s["lon"]))
    dist_km = round(haversine_m(lat, lon, best["lat"], best["lon"]) / 1000, 2)
    mw = best.get("load_0flex_mw")
    if mw is None:
        return []
    flex = best.get("load_20flex_mw")
    flex_txt = f" ({flex} MW at 20% flex)" if flex is not None else ""
    return [{
        "id": "E2",
        "status": "measured",
        "value": _e2_category(float(mw)),
        "source": _source(
            f"Elia Hosting Capacity Map (2027, Load 0% flex) — nearest substation "
            f"{best['substation']} at {dist_km} km: {mw} MW available for load{flex_txt}. "
            f"Provisional FR bands",
            "https://www.elia.be/en/customers/connection/grid-hosting-capacity",
            accessed),
    }]
