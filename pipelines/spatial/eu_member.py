# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""One factory for every country that has NO national quirks — the anti-clone.

Rule (Franck, 2026-07-11): think COMMON, don't accumulate near-identical per-country files. A full
EU/EEA member with nothing special is entirely described by the EU-level bricks (energy-charts E1,
EEA WISE W2, Natura F1, Corine F2) plus its ISO code. `make_eu_member_spec()` returns that spec;
a country module shrinks to one line. Only genuine national specifics (BE regional, NL/LU/GB/DE
national feeds and gaps) keep a hand-written spec.

Flags for the two common deviations, both seen in the field:
- e1=False   — energy-charts does not serve the zone (Ireland: HTTP 500 for `ie`).
- natura=False — the country is outside Natura 2000 (Norway: Emerald Network instead).
"""

from . import eu
from .http import SourceUnavailable, get_json

_BASE_GAPS = {
    "E2": "not_collected — grid hosting capacity is per national TSO; no single open feed wired (v1)",
    "E3": "not_collected — no public national connection-queue feed wired",
    "W3": "not_collected — abstraction volumes not wired",
    "L1": "not_collected — national income per region (v1; bands are a methodology decision anyway)",
    "L3": "not_collected — national Seveso register not wired (v1)",
}

_L1_RAW_GAP = ("not_collected — raw Eurostat NUTS2 disposable income in provenance (l1_eurostat, "
               "frozen skeleton baseline); bands are a methodology decision (same refusal as FR/BE/NL)")


def _nominatim_commune(lat: float, lon: float) -> dict:
    try:
        data = get_json("https://nominatim.openstreetmap.org/reverse",
                        {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10})
    except SourceUnavailable as exc:
        raise SourceUnavailable(f"backbone geocoder unreachable: {exc}") from exc
    addr = data.get("address", {})
    name = (addr.get("city") or addr.get("town") or addr.get("municipality")
            or addr.get("village") or addr.get("suburb") or addr.get("county"))
    return {"name": name, "admin_name": addr.get("state") or addr.get("county"),
            "admin_iso": addr.get("ISO3166-2-lvl4")}


def _corine_f2(ctx, prov):
    clc_code, clc_cat = eu.corine_at_point(ctx["lat"], ctx["lon"])
    prov["f2_crosscheck"] = {"primary": None, "primary_source": None,
                             "land_cover": clc_cat, "clc_code": clc_code, "agree": None,
                             "note": "no national legal-zoning source wired (EU-member v0)"}
    if clc_cat is None:
        return []
    return [{"id": "F2", "status": "measured", "value": clc_cat,
             "source": {"title": f"Corine Land Cover 2018 (EEA) — CLC code {clc_code} at point "
                                 f"(EU-wide; no national zoning source in v0)",
                        "url": eu.EEA_CORINE, "accessed": ctx["accessed"]}}]


def make_eu_member_spec(iso: str, *, e1: bool = True, natura: bool = True, f1_cdda: bool = False,
                        f2=None,
                        l3_ied: bool = False, extra_collectors: list | None = None,
                        summary: dict | None = None, extra_gaps: dict | None = None) -> dict:
    """The standard EU/EEA-member spatial spec, parameterized by ISO code (see module docstring).

    Per-country deltas stay declarative (no clones): `f1_cdda` uses the EEA CDDA layer for F1 where
    Natura 2000 does not apply (Norway); `l3_ied` wires the EEA IED Seveso flag (only for countries
    that populate it); `extra_collectors` appends national feeds (a country's grid map), each a
    (ids, fn) pair whose ids leave the gap set automatically. L1 income (Eurostat NUTS2) is NOT a
    flag here — it is frozen into the skeleton (country.build_draft) for every country."""
    iso_u = iso.upper()
    gaps = dict(_BASE_GAPS)
    gaps["L1"] = _L1_RAW_GAP
    if not e1:
        gaps["E1"] = "not_collected — energy-charts does not serve this synchronous zone; national TSO source (v1)"
    if not natura and not f1_cdda:
        gaps["F1"] = "not_collected — outside Natura 2000 (Emerald Network); a national protected-areas layer (v1)"
    if extra_gaps:
        gaps.update(extra_gaps)

    collectors = []
    if e1:
        collectors.append((("E1",),
            lambda ctx, prov, i=iso_u: [x] if (x := eu.collect_e1_energy_charts(i, ctx["accessed"])) else []))
    collectors.append((("W1",),
        lambda ctx, prov: [x] if (x := eu.collect_w1_aqueduct(ctx["lat"], ctx["lon"], ctx["accessed"])) else []))
    collectors.append((("W2",),
        lambda ctx, prov: [x] if (x := eu.collect_w2_universal(ctx["lat"], ctx["lon"], ctx["accessed"])) else []))
    if natura:
        collectors.append((("F1",),
            lambda ctx, prov: [x] if (x := eu.natura_rings(ctx["lat"], ctx["lon"], ctx["accessed"])) else []))
    elif f1_cdda:
        collectors.append((("F1",),
            lambda ctx, prov: [x] if (x := eu.cdda_rings(ctx["lat"], ctx["lon"], ctx["accessed"])) else []))
    # F2 defaults to Corine (EU-wide land cover). A country with real LEGAL zoning passes its own
    # collector here — better evidence, same slot, no clone (CH: ARE parcel-level building zones).
    collectors.append((("F2",), f2 or _corine_f2))
    if l3_ied:
        collectors.append((("L3",),
            lambda ctx, prov: [x] if (x := eu.collect_l3_ied_seveso(ctx["lat"], ctx["lon"], ctx["accessed"])) else []))
    collectors.extend(extra_collectors or [])

    collectable = {"E2", "E3", "W3", "L1", "L3"}
    if not e1:
        collectable.add("E1")
    if not natura and not f1_cdda:
        collectable.add("F1")
    if l3_ied:
        collectable.discard("L3")
    for ids, _fn in (extra_collectors or []):  # national feeds leave the gap set
        collectable.difference_update(ids)

    return {
        "iso": iso_u,
        "generator": f"pipelines.spatial.eu_member[{iso_u}] v0",
        "summary": summary or {
            "fr": f"BROUILLON {iso_u} v0 (socle EU : carbone réseau, masse d'eau, Natura, Corine) — à vérifier.",
            "en": f"{iso_u} DRAFT v0 (EU-level: grid carbon, water body, Natura, Corine) — verify before use.",
        },
        "fetch_commune": _nominatim_commune,
        "identity_fields": lambda c: {
            "municipality": c.get("name") or "UNKNOWN — to fill",
            **({"admin_area": c["admin_iso"].split("-", 1)[1]} if c.get("admin_iso") and "-" in c["admin_iso"] else {}),
        },
        "collectors": collectors,
        "collectable_gaps": frozenset(collectable),
        "provenance_commune": lambda c: {"admin_area_name": c.get("admin_name")},
        "provenance_extra": lambda ctx, prov: {"known_gaps": gaps,
                                               "f2_crosscheck": prov.get("f2_crosscheck")},
        "manual_still_required": ["F3", "L2", "T1", "T2"] + sorted(collectable),
    }
