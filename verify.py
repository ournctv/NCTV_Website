#!/usr/bin/env python3
"""verify.py -- the checks CLAUDE.md describes, made runnable.

Read-only. It inspects the *built* site, so run `python3 build.py` first:

    python3 build.py && python3 verify.py

    python3 verify.py --list          # name every check
    python3 verify.py banner sponsor  # run only checks whose name matches

Each check returns a list of failure strings; an empty list is a pass. The
exit status is 1 if anything failed, so it can gate a commit.

Why these checks and not others: every one of them guards something that
looks completely normal when it is wrong. A hotspot that has slid off its
logo is still valid markup. A crop left over from a superseded banner is
still a real image. A description that lost its joining space still builds.
None of it shows up in a page that renders, which is why it is worth a
script rather than a look.
"""

import ast
import collections
import math
import os
import re
import statistics
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

CHECKS = []


def check(name, blurb):
    def deco(fn):
        CHECKS.append((name, blurb, fn))
        return fn
    return deco


# -- small helpers ------------------------------------------------------------

def pages():
    """Every built page, newest read cached."""
    if not hasattr(pages, "_c"):
        pages._c = {}
        for f in sorted(os.listdir(".")):
            if f.endswith(".html"):
                pages._c[f] = open(f, encoding="utf-8").read()
    return pages._c


def css():
    if not hasattr(css, "_c"):
        css._c = open("styles.css", encoding="utf-8").read()
    return css._c


def css_rules():
    """[(selector list, body)], comments stripped.

    Comments go first or the paragraph above a rule is read as part of its
    selector list -- which is how a substring test once passed one class by
    accident while failing its neighbour.
    """
    if not hasattr(css_rules, "_c"):
        src = re.sub(r"/\*.*?\*/", "", css(), flags=re.S)
        out = []
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", src):
            sels = [s.strip() for s in m.group(1).split(",") if s.strip()]
            out.append((sels, m.group(2), m.start()))
        css_rules._c = out
    return css_rules._c


def rule_for(selector):
    """Every rule listing `selector` as one of its own, matched exactly."""
    return [(s, b, p) for s, b, p in css_rules() if selector in s]


def asset_ver():
    if not hasattr(asset_ver, "_c"):
        m = re.search(r'^ASSET_VER\s*=\s*"(\d+)"', open("build.py", encoding="utf-8").read(), re.M)
        asset_ver._c = m.group(1) if m else None
    return asset_ver._c


def wih_scale():
    if not hasattr(wih_scale, "_c"):
        m = re.search(r'^WIH_SCALE\s*=\s*([0-9.]+)',
                      open("build.py", encoding="utf-8").read(), re.M)
        wih_scale._c = float(m.group(1)) if m else 1.0
    return wih_scale._c


def im(path):
    from PIL import Image
    return Image.open(path)


def token(name):
    m = re.search(r"--%s:\s*(#[0-9A-Fa-f]{3,8})" % re.escape(name), css())
    return m.group(1) if m else None


def rgb(hexstr):
    h = hexstr.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# The four film-strip banners: class, the page that carries it, and the
# master in assets/. verify runs the whole block over all four from this one
# list, so a check written for any of them covers the others.
STRIP_BANNERS = [
    ("civic-banner",  "videos-civic.html",              "assets/Gov_Banner.webp"),
    ("sports-banner", "videos-sports-connection.html",  "assets/Sports_Banner.webp"),
    ("nl-banner",     "videos-nantucket-life.html",     "assets/nl-banner.webp"),
    ("np-banner",     "videos-partner-programs.html",   "assets/nonprofit-banner.webp"),
]

# The three video banners' fallback stills. The home one is a night scene
# whose sky row maxes at 21, so it is tested against a far darker floor -- a
# real letterbox bar is encoded black and survives q88 at 0-3. Do not tidy
# this up to one threshold; see "A dark banner is not a broken banner".
HERO_FALLBACKS = [
    ("assets/hero-fallback-home.webp",    6),
    ("assets/hero-fallback-shorts.webp",  24),
    ("assets/hero-fallback-newmoon.webp", 24),
]

FF_URL = "https://filmfreeway.com/NEWMoonFest"

CURSOR_SELECTORS = [
    "button", "summary", ".btn:not(.btn--static)",
    ".nav__link", ".nav__brand", ".skip-link",
    ".watch-episode__link", ".watch-episode__more",
    ".sport-link", ".partner", ".cfn-fund", ".cfn-funds__mark",
    ".ff-btn", ".hero-chip", ".civic-links__btn", ".filmmap__btn",
    ".newsreel__link", ".encore-img-link",
    ".sponsor-map__box", ".sponsor-map__btn", ".sponsormap__btn",
    ".auction-partners__shop", ".video-credit__cta",
    ".footer__social a",
]


def strip_colour(path, rows=12, step=3):
    """The commonest fully opaque colour across the top rows.

    One pixel is not a safe sample: a read of px[w//2, 2] once returned
    (17,24,37) on a strip that is really (13,24,38), and a sample that landed
    on something bright would invert the whole measurement.
    """
    img = im(path).convert("RGBA")
    W, H = img.size
    px = img.load()
    c = collections.Counter(px[x, y][:3]
                            for y in range(0, min(rows, H))
                            for x in range(0, W, step)
                            if px[x, y][3] == 255)
    return c.most_common(1)[0][0] if c else None


def banner_sources(cls, page):
    """[(min-width, file, version, w, h)] widest first, then the <img>."""
    h = pages()[page]
    i = h.index('class="%s"' % cls)
    body = h[i:h.index("</section>", i)]
    srcs = [(int(a), b, c, int(d), int(e)) for a, b, c, d, e in re.findall(
        r'<source media="\(min-width:(\d+)px\)" srcset="([^"?]+)\?v=(\d+)"'
        r' width="(\d+)" height="(\d+)"', body)]
    m = re.search(r'<img src="([^"?]+)\?v=(\d+)"\s+width="(\d+)" height="(\d+)"', body)
    img = (0, m.group(1), m.group(2), int(m.group(3)), int(m.group(4))) if m else None
    return srcs, img, body


