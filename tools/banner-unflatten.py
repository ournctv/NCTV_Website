#!/usr/bin/env python3
"""Put a film-strip banner's sprocket holes back to transparent.

    python3 tools/banner-unflatten.py SRC DST

The four film-strip banners are cut out: the holes are transparent, so they
show `--fog` through the page and read as soft grey perforation. An export
that flattens the artwork fills them with white instead, and nothing about the
file then looks wrong -- it is a valid WebP of a film strip, just one whose
holes are brighter than the three beside it.

`nonprofit-banner` arrived that way on 2026-10-30: RGB with no alpha channel
at all, holes at pure (255,255,255), and a 1px line of (222,228,235) across
row 0 where the other three have a transparent row. Both are flatten
artifacts, not design.

**This unblends rather than keys.** A flattened hole is `white OVER strip`, so
how far a pixel has travelled from the strip colour toward white *is* its
coverage, antialiasing included. Setting alpha to the inverse of that and the
colour back to strip reproduces the cut-out exactly, soft edges and all. A
plain threshold would give hard, jagged holes.

**Only outside the photo band, and not within MARGIN of it.** The band is
found the same way tools/crop-banner.py finds it, and nothing inside it is
touched -- a white wall or a bright sky in a frame is picture, not
perforation. The margin matters as much as the band: a light photo bleeds a
pixel or two past the boundary, and without it rows 81 and 344-345 of
nonprofit-banner came out down to alpha 38, which is a faint light speckle
drawn the whole way along the top and bottom of the frames. There is a clear
run of strip either side -- 18 rows above, 23 below -- so 8 costs nothing.

Compare the result against a banner that was never flattened before shipping
it: the transparent fraction should land near 9%, and the holes should come
out 30 to a band.
"""

import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MARGIN = 8        # rows either side of the photo band that are picture too
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from importlib.machinery import SourceFileLoader

_cb = SourceFileLoader("_cb", os.path.join(ROOT, "tools", "crop-banner.py")).load_module()


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip().split("\n\n")[1].strip())
    src, dst = sys.argv[1], sys.argv[2]

    im = Image.open(src)
    if "A" in im.getbands() and min(im.getchannel("A").getdata()) < 250:
        sys.exit("%s already has transparency -- nothing to unflatten" % src)
    im = im.convert("RGB")
    w, h = im.size

    found = _cb.measure(im)
    if found is None:
        sys.exit("found no photo band in %s -- is it a film strip at all?" % src)
    strip, (top, bot), _gutters, _starts = found

    out = im.convert("RGBA")
    px, op = im.load(), out.load()
    # How far white is from the strip, per channel, as the denominator of the
    # coverage. Read it rather than assuming 255 minus the strip.
    span = [255 - strip[i] for i in range(3)]
    touched = 0
    for y in range(h):
        if top - MARGIN <= y <= bot + MARGIN:
            continue                      # picture, never perforation
        for x in range(w):
            p = px[x, y]
            # Coverage is the smallest per-channel travel toward white, so a
            # pixel that is bright in only one channel is colour, not a hole.
            t = min((p[i] - strip[i]) / span[i] if span[i] else 0.0 for i in range(3))
            if t <= 0.02:
                continue
            t = min(t, 1.0)
            op[x, y] = (strip[0], strip[1], strip[2], int(round(255 * (1 - t))))
            touched += 1

    out.save(dst, "WEBP", quality=90, method=6, lossless=False)

    chk = Image.open(dst)
    a = chk.getchannel("A")
    frac = sum(1 for v in a.getdata() if v < 128) / (chk.width * chk.height)
    # Count a pixel as hole at half coverage, not at exactly 0: the holes are
    # antialiased, so their edge pixels sit at alpha 1 or 2 and counting on
    # equality double-counts every hole.
    clear = lambda x, y: a.getpixel((x, y)) < 128
    bands, rows = [], [y for y in range(h) if any(clear(x, y) for x in range(w))]
    for y in rows:
        if bands and y == bands[-1][1] + 1:
            bands[-1][1] = y
        else:
            bands.append([y, y])
    print("%s  %dx%d  strip %s  photo band y%d-%d" % (os.path.basename(src), w, h, strip, top, bot))
    print("touched     %d pixels, all of them outside the photo band" % touched)
    print("bands       %s" % " ".join("y%d-%d" % (a_, b_) for a_, b_ in bands))
    for a_, b_ in bands:
        if b_ - a_ < 3:
            continue
        y = (a_ + b_) // 2
        n = sum(1 for x in range(1, w) if clear(x, y) != clear(x - 1, y))
        print("            y=%d holds %d holes" % (y, (n + 1) // 2))
    print("transparent %.1f%% -- the three cut-out banners sit at 8.8 to 9.1%%" % (frac * 100))
    # Two fat bands and nothing else. A thin one anywhere but the very top
    # edge is a photo bleeding past the band, not a row of holes.
    stray = [b for b in bands if b[1] - b[0] < 4 and b[0] > 1]
    if stray:
        sys.exit("\nstray thin transparent band(s) at %s -- raise MARGIN and run again"
                 % ", ".join("y%d-%d" % (a_, b_) for a_, b_ in stray))
    if len([b for b in bands if b[1] - b[0] >= 4]) != 2:
        sys.exit("\nexpected exactly two hole bands; check the artwork")
    print("wrote       %s (%d bytes)" % (dst, os.path.getsize(dst)))


if __name__ == "__main__":
    main()
