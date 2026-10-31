#!/usr/bin/env python3
"""Encode one festival photo into the two sizes a gallery year needs.

    python3 tools/gallery-photo.py SOURCE STEM

writes assets/STEM.webp (the masonry thumbnail) and assets/STEM-lg.webp (what
the lightbox opens), and keeps the supplied file in image-originals/ as
STEM-original.<ext>.

The two sizes are not a guess: they are what the 77 photos of the 2026 set
already are, measured before the 2024 set was added. The thumbnail is a flat
700px WIDE whatever the orientation -- the masonry lays out in columns, so
width is the dimension that has to match and height is free. The large copy is
1800px on its LONG edge, so a portrait and a landscape open at the same area
rather than the same width.

Quality 84 was recovered the same way, by re-encoding nsf2026-01-original.jpg
across the range and matching the byte count of the file already in assets/.
Keep it: a gallery where half the years were encoded at a different quality is
a gallery that looks inconsistent at full screen.

photo_gallery_section() reads the thumbnail's real pixel size out of the file
and writes it into the <img>, because a lazy image with no width/height is
0px tall and the whole masonry collapses into the viewport at once. So the
thumbnail has to exist on disk before build.py runs.
"""
import os
import shutil
import sys
from PIL import Image

THUMB_W  = 700
LARGE_LONG = 1800
QUALITY  = 84

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(src, stem):
    im = Image.open(src).convert("RGB")

    # Never upscale. Enlarging adds no detail, only bytes.
    if im.width < THUMB_W or max(im.size) < LARGE_LONG:
        print("WARNING: %s is %dx%d, smaller than the %dpx thumbnail or the "
              "%dpx long edge.\n         It is encoded at its own size; ask "
              "for a larger original." % (src, im.width, im.height, THUMB_W,
                                          LARGE_LONG))

    out = []
    for suffix, (w, h) in (
            ("", (min(THUMB_W, im.width),
                  round(im.height * min(THUMB_W, im.width) / im.width))),
            ("-lg", (lambda s: (round(im.width * s), round(im.height * s)))(
                min(1.0, LARGE_LONG / max(im.size))))):
        path = os.path.join(ROOT, "assets", "%s%s.webp" % (stem, suffix))
        im.resize((w, h), Image.LANCZOS).save(
            path, "WEBP", quality=QUALITY, method=6)
        out.append((path, w, h, os.path.getsize(path)))

    keep = os.path.join(os.path.dirname(ROOT), "image-originals",
                        "%s-original%s" % (stem, os.path.splitext(src)[1]))
    os.makedirs(os.path.dirname(keep), exist_ok=True)
    shutil.copy2(src, keep)

    print("%-14s %s -> %s" % (stem, im.size, " + ".join(
        "%dx%d %.0fKB" % (w, h, n / 1024) for _, w, h, n in out)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
