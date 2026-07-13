# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""DCWatch reader — per-site power (MW) and disclosed metrics from the DCWatch
digital common (Hubblo), ODbL.

DCWatch <https://dcwatch.hubblo.org> is a collaborative research common on
data-center footprint; per-site power is human-collected from public sources
(press, permits, operator PDFs), which is exactly the field our deterministic
spatial pipeline cannot auto-fill. Same license as our published data (ODbL):
attribution required — every value carried from here must credit DCWatch and,
when present, its primary source (`lien_fournisseur`).

Bulk-not-API (A-23 pattern): we read the versioned CSV export from the GitLab
repository, pinned to an immutable COMMIT (the dated release tags predate the
export file, so tags cannot pin it). Proposals only, never a publication: the
matching to our corpus stays at the human gate (`propose.py`).
"""

import csv
import io
import re
import unicodedata

from pipelines.spatial.http import get_text

# Immutable pin: commit that introduced/last-updated the single-CSV export.
# Bump deliberately when adopting a newer DCWatch snapshot (journal the change).
DCWATCH_COMMIT = "7dd5b5e9"
DCWATCH_CSV_URL = (
    "https://gitlab.com/api/v4/projects/hubblo%2Fdatacenter-watch"
    f"/repository/files/export_from_poc.csv/raw?ref={DCWATCH_COMMIT}"
)
ATTRIBUTION = f"DCWatch (Hubblo), ODbL — export {DCWATCH_COMMIT}, gitlab.com/hubblo/datacenter-watch"


def _num(raw: str | None) -> float | None:
    """French-locale number ('1,5', '188,04', thin spaces) -> float, None if absent/zero."""
    if not raw:
        return None
    cleaned = raw.replace(" ", "").replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return value if value > 0 else None


def normalize_name(s: str | None) -> str:
    """Accent-insensitive, punctuation-collapsed uppercase key for matching."""
    s = unicodedata.normalize("NFD", (s or "").upper())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def parse(text: str) -> list[dict]:
    """Parse the DCWatch CSV export into normalized records (one per site row)."""
    records = []
    for row in csv.DictReader(io.StringIO(text)):
        records.append({
            "name": (row.get("nom") or "").strip(),
            "operator": (row.get("operateur") or "").strip(),
            "commune": (row.get("nom_commune") or "").strip(),
            "code_insee": (row.get("code_insee") or "").strip(),
            "country": (row.get("code_pays") or "").strip(),
            "status": (row.get("etat_avancement_synthèse") or row.get("etat_avancement") or "").strip(),
            "power_mw": _num(row.get("puiss_MW")),
            "pue_disclosed": _num(row.get("PUE_officiel")),
            "cooling": (row.get("cooling") or "").strip() or None,
            # primary source when the common recorded one — "the press points, the registry proves"
            "source_url": (row.get("lien_fournisseur") or "").strip() or None,
            "provenance": (row.get("provenance") or "").strip() or None,
        })
    return records


def fetch(country: str | None = "FR") -> list[dict]:
    """Download the pinned export and return records, optionally filtered by country."""
    records = parse(get_text(DCWATCH_CSV_URL))
    if country:
        records = [r for r in records if r["country"] == country]
    return records
