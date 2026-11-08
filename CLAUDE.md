# NCTV website — working notes

Static site for Nantucket Community Television. 35 HTML pages, no framework,
no build tooling beyond one Python script.

## How the site is built

`build.py` generates **every** `.html` file in this folder. `styles.css` and
`site.js` are edited by hand and loaded by all pages.

The nav bar and footer are **markup in every page**, emitted by `nav_html()`
and `footer_html()` in `build.py`. To add, rename or reorder a nav link, edit
the `NAV` list there, not `site.js` — which now only wires the behaviour, plus
one line that corrects the footer's copyright year if a visitor reads the page
in a later year than the one it was built in. Until 2026-10-28 `site.js` built
both with `innerHTML` on every page load.

The footer's three social marks (`FOOTER_SOCIAL`) carry the words **"Connect
with us:"** in front of them, added 2026-10-31 after Frank looked for the links
and did not see them. The label is a `<span class="footer__social-label">` in
the markup, not a CSS `::before`: generated content cannot be selected and some
screen readers skip it. `.footer__social` needs `align-items:center` — flex
items stretch by default, which leaves the words at the top of the 42px icons —
and `flex-wrap:wrap`, because label plus icons is about 290px against a phone
column that can be narrower. The icons keep their own `aria-label`s; "Connect
with us:" does not say which is which.

**X was added 2026-11-05** (`x.com/OurNCTV`, the same handle as the Facebook
and Instagram accounts), after Instagram. All three marks are inline 24x24
SVGs written into `FOOTER_SOCIAL` — nothing in `assets/`, so adding one is a
content change and `ASSET_VER` does not move. It needed no CSS: the row is a
`gap:12px` flex of 42px circles, and at 375px the label and all three still
share one line with no horizontal overflow. A fourth would be the one to
measure, since that is where the row starts needing its `flex-wrap`.

**Controls are unselectable, and the list of them is explicit.** Frank,
2026-10-31: clicking the Book Festival logo on the home page sometimes turned
the pointer into an I-beam and lost the click. **Nothing declares
`cursor:text`** — every control already computed `pointer`, so the cursor was
never the fault. A press that drifts a pixel or two stops being a click and
becomes a text selection, and over a logo `<img>` it can start an image drag
instead; the pointer changes mid-gesture either way. Safari begins both more
eagerly than Chromium, which is why it shows for Frank and not in the preview
pane. The rule at the foot of `styles.css` gives every control
`cursor:pointer`, `user-select:none` and `-webkit-user-select:none`, and every
linked image `-webkit-user-drag:none`.

Three things about it are load-bearing:

- **It is a list, not `a{...}`.** Body copy, the footer address and the
  `mailto:`/`tel:` links must stay selectable — people copy those. Adding a
  new kind of button means adding its class to the list; verify.py checks all
  24 selectors and also checks that no blanket `a`, `p`, `body` or `*` rule has
  crept in.
- **`.btn--static` is excluded** with `:not()`. It is the span reading "Email
  info@ournctv.org" on `create.html`, which exists to be read off the page.
- **`button:disabled{cursor:default}` is restated after the list.** The 2,243
  pending agenda buttons carry `.watch-episode__link`, which is in the list and
  sits later in the file, so without the guard they would take the hand.
  `.photo-grid__item` needs no guard — its own `cursor:zoom-in` already
  outranks the bare `button` selector.

`search.js` is hand-edited too, but loads only on `search.html`. Five more
files are **generated** by `build.py` alongside the pages — never edit them,
and never count them as pages:

| file | what it is |
|---|---|
| `search-index.js` | every video card on the site, for `search.html` |
| `sitemap.xml` | the 35 pages, for crawlers |
| `robots.txt` | points crawlers at the sitemap |
| `404.html` | shown for any address that does not exist |
| `CNAME` | the host out of `SITE_URL`, which binds the custom domain |

**Never edit the generated `.html` files.** Any change there is destroyed on the
next build. Edit `build.py`, then run:

```
python3 build.py
```

It prints "Wrote 5 other files" and then "Wrote 35 pages". `OUT` is derived
from the script's own location, so it always writes beside `build.py`.

## The header

Rebuilt on 2026-10-29 at Frank's request: *"delete the header above the
navigation bar ... make the navigation bar have an attractive background
colour ... make the font and the logo larger ... keep the search bar where it
is. However, justify all the other menu items over to the left, next to the
logo."* Five things changed together, and they are load-bearing on each other.

**The status strip is gone.** The mono "ON AIR / Nantucket, MA / TV Channels"
band that sat above the nav is deleted outright, markup and CSS. It also took
a latent bug with it: the mobile drawer is `position:fixed` and opened at a
fixed offset from the top of the window, which was right once the page had
scrolled but overlapped the nav by the strip's height while it was still at
the top.

**The bar is dark now** -- `--nav-bg`, the same `#0C1826` as the footer, so the
page is bookended. It used to be the page's own background at 86% with a blur
over it, which barely read as a band and leaned on the strip above it for the
header to have any weight. **Re-theming it is that one token plus `--nav-ink`**
for the link colour; nothing else hard-codes either.

**The links sit against the logo and the search box is pushed to the far
end.** Before, `.nav__menu` took `margin-left:auto` and the whole group --
links and box together -- travelled right as a block. Now the menu takes
`flex:1 1 auto` and the *box* takes the auto margin. The box keeps its
`position:relative;left:calc(var(--gut) - 20px)` outdent, which is what puts
it 20px from the window edge rather than at the gutter; it is an offset and
not a margin so it never moves the links beside it.

**The logo and the type both scale with the window.** The logo was a flat
44px and is now `clamp(48px,4.1vw,62px)`; the links were
`clamp(1rem,1.25vw,1.28rem)` and are now `clamp(1.04rem,1.42vw,1.44rem)`.
62px is the logo's ceiling because `nctv-nav-lockup-white.webp` is 124px tall
and every image here draws at half the pixels it carries -- raise the ceiling
and you must re-export the asset.

**The wordmark is `assets/nctv-nav-lockup-white.webp`** -- play button to the
left of the type, which is the arrangement Frank supplied on 2026-10-29. It
arrives as black artwork on transparency and is recoloured: every pixel that
is not the green play button becomes white, alpha kept, which is
`g - max(r,b) > 30` picking the green out. The black original is in
`image-originals/`. **The tag carries a `?v=` now** -- it had none, so the two
swaps so far only got away with it by changing the filename; a third swap
under the same name would have been served from Safari's cache. `_NAV_LOGO`
near the `NAV` list builds the tag.

**The drawer starts at 1200px, not 1100px.** The band between those two was
always the tight one: it had a rule of its own robbing the header of its
gutter to buy forty pixels. A bigger logo and bigger type make it unwinnable
rather than tight, so the hamburger starts there and that rule is deleted.

Measured on 2026-10-29 at 1201, 1280, 1440 and 1920: no horizontal overflow,
the logo never below 2x density, the search box exactly 20px clear at every
width, and 60px of slack between the last link and the box at the tightest
desktop width. **That slack is the budget.** Anything else added to the
header comes out of it, so measure at 1201px and at 1920px, not at one width.
The nav still spans the window rather than keeping to the 1200px column, for
the same reason it always did.

The drawer carries the bar's colour down the page, so the dropdown inside it
drops its paper background and its links take `--nav-ink`. On the desktop bar
the dropdown stays a light card -- that still reads well against the dark.

## The logo cards, and why their hover is loud

The nonprofit grid (`.partner`, 15 tiles on **two** pages -- Nonprofit Videos
and the home page), the four Initiative Fund logos under it (`.partner
.cfn-fund`) and the Foundation's own mark (`.cfn-funds__mark`) are all links
whose entire content is a logo. Nothing else on the card says so. Frank raised
it on 2026-10-30 -- *"users won't know the logos are clickable"* -- and asked
for a hover that clearly shows the logo being selected, so the state is
deliberately strong: the card springs up 8px and grows to 1.04, a 3px green
ring draws itself around it, the paper warms to a 10% green, and the logo
steps to 1.09. One rule covers all three families.

Four things to keep:

- **The leading `a` in `a.partner:hover` is load-bearing, not decoration.**
  These tiles carry `data-reveal`, and `[data-reveal].in{transform:none}` near
  the foot of the stylesheet has the same specificity as a bare
  `.partner:hover`, so it won on source order. The old 4px lift had therefore
  **never run** -- the shadow and the logo scale did, which is why it looked
  merely weak rather than broken. Measured in the browser on 2026-10-30:
  `transform` computed to `none` while hovered. Check a hover rule that sits
  above that block by reading the computed transform, not by looking at it.
- **The ring is a box-shadow, not a thicker border**, so a selected card
  cannot reflow the grid around it. It also follows the card's own 16px
  radius, which an `outline` does not.
- **Keyboard focus keeps the real `outline`** and drops the box-shadow ring,
  so the two never double up. An outline survives forced-colours mode where a
  box-shadow is dropped. The rule also puts back `border-radius:16px`, because
  the global `:focus-visible` squares its target to 4px -- written for the
  small round controls, wrong on a card.
- **A scaled card needs `position:relative` and `z-index:2`** or its neighbour
  can paint over the growing edge. At 1440 the rightmost tile grows from 1256
  to 1260 against a 1200px column in a 1440px window, so nothing overflows;
  re-check that if the scale goes up.

The site's `prefers-reduced-motion` block kills every animation and transition
outright, so the ring and the tint still appear for a visitor who asks for
less motion -- just without the spring. That is the right trade: the
affordance is the point, the motion is the delivery.

A hover state does nothing on a touch screen. If the logos need to read as
clickable there too, that is a separate, persistent affordance -- not this.

## Services: two pages behind one nav item

`create.html` was a single top-level nav link reading **Free Services** until
2026-10-30, when Frank added the paid side of the work beside it. The nav item
is now a **Services** dropdown over `create.html` (Free Services) and
`services-professional.html` (Professional Services). The free page kept its
own file name, so every existing link to it, the "Become a member" button on
the home page included, still resolves.

The nav machinery needed nothing: `NAV` already takes a `children` list, and
`nav_html()` marks the parent current when any child is the page being built.
**The header's width budget went up, not down** -- "Services" plus a chevron
is narrower than "Free Services" was, so the slack at 1201px measured 75px
where the note above records 60. The search box still clears the window edge
by exactly 20px at 1201 and at 1920.

The new page is Frank's copy word for word, including his terminal
punctuation, which some list items carry and some do not. `SERVICES_PRO` is
the list **in his order**, which is his emphasis -- do not sort it the way the
partner sections are sorted.

**Two source-order traps were hit writing this page and the logo hover, both
the same shape.** A single-class rule cannot override another single-class
rule that sits further down this stylesheet, however specific it reads:
`.svc-head{margin-bottom:...}` lost to `.section__head{margin-bottom:...}`
silently, giving 56px where 20 was wanted. The fix is to qualify --
`.section__head.svc-head` -- rather than to move the rule, since moving it
only works until the next edit. **Read the computed value in a browser** when
a rule near the top of the file is meant to beat one near the bottom.

## Search

`search.html` searches every video on the site by title and by description.

`build_search_index()` in `build.py` runs **after** the pages are built and
reads them back: every `<article class="watch-episode">` on every page becomes
one record, `[youtube id, title, description, page index]`. It is written to
`search-index.js` as one assignment to `window.NCTV_SEARCH` — a plain script,
not JSON fetched at runtime, because the site has to work from `file://`. It is
about 2.1 MB, which is why only `search.html` loads it. Its `?v=` is a hash of
its own contents, not `ASSET_VER`, so a changed archive busts its own cache.

There are no placeholder partner pages left. All twenty have real
`.watch-episode` listings and are indexed; the Rossini Club was the last one,
built out on 2026-10-25. A page that shows `.video` cards titled "Video 1"
again would be a regression, not a page awaiting content.

`search.js` ranks the records. Two behaviours worth knowing before changing it:
a multi-word query returns only the videos matching **every** word (the best
available number of words, if none match all), and results are deduplicated by
YouTube id, because the NHA page cross-lists about forty of its talks under two
playlists on purpose.

**Everything on the page shares one global scope**, so `search.js` is wrapped in
an IIFE. It declared a bare `const PAGE` once and collided with a `PAGE` that
`site.js` declared at the time, which killed the whole script. `site.js` no
longer declares one, but the hazard is the shared scope, not that name.

## Cache busting — ASSET_VER

`ASSET_VER` near the top of `build.py` is appended to CSS, JS and image URLs as
`?v=NNN`. The site owner views the site in Safari, which caches aggressively.

**Bump it when you change `styles.css`, `site.js`, or any file in `assets/`.**
Do *not* bump it for changes that only affect generated HTML (text, titles,
descriptions) — the HTML isn't cached by that mechanism, so bumping is noise.

Read its current value from `build.py` — it changes several times in a working
session, so a number written here goes stale immediately.

## The site's address, and what a shared link looks like

`SITE_URL` near the top of `build.py` is the one place the live address is
written down: `https://www.ournctv.org`, which is what the homepage promo
announces. Every absolute URL on the site is derived from it — the
`rel="canonical"` link in each `<head>`, the Open Graph tags, `sitemap.xml`
and `robots.txt`. **If the site ends up on a different address, change that
one string.** Nothing else hard-codes it. `page_url()` turns a page name into
its address; `index.html` resolves to the bare root, so `/` and
`/index.html` never compete as two addresses for one page.

`META_DESC`, a few lines below it, holds the sentence Google prints under the
page title, one per page. **A page with no entry stops the build** — the
check sits just above the write loop and names the page. That is deliberate:
until 2026-10-28 all 33 pages then on the site shared one sentence, which made the Shorts Fest
page and the Civic TV page read identically in a search listing. The 20
partner pages are filled from `_PARTNER_ORGS` rather than written out
one by one.

The picture a shared link shows — on Facebook, Instagram, iMessage, WhatsApp
and X — is `assets/og-card.jpg`, built by `tools/og-card.py` from the
homepage hero photo at 1200x630 with the white NCTV mark over a scrim. It is
the one JPEG on a site that is otherwise WebP, because some scrapers still do
not read WebP. Re-run that script if the hero photo changes.

`404.html` is deliberately **not** in `files`: it is not part of the
navigation and does not belong in the sitemap, and GitHub Pages picks it up by
name. Because it is served for any missing address, including a deep one like
`/civic/2026/march`, every link in it is rewritten to start from the top of
the site after `shell()` builds it. An assertion fails the build if a relative
URL survives.

"The top of the site" is `BASE_PATH`, derived from `SITE_URL` — `/` at a
domain root, `/Test-Website/` for a GitHub Pages project site served from
under a repository name. **Set `SITE_URL` and the 404 page follows.** The 35
normal pages need nothing: they link to each other relatively and work at
either depth. Switching between a staging address and the live one is that one
line plus a rebuild, and the change is output-neutral at the live address.

`CNAME` comes off the same string. GitHub Pages reads a file of that name at
the top of the repository and serves the site under the host it holds; with
the file missing, the custom domain in the repository's settings switches
itself off and the live address answers 404. Deploying is copying this folder,
so **the build writes it** rather than leaving one hand-made copy to survive
being copied over — `_cname()` beside `_base_path()` takes the host out of
`SITE_URL`, one line, no scheme and no path.

It writes nothing for an address that is not a custom domain, and **never
deletes a CNAME that is already there**: a `*.github.io` host is what Pages
serves from anyway, and a project site under a repository name cannot carry
one at all, since the file claims a whole domain. So a rebuild at a staging
address leaves the live file alone instead of switching the domain off. The
`print` counts the list, so it says 4 or 5 according to what was actually
written.

## Keyboard and screen-reader basics

Two things every page carries, both emitted by `shell()`:

- A **skip link** — the first thing the Tab key reaches, letting a keyboard
  visitor jump the nine nav links and the search box. It lands on the first
  element of the page body, which `shell()` gives `id="main" tabindex="-1"`.
  The `tabindex` is what actually moves the keyboard: without it the page
  scrolls but focus stays in the nav.
- **A placeholder control is `disabled`**, not merely dimmed. The pending
  "Meeting Agenda" buttons are the case to remember: `videos-civic.html`
  carries 2,243 of them, and until 2026-10-28 they were focusable buttons
  that announced as actionable and did nothing. Dimming a control in CSS does
  not take it out of the tab order.

## Banner videos

Three pages carry a looping video banner: the home page, Shorts Fest and New
Moon Fest. All three are **Vimeo background embeds**, named in `build.py` as
`BANNER_VIDEO` (home) and the first argument of `video_hero()` (the other
two). The value is a Vimeo id and its private hash, `"<id>:<hash>"` -- the two
halves of a Vimeo share link.