def disc_hotspots():
    """Every disc hotspot on the site: (page, artwork, centre, radius)."""
    out = []
    for f, h in pages().items():
        for m in re.finditer(r'<div class="sponsor-map[^"]*"[^>]*>(.*?)</div>', h, re.S):
            blk = m.group(1)
            art = re.search(r'<img[^>]*src="(assets/[^"?]+)', blk)
            btns = re.findall(
                r'class="sponsor-map__btn"[^>]*style="left:([\d.]+)%;top:([\d.]+)%;'
                r'width:([\d.]+)%;height:([\d.]+)%"', blk)
            if not (art and btns):
                continue
            W, H = im(art.group(1)).size
            for L, T, Wp, Hp in btns:
                L, T, Wp, Hp = map(float, (L, T, Wp, Hp))
                w, hh = Wp / 100 * W, Hp / 100 * H
                out.append((f, art.group(1),
                            ((L + Wp / 2) / 100 * W, (T + Hp / 2) / 100 * H),
                            w / 2, w, hh))
    return out


# -- the checks ---------------------------------------------------------------

@check("pages-parse", "every built page nests strictly")
def _():
    # Strict last-in-first-out, not "pop until something matches". The lenient
    # form reads clean on a page that has lost a </div>: the next outer close
    # swallows the orphan, and </body> swallows the last one, so a page with a
    # genuinely broken box reports nothing. All 36 pages nest strictly today,
    # so there is no reason to be lenient.
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "source", "track", "wbr"}
    bad = []
    for f, h in pages().items():
        class P(HTMLParser):
            def __init__(s):
                super().__init__(convert_charrefs=True)
                s.st, s.err = [], []

            def handle_starttag(s, t, a):
                if t not in VOID:
                    s.st.append((t, s.getpos()[0]))

            def handle_endtag(s, t):
                if t in VOID:
                    s.err.append("</%s> on a void element, line %d" % (t, s.getpos()[0]))
                    return
                if not s.st:
                    s.err.append("stray </%s>, line %d" % (t, s.getpos()[0]))
                    return
                if s.st[-1][0] == t:
                    s.st.pop()
                    return
                s.err.append("</%s> at line %d, but <%s> from line %d is still open"
                             % (t, s.getpos()[0], s.st[-1][0], s.st[-1][1]))
                if t in [x[0] for x in s.st]:
                    while s.st and s.st.pop()[0] != t:
                        pass
        p = P()
        p.feed(h)
        p.close()
        for e in p.err[:3]:
            bad.append("%s: %s" % (f, e))
        if p.st:
            bad.append("%s: never closed: %s" % (
                f, ", ".join("<%s> line %d" % x for x in p.st[:4])))
    return bad


@check("assets-exist", "every referenced assets/... file is on disk")
def _():
    bad = []
    for f, h in pages().items():
        for ref in sorted(set(re.findall(r'(?:src|href|srcset)="(assets/[^"?]+)', h))):
            if not os.path.exists(ref):
                bad.append("%s -> %s is missing" % (f, ref))
    return bad


@check("internal-links", "every internal *.html link resolves")
def _():
    bad = []
    for f, h in pages().items():
        for ref in sorted(set(re.findall(r'href="([^":#?]+\.html)(?:[#?][^"]*)?"', h))):
            if ref.startswith(("http://", "https://", "//")):
                continue
            if not os.path.exists(ref.lstrip("/")):
                bad.append("%s -> %s does not exist" % (f, ref))
    return bad


@check("asset-version", "every versioned asset URL carries the current ASSET_VER")
def _():
    v = asset_ver()
    if not v:
        return ["ASSET_VER not found in build.py"]
    bad = []
    for f, h in pages().items():
        for seen in sorted(set(re.findall(r'assets/[^"?]+\?v=(\d+)', h))):
            if seen != v:
                bad.append("%s carries ?v=%s, ASSET_VER is %s" % (f, seen, v))
    return bad


@check("cursor-rules", "the 24 control selectors, and no blanket rule among them")
def _():
    bad = []
    hit = [(s, b, p) for s, b, p in css_rules()
           if "cursor:pointer" in b.replace(" ", "") and "user-select:none" in b.replace(" ", "")]
    if not hit:
        return ["no rule setting both cursor:pointer and user-select:none"]
    sels = [s for s, _, _ in hit for s in s]
    for want in CURSOR_SELECTORS:
        if want not in sels:
            bad.append("control selector missing from the cursor rule: %s" % want)
    for blanket in ("a", "p", "body", "*"):
        if blanket in sels:
            bad.append("a blanket `%s` rule has crept into the cursor list" % blanket)
    if ".btn" in sels:
        bad.append(".btn is listed bare; it must be .btn:not(.btn--static)")
    # the disabled guard has to be restated AFTER the list, or the 2,243
    # pending agenda buttons take the hand.
    dis = [p for s, b, p in css_rules()
           if "button:disabled" in s and "cursor:default" in b.replace(" ", "")]
    if not dis:
        bad.append("button:disabled{cursor:default} is missing")
    elif max(p for _, _, p in hit) > min(dis):
        bad.append("button:disabled{cursor:default} sits before the cursor list")
    if not rule_for("a img") and not rule_for("button img"):
        bad.append("no -webkit-user-drag rule on linked images")
    return bad


