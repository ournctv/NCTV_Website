#!/usr/bin/env python3
"""Darken a sponsor banner's background field without touching its logos.

    python3 tools/banner-darken.py SRC DST --by 15 --keep CX,CY,R [--keep ...]

SRC is the artwork as supplied, DST the WebP to write. `--by` is the
percentage taken off the field, applied to the sRGB values: --by 15 multiplies
them by 0.85, which is the operation quoted when a contrast reading is
reported. Each `--keep` is a disc, in the artwork's own pixels, left exactly
as it is -- that is where a sponsor's own mark sits, and a brand colour is not
ours to shift.

Outside those discs the amount is weighted by how white the pixel is, so the
caption keeps its white while the field behind it darkens, and the two blend
smoothly through the type's antialiasing instead of leaving a halo. The ramp
runs from FIELD_MAX (fully field) to TEXT_MIN (fully text); read the real
figures off the artwork before changing them.

Prints the caption's measured contrast before and after, since raising it is
the only reason to run this.
"""
import argparse
import statistics
import sys

from PIL import Image

FIELD_MAX = 125   # the field's lightest min-channel, measured on the artwork
TEXT_MIN = 235    # below the white caption's core, above every field pixel


def luminance(c):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + .05) / (min(la, lb) + .05)


def caption_reading(px, box):
    """White glyphs against the field they sit on, as a contrast ratio."""
    x1, y1, x2, y2 = box
    glyph, field = [], []
    for y in range(y1, y2):
        for x in range(x1, x2):
            p = px[x, y][:3]
            (glyph if min(p) > 235 else field).append(p)
    if not glyph or not field:
        sys.exit("no caption found in %r" % (box,))
    field.sort(key=luminance)
    gl = tuple(int(statistics.median(c[i] for c in glyph)) for i in range(3))
    return (contrast(gl, field[len(field) // 2]),
            contrast(gl, field[int(len(field) * .90)]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--by", type=float, required=True,
                    help="percent taken off the field's sRGB values")
    ap.add_argument("--keep", action="append", default=[], metavar="CX,CY,R",
                    help="a disc to leave untouched; repeatable")
    ap.add_argument("--caption", default="170,190,870,360", metavar="X1,Y1,X2,Y2",
                    help="where the white caption sits, for the contrast reading")
    ap.add_argument("--quality", type=int, default=88)
    args = ap.parse_args()

    discs = []
    for k in args.keep:
        cx, cy, r = (float(v) for v in k.split(","))
        discs.append((cx, cy, (r - 3) ** 2))
    box = tuple(int(v) for v in args.caption.split(","))
    k = 1.0 - args.by / 100.0

    im = Image.open(args.src).convert("RGBA")
    W, H = im.size
    px = im.load()
    before = caption_reading(px, box)

    span = TEXT_MIN - FIELD_MAX
    touched = 0
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if any((x - cx) ** 2 + (y - cy) ** 2 < rr for cx, cy, rr in discs):
                continue
            w = (TEXT_MIN - min(r, g, b)) / span
            w = 0.0 if w < 0 else (1.0 if w > 1 else w)
            if w == 0.0:
                continue
            f = 1.0 - (1.0 - k) * w
            px[x, y] = (round(r * f), round(g * f), round(b * f), a)
            touched += 1

    after = caption_reading(px, box)
    im.save(args.dst, "WEBP", quality=args.quality, method=6)
    print(f"{args.src} -> {args.dst}  {W}x{H}  {args.by:g}% off {touched} px")
    print(f"  caption contrast  median {before[0]:.2f}:1 -> {after[0]:.2f}:1"
          f"   lightest decile {before[1]:.2f}:1 -> {after[1]:.2f}:1")
    print("  WCAG asks 3:1 for large text" +
          ("" if after[1] >= 3 else "  <- the light end is still short"))


if __name__ == "__main__":
    main()