`background=1` gives autoplay, muted, looped, and **no player controls at
all**. `dnt=1` asks Vimeo not to track the visitor. Vimeo also serves the
video, so none of it rides on our own bandwidth -- which is why the
self-hosted files were removed again.

**Do not move these back to YouTube.** Its player paints a transport strip
over the banner -- a pause button, a mute button, and prev/next whenever the
embed is set to loop -- for roughly the first four seconds of *every* load.
`controls=0` does not suppress it, `youtube-nocookie` behaves the same, and
nothing on our side can cover it, because it is drawn inside the cross-origin
iframe, dead-centre, where it cannot even be cropped out. Frame.io is worse
still: its share links are review pages with permanent controls and a
timecode, and a Frame.io staffer has said embedding is unsupported and may
break at any time.

Two details the embed needs:

- **It letterboxes.** An iframe has no `object-fit`, so `styles.css` oversizes
  it past the hero on whichever axis is short and lets `.hero__media` clip it.
  The `cqw`/`cqh` rule measures the hero box itself and is what actually runs;
  the `vw`/`vh` pair above it is a fallback that assumes a viewport-sized hero,
  true of the home banner but not the shorter event ones.
- **The photo holds until real frames arrive**, via Vimeo's own postMessage
  protocol (`addEventListener` / `play`), used directly so we need not fetch
  `player.js` for one event. Subscribe on the player's `ready`, never on the
  iframe's `load`: load fires first (about 130ms against 160ms), and the
  player silently discards a method call that arrives before it is ready.

### The banner that played perfectly inside a 0x0 iframe

Read this before touching `_HERO_SCRIPT`. It cost a full day, most of it spent
on confident wrong answers.

**Symptom.** In Safari, the first banner page of a session played. Every
banner page after it did not, including returning to one that had just worked.
Quitting Safari reset it. Chromium never reproduced it.

**Cause.** Safari refuses a renderer to an iframe inserted while a freshly
navigated page is still settling. The frame still loads and its contents still
run -- the Vimeo player reported `ready`, then `play`, then an advancing
`currentTime` with `paused=false` and a real `videoWidth` -- but the element
computes to `width:0;height:0` with `display:block`, `visibility:visible`,
`opacity:1`, `isConnected:true` and one client rect. An inline pixel width set
on it is simply discarded. A frame in that state never recovers, however it is
restyled.

It is not specific to Vimeo, to cross-origin content or to video. The proof
was a control frame: a plain same-origin `about:blank` iframe, hard-coded to
120x80, created on the same page at the same moment, which also measured 0x0.

**Fix.** `build()` loads the player, then looks again 1200ms later. If the
frame still has no box it is torn down and rebuilt from scratch, up to four
times, backing off 1200 / 2000 / 3000 / 4000ms. In practice the first retry
succeeds and the video appears about 3.2 seconds in; on an unaffected page
there is no retry at all and it appears in under a second.

That costs one discarded player load per retry, and an attempt was made to
avoid it by measuring the frame before setting `src`. **It does not work, so
do not try it again.** A just-appended iframe measures 0x0 in WebKit whether
or not it is going to get a renderer, because layout is deferred, so the check
reported failure on every page -- including ones that were about to play
perfectly -- and twelve rapid retries chased a phantom. A `requestAnimationFrame`
would be the obvious next idea; the window here lasts seconds, not frames.
The only reliable test is to look a while later, which is what this does.

**Also keep:** `show()` reveals only a player that occupies space (`boxed()`).
The player's own word is not evidence that anything is on screen, and trading
a good photo for a box with no pixels in it is worse than not playing at all.
With that in place the worst case is a still photo, which is a fine banner.

**Dead ends, recorded so nobody pays for them twice.** A stale cached script;
Safari's autoplay policy; the per-site Auto-Play setting; decoders retained by
the back/forward cache; a content blocker hiding the frame (ruled out in a
private window); and container query units. That last one is why the cover
crop is computed in JS now -- `container-type:size` on `.hero__video` with
`cqw`/`cqh` on the iframe was suspected and removed, and the bug survived it
unchanged. The JS sizing is kept because it is deterministic and rests on no
feature support, not because the units were at fault.

**The lesson worth keeping:** a health check that only asks the player how it
is doing will report a healthy player in an invisible box. Measure the
geometry. The readout that solved this printed the element's own computed
width beside the inline width we had set, and the answer was visible in one
line after a day of asking the wrong questions.

### Releasing the player on navigation

`_HERO_SCRIPT` is a `build()` / `teardown()` pair that releases the player on
`pagehide` and rebuilds on a `pageshow` with `event.persisted`. This was
written as a fix for the bug above and did not fix it; instrumentation later
confirmed teardown had been running correctly all along. It is kept because it
is right in its own right: Safari holds a navigated-away page whole in its
back/forward cache, player included, and a background video is worth giving
back. The structure also carries the `ResizeObserver` disconnect and the retry
bookkeeping. `teardown()` blanks `frame.src` before removing the node, and
`pagehide` strips `is-playing` so a restored page shows its photo while the
new player boots.

### The fallback photos are the videos' own first frames

Each banner's fallback is a still of the first frame of that banner's video,
so the photo and the video's opening frame are the same picture and the
cross-fade into playback is invisible. Before this they were unrelated stills,
and the home page cut from a bright daylight exterior to a night aerial, which
read as a fault rather than a transition.

| page | fallback | video |
|---|---|---|
| index.html | `hero-fallback-home.webp` | night sports field |
| events-shorts-fest.html | `hero-fallback-shorts.webp` | tall ship in the harbor |
| events-new-moon-fest.html | `hero-fallback-newmoon.webp` | Siasconset Casino exterior |

**Replace a banner video and the fallback has to be re-extracted with it**, or
the banner jumps on every load. How they were made: fetch the player config
from `player.vimeo.com` with a `Referer`, read `request.files.hls.cdns`, pick
the highest-resolution rendition from the master playlist, and pull frame one
with ffmpeg (`imageio_ffmpeg` supplies the binary; there is no system ffmpeg).
`-ss` before `-i` is what works on these streams -- input seeking past the
first segment fails, so use output seeking for anything later. Then 1920 wide,
WebP, quality 88. yt-dlp does not work on these.

Two things that have to stay in step for the trick to work:

- `.hero__fallback` must keep `object-position:center`. The iframe is centred
  by its own transform, so any bias on the photo makes the two disagree. It
  was `center 38%` while the fallback was an unrelated photo of the building.
- The fallback's aspect ratio should match the video's. Both are rendered
  cover into the same box; equal ratios mean equal framing.

Both festival videos used to carry baked-in letterbox bars -- 177px on Shorts
Fest, 150px at the top on New Moon -- and that was the documented reason not
to make either banner taller: at `min(86vh,760px)` the cover crop scales to
fit the width and shows the video's full height, bars and all.

All three banner videos were replaced across 2026-10-30 and 10-31 and **none
of the replacements has them**, measured at five points through each run,
which is what made it safe to raise both festival banners to the home hero's
height:

| page | video | id | master on Frank's Desktop |
|---|---|---|---|
| Home | *Website Splash* | `1241589049:76cd5a88fc` | `~/Desktop/Website/Website Splash/Export/Website Splash.mp4` |
| New Moon | *New Moon Fest Highlights_Final* | `1241568900:0350ef0ccc` | `~/Desktop/Website/NMF/New Moon Fest Highlights_Final.mp4` |
| Shorts Fest | *Shorts Fest Hero_Final* | `1241561028:9873c01443` | `~/Desktop/Website/Shorts Fest/Shorts Fest Hero_Final.mp4` |

**Match the master to the upload before extracting from it.** The Website
Splash folder held two plausible files; the one Frank uploaded was identified
by duration, read off the player's own `<video>` element (100.625s against the
master's 100.63s, the other candidate 100.17s), then confirmed by comparing a
32x18 luminance grid of the opening frame -- mean delta 5.47, which is what an
HLS re-encode of a dark scene costs. Guessing by filename alone would have
shipped a still from the wrong cut, and it would have looked fine.

**The home fallback is a night scene, and its sky row maxes at 21.** The
`< 24` dark-row test the other two fallbacks use calls that a letterbox bar.
`verify.py` tests the home one against `< 6` instead -- a real bar is encoded
black and survives q88 at 0-3 -- with a comment saying not to tidy the
threshold up to match. See "A dark banner is not a broken banner" below.

**All three fallbacks carry `?v={ASSET_VER}`.** The home one did not until
2026-10-31, which went unnoticed only because the file had never been
replaced; the moment it was, a returning visitor would have kept the old photo
behind the new video and watched it jump on play. `video_hero()` now appends
the version too, and `verify.py` checks all three.

**Check a replacement video for bars before raising a banner**; `verify.py`
checks the shipped fallback's top and bottom row, which catches it after the
fact. Both fallbacks came from their master's frame one directly rather than
off the HLS stream -- easier, and first-generation, whenever Frank still has
the file. He also exports a `* Hero Still.png` beside each master; they match
frame one to within a rounding error.

### The banners carry the festival's title card

`hero_title_card()` beside `video_hero()` lays a logo and two sentences over
the footage, and `video_hero(overlay=...)` renders it with the scrim. Both
event pages use it; it replaced the intro band that used to sit under each
banner, so a page says its lead and standfirst once. Those
`*_intro_section()` functions are still in `build.py`, unused, with their
rules in `styles.css`; restoring either is one line in that page's body, and
each sponsor band's tight top padding is scoped to `.X-intro + .X-sponsors`
so it comes back with it.

The two logos need opposite treatment, which is why the artwork is a
parameter. New Moon's canoe mark is one flat ink at `#084C6E` and would vanish
into the footage, so it ships as `newmoon-logo-white.webp` beside the blue
one -- made by keeping the alpha channel and replacing the colour, on the
2034px original before scaling, so the antialiased edges resample as white
rather than as blue gone pale. Shorts Fest's clapperboard is multi-colour on
its own near-black board and already reads on dark; there is no white cut of
it to make. Sizes differ too (`--card-logo`): the canoe is wide and low, the
clapperboard nearly square.

The standfirst is deliberately **not** given `.hero__sub`'s clamp, whose 1rem
floor would set it at 16px on a phone. It is the page's introduction, the same
words that sat at a flat 20px in the band, so its floor is 1.15rem.

### A dark banner is not a broken banner

Chasing the above, a lot of time went into the home video looking black. It is
not. `Webpage Splash 3` is a 100-second montage that opens on a night-time
aerial of a football field: mean luminance about 40/255 over its first 16
seconds, and 7/255 at the 16-second mark. `.hero__scrim` then lays navy over it
at 55% opacity at the top and 82% at the bottom, which brings the banner to
roughly 26-31/255. The fallback it cross-faded from, `front-door.webp`, was a
bright daylight exterior. That is no longer the case -- the fallbacks are the
videos' own first frames now, and `front-door.webp` has been deleted; only
`tools/og-card.py` still wants that photo, and it reads the original. Bright photo to near-black video reads as a failure
even when every part of the mechanism is working. Measure the footage before
instrumenting the page.

### Why the reveal timer is armed, then disarmed

`_HERO_SCRIPT` sets `var timer = setTimeout(show, 8000)` and clears it the
moment `ready` arrives. That shape matters, and the obvious simplification --
"just reveal on a timer" -- is the bug it replaced.

It used to be `setTimeout(show, 2000)` with no clear, so the photo came down
after two seconds whether or not a single frame had painted. None of these
videos has a progressive file; they are **HLS only**, so a first frame costs
the player bundle, a master playlist, a media playlist and a media segment.
Measured here on a warm cache, `ready` landed at 140-153ms but `play` at
717ms, 1003ms and 1000ms -- already half the old budget with everything
going right. A cold cache, a thin connection, Safari's per-site **Auto-Play**
set to "Never" (and `localhost` is its own site, so it can differ from the
live domain), Low Power Mode, or a blocker on `player.vimeo.com` all pushed
past 2s, and the page threw away a good photo to show an empty black iframe.

So: `ready` is proof the player is talking to us. Once it arrives, the timer
goes and we wait for the real `play` however long it takes -- a video that
never plays simply keeps its photo. The timer now exists only for a player
that never says anything at all, which is why 8s is affordable; the thing it
is racing is a fallback photo, not a blank box.

Two ordering rules inside that handler, both load-bearing:

- `clearTimeout(timer)` sits **after** the subscribe `postMessage` and
  **inside** the same `try`. If the subscribe throws, `play` will never come,
  and the timer has to still be armed to rescue it.
- Nothing but `play`/`playing` may call `show()` once the timer is cleared.
  Add another reveal path and the old bug comes back by the back door.

`prefers-reduced-motion` returns before any of this and keeps the photo, by
design. A banner showing a still photo is not a fault; a banner showing black
is.

`shell()` derives each page's preconnects from its own body -- Vimeo's two
hosts when the page holds a player embed, `img.youtube.com` when it holds a
thumbnail -- so the hosts can never drift from what the page actually loads,
and a page that uses neither pays for neither. Fonts are on every page and
stay in the markup. Do not hand-list a host here again: the previous pair
pointed at `www.youtube.com` and `i.ytimg.com`, and neither was ever fetched.

Two things live outside the repo and can bite: the Vimeo plan has to keep
`background=1` available, and each video's "where can this be embedded"
setting has to allow the live domain.

The second one did bite, on 2026-10-31: *Shorts Fest Hero_Final* played on
vimeo.com but refused to embed, and the banner showed Vimeo's "Because of its
privacy settings, this video cannot be played here" through the reveal timer
-- an error page is still a boxed iframe, so the 8s backstop shows it. Frank
changed the setting and nothing in the repo moved. **Diagnose it with oEmbed
before touching any code**, because a wrong id and a blocked embed look the
same on the page:

    https://vimeo.com/api/oembed.json?url=https%3A%2F%2Fvimeo.com%2F<id>%2F<hash>

Full JSON means the id and hash are right and the video is embeddable; 403
means it is not, and the fix is on Vimeo. Compare against a banner that does
work -- they are all on the same account, so a difference is the per-video
setting. A share link copied out of Vimeo carries `?share=copy&fl=..&fe=..`;
that is the share dialog's own tracking, not part of the address, and the
page's `og:video:url` shows the real one.

Self-hosted MP4 banners were built and measured first, then removed when
Vimeo was chosen; `tools/hero-video.py` went with them. The source videos are
on the owner's Desktop, outside the repo. If self-hosting is ever wanted
again, the encode settings that worked are in Claude's project memory.

## Sports: SPORTS_VIDEOS is not only games

`SPORT_SEASONS` holds the Fall/Winter/Spring button rows; `SPORTS_VIDEOS` holds
the cards behind each button, keyed by sport then school year. Two things in
there will mislead you if you skim:

**The second field of a `SPORT_SEASONS` entry is dead data.** It is a YouTube
playlist URL, `sport_buttons()` unpacks it as `url`, and it is never emitted
anywhere. Cross Country and Golf carry `""` because no playlist exists for
them. Don't go hunting for one, and don't assume a missing URL is a bug.

**Every list is newest-first, by the date printed in the card title.** Frank
asked for this on 2026-11-05; until then all 59 lists were oldest-first. The
order lives in the data here, unlike the Civic page, so a new card goes at the
**top** of its season. The date comes in five forms -- `September 14, 2026`,
`Nov. 7 2024` with no comma, `12/28/2021`, `12/22/22`, and one Girls Soccer
card reading `27 de septiembre de 2025` -- so read the title, not the shape
you expect. Upcoming games sort on their dates like anything else, which puts
the furthest-away game at the top of an all-upcoming season; Frank confirmed
that reading the same day and asked to keep it. `verify.py` checks every
list from the built page.

**A card whose title has no date is dated by `SPORT_CARD_DATES`.** 27 of them
exist -- the 22-23 Basketball, Hockey and Lacrosse runs, where the title is
often just `Whalers Boys Varsity Lacrosse`. Until 2026-11-05 nothing could
place such a card and it kept whatever position it landed in; Frank's rule now
is the **streaming date**, or the posting date when the video was never a
stream. The table sits under `SPORTS_VIDEOS` in build.py, renders nothing, and
holds yt-dlp's `release_date` with `upload_date` as the fallback.

Use `release_date`, not `upload_date`: those games began in the evening
Eastern, so their UTC `upload_date` is the next day and would date every one of
them a day late. All 27 were already in the right place under the new rule, so
adding it moved no cards.

`verify.py` **fails** on an undated card that is missing from the table, which
is the point -- a card with no date anywhere has no position the rule can
derive, and silently leaving it where it fell is what the table replaces. The
Civic page has the same arrangement in `CIVIC_CARD_DATES`.