@check("banner-markup", "four film strips: four sources widest-first, all sized and versioned")
def _():
    bad = []
    v = asset_ver()
    for cls, page, _master in STRIP_BANNERS:
        try:
            srcs, img, body = banner_sources(cls, page)
        except ValueError:
            bad.append("%s: no .%s section" % (page, cls))
            continue
        if len(srcs) != 3 or img is None:
            bad.append("%s: expected 3 <source> and 1 <img>, got %d and %s"
                       % (cls, len(srcs), bool(img)))
            continue
        mins = [s[0] for s in srcs]
        if mins != sorted(mins, reverse=True):
            bad.append("%s: <source> order is %s, must be widest-first" % (cls, mins))
        for _mw, fil, ver, w, hgt in srcs + [img]:
            if ver != v:
                bad.append("%s: %s carries ?v=%s, ASSET_VER is %s" % (cls, fil, ver, v))
            if not (w and hgt):
                bad.append("%s: %s has no width/height (the browser needs the ratio)" % (cls, fil))
            if os.path.exists(fil):
                rw, rh = im(fil).size
                if (rw, rh) != (w, hgt):
                    bad.append("%s: %s is %dx%d on disk but declared %dx%d"
                               % (cls, fil, rw, rh, w, hgt))
        if body.count("alt=") != 1:
            bad.append("%s: expected exactly one alt (one covers all four sizes)" % cls)
    return bad


@check("banner-crop-widths", "each crop is at least as wide as the band it serves")
def _():
    bad = []
    for cls, page, _m in STRIP_BANNERS:
        srcs, img, _ = banner_sources(cls, page)
        for mw, fil, _v, w, _h in srcs:
            if w < mw:
                bad.append("%s: %s is %dpx wide but serves screens from %dpx" % (cls, fil, w, mw))
    return bad


@check("banner-crops-match-master", "every crop is still a slice of the master in assets/")
def _():
    bad = []
    for cls, page, master in STRIP_BANNERS:
        if not os.path.exists(master):
            bad.append("%s: master %s is missing" % (cls, master))
            continue
        M = im(master).convert("RGBA")
        srcs, img, _ = banner_sources(cls, page)
        for _mw, fil, _v, _w, _h in srcs + [img]:
            if fil == master or not os.path.exists(fil):
                continue
            c = im(fil).convert("RGBA")
            w, h = c.size
            if w > M.size[0] or h > M.size[1]:
                bad.append("%s: %s is larger than its master" % (cls, fil))
                continue
            pa, pb = c.load(), M.crop((0, 0, w, h)).load()
            n = d = 0
            for x in range(0, w, 7):
                for y in range(0, h, 7):
                    d += max(abs(pa[x, y][i] - pb[x, y][i]) for i in range(3))
                    n += 1
            mean = d / max(n, 1)
            if mean > 8:
                bad.append("%s: %s diverges from the master (mean %.1f) -- "
                           "re-run tools/crop-banner.py after an artwork swap" % (cls, fil, mean))
    return bad


@check("banner-alpha", "every crop keeps its alpha, so the sprocket holes are not black")
def _():
    bad = []
    for cls, page, master in STRIP_BANNERS:
        srcs, img, _ = banner_sources(cls, page)
        for _mw, fil, _v, _w, _h in srcs + [img] + [(0, master, "", 0, 0)]:
            if not os.path.exists(fil):
                continue
            a = im(fil).convert("RGBA").getextrema()[3]
            if a[0] == 255:
                bad.append("%s: %s has no transparent pixel -- the holes will paint black"
                           % (cls, fil))
    return bad


@check("banner-strip-colour", "the film strip still matches --nav-bg")
def _():
    nav = token("nav-bg")
    if not nav:
        return ["--nav-bg not found in styles.css"]
    want = rgb(nav)
    bad = []
    for cls, _page, master in STRIP_BANNERS:
        if not os.path.exists(master):
            continue
        got = strip_colour(master)
        # The strip is #0D1826 against --nav-bg #0C1826: one level apart, "a
        # rounding error" as CLAUDE.md puts it. 3 is the slack that allows.
        # It is a modal colour over thousands of samples of one flat region,
        # so a re-encode does not move it; a recolour moves it far more.
        if got is None or max(abs(got[i] - want[i]) for i in range(3)) > 3:
            bad.append("%s: strip is %s, --nav-bg is %s %s -- more than 3 levels apart "
                       "on some channel, so they have drifted" % (cls, got, nav, want))
    return bad


@check("civic-banner-no-background", ".civic-banner must not take a background of its own")
def _():
    bad = []
    for sels, body, _p in css_rules():
        if ".civic-banner" in sels and re.search(r"\bbackground(-color)?\s*:", body):
            bad.append(".civic-banner sets a background; the sprocket holes would change colour")
    return bad


@check("banner-css-rules", "the four strips keep their two rules, matched by exact selector")
def _():
    bad = []
    for cls, _page, _m in STRIP_BANNERS:
        if not any("padding-top:2px" in b.replace(" ", "") for _s, b, _p in rule_for("." + cls)):
            bad.append(".%s has no padding-top:2px" % cls)
        if not any("display:block" in b.replace(" ", "")
                   for _s, b, _p in rule_for(".%s picture" % cls)):
            bad.append(".%s picture{display:block} is missing" % cls)
    return bad


@check("hero-fallback-version", "all three banner fallbacks carry ?v=ASSET_VER")
def _():
    v = asset_ver()
    bad = []
    for path, _thr in HERO_FALLBACKS:
        base = os.path.basename(path)
        seen = set()
        for f, h in pages().items():
            seen |= set(re.findall(re.escape("assets/" + base) + r'\?v=(\d+)', h))
            if re.search(re.escape("assets/" + base) + r'(?!\?v=)', h):
                bad.append("%s: %s is referenced without a ?v=" % (f, base))
        if not seen:
            bad.append("%s is never referenced with a version" % base)
        for s in seen:
            if s != v:
                bad.append("%s carries ?v=%s, ASSET_VER is %s" % (base, s, v))
    return bad


