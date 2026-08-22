import Lean
import VersoBlog
import LeaderboardSite.Data

set_option maxRecDepth 65536

open Lean Elab Term
open Verso Doc
open Verso.Genre.Blog
open Verso.Output Html

namespace LeaderboardSite.Pages.Preview

open LeaderboardSite.Data

private def textInline (text : String) : Inline Page := .text text
private def textHtml (text : String) : Html := Html.text true text

private def htmlBlob (html : Html) : Block Page :=
  .other (BlockExt.blob html) #[]

private def groupTabs : Html := {{
  <nav class="lifecycle-group-tabs" aria-label="Leaderboard groups">
    <a data-lifecycle-group-tab="formalization-evaluation"
       href="preview/formalization-evaluation/">{{textHtml "Formalization evaluation"}}</a>
    <a data-lifecycle-group-tab="software-verification"
       href="preview/software-verification/">{{textHtml "Software verification"}}</a>
    <a data-lifecycle-group-tab="open-conjectures"
       href="preview/open-conjectures/">{{textHtml "Open conjectures"}}</a>
    <a href="preview/recent/">{{textHtml "Recent solutions"}}</a>
  </nav>
}}

private def appShell (view : String) (identity : String := "") : Block Page :=
  htmlBlob {{
    <section class="lifecycle-app wrap" data-lifecycle-app="true" data-lifecycle-view={{view}}
             data-lifecycle-identity={{identity}} aria-labelledby="lifecycle-preview-title">
      <aside class="lifecycle-preview-banner">
        <span class="lifecycle-preview-badge">{{textHtml "Preview"}}</span>
        <div>
          <h1 id="lifecycle-preview-title">{{textHtml "LeanEval lifecycle-aware leaderboard"}}</h1>
          <p>{{textHtml "Local-only preview of the normalized materialized-domain contract."}}</p>
        </div>
        <a href=".">{{textHtml "Current leaderboard"}}</a>
      </aside>
      {{groupTabs}}
      <div class="lifecycle-app-status" role="status" aria-live="polite">
        {{textHtml "Loading leaderboard data…"}}
      </div>
      <div class="lifecycle-app-content"></div>
      <noscript>
        <p>{{textHtml "This preview uses client-side tables. Enable JavaScript to inspect it; the current leaderboard remains available at the site root."}}</p>
      </noscript>
    </section>
  }}

private def pagePart (title view : String) (identity : String := "") : Part Page :=
  .mk #[textInline title] title none #[appShell view identity] #[]

def _root_.LeaderboardSite.Pages.Preview : VersoDoc Page :=
  .mk (fun _ => pagePart "Lifecycle-aware leaderboard preview" "group" "formalization-evaluation") "{}"

def _root_.LeaderboardSite.Pages.PreviewFormalization : VersoDoc Page :=
  .mk (fun _ => pagePart "Formalization evaluation" "group" "formalization-evaluation") "{}"

def _root_.LeaderboardSite.Pages.PreviewSoftware : VersoDoc Page :=
  .mk (fun _ => pagePart "Software verification" "group" "software-verification") "{}"

def _root_.LeaderboardSite.Pages.PreviewConjectures : VersoDoc Page :=
  .mk (fun _ => pagePart "Open conjectures" "group" "open-conjectures") "{}"

def _root_.LeaderboardSite.Pages.PreviewRecent : VersoDoc Page :=
  .mk (fun _ => pagePart "Recent solutions" "recent") "{}"

def _root_.LeaderboardSite.Pages.PreviewProblems : VersoDoc Page :=
  .mk (fun _ => pagePart "Problem comparisons" "group" "formalization-evaluation") "{}"

private def previewProblemPart (title problemId : String) : Part Page :=
  pagePart title "problem" problemId

private def previewPageName (namePrefix problemId : String) : Lean.Name :=
  ((`LeaderboardSite.Pages.Preview).str namePrefix).str problemId

scoped syntax "preview_problem_pages%" : term

private def problemPageTerms : TermElabM Expr := do
  let problems ← validateProblems (← parseProblemsPayload)
  let mut terms : Array (TSyntax `term) := #[]
  for problem in problems do
    let pageName := previewPageName "Problem" problem.id
    let part ← `(previewProblemPart $(quote problem.title) $(quote problem.id))
    terms := terms.push (← `(Dir.page $(quote problem.id) $(quote pageName) $part #[]))
  let result : TSyntax `term ← `(#[$[$terms],*])
  let expected ← Lean.Elab.Term.elabTerm (← `(Array Dir)) none
  Lean.Elab.Term.elabTerm result (some expected)

elab_rules : term
  | `(preview_problem_pages%) => problemPageTerms

end LeaderboardSite.Pages.Preview