**Not every card is a game.** Cross Country and Golf (added 2026-10-30) hold
*Spotlight* features — NSC's profiles of the teams it cannot carry on a live
broadcast. They have no opponent in the title, no `vs.`, and no Instagram
highlight reel, so `civic_card` greys their Highlight button out. That is
correct, not a gap to fill. `SPORT_UPCOMING` still says "This game is
upcoming", which would read oddly on a Spotlight; nothing uses it there yet.

**Choosing a sport opens its most recent school year.** Asked for on
2026-11-03. `autoOpenNewestYear()` in `site.js` runs at the end of the
sport-button handler: it finds the sport panel's own enabled `.year-btn`s and
clicks the one with the greatest `data-year`. Every sport gets this, so the
games are on screen after one click rather than two.

This replaced `autoOpenLoneYear()`, which fired only when a sport had exactly
one year — true of Cross Country and Golf alone, leaving the other thirteen
sports a click short.

Four things about it are load-bearing:

- **It reads `data-year`; it names no sports and counts nothing.** The greatest
  label wins. `sport_year_picker()` emits `sorted(...)`, so that is also the
  last button today, but reading the attribute means reordering that loop
  cannot quietly break the feature. Every label is `School Yr NN-NN`, so a
  string compare is a date compare — only a century rollover would need
  rethinking.
- **Disabled buttons do not count.** A greyed year has nothing behind it. The
  spring sports are the live case: Lacrosse, Softball and Baseball stop at
  25-26 until their 26-27 seasons are played, and the newest year they really
  have is the right one to open.
- **It clicks the button instead of setting the classes.** The year picker's
  handler unhides the panel and starts the reels, and a separate listener on
  `.year-btn` re-measures the descriptions. Styling the button by hand here
  would skip both, and the clamp is the one that would rot quietly — a
  description has no measurable height until its panel is showing.
- **It runs after the panels loop, never inside it.** `startReels` skips
  anything still inside a `[hidden]` ancestor, so the sport panel has to be
  visible before the year beneath it is opened.

It bails out if any year in that picker is already showing, which means the
panel never closed: clicking then would either toggle the open year shut or
discard a year the reader had chosen. Hiding a sport panel runs `clearPicks`
over its year buttons, so a reopened sport always starts with none active and
the newest year opens again.

The year button still toggles, so pressing the open year collapses it and
leaves the sport showing an empty picker. That is the pre-existing
`yearpick--toggle` behavior, not something the auto-open introduced.

**Resolved: the card that pointed at the wrong game.** `SJEJ-n9dEzw` sat in
Volleyball 26-27 titled *"vs Monomoy Sharks - October 21, 2026"* while the
video is *"vs Nauset Warriors - October 28, 2026"*. On Frank's instruction
(2026-10-30) the card was repointed at the Nauset game: YouTube's title, its
description verbatim, `upcoming` cleared. There is no Monomoy volleyball
fixture in 26-27 — the only one on the channel is `lFVVlYevKH0` from **25-26**
(Sept 29, 2025), which is correctly titled and still plays — so the Oct 21
card had almost certainly been built from the published schedule and never
reconciled after the fixture changed.

The lesson worth keeping: **a card made from a schedule is a claim, not a
record.** Update_SC step 4 only resolves ids, so it cannot catch a card whose
id is alive but whose *title* describes a different game. That mismatch is
only visible by reading the video's own title against the card's, which is why
step 1 resolves every link before wiring it up. No Highlight reel exists for
the Nauset game — the newest reel on the grid post-dates it — so its Highlight
button is correctly greyed.

**Stale `upcoming` flags and dead links are swept, not fixed by hand.**
Update_SC step 4 (added 2026-10-30) walks every card flagged `upcoming=True`
and resolves each id: one that has aired gets its flag flipped and YouTube's
description pulled in, and one whose video no longer resolves gets **deleted**,
because a dead embed promises a game nobody can watch. Three cards went on the
first sweep — `LxD6pzjhw7s` (Girls Soccer vs. Archbishop Williams) and the two
`POSTPONED` cards, `hvuN8XTDi_w` and `lveKgp1EPOk`. Their exact tuples are
archived in the session scratchpad.

Two traps are already paid for, so don't rediscover them:

- **Availability comes from `yt-dlp`, never from oEmbed.** YouTube's oEmbed
  endpoint returns **401 on public 2021-22 live streams** — six of them in this
  file. Deleting on an oEmbed failure would have taken out six working cards.
- **The title's date is not evidence.** `txPt6UGEmeY` was titled *"Girls Soccer
  vs. St. John Paul II Lions - October 20, 2026"* and flagged upcoming, and
  YouTube says the stream begins **two days from Oct 30** — NSC moved it and
  left the old date in the title. A "past date plus upcoming flag" rule would
  delete a game that has not happened yet. The video's status decides.

**But a stale date is still a bug, and the card now gets re-dated.** Frank
found that one on 2026-10-31, eleven days after its printed date had gone by.
Update_SC step 4 used to leave a still-scheduled card *completely* alone, title
included, which is how it survived. The amended rule splits the two things the
sweep was conflating:

- **The flag and the description stay** — the game has not happened, so
  `upcoming` stays `True` and the description stays empty.
- **The date is re-synced.** yt-dlp's **`release_date`** is the scheduled start
  and is authoritative for an `is_upcoming` video. Compare it with the date in
  the card's title on every sweep and rewrite the title when they differ. Keep
  the site's typography — `&rsquo;` against YouTube's straight apostrophe is
  not a mismatch.
- **Pass `--ignore-no-formats-error`** to `yt-dlp --dump-json`, or the dump
  fails whole on *"This live event will begin in N days"* and `release_date`
  never comes back. That flag is the whole reason the date was unreadable
  before.
- **Only for scheduled streams.** An aired video's upload date and game date
  can legitimately differ, so those disagreements stay flagged for Frank, not
  fixed. `txPt6UGEmeY` now reads **November 2, 2026**; the 2026-10-31 sweep
  checked all 28 upcoming cards and the other 27 already matched.

**A Spotlight's facts come off the home page, not off YouTube.** Both premiered
as `NEWS` cards first, and those cards carry the opponent, the venue and the
date of the competition filmed. The YouTube descriptions give the coach and the
season record and name neither a date nor an opponent, so both sources are
needed and neither is sufficient. The two disagree on one spelling: the news
card says **Gardner Farm**, YouTube says "Gardner Farms". The site's own wording
won; it is unresolved.

**Coaches are named, student athletes are not.** Sam Herrick (golf) is burned
into the video as an on-screen lower third, so that spelling is confirmed by the
footage itself. Matt Phipps (cross country) comes only from NCTV's own YouTube
description — better than captions, but not corroborated. The cross country
thumbnail's lower third names the runner being interviewed; she stays out, under
the usual rule. See the naming rules in the video-description notes.

## The film-strip banners — cropped, not scaled

Four pages carry a still image rather than a video banner: Civic TV, and
Sports Connection, Nantucket Life and Nonprofit Videos since 2026-10-30. All
four use the same artwork template and the same mechanism, so **keep
`civic_banner()`, `sports_banner()`, `nl_banner()` and `np_banner()` in step**
— and the two CSS rules under each. The
artwork is a strip of film holding five photo frames at 4.66:1, and `width:100%`
on a shape that wide collapses it: at 375px the strip rendered **80px tall** and
nothing inside the frames survived. The fix is a `<picture>` in `civic_banner()`
that drops whole frames off the right as the screen narrows, spending width the
phone hasn't got to buy back height it has.

```
  under 460px   Gov_Banner-xs    840x429   2 frames   1.96:1   375px -> 192 tall
  460 - 759     Gov_Banner-sm   1231x429   3 frames   2.87:1
  760 - 1099    Gov_Banner-md   1621x429   4 frames   3.78:1
  1100 and up   Gov_Banner      2000x429   5 frames   4.66:1   1440px -> 309 tall
```

Rendered height stays between 160 and 309px at every width from 320 up, where
before it ran from 80.

**Don't hand-pick the crop widths, and don't write them down.**
`tools/crop-banner.py` finds the strip colour, the photo band and the gutters
by looking at whatever is in `assets/`, derives the widths from them, writes
all three crops, and then fails if `civic_banner()` disagrees with what it just
wrote. Run it; read what it prints.

That is not caution for its own sake. The artwork was replaced **four times**
on 2026-10-30. The second swap changed the strip from `#444` to black and moved
one crop width (1232 → 1233); the fourth moved **all three**, and the sliver
with them, while looking all but identical to the third. Numbers typed in by
hand would have cut those banners in the wrong places and still produced files
that looked entirely normal. So would a gutter detector that knew what shade
the strip was.

**The strip is `#0D1826`, which is `--nav-bg` to within a rounding error.** The
match is unenforced — the banner is a picture, so no token reaches inside it —
so `verify.py` reads both and fails if they drift apart. Recolour the nav and
you will be told, rather than finding out by eye later.

**The sprocket holes are transparent, not painted white**, as of the fourth
version. They show whatever sits behind the banner, which is `--fog`, so they
read as soft grey. Two things follow. `.civic-banner` must never take a
background of its own, or the holes change colour with it. And every crop has
to keep its alpha: Pillow will drop it on a re-encode it does not expect, and a
crop that lost it paints those holes **black**. `verify.py` checks both.

**`.civic-banner` carries `padding-top:2px`**, asked for once the strip matched
the nav and the two ran together, set at 5px and trimmed to 2px the same day.
It is a hairline on purpose; don't round it up. Padding rather than margin so
it cannot collapse, and the band shows `--fog` — the same colour as the holes,
so it reads as part of the perforation instead of a rule under the nav.

**Replace the artwork and you must re-run that tool**, exactly as replacing a
banner video means re-extracting its fallback frame. Nothing about the markup
or the file sizes would look wrong if you didn't; the crops would just be
slices of a banner nobody uses any more. `verify.py` catches that too, by
sampling each crop against the master now in `assets/` and failing if they
diverge — so run it after any swap.

A crop never ends on a gutter. The master doesn't either: it runs ~54px into a
sixth frame, so the strip reads as continuing past the edge of the page, and
every crop carries the same sliver so all four sizes end the same way.

Two smaller traps that cost real time:

- **`width`/`height` belong on the `<source>` tags, not just the `<img>`.**
  They aren't a size — the CSS still does the sizing — they hand the browser
  the aspect ratio of whichever source it picks. Put them only on the `<img>`
  and every width reserves that file's 1.97:1 box, so the desktop page lurches
  as the real banner lands.
- **Source order is load-bearing.** A `<picture>` takes the *first* `<source>`
  whose media matches, so they run widest-first and the `<img>` is last.
  Reorder them and every screen gets the 2-frame crop.

One alt text covers all four, because `<picture>` has no per-source alt. It
describes the whole artwork rather than the two frames a phone shows: a screen
reader user then gets the same account of the strip at every width, which is
the more useful of the two readings.

### The other three strips

Frank replaced Sports Connection, Nantucket Life and Nonprofit Videos on
2026-10-30, each time asking for it to be formatted like the Civic one, so all
three are: `<picture>`, four crops, the same three breakpoints, the same two
CSS rules (`padding-top:2px` on the section and `picture{display:block}` under
it), one alt for all four sizes.

```
                    Sports   NL     Nonprofit
  under 460px   -xs    840    846    840    375px -> ~191 tall
  460 - 759     -sm   1230   1235   1231
  760 - 1099    -md   1621   1620   1621
  1100 and up   master              2000    1440px -> 309 tall
```

**The four banners' widths differ by a few pixels and that is fine.** Each
states its own in its own markup, `verify.py` reads the rest off the files, and
the only hard rule is that a crop must be at least as wide as the band it
serves — which is checked. Nantucket Life's frames are not all one width (378,
359, 363, 367 against Civic's steady 390), so its cuts land where its own
gutters are.

**`tools/crop-banner.py` takes the banner as an argument now** — no argument
means Gov_Banner, as the Civic notes above say, and `Sports_Banner`,
`nl-banner` or `nonprofit-banner` cuts the others. Nothing else changed about
the cutting; the Civic crops come out byte-identical to the hand-checked ones
after every edit made to that tool, which is the regression worth re-running.

Five things these swaps taught, all of them general:

- **Both new strips open mid-picture, where Civic opens on a 9px margin.** So
  the cuts are counted *back from the right*, one whole frame at a time,
  rather than forward from the start. Counted forward the banners disagree
  about what "four frames" means and the widest Sports crop comes out 2000px —
  no crop at all. It also means the two new banners' crops hold one fewer
  whole frame than the Civic ones at the same width, which is correct, not a
  miscut.
- **One pixel is not a safe sample for the strip colour.** `measure()` read
  `px[w//2, 2]` and got `(17,24,37)` at 191 alpha on the Sports artwork,
  against a strip that is really `(13,24,38)`. It happened to survive the 45-wide
  tolerance; a sample that landed on something bright would have inverted the
  whole measurement. It takes the commonest fully opaque colour across the top
  rows now, and `verify.py` reads it the same way.
- **An export can arrive flattened, and nothing about it looks wrong.** The
  Nonprofit banner's first version came as RGB with no alpha channel at all,
  its sprocket holes filled pure white instead of cut out, and a 1px line of
  (222,228,235) across row 0 where the others have a transparent row. On the
  page that is bright white perforation beside three banners whose holes are
  `--fog`. Frank sent a properly cut-out replacement within the hour, so what
  is in `assets/` is his file byte for byte and no repair is applied to it —
  but the repair exists for the next one. `tools/banner-unflatten.py` puts a
  flattened strip back: a filled hole is *white over strip*, so how far a
  pixel has travelled from the strip colour toward white is its coverage, and
  alpha is the inverse of that — which reproduces the antialiased edges a
  threshold would jag. It touches nothing inside the photo band, nor within
  8px of it, because a light photo bleeds a pixel or two past the boundary;
  without that margin rows 81 and 344-345 came out at alpha 38, a faint light
  speckle drawn along every frame edge. It got that artwork to 30 holes a band
  and 9.1% transparent against the siblings' 8.8-9.1%, which is how you check
  it worked. **Say that the holes are wrong rather than only fixing them** —
  the artwork is Frank's, and he had a correct export to hand.
- **A stray bright line at the very edge broke the band detection.** That
  flattened row 0 is 89% off-strip, so `rows[0]` put the photo band's top at 0, which
  pulled the gutter scan up through the sprocket holes and lost two of the
  five gutters — and the crop widths that came out of it, 1611/1221/820, were
  plausible enough to ship. `measure()` takes the **longest run** of photo
  rows now, not the first to the last. One pixel at the edge is never the
  photo band.
- **The old Sports banner had no `?v=`.** It was one flat 1920x411 image with
  `alt="Nantucket Sports Connection"`, duplicating the page's own `<h1>`, and
  the new file has the same name — so without the version query Safari would
  have served the old one from cache forever. The same trap the nav logo hit.
  The Nantucket Life and Nonprofit banners already carried one, which is the
  only reason those swaps did not need the same repair. **Every one of these
  is an `assets/` change, so `ASSET_VER` moves**: 397 to 398 to 399 to 400,
  and to 401 for the Nonprofit banner's second version.

`verify.py` runs the whole banner block over all four pages from one list, so
a check written for any of them covers the others. Every superseded banner and
its source is in `image-originals/superseded/` — `Sports_Banner-old.*`,
`nl-banner-old.*` and `nonprofit-banner-old.*`, beside the Civic pair —
plus `nonprofit-banner-filmstrip-flattened.webp`, the first film-strip
version, named the way the three superseded Gov_Banner revisions are. Nothing
was deleted.

**Check a CSS rule by its selector list, not by searching the stylesheet for
it.** The four banners share their rules now, so `.nl-banner{padding-top:2px}`
is nowhere in the file while `.nl-banner,.np-banner{padding-top:2px}` is — and
that string *contains* `.np-banner{padding-top:2px}`, so a substring test
passed one class by accident while failing the other. `verify.py` splits the
rules and matches the selector exactly, stripping comments first, or the
paragraph above a rule is read as part of its selector list.

## Latest NCTV News — the home page carousel

Added 2026-10-30, replacing the "Around the Island" month calendar, which was
scaffolding: twelve month buttons over twelve grids of six empty camera icons,
and not one real photograph in any of them. `MONTHS`, `calendar_block()`, the
`.calendar__*` / `.photo-ph` / `.head-row` / `.head-seagull` rules and
`initCalendar()` all went with it. `assets/seagull-camera.webp` is now
unreferenced; it was left in place rather than deleted.