@check("hero-fallback-bars", "no letterbox bar baked into a banner fallback")
def _():
    bad = []
    for path, thr in HERO_FALLBACKS:
        if not os.path.exists(path):
            bad.append("%s is missing" % path)
            continue
        img = im(path).convert("RGB")
        W, H = img.size
        px = img.load()
        xs = range(0, W, 5)
        for label, y in (("top", 0), ("bottom", H - 1)):
            mean = sum(sum(px[x, y]) / 3 for x in xs) / len(xs)
            if mean < thr:
                bad.append("%s: %s row means %.1f, under its %d floor -- "
                           "looks like a letterbox bar" % (os.path.basename(path), label, mean, thr))
    return bad


@check("sponsor-discs-square", "every disc hotspot is a square box, so it traces a circle")
def _():
    bad = []
    for page, art, _c, _r, w, h in disc_hotspots():
        if abs(w - h) > 1.5:
            bad.append("%s (%s): hotspot is %.1fx%.1f -- border-radius:50%% draws an ellipse"
                       % (page, os.path.basename(art), w, h))
    return bad


@check("sponsor-discs-on-logo", "every disc hotspot still sits over its logo")
def _():
    # A hotspot that has slid off its logo is still perfectly valid markup and
    # passes every structural test, so this is the one that catches a redrawn
    # banner. Ink inside the circle, field just outside it, 36 points round.
    bad = []
    for page, art, (cx, cy), r, _w, _h in disc_hotspots():
        img = im(art).convert("RGB")
        W, H = img.size
        px = img.load()
        ins, out = [], []
        for k in range(36):
            a = 2 * math.pi * k / 36
            for rad, acc in ((0.95 * r, ins), (1.08 * r, out)):
                x = min(W - 1, max(0, int(round(cx + rad * math.cos(a)))))
                y = min(H - 1, max(0, int(round(cy + rad * math.sin(a)))))
                acc.append(px[x, y])
        field = tuple(sorted(c[i] for c in out)[len(out) // 2] for i in range(3))
        dist = lambda c: max(abs(c[i] - field[i]) for i in range(3))
        m_in = statistics.median(map(dist, ins))
        m_out = statistics.median(map(dist, out))
        # The field is sampled from the hotspot's own outer ring rather than
        # assumed flat, so this works on the gradient banners too.
        if m_in < 30:
            bad.append("%s (%s): circle at (%.0f,%.0f) r=%.0f has no logo under it "
                       "(inside differs from field by only %.0f)"
                       % (page, os.path.basename(art), cx, cy, r, m_in))
        if m_out > 20:
            bad.append("%s (%s): circle at (%.0f,%.0f) r=%.0f still has ink outside it "
                       "(outside differs from field by %.0f) -- it may have slid"
                       % (page, os.path.basename(art), cx, cy, r, m_out))
    return bad


@check("sponsor-boxes", "no two box hotspots overlap")
def _():
    bad = []
    for f, h in pages().items():
        for m in re.finditer(r'<div class="sponsor-map[^"]*"[^>]*>(.*?)</div>', h, re.S):
            blk = m.group(1)
            art = re.search(r'<img[^>]*src="(assets/[^"?]+)', blk)
            boxes = re.findall(
                r'class="sponsor-map__box"[^>]*style="left:([\d.]+)%;top:([\d.]+)%;'
                r'width:([\d.]+)%;height:([\d.]+)%"', blk)
            if not (art and boxes):
                continue
            rects = []
            for L, T, Wp, Hp in boxes:
                L, T, Wp, Hp = map(float, (L, T, Wp, Hp))
                rects.append((L, T, L + Wp, T + Hp))
            for i in range(len(rects)):
                for j in range(i + 1, len(rects)):
                    a, b = rects[i], rects[j]
                    ox = min(a[2], b[2]) - max(a[0], b[0])
                    oy = min(a[3], b[3]) - max(a[1], b[1])
                    if ox > 0.2 and oy > 0.2:
                        bad.append("%s (%s): box hotspots %d and %d overlap"
                                   % (f, os.path.basename(art.group(1)), i + 1, j + 1))
    return bad


@check("filmfreeway-buttons", "every FilmFreeway button points at the one address")
def _():
    bad = []
    found = 0
    for f, h in pages().items():
        for m in re.finditer(r'<a[^>]*\bclass="[^"]*\bff-btn\b[^"]*"[^>]*>', h):
            found += 1
            hm = re.search(r'href="([^"]+)"', m.group(0))
            if not hm or hm.group(1) != FF_URL:
                bad.append("%s: an ff-btn points at %s, not %s"
                           % (f, hm.group(1) if hm else "nothing", FF_URL))
        if "/dashboard" in h:
            bad.append("%s: a /dashboard link survives" % f)
    if found == 0:
        bad.append("no .ff-btn found at all")
    return bad


@check("ff-btn-source-order", "a.ff-btn keeps its `a` and stays after the two link rules")
def _():
    bad = []
    pos = [p for s, _b, p in css_rules() if "a.ff-btn" in s]
    if not pos:
        return ["a.ff-btn is missing, or was written as a bare .ff-btn (it would lose "
                "to .news-list a and .nmf-rules__submit a, both 0,1,1)"]
    for other in (".news-list a", ".nmf-rules__submit a"):
        op = [p for s, _b, p in css_rules() if other in s]
        if op and min(pos) < max(op):
            bad.append("a.ff-btn sits before %s; the later rule wins at equal specificity"
                       % other)
    return bad


@check("partner-pages-reachable", "every partner page is reachable from a logo on both hubs")
def _():
    disk = sorted(p for p in pages() if p.startswith("partner-"))
    bad = []
    for hub in ("index.html", "videos-partner-programs.html"):
        if hub not in pages():
            bad.append("%s is missing" % hub)
            continue
        linked = set()
        for m in re.finditer(r"<a[^>]+>", pages()[hub]):
            tag = m.group(0)
            if re.search(r'class="[^"]*\b(partner|cfn-fund|cfn-funds__mark)\b', tag):
                hm = re.search(r'href="([^"]+)"', tag)
                if hm:
                    linked.add(hm.group(1).split("#")[0])
        for p in disk:
            if p not in linked:
                bad.append("%s: no logo links to %s" % (hub, p))
        for l in sorted(linked):
            if l.endswith(".html") and l not in disk:
                bad.append("%s: a logo links to %s, which is not a partner page" % (hub, l))
    return bad


@check("news-dates-descending", "the news carousel is newest-first by its printed date")
def _():
    src = open("build.py", encoding="utf-8").read()
    m = re.search(r"^NEWS = \[.*?^\]", src, re.S | re.M)
    if not m:
        return ["NEWS list not found in build.py"]
    dates = re.findall(r'date="(\d{1,2})/(\d{1,2})/(\d{2})"', m.group(0))
    if not dates:
        return ["no date= fields in NEWS"]
    keys = [(2000 + int(y), int(mo), int(d)) for mo, d, y in dates]
    bad = []
    for i in range(1, len(keys)):
        if keys[i] > keys[i - 1]:
            bad.append("NEWS item %d (%s) is newer than item %d (%s) -- the list is "
                       "newest-first by the date printed on the card"
                       % (i + 1, "/".join(dates[i]), i, "/".join(dates[i - 1])))
    return bad


def panel_spans(h, classes=("year-panel",)):
    """(start, end, label) for every panel of these classes, by div depth.

    Needed because the panels nest: Browse by Topic -> "Whales, Whaling and
    Whale Ecology" -> a year picker of its own, and on the Civic page a
    quarter-panel inside a year-panel. The default is year-panel alone so
    that duplicate-video-ids keeps scoping to the year it always has.
    """
    out = []
    pat = r'<div class="(?:%s)"[^>]*data-(?:year|quarter)="([^"]+)"' % "|".join(classes)
    for m in re.finditer(pat, h):
        depth, i = 0, m.start()
        while i < len(h):
            n = re.compile(r"<div\b|</div>").search(h, i)
            if not n:
                break
            depth += 1 if n.group(0) == "<div" else -1
            i = n.end()
            if depth == 0:
                break
        out.append((m.start(), i, m.group(1)))
    return out


@check("duplicate-video-ids", "no single list shows the same video twice")
def _():
    # Scoped to the innermost year-panel, not the page. Filing one lecture
    # under both its year and its topic is the whole point of the NHA page's
    # three pickers -- 142 of its ids are deliberately listed twice -- and the
    # same lecture under two topics is fine too. What is never right is the
    # same video twice in one open panel, where a reader sees both at once.
    #
    # Match the card's own watch link, never any URL in the page: a
    # description can legitimately carry a youtu.be link to another video.
    bad = []
    for f, h in pages().items():
        ids = [(m.start(), m.group(1)) for m in re.finditer(
            r'class="watch-episode__link"[^>]*href="[^"]*?(?:v=|youtu\.be/|embed/)'
            r'([A-Za-z0-9_-]{11})', h)]
        if not ids:
            continue
        spans = panel_spans(h)
        buckets = collections.defaultdict(list)
        for pos, vid in ids:
            inner = max((s for s in spans if s[0] < pos < s[1]),
                        key=lambda s: s[0], default=None)
            buckets[(inner[0], inner[2]) if inner else (-1, "(no panel)")].append(vid)
        for (st, lab), vids in sorted(buckets.items()):
            dupe = [v for v, n in collections.Counter(vids).items() if n > 1]
            if dupe:
                bad.append("%s: panel %s lists %s twice in the same list"
                           % (f, lab, ", ".join(sorted(dupe)[:4])))
    return bad


@check("civic-pending-buttons", "every greyed agenda button is really disabled")
def _():
    # Dimming a control in CSS does not take it out of the tab order.
    h = pages().get("videos-civic.html", "")
    pend = re.findall(r"<button[^>]*watch-episode__link[^>]*>", h)
    bad = []
    n = 0
    for tag in pend:
        if "--pending" in tag:
            n += 1
            if "disabled" not in tag:
                bad.append("a --pending agenda button is not disabled: %s" % tag[:90])
    if n == 0:
        bad.append("no --pending agenda buttons found at all on videos-civic.html")
    return bad


# -- card order ---------------------------------------------------------------

_MONTHS = {}
for _i, _m in enumerate(("January February March April May June July August "
                         "September October November December").split()):
    _MONTHS[_m.lower()] = _i + 1
    _MONTHS[_m[:3].lower()] = _i + 1
_MONTHS["sept"] = 9
for _i, _m in enumerate(("enero febrero marzo abril mayo junio julio agosto "
                         "septiembre octubre noviembre diciembre").split()):
    _MONTHS[_m] = _i + 1


def title_date(t):
    """The date printed in a card title, in every form the site uses.

    Five forms, because a parser that only reads "September 14, 2026" misses a
    third of the Sports page: "Nov. 7 2024" with no comma, "Jan. 8th, 2026"
    with an ordinal, "12/28/2021" and "12/22/22" from the 2021-23 titles, and
    "27 de septiembre de 2025" -- one Girls Soccer card is in Spanish.

    Takes the LAST match of the first form that matches, so a title that
    mentions another date first ("a rematch of the Oct. 8, 2025 meeting") is
    still dated by its own. No title on the site carries two dates today;
    the rule is there so that one arriving later does not silently misfile.

    None when a title carries no date at all -- 27 Sports cards and 6 Civic
    ones. Those are skipped rather than failed; see card_order.
    """
    for pat, pick in (
            # "27 de septiembre de 2025"
            (r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})",
             lambda g: (int(g[2]), _MONTHS.get(g[1].lower()), int(g[0]))),
            # "September 14, 2026" / "Nov. 7 2024" / "Jan. 8th, 2026"
            (r"([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})",
             lambda g: (int(g[2]), _MONTHS.get(g[0].lower()), int(g[1]))),
            # "12/28/2021" / "12/22/22"
            (r"(\d{1,2})/(\d{1,2})/(\d{2,4})",
             lambda g: (int(g[2]) + (2000 if int(g[2]) < 100 else 0),
                        int(g[0]), int(g[1]))),
    ):
        best = None
        for m in re.finditer(pat, t, re.I):
            y, mo, d = pick(m.groups())
            if mo and 1 <= d <= 31:
                best = (y, mo, d)
        if best:
            return best
    return None


