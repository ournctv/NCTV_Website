#!/usr/bin/env python3
"""Cut a film-strip banner down to its narrow-screen crops.

    python3 tools/crop-banner.py            # Gov_Banner, the Civic TV strip
    python3 tools/crop-banner.py Sports_Banner

reads assets/STEM.webp and writes assets/STEM-md.webp, -sm.webp and -xs.webp
beside it, then checks that build.py still states the widths it just wrote.

The artwork is a strip of film holding five or so photo frames at roughly
4.66:1. Scaled down to a phone that is 80px tall and nothing inside the frames
survives, so the narrow sizes drop whole frames off the right instead of
shrinking them -- spending width the phone has not got to buy back height it
has.

**Nothing here is hard coded to one banner.** The script finds the strip
colour, the photo band and the gutters between frames by looking at the file,
then derives the crop widths from them. That is deliberate: the Civic artwork
was replaced twice on 2026-10-30, the second time swapping a #444 strip for a
black one and moving every frame boundary, and hand-written numbers would have
cut the new banner in the wrong places while still producing files that looked
perfectly fine. Run this after any artwork swap and read what it prints.

**Each crop drops exactly one more whole frame off the right**, which is why
the cuts are counted back from the end of the strip rather than forward from
its start. The two banners differ at the start and would disagree if they were
counted that way: Gov_Banner opens with 9px of strip before its first frame,
Sports_Banner opens in the middle of a picture. Counting from the right also
makes the widths come out the same for both, the two being the same template.

A crop never ends on a gutter. Neither master does -- each runs some way into
its last frame, so the strip reads as continuing past the edge of the page --
and every crop copies that same sliver, so all four sizes end the same way.

Quality 90 rather than the 84 the photo galleries use, because this is a second
generation: the master is already a lossy WebP and there is no better source.
The cut is left-anchored and full height, so it is a pixel-exact copy on the
same macroblock grid and the re-encode is close to an identity at that quality.
Resampling here instead -- a resize down to the display width -- would show.
"""

import os
import sys
from collections import Counter

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The three crops, widest first, each one whole frame narrower than the last.
SUFFIXES = ["-md.webp", "-sm.webp", "-xs.webp"]

TOL = 45          # how far off the strip colour a pixel has to be to be picture
MIN_GUTTER = 8    # narrower runs of strip colour are shadows inside a photo


def measure(im):
    """Find the strip colour, the photo band and the frame boundaries."""
    w, h = im.size
    px = im.load()

    # The top edge of the artwork is always strip, never picture -- but one
    # pixel of it is not a safe sample. Sports_Banner's midpoint at row 2 is a
    # half-transparent (17,24,37) against a strip that is really (13,24,38),
    # and a sample that landed on something bright would invert the whole
    # measurement. Take the commonest fully opaque colour across the top rows.
    band = [px[x, y] for y in range(1, 6) for x in range(0, w, 2)]
    opaque = [p for p in band if len(p) < 4 or p[3] == 255] or band
    strip = Counter(p[:3] for p in opaque).most_common(1)[0][0]
    off = lambda p: max(abs(p[i] - strip[i]) for i in range(3)) > TOL

    # The photo band is the run of rows where most of the width is picture.
    # Sprocket holes are bright but sparse, so they never clear the half mark.
    rows = [y for y in range(h)
            if sum(off(px[x, y]) for x in range(0, w, 3)) > len(range(0, w, 3)) * 0.5]
    if not rows:
        return None
    # The LONGEST run of those rows, not the first to the last. A banner can
    # carry a stray bright line at its very edge -- nonprofit-banner's row 0 is
    # (222,228,235) right across, which is the 1px transparent top row the
    # other three have, flattened on export. Taking rows[0] put `top` at 0,
    # which pulled the gutter scan up through the sprocket holes and lost two
    # of the five gutters. One pixel at the edge is never the photo band.
    runs = []
    for y in rows:
        if runs and y == runs[-1][1] + 1:
            runs[-1][1] = y
        else:
            runs.append([y, y])
    top, bot = max(runs, key=lambda r: r[1] - r[0])

    # Inside that band, a column that is strip colour all the way down is a
    # gutter between two frames (or the margin at either end).
    band = range(top + 6, bot - 5, 4)
    cols = [x for x in range(w) if not any(off(px[x, y]) for y in band)]
    runs = []
    for x in cols:
        if runs and x == runs[-1][1] + 1:
            runs[-1][1] = x
        else:
            runs.append([x, x])
    runs = [r for r in runs if r[1] - r[0] + 1 >= MIN_GUTTER]

    starts = [r[1] + 1 for r in runs]           # first picture column of each frame
    return strip, (top, bot), runs, starts


