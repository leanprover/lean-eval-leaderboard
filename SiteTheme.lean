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
    let appRoot ←
      if isHome then
        pure {{
          <div id="app-root" class="leaderboard-root" data-page={{title}}></div>
        }}
      else
        pure Html.empty
    let pageCopy ←
      if isHome then
        pure Html.empty
      else
        pure {{
          <div class="wrap prose page-copy">
            {{ ← param "content" }}
          </div>
        }}
    return {{
      <html lang="en">
        <head>
          <meta charset="UTF-8"/>
          <meta name="viewport" content="width=device-width, initial-scale=1"/>
          <title>{{ title }} s!" | {siteName}"</title>
          {{← builtinHeader }}
          <link rel="stylesheet" href="static/style.css"/>
          <script defer="true" src="static/app.js"></script>
          <script defer="true" src="static/background.js"></script>
        </head>
        <body class={{pageClass}}>
          <div class="site-shell">
            <header class="topbar">
              <div class="wrap topbar-inner">
                <a class="wordmark" href=".">
                  <span class="wordmark-mark">"⊢"</span>
                  <span class="wordmark-text">"Lean AI formalization leaderboard"</span>
                </a>
                {{ ← topNav (homeLink := name) }}
              </div>
            </header>
            <main class="page" role="main">
              {{pageCopy}}
              {{appRoot}}
            </main>
            <footer class="footer">
              <div class="wrap footer-inner">
                <span>"Public results for lean-eval."</span>
                <a href="https://github.com/leanprover/lean-eval">"Benchmark repo"</a>
                <a href="https://github.com/leanprover/lean-eval-leaderboard">"Results repo"</a>
              </div>
            </footer>
          </div>
        </body>
      </html>
    }}
}
