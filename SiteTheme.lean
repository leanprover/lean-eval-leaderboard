import Verso.Doc.Html
import VersoBlog

open Verso.Genre Blog Theme Template
open Verso.Genre.Blog.Site.Syntax
open Verso.Output Html

def theme (name : String) (siteName : String) : Theme := {
  Theme.default with
  primaryTemplate := do
    let title ← param (α := String) "title"
    return {{
      <html lang="en">
        <head>
          <meta charset="UTF-8"/>
          <meta name="viewport" content="width=device-width, initial-scale=1"/>
          <title>{{ title }} s!" | {siteName}"</title>
          <link rel="stylesheet" href="static/style.css"/>
          <script defer="true" src="static/app.js"></script>
          {{← builtinHeader }}
        </head>
        <body>
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
              <div class="wrap prose">
                {{ ← param "content" }}
              </div>
              <div id="leaderboard-root" class="leaderboard-root"></div>
            </main>
            <footer class="footer">
              <div class="wrap footer-inner">
                <span>"Public results for lean-eval."</span>
                <a href="https://github.com/kim-em/lean-eval">"Benchmark repo"</a>
                <a href="https://github.com/kim-em/lean-eval-leaderboard">"Results repo"</a>
              </div>
            </footer>
          </div>
        </body>
      </html>
    }}
}
