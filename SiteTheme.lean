import Verso.Doc.Html
import VersoBlog

open Verso.Genre Blog Theme Template
open Verso.Genre.Blog.Site.Syntax
open Verso.Output Html

def theme (name : String) (siteName : String) : Theme := {
  Theme.default with
  primaryTemplate := do
    let title ← param (α := String) "title"
    let path := (← read).path
    let isHome := path.isEmpty
    let pageClass := if isHome then "home-page" else "inner-page"
    -- Verso emits a `<base href>` tag pointing at the site root, so all
    -- relative URLs in the page resolve against that base. Asset and nav
    -- hrefs below use plain relative paths (no leading `/` or `../`).
    -- The home page emits its own wrappers (a full-width
    -- `.leaderboard-root` for the hero/leaderboard plus a
    -- `.wrap.prose.page-copy` for the intro prose), so the theme just
    -- renders the content directly. Inner pages get the standard prose
    -- container from the theme.
    let pageCopy ←
      if isHome then
        pure (← param "content")
      else
        pure {{
          <div class="wrap prose page-copy">
            {{ ← param "content" }}
          </div>
        }}
    let githubIcon : Html := {{
      <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
      </svg>
    }}
    return {{
      <html lang="en">
        <head>
          <meta charset="UTF-8"/>
          <meta name="viewport" content="width=device-width, initial-scale=1"/>
          <title>{{ title }} s!" | {siteName}"</title>
          <link rel="preconnect" href="https://fonts.googleapis.com"/>
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous"/>
          <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=Oranienbaum&family=Fira+Code:wght@400;500&display=swap"/>
          {{← builtinHeader }}
          <link rel="icon" type="image/svg+xml" href="static/favicon.svg"/>
          <link rel="stylesheet" href="static/style.css"/>
          <script src="static/theme-toggle.js"></script>
          <script defer="true" src="static/background.js"></script>
          <script defer="true" src="static/site.js"></script>
        </head>
        <body class={{pageClass}}>
          <div class="site-shell">
            <header class="topbar">
              <div class="wrap topbar-inner">
                <a class="wordmark" href=".">
                  <span class="wordmark-mark">"⊢"</span>
                  <span class="wordmark-text">"lean-eval"</span>
                </a>
                <div class="topbar-actions">
                  <nav class="top">
                    <ol>
                      <li><a href="problems/">"Problems"</a></li>
                      <li><a href="submit/">"Submit"</a></li>
                    </ol>
                  </nav>
                  <a class="topbar-github" href="https://github.com/leanprover/lean-eval-leaderboard"
                     aria-label="View source on GitHub"
                     target="_blank" rel="noopener">{{githubIcon}}</a>
                  <button class="theme-toggle" type="button" aria-label="Toggle dark mode">
                    <span class="icon-sun" aria-hidden="true">"☀"</span>
                    <span class="icon-moon" aria-hidden="true">"☾"</span>
                  </button>
                </div>
              </div>
            </header>
            <main class="page" role="main">
              {{pageCopy}}
            </main>
            <footer class="footer">
              <div class="wrap footer-inner">
                <div class="footer-row footer-row--repos">
                  <span>"Public results for lean-eval."</span>
                  <a href="https://github.com/leanprover/lean-eval">{{githubIcon}}<span>"Benchmark repo"</span></a>
                  <a href="https://github.com/leanprover/lean-eval-leaderboard">{{githubIcon}}<span>"Results repo"</span></a>
                </div>
                <div class="footer-row footer-row--community">
                  <span>"Community"</span>
                  <a href="https://lean-lang.org/">"Lean"</a>
                  <a href="https://mathlib-initiative.org/">"Mathlib Initiative"</a>
                  <a href="https://leanprover.zulipchat.com/">"Zulip"</a>
                </div>
              </div>
            </footer>
          </div>
        </body>
      </html>
    }}
}
