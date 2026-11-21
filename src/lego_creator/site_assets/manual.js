// Brick Steps: one card per screen, buttons + swipe + arrow keys, resume via hash, offline via service worker.
(function () {
  "use strict";

  function registerServiceWorker(images) {
    var sw = document.body.getAttribute("data-sw");
    if (!sw || !("serviceWorker" in navigator)) return;
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

  function indexOf(id) {
    for (var k = 0; k < cards.length; k++) if (cards[k].id === id) return k;
    return -1;
  }

  function show(k, dir) {
    k = Math.max(0, Math.min(cards.length - 1, k));
    cards[current].classList.remove("on");
    current = k;
    var card = cards[current];
    card.style.setProperty("--dir", (dir || 0) * 24 + "px");
    card.classList.add("on");
    prev.disabled = current === 0;
    next.textContent = current === 0 ? "시작하기 ›" : current === cards.length - 1 ? "처음으로" : "다음 ›";
    if (history.replaceState) history.replaceState(null, "", "#" + card.id);
    window.scrollTo(0, 0);
    try { localStorage.setItem(key, card.id); } catch (e) {}
    document.dispatchEvent(new CustomEvent("brick-steps:show", { detail: { card: card, dir: dir || 0 } }));
  }

  function forward() { show(current === cards.length - 1 ? 0 : current + 1, 1); }
  function back() { show(current - 1, -1); }

  deck.classList.add("js");
  pager.hidden = false;
  prev.addEventListener("click", back);
  next.addEventListener("click", forward);
  document.addEventListener("keydown", function (e) {
    if (e.key === "ArrowRight") forward();
    if (e.key === "ArrowLeft") back();
  });

  var startX = null;
  deck.addEventListener("touchstart", function (e) {
    // A drag on the 3D view turns the model; it must not also turn the page.
    startX = e.target.closest(".stage3d") ? null : e.touches[0].clientX;
  }, { passive: true });
  deck.addEventListener("touchend", function (e) {
    if (startX === null) return;
    var dx = e.changedTouches[0].clientX - startX;
    startX = null;
    if (Math.abs(dx) > 60) (dx < 0 ? forward : back)();
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
