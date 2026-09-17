"""Dedup brick: spatial + nominal candidate matching against the existing corpus."""

from pipelines.dedup import coords_of, haversine_km, name_matches, near_existing

# Two records, two storage shapes: a panel (identity-nested) and a watchlist entry (top-level).
PANEL = {"identity": {"name": "Fouju A", "operator": "Acme", "municipality": "Fouju",
                      "coordinates": {"lat": 48.60, "lon": 2.78}}}
WATCH = {"name": "Marne B", "operator": "Globex", "municipality": "Marne-la-Vallée",
         "coordinates": {"lat": 48.85, "lon": 2.60}}
CORPUS = [PANEL, WATCH]


def test_coords_of_reads_both_shapes():
    assert coords_of(PANEL) == (48.60, 2.78)
    assert coords_of(WATCH) == (48.85, 2.60)
    assert coords_of({"identity": {}}) is None          # no coords → unmatchable, not a crash
    assert coords_of({"coordinates": {"lat": "x"}}) is None  # malformed → None


def test_haversine_km_sane():
    # Paris ↔ ~1 km north: within a few metres of 1 km.
    d = haversine_km(48.8566, 2.3522, 48.8656, 2.3522)
    assert 0.99 < d < 1.02


def test_near_existing_flags_duplicate_within_radius():
    # A candidate 300 m from the Fouju panel → same site.
    hits = near_existing(48.6027, 2.78, CORPUS, km=2.0)
    assert len(hits) == 1
    assert hits[0]["identity"]["name"] == "Fouju A"
    assert hits[0]["_distance_km"] < 0.5           # annotation present, small


def test_near_existing_ignores_far_candidate():
    # A candidate in Marseille matches nothing in an Île-de-France corpus.
    assert near_existing(43.30, 5.37, CORPUS, km=2.0) == []


def test_near_existing_skips_records_without_coords():
    corpus = [{"identity": {"name": "no-geo"}}, PANEL]
    hits = near_existing(48.6027, 2.78, corpus, km=2.0)
    assert [h["identity"]["name"] for h in hits] == ["Fouju A"]


def test_name_matches_requires_both_commune_and_operator():
    # Same commune + same operator (case/spacing-insensitive) → match.
    assert name_matches("fouju", "ACME", CORPUS)
    # Same commune, different operator → not a duplicate (one town, many sites).
    assert name_matches("Fouju", "Other Corp", CORPUS) == []
    # Empty operator never matches (absence is not agreement).
    assert name_matches("Fouju", "", CORPUS) == []
