# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Statbel fiscal income (Table D) — cached reference, keyed by NIS commune code.

Same brick as INSEE Filosofi in the FR pipeline: download once, join by code. Table D carries
the median net taxable income per declaration for every STATISTICAL SECTOR; we group sector
medians by their commune NIS prefix. The commune aggregate (median of sector medians) feeds the
provenance sidecar only — see sources.collect_l1_raw for why no L1 value is emitted in Belgium.
"""

import re
import zipfile
from xml.etree import ElementTree as ET

from ..cache import cached_path
from ..http import SourceUnavailable

_TABLE_D_URL = ("https://statbel.fgov.be/sites/default/files/files/documents/Huishoudens/"
                "10.9%20Fiscale%20inkomens/fisc2023_D_FR.xlsx")
_REFNIS_URL = ("https://statbel.fgov.be/sites/default/files/Over_Statbel_FR/Nomenclaturen/"
               "REFNIS_2025.csv")
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

_index: dict[str, list[float]] | None = None
_refnis: dict[str, str] | None = None


def _normalize(name: str) -> str:
    out = name.lower().strip()
    for src, dst in (("à", "a"), ("â", "a"), ("ä", "a"), ("é", "e"), ("è", "e"), ("ê", "e"),
                     ("ë", "e"), ("î", "i"), ("ï", "i"), ("ô", "o"), ("ö", "o"), ("û", "u"),
                     ("ü", "u"), ("ç", "c"), ("'", " "), ("-", " ")):
        out = out.replace(src, dst)
    return " ".join(out.split())


def load_refnis() -> dict[str, str]:
    """{normalized commune name (FR and NL): NIS code} from the official REFNIS nomenclature."""
    global _refnis
    if _refnis is not None:
        return _refnis
    path = cached_path(_REFNIS_URL, "statbel_refnis_2025.csv")
    index: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines()[1:]:
        parts = line.split("|")
        if len(parts) < 5:
            continue
        code = parts[0].strip()
        if not re.fullmatch(r"\d{5}", code) or code.endswith("000"):
            continue  # keep commune rows only (aggregates end in 000)
        for name in (parts[1], parts[4]):
            if name.strip():
                index[_normalize(name)] = code
    if not index:
        raise SourceUnavailable("REFNIS nomenclature parsed to zero communes")
    _refnis = index
    return index


def load_sector_income() -> dict[str, list[float]]:
    """{nis_commune_code: [sector median incomes EUR]} from the cached Table D extract."""
    global _index
    if _index is not None:
        return _index
    path = cached_path(_TABLE_D_URL, "statbel_fisc2023_table_d.xlsx")
    index: dict[str, list[float]] = {}
    with zipfile.ZipFile(path) as z:
        try:
            ss = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter(_NS + "t")) for si in ss]
        except KeyError:
            shared = []
        root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        for row in root.iter(_NS + "row"):
            cells: dict = {}
            for c in row:
                ref = c.attrib.get("r", "")
                m = re.match(r"([A-Z]+)", ref)
                if not m:
                    continue
                v = c.find(_NS + "v")
                if v is None:
                    continue
                cells[m.group(1)] = shared[int(v.text)] if c.attrib.get("t") == "s" else v.text
            nis = str(cells.get("A", "")).strip()
            if not re.fullmatch(r"\d{5}", nis):
                continue  # header/blank rows
            try:
                median = float(str(cells.get("G", "")).strip())
            except (TypeError, ValueError):
                continue  # sectors under the disclosure threshold print '.'
            index.setdefault(nis, []).append(median)
    if not index:
        raise SourceUnavailable("Statbel Table D parsed to zero commune sectors")
    _index = index
    return index