The section sits below Featured Video (Frank moved the video back above it on
2026-10-30, having first asked for the reel on top) and shows one card at a
time, centred on the page: a large dated polaroid graphic, with the card before it and the
card after it shown small on either side, its paragraph centred underneath,
then a back arrow, a row of dots and a forward arrow. It turns itself over
every twelve seconds (Frank, 2026-10-30).

**The big card is a link**, to wherever its own paragraph's first "click here"
goes. build.py reads that address back out of the copy rather than keeping a
second copy of it, so changing the link in a paragraph moves the card with it.
The Island Cup paragraph has two links and takes the first, the live
broadcast, not the documentary. The Chris Morris paragraph has none, so that
card is a plain picture and does not lift under the pointer.

Above the section's own label is the **mailing-list sentence**, pointing at
Frank's Constant Contact sign-up page (`NEWS_SIGNUP_URL`). Frank asked on
2026-10-30 for it to be set exactly like the "Do You Have A Story?" notice on
the Shorts Fest page, so `.newsreel__signup` is **added to that rule's own
selectors** rather than given a copy of its declarations: green Space Mono at
20px, spanning the page, upright. Restyle one and the other follows, which is
the point. Everything `.newsreel__signup` keeps for itself is the gap down to
the section label.

The paragraph is set at **1.4rem, the same size as the section headings** --
the one over the partner logos, for instance -- and runs the full page column
rather than a narrow measure (Frank, 2026-10-30). The eyebrow above it uses
`.section__head--tight`: the standard gap under a section head is sized for a
label plus a sentence, and left a hole above the first card.

The two small cards are **one `<img>` each**, whose `src` site.js moves along
with the big card -- not six more copies of the markup. Both files are already
in the browser from the track, so the swap is instant. A mouse can click them
to go that way; they carry `tabindex="-1"` and `aria-hidden="true"`, so the
keyboard and a screen reader get the arrows instead of being offered the same
move twice. They drop away below 900px, where three cards cannot share the
row and still leave the middle one readable.

**To add an item, put it at the top of `NEWS` in build.py.** The list is in
newest-first order by the date printed on the graphic itself, and everything
else counts itself from the list: the dots, the `n of N` labels, which card
loads eagerly. Nothing in site.js or styles.css needs touching.

Each item carries that printed date in `date=`, and the paragraph opens with
it. verify.py parses those six dates and fails if the list is not in
descending order, so the rule is enforced rather than just written down here.
Read the date off the card before typing it: in that brush face a 9 is easy to
take for a 7, which is how the golf card spent a day in the wrong place.

Three things about it that are easy to undo by accident:

- **The cards are stacked in one grid cell** (`grid-area:1/1`), not hidden one
  at a time. That is what makes the box as tall as the longest card, so the
  page below it does not jump every seven seconds. Swap it for `display:none`
  and the whole page starts hopping. The cost is paid the other way: on the
  five shorter cards there is empty space between the text and the arrows,
  most noticeable at phone width, where the longest card runs five lines and
  the rest run three. That is the trade, and the still page is worth it.
- **A card that is not showing is `visibility:hidden`, not just transparent.**
  Opacity alone would leave six cards' worth of links in the tab order and in
  a screen reader, five of them invisible.
- **The middle column of the stage is `minmax(0,520px)`, not `auto`.** An
  auto column asks the image for its max-content width, gets the file's
  1080px, takes the whole row, and leaves the two small cards at zero width.
- **The first card carries `is-current` from build.py**, not from site.js. With
  JavaScript off the section is that one card and its paragraph, rather than
  an empty box the height of the tallest.

The clock stops while the pointer is over the section, while the keyboard is
inside it, and while the tab is in the background. Anything the visitor does —
an arrow, a dot — restarts the seven seconds from that card, so the card they
asked for gets a full turn rather than the tail of the one already running. A
visitor who has asked for reduced motion gets no automatic advance at all; the
arrows are how they get through the set.

The podcast card's link is a second short URL for the **same** Google
appointment schedule `BOOK_PODCAST` on the Create page points at: both
`calendar.app.google/uscVAZHWcLDqj9ot6` and `.../TzZCpJUT8cxB6bBd6` redirect
to the one "NCTV Podcast Slot" schedule. They are left as Frank supplied them.

The graphics are 1080x1300 **RGBA** WebP at quality 88, the full size of
Frank's originals in `../image-originals/news-*-original.webp`, and the card is
drawn at 520px so there are two pixels of image per pixel of screen. Enlarging
the card past 520px means going back to Frank for bigger originals, not scaling
these up.

**The polaroids are cut out of their background** -- transparent corners and a
slightly ragged edge, about 11px of clear margin all round. So they are saved
RGBA, never flattened to RGB, and their shadow is a `filter: drop-shadow`, not
a `box-shadow`: a box shadow draws a hard rectangle in the clear corners. The
versions they replaced, which were opaque white rectangles, are in
`../image-originals/superseded/`.

Every link in the copy was resolved
before it went in. The two in the Island Cup card are deliberately different
addresses: the first is the scheduled live broadcast, the second the
documentary.

## Clickable sponsor logos

Four banners carry them now. Two mechanisms, both laid over ONE flat image, both
positioned in the artwork's own pixels so the overlay rescales with the picture:

| where | helper | shape |
|---|---|---|
| Shorts Fest top banner | `disc_sponsor_links()` | centre + radius |
| New Moon Fest top banner | `disc_sponsor_links()` | centre + radius |
| Nantucket Life sponsor banner | `disc_sponsor_links()` | centre + radius |
| The two 2026 sponsor flyers | `box_sponsor_links()` | rectangle |

A disc hotspot is a **square** box in artwork pixels, because that is what makes
`border-radius:50%` trace a circle instead of an ellipse. `verify.py` asserts
the squareness for every one of them.

**Measure the boxes off the artwork; never by eye.** For the Nantucket Life
banner (added 2026-10-31) the field is a blue gradient at saturation 135-170
and both seals are drawn in neutral ink at saturation 0, so thresholding on
saturation separates them in one pass. Watch for a logo arriving as **more
than one component**: the NHA seal comes back as the white ring outside its
black band plus the white centre inside it, and the two have to be unioned
before the bounding box means anything. The Chamber's is a single disc.

**Then check the numbers against the picture, not against themselves.**
`verify.py` walks 36 points round each shipped circle and requires ink at
`0.95r` and field at `1.08r`. That is the check that fails when the banner is
redrawn — a hotspot that has slid off its logo is still perfectly valid markup
and still passes every structural test.

The Nantucket Life banner takes **no `data-reveal`** on its `.sponsor-map`
wrapper, unlike the two festival ones: it has always been painted with the
page, and adding one would fade it in.

Both of its addresses were loaded on 2026-10-31 before going in — `nha.org`
answers "Home - Nantucket Historical Association", `www.nantucketchamber.org`
"Home - Nantucket Island Chamber of Commerce". Probe, do not assume: a 200 can
still be a parked lander.

## The FilmFreeway Gold button

Three of them: two on the New Moon Fest page (Frank, 2026-10-30) and the
home page's 11/1/26 carousel card (2026-10-31). Each replaced a "click here"
link, and each reads "...click this button:" followed by the card. **No full
stop after it** -- a period against the button reads as a stray mark.

- **One artwork, `assets/filmfreeway-gold.webp`**, shipped at 420x60 for a
  210x30 box. Frank has supplied the same 1669x248 PNG twice; check
  `../image-originals/` before encoding a new one, because a second copy of
  the same lockup drifts the moment one of them is re-exported.
- **`a.ff-btn` must stay after `.news-list a` and `.nmf-rules__submit a` in
  `styles.css`, and must keep its `a`.** Those two rules dress a link for
  words -- an underline in one, a green border-bottom and 1px of bottom
  padding in the other -- and are (0,1,1). A bare `.ff-btn` is (0,1,0) and
  loses to them, which draws a green line under the card and shoves it off
  centre. Equal specificity plus later position is the whole mechanism.
- **All three go to `filmfreeway.com/NEWMoonFest`.** The two on the New Moon
  Fest page pointed at `filmfreeway.com/dashboard` -- a visitor's own
  FilmFreeway account -- from 2026-10-30, which was what Frank asked for at
  the time; he moved them to the festival page on 2026-10-31 once the home
  card went in. The constant that held the `/dashboard` value is gone, not
  kept as a second name. `verify.py` now holds all three to ONE address and
  asserts no `/dashboard` link survives anywhere.
- **`NEWS` is built thousands of lines above `NMF_SUBMIT_URL`**, so the home
  card carries `NMF_SUBMIT_URL_LITERAL` declared beside `NEWS` instead. Same
  constraint as `PAGE_ONLY_PARTNERS`. Change one and change the other.
- **The card's picture is a link too**, and `news_section()` takes its href by
  reading the first `href="..."` out of the copy. Putting a button in the copy
  silently moves the picture's link with it, which here is what you want --
  but a button pointing somewhere else would drag the picture along.

## Page types

- **Standard pages** (home, staff, contact, classes, create, professional
  services) — built inline.
- **Channel pages** — Civic TV, Nantucket Life, Sports Connection.
- **Event pages** — Shorts Fest, New Moon Fest. Hand-built custom layouts;
  read the functions before editing.
