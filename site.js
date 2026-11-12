/* =====================================================================
   Nantucket Community Television — site.js
   ---------------------------------------------------------------------
   Behaviour only. The nav and footer markup is built into every page by
   build.py, so it is on screen before this file runs.

   TO ADD / RENAME / REORDER A NAV LINK: edit NAV in build.py, not here.
   ===================================================================== */

/* ---------- nav behaviour ---------- */
function wireNav(nav){
  const burger = nav.querySelector(".nav__burger");
  burger.addEventListener("click", ()=>{
    const open = nav.classList.toggle("is-open");
    burger.setAttribute("aria-expanded", open);
  });

  const items = [...nav.querySelectorAll(".nav__item")];
  const mobile = ()=> window.matchMedia("(max-width:1100px)").matches;

  items.forEach(item=>{
    const trigger = item.querySelector(".nav__link");
    const hasPanel = item.querySelector(".nav__panel");
    if(!hasPanel) return;

    // On desktop, hover + keyboard focus open the panel via CSS — the click
    // just shouldn't navigate. On mobile, click toggles the accordion.
    trigger.addEventListener("click",(e)=>{
      e.preventDefault();
      if(!mobile()) return;               // desktop handled by CSS hover/focus
      const open = item.classList.contains("open");
      items.forEach(i=>{
        i.classList.remove("open");
        const t=i.querySelector(".nav__link"); if(t) t.setAttribute("aria-expanded","false");
      });
      if(!open){ item.classList.add("open"); trigger.setAttribute("aria-expanded","true"); }
    });
  });

  // close dropdowns when clicking outside
  document.addEventListener("click",(e)=>{
    if(!nav.contains(e.target)){
      items.forEach(i=>i.classList.remove("open"));
    }
  });
  // esc closes everything
  document.addEventListener("keydown",(e)=>{
    if(e.key==="Escape"){
      items.forEach(i=>i.classList.remove("open"));
      nav.classList.remove("is-open");
      burger.setAttribute("aria-expanded","false");
    }
  });
}

/* ---------- footer year ----------
   The footer is built into every page, so only the year can go stale between
   builds. That one word is all JavaScript touches here. */
function refreshFooterYear(){
  const el = document.getElementById("footer-year");
  if(!el) return;
  const now = String(new Date().getFullYear());
  if(el.textContent !== now) el.textContent = now;
}

/* ---------- latest NCTV news carousel (home) ----------
   One card showing, the rest stacked behind it under visibility:hidden.
   It turns itself over every seven seconds, and the arrows and dots below
   it set the card directly. Anything the visitor does restarts the clock,
   so the card they asked for gets its full turn rather than the remainder
   of the one that was already running. */
function initNewsreel(){
  const box = document.querySelector("[data-newsreel]");
  if(!box) return;
  const slides = [...box.querySelectorAll(".newsreel__slide")];
  const copies = [...box.querySelectorAll(".newsreel__copy")];
  const dots   = [...box.querySelectorAll(".newsreel__dot")];
  if(slides.length < 2) return;
  // The two small cards either side are one <img> each; their src follows the
  // big card. Both files are already in the browser from the track above.
  const peeks = {
    prev: box.querySelector('[data-newsreel-peek="prev"]'),
    next: box.querySelector('[data-newsreel-peek="next"]')
  };
  const art = slides.map(s=>s.querySelector("img").getAttribute("src"));
  const ms = Number(box.dataset.newsreelMs) || 7000;
  const still = window.matchMedia("(prefers-reduced-motion:reduce)").matches;

  let at = slides.findIndex(s=>s.classList.contains("is-current"));
  if(at < 0) at = 0;
  let timer = null;

  function show(i){
    at = (i + slides.length) % slides.length;
    slides.forEach((s,n)=>s.classList.toggle("is-current", n===at));
    copies.forEach((c,n)=>c.classList.toggle("is-current", n===at));
    if(peeks.prev) peeks.prev.src = art[(at - 1 + slides.length) % slides.length];
    if(peeks.next) peeks.next.src = art[(at + 1) % slides.length];
    dots.forEach((d,n)=>{
      d.classList.toggle("is-current", n===at);
      if(n===at) d.setAttribute("aria-current","true");
      else       d.removeAttribute("aria-current");
    });
  }
  function stop(){ if(timer){ clearInterval(timer); timer = null; } }
  function start(){
    stop();
    // Nothing moves on its own for a visitor who has asked for less motion;
    // the arrows and dots are how they get through the cards.
    if(still) return;
    timer = setInterval(()=>show(at + 1), ms);
  }
  function go(i){ show(i); start(); }

  // Both the arrow and the small card on that side carry the attribute.
  box.querySelectorAll("[data-newsreel-prev]")
     .forEach(el=>el.addEventListener("click", ()=>go(at - 1)));
  box.querySelectorAll("[data-newsreel-next]")
     .forEach(el=>el.addEventListener("click", ()=>go(at + 1)));
  dots.forEach((d,n)=>d.addEventListener("click", ()=>go(n)));

  // Hold still while someone is reading a card or reaching for a link in it.
  box.addEventListener("mouseenter", stop);
  box.addEventListener("mouseleave", start);
  box.addEventListener("focusin", stop);
  box.addEventListener("focusout", (e)=>{
    if(!box.contains(e.relatedTarget)) start();
  });
  // A background tab should not spend seven seconds a card getting through
  // the set where no one can see it happening.
  document.addEventListener("visibilitychange", ()=>{
    if(document.hidden) stop(); else start();
  });

  show(at);
  start();
}