def card_dates(name):
    """A build.py fallback table: the date for a card whose title has none.

    SPORT_CARD_DATES or CIVIC_CARD_DATES. Read out of the source rather than
    imported, because importing build.py would run it. Each is a plain dict of
    video id -> "YYYY-MM-DD", and the per-row comments carry the provenance.
    """
    if not hasattr(card_dates, "_c"):
        card_dates._c = {}
    if name not in card_dates._c:
        src = open("build.py", encoding="utf-8").read()
        m = re.search(r"^%s = \{.*?^\}" % name, src, re.S | re.M)
        if not m:
            raise ValueError("%s not found in build.py" % name)
        card_dates._c[name] = {
            vid: tuple(int(x) for x in d.split("-"))
            for vid, d in re.findall(
                r'"([A-Za-z0-9_-]{11})":\s*"(\d{4}-\d{2}-\d{2})"', m.group(0))}
        if not card_dates._c[name]:
            raise ValueError("%s parsed as empty" % name)
    return card_dates._c[name]


def card_order(page, fallback=None, table_name=None):
    """Every list on one page, newest-first, by the date in each card title.

    A "list" is one innermost panel -- one year on the Sports page, one
    quarter of one year on the Civic page. Checking the page as a whole would
    be meaningless: it holds 425 separate lists whose dates interleave.

    Cards outside every panel are not checked. On the Civic page those are the
    ten Nantucket Government 101 department videos, which sit in a flat
    alphabetical list; CLAUDE.md says that one is not a meeting list and keeps
    its own order, and it has no dates to sort by anyway.

    `fallback` maps a video id to a date for cards whose title carries none,
    and `table_name` is what to call it in a failure. Given one, a card that is
    in neither the title nor the table is a FAILURE, not a skip -- that is what
    stops an undated card from being dropped into a list at no particular
    position. A title that does carry a date still wins over the table, so a
    video cross-listed under a dated title and an undated one is placed
    correctly in both.

    Equal dates pass. Two meetings on one day is ordinary -- the Select Board
    met twice on Jul. 17th 2024 -- and nothing in the page decides which of
    the two should read first.
    """
    h = pages()[page]
    spans = panel_spans(h, ("year-panel", "quarter-panel"))
    buckets = collections.defaultdict(list)
    for m in re.finditer(r'<article class="watch-episode".*?</article>', h, re.S):
        inner = max((s for s in spans if s[0] < m.start() < s[1]),
                    key=lambda s: s[0], default=None)
        if not inner:
            continue
        t = re.search(r'<h3 class="watch-episode__title">(.*?)</h3>', m.group(0), re.S)
        v = re.search(r'(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})', m.group(0))
        buckets[(inner[0], inner[2])].append(
            (t.group(1) if t else "(no title)", v.group(1) if v else None))
    if not buckets:
        return ["%s: no panelled card lists found -- has the markup changed?" % page]
    bad, dateless = [], []
    for (start, label), cards in sorted(buckets.items()):
        dated = []
        for title, vid in cards:
            d = title_date(title)
            if d is None and fallback is not None:
                d = fallback.get(vid)
                if d is None:
                    dateless.append(
                        "%s, panel %s: %r has no date in its title and none in "
                        "%s, so nothing puts it in order -- add its streaming "
                        "date (or its posting date if it was never streamed)"
                        % (page, label, title[:60], table_name))
                    continue
            if d:
                dated.append((title, d))
        for i in range(1, len(dated)):
            if dated[i][1] > dated[i - 1][1]:
                bad.append("%s, panel %s: %r sits below %r -- the list is "
                           "newest-first by the date in the title"
                           % (page, label, dated[i][0][:60], dated[i - 1][0][:60]))
    return dateless + bad