- **Partner pages** — 20 in all: 15 with a tile in the grid (`PARTNERS`)
  and 5 reached only from elsewhere (`PAGE_ONLY_PARTNERS`, which is where the
  Community Foundation's four Initiative Funds sit).
  - **Every one of them is custom now.** All twenty are listed in
    `CUSTOM_PARTNER_PAGES` and built by `custom_partner_page()` further down
    the file, so the generic partner loop below that set has nothing left to
    build. It is kept for the next partner added tile-first. `video_page()`
    itself is still live — Civic TV and Sports Connection use it.
  - Entries in `PAGE_ONLY_PARTNERS` must be **string literals**: that list sits
    thousands of lines above where `CFN_PAGE` and the rest are defined.
  - **The logo grid is drawn alphabetically**, by the same `label_key()` the
    section headings use, so the order the list is written in does not matter
    (Frank, 2026-10-25). `partner_buttons()` does the sorting, and the home
    page draws the same grid, so both pages agree. The Community Foundation's
    four Initiative Fund logos, in the section below the grid, are sorted the
    same way by `cfn_funds_section()`.
  - **Both pages show all twenty.** The home page drew only the 15-tile grid
    until 2026-10-31, so the Foundation and its four funds appeared on the
    Nonprofit Videos page alone; it now draws `cfn_funds_section()` too. Two
    things that shape how:
    - It goes **inside** the `section--paper` block, after that section's
      `.wrap` closes -- the same shape the hub page uses. `.cfn-funds` brings
      its own `.wrap` and sets no background, so dropped between the two paper
      sections it reads as a fog-coloured stripe.
    - `cfn_funds_section(lazy=)` mirrors `partner_buttons(lazy=)`: lazy on the
      home page, where it is five screens down, eager on the hub, where it is
      the content.
    `verify.py` checks the PAGES, not the tiles -- it lists `partner-*.html`
    off disk and asserts every one is reachable from a logo on both pages. A
    fund added to `CFN_FUNDS` with no page, or a page with no logo, fails
    there; a tile count would not notice either.
- **School Videos** (`videos-school.html`) — one page covering several
  organizations. See "School Videos page specifics" below.
- **Live TV** (`videos-live.html`) — the embedded broadcast player. See
  "Live TV" below.

### Meeting titles

Every recorded-meeting title leads with its date in the School Committee's form:
abbreviated month with a period (May takes none), the day with its ordinal
suffix, then the year and the body, and no dash between them —
`Sep. 15th, 2026 School Committee`. The 2,732 Civic TV titles were converted to
this from `September 15, 2026 - School Committee` at the site owner's request.

Nothing in build.py parses these dates: a civic card's quarter comes from the
third element of its tuple in `CIVIC_BOARDS`, and the agendas and descriptions
are keyed by video id, so the format is display only as far as the build goes.
`verify.py` does read them, to check that each list runs newest-first, so a
date typed into a title wrongly is now a build failure rather than only a
wrong-looking card — it also supplies each thumbnail's
`alt` text. Dates written inside an agenda or a description are the meeting
posting's own wording and are left long.

**Two boards have no quarter row.** Public Forums never had one. Annual/Special
Town Meeting lost its on 2026-10-27 at Frank's request: the meeting sits once a
year over two or three evenings, so every year drew four quarter buttons with
three greyed out. `CIVIC_NO_QUARTERS` in `build.py` names those boards and
`civic_board_picker()` puts the cards straight under the year, keeping their
agenda and warrant buttons. The month is still stored in every tuple — keep
filling it in, since a board can be taken back out of that set.

**Meetings are stored oldest-first and drawn newest-first.** `civic_year_cards()`
and `civic_forum_cards()` reverse the list as they render, so a quarter or a
forum year reads newest at the top; every list on the School Videos page does
the same through `programs_section(..., newest_first=True)`. The reversal is deliberately
at render time and not in the data, which keeps the storage order stable while
the page order is derived from it. The hairline still falls between cards,
since `rule=(i != last)` is applied after the reversal.

**Place a new meeting by its date, which usually means appending.** A meeting
is normally the newest in its year, so the end of the list is where it goes --
and because the list is drawn in reverse, that puts it at the top of its
quarter. But appending is a *position*, not a date: append a meeting posted
late, or a backfilled re-upload, and it lands above meetings that happened
after it. Appending a January meeting in December tops the Jan-Mar panel above
March. So insert at the position the date gives it, and append when that
position is the end. `verify.py` fails the build on either mistake, which is
the backstop, not the rule.

`verify.py` checks the order from the BUILT page and never from
`CIVIC_BOARDS`: measuring the literal reports every list as backwards when the
page is perfectly right, which is a mistake that has already been made once.

**A card whose title has no readable date is dated by `CIVIC_CARD_DATES`**,
which sits under `CIVIC_FORUMS` and renders nothing. Six cards need it: four
Public Forums, one video that was never streamed, and the Article 12 info
session. The rule, Frank's from 2026-11-05, is the **streaming date**, or the
posting date when the video was never a stream, and `verify.py` fails on an
undated card missing from the table. All six were already in the right place,
so adding it moved nothing.

A title that does carry a date still wins over the table. `ymII7Vgyx04` is
cross-listed as an undated Public Forum and as "Feb. 2nd, 2019 Nantucket: 2030
& Beyond" under Select Board 2019; one entry places the first and the title
places the second.

Two rows are worth not "simplifying". `rr8dnFrxNCY` prints its date as
`7 18 18`, which the date reader cannot parse, and its upload is a week after
the meeting -- taking the upload date files it above the Jul. 23rd forum.
`Wcgd7v_Kvsk` was an evening stream, so its UTC upload lands the next day and
would date it May 1st instead of Apr. 30th. Both are enforced by the check,
not just written here.

**A board opens on its newest year and newest quarter.** Frank asked for this
on 2026-11-05: clicking a board name used to open the board and stop there,
leaving both rows unselected until he picked a year himself. `restoreYear()`
and `restoreQuarter()` in site.js now fall back to `newestPick()` whenever the
remembered choice cannot be honoured — on the first board of a session, when
nothing is remembered, and on a board whose archive does not reach the
remembered year or whose newest year lacks the remembered quarter.

The remembering still comes first and is unchanged: pick 2019 Jul-Sep on one
board and the next board that has it still opens there. The fallback never
writes to `civicPick` and never goes through `.click()`, so a quarter nobody
chose cannot overwrite the one they did — the boards in between open on their
own newest and the reader's choice comes back afterwards. Annual/Special Town
Meeting and Public Forums have no quarter row at all, so they stop after the
year.

The year and quarter buttons are not reversed — they stay oldest-left, by
request. Nantucket Government 101 is not a meeting list and keeps its own
order.

### Adding another custom partner page

`custom_partner_page()` takes a logo, mission text, website phrase, and a list
of `(section label, videos)` groups. ~10 lines. Add the page to
`_PARTNER_ORGS` as well, or the description check at the foot of `build.py`
stops the build. `videos` is one of four shapes:

- a flat list of `(video_id, title, description)` — Dreamland, Linda Loring
- a dict of `{year: [(video_id, title, description), ...]}` — Atheneum,
  Book Festival
- a `Subgroups([...])` list of `(label, videos)` pairs — no page uses it now
- a `Picker([...])` list of `(label, videos)` pairs — NHA

The dict form renders a row of year buttons (oldest left, newest right) with one
year's videos visible at a time, driven by `initYearPicker()` in `site.js`. A
year may be listed with an empty list to reserve its button before the videos
exist; the picker opens on the newest year that actually has any.

`Subgroups` nests one more level of accordions inside a section instead of
listing video cards. It nests arbitrarily deep, and `program_group()` styles
every level past the first with `dl-group--sub` (indented, one size down). The
NHA's two Browse lists were its only users until they became `Picker`s, so it
is live but unused — keep it for the next section that wants nested rows.

`Picker` holds the same `(label, videos)` pairs but draws the children as a
wrapping row of buttons over a single panel rather than a column of accordion
rows — see "NHA page specifics" below. Reach for it when a section has enough
children that a stack reads as a list to scroll past rather than a set of
choices to pick from. Nothing is open on load, and a second click on the open
button shuts it. A child may itself be any of the four shapes, so a `Picker`
panel can hold a year picker of its own; `initYearPicker()` scopes its buttons
and panels to one picker's own level so the two do not fight, and the
`.yearpick--labels` rules use child combinators for the same reason.

A group may carry a third element, `(label, videos, intro)`: a note set once at
the top of that section. It exists for text that would otherwise repeat on
every card inside it -- the Arts Council closes all four Emergence episodes
with the same paragraph about the series, so the paragraph is the section's
note and the cards carry only what differs. Prefer this to deleting a partner's
own wording.

**Section order is alphabetical and enforced in code.** `custom_partner_page()`
sorts the groups it is given by `label_key()`, so the order they are written in
does not matter and a section added later cannot land out of order (Frank,
2026-10-25 -- "Halloween Parade" had arrived after "Talk of the Town" on the
Chamber page). `label_key()` strips markup and entities, ignores leading
punctuation so `&rsquo;Sconset` files under S, ignores a leading "The" so
"The Cranberry Bogs" files under C, and case-folds. Only "The" is dropped --
no section starts with "A" or "An", and guessing at articles that are not
there would file a future section where nobody looks for it. Digits sort
before letters, so "50th Anniversary Video" leads the Land & Water Council
page. Only the top-level sections are sorted -- the children inside a
`Picker` or `Subgroups` keep their list order, some of them being
chronological.

A final `collapsible=False` argument renders the groups permanently open, with
a plain heading in place of the click-to-toggle summary. The Book Festival
archive uses it; nothing else does.

An empty group list is fine: `programs_section()` renders nothing at all rather
than a bare "Programs" heading over empty space, so a page can go up with its
banner and mission before any videos exist. The Civic League page is the
current example.

## Film panels — the two festival pages

A film is a `(button_title, slug, detail)` tuple. `SHORTS_2026` holds the
Shorts Fest 2026 Official Selection; `NMF_2024` / `NMF_2025` / `NMF_2026` hold
the New Moon Fest selections. `movie_panel_html()` builds one panel from the
`detail` dict and is shared by both, which is why it is defined above the
Shorts Fest page rather than beside the New Moon lists where it started.

`detail` is `None` until the film's content arrives. It needs **all three** of
`poster`, `meta` and `synopsis` or it raises, so a film without them gets a
short "coming soon" panel instead — never a button that does nothing when it
is clicked. `quotes`, `credits`, `directed` and `title` are optional;
`title` overrides the button's label when the two differ.

The two pages differ in one way only: New Moon wraps its lists in a year
picker, Shorts Fest does not, because its other years live in the Awards,
Festival Photos and Watch Past Films sections. Both rely on
`initMoviePicker()`, which scopes on `.pastsel__movies` and the panels beside
it — **those two `<div>`s have to stay siblings.**

### Links in a synopsis

Allowed, and Zubbies is the precedent (2026-10-29): Frank supplied the film's
own site and asked for it. Same markup as every other outbound link on the
site, `target="_blank" rel="noopener"`, written straight into the synopsis
string. **Probe the domain before linking it** — a 200 is not enough, check
the page is what it claims to be, the way [[auction-partner-links]] does.

### Where the credits go

**Always below the poster, on both pages.** The block is a third child of
`.movie-panel` — `.movie-credits-wrap`, a row of its own under the poster and
the synopsis — for every film with credits, however few. Frank settled this
on 2026-10-28, Shorts Fest first and then New Moon. A long list beside the
poster had pushed the poster far up the page; putting *every* list there is
what makes the panels read the same whether a film has five credits or
fifteen.

There is no "beside the poster" branch any more. If one is ever wanted again,
it is a second parent for `inner` in `movie_panel_html()`, not a CSS change.

**How many columns** is the separate question, and `CREDITS_COLUMNS_FROM = 8`
answers it: eight or more **lines**, or a `None` in the list, and the wrapper
takes the `--cols` modifier. Lines, not entries — `credit_lines()` estimates
them at `CREDITS_LINE_CHARS = 40` to the line, which is the measured capacity
of the 341px single column at 18.4px. Stick Shadow Path is why: seven credits
but eleven lines, because `Special Thanks: Anne Kuszpa, Nantucket Party
Rentals, 97.7 ACK FM & Chip Webster Architecture` is one entry and three
lines. Counting entries left it in a single column 354px tall, taller than
Put on a Sweater's sixteen credits set in three. Without it the list sets in one column at the
width the first column would have had, starting at the poster's left edge.
Two columns of two names with a third of the panel of air between them reads
as a mistake; and left to run the whole panel, a short list would be one
1072px line with 800px of air after it, out of line with the columned panels
above and below.

**The column count steps with the room, in two stages:** two columns from a
640px block, three from 960px, and the three-column gap drops to a flat 24px
where the two-column one is `clamp(24px,3vw,46px)`. That 18px is not cosmetic
— at the wider gap three columns across the 1072px panel leave 329px each,
and `Director of Photography: Greg Shephard` wraps at 329px but not at 341.
If the credits font size changes, re-measure both thresholds.

Only `.movie-credits-wrap` carries `container-type`, so the `@container`
rules that turn the columns on cannot match a short list — there is nothing
to re-check in the CSS when the threshold moves.

A credit that is itself a whole cast list (`Starring:` + twelve names, 203
characters on Essex Girls) sets as one six-line block that `break-inside`
keeps together, so the balancer leaves that column short. That is the right
trade: splitting a cast list down a column gap is worse than a ragged edge.

Two things to leave alone. Each credit is its own `<span>` with
`break-inside:avoid`, which is what stops a credit that wraps from being split
down the middle of the column gap. And the columns **must** stay behind a
query of some kind: a `None` in the list emits a *forced*
`break-before:column`, and a forced break makes a second column even where
only one fits, which put the cast off the side of a phone screen.

A `None` is not a credit. It means "start the second column here", which is
how the crew and the cast land in a column each instead of wherever the
browser's balancing happened to fall.

### The poster

```
python3 tools/film-poster.py SOURCE SLUG [--pad]
        [--16x9 [--left|--right] [--top|--bottom]]
```

writes `assets/SLUG-poster.webp` and keeps the supplied file in
`image-originals/`. 920px wide, because every image here is encoded at twice
its rendered width and the Shorts Fest poster renders at most 460px.

**The two pages render the poster at different sizes.** New Moon's are
portrait one-sheets and keep the shared `clamp(220px,26vw,300px)`; Shorts Fest
sends 16:9 frame grabs, which read as a thumbnail at that width, so
`.shorts-selection .movie-poster` overrides it to `clamp(280px,40vw,460px)`.
The New Moon files are only 527-600px wide, so widening the shared rule would
upscale them -- that is why the override is scoped rather than global.

Frank sends these as frame grabs, letterboxed inside a 4:3 or square frame.
**The bars are not pure black** — 27/255 on the first one — so detection has
to compare each line against the outermost line, not against black, and it
still lands a few pixels inside the picture, which stretched a face by 0.7%.
The tool squares a nearly-16:9 crop up to exactly 16:9 for that reason.

**`--pad` is the opposite, and a title card usually needs it.** A card that
arrives trimmed to its own text — Stick Shadow Path came as 1406x388, words
on black — would be *cropped tighter still* by the default path, to the
bounding box of the lettering. `--pad` instead fills the short axis out to
16:9 in the border colour, putting the card back the size it was in the film.
It asserts the corner really is black first, because the fill is black.

**`--16x9` forces the centred exact-16:9 crop** that `snap()` otherwise
applies only within 3%. Use it when Frank says a poster is 16:9 and the file
is not: Stick Shadow Path's arrived 640x416 (1.538:1) and lost 28px off the
top and bottom.

**`--left` / `--right` take that crop from one edge instead of the middle**,
for a frame whose title sits off to one side. The One Star Weekend is
2000x900 with its title running to x=1892; centred, the crop ends at x=1800
and cuts the word in half, so it is built `--16x9 --right`. **Measure where
the title ends before choosing** — threshold the bright pixels and read the
bounding box, the same discipline as [[sponsor-flyer-image-map]].

**Threshold on the lettering's colour, not on brightness**, when anything
else in the frame is bright. No Matter What is cream type over open ocean,
and a plain `>230` threshold returned x=54..1998 — it was measuring the
whitecaps. Keying on the cream instead (`g - b > 25`) gave the real extent,
x=138..1878, and the difference is between thinking the title touches the
edge and knowing it clears by 109px.

**`--top` / `--bottom` do the same on the vertical axis**, for a 4:3
photograph whose subject is not in the middle of the frame. The Keeper
arrived 1446x1088 and loses 275 rows: the lighthouse lamp's burst runs
y=150..230, so a centred crop starts at y=137 and shaves the halo, while the
bottom 188 rows are unlit foreground at a mean brightness of 0.4. It is built
`--16x9 --top`, which keeps the whole sky and throws away only the black.
Measure the same way — mean brightness per band of rows, and the extent of
the near-peak pixels — rather than guessing which end is expendable. The two
axes are independent, so one of each may be given.

**The output is never wider than the source**, and the tool prints a warning
with the density it achieved when it has to fall short. Act on it — ask for a
larger original. Asking worked on 2026-10-28: Stick Shadow Path's first file
was 640x416 and would have shipped at 1.39x, and Frank had a 2000x1124 frame.
Say plainly that the poster will look soft and what size would fix it.

**Which attachment is the poster is not always obvious.** Frank sent six
images for Stick Shadow Path: a title card, four credit cards and a photo.
The *title card* was one of the credit screenshots and the photo was the
poster — the opposite of the guess made here. When more than one attachment
could be the poster, ask rather than infer; a title card that names the film
is not automatically the poster.

A
genuinely portrait poster is nowhere near the ratio and is left alone.

Posters are landscape here and portrait on the New Moon page. That is fine;
`.movie-panel` is a flex row and takes either.

### The meta line

**The two pages use different formats**, and that is deliberate.

- **New Moon Fest:** `GENRE / DURATION / LANGUAGE / ORIGIN`, all caps, e.g.
  `STOP MOTION ANIMATION / 45 SECONDS / ENGLISH / NANTUCKET`. The films come
  from around the world, so language and country tell a reader something.
- **Shorts Fest:** `GENRE / DURATION` only. Frank cut `/ ENGLISH / NANTUCKET`
  from Put on a Sweater on 2026-10-28. Every film in the selection is
  Nantucket and in English — the submission rules require the film to be
  created on or inspired by the island — so the two fields said the same
  thing on every panel. Follow this for the remaining films; do not re-add
  them.

Frank supplies genre and runtime.

### The sponsor banners and flyers

Both festival pages carry one, straight under the page's intro and the full
width of the column: `assets/2026-top-sponsors.webp` on New Moon,
`assets/shorts-top-sponsors.webp` on Shorts Fest, added 2026-10-30 at Frank's
request and modelled on the New Moon one. They render identically -- 1072 x
241 at a 1440px window -- because both sit in a `.sponsor-map` inside a
`.wrap` and their sections take `padding-top:12px` under an intro whose bottom
padding is 14px. **That 12/14 pair is the placement**; change one page's and
the two stop matching.

**A banner is one image with invisible links laid over it.** The logos are
discs, so a hotspot is a CENTRE and a RADIUS in the artwork's own pixels, not
a rectangle -- that keeps the box square, which is what makes
`border-radius:50%` trace a circle instead of an ellipse -- and
`disc_sponsor_links(art, links)` turns both into percentages, so the overlay
rescales with the image. The sports page keeps its own `sponsor_map()`, which
takes rectangles, because one of its logos is a rounded box rather than a disc.

**Measure the discs off the artwork; do not eyeball them.** Threshold the
white away from the coloured field, label the connected components and keep
the big round ones -- the caption is white too, so it labels as a crowd of
small components you drop by size. Then check twice: draw the circles back
onto the artwork and look at it, and probe points around each edge, inside and
out, confirming white within and field without. The two Shorts Fest discs came
out 382px across on a 2000x450 banner, 72 of 72 probes correct.

**A recolour is not a redraw.** The Shorts Fest banner was recoloured twice
on 2026-10-30, blue to pale teal to a deeper teal. Every time, both discs
re-measured to the same centres and radii within half a pixel and all 144 edge
probes passed on the stored figures, so the hotspots stood unchanged -- and
the re-measurement is what proved it. Re-measure anyway; that is how you find
out which kind of change it was.

**Measure the caption's contrast off the rendered pixels when a field
changes.** The banner's white caption read 3.82:1 on the original blue,
**1.71:1** on the pale teal and **2.29:1** on the deeper one -- 2.14:1 at the
lighter end of its gradient -- against the 3:1 WCAG asks for large text, and
4.5:1 at phone width, where the caption drops below the large-text size. The
artwork is Frank's, so every reading is reported rather than acted on -- give
him the number and the size of the fix, and let him choose. On 2026-10-30 he
took 15% off the gradient teal, then replaced the whole thing with a **flat**
teal, `#0297B2`, which reads **3.46:1** everywhere. A flat field is the easy
case: there is no light corner to fall short in.

`assets/shorts-top-sponsors.webp` is a **straight encode** of the file in
`image-originals/` again. It was not, for one revision --
`tools/banner-darken.py` had been applied to it -- and that tool is still
there for the next field that needs it:

```
python3 tools/banner-darken.py SRC DST --by 15 --keep CX,CY,R --keep CX,CY,R
```

Two things it does that matter if it is ever used again. **Each `--keep` disc
is left exactly alone**, because a sponsor's own red or navy is not ours to
shift; only the field outside them moves. And outside those discs the amount
is **weighted by how white the pixel is**, so a white caption keeps its white,
the field behind it darkens, and the two meet through the type's own
antialiasing instead of leaving a halo -- check that by reading mean
brightness in rings at r+2, +5, +12 and +30 outside each disc. Its FIELD_MAX
and TEXT_MIN are measured off one artwork; re-read them for another.

**A sponsor whose site cannot be confirmed gets no hotspot.** Probe the
domain, do not search for it, and read the page -- a 200 can be a parked
lander. The Arts Council's URL was already on its own partner page; the Boys
&amp; Girls Club's was probed on 2026-10-30.

These are top-tier banners, so they load **eagerly**. Only the second sports
banner, at the foot of its page, passes `lazy=True`.

**Each festival page also closes with a 2026 Sponsors flyer**, under an
eyebrow and a one-line `<h2>`: `assets/2026-nmf-sponsor-flyer.webp` on New
Moon, `assets/2026-shorts-sponsor-flyer.webp` on Shorts Fest, added
2026-10-30. A flyer's logos are rectangles rather than discs, so they go
through `box_sponsor_links(art, links)` and take `.sponsor-map__box`.

**Measure a flyer's boxes, do not eyeball them** -- the Shorts one holds ten
logos and the New Moon one thirty-five. Threshold the flat background away
(read its colour from pixel 8,8), downscale, dilate so the pieces of one logo
join, label the components, undo the dilation and pad each box by about 8px.
Then check three ways: no two padded boxes overlap, no box's own 1px frame
touches ink (a box that crops its mark fails this), and the boxes drawn back
onto the flyer look right. **A cluster is not always one sponsor** -- the red
N and Nantucket Current sit either side of a hairline on the Shorts flyer and
are two links, with the hairline in neither.

**The hover treatment follows the artwork, not the class.** `.sponsor-map__box`
washes white and rings white, which is right on the New Moon flyer's navy and
invisible on the Shorts flyer's cream, so `.shorts-flyer` inverts both to
navy. Check a new flyer's background before reusing either.

**The margin goes on the wrapper, not the image** -- the hotspots are
positioned against the wrapper, so a margin on the image slides the picture
out from under them. `margin-inline:auto` on `.sponsor-flyer` is what centres
one.

On a phone a flyer is about 335px wide, which puts the smallest hotspot near
20px. Both pages are like that; it is the trade a single-image sponsor wall
makes, not a Shorts Fest bug.

The Shorts Fest flyer's head carries a `<p>` under its `<h2>` -- Frank's
wording of 2026-10-30, which is a thanks line plus an invitation to sponsor,
ending in an address. It is the only link in any `.section__head` on the site,
and `a{color:inherit}` meant a bare mailto there looked like plain text, so
`.section__head p a` now takes the same green underline the address further up
that page has. Watch for that if a link lands in another section head.

**The Shorts Fest page runs tight from the banner into the notice** -- the
banner section takes no bottom padding and `.shorts-notice` 24px of top, by
Frank's request on 2026-10-30. It had been 58+37. The Encore Screenings
graphic is capped at 960px and centred in the 1072px column, asked for in the
same breath; `.encore-img-link` carries the auto margin, the image inside it
is `width:100%`.

## Notable Nantucket Women — New Moon Fest

Twenty-five women, one at a time. `NOTABLE_WOMEN` in `build.py` holds them;
`nmf_women_section()` draws the section. It is the **second-to-last** section
of the page, **above** "Our Team" — it was built below it on 2026-11-08 and
Frank swapped the two the same day, so the page ends on the festival's own
people. The two are siblings in `newmoon_body` and neither depends on the
order; swapping them back is swapping those two lines. "Our Team" is itself
the heading Frank renamed from "Meet the Team" that day.

The section is **the auction section's shape** — eyebrow, one collapsible, and
everything behind it — except that the summary is the subtitle Frank wrote,
"Meet these Legendary Nantucketers", instead of "Learn More". Expanding it
shows the introduction, then a picker of twenty-five name buttons.

**The introduction has its own size and its own last line.** It shares
`.auction-note`'s margin, serif face, measure and colour, but not its
font-size: Frank asked for it a size smaller on 2026-11-08, so `.wih-intro` has
its own rule in the type scale at `clamp(1.2rem,1.47vw,1.36rem)` — the
`.news-sign` rung, one step under the auction note, not a new number. The
closing sentence ("To learn more about these notable Nantucket women, please
click the buttons below.") is Frank's wording and is part of `NMF_WOMEN_INTRO`,
not markup, so it travels with the paragraph.

`NMF_WOMEN_INTRO` is a **list, one string to a paragraph** — two of them since
Frank asked on 2026-11-08 for the Stevens quotation to begin a new paragraph.
The renderer writes one `<p class="wih-intro">` each, and `.wih-intro`'s own
bottom margin is the gap between them, so there is no rule for this and another
break is another string in the list.

**No JavaScript was written for it.** The picker is `.yearpick
.yearpick--toggle .yearpick--labels` exactly as the NHA's "Browse by Topic" is:
`--labels` puts the names in the sans face and lets them wrap as a block,
`--toggle` is what shuts a woman's panel when her own button is clicked again,
and `data-year` holds a slug here the way it holds a topic name there.
`initYearPicker()` already carried both branches. The buttons also take this
page's gold active state for free, that rule being written against `.year-btn`.

**Nothing is open on load** — no `is-active`, every panel `hidden` — so the
reader opens the section and sees the choices. The awards and auction pickers
on the same page both open on a chosen year, so this is one copy-and-paste
away from being undone; `verify.py` checks it.

**The eyebrow is an `<h2>`**, like Our Team's and for the same reason: each
woman's name is an `<h3>`. That means it matches `.section__head h2`, the
*subtitle* rule, and picks up its `margin-top:12px` — so `.nmf-women` is on
that `margin-top:0` selector list beside `.nmf-team`, and on the tight
`margin-bottom` list with the other collapsible-subtitle sections.

**The portraits are drawn at `WIH_SCALE` times their own pixel size** — 1.25
since Frank asked for a quarter more on 2026-11-08. They were cropped out of
the PDF he supplied — a print of the festival's own "About: Women in History"
page — and are about 155x196, which is **all that file carries**: the PDF holds
1112px-wide bitmaps of the printed page, so re-rendering it at any DPI enlarges
the same pixels. That quarter is therefore an **upscale**, and it softens them.
He was told before it was done.

The scaling is on the `<img>` and nowhere else. The WebP files keep their own
pixels, so the assets stay as sharp as they ever were and going back to 1:1 is
one constant. `.wih-portrait` still sets **no `width` at all** — these are
nineteen different sizes and one width would flatten them to the same picture —
and `verify.py` still fails on a `width` in that rule. It also now checks each
`<img>` asks for exactly `WIH_SCALE` × the file, which catches both a tag that
drifts off the constant and a file re-encoded larger to meet it. If larger
originals ever arrive — the credits give the NHA's accession number for sixteen
of them — replace the files, set `WIH_SCALE` back to 1, and nothing else moves.

Six women have no portrait on the source page, seven carry no image credit, and
the Monaghan sisters are one entry with two portraits. All three are rendered
away rather than left as empty furniture, which is why `images` is a list.

**The copy is the source page's, word for word, and nothing was retyped.** The
bios come out of the PDF's text layer joined line by line; the literal was
proved by running it back through the interpreter and comparing every field,
the check the re-wrapping notes exist for. Only typography changed: the source
mixes straight and curly quotes, and those are the site's entities here, the
same conversion a YouTube description's straight apostrophe gets.

**Its own errors were flagged, then corrected when Frank asked** — ten were
raised on 2026-11-08 and he said to fix them, so nine are fixed: "attach
Autopscot's village" → attack, a quotation that closed on a right single
quote, an unclosed quotation in Abiah's entry, Elliza → Eliza, Talcahhuano →
Talcahuano, Azubah Cast → Cash, "attached racial discrimination" → attacked,
"Jewitt was made and honorary" → "Jewett was made an honorary", and "on
hundred ten years old" → "one hundred ten". The comment above `NOTABLE_WOMEN`
lists each one.

**Eunice Ross keeps "seventeen-year-old"** — that flag was **withdrawn**. The
NHA's own description of `yDFnxSufBQU`, on this site, reads seventeen-year-old
as well, and the sources behind it agree; the doubtful figure is the 1824
birth year in the heading, and Frank said on 2026-11-08 to leave that alone
too.

**Reverend Baker has no date on *By the Sea*.** "In 1838, she published" was
impossible (born 1846, minister from 1880), and no catalogue gives a year, so
Frank's answer was to take the date out rather than guess. The sentence now
begins "She published a volume of her collected poems". A year, if one ever
surfaces, goes back there.

**The introduction says Stevens.** Frank pasted that paragraph himself, so
"Travel writer William Oliver **Stephens**" was flagged rather than changed;
he asked for it on 2026-11-08. William Oliver Stevens wrote *Nantucket: The
Far-Away Island*, and partner-nha.html spells him Stevens in the same
quotation.

**Kezia Folger Coffin is dated 1723–1798, and that disagrees with
`partner-nha.html`** — which says 1772–1798, in the description of the 2018
Whaling Museum talk (`7KqRYdWzfk0`), the only dated mention of her on that
page. On 2026-11-08 Frank first made partner-nha.html the authority and the
heading read 1772–1798 briefly; shown what that date implies, he reversed it
the same day. **The conflict is known, settled and deliberate** — do not
"correct" this heading to match the other page, and do not re-raise it as a
discrepancy. What settled it: 1772 would put her at four years old at the
Declaration, seven during the 1779 smuggling her own entry describes, and
twenty-six at her death, against 9 December 1723 in the Quaker birth records,
the Maria Mitchell Association and the genealogies. The NHA's figure sits in a
YouTube description, which this site reproduces verbatim, so it is not ours to
edit here — correcting it would mean correcting it on YouTube, and that is
Frank's to do.

The order is the source page's too: roughly by birth year with four entries
out of sequence, which is a curated order rather than a sorting mistake.

**Six panels link to the film the site already has about that woman.**
`WOMEN_FILMS` in `build.py` keys them by slug — Wonoma, Susan Veeder, Eunice
Ross and the Monaghan sisters from the NHA's "Extraordinary Nantucket Woman"
series, plus Phebe Coffin Hanaford and Clara Parker. Every one is on
`partner-nha.html` and nowhere else. The link goes where that page's own cards
go — `youtu.be`, `target="_blank" rel="noopener"` — because no card there
carries an `id`, so there is nothing nearer to point at. One film to a woman,
the one that is about her; the rest of the candidates (a second Ross and a
second Veeder film, four more Monaghan films about Greater Light, the
Boston-Higginbotham House dig, and the 2018 Whaling Museum talk that covers
fifteen of these women at once) were raised with Frank, not added.
`verify.py` checks each link is a `youtu.be` id in a new tab and is still
listed on `partner-nha.html`.

## Live TV

`videos-live.html` embeds NCTV's own broadcast stream. Until 2026-10-29 the
Watch menu sent people out to TelVue, the vendor that carries the stream --
its header, its search box, its Home / Videos / Series / Playlists row, NCTV's
channel some way down somebody else's page. Frank asked for the player on our
own page instead.

The player is TelVue's and it is still TelVue serving the video; nothing is
hosted here. Three things about it are worth knowing:

- **`showtabssearch=false` is the whole trick.** It drops the vendor's own
  chrome and leaves the player by itself. `autostart=true` is what the old
  link carried, so the page behaves as the destination did; the browser's
  autoplay policy still has the last word, and the iframe's `allow` list says
  `autoplay` so the policy is the only thing deciding.
- **There are two channels, and the old link only reached one.** Playlist
  1706 holds a stream per channel -- 257 is Civic 8, 1048 is HD 1072 -- and
  the outside link opened Civic 8 with HD 1072 behind a tab on the vendor's
  site. Both are buttons on the page now.
- **One iframe, re-pointed.** `initLiveChannels()` in `site.js` swaps its
  `src`. A frame each would open both streams and keep pulling the one nobody
  is watching. The frame is written out with the first channel's address
  already in it, so the page plays with no JavaScript at all.

TelVue sends no `X-Frame-Options` and no `frame-ancestors`, checked
2026-10-29, which is why it frames at all. If that ever changes the page goes
blank rather than degrading -- the note under the player links the stream on
TelVue directly, which is the way out.

## Festival photo galleries

`SHORTS_PHOTOS` maps a year to a list of `("stem", "alt text")`, and
`photo_gallery_section()` builds the year picker and the masonry grid from it.
A year whose list is empty renders as a **disabled, dashed button** with a
title explaining the photos are not online yet — so adding a year is adding
its list, nothing else. As of 2026-10-30 every Shorts Fest year is live:
2023 has 74 photos, 2024 has 64, 2025 has 45 and 2026 has 77. 2025 was the
last dashed button, opened from 71 files sent in four batches and then cut
back by Frank from a numbered contact sheet of the whole year.

**Children.** Two 2025 frames were published and then withdrawn because they
show a young child; Frank's rule is that no picture of her goes on the site,
and his standing instruction is to **ask before withdrawing any photo of a
child** rather than deciding it yourself. Withdrawn files move to
`image-originals/withdrawn/`, never to the trash, and their stem numbers are
retired, not reused — so a year's stems can have deliberate holes in them.
An ordinary editorial cut works the same way but goes to
`image-originals/removed/`; keep the two folders apart, because one records a
rule and the other records a preference. When Frank is choosing which frames
to keep, send him a numbered contact sheet of the whole year rather than a
list of descriptions — he picks by eye, and the numbers are what he answers
with.
Check every new batch frame by frame, at full size, before encoding it.

### Encoding

```
python3 tools/gallery-photo.py SOURCE STEM
```

writes `assets/STEM.webp` and `assets/STEM-lg.webp` and keeps the supplied
file as `image-originals/STEM-original.<ext>`.

**Thumbnail 700px wide, large copy 1800px on its long edge, quality 84.**
These are not a fresh choice — they are what the 2026 set already is, and
the quality was recovered by re-encoding `nsf2026-01-original.jpg` across the
range until the byte count matched the file in `assets/`. A year encoded at a
different quality is visible against the others at full screen.

The thumbnail is a flat **width**, not a long edge, because the masonry lays
out in columns: width is the dimension that has to agree between photos and
height is free. The large copy is the long edge instead, so a portrait and a
landscape open at the same area rather than the same width.

**The thumbnails have to exist before `build.py` runs.**
`photo_gallery_section()` opens each one and writes its real pixel size into
the `<img>`; a lazy image with no `width`/`height` is 0px tall, so the whole
grid collapses into the viewport and every photo loads at once.

### The credit line

`SHORTS_PHOTO_CREDITS[year]` is a `(who, url)` pair and `photo_credit()`
renders it as *"Photos by X. For prints, click here."*, with only **click
here** linked. It appears above the grid and again in the lightbox caption.
Every festival year so far is Charity Grace Photography. Her site answers
curl with a Cloudflare 403 "Just a moment…" page — open it in the browser
pane before concluding a link is dead.

**Opening a new year is two edits, and the second one fails silently.** Filling
`SHORTS_PHOTOS[year]` turns the dashed button live on its own, so the gallery
looks finished while `photo_credit()` returns `""` for a year missing from
`SHORTS_PHOTO_CREDITS` -- no error, no warning, just no credit line above the
grid or in the lightbox. Frank has asked for the photographer's tag on every
batch, so **add the credit entry in the same pass and then confirm the line
renders**, rather than trusting the build.

**Scope any patch to these dicts.** The New Moon gallery keeps its own
`(who, url)` dict whose Charity Grace lines are byte-identical to the Shorts
Fest ones, so a global search-and-replace on a credit line matches twice and a
`count == 1` assertion fails -- which is the assertion doing its job. Match the
enclosing `SHORTS_PHOTO_CREDITS = {...}` block first, then edit inside it.

### Near-identical frames

Frank asks for duplicates dropped, and the shoots are burst photography, so
there are always some. **Rank them with a measurement**: a 256-bit dHash
plus an aHash over every pair. The 2024 set's first batch had two corridor
frames 26 bits apart and nothing else closer than 148 — a gap that wide
makes the decision for you.

**But the gap is not always there, and then the hash is the wrong tool.**
The second 2024 batch ran 38, 41, 58, 63, 90, 98, 110, 127, 140 with nothing
separating “same frame” from “same subject”: seven of its seventeen were a
podium burst where the unchanging stage and screen dominate the hash and only
the speaker's expression changes. Two frames of the same audience watching
two *different* films scored 38 for the same reason — the dark room is most
of the picture, so a low distance there means the camera did not move, not
that the photograph is the same. When the distances form a continuum, rank
with the hash and then **look at the frames and cut by eye**, and say in the
reply that the cut was a judgement rather than a measurement. Report every
drop with its distance either way, so Frank can reverse one in a word.

**Check the alt text against the full-size frame, not the thumbnail.** Six of
the sixteen 2024 descriptions were wrong when checked at 1100px — "a
volunteer handing ballots" was a conversation, the "ballot table" was the
check-in desk. Alt text is read aloud; a guess about what is happening in a
picture is worse than a plain description of it. Keep them generic and
**name nobody**, the way [[never-add-tags-unasked]] keeps names out
elsewhere — the 2024 badges are legible at full size, which is exactly why
this matters.

**A printed placard is a source; a lanyard is not.** Alt text names nobody by
default, but Frank agreed on 2026-10-29 that the panel photos are different:
the festival sets a printed card on each chair -- JOHN COPENHAVER, FILMMAKER
and so on -- and a sign the audience was meant to read is the festival's own
statement of who that is, not an inference. So **name the person when a
placard in the frame names them, and keep everyone else generic**, including
anyone identified only by a lanyard or a badge that had to be zoomed into.
That line is the whole rule; do not widen it to faces recognised from another
photograph.

**An award certificate held up in the frame is the same kind of source, and a
better one.** The sixth 2024 batch put both 2024 certificates in front of the
camera: "BEST NEW FILMMAKER / John Eboli / for Nantucket Cribz" and "AUDIENCE
AWARD / Oscar Waldman & Sam Billings / for Azure Odyssey", each readable after
a crop and a brightness lift, one of them upside down in the winner's hands and
needing a 180-degree rotation. That is the festival writing down who won what,
inside the photograph, so it names people exactly as a chair placard does --
and it names the *film* too, which a placard does not. Both readings matched
this repo's own `AWARDS["2024"]`, which is the corroboration to look for before
writing a name. **Where the certificate is in frame but the handwriting is not
legible, name nobody**: nsf2024-62 shows an AUDIENCE AWARD certificate and
stays generic, because reading the names off a *different* photograph is the
face-matching this rule exists to prevent. A certificate that names two people
without saying which is which names them both and assigns neither.

**Cross-check every new batch against the photos already published, before
encoding.** The sixth 2024 batch of fourteen held nine distinct pictures, and
three of those nine were already on the page -- they scored 1, 1 and 0 against
nsf2024-58, -59 and -60. Five more were second renditions of five others in the
same batch, at distances 0 and 1. Re-sends are normal and cost nothing to
detect; encoding them silently puts the same photograph on the page twice,
which no later check would catch, because two copies of one picture are two
valid entries. Run the new files against `image-originals/` first, every time.

**A stem number is not a display position.** Stems are numbered in arrival
order; the page shows `SHORTS_PHOTOS` in *list* order, and the 2024 list is
chronological -- lobby, audience, panel, awards. When a late batch brings a
lobby photo in after the award photos, put the entry where it belongs in the
list and leave its stem alone. Renumbering to close the gap means renaming two
files per photo and rewriting every entry below it, for nothing a visitor can
see. Leave a comment saying so, or the next person will "fix" it.


## Production credits

Most of the archive is NCTV's own work. A video made by an outside production
company carries that maker's credit **under its thumbnail** -- the site owner
calls these "tags" (the YP tag, the SP tag, the NM tag, the TN tag).

> **Never add a tag that was not asked for.** Standing rule, 2026-10-25: no NM,
> YP, SP or TN tag goes on a video unless the site owner names that video and
> that tag. Who made a video is a claim about someone else's work, and YouTube text,
> channel ownership and a run of similar videos are not evidence. When a video
> looks like it should carry one, say so and leave the card alone.

This is the settled placement, agreed 2026-10-25. It does not vary by company:

```
Video created by:  [mark]
click for website
```

Two right-aligned lines of mono text ending flush on the mark's left edge, the
square mark beside them at two text lines tall, the whole block right-justified
so the mark's right edge meets the thumbnail's. An inline version inside the
description was tried first and dropped.

Not every tag has all four parts. `credit_block(name, logo, url)` builds the
full one; a maker with no website loses the "click for website" line and nothing
in its block is clickable. `NM_CREDIT` is wording alone, `TN_CREDIT` is wording
plus mark. All of them use `.video-credit`, which is what puts a block under the
thumbnail at the right edge in the same face and size.

`credit_block(name, logo, url)` near `ASSET_VER` builds every one of them, and
`VIDEO_CREDITS` maps YouTube id -> block. A new video is one line; a new company
is a logo plus two. Keyed by id rather than set on the video's tuple, so a credit
follows its video onto every page that lists it -- several are cross-listed.

Four things to keep:

- **Only "click for website" is the link.** Not the wording above it, not the
  mark. The link needs its `aria-label` and the mark needs the company name as
  its `alt`, because the name appears nowhere else in the block.
- **Logos are 96px square WebP** in `assets/`, 2x the 46px they render at, with
  the original in `image-originals/`. A new logo means bumping `ASSET_VER`.
- **Remove any production credit already written into the description**, or the
  card says it twice. "60 Years of Conservation" carried "Produced by Dan
  Driscoll and September Productions" from the Foundation's own YouTube text.
- **Check YouTube's own description before crediting a video.** The same card
  was first going to be credited to the wrong company; the YouTube text caught
  it.

### The NM tag

Novation Media's is the one credit set by rule rather than one video at a time:
the NHA videos **posted to YouTube in 2024 or later** carry "Edited by Novation
Media" (Frank, 2026-10-25). The rule describes how the list was built; it is
not standing permission to extend it. `NM_VIDEOS` is a closed list of 77 ids,
and a newer NHA video does not join it without being asked for -- see the
standing rule above. It is the same block with the two parts it
has no use for removed -- there is no mark and no site, so no "click for
website" line -- and `NM_CREDIT` reuses `.video-credit` so the placement, face
and size match the other two exactly.

`NM_VIDEOS` near `ASSET_VER` holds the 77 ids, grouped by year, and is folded
into `VIDEO_CREDITS` after the hand-set entries so a video that names its own
production company keeps that block instead.

Two things to keep:

- **The cutoff is the upload date, not the event year.** The NHA's year buttons
  follow the event, so a 2023 lecture posted in 2024 is tagged and filed under
  2023. That is correct, not a bug. If asked to extend the list, read the dates
  off YouTube (`yt-dlp --print "%(id)s|%(upload_date)s"`) rather than guessing.
- **A video that names a different maker on its own card is left out.** Three
  are: the two "Nantucket About Town" episodes print "Edited by Andrew Daume"
  in their own description text, and `8NRGe4SHOcs` is Ric Burns's film. Flag
  cases like these rather than letting the date rule decide them.

### The TN tag

Nantucket Government 101 on the Civic TV page is the Town's own series, so every
video in it carries "Created by the Town of Nantucket's / Communications Office"
beside the Town seal, with nothing clickable -- the Town has no site the block
sends anyone to. It is the second rule-based tag, and the only one set off a
list rather than off ids: `VIDEO_CREDITS.update({vid: TN_CREDIT for vid, *_ in
GOVT101})` sits directly under `GOVT101`, so a department added there is
credited without a second edit. That is deliberate (the site owner was told);
it is the section's defining property, not a guess about someone else's work.

Two things it changed, both worth knowing before touching the Civic TV page:

- **Government 101 cards are `nl_episode()`, not `civic_card()`.** A tag is
  drawn by `nl_episode()`, which also puts the watch link under the description
  rather than under the thumbnail, which is where the tag goes. The site owner
  asked for exactly that layout on 2026-10-25, pointing at the Golf Club
  Foundation page. The section no longer carries the note that used to sit above
  its cards.
- **`AWARD_COLORS`, `trophy()` and `nl_episode()` now live beside
  `VIDEO_CREDITS`** near the top of the file. They were defined around line
  27400, but `videos_pages` is assembled around line 26480 and Government 101
  calls `nl_episode()` while it is being built, so the definitions had to come
  first. Nothing else moved and no other page's output changed.

## A document on a card — the Town Meeting warrants

A civic card normally offers its posted agenda, which the button swaps for the
description in place. Five cards offer a whole document instead — both
sittings of the 2025 Annual Town Meeting, both of the 2026, and the November
4, 2025 Special Town Meeting — whose buttons read **Warrant** and open that
meeting's warrant in an overlay (`initDocModal()` in `site.js`, `.docmodal` in
`styles.css`). In place would push every meeting below them off the screen;
the 2025 Annual alone is 104 articles and 70,000 words. Frank asked for 2026,
then 2025, then the Special on 2026-10-27; he explicitly did not want the PDFs
hosted. **A card can carry more than one**, and all five do: a second
button, **Summary**, opens the Town's list of how each article was disposed
of and by what vote. It is a six-document, ten-button page now, so neither
count is a check on the other.

`CIVIC_DOCS` in `build.py` maps a video id to a list of `(button label,
overlay heading, body html)`, and `civic_card()` checks it before it checks
`CIVIC_AGENDAS`, writing one button per entry in the order given. **Where the
button goes is a second decision.** A heading listed in `CIVIC_DOC_NOTES` is
written under the title instead, led by the line that dictionary gives it
(`.watch-episode__note`) — the summary reads *"To see the vote results,
please click this button:"*, which is Frank's wording. Everything else sits
in the actions row beside the watch link, which is `flex-wrap` and takes a
second button without crowding. The note is a `<p>` of its own and not a
`.watch-episode__desc`, so it is never clamped and never reaches the search
index. **The bodies are not in the cards.** `civic_doc_store()` emits each distinct document once,
hidden, at the foot of the Civic TV page, and each button names one with
`data-doc`; cards sharing a heading share the copy, because one warrant
governs every sitting of its meeting. A copy per card put the 2025 warrant
into the page twice at half a megabyte each. Nothing is fetched, so it works
offline, and nothing reaches the search index, which reads
`.watch-episode__desc` only. The three warrants and three summaries add
about 0.8 MB to `videos-civic.html`, which is 5.3 MB now.

The overlay **moves** the document into itself and hands it back on close, so
the page holds one copy and an in-page search never finds a sentence twice.

Six things about the warrant text itself:

- **It is extracted, never retyped, and the tool reads scans as well as
  born-digital files.** `tools/warrant-to-html.py` reads the PDF and writes
  the literal in the exact form `build.py` holds. Another year is one run of
  that tool plus one line in `CIVIC_DOCS` per sitting. **Check which kind of
  PDF it is**, because a scan is marked up a different way: the Special Town
  Meeting warrant is a photocopy — thirteen page images with an OCR layer
  under them and not one drawable rectangle in the file — so the
  box-and-hairline test below finds nothing. `scanned()` catches that case
  (no drawings anywhere, an image on every page) and `Shading` renders the
  page grey at 3x and takes the median of each character's own column
  instead, so the highlighting still comes out as `<ins>`. What cannot come
  out is `<del>`: on a scan a rule through a word is just more ink. **How
  good the copy is decides whether any of that works.** The first copy Frank
  had measured 245-253 under highlighted lines against 253-255 under plain
  ones, which overlap; the motions edition he sent later separates at 212
  against 255. `TM_WARRANT_STM_2025` is regenerated with
  `tools/stm-2025-warrant.py` rather than with the tool directly — that
  wrapper exists for one block, the Use Chart, whose twenty district names are
  set sideways down twenty narrow columns and arrive as a hundred loose
  fragments.
- **Two warrants are enough to show how much the typesetting varies.** The
  tool finds the running footer rather than assuming a band — 2026's sits in
  the bottom 44pt, 2025's reaches 68pt up — and it has to tell a highlight
  from the rest of the page furniture. 2025 draws its tables as filled
  rectangles: 1,828 black slivers a point wide for the borders and 530 white
  blocks the width of a column for the cells. **A highlight is a box with a
  real colour, lighter than black and darker than white.** Taking every box
  of about line height, which is what the first version did, marked 52 runs
  of the 2026 warrant as new language that the PDF does not highlight.
- **The Town marks bylaw edits by drawing rectangles, not by styling text** —
  a grey box behind new language, a hairline through language to be struck.
  Any ordinary text extraction loses both and welds the old wording to the
  new; "as measured by the exterior interior faces of the exterior walls" is
  one real line. The tool tests every character against its page's rectangles
  and emits `<del>` and `<ins>`. Every zoning article tells the reader that
  new language is highlighted and deleted language struck through, so the CSS
  has to keep looking like that.
- **A line break is not a word break, and not a tag break either.** The
  warrants hyphenate across lines, so joining the lines with a space wrote
  "non- substantive" and "Short- Term" into all three of them. `knit()` drops
  the space after a hyphen that follows a letter or digit — but not after
  the Massachusetts drafting idiom "words:- select" — and closes the
  `</ins><ins>` seam at each line end, which had been striping the highlights
  into bars.
- **A summary is not a warrant and is not read the same way.** The Town
  publishes its action summary as plain text, so there is nothing to measure
  and nothing to mark up. `tools/action-summary.py` turns it into a
  `TM_SUMMARY_*` literal: the lead, a `<p>` per paragraph of it, then one
  `<p>` per article with the title in `<strong>` and the result after it. It
  rewords nothing — the only repairs are the ones copying out of a PDF asks
  for, a vote rejoined across a page break and a space dropped before a colon
  or a period — and it refuses to run unless the articles number from 1
  without a gap and every one states a result. **Where a title ends is told,
  not guessed**, because the Town set all three meetings differently:
  `--split call` (the default) ends it where the call state begins, which is
  both Annual Town Meetings, and `--split line` gives the title the line to
  itself with the vote underneath, which is the 2025 Special. Guess wrong and
  a title swallows its vote or breaks mid-sentence, so read a new summary's
  output before shipping it. **An article with no call state at all is the
  Town's omission, not a parse failure** — 2025's Article 87 has none — and
  `call` then ends the title at its first sentence and says so on stderr.
- **The stored blocks carry no straight quotes of either kind.** They are
  single-quoted Python literals holding double-quoted class attributes, so the
  tool turns every `'` into `&rsquo;` and every `"` into `&ldquo;`/`&rdquo;`.
  The tool refuses to print a literal that does not rebuild its HTML byte for
  byte.

## Tables in a posted agenda

**Check every agenda for a table before storing it.** CivicClerk serves each
agenda two ways, and `CIVIC_AGENDAS` is built from the plain-text rendition,
which is fine until the agenda carries a table. Then it flattens the table into
one run-together list item **with the columns interleaved** -- wherever a cell
wraps to a second line, that line is emitted wherever it physically fell, which
drops it inside the neighboring cell:

```
35 Select Board for Zoning Map Change: RC-2 to CMI or CTEC - 43 Nobadeer
Planning Board Farm Road
```

is really article 35, sponsored by *Select Board for Planning Board*, to make a
*Zoning Map Change: RC-2 to CMI or CTEC - 43 Nobadeer Farm Road*. The words are
out of order, so splitting the stored string cannot repair it -- a regex just
produces tidy-looking rows holding the wrong text. **Read the PDF instead.**

`tools/agenda-tables.py` does it, and the tables are ruled, so it is geometry
rather than guesswork: vertical rules at x=95.6/145.0/235.0/561.4 and a
horizontal rule every ~25.3pt, the same in the 2025 and 2026 templates.

```
python3 tools/agenda-tables.py --scan                            # who is affected
python3 tools/agenda-tables.py --board "Finance Committee" --year 2026
python3 tools/agenda-tables.py --board "Finance Committee" --year 2026 --apply
```

Without `--apply` it prints the rebuilt entries to paste. With it, it writes
them and leaves `build.py.bak-agenda-tables`. **It is a content change, so
`ASSET_VER` must not move** -- the output is a nested `<ol>`, the vocabulary
`CIVIC_AGENDAS` already uses, and the stylesheet already draws level two
lower-alpha. 18 agendas and 188 article rows went through it on 2026-10-27/28;
no stored agenda holds a flattened table now.

Four things it handles that are not obvious:

- **A date can carry several postings, and CivicClerk labels Agenda Packets
  `type: Agenda` too.** March 4, 2025 offered a 2-page agenda and a 145-page
  packet; February 20 had four postings. Scoring the candidates against the
  stored text picks the *packet*, which contains the agenda plus everything
  else, so the script scores only to rule out the unrelated and then takes the
  shortest survivor.
- **A cell that overflows its ruled row gets its own ruled row**, with an empty
  Article cell -- `['', 'al', '']` is the tail of "et al". Those fold into the
  row above. Five of the eight 2026 agendas needed it and none of the ten 2025
  ones did, so a clean run proves nothing about the next.
- **A leading article number can be eaten as a list marker.** Where a row began
  a line, whatever built the stored HTML read the number as an ordered-list
  marker and consumed it. Both shapes are real: February 5, 2026 opened a
  spurious nested `<ol>` mid-table and lost article 1's number; March 10, 2026
  started a new sibling `<li>`, lost article 8's number, and that stray item
  then swallowed the real agenda item 8, "Committee Reports". So a rebuild can
  *gain* content. Each gain is declared in `RECOVERED` and asserted on rather
  than absorbed into a total -- on March 10 the arithmetic nets to zero, which
  is exactly how a real change hides.
- **The table can run past its own list item**, so the script walks forward
  until every cell token is accounted for. Replacing only the header's own item
  would leave half a table behind.

What makes it safe to run unattended is the token check: every word of every
extracted cell must already be in the stored text, allowing for the one literal
"Article" the template adds per row and the four scrambled header words it
drops. Passing proves the rebuild is a re-ordering of the posting and not a
paraphrase. It compares alphanumeric tokens only -- a raw word comparison trips
over the added dashes and brackets, and over `Owner&rsquo;s` in the stored text
against `Owner's` in the PDF. Replaying both runs through the script reproduces
the hand-made result byte for byte.

**An unfamiliar table header is reported, not rendered.** The row format --
`Article 8 &ndash; Appropriation: ... (Select Board)`, description first and
sponsor in brackets -- is Frank's choice for the one header seen so far. A
table with different columns stops and asks.

**Leave the postings' own inconsistencies alone.** The same petitioner appears
as both `Stephen Maury et al` and `Stephen Maury, et al` across agendas, and one
description carries literal asterisks (`*aka Van Gilder Avenue*`). House rule is
the posting's own capitalization and punctuation, so all of it stays.

## Staff & Board page

Both rosters are `person_card()` over `STAFF` and `BOARD`, two lists of dicts
near the top of `staff_body`. A dict is `name`, an optional `role`, an optional
`email` and an optional `bio` (a list of paragraphs, which becomes the Read bio
disclosure). The monogram is derived from the name, so nothing has to be typed
twice.

**These two lists are the one place on the site that is plain text, not
entities.** `_esc()` escapes `&`, `<` and `>` and nothing else, so a role is
written `Creative Director & Editor` with a literal ampersand and a bio uses
straight apostrophes. Everywhere else in `build.py` the copy carries
`&rsquo;`, `&mdash;` and `&amp;` already escaped. Paste `&amp;` into a role
here and the page shows `&amp;`.

**A row is one column at every width** (Frank, 2026-10-30). It used to be 288px
for the name and role with the bio beside them, which gave a job title a 288px
measure and broke the long ones over three lines -- "SPORTS / BROADCAST /
HOST/PRODUCER". Stacking it also puts Read bio under the title rather than
beside it, which is what Frank asked for.

**Name and email share one line** (Frank, 2026-10-31), in `.person__line`:
`align-items:baseline`, so the two sit on one baseline rather than the address
floating in the middle of the name's line box, and `flex-wrap:wrap`, so a pair
too wide for the row drops the address under the name instead of overflowing.
The email's old `margin:14px 0 0` went with the position that needed it.

**The address is set in the name's own rule**, asked for the same day: same
face, same size. It is written as a shared selector list --
`.person__name,.person__email{...}` in both the base rule and the 20px type
scale -- rather than a second rule holding the same numbers, so resizing the
name carries the address with it. **Colour is the only thing separating them
now**: the name is `--ink`, the address `--ink-soft`. Change that and the two
become indistinguishable.

**A `|` divides them** (Frank, 2026-10-31): `.person__sep`, emitted by
`person_card()` inside the `{email}` string so it exists only where there is
an address to divide from -- a person with no email gets no bar hanging off
the end of their name. It carries `aria-hidden="true"`, being decoration
between two things a reader can already see are separate, and it is in the
shared size rule with the name and the address so its cap height matches
theirs exactly. Its colour is `--sand`, the token the row hairlines use, so it
reads as the same family of rule rather than as a third piece of text.

**Under 760px the row stacks outright** -- `flex-direction:column` and the bar
`display:none` -- rather than being left to `flex-wrap`. Wrapping would strand
the bar at the head of the address's own line, and it would strand at a
different width for every name: with the sizes matched the pair is wide, and
"JohnCarl McGrady" plus his address is the first to break. Stacking at a fixed
breakpoint makes it one behaviour instead of ten. Between about 660 and 760px
the longest pair would still have fitted on one line; that is the cost of the
fixed breakpoint and it is deliberate.

**The two group labels are `<h2 class="eyebrow">`, not spans.** The page had no
`<h2>` at all between the `<h1>` and the names once the titles came off on
2026-10-30, so the groups were visual only. Converting them meant stating
`line-height:1.65` on `.section__head .eyebrow`: `h1,h2,h3,h4` set 1.05, and the
dot is pinned with `calc(.825em - 5.5px)`, which is half of a 1.65 line box.
Without the pin the dot rides up off the cap line of **every** section title on
the site, not just these two. It is a no-op for the spans, which inherited 1.65
from `body` anyway -- the home page's three heads measure identically either
way. Convert another eyebrow to a heading and nothing more is needed.

**`BOARD` is the two officers, then the other eight A-Z by surname** (Frank,
2026-10-31): Dan Driscoll (President & Clerk), John Copenhaver (Treasurer),
then Burkhart to Soeder. It was sorted straight through earlier the same day,
which buried the officers mid-list; this is the correction. **Do not re-sort
the list as a whole** -- a script that does will look like it is tidying up and
will move the officers back down. A new member goes into the A-Z run below
them, keyed on the last whitespace-separated word of the name.

## Atheneum page specifics

`ATHENEUM_SERIES` holds video IDs grouped by series then year.
`ATHENEUM_TITLES` maps video ID → `(title, description)`. All 66 videos are
populated. Any ID missing from `ATHENEUM_TITLES` falls back to a generated
"<series> <year>" label, so new videos can be added IDs-first and captioned later.

Title patterns, normalized per section — match them when adding videos:

| Section | Pattern |
|---|---|
| Geschke Lectures | `<Year> Geschke Lecture Series: <Speaker>, <Talk title>` |
| Dance Festival | `<Year> Nantucket Dance Festival <Event type>` |
| Summer Forum | `<Year> Nantucket Annual Summer Forum` |
| Constance Laibe Hays | `<Year> Constance Laibe Hays Memorial Lecture: <Speaker>` |
| One Book One Island | varied by design — genuinely different event types |

Where a title carried a date that appears nowhere else, the date was moved to
the head of the description as its own line (e.g. "July 30, 2018").

## Book Festival page specifics

`BOOKFEST_YEARS` maps year → list of `(id, title, description)`: 2017, 2018,
2019, 2022, 2023, 2024, 2025, 2026 — 183 videos. There is no 2020 or 2021
button because there was no festival those years. Built with
`collapsible=False`, so the archive is one static heading rather than a
toggle.

Two conventions to keep when adding videos:

- **Titles carry no year or festival prefix.** The videos arrived with six
  different ones ("NBF 2017:", "2022 BookFest -", "BookFest 2024:"); they were
  all stripped, since the year is already on the button above the card. Promo
  clips, whose whole title was the festival's name, became "Festival Promo".
- **Book titles are wrapped in `<cite>`**, which `styles.css` renders italic.
  `<cite>` rather than `<em>` because a screen reader gives `<em>` vocal
  stress, which is wrong for a title. Periodicals and films on that page are
  not yet marked up.

Descriptions were written from the videos' auto-captions, two sentences each.
Videos with no transcript, and all montage/promo clips, have none by request.

## NHA page specifics

The largest page on the site: 675 cards in a two-level accordion under
"Programs". The top level is All Lectures, Nantucket Documentaries, Historic
Films, and two `Picker` parents — "Browse by Topic" (16 children) and
"Browse by NHA Program" (9) — whose children are drawn as rows of buttons
(Frank, 2026-10-25) and are alphabetical. Three of those buttons open a panel
holding a year picker, so this is the one page where a `.yearpick` sits inside
a `.yearpick`. Two sort cases
worth knowing: &rsquo;Sconset files under S, the leading apostrophe being
punctuation rather than a letter, and the four `Symposium:` playlists sort
together under S, then by what follows the colon.

Not every NHA playlist is on the page. Webinars, Special Events and
Fundraisers, and About the NHA were excluded by request, not overlooked.

Things that were decided deliberately and should not be "fixed" without asking:

- **Dead videos are left out.** Private and unavailable IDs in the NHA's
  playlists are skipped rather than linked; the NHA clears them on their own
  account.
- **Vertical videos are left out.** Shorts are dropped by comparing yt-dlp's
  `width` and `height` — `fetch-video.py --meta FILE` writes both.
- **Cross-listed videos stay.** ~38 videos appear in two sections because the
  NHA files them in two playlists. This is intentional.
- **Historic Films is ordered by when the footage was shot, not by upload
  date, and is not grouped by year.** 41 of its 44 videos were uploaded in
  2011-2012 when the collection was digitized, so upload dates sort it into
  noise and year buttons would put nearly everything under two labels. The
  list runs 1920s to 1976 by shooting date, read from the titles and
  descriptions. See the comment above `NHA_FILMS` in `build.py` before
  re-sorting it — a naive "earliest year in the description" scan gets six
  entries wrong.

## School Videos page specifics

The only page that introduces more than one organization. The hero is the
district; each school below it gets an `org_banner()` — the same shape as a
page hero but shorter, flatter and with no visible title, since the school's
name is already in its logo. A visually hidden `<h2>` keeps the heading for
screen readers and the document outline. Each school's
`programs_section(..., heading=None)` drops the "Programs" head so it is not
repeated three times down the page.

`NPS_COMMITTEE` is keyed by **school year**, July to June, as strings
("School Yr 25-26") rather than the integer years every other section uses.
`program_group()` sorts and renders dict keys as-is, so string keys need no
code change.

**Every list on this page reads newest-first.** All three of them --
`NPS_COMMITTEE`, `WHALER_WORD` and `CPS_PULSE` -- are stored oldest-first and
rendered through `programs_section(..., newest_first=True)`, so the END of a
list is the TOP of its panel. Frank asked for this on 2026-11-05. Until then
only the School Committee list was reversed; Whaler Word and The CPS Pulse ran
**Episode 1 at the top**, which read naturally for a numbered series. He was
told that flipping them makes the episode runs count down -- Episode 34 first,
Episode 1 last -- and asked for it anyway, so the whole site now follows one
rule. Do not revert either list to episode order.

`newest_first` is passed per CALL and applies to every group in it, so the two
edits also reversed Graduation, Senior Awards and 8th Grade Promotion. Those
hold exactly one card per year panel, so it changed nothing for them -- but a
second card added to any of those panels now sorts newest-first too.

**Place a new card by its date, which usually means appending**, exactly as on
the Civic page. `verify.py`'s `school-dates-descending` checks all 18 dated
lists from the built page and fails the build if one runs backwards, including
if a `newest_first=True` is ever dropped.

**Flagged, not fixed: two CPS Pulse cards are both "Episode 25"** --
Apr. 11th and Mar. 28th 2025. The dates are right and the page order is right;
the numbering is NSC's own in the YouTube titles, and that 17-card year is a
partial run with real gaps anyway (36, 35, 34, 31, 30, 29, 26, 25, 25, ...),
so the duplicate is the only thing out of place. Left as posted.

Deliberate, and not to be "fixed":

- **Meetings that have not happened yet are excluded.** The playlist carries
  scheduled premieres months ahead; they are filtered on yt-dlp's
  `live_status == is_upcoming`.
- **Only the two most recent school years have descriptions.** These meetings
  run two to four hours each, and 145 older ones are deliberately blank rather
  than thin. The descriptions YouTube holds are the same boilerplate paragraph
  with a dead Zoom registration link on every meeting, so they were not kept.
- **Meetings are filed by the date in their own title**, not the upload date.
  One title is wrong at the source — "2/4/29" went up in February 2020 — and is
  corrected to 2020-02-04.

## Fetching video metadata

`tools/fetch-video.py` pulls titles and descriptions from YouTube via `yt-dlp`
and prints them in this file's house format — HTML entities already escaped,
wrapped to 100 columns. Paste the output straight into `build.py`.

Use it instead of copying text off a YouTube page. It removes the entire class
of damage described under "Text pasted from YouTube arrives damaged" below.

```
python3 tools/fetch-video.py ID [ID ...]                 # flat (id, title, desc) lists
python3 tools/fetch-video.py --format atheneum ID ...    # ATHENEUM_TITLES dict entries
python3 tools/fetch-video.py --playlist URL              # a whole channel or playlist
```

Three flags worth knowing: `--paras 1` keeps only the first paragraph (YouTube
descriptions usually trail off into boilerplate), `--strip-urls` drops bare
links, and `--meta FILE` writes `id<TAB>year<TAB>width<TAB>height` rows
alongside the output. `--meta` is how vertical videos and upload years are
found — `height > width` means a Short. Progress goes to stderr, so
`> out.txt` captures clean output only.

**Requires `yt-dlp`**, found at `~/.local/bin/yt-dlp` or anywhere on `PATH`
(override with `--ytdlp PATH`). It is not bundled; install the official binary
from <https://github.com/yt-dlp/yt-dlp/releases> if it's missing.

Three things to watch:

- **Playlists can list the same video several times.** The 2019 playlist had 65
  entries for 28 videos. Deduplicate before building a year, or the page repeats
  cards. `--playlist` does not deduplicate.
- **A video with no YouTube description yields `""`**, marked with an inline
  `# TODO` comment and listed on stderr. Several descriptions in `build.py` were
  written by hand and do not exist on YouTube — pasting over them loses real
  copy. Check the TODO lines before committing.
- **It fixes mechanical damage only.** A misspelled surname or a wrong book
  title still needs a human read. Proofread the output.

## Gotchas learned the hard way

**HTML inside a label breaks attributes.** The Summer Forum section label
contains a `<span>` for the co-sponsor note. Interpolating that into an
`aria-label` closed the attribute early and dumped markup onto the page as
visible text. `program_group()` strips tags with `re.sub(r"<[^>]+>", "", label)`
before using a label in an attribute. Do the same anywhere else.

**Text pasted from YouTube arrives damaged.** Recurring problems, all seen in
real copy: mojibake (`Ã ` for `à`, `â€™` for `'`) from UTF-8 read as cp1252;
quotes that open single and close double; YouTube redirect wrappers around links
(`youtube.com/redirect?event=video_description&redir_token=...`); timestamp links
wrapped around times like "9:30"; doubled spaces; invisible characters such as a
zero-width joiner at the end of a title (one real 2025 Book Festival title ends
in one) — they display as nothing but leave stray bytes in the HTML. Always read
pasted metadata before committing it — several real errors (a misspelled surname,
a missing verb, a wrong book title) were caught this way.

Don't paste by hand if you can avoid it — `tools/fetch-video.py` pulls the text
straight from YouTube already cleaned and escaped. See "Fetching video metadata"
above. (The mojibake is cp1252, not Latin-1: `â€™` contains `€`, which Latin-1
can't encode, so a Latin-1 round-trip repairs nothing.)

**YouTube thumbnails, and why `onerror` doesn't work.** `nl_episode()` falls
back to `img.youtube.com/vi/<id>/maxresdefault.jpg` when no local thumbnail is
given. Older uploads have no `maxresdefault`, and YouTube answers those with a
404 whose *body* is a valid 120x90 grey placeholder — so the browser decodes it
and fires `load`, not `error`, and an `onerror` handler never runs.
`initThumbFallback()` in `site.js` detects the placeholder by its width and
swaps in `hqdefault`, which always exists. This is automatic; nothing to do
when adding videos. Nantucket Life uses local thumbnails in `assets/`.

**Measuring anything inside a closed `<details>` returns zero.** The ten-line
description clamp (`clampDescriptions()` in `site.js`, "Click to See More")
can't tell whether text overflows until its section is actually visible, so it
re-runs on `<details>` toggle and on board-, year- and quarter-button clicks.
The Civic TV page needs all three: most of its cards sit three pickers deep
(two for the boards in `CIVIC_NO_QUARTERS`) and have no measurable height until
the innermost panel is showing. Anything else
that measures rendered height needs the same treatment. When checking this in a
browser pane, give the pane a real width first — a zero-width viewport reports
every description as overflowing.

**`yt-dlp --print` does not interpret `\t`.** `--print "%(id)s\t%(width)s"`
writes a literal backslash-t, not a tab, so `awk -F'\t'` sees one field and
silently reports nothing. This cost two debugging sessions: once parsing a
playlist list, once scanning for vertical videos, where it reported 0 of 13.
Use `fetch-video.py --meta` instead, which writes real tabs.

**`yt-dlp` inside a `while read` loop eats the loop's input.** It reads stdin,
so the loop consumes its own list and runs once. Redirect it: `yt-dlp ... </dev/null`.

**English captions are often under `en-orig`, not `en`.** On videos with
multiple audio tracks, YouTube names the original-language auto-captions
`en-orig` and publishes a plain `en` that is a *machine translation* of it.
`--sub-lang en` can miss the real track entirely and report a video as having
no captions when it has a half-megabyte transcript. Worse, when `en` does
download it reads like a bad translation — one School Committee meeting came
through calling a school "the Impedance school". Ask for both, original first:

```
yt-dlp --write-auto-subs --sub-lang "en-orig,en" --sub-format vtt ...
```

Check with `--list-subs` before concluding a video has no transcript; four
School Committee meetings were wrongly recorded as caption-less this way.

**Then pick the file by name, not by size.** Downloading both leaves two files
and the choice still has to be made. On 2026-10-11 a selection of `ls -S | head
-1` took the larger file, which for one video was the translation, and it
reached the point of being read before the giveaways showed up — "Office of
City Administration", "the Health Board", "a hardship discharge procedure",
"Congratulations" for hello. The site owner's rule since: **always `en-orig`,
never `en`.** The one exception is a video that has only `en` and no `en-orig`
— there the `en` track is the original recognition, not a translation.

**Use HTML entities** in titles and descriptions: `&amp;` `&rsquo;` `&ldquo;`
`&rdquo;` `&ndash;` `&mdash;` `&hellip;`. Unescaped `&` can break the page.

## Verifying a change

After rebuilding, it's worth checking:

- every referenced `assets/...` file exists
- every internal `href="*.html"` resolves
- no duplicate video IDs where they'd be unintended (note that a description
  can legitimately contain a `youtu.be/` link to another video — match on the
  card's own `watch-episode__link`, not on any URL in the page)
- the page parses (`html.parser.HTMLParser().feed(...)`)
- the build is idempotent: run it twice, compare `md5 -q` of a page
- the card count didn't change when it shouldn't have — reorganizing sections
  should move cards, never drop them

Note that a page can pass all of these and still render wrong — the `aria-label`
bug above did. **Look at the actual page in a browser.**

## Previewing

Open `index.html` directly in Safari (`file://` works — no server needed; no
module scripts, no `fetch()`, no absolute paths). Hard refresh with
**Cmd+Option+E, then reload**.

Stay online when previewing: fonts come from Google Fonts and some thumbnails
from YouTube.

For a closer match to production: `python3 -m http.server 8000`, then
`http://localhost:8000`.
