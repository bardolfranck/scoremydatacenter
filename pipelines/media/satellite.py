# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Franck Bardol and contributors — ScoreMyDataCenter
# https://scoremydatacenter.org · independent data center acceptability-risk score
"""Satellite thumbnail per DC — brief 9-img-sat (2026-07-15) + doctrine A-28.

Coordinates from the corpus → Esri World Imagery XYZ tiles (free, no key)
→ crop centred on the EXACT world pixel of the point (never a tile corner)
→ auto zoom from the OSM building footprint (~70 % of the frame, clamp
z15-19, fallback z18) → A-28 signature cartouche BURNED into the image
(« scoremydatacenter.org · Esri, Maxar, Earthstar Geographics ») → WebP
1200×800 + 400×267 thumb → R2 under a non-enumerable key
`sat/{id}-{hmac8}.webp` (HMAC-SHA256 of the id, secret outside the repos).

Out-of-band job: never part of the deterministic engine build (the golden
never sees it); idempotent (existing R2 objects are skipped); network-polite
(one Esri fetch per missing DC, small delay).

    uv run python -m pipelines.media.satellite --limit 3          # dry local
    uv run python -m pipelines.media.satellite --upload           # + R2
Environment: SMDC_MEDIA_SECRET (HMAC key, required for real keys),
SMDC_MEDIA_BASE (public base URL, used by build_prod_artifacts).
"""

import argparse
import hashlib
import hmac
import io
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent.parent
TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "ScoreMyDataCenter-media/1.0 (contact@scoremydatacenter.org)"}
ATTRIBUTION = "scoremydatacenter.org · Esri, Maxar, Earthstar Geographics"
W, H = 1200, 800
THUMB_W, THUMB_H = 400, 267
BUCKET = "smdc-media"
OUT_DIR = REPO / ".media-sat"  # local staging, gitignored — R2 is the store
MANIFEST = OUT_DIR / "uploaded.txt"  # keys confirmed on R2 — skips 444 network probes
FONT = REPO / "site" / "src" / "og" / "fonts" / "chivo-mono-400.ttf"


def media_key(dc_id: str, secret: str) -> str:
    """Non-enumerable R2 key (A-28): sat/{id}-{hmac8}.webp."""
    digest = hmac.new(secret.encode(), dc_id.encode(), hashlib.sha256).hexdigest()[:8]
    return f"sat/{dc_id}-{digest}.webp"