@check("civic-dates-descending", "every Civic TV list is newest-first by its titles' dates")
def _():
    # The honest test reads the BUILT page, never CIVIC_BOARDS. The data is
    # stored oldest-first on purpose -- Update_CTV appends -- and
    # civic_year_cards() reverses it as it renders. Measuring the literal
    # says every list is backwards when the page is perfectly right, which is
    # exactly the mistake this check exists to stop. It also catches the
    # reverse: a renderer that stopped reversing.
    #
    # Six cards carry no readable date in the title -- five Public Forums and
    # one cross-listed video -- so CIVIC_CARD_DATES places them and this fails
    # on any undated card missing from it.
    return card_order("videos-civic.html", card_dates("CIVIC_CARD_DATES"),
                      "CIVIC_CARD_DATES")


@check("school-dates-descending", "every School Videos list is newest-first by its titles' dates")
def _():
    # Added 2026-11-05, when Frank had the whole page put newest-first. Until
    # then Whaler Word and The CPS Pulse ran Episode 1 at the top, so the page
    # held lists going both ways and could not be checked as one thing; he
    # asked for every list on it to read newest to oldest, which made it
    # checkable. Both lists are now rendered through
    # programs_section(newest_first=True) like the School Committee one.
    #
    # No fallback table: 21 school cards carry no date (the Class of YYYY
    # graduations, Senior Awards and the 8th Grade Promotions), and every one
    # of them sits alone in its own year panel, where order cannot be wrong.
    # Should a second card ever join one of those panels, this check would
    # skip the undated one -- add a CARD_DATES table then, as the other two
    # pages have.
    return card_order("videos-school.html")