/* ---------- scroll reveal ---------- */
function initReveal(){
  const els = document.querySelectorAll("[data-reveal]");
  if(!("IntersectionObserver" in window) ||
     window.matchMedia("(prefers-reduced-motion:reduce)").matches){
    els.forEach(el=>el.classList.add("in")); return;
  }
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(en=>{ if(en.isIntersecting){ en.target.classList.add("in");
      io.unobserve(en.target);} });
  },{rootMargin:"0px 0px -8% 0px",threshold:.12});
  els.forEach(el=>io.observe(el));
}

/* ---------- New Moon Fest: Official Film Selections movie picker ---------- */
function initMoviePicker(){
  /* Scope on the row of film buttons and the panels beside it, not on the
     wrapper. The New Moon Fest years were <details class="pastsel__year">
     until 2026-10-18 and are now panels of a year picker; keying off the
     structure instead of that class survives the change. */
  document.querySelectorAll(".pastsel__movies").forEach(function(row){
    var group = row.parentElement;
    var btns = row.querySelectorAll(".movie-btn");
    var panels = group.querySelectorAll(".movie-panel");
    btns.forEach(function(btn){
      btn.addEventListener("click",function(){
        var slug = btn.getAttribute("data-movie");
        var target = group.querySelector('.movie-panel[data-movie="'+slug+'"]');
        var wasActive = btn.classList.contains("is-active");
        btns.forEach(function(b){ b.classList.remove("is-active"); });
        panels.forEach(function(p){ p.hidden = true; });
        if(!wasActive && target){ btn.classList.add("is-active"); target.hidden = false; }
      });
    });
  });
}

/* ---------- Atheneum: year picker for lecture archives ----------
   Like the movie picker above, but one year is always selected: clicking the
   active year again leaves it open rather than collapsing to nothing. */
/* ---------- committee picker ----------
   The civic archive asks for a board before it asks for a year, so this is the
   outer twin of initYearPicker: same toggle, one level up. Its classes are
   deliberately distinct from the year picker's -- a nested .yearpick would
   otherwise be swept up by that function's descendant lookup.

   The reader's year and quarter follow them from board to board. Asked for on
   2026-10-11: picking a new board used to drop you back to no year and no
   quarter, so comparing the same months across two boards meant three clicks
   each way. The choice is remembered here, in memory only, so a page refresh
   starts over -- also asked for.

   Only the civic page has a board picker, and .yearpick is shared with the
   partner and school pages, which open on a year chosen in the markup. So
   everything below is scoped to .boardpick and is inert everywhere else. */
var civicPick = { year: null, quarter: null };

/* Clearing a level still clears every level below it. The difference is that a
   level is now re-selected from civicPick straight afterwards, when the board
   or year the reader moved to happens to offer what they had chosen. */
function clearPicks(root, btnSel, panelSel){
  root.querySelectorAll(btnSel).forEach(function(b){
    b.classList.remove("is-active");
    if(!b.disabled) b.setAttribute("aria-pressed", "false");
  });
  root.querySelectorAll(panelSel).forEach(function(p){ p.hidden = true; });
}

