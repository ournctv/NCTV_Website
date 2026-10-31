#!/usr/bin/env python3
"""Turn a title card or film still into a poster for a film panel.

    python3 tools/film-poster.py SOURCE SLUG [--pad]
            [--16x9 [--left|--right] [--top|--bottom]]

writes assets/SLUG-poster.webp and keeps the supplied file in
image-originals/. Frank sends these as frame grabs, so they usually arrive
letterboxed inside a 4:3 or square frame; the bars are stripped before the
resize, or the poster ends up mostly black.

--pad does the opposite, for a title card that arrives trimmed to its text:
it pads the short axis out to 16:9 in the colour already on the border, which
puts the card back the size it was in the film rather than cropping it
tighter. Trimming such a card would cut it to the bounding box of the words.

--16x9 forces the centred exact-16:9 crop that snap() otherwise applies only
to a frame that is already within 3% of it. Use it when Frank says a poster
is 16:9 and the file is not -- Stick Shadow Path arrived 640x416 (1.538:1).

--left and --right take the crop from that edge instead of the middle, for a
frame whose title sits off to one side. The One Star Weekend is 2000x900 with
its title running to x=1892: centred, the crop ends at x=1800 and cuts the
word in half; --right keeps x=400..2000 and loses only the porch railing.
Measure where the title ends before choosing -- do not eyeball it.

--top and --bottom do the same on the other axis, for a 4:3 frame whose
subject is not in the middle of it. The Keeper is 1446x1088 and loses 275
rows: the lamp burst runs y=150..230, so a centred crop starts at y=137 and
shaves the halo, while the bottom 188 rows are unlit foreground at a mean
brightness of 0.4. --top keeps y=0..812 and throws away only the black.
The two axes are independent; one of each may be given.

The output is never wider than the source. An upscale adds no detail, only
bytes, and the warning it prints is worth acting on: ask Frank for a larger
original rather than shipping a soft poster.

920px wide is twice the poster's rendered maximum on the Shorts Fest page
(`.shorts-selection .movie-poster`, clamp(280px,40vw,460px) in styles.css),
and every image on this site is encoded at twice its rendered width for
high-density screens.
"""
import os
import shutil
import sys
from PIL import Image

WIDTH   = 920
QUALITY = 88
TOL     = 6     # a "black" bar is rarely pure black -- 27/255 is typical
STEP    = 3     # sample every third pixel along a line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def content_box(im):
    """The picture inside the letterbox bars, as a crop box.

    A bar is a run of lines that are all one flat colour. Each line is
    compared against the outermost line rather than against black, so a grey
    or coloured mat is stripped too."""
    w, h = im.size
    px = im.load()

    def flat(line, ref):
        return all(abs(c - r) <= TOL for p, q in zip(line, ref) for c, r in zip(p, q))

    def row(y):   return [px[x, y] for x in range(0, w, STEP)]
    def col(x):   return [px[x, y] for y in range(0, h, STEP)]

    top, ref = 0, row(0)
    while top < h - 1 and flat(row(top), ref):
        top += 1
    bot, ref = h - 1, row(h - 1)
    while bot > top and flat(row(bot), ref):
        bot -= 1

    left, ref = 0, col(0)
    while left < w - 1 and flat(col(left), ref):
        left += 1
    right, ref = w - 1, col(w - 1)
    while right > left and flat(col(right), ref):
        right -= 1

    # A picture with no bars scans to nothing on that axis; keep it whole.
    if bot <= top or right <= left:
        return (0, 0, w, h)
    return snap(w, h, (left, top, right + 1, bot + 1))