@check("sports-dates-descending", "every Sports Connection list is newest-first by its titles' dates")
def _():
    # Here the order really is in the data, so this check and a glance at
    # SPORTS_VIDEOS agree. Upcoming games are sorted on their dates like any
    # other card, which puts the furthest-away game at the top of an
    # all-upcoming season; Frank confirmed that reading on 2026-11-05.
    #
    #
    # The fallback table makes this total: 27 cards carry no date in the
    # title, and passing SPORT_CARD_DATES both places them and fails on any
    # undated card that is missing from it.
    return card_order("videos-sports-connection.html",
                      card_dates("SPORT_CARD_DATES"), "SPORT_CARD_DATES")


def sports_videos():
    """SPORTS_VIDEOS as data: {sport: {year: [(id, title, desc, upcoming)]}}.

    Read out of the source and literal_eval'd rather than imported, because
    importing build.py would run it. The literal is plain -- no sentinels --
    so this is the whole of it.
    """
    if not hasattr(sports_videos, "_c"):
        tree = ast.parse(open("build.py", encoding="utf-8").read())
        for node in tree.body:
            if (isinstance(node, ast.Assign)
                    and getattr(node.targets[0], "id", "") == "SPORTS_VIDEOS"):
                sports_videos._c = ast.literal_eval(node.value)
                break
        else:
            raise ValueError("SPORTS_VIDEOS not found in build.py")
    return sports_videos._c


def sport_upcoming_text():
    """SPORT_UPCOMING, read from build.py so a reword cannot mute the check."""
    if not hasattr(sport_upcoming_text, "_c"):
        m = re.search(r'^SPORT_UPCOMING = "([^"]+)"',
                      open("build.py", encoding="utf-8").read(), re.M)
        if not m:
            raise ValueError("SPORT_UPCOMING not found in build.py")
        sport_upcoming_text._c = m.group(1)
    return sport_upcoming_text._c


@check("sports-upcoming-lead", "an upcoming game leads with the sentence and carries its description below")
def _():
    # Frank asked for this shape on 2026-11-10: a game that has not aired says
    # "This game is upcoming." and then, below it, the preview NSC posted with
    # the scheduled stream. Before that the sentence was the whole of the card
    # and the description was thrown away by the renderer.
    #
    # What makes it worth a check is how the sentence is supposed to GO. It is
    # not deleted when the game airs; the trailing flag in SPORTS_VIDEOS flips
    # to False and sport_desc() stops prepending it. So the sentence must live
    # only in the renderer. The day someone "helpfully" pastes it into a
    # description literal instead, that card keeps saying a played game is
    # upcoming forever, and flipping the flag -- the one thing the protocol
    # does to heal a card -- will not fix it. Nothing about the page looks
    # wrong until the game has been over for a week.
    #
    # Four things, then: the sentence leads rather than trails, every upcoming
    # card has a description under it, the count on the page matches the flags
    # in the data, and the sentence appears in no description literal and on no
    # other page.
    sentence = sport_upcoming_text()
    page = "videos-sports-connection.html"
    bad = []

    # (1) and (2): how the sentence sits in each description on the page.
    bodies = re.findall(r'<p class="watch-episode__desc">(.*?)</p>',
                        pages()[page], re.S)
    carrying = [b for b in bodies if sentence in b]
    for b in carrying:
        if not b.startswith(sentence):
            bad.append("%s: a card has %r somewhere other than the start of "
                       "its description -- it is the lead-in, not a trailer"
                       % (page, sentence))
        elif b[len(sentence):].strip() in ("", "<br>", "<br><br>"):
            bad.append("%s: %r stands alone on a card, with no description "
                       "under it -- pull the stream's YouTube description into "
                       "its SPORTS_VIDEOS entry (if YouTube really has none, "
                       "say so here and loosen this check)"
                       % (page, b[:70]))

    # (3): the page's count against the data's flags.
    flagged = [(vid, title) for years in sports_videos().values()
               for cards in years.values()
               for vid, title, _desc, up in cards if up]
    if len(carrying) != len(flagged):
        bad.append("%s shows the sentence on %d cards but SPORTS_VIDEOS flags "
                   "%d as upcoming -- a flag was flipped without a rebuild, or "
                   "sport_desc() stopped leading with it"
                   % (page, len(carrying), len(flagged)))

    # (4): the sentence belongs to the renderer alone.
    for years in sports_videos().values():
        for cards in years.values():
            for vid, title, desc, _up in cards:
                if sentence in (desc or ""):
                    bad.append("%s carries %r inside its own description "
                               "literal -- it must come from sport_desc(), or "
                               "flipping the flag will never remove it"
                               % (vid, sentence))
    for name, html in pages().items():
        if name != page and sentence in html:
            bad.append("%s says %r, and only the Sports Connection page should"
                       % (name, sentence))
    return bad


