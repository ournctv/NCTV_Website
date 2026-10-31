#!/usr/bin/env python3
"""Build assets/og-card.jpg -- the picture Facebook, Instagram, iMessage and
X show when someone shares a link to this site.

Run from the project root:  python3 tools/og-card.py

Facebook's recommended share image is 1200x630 (1.91:1). The source photo is
the front-door original at 2000x1500 (4:3), so it is cropped to that ratio
rather than squashed, then the white NCTV mark is laid over a bottom scrim so
a shared card is recognisable as NCTV at thumbnail size.

It reads the original from ../image-originals/, outside the repo, because the
in-repo assets/front-door.webp was deleted in 2026-10 when the banner
fallbacks became stills of their own videos and nothing on the site used that
photo any more. The share card still wants the building, so the original is
the source now. If image-originals is not beside the project, this tool
cannot run; nothing else depends on it, and the card it writes is committed.

JPEG, not WebP: every scraper reads JPEG, and some older ones still do not
read WebP. This is the one JPEG on the site for that reason.
"""
import os
from PIL import Image

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTO = os.path.join(ROOT, "..", "image-originals", "front-door.jpg")
MARK  = os.path.join(ROOT, "assets", "nctv-logo-whitetext.webp")
OUT   = os.path.join(ROOT, "assets", "og-card.jpg")

W, H       = 1200, 630
FOCUS_Y    = 0.38   # this photo's own focal point; the hero is centred now
MARK_H     = 88     # rendered height of the logo, in card pixels
MARGIN     = 52
SCRIM_TOP  = 0.46   # the scrim starts just above the midline and deepens to the foot
SCRIM_MAX  = 0.86

photo = Image.open(PHOTO).convert("RGB")
pw, ph = photo.size

# Crop to 1.91:1 taking the full width, centred on the focal point and then
# pushed back inside the frame if that would run off an edge.
ch = round(pw * H / W)
assert ch <= ph, "source is too wide to crop to %dx%d: %dx%d" % (W, H, pw, ph)
top = min(max(round(ph * FOCUS_Y) - ch // 2, 0), ph - ch)
card = photo.crop((0, top, pw, top + ch)).resize((W, H), Image.LANCZOS)

# Bottom scrim, one row at a time: cheaper than building a gradient image and
# exact about where it starts.
px = card.load()
y0 = round(H * SCRIM_TOP)
for y in range(y0, H):
    a = SCRIM_MAX * (y - y0) / (H - 1 - y0)
    for x in range(W):
        r, g, b = px[x, y]
        px[x, y] = (round(r * (1 - a)), round(g * (1 - a)), round(b * (1 - a)))

mark = Image.open(MARK).convert("RGBA")
mw = round(mark.width * MARK_H / mark.height)
card.paste(mark.resize((mw, MARK_H), Image.LANCZOS),
           (MARGIN, H - MARGIN - MARK_H),
           mark.resize((mw, MARK_H), Image.LANCZOS))

card.save(OUT, "JPEG", quality=86, optimize=True, progressive=True)
print("wrote %s  %dx%d  %.0f KB" % (OUT, W, H, os.path.getsize(OUT) / 1024))
