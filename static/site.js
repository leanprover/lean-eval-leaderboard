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