@check("nmf-women-panels", "the Notable Nantucket Women picker opens empty, its portraits track WIH_SCALE and its films are ours")
def _():
    # Three things this guards, all of which look perfectly normal when they
    # are wrong.
    #
    # The picker must open with nothing selected and every panel hidden. That
    # is what makes the section a set of choices rather than one woman's life
    # with twenty-four buttons round it, and it is only true because no
    # is-active and no unhidden panel is written into the markup -- one
    # copy-and-paste from the awards or auction picker, which both DO open on
    # a chosen panel, would quietly undo it.
    #
    # Every button must have the panel its data-year names, and the other way
    # round. initYearPicker() hides the panels that do not match and shows
    # nothing when none does, so a mistyped slug is a button that does
    # nothing at all -- no error, no empty panel, just a dead control.
    #
    # And the portraits must still be drawn at their own size. They were
    # cropped out of the PDF Frank supplied and are about 155px across, which
    # is all that file carries; .wih-portrait therefore sets no width, and the
    # <img> states its real pixels so the box is reserved. A width rule added
    # to that selector later would enlarge nineteen thumbnails past their own
    # resolution and blur every one of them, which is exactly the kind of
    # change that looks deliberate in a stylesheet. If larger originals ever
    # arrive, widen the rule and this check comes off with it.
    bad = []
    h = pages()["events-new-moon-fest.html"]
    m = re.search(r'<section class="section nmf-women">.*?\n</section>', h, re.S)
    if not m:
        return ["the Notable Nantucket Women section is not on the page"]
    sec = m.group(0)

    btns = re.findall(r'<button[^>]*class="year-btn"[^>]*data-year="([^"]+)"', sec)
    panels = re.findall(r'<div class="year-panel" data-year="([^"]+)"([^>]*)>', sec)
    if len(btns) != len(set(btns)):
        bad.append("a slug is used by two buttons")
    if sorted(btns) != sorted(p for p, _ in panels):
        bad.append("buttons and panels do not pair up: %s" %
                   (set(btns) ^ set(p for p, _ in panels)))
    for slug, attrs in panels:
        if "hidden" not in attrs:
            bad.append("%s opens on load; the picker must open empty" % slug)
    if "is-active" in sec:
        bad.append("a name button carries is-active; the picker must open empty")

    # No width on the portrait, read off the rule itself rather than by
    # searching the file -- the selector may pick up company later, the way
    # the four film-strip banners did.
    for rule in re.findall(r'([^{}]*)\{([^{}]*)\}', css()):
        sels = [x.strip() for x in rule[0].split("}")[-1].split(",")]
        if ".wih-portrait" in sels and re.search(r'(^|;)\s*width\s*:', rule[1]):
            bad.append(".wih-portrait is given a width: %s" % rule[1].strip())

    # Every portrait exists, is versioned, and states the file's own pixels.
    for tag in re.findall(r'<img class="wih-portrait"[^>]*>', sec):
        src = re.search(r'src="([^"?]+)\?v=(\d+)"', tag)
        if not src:
            bad.append("a portrait has no src?v=: %s" % tag[:90])
            continue
        path, ver = src.group(1), src.group(2)
        if not os.path.exists(path):
            bad.append("%s is referenced and missing" % path)
            continue
        if ver != asset_ver():
            bad.append("%s carries ?v=%s, not %s" % (path, ver, asset_ver()))
        # The tag draws the file at WIH_SCALE, so it must ask for exactly
        # that and the file must still be the size it was cropped at. Both
        # halves matter: a tag that drifts off the constant makes the
        # upscale accidental, and a file that grows to meet the tag is the
        # blur baked in, which is the thing the constant exists to avoid.
        w = re.search(r'width="(\d+)" height="(\d+)"', tag)
        real = im(path).size
        want = (int(round(real[0] * wih_scale())), int(round(real[1] * wih_scale())))
        if not w or (int(w.group(1)), int(w.group(2))) != want:
            bad.append("%s is %dx%d, so at %gx the tag wants %dx%d; it says %s" %
                       ((path,) + real + (wih_scale(),) + want +
                        (w.group(0) if w else "nothing",)))

    # And every film a panel links to must still be on the site. Six panels
    # end with a link to the NHA film about that woman, and the only reason
    # a reader is sent off to YouTube is that the film is one of ours and
    # the card is on partner-nha.html. If that page ever stops listing the
    # id -- the video pulled, the card moved to another partner, the whole
    # section rebuilt -- the link still works and still plays, so nothing
    # breaks visibly; it just stops being a pointer into our own archive.
    # The link must also be a youtu.be address in a new tab, which is the
    # form every card on that page uses.
    nha = pages()["partner-nha.html"]
    films = re.findall(r'<p class="wih-film">[^<]*<a ([^>]*)>', sec)
    if not films:
        bad.append("no panel links to a film; six of them should")
    for attrs in films:
        href = re.search(r'href="https://youtu\.be/([A-Za-z0-9_-]{11})"', attrs)
        if not href:
            bad.append("a film link is not a youtu.be/<id> address: %s" % attrs[:90])
            continue
        if 'target="_blank"' not in attrs or 'rel="noopener"' not in attrs:
            bad.append("%s does not open in a new tab with rel=noopener" % href.group(1))
        if "youtu.be/%s" % href.group(1) not in nha:
            bad.append("%s is linked from a panel but is not on partner-nha.html"
                       % href.group(1))
    return bad



def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--list" in sys.argv:
        for name, blurb, _ in CHECKS:
            print("  %-28s %s" % (name, blurb))
        return 0
    run = [c for c in CHECKS if not args or any(a in c[0] for a in args)]
    if not run:
        print("no check matches %s" % args, file=sys.stderr)
        return 2
    fails = 0
    for name, blurb, fn in run:
        try:
            out = fn()
        except Exception as e:          # a broken check is a failure, not a pass
            out = ["check raised %s: %s" % (type(e).__name__, e)]
        if out:
            fails += 1
            print("FAIL  %-28s %s" % (name, blurb))
            for line in out[:12]:
                print("        %s" % line)
            if len(out) > 12:
                print("        ... and %d more" % (len(out) - 12))
        else:
            print("ok    %-28s %s" % (name, blurb))
    print()
    print("%d checks, %d failed" % (len(run), fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
