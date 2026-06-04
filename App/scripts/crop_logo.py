"""Crop App/backend/static/aqua_solutions_logo.png to droplet-only with
transparent background.

Usage: python scripts/crop_logo.py

Reads the original logo (3414 x 1584) and writes
App/backend/static/aqua_solutions_drop.png. The crop bounding box was
chosen by visual inspection — the droplet sits in the upper-left
~12% of the source image. Near-white pixels (R, G, B all >= 240)
become transparent so the result can sit on any background.

If the crop is off (droplet clipped or wordmark leaking in), adjust
the percentage constants in crop_drop() and re-run; the script is
idempotent — it always reads the original and overwrites the cropped
output.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "App/backend/static/aqua_solutions_logo.png"
DST = REPO_ROOT / "App/backend/static/aqua_solutions_drop.png"
WHITE_THRESHOLD = 240


def crop_drop(img: Image.Image) -> Image.Image:
    """Return a generous sub-image that contains only the droplet (and
    surrounding whitespace). The wordmark and tagline are NOT inside
    this region, so the white-knockout-then-getbbox step at the end
    can tighten to the droplet outline."""
    w, h = img.size
    left = int(w * 0.01)
    upper = int(h * 0.02)
    right = int(w * 0.16)
    lower = int(h * 0.85)
    return img.crop((left, upper, right, lower))


def make_transparent(img: Image.Image, threshold: int = WHITE_THRESHOLD) -> Image.Image:
    """Convert near-white pixels to transparent."""
    rgba = img.convert("RGBA")
    pixels = list(rgba.getdata())
    new_pixels = [
        (r, g, b, 0) if (r >= threshold and g >= threshold and b >= threshold) else (r, g, b, a)
        for r, g, b, a in pixels
    ]
    rgba.putdata(new_pixels)
    return rgba


def main() -> None:
    src = Image.open(SRC)
    cropped = crop_drop(src)
    transparent = make_transparent(cropped)
    # Tighten to the actual droplet bounding box: any rows/columns that
    # are entirely transparent after the knockout get trimmed.
    bbox = transparent.getbbox()
    if bbox is None:
        raise SystemExit("getbbox() returned None — no opaque pixels in crop")
    tight = transparent.crop(bbox)
    tight.save(DST, "PNG")
    print(f"Wrote {DST.relative_to(REPO_ROOT)} ({tight.size[0]}x{tight.size[1]})")


if __name__ == "__main__":
    main()
