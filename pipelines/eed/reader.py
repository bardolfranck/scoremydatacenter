# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""EED regulatory disclosures — the Dutch (RVO) per-facility data-centre report.

WHY THIS SOURCE. Commercial aggregators publish data-centre "MW" that is, in practice, the
grid feed, the full-build target, a campus total or plain MVA — mislabelled as IT load and wrong
by 2x to 13x (measured: Atman Warsaw 57 vs 12.1 operator-stated; DATASIX Vienna 3.0 vs 0.712;
Digital Realty DUS1 2.3 vs 23 between two aggregators). Directive (EU) 2023/1791 (EED) Art. 12
makes every data centre >= 500 kW installed IT power report a fixed schema annually. The EU
database itself is closed — Delegated Regulation (EU) 2024/1364 Art. 5(5) obliges the Commission
and Member States to keep per-facility values confidential, publishing only national aggregates.
But Art. 5(3) gives each Member State the raw data FOR ITS OWN TERRITORY, and the Netherlands
publishes it: RVO ships the full EED schema as an open spreadsheet, named facility by named
facility. That is the authoritative source this module reads.

WHAT IT GIVES (per facility, EED Annex I-III): installed IT power **with the declared
INSTALLED-vs-RATED basis** — the exact distinction the aggregators destroy — plus computer-room
area, total/IT/backup energy, water input, waste heat reused, renewable split, and the Eurostat
LAU code.

Stdlib only: an .xlsx is a zip of XML, so it is read with zipfile + ElementTree. No new dependency
(same refusal as netCDF/h5py elsewhere in this pipeline).
"""

import io
import urllib.request
import zipfile
from xml.etree import ElementTree as ET

RVO_XLSX = ("https://www.rvo.nl/sites/default/files/2026-07/"
            "Rapportages%20energie-efficientie%20datacentra_2.xlsx")
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_UA = "ScoreMyDataCenter/1.0 (+https://scoremydatacenter.org)"

# The EED Annex I-III fields we carry forward, mapped from the RVO column headers.
FIELDS = {
    "referenceId": "reference_id", "owner_name": "owner", "operator_name": "operator",
    "name": "name", "lauCode": "lau_code", "type": "type",
    "operational StartYear": "start_year",
    "itPowerDemand Installed": "it_power_kw",
    "itPowerDemand InstalledType": "it_power_basis",      # INSTALLED | RATED — never merge these
    "totalComputerRoom FloorArea": "computer_room_m2",
    "totalFloorArea": "total_floor_m2",
    "totalEnergy Consumption": "energy_kwh",
    "totalEnergy ITEquipment Consumption": "energy_it_kwh",
    "total WaterInput": "water_m3",
    "totalPotable WaterInput": "water_potable_m3",
    "wasteHeat Reused": "waste_heat_kwh",
    "totalRenewable EnergyConsumption": "renewable_kwh",
}


def _col_index(ref: str) -> int:
    """'BC12' -> zero-based column index."""
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def _rows(blob: bytes):
    """Yield the sheet as lists of cell strings (shared-string table resolved)."""
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{_NS}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{_NS}t")))
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    for row in sheet.iter(f"{_NS}row"):
        cells: dict[int, str] = {}
        for c in row.iter(f"{_NS}c"):
            v = c.find(f"{_NS}v")
            if v is None or v.text is None:
                continue
            text = shared[int(v.text)] if c.get("t") == "s" and v.text.isdigit() else v.text
            cells[_col_index(c.get("r", "A1"))] = text
        yield [cells.get(i, "") for i in range(max(cells) + 1)] if cells else []


def parse(blob: bytes) -> list[dict]:
    """The RVO sheet -> one dict per facility, keyed by our FIELDS names."""
    rows = [r for r in _rows(blob) if r]
    header = next((r for r in rows if "referenceId" in r), None)
    if header is None:
        return []
    idx = {col: header.index(col) for col in FIELDS if col in header}
    out = []
    for r in rows[rows.index(header) + 1:]:
        rec = {out_name: (r[i].strip() if i < len(r) and r[i] else None)
               for col, out_name in FIELDS.items() if (i := idx.get(col)) is not None}
        if not rec.get("name"):
            continue
        kw = rec.get("it_power_kw")
        # kW in the source; MW is what the corpus speaks. Basis is carried, never inferred.
        rec["it_power_mw"] = round(float(kw) / 1000, 4) if kw else None
        out.append(rec)
    return out


def fetch(url: str = RVO_XLSX) -> list[dict]:
    """Download and parse the current RVO disclosure sheet."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return parse(resp.read())