def snap(w, h, box, target=16 / 9, tol=0.03, anchor="center",
         vanchor="center"):
    """Square up a crop that is nearly 16:9.

    Bar detection lands a few pixels inside the picture -- JPEG ringing along
    the edge of a bar is not quite flat -- and those few pixels are enough to
    make the output 1.765:1 instead of 1.778:1. That is a visible stretch on a
    face. When the detected box is within `tol` of 16:9 the frame really is
    16:9, so take the largest exact-ratio box that fits, centred on what was
    detected. A genuinely portrait poster is nowhere near the ratio and is
    returned untouched."""
    l, t, r, b = box
    if abs((r - l) / (b - t) / target - 1) > tol:
        return box
    cw = w
    ch = round(cw / target)
    if ch > h:
        ch, cw = h, round(h * target)
    cx, cy = (l + r) // 2, (t + b) // 2
    if anchor == "left":
        l = 0
    elif anchor == "right":
        l = w - cw
    else:
        l = min(max(cx - cw // 2, 0), w - cw)
    if vanchor == "top":
        t = 0
    elif vanchor == "bottom":
        t = h - ch
    else:
        t = min(max(cy - ch // 2, 0), h - ch)
    return (l, t, l + cw, t + ch)


def pad_box(im, target=16 / 9):
    """A crop box larger than the image, for the pad path.

    PIL crops outside the bounds happily and fills with black, which is what
    a title card wants, but the fill is only right when the border really is
    black -- so the caller checks that first."""
    w, h = im.size
    ch = round(w / target)
    if ch < h:                      # already wider than 16:9; pad the width
        cw, ch = round(h * target), h
        off = (cw - w) // 2
        return (-off, 0, cw - off, h)
    off = (ch - h) // 2
    return (0, -off, w, ch - off)


def main(src, slug, pad=False, force169=False, anchor="center",
         vanchor="center"):
    src_size = Image.open(src).size
    im = Image.open(src).convert("RGB")
    if pad:
        box = pad_box(im)
        edge = im.getpixel((0, 0))
        assert all(c <= TOL for c in edge), (
            "--pad fills with black, but this image's corner is %s. Pad it by "
            "hand, or the card will sit on a black band." % (edge,))
    elif force169:
        box = snap(im.width, im.height, (0, 0, im.width, im.height), tol=1,
                   anchor=anchor, vanchor=vanchor)
    else:
        box = content_box(im)
    im = im.crop(box)

    # Never upscale. A 920px poster made from a 640px source is 920px of the
    # same detail and a bigger file; the right fix is a larger original.
    width = min(WIDTH, im.width)
    if width < WIDTH:
        print("WARNING: source is only %dpx wide after the crop, so the poster "
              "is %dpx, not %d.\n         It renders at 460px, so this is "
              "%.2fx density where the site's standard is 2x.\n         Ask "
              "for a larger original." % (im.width, width, WIDTH, width / 460))

    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)

    out = os.path.join(ROOT, "assets", "%s-poster.webp" % slug)
    im.save(out, "WEBP", quality=QUALITY, method=6)

    keep = os.path.join(os.path.dirname(ROOT), "image-originals",
                        "%s-poster-source%s" % (slug, os.path.splitext(src)[1]))
    os.makedirs(os.path.dirname(keep), exist_ok=True)
    shutil.copy2(src, keep)

    print("source %s  content %s" % (src_size, box))
    print("wrote  %s  %dx%d  %.0f KB  (%.3f:1)"
          % (out, width, h, os.path.getsize(out) / 1024, width / h))
    print("kept   %s" % keep)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    known = {"--pad", "--16x9", "--left", "--right", "--top", "--bottom"}
    anchors = flags & {"--left", "--right"}
    vanchors = flags & {"--top", "--bottom"}
    if (len(args) != 2 or flags - known
            or flags >= {"--pad", "--16x9"}
            or len(anchors) > 1 or len(vanchors) > 1
            or ((anchors or vanchors) and "--16x9" not in flags)):
        sys.exit(__doc__)
    main(args[0], args[1], pad="--pad" in flags, force169="--16x9" in flags,
         anchor=anchors.pop()[2:] if anchors else "center",
         vanchor=vanchors.pop()[2:] if vanchors else "center")
