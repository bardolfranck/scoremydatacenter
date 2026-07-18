# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Satellite media pipeline — network-free invariants (brief 9-img-sat, A-28)."""

from pipelines.media.satellite import media_key, world_pixel, zoom_for_bbox


def test_media_key_non_enumerable_and_deterministic():
    a = media_key("fr-data4-campus-paris-saclay", "secret-1")
    b = media_key("fr-data4-campus-paris-saclay", "secret-1")
    c = media_key("fr-data4-campus-paris-saclay", "secret-2")
    assert a == b                      # deterministic: the build recomputes it
    assert a != c                      # secret-dependent: no secret, no key
    assert a.startswith("sat/fr-data4-campus-paris-saclay-") and a.endswith(".webp")
    assert len(a.split("-")[-1]) == len("12345678.webp")  # hmac8


def test_world_pixel_centering_math():
    # lon 0 / lat 0 sits exactly at the middle of the world canvas
    x, y = world_pixel(0.0, 0.0, 3)
    assert abs(x - (2 ** 3 * 256) / 2) < 1e-6
    assert abs(y - (2 ** 3 * 256) / 2) < 1e-6


def test_zoom_for_bbox_clamps_and_fits():
    # a tiny footprint gets the max zoom, a huge one the min clamp
    assert zoom_for_bbox(48.7000, 2.1900, 48.7004, 2.1904, 48.7) == 19
    assert zoom_for_bbox(48.700, 2.190, 48.701, 2.191, 48.7) == 18
    assert zoom_for_bbox(48.0, 1.0, 49.0, 3.0, 48.5) == 15
