// Mark the current page in the top nav with aria-current="page".
// Walks nav.top a[href] and matches normalized hrefs against the
// current pathname.
(function markActiveNav() {
  function run() {
    var here = location.pathname.replace(/\/+$/, "") || "/";
    document.querySelectorAll("nav.top a[href]").forEach(function (a) {
      var u;
      try { u = new URL(a.getAttribute("href"), location.href); }
      catch (_) { return; }
      var p = u.pathname.replace(/\/+$/, "") || "/";
      if (p === here) { a.setAttribute("aria-current", "page"); }
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();

// Esc dismisses an open theorem-card popover by blurring the trigger
// (the card hides via CSS :focus-within once focus is released).
document.addEventListener("keydown", function (e) {
  if (e.key !== "Escape") return;
  var el = document.activeElement;
  if (el && el.classList && el.classList.contains("problem-id-trigger")) {
    el.blur();
  }
});

// Live filter for the Problems index. Hides any per-problem section
// whose precomputed haystack doesn't include the query
// (case-insensitive). The page identifies itself via explicit
// `[data-problem-section]` and `[data-problem-group]` markers emitted
// from `LeaderboardSite/Pages/Problems.lean` rather than by guessing
// at heading levels or section nesting.
(function setupProblemsFilter() {
  function run() {
    var box = document.querySelector(".problems-filter[data-problems-filter]");
    if (!box) return;
    var input = box.querySelector(".problems-filter-input");
    var counter = box.querySelector(".problems-filter-count");
    if (!input) return;

    // Each problem `<section>` contains a hidden marker span carrying
    // the precomputed lower-cased haystack as `data-filter-text`.
    var markers = Array.prototype.slice.call(
      document.querySelectorAll("[data-problem-section]")
    );
    var entries = markers.map(function (m) {
      var sec = m.closest("section");
      return sec
        ? { el: sec, text: (m.getAttribute("data-filter-text") || "").toLowerCase() }
        : null;
    }).filter(Boolean);
    var groups = Array.prototype.slice.call(
      document.querySelectorAll("[data-problem-group]")
    ).map(function (g) { return g.closest("section"); }).filter(Boolean);

    function update() {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      for (var i = 0; i < entries.length; i++) {
        var match = !q || entries[i].text.indexOf(q) !== -1;
        entries[i].el.hidden = !match;
        if (match) shown++;
      }
      if (counter) {
        counter.textContent = q ? shown + " of " + entries.length + " match" : "";
      }
      // Group section "all hidden" hint.
      for (var j = 0; j < groups.length; j++) {
        var any = false;
        groups[j].querySelectorAll("[data-problem-section]").forEach(function (m) {
          var sec = m.closest("section");
          if (sec && !sec.hidden) any = true;
        });
        groups[j].classList.toggle("group-empty", !any && !!q);
      }
    }

    input.addEventListener("input", update);

    // Fragment navigation: if a #problem-id was used to arrive here and
    // a filter query later hides the target, unhide it and focus its
    // heading so deep links keep working. Verso puts the id on the
    // heading element, not the surrounding <section>, so walk up.
    function revealFragmentTarget() {
      if (!location.hash) return;
      var target = document.getElementById(location.hash.slice(1));
      if (!target) return;
      var sec = target.closest("section");
      if (sec) sec.hidden = false;
      var heading = (target.tagName && /^H[1-6]$/.test(target.tagName))
        ? target
        : (sec ? sec.querySelector(":scope > h2, :scope > h3") : null);
      if (heading) {
        if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
        heading.focus({ preventScroll: true });
        heading.scrollIntoView();
      }
    }
    revealFragmentTarget();
    window.addEventListener("hashchange", revealFragmentTarget);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