function initQuarterPicker(){
  document.querySelectorAll(".quarterpick").forEach(function(pick){
    var btns   = pick.querySelectorAll(".quarter-btn");
    var panels = pick.querySelectorAll(".quarter-panel");
    btns.forEach(function(btn){
      if(btn.disabled) return;
      btn.addEventListener("click", function(){
        var want = btn.getAttribute("data-quarter");
        if(pick.closest(".boardpick")) civicPick.quarter = want;
        btns.forEach(function(b){
          var on = b === btn;
          b.classList.toggle("is-active", on);
          if(!b.disabled) b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        panels.forEach(function(p){
          p.hidden = p.getAttribute("data-quarter") !== want;
        });
      });
    });
  });
}

/* The newest usable option in one picker, as [button, panel].

   "Usable" means not disabled and actually having a panel: an empty civic
   quarter is rendered disabled with no panel at all. Candidates are tried
   from the newest down, so a button without its panel falls through to the
   next rather than leaving the row blank. data-year is four digits and
   data-quarter one, so comparing them as text orders them correctly. */
function newestPick(root, btnSel, panelSel, attr){
  var btns = Array.prototype.filter.call(
    root.querySelectorAll(btnSel), function(b){ return !b.disabled; });
  btns.sort(function(a, b){
    var x = a.getAttribute(attr), y = b.getAttribute(attr);
    return x < y ? 1 : x > y ? -1 : 0;
  });
  for(var i = 0; i < btns.length; i++){
    var v = btns[i].getAttribute(attr);
    var panel = root.querySelector(panelSel + '[' + attr + '="' + v + '"]');
    if(panel) return [btns[i], panel];
  }
  return null;
}

function showPick(btn, panel){
  btn.classList.add("is-active");
  btn.setAttribute("aria-pressed", "true");
  panel.hidden = false;
}

/* Re-select the remembered quarter inside a year panel that has just opened,
   and fall back to the newest quarter the board actually has.

   An empty quarter is rendered disabled and gets no panel at all. Before
   2026-11-05 such a board simply left the row unselected, and so did the very
   first board opened in a session, when nothing had been remembered yet --
   Frank asked for the newest to open instead.

   The fallback deliberately does NOT write to civicPick, and does not go
   through .click(): a quarter nobody chose must not overwrite the one they
   did. A reader who picked Q2 still gets Q2 back on the next board that has
   it, even though the boards in between opened on their own newest. */
function restoreQuarter(yearPanel){
  var qp = yearPanel.querySelector(".quarterpick");
  if(!qp) return;
  clearPicks(qp, ".quarter-btn", ".quarter-panel");
  var btn = null, panel = null;
  if(civicPick.quarter !== null){
    btn   = qp.querySelector('.quarter-btn[data-quarter="' + civicPick.quarter + '"]');
    panel = qp.querySelector('.quarter-panel[data-quarter="' + civicPick.quarter + '"]');
  }
  if(!btn || btn.disabled || !panel){
    var best = newestPick(qp, ".quarter-btn", ".quarter-panel", "data-quarter");
    if(!best) return;
    btn = best[0]; panel = best[1];
  }
  showPick(btn, panel);
}

/* The same, one level up, for a board panel that has just opened. A board whose
   archive does not reach the remembered year now opens on its own newest year
   instead of on nothing, and so does the first board opened in a session. */
function restoreYear(boardPanel){
  var yp = boardPanel.querySelector(".yearpick");
  if(!yp) return;
  clearPicks(yp, ".year-btn", ".year-panel");
  clearPicks(yp, ".quarter-btn", ".quarter-panel");
  var btn = null, panel = null;
  if(civicPick.year !== null){
    btn   = yp.querySelector('.year-btn[data-year="' + civicPick.year + '"]');
    panel = yp.querySelector('.year-panel[data-year="' + civicPick.year + '"]');
  }
  if(!btn || btn.disabled || !panel){
    var best = newestPick(yp, ".year-btn", ".year-panel", "data-year");
    if(!best) return;
    btn = best[0]; panel = best[1];
  }
  showPick(btn, panel);
  restoreQuarter(panel);
}

function initBoardPicker(){
  document.querySelectorAll(".boardpick").forEach(function(pick){
    var btns   = pick.querySelectorAll(".board-btn");
    var panels = pick.querySelectorAll(".board-panel");
    btns.forEach(function(btn){
      btn.addEventListener("click", function(){
        var want = btn.getAttribute("data-board");
        var open = !btn.classList.contains("is-active");
        btns.forEach(function(b){
          var on = (b === btn) && open;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        panels.forEach(function(p){
          var mine = p.getAttribute("data-board") === want;
          p.hidden = !(mine && open);
          if(p.hidden){
            clearPicks(p, ".year-btn", ".year-panel");
            clearPicks(p, ".quarter-btn", ".quarter-panel");
          } else {
            restoreYear(p);
          }
        });
      });
    });
  });
}

/* ---------- sport picker (NSC archive) ----------
   The outer level of the Sports Connection archive: pick a sport, then a
   school year, then the games. Shaped like initBoardPicker but with none of
   its remembered state -- there is no third level here to restore, and the
   class is its own so the civic picker's logic stays out of it. */
/* ---------- Past TV Shows: sortable columns ----------
   Show Name sorts alphabetically, the two date columns chronologically. Every
   sortable cell carries data-sort: the name lowercased, and dates as ISO, whole
   or partial. ISO sorts correctly as plain text, so no date parsing is needed
   here. Clicking the column already sorted reverses it. A row with nothing in
   that column sits at the bottom either way -- flipping the direction should
   not push the blanks to the top. */
function initShowsTable(){
  document.querySelectorAll(".shows__table").forEach(function(table){
    var tbody = table.querySelector("tbody");
    if(!tbody) return;
    var heads = table.querySelectorAll("thead th[aria-sort]");
    heads.forEach(function(th){
      var btn = th.querySelector(".shows__sort");
      if(!btn) return;
      btn.addEventListener("click", function(){
        var idx = th.cellIndex;
        var dir = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
        heads.forEach(function(h){ h.setAttribute("aria-sort", "none"); });
        th.setAttribute("aria-sort", dir);
        // An empty data-sort means "no value here", so it has to win over the
        // cell's text -- otherwise a blank date sorts as its em dash and the
        // blanks climb to the top when the order is reversed.
        var cellKey = function(row, i){
          var c = row.cells[i];
          if(!c) return "";
          var v = c.hasAttribute("data-sort") ? c.getAttribute("data-sort") : c.textContent;
          return (v || "").trim().toLowerCase();
        };
        var key = function(row){ return cellKey(row, idx); };
        // A show and its episode panel are two rows but one unit: sort the
        // show rows and carry each panel along, or the panels end up under
        // whichever show happens to land above them.
        var pairs = Array.prototype.slice.call(tbody.rows)
          .filter(function(r){ return !r.classList.contains("shows__panel"); })
          .map(function(r){
            var n = r.nextElementSibling;
            return [r, (n && n.classList.contains("shows__panel")) ? n : null];
          });
        // Ties fall back to the show name, which is always column 0.
        var nameKey = function(row){ return cellKey(row, 0); };
        var rows = pairs.map(function(pr){ return pr[0]; });
        rows.sort(function(a, b){
          var x = key(a), y = key(b);
          if(!x) return y ? 1 : 0;      // blanks last, whichever way the column runs
          if(!y) return -1;
          if(x !== y) return (x < y ? -1 : 1) * (dir === "ascending" ? 1 : -1);
          // Equal in this column -- two shows of one genre, or one year. Order
          // them by name, A-Z either way, so the grouping stays readable.
          var nx = nameKey(a), ny = nameKey(b);
          return nx === ny ? 0 : (nx < ny ? -1 : 1);
        });
        var panelOf = new Map(pairs);
        rows.forEach(function(r){
          tbody.appendChild(r);
          var pnl = panelOf.get(r);
          if(pnl) tbody.appendChild(pnl);
        });
      });
    });

    // 2. clicking a show name opens its episodes, one show at a time
    tbody.querySelectorAll(".shows__name").forEach(function(btn){
      btn.addEventListener("click", function(){
        var row = btn.closest("tr");
        var panel = row.nextElementSibling;
        if(!panel || !panel.classList.contains("shows__panel")) return;
        var opening = panel.hidden;
        tbody.querySelectorAll(".shows__panel").forEach(function(p){
          if(!p.hidden){ clearPicks(p, ".year-btn", ".year-panel"); }
          p.hidden = true;
        });
        tbody.querySelectorAll(".shows__name").forEach(function(b){
          b.setAttribute("aria-expanded", "false");
        });
        if(opening){
          panel.hidden = false;
          btn.setAttribute("aria-expanded", "true");
        }
        clampDescriptions(panel);
      });
    });
  });
}

/* ---------- Instagram reels ----------
   Hiding an <iframe> does not stop it: a cross-origin embed keeps playing, and
   its sound keeps coming, from a card that has been collapsed or a panel that
   has been switched away from. Instagram exposes no player API we can call
   from here, so the frame is unloaded instead -- its src is parked on data-src
   and put back when it is next shown. Unloading also frees the player rather
   than leaving it running out of sight. */
function stopReels(root){
  (root || document).querySelectorAll("iframe.reel").forEach(function(f){
    var src = f.getAttribute("src");
    if(src){ f.dataset.src = src; f.removeAttribute("src"); }
  });
}
function startReels(root){
  (root || document).querySelectorAll("iframe.reel").forEach(function(f){
    // Only load one the reader can actually see. Any hidden ancestor counts --
    // its own card may be collapsed, or the school year or sport above it may
    // be shut. Restoring regardless would fetch the embed, and hand Instagram
    // a visit, for a reel nobody is looking at.
    if(f.closest("[hidden]")) return;
    if(!f.getAttribute("src") && f.dataset.src) f.setAttribute("src", f.dataset.src);
  });
}

/* ---------- choosing a sport opens its most recent school year ----------
   Asked for on 2026-11-03: click a sport and the latest season's games are
   already there, instead of a row of year buttons and nothing to read. This
   replaced an earlier version that only opened the year when a sport had
   exactly one of them, which covered Cross Country and Golf and left the
   other thirteen sports needing a second click.

   "Most recent" is the greatest data-year, not the last button in the DOM.
   The two are the same today -- sport_year_picker() emits sorted(...) -- but
   reading the attribute means a change to that loop's order cannot quietly
   break this. The labels are all "School Yr NN-NN", so a plain string compare
   is a date compare; it would need rethinking only at a century rollover.

   The button is clicked rather than switched on by hand, so the year picker's
   own handler does the work -- it unhides the panel, starts the reels and sets
   aria-pressed -- and the clamp listener wired to .year-btn re-measures the
   descriptions that have just become visible. Setting the classes here instead
   would leave two copies of that logic to keep in step, and the clamp would be
   the one to rot: a description has no measurable height until its panel is
   showing, so it has to be measured after the reveal, not before.

   Disabled buttons do not count. A greyed year is a year with nothing behind
   it, so a sport holding real years beside a greyed one should open a real
   one. Spring sports are the live example: Lacrosse, Softball and Baseball
   top out at 25-26 because their 26-27 seasons have not been played, and the
   newest year they actually have is the right one to open. */
function autoOpenNewestYear(sportPanel){
  var pick = sportPanel.querySelector(".yearpick");
  if(!pick) return;
  // Only this picker's own buttons, on the off chance a panel ever nests
  // another picker inside it -- the same guard initYearPicker uses.
  var btns = Array.prototype.filter.call(
    pick.querySelectorAll(".year-btn:not([disabled])"),
    function(b){ return b.closest(".yearpick") === pick; });
  if(!btns.length) return;
  // Any year already showing means this was called on a panel that never
  // closed. Clicking then would either toggle that year shut or throw away a
  // choice the reader had made, so leave it as it is.
  var live = btns.some(function(b){ return b.classList.contains("is-active"); });
  if(live) return;
  var newest = btns.reduce(function(a, b){
    return b.getAttribute("data-year") > a.getAttribute("data-year") ? b : a;
  });
  newest.click();
}

function initSportPicker(){
  document.querySelectorAll(".sportpick").forEach(function(pick){
    var btns   = pick.querySelectorAll(".sport-btn");
    var panels = pick.querySelectorAll(".sport-panel");
    btns.forEach(function(btn){
      btn.addEventListener("click", function(){
        var want = btn.getAttribute("data-sport");
        var open = !btn.classList.contains("is-active");
        btns.forEach(function(b){
          var on = (b === btn) && open;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        var opened = null;
        panels.forEach(function(p){
          var mine = p.getAttribute("data-sport") === want;
          p.hidden = !(mine && open);
          if(p.hidden){ clearPicks(p, ".year-btn", ".year-panel"); stopReels(p); }
          else { startReels(p); opened = p; }
        });
        // After the loop, not inside it: the year button's own handler starts
        // the reels in the panel it reveals, and startReels skips anything
        // still inside a [hidden] ancestor.
        if(opened) autoOpenNewestYear(opened);
      });
    });
  });
}

/* Photo lightbox for the Shorts Fest gallery.

   The overlay is built on the first click rather than shipped in every page,
   and the large file is only fetched at that point -- the grid carries the
   small copies, so opening the gallery costs a few hundred KB and a full-size
   photo is loaded only when somebody actually asks for one. */
/* ---------- overlay keyboard handling ----------
   Esc closes; Tab cycles between the overlay's own stops instead of walking
   the page behind it. The box is read through a function because both callers
   build theirs on first open, so it is null when this is wired. */
function wireOverlayKeys(getBox, closeBox){
  document.addEventListener("keydown", function(e){
    var box = getBox();
    if(!box || box.hidden) return;
    if(e.key === "Escape"){ closeBox(); return; }
    if(e.key !== "Tab") return;
    var stops = box.querySelectorAll("button, a[href]");
    if(!stops.length) return;
    var first = stops[0], last = stops[stops.length - 1], at = document.activeElement;
    if(e.shiftKey && (at === first || !box.contains(at))){
      e.preventDefault(); last.focus();
    } else if(!e.shiftKey && (at === last || !box.contains(at))){
      e.preventDefault(); first.focus();
    }
  });
}

function initPhotoLightbox(){
  var box = null, lastFocus = null;

  function build(){
    box = document.createElement("div");
    box.className = "lightbox";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "Photo viewer");
    box.innerHTML =
      '<button type="button" class="lightbox__close" aria-label="Close photo">\u00d7</button>' +
      '<figure class="lightbox__fig">' +
        '<img class="lightbox__img" alt="">' +
        '<figcaption class="lightbox__credit"></figcaption>' +
      '</figure>';
    // Anything that is not the photo itself, or a link in its caption, closes
    // the viewer. Testing for `e.target === box` was not enough: the <figure>
    // stretches to the full width of the overlay, so a portrait photo had
    // roughly 300px of figure down either side where a click hit the figure
    // and nothing happened. Asking what was clicked, rather than where, keeps
    // this right however the layout changes.
    box.addEventListener("click", function(e){
      if(e.target.closest(".lightbox__img, .lightbox__credit a")) return;
      closeBox();
    });
    document.body.appendChild(box);
  }

  function openBox(item){
    if(!box) build();
    lastFocus = document.activeElement;
    var thumb = item.querySelector("img");
    var img = box.querySelector(".lightbox__img");
    img.src = item.getAttribute("data-full");
    img.alt = thumb ? thumb.alt : "";
    // Reuse the credit already rendered above the grid rather than repeating
    // it in a data attribute: the two can then never disagree, and a year
    // published without a credit simply shows none here either.
    var panel  = item.closest(".year-panel");
    var credit = panel && panel.querySelector(".photo-credit");
    var slot   = box.querySelector(".lightbox__credit");
    slot.innerHTML = credit ? credit.innerHTML : "";
    slot.hidden = !credit;
    box.hidden = false;
    document.body.classList.add("is-lightboxed");
    box.querySelector(".lightbox__close").focus();
  }

  function closeBox(){
    if(!box || box.hidden) return;
    box.hidden = true;
    // Drop the source so the next open cannot flash the previous photo.
    box.querySelector(".lightbox__img").removeAttribute("src");
    document.body.classList.remove("is-lightboxed");
    if(lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }

  document.addEventListener("click", function(e){
    var item = e.target.closest(".photo-grid__item");
    if(!item) return;
    openBox(item);
  });

  // Two stops here -- the close button and the credit's prints link -- so Tab
  // cycles between them rather than pinning.
  wireOverlayKeys(function(){ return box; }, closeBox);
}

function initYearPicker(){
  document.querySelectorAll(".yearpick").forEach(function(pick){
    // Scoped to THIS picker's own buttons and panels. The NHA's "Browse by
    // Topic" buttons open panels that hold year pickers of their own, so a
    // plain querySelectorAll would hand the outer picker the inner one's
    // buttons and hide its panels on every click. Everywhere else nothing
    // nests and the filter changes nothing.
    var own    = function(el){ return el.closest(".yearpick") === pick; };
    var btns   = Array.prototype.filter.call(pick.querySelectorAll(".year-btn"), own);
    var panels = Array.prototype.filter.call(pick.querySelectorAll(".year-panel"), own);
    btns.forEach(function(btn){
      btn.addEventListener("click",function(){
        var yr = btn.getAttribute("data-year");
        var civic = !!pick.closest(".boardpick");
        // A picker marked --toggle shuts when its open year is clicked again.
        // Every other one keeps a year open once chosen, which is what the
        // lecture and meeting archives want: collapsing to nothing there would
        // just look like the page had lost its contents.
        //
        // A single BUTTON marked --toggle does the same on its own, inside a
        // picker that does not. The Luna Fest archive is one of these: it sits
        // among the New Moon years, which still hold open once chosen, but its
        // own button closes the table a second click (Frank, 2026-11-07).
        var shut = btn.classList.contains("is-active") &&
                   (pick.classList.contains("yearpick--toggle") ||
                    btn.classList.contains("year-btn--toggle"));
        if(civic) civicPick.year = yr;
        btns.forEach(function(b){
          var on = (b === btn) && !shut;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        panels.forEach(function(p){
          p.hidden = shut || p.getAttribute("data-year") !== yr;
          if(p.hidden){ clearPicks(p, ".quarter-btn", ".quarter-panel"); stopReels(p); }
          else { startReels(p); if(civic) restoreQuarter(p); }
        });
        // A picker marked --opens keeps its panels inside a collapsible: the
        // New Moon auction, where the year buttons sit above a shut "Learn
        // More". Without this a click would change what is behind the caret
        // and look like it had done nothing. Only this picker's own <details>
        // is opened, and only when a year is being shown.
        if(!shut && pick.classList.contains("yearpick--opens")){
          var det = pick.querySelector("details");
          if(det) det.open = true;
        }
      });
    });
  });
}

/* ---------- YouTube thumbnail fallback ----------
   Older uploads have no maxresdefault image. YouTube answers those requests
   with a 404 whose BODY is a valid 120x90 grey placeholder, so the browser
   decodes it and fires "load" — an onerror handler never runs. Detect the
   placeholder by its size and swap in hqdefault (480x360), which always
   exists. The swapped URL no longer matches, so this cannot loop. */
function initThumbFallback(){
  document.querySelectorAll(".watch-episode__thumb img").forEach(function(img){
    function check(){
      var m = img.src.match(/\/vi\/([A-Za-z0-9_-]{11})\/maxresdefault\.jpg/);
      if(m && img.naturalWidth && img.naturalWidth <= 120){
        img.src = "https://img.youtube.com/vi/" + m[1] + "/hqdefault.jpg";
      }
    }
    if(img.complete) check(); else img.addEventListener("load", check);
  });
}

/* ---------- long description toggles ----------
   A description running past ten lines collapses, with "Click to See More" on
   the eleventh. The ten-line limit lives in CSS (-webkit-line-clamp) so it
   reflows with the window; this only works out which descriptions actually
   overflow and wires up their control.

   A description inside a closed <details> or a hidden year panel measures zero
   height, so the test has to run again whenever one of those is revealed.
   Already-measured descriptions carry data-clamp so the work happens once. */
function clampDescriptions(root){
  (root || document).querySelectorAll(".watch-episode__desc").forEach(function(p){
    if(p.dataset.clamp || !p.textContent.trim()) return;
    if(!p.offsetParent && p.offsetHeight === 0) return;   // still hidden
    p.dataset.clamp = "done";
    p.classList.add("is-clamped");
    if(p.scrollHeight <= p.clientHeight + 1){             // fits in ten lines
      p.classList.remove("is-clamped");
      return;
    }
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "watch-episode__more";
    btn.textContent = "Click to See More";
    btn.setAttribute("aria-expanded", "false");
    btn.addEventListener("click", function(){
      var clamped = p.classList.toggle("is-clamped");
      btn.textContent = clamped ? "Click to See More" : "Click to See Less";
      btn.setAttribute("aria-expanded", clamped ? "false" : "true");
    });
    p.insertAdjacentElement("afterend", btn);
  });
}

/* ---------- agenda toggles ----------
   Some School Committee and Civic TV cards carry the meeting's posted agenda
   alongside the description. The button swaps one for the other in place and
   renames itself, so a reader can always get back to the description. Nothing
   is fetched: both blocks ship in the page, which keeps the control working
   offline and makes the agenda findable by an in-page search even before it is
   shown. */
function initAgendaToggles(){
  document.querySelectorAll(".watch-episode__agenda-btn").forEach(function(btn){
    if(btn.dataset.wired) return;
    btn.dataset.wired = "1";
    // the button sits beside the thumbnail, the description in the other
    // column, so scope the lookup to the whole card rather than either column
    var card    = btn.closest(".watch-episode");
    var desc    = card.querySelector(".watch-episode__desc");
    var agenda  = card.querySelector(".watch-episode__agenda");
    if(!agenda) return;
    var label   = btn.dataset.label || "Meeting Agenda";
    // A card marked data-title-moves drops its title below the buttons while
    // the panel is open, so a tall panel (an Instagram reel) starts level with
    // the thumbnail rather than under a heading. The title is moved rather
    // than duplicated: two copies would read twice to a screen reader, and
    // the columns are separate elements, so CSS order cannot do it.
    var moveTitle = card.hasAttribute("data-title-moves");
    var title   = card.querySelector(".watch-episode__title");
    var media   = card.querySelector(".watch-episode__media");
    var text    = card.querySelector(".watch-episode__text");
    btn.addEventListener("click", function(){
      var showing = agenda.hasAttribute("hidden");
      agenda.toggleAttribute("hidden", !showing);
      if(showing) startReels(agenda); else stopReels(agenda);
      if(moveTitle && title && media && text){
        if(showing) media.appendChild(title);
        else text.insertBefore(title, text.firstChild);
      }
      btn.setAttribute("aria-expanded", showing ? "true" : "false");
      // A card with an agenda but no description has nothing to swap out: the
      // agenda just opens and closes under the title, and the button says so.
      // With a description the button offers that back instead, at the end.
      if(!desc){ btn.textContent = showing ? "Hide " + label : label; return; }
      desc.toggleAttribute("hidden", showing);
      // the "Click to See More" control, if this description grew one
      var more = desc.nextElementSibling;
      if(more && more.classList.contains("watch-episode__more"))
        more.toggleAttribute("hidden", showing);
      btn.textContent = showing ? "Show Description" : label;
    });
  });
}

/* ---------- document overlay ----------
   A card can offer a whole document instead of a posted agenda -- a Town
   Meeting warrant, 84 articles of it for 2026 and 104 for 2025. An agenda
   swaps itself for the description in place, which is right for a page of
   bullet points and wrong for tens of thousands of words: everything below
   the card would be pushed off the screen. So this one opens over the page.

   The documents sit together in one hidden block near the foot of the page,
   not inside the cards, because a warrant belongs to every sitting of its
   Town Meeting and the button only names it. The one that is opened is moved
   into the overlay and handed back on close rather than copied, so the page
   holds one of it and an in-page search never finds the same sentence twice.
   Nothing is fetched: it ships with the page, the way the agendas do.

   The home page uses it too, for the press release behind the Rika Welsh
   card's second "click here" (2026-11-12). That trigger is a word inside a
   sentence rather than a button under a thumbnail, so it carries its own
   class; everything below it is the same. */
function initDocModal(){
  var box = null, home = null, body = null, lastFocus = null;

  function build(){
    box = document.createElement("div");
    box.className = "docmodal";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.innerHTML =
      '<div class="docmodal__panel">' +
        '<div class="docmodal__bar">' +
          '<h2 class="docmodal__title"></h2>' +
          '<button type="button" class="docmodal__close">Close</button>' +
        '</div>' +
        '<div class="docmodal__body"></div>' +
      '</div>';
    // Anything outside the panel closes it. Asking what was clicked rather
    // than where keeps this right however the panel is laid out.
    box.addEventListener("click", function(e){
      if(!e.target.closest(".docmodal__panel") || e.target.closest(".docmodal__close"))
        closeBox();
    });
    document.body.appendChild(box);
  }

  function openBox(btn){
    // The document is not in the card. One warrant belongs to every card for
    // its Town Meeting, so it ships once per page and the button names it.
    var doc = document.getElementById(btn.dataset.doc);
    if(!doc) return;
    if(!box) build();
    lastFocus = document.activeElement;
    home = doc.parentNode;
    body = box.querySelector(".docmodal__body");
    body.appendChild(doc);
    var title = btn.getAttribute("data-doc-title") || btn.textContent;
    box.querySelector(".docmodal__title").textContent = title;
    box.setAttribute("aria-label", title);
    box.hidden = false;
    document.body.classList.add("is-docopen");
    body.scrollTop = 0;
    box.querySelector(".docmodal__close").focus();
  }

  function closeBox(){
    if(!box || box.hidden) return;
    // Hand the document back before hiding, so the card is whole again even
    // if the overlay is never opened a second time.
    if(home && body && body.firstElementChild) home.appendChild(body.firstElementChild);
    box.hidden = true;
    document.body.classList.remove("is-docopen");
    if(lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }

  document.addEventListener("click", function(e){
    // Two triggers: the Warrant and Summary buttons under a Town Meeting
    // card, and the "click here" inside a news paragraph.
    var btn = e.target.closest(".watch-episode__doc-btn, .newsreel__doc");
    if(!btn) return;
    openBox(btn);
  });

  // The warrant carries no link, so for it this pins focus to the close
  // button. The press release ends on one, and wireOverlayKeys collects
  // `button, a[href]`, so there the tab cycles Close and that link.
  wireOverlayKeys(function(){ return box; }, closeBox);
}

/* ---------- Luna Fest film descriptions ----------
   The LUNAFEST table's fourth column is a button per film, and this is what
   it opens. It reuses .docmodal -- the warrant overlay's chrome, scrim, dark
   bar and Close button -- because it is the same gesture: a control in a row
   opening a panel of text over the page. Only the size differs, which is
   .docmodal--text in the stylesheet.

   Unlike initDocModal this moves nothing. The description is a paragraph of
   plain text on the button's own data attributes, so it is read straight out
   with textContent: no element to borrow and hand back, and nothing in the
   string can be markup. */
function initFilmModal(){
  var box = null, lastFocus = null;

  function build(){
    box = document.createElement("div");
    box.className = "docmodal docmodal--text";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.innerHTML =
      '<div class="docmodal__panel">' +
        '<div class="docmodal__bar">' +
          '<h2 class="docmodal__title"></h2>' +
          '<button type="button" class="docmodal__close">Close</button>' +
        '</div>' +
        '<div class="docmodal__body">' +
          '<p class="docmodal__meta"></p>' +
          '<p class="docmodal__text"></p>' +
        '</div>' +
      '</div>';
    box.addEventListener("click", function(e){
      if(!e.target.closest(".docmodal__panel") || e.target.closest(".docmodal__close"))
        closeBox();
    });
    document.body.appendChild(box);
  }

  function openBox(btn){
    if(!box) build();
    lastFocus = document.activeElement;
    var title = btn.getAttribute("data-film") || "";
    box.querySelector(".docmodal__title").textContent = title;
    box.setAttribute("aria-label", title);
    // Director and running time on one line. A film whose CSV cell read n/a
    // carries an empty data-duration, and filter() drops it rather than
    // leaving a stray separator or the words "n/a" on the page.
    var meta = [btn.getAttribute("data-director"), btn.getAttribute("data-duration")]
      .filter(function(v){ return v; }).join("  ·  ");
    var slot = box.querySelector(".docmodal__meta");
    slot.textContent = meta;
    slot.hidden = !meta;
    box.querySelector(".docmodal__text").textContent = btn.getAttribute("data-desc") || "";
    box.hidden = false;
    document.body.classList.add("is-docopen");
    box.querySelector(".docmodal__body").scrollTop = 0;
    box.querySelector(".docmodal__close").focus();
  }

  function closeBox(){
    if(!box || box.hidden) return;
    box.hidden = true;
    document.body.classList.remove("is-docopen");
    if(lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }

  document.addEventListener("click", function(e){
    var btn = e.target.closest(".lunafest-films__desc");
    if(!btn) return;
    openBox(btn);
  });

  // One stop, the close button: a description carries no links.
  wireOverlayKeys(function(){ return box; }, closeBox);
}

/* Live TV: two channels, one player frame.
   The frame is written out with the first channel's address already in it, so
   the page plays without this script -- all the buttons do is re-point it. A
   frame each would have opened both streams and kept pulling the one nobody
   is watching. Re-pointing src is also what stops the old stream: dropping the
   address is what ends the connection. */
function initLiveChannels(){
  const wrap = document.querySelector(".livetv");
  if(!wrap) return;
  const frame = wrap.querySelector(".livetv__frame iframe");
  const btns  = [...wrap.querySelectorAll(".live-btn")];
  if(!frame || !btns.length) return;
  btns.forEach(function(btn){
    btn.addEventListener("click", function(){
      if(btn.classList.contains("is-active")) return;
      btns.forEach(function(b){
        const on = b === btn;
        b.classList.toggle("is-active", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      });
      frame.title = btn.dataset.title || frame.title;
      frame.src   = btn.dataset.src;
    });
  });
}

document.addEventListener("DOMContentLoaded",()=>{
  const nav = document.getElementById("site-nav");
  if(nav) wireNav(nav);
  refreshFooterYear();
  initNewsreel();
  initReveal();
  initMoviePicker();
  initShowsTable();
  initSportPicker();
  initYearPicker();
  initPhotoLightbox();
  initBoardPicker();
  initQuarterPicker();
  initThumbFallback();
  initLiveChannels();
  clampDescriptions();
  initAgendaToggles();
  initDocModal();
  initFilmModal();
  // Measure again as sections and panels are revealed. The civic page nests
  // three pickers -- board, then year, then quarter -- and a card has no
  // measurable height until the innermost panel is showing, so every level
  // re-runs. These listeners are registered after the pickers' own, so the
  // panel is already visible by the time the measuring happens.
  document.querySelectorAll("details.dl-group").forEach(function(d){
    d.addEventListener("toggle", function(){ if(d.open) clampDescriptions(d); });
  });
  document.querySelectorAll(".sport-btn, .board-btn, .year-btn, .quarter-btn").forEach(function(b){
    b.addEventListener("click", function(){
      clampDescriptions(b.closest(".sportpick, .boardpick, .yearpick, .quarterpick"));
    });
  });
});