def world_pixel(lon: float, lat: float, z: int) -> tuple[float, float]:
    """Web-Mercator world pixel of a point at zoom z (256px tiles)."""
    n = 2 ** z * 256
    x = (lon + 180.0) / 360.0 * n
    lat_r = math.radians(lat)
    y = (1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n
    return x, y


def zoom_for_bbox(south: float, west: float, north: float, east: float, lat: float) -> int:
    """z such that the footprint bbox fills ~70 % of the frame; clamp 15-19."""
    for z in range(19, 14, -1):
        x1, y1 = world_pixel(west, north, z)
        x2, y2 = world_pixel(east, south, z)
        if abs(x2 - x1) <= W * 0.7 and abs(y2 - y1) <= H * 0.7:
            return z
    return 15


def osm_footprint_zoom(lat: float, lon: float, timeout: int = 12) -> int:
    """Auto zoom from the OSM building footprint around the point; z18 fallback."""
    q = (f'[out:json][timeout:{timeout}];'
         f'way(around:120,{lat},{lon})["building"];out bb 1;')
    try:
        r = requests.post(OVERPASS_URL, data={"data": q}, headers=UA, timeout=timeout + 3)
        r.raise_for_status()
        els = r.json().get("elements", [])
        if els and "bounds" in els[0]:
            b = els[0]["bounds"]
            return zoom_for_bbox(b["minlat"], b["minlon"], b["maxlat"], b["maxlon"], lat)
    except Exception:
        pass  # Overpass is best-effort — the fallback zoom is always safe
    return 18


def fetch_tile(session: requests.Session, z: int, x: int, y: int) -> Image.Image:
    n = 2 ** z
    r = session.get(TILE_URL.format(z=z, x=x % n, y=y), headers=UA, timeout=20)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def centered_view(session: requests.Session, lat: float, lon: float, z: int) -> Image.Image:
    """Paste every intersecting tile at its world offset, crop the centred window."""
    cx, cy = world_pixel(lon, lat, z)
    left, top = cx - W / 2, cy - H / 2
    tx0, ty0 = int(left // 256), int(top // 256)
    tx1, ty1 = int((left + W) // 256), int((top + H) // 256)
    canvas = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            canvas.paste(fetch_tile(session, z, tx, ty), ((tx - tx0) * 256, (ty - ty0) * 256))
    ox, oy = int(left - tx0 * 256), int(top - ty0 * 256)
    return canvas.crop((ox, oy, ox + W, oy + H))


def burn_cartouche(img: Image.Image, scale: float = 1.0) -> Image.Image:
    """A-28: the signature travels IN the image — bottom strip, site + imagery credit."""
    draw = ImageDraw.Draw(img, "RGBA")
    size = max(int(13 * scale), 8)
    font = ImageFont.truetype(str(FONT), size)
    pad = max(int(6 * scale), 3)
    text = ATTRIBUTION
    box = draw.textbbox((0, 0), text, font=font)
    th = box[3] - box[1] + 2 * pad
    draw.rectangle([(0, img.height - th), (img.width, img.height)], fill=(16, 42, 67, 200))
    draw.text((max(int(10 * scale), 4), img.height - th + pad - box[1]), text,
              font=font, fill=(255, 255, 255, 235))
    return img


def r2_available() -> bool:
    """ONE probe before any batch: if R2 is unreachable (service not enabled,
    network down), abort politely instead of failing 444 times."""
    p = subprocess.run(["npx", "wrangler", "r2", "bucket", "list"],
                       cwd=REPO / "site", capture_output=True, text=True, timeout=60)
    return p.returncode == 0


def manifest_keys() -> set[str]:
    return set(MANIFEST.read_text().split()) if MANIFEST.is_file() else set()


def manifest_add(key: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    with MANIFEST.open("a") as f:
        f.write(key + "\n")


def r2_object_exists(key: str) -> bool:
    p = subprocess.run(["npx", "wrangler", "r2", "object", "get", f"{BUCKET}/{key}",
                        "--file", "/dev/null", "--remote"],
                       cwd=REPO / "site", capture_output=True, text=True)
    return p.returncode == 0


def r2_upload(key: str, path: Path) -> bool:
    p = subprocess.run(["npx", "wrangler", "r2", "object", "put", f"{BUCKET}/{key}",
                        "--file", str(path), "--content-type", "image/webp", "--remote"],
                       cwd=REPO / "site", capture_output=True, text=True)
    if p.returncode != 0:
        print(f"  R2 upload failed for {key}: {(p.stderr or p.stdout).strip().splitlines()[-1:]}",
              file=sys.stderr)
    return p.returncode == 0


def load_corpus() -> list[dict]:
    """The served artifacts are the source of truth for id + coordinates."""
    dcs = []
    for f in sorted((REPO / "site" / "public" / "data" / "dc").glob("*.json")):
        d = json.loads(f.read_text())
        if d["id"].startswith("zz-"):
            continue  # fixtures never get media (A-28 / no-fixtures-in-prod)
        dcs.append(d)
    geo = {f["properties"]["id"]: f["geometry"]["coordinates"]
           for f in json.loads((REPO / "site" / "public" / "data" / "map.geojson").read_text())["features"]}
    for d in dcs:
        d["_lonlat"] = geo.get(d["id"])
    return [d for d in dcs if d.get("_lonlat")]


def generate_one(session: requests.Session, dc: dict, secret: str) -> tuple[str, Path, Path]:
    lon, lat = dc["_lonlat"]
    z = osm_footprint_zoom(lat, lon)
    img = centered_view(session, lat, lon, z)
    img = burn_cartouche(img, scale=1.0)
    thumb = img.resize((THUMB_W, THUMB_H), Image.LANCZOS)
    thumb = burn_cartouche(thumb, scale=0.55)
    key = media_key(dc["id"], secret)
    OUT_DIR.mkdir(exist_ok=True)
    full_path = OUT_DIR / key.replace("sat/", "")
    thumb_path = OUT_DIR / key.replace("sat/", "").replace(".webp", "-thumb.webp")
    img.save(full_path, "WEBP", quality=82)
    thumb.save(thumb_path, "WEBP", quality=80)
    return key, full_path, thumb_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only the first N missing (0 = all)")
    ap.add_argument("--only", help="comma-separated dc ids")
    ap.add_argument("--upload", action="store_true", help="upload to R2 (needs the service enabled)")
    ap.add_argument("--delay", type=float, default=0.4, help="politeness delay between DCs (s)")
    args = ap.parse_args()

    secret = os.environ.get("SMDC_MEDIA_SECRET")
    if not secret:
        print("SMDC_MEDIA_SECRET missing (see ~/.smdc/media.env) — refusing to mint keys", file=sys.stderr)
        return 2

    dcs = load_corpus()
    if args.only:
        wanted = set(args.only.split(","))
        dcs = [d for d in dcs if d["id"] in wanted]

    if args.upload and not r2_available():
        print("media-sat: R2 unreachable (service not enabled?) — aborting before the batch", file=sys.stderr)
        return 1

    session = requests.Session()
    uploaded = manifest_keys()
    done = skipped = failed = 0
    for dc in dcs:
        key = media_key(dc["id"], secret)
        if args.upload and key in uploaded:
            skipped += 1
            continue
        if args.upload and r2_object_exists(key):
            manifest_add(key)
            skipped += 1
            continue
        # Local staging is reusable: a previous run's image never regenerates
        # (Esri politeness) — it just gets (re)uploaded.
        staged = OUT_DIR / key.replace("sat/", "")
        staged_thumb = OUT_DIR / key.replace("sat/", "").replace(".webp", "-thumb.webp")
        if staged.is_file() and staged_thumb.is_file():
            if args.upload:
                ok = r2_upload(key, staged) and r2_upload(key.replace(".webp", "-thumb.webp"), staged_thumb)
                if ok:
                    manifest_add(key)
                failed += 0 if ok else 1
                done += 1 if ok else 0
            else:
                skipped += 1
            continue
        try:
            key, full_path, thumb_path = generate_one(session, dc, secret)
        except Exception as e:  # noqa: BLE001 — one bad site never kills the batch
            print(f"  {dc['id']}: generation failed ({e})", file=sys.stderr)
            failed += 1
            continue
        if args.upload:
            ok = r2_upload(key, full_path) and r2_upload(key.replace(".webp", "-thumb.webp"), thumb_path)
            if ok:
                manifest_add(key)
            failed += 0 if ok else 1
            done += 1 if ok else 0
        else:
            done += 1
        print(f"  {dc['id']} → {key} (z auto)")
        if args.limit and done >= args.limit:
            break
        time.sleep(args.delay)
    print(f"media-sat: {done} generated, {skipped} already on R2, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
