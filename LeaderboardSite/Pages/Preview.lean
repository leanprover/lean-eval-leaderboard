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
  <nav class="v2-group-tabs" aria-label="Leaderboard groups">
    <a data-v2-group-tab="formalization-evaluation"
       href="formalization-evaluation/">{{textHtml "Formalization evaluation"}}</a>
    <a data-v2-group-tab="software-verification"
       href="software-verification/">{{textHtml "Software verification"}}</a>
    <a data-v2-group-tab="open-conjectures"
       href="open-conjectures/">{{textHtml "Open conjectures"}}</a>
    <a href="recent/">{{textHtml "Recent solutions"}}</a>
  </nav>
}}

private def appShell (preview : Bool) (view : String) (identity : String := "") : Block Page :=
  let heading := if preview then "LeanEval lifecycle-aware leaderboard preview" else "LeanEval leaderboard"
  let description :=
    if preview then
      "Preview of the lifecycle-aware leaderboard now available at the stable site routes."
    else
      "Lifecycle-aware standings, problem histories, recent solutions, and replay status."
  let bannerLink :=
    if preview then
      {{<a href=".">{{textHtml "Current leaderboard"}}</a>}}
    else
      {{<a href="legacy/">{{textHtml "Legacy leaderboard"}}</a>}}
  let badge :=
    if preview then
      {{<span class="v2-preview-badge">{{textHtml "Preview"}}</span>}}
    else
      .seq #[]
  htmlBlob {{
    <section class="v2-app wrap" data-v2-app="true" data-v2-view={{view}}
             data-v2-identity={{identity}} aria-label={{heading}}>
      <aside class="v2-preview-banner">
        {{badge}}
        <div>
          <p>{{textHtml description}}</p>
        </div>
        {{bannerLink}}
      </aside>
      {{groupTabs}}
      <div class="v2-app-status" role="status" aria-live="polite">
        {{textHtml "Loading leaderboard data…"}}
      </div>
      <div class="v2-app-content"></div>
      <noscript>
        <p>{{textHtml "This leaderboard uses client-side tables. Enable JavaScript to inspect it; the legacy leaderboard remains available from the link above."}}</p>
      </noscript>
    </section>
  }}

private def pagePart (preview : Bool) (title view : String) (identity : String := "") : Part Page :=
  .mk #[textInline title] title none #[appShell preview view identity] #[]

def _root_.LeaderboardSite.Pages.V2Front : VersoDoc Page :=
  .mk (fun _ => pagePart false "LeanEval leaderboard" "group" "formalization-evaluation") "{}"

def _root_.LeaderboardSite.Pages.V2Formalization : VersoDoc Page :=
  .mk (fun _ => pagePart false "Formalization evaluation" "group" "formalization-evaluation") "{}"

def _root_.LeaderboardSite.Pages.V2Software : VersoDoc Page :=
  .mk (fun _ => pagePart false "Software verification" "group" "software-verification") "{}"

def _root_.LeaderboardSite.Pages.V2Conjectures : VersoDoc Page :=
  .mk (fun _ => pagePart false "Open conjectures" "group" "open-conjectures") "{}"

def _root_.LeaderboardSite.Pages.V2Recent : VersoDoc Page :=
  .mk (fun _ => pagePart false "Recent solutions" "recent") "{}"

def _root_.LeaderboardSite.Pages.V2Problems : VersoDoc Page :=
  .mk (fun _ => pagePart false "Problems" "group" "formalization-evaluation") "{}"

def _root_.LeaderboardSite.Pages.Preview : VersoDoc Page :=
  .mk (fun _ => pagePart true "Lifecycle-aware leaderboard preview" "group" "formalization-evaluation") "{}"

def _root_.LeaderboardSite.Pages.PreviewFormalization : VersoDoc Page :=
  .mk (fun _ => pagePart true "Formalization evaluation" "group" "formalization-evaluation") "{}"

def _root_.LeaderboardSite.Pages.PreviewSoftware : VersoDoc Page :=
  .mk (fun _ => pagePart true "Software verification" "group" "software-verification") "{}"

def _root_.LeaderboardSite.Pages.PreviewConjectures : VersoDoc Page :=
  .mk (fun _ => pagePart true "Open conjectures" "group" "open-conjectures") "{}"

def _root_.LeaderboardSite.Pages.PreviewRecent : VersoDoc Page :=
  .mk (fun _ => pagePart true "Recent solutions" "recent") "{}"

def _root_.LeaderboardSite.Pages.PreviewProblems : VersoDoc Page :=
  .mk (fun _ => pagePart true "Problem comparisons" "group" "formalization-evaluation") "{}"

private def problemPart (preview : Bool) (title problemId : String) : Part Page :=
  pagePart preview title "problem" problemId

private def previewPageName (namePrefix problemId : String) : Lean.Name :=
  ((`LeaderboardSite.Pages.Preview).str namePrefix).str problemId

scoped syntax "preview_problem_pages%" : term
scoped syntax "v2_problem_pages%" : term

private def problemPageTerms (preview : Bool) (namePrefix : String) : TermElabM Expr := do
  let problems ← validateProblems (← parseProblemsPayload)
  let mut terms : Array (TSyntax `term) := #[]
  for problem in problems do
    let pageName := previewPageName namePrefix problem.id
    let part ← `(problemPart $(quote preview) $(quote problem.title) $(quote problem.id))
    terms := terms.push (← `(Dir.page $(quote problem.id) $(quote pageName) $part #[]))
  let result : TSyntax `term ← `(#[$[$terms],*])
  let expected ← Lean.Elab.Term.elabTerm (← `(Array Dir)) none
  Lean.Elab.Term.elabTerm result (some expected)

elab_rules : term
  | `(preview_problem_pages%) => problemPageTerms true "PreviewProblem"
  | `(v2_problem_pages%) => problemPageTerms false "V2Problem"

end LeaderboardSite.Pages.Preview
