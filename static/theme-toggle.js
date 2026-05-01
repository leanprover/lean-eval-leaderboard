(() => {
  const STORAGE_KEY = "leaderboard-theme";

  function isDark() {
    return document.documentElement.classList.contains("dark-theme");
  }

  function syncToggleButtons() {
    const dark = isDark();
    document.querySelectorAll(".theme-toggle").forEach((btn) => {
      btn.setAttribute("aria-pressed", String(dark));
    });
  }

  function applyTheme(mode) {
    const root = document.documentElement;
    if (mode === "dark") root.classList.add("dark-theme");
    else root.classList.remove("dark-theme");
    syncToggleButtons();
    document.dispatchEvent(new CustomEvent("themechange", { detail: { mode } }));
  }

  function readPreference() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "dark" || saved === "light") return saved;
    } catch (e) {}
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function persist(mode) {
    try { localStorage.setItem(STORAGE_KEY, mode); } catch (e) {}
  }

  function wireToggleButtons() {
    document.querySelectorAll(".theme-toggle").forEach((btn) => {
      btn.addEventListener("click", () => {
        const next = isDark() ? "light" : "dark";
        applyTheme(next);
        persist(next);
      });
    });
    syncToggleButtons();
  }

  // Apply the saved/preferred theme synchronously so the dark-theme class is
  // set before first paint. Buttons may not exist yet — `wireToggleButtons`
  // re-syncs after DOMContentLoaded.
  applyTheme(readPreference());

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireToggleButtons);
  } else {
    wireToggleButtons();
  }

  // Follow the OS theme as long as the user has not made an explicit choice.
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  media.addEventListener("change", (e) => {
    let saved = null;
    try { saved = localStorage.getItem(STORAGE_KEY); } catch (err) {}
    if (saved !== "dark" && saved !== "light") {
      applyTheme(e.matches ? "dark" : "light");
    }
  });
})();
