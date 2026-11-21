// Brick Steps: one card per screen, buttons + arrow keys, section bar + contents jumps (no swipe: it fired by mistake),
// resume via hash, offline via service worker.
(function () {
  "use strict";

  function registerServiceWorker(images) {
    var sw = document.body.getAttribute("data-sw");
    if (!sw || !("serviceWorker" in navigator)) return;
    // A new deploy's worker takes over open pages; reload once so the page matches the new files.
    // Not on the first install, when there was no worker before.
    if (navigator.serviceWorker.controller) {
      var reloaded = false;
      navigator.serviceWorker.addEventListener("controllerchange", function () {
        if (reloaded) return;
        reloaded = true;
        location.reload();
      });
    }
    var scope = sw.slice(0, sw.lastIndexOf("/") + 1) || "./";
    navigator.serviceWorker.register(sw, { scope: scope }).then(function () {
      return navigator.serviceWorker.ready;
    }).then(function (reg) {
      // Cache every picture of this manual now, so it still works at the build table without Wi-Fi.
      if (reg.active && images.length) reg.active.postMessage({ type: "cache", urls: images });
    }).catch(function () {});
  }

  // The hidden lab of drafts: five taps on the gallery logo within two seconds.
  var lab = document.body.getAttribute("data-lab");
  var brand = document.querySelector(".site-head .brand");
  if (lab && brand) {
    var taps = [];
    brand.addEventListener("click", function () {
      var now = Date.now();
      taps = taps.filter(function (t) { return now - t < 2000; });
      taps.push(now);
      if (taps.length >= 5) location.href = lab;
    });
  }

  // Adventure map: stops show what this device has built, and open a sheet to start or clear a build.
  var map = document.querySelector(".map");
  if (map) {
    var stops = Array.prototype.slice.call(map.querySelectorAll("a.stop"));
    var sheet = document.querySelector(".sheet");
    var clear = sheet.querySelector(".clear");
    var go = sheet.querySelector(".go");
    var openStop = null, armed = false;
    var pathOf = function (a) { return new URL(a.getAttribute("href"), location.href).pathname; };
    var isBuilt = function (a) {
      try { return localStorage.getItem("brick-steps:built:" + pathOf(a)) === "1"; } catch (e) { return false; }
    };
    var paint = function () {
      var next = null;
      stops.forEach(function (a) {
        var built = isBuilt(a);
        a.classList.toggle("built", built);
        a.classList.remove("next");
        if (!built && !next) next = a;
      });
      if (next) next.classList.add("next");
    };
    var close = function () {
      sheet.classList.remove("on");
      setTimeout(function () { if (!sheet.classList.contains("on")) sheet.hidden = true; }, 220);
    };
    stops.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        openStop = a;
        var built = isBuilt(a);
        sheet.querySelector(".sheet-img").src = a.getAttribute("data-img");
        sheet.querySelector(".name").textContent = a.getAttribute("data-name");
        sheet.querySelector(".story").textContent = a.getAttribute("data-story");
        sheet.querySelector(".meta").textContent = a.getAttribute("data-meta");
        var from = sheet.querySelector(".from");
        from.textContent = a.getAttribute("data-from") || "";
        from.hidden = !from.textContent;
        go.href = a.getAttribute("href") + (built ? "#cover" : "");
        go.textContent = built ? "다시 만들기 ›" : "만들기 시작 ›";
        clear.hidden = !built;
        clear.textContent = "‘다 만들었어요’ 표시 지우기";
        armed = false;
        sheet.hidden = false;
        requestAnimationFrame(function () { requestAnimationFrame(function () { sheet.classList.add("on"); }); });
      });
    });
    sheet.querySelector(".x").addEventListener("click", close);
    // A tap anywhere off the sheet closes it; a tap on another stop opens that one instead.
    document.addEventListener("click", function (e) {
      if (sheet.hidden || sheet.contains(e.target) || e.target.closest("a.stop")) return;
      close();
    });
    clear.addEventListener("click", function () {
      if (!armed) { armed = true; clear.textContent = "한 번 더 누르면 ‘다 만들었어요’ 표시만 지워요"; return; }
      var path = pathOf(openStop);
      try {
        localStorage.removeItem("brick-steps:built:" + path);
        localStorage.removeItem("brick-steps:" + path);
        localStorage.removeItem("brick-steps:" + path + ":max");
      } catch (e) {}
      paint();
      close();
    });
    paint();
  }

  var deck = document.getElementById("deck");
  var pager = document.querySelector(".pager");
  if (!deck || !pager) {
    registerServiceWorker([]);
    return;
  }

  var cards = Array.prototype.slice.call(deck.querySelectorAll(".card"));
  var prev = pager.querySelector(".prev");
  var next = pager.querySelector(".next");
  var key = "brick-steps:" + location.pathname;
  var current = 0;
  var chapters = document.querySelector(".chapters");
  var contents = document.querySelector(".contents");
  var builds = cards.filter(function (c) { return c.getAttribute("data-chapter") === "build"; });
  var furthest = 0;
  try { furthest = Math.max(0, cards.indexOf(document.getElementById(localStorage.getItem(key + ":max")))); } catch (e) {}

  function indexOf(id) {
    for (var k = 0; k < cards.length; k++) if (cards[k].id === id) return k;
    return -1;
  }

  function mark() {
    var card = cards[current];
    var chapter = card.getAttribute("data-chapter");
    if (chapters) {
      var built = 0;
      for (var b = 0; b < builds.length; b++) if (cards.indexOf(builds[b]) <= current) built++;
      chapters.querySelectorAll(".chapter").forEach(function (a) {
        var c = a.getAttribute("data-chapter");
        if (c === chapter) a.setAttribute("aria-current", "step"); else a.removeAttribute("aria-current");
        if (c === "build") a.style.setProperty("--fill", (builds.length ? 100 * built / builds.length : 0) + "%");
      });
    }
    if (contents) {
      contents.querySelectorAll(".tile").forEach(function (a) {
        var k = indexOf(a.getAttribute("href").slice(1));
        a.classList.toggle("seen", k > 0 && k <= furthest && a.classList.contains("step"));
        if (k === current) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
      });
    }
  }

  function show(k, dir) {
    k = Math.max(0, Math.min(cards.length - 1, k));
    cards[current].classList.remove("on");
    current = k;
    var card = cards[current];
    card.style.setProperty("--dir", (dir || 0) * 24 + "px");
    // A jump from the section bar or contents swaps the card at once, without the slide.
    card.classList.toggle("jump", !dir);
    card.classList.add("on");
    prev.disabled = current === 0;
    next.textContent = current === 0 ? "시작하기 ›" : current === cards.length - 1 ? "처음으로" : "다음 ›";
    if (history.replaceState) history.replaceState(null, "", "#" + card.id);
    window.scrollTo(0, 0);
    furthest = Math.max(furthest, current);
    if (card.id === "done") {
      try { localStorage.setItem("brick-steps:built:" + location.pathname, "1"); } catch (e) {}
    }
    try { localStorage.setItem(key, card.id); localStorage.setItem(key + ":max", cards[furthest].id); } catch (e) {}
    mark();
    document.dispatchEvent(new CustomEvent("brick-steps:show", { detail: { card: card, dir: dir || 0 } }));
  }

  function forward() { show(current === cards.length - 1 ? 0 : current + 1, 1); }
  function back() { show(current - 1, -1); }

  deck.classList.add("js");
  // Keep the screen on while a child builds: the iPad sits on the table between taps.
  // Wake locks end when the page is hidden, so take it again on return. Unsupported browsers just skip this.
  function stayAwake() {
    if (document.visibilityState !== "visible" || !navigator.wakeLock) return;
    navigator.wakeLock.request("screen").catch(function () {});
  }
  document.addEventListener("visibilitychange", stayAwake);
  stayAwake();
  pager.hidden = false;
  prev.addEventListener("click", back);
  next.addEventListener("click", forward);
  document.addEventListener("keydown", function (e) {
    if (e.key === "ArrowRight") forward();
    if (e.key === "ArrowLeft") back();
  });

  function jump(e) {
    var a = e.target.closest("a[href^='#']");
    if (!a) return;
    var k = indexOf(a.getAttribute("href").slice(1));
    if (k < 0) return;
    e.preventDefault();
    if (contents && contents.open) contents.close();
    show(k, 0);
  }
  if (chapters) {
    chapters.hidden = false;
    chapters.addEventListener("click", jump);
    var toc = chapters.querySelector(".toc");
    if (contents && contents.showModal) {
      toc.addEventListener("click", function () { mark(); contents.showModal(); });
      contents.addEventListener("click", jump);
      contents.querySelector(".close").addEventListener("click", function () { contents.close(); });
    } else {
      toc.hidden = true;
    }
  }
  window.addEventListener("hashchange", function () {
    var k = indexOf(location.hash.slice(1));
    if (k >= 0 && k !== current) show(k, 0);
  });

  var saved = null;
  try { saved = localStorage.getItem(key); } catch (e) {}
  var start = indexOf(location.hash.slice(1));
  if (start < 0 && saved) start = indexOf(saved);
  cards[0].classList.add("on");
  show(start < 0 ? 0 : start, 0);

  var images = Array.prototype.map.call(deck.querySelectorAll("img"), function (img) { return img.src; });
  var model3d = document.body.getAttribute("data-model3d");
  if (model3d) images.push(new URL(model3d, location.href).href);
  registerServiceWorker(images);
})();