def whole_frames(gutters, cut):
    """How many frames a crop of this width shows with both their edges."""
    return sum(1 for i in range(len(gutters) - 1) if gutters[i + 1][0] < cut)


def main():
    stem = sys.argv[1] if len(sys.argv) > 1 else "Gov_Banner"
    src = os.path.join(ROOT, "assets", stem + ".webp")
    if not os.path.exists(src):
        sys.exit("no such banner: %s" % src)

    im = Image.open(src)
    w, h = im.size
    found = measure(im)
    if found is None:
        sys.exit("found no photo band in %s -- is it a film strip at all?" % src)
    strip, (top, bot), gutters, starts = found

    # Three crops need three frames to drop plus one to keep, and the sliver is
    # measured from the last boundary, so five boundaries is the floor.
    if len(starts) < 5:
        sys.exit("found only %d frame boundaries in %s; expected at least 5. "
                 "Check the artwork before trusting any crop." % (len(starts), src))

    sliver = w - starts[-1]            # how far the master runs into its last frame
    opens = "mid-picture" if gutters[0][0] > 0 else "with %dpx of strip" % (gutters[0][1] + 1)
    print("master      %dx%d  strip %s  photo band y%d-%d  opens %s"
          % (w, h, strip, top, bot, opens))
    print("gutters     %s" % " ".join("%d-%d" % (a, b) for a, b in gutters))
    print("frames      %s" % " ".join(str(s) for s in starts))
    print("sliver      %dpx into the last frame -- every crop ends the same way\n" % sliver)

    written = {}
    for i, suffix in enumerate(SUFFIXES):
        cut = starts[-2 - i] + sliver
        if cut >= w:
            sys.exit("the %s crop would be %dpx, no narrower than the master" % (suffix, cut))
        name = stem + suffix
        path = os.path.join(ROOT, "assets", name)
        im.crop((0, 0, cut, h)).save(path, "WEBP", quality=90, method=6)
        written[name] = cut
        print("%-22s %4dx%-4d %7d bytes   %d whole frames + sliver"
              % (name, cut, h, os.path.getsize(path), whole_frames(gutters, cut)))
    print("%-22s %4dx%-4d %7d bytes   %d whole frames + sliver   (the master, untouched)"
          % (stem + ".webp", w, h, os.path.getsize(src), whole_frames(gutters, w)))

    # Close the loop: the widths live in the markup too, and a crop whose
    # <source> claims the wrong pixels makes the page jump as it loads.
    build = open(os.path.join(ROOT, "build.py"), encoding="utf-8").read()
    stale = [(n, c) for n, c in list(written.items()) + [(stem + ".webp", w)]
             if 'assets/%s?v={ASSET_VER}" width="%d" height="%d"' % (n, c, h) not in build]
    if stale:
        print("\nbuild.py does NOT state these -- fix the banner markup before shipping:")
        for n, c in stale:
            print('    assets/%s?v={ASSET_VER}" width="%d" height="%d"' % (n, c, h))
        sys.exit(1)
    print("\nbuild.py states all four correctly.")


if __name__ == "__main__":
    main()
