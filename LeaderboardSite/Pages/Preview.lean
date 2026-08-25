import Lean
import VersoBlog
import LeaderboardSite.Data
import LeaderboardSite.Pages.ProblemDetail

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

private def headingBlock (text : String) : Block Page :=
  .other (BlockExt.blob {{ <h2>{{textHtml text}}</h2> }}) #[]

private def divBlock (classes : String) (contents : Array (Block Page)) : Block Page :=
  .other (BlockExt.htmlDiv classes) contents

private def groupTabs : Html := {{
  <nav class="lifecycle-group-tabs" aria-label="Leaderboard groups">
    <a data-lifecycle-group-tab="formalization-evaluation"
       href="formalization-evaluation/">{{textHtml "Formalization evaluation"}}</a>
    <a data-lifecycle-group-tab="software-verification"
       href="software-verification/">{{textHtml "Software verification"}}</a>
    <a data-lifecycle-group-tab="open-conjectures"
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
      {{<span class="lifecycle-preview-badge">{{textHtml "Preview"}}</span>}}
    else
      .seq #[]
  htmlBlob {{
    <section class="lifecycle-app wrap" data-lifecycle-app="true" data-lifecycle-view={{view}}
             data-lifecycle-identity={{identity}} aria-label={{heading}}>
      <aside class="lifecycle-preview-banner">
        {{badge}}
        <div>
          <p>{{textHtml description}}</p>
        </div>
        {{bannerLink}}
      </aside>
      {{groupTabs}}
      <div class="lifecycle-app-status" role="status" aria-live="polite">
        {{textHtml "Loading leaderboard data…"}}
      </div>
      <div class="lifecycle-app-content"></div>
      <noscript>
        <p>{{textHtml "This leaderboard uses client-side tables. Enable JavaScript to inspect it; the legacy leaderboard remains available from the link above."}}</p>
      </noscript>
    </section>
  }}

private def pagePart (preview : Bool) (title view : String) (identity : String := "") : Part Page :=
  .mk #[textInline title] title none #[appShell preview view identity] #[]

def _root_.LeaderboardSite.Pages.LifecycleFront : VersoDoc Page :=
  .mk (fun _ => pagePart false "LeanEval leaderboard" "group" "formalization-evaluation") "{}"

def _root_.LeaderboardSite.Pages.LifecycleFormalization : VersoDoc Page :=
  .mk (fun _ => pagePart false "Formalization evaluation" "group" "formalization-evaluation") "{}"

def _root_.LeaderboardSite.Pages.LifecycleSoftware : VersoDoc Page :=
  .mk (fun _ => pagePart false "Software verification" "group" "software-verification") "{}"

def _root_.LeaderboardSite.Pages.LifecycleConjectures : VersoDoc Page :=
  .mk (fun _ => pagePart false "Open conjectures" "group" "open-conjectures") "{}"

def _root_.LeaderboardSite.Pages.LifecycleRecent : VersoDoc Page :=
  .mk (fun _ => pagePart false "Recent solutions" "recent") "{}"

def _root_.LeaderboardSite.Pages.LifecycleProblems : VersoDoc Page :=
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

private def problemPart
    (preview : Bool)
    (title problemId : String)
    (notesText sourceText informalSolution : Option String)
    (anchors : Array (Block Page)) : Part Page :=
  let statement := divBlock "wrap prose lifecycle-problem-statement" <|
    #[headingBlock "Problem statement"] ++
      LeaderboardSite.Pages.ProblemDetail.problemStatementBlocks
        notesText sourceText informalSolution anchors
  .mk #[textInline title] title none #[appShell preview "problem" problemId, statement] #[]

private def previewPageName (namePrefix problemId : String) : Lean.Name :=
  ((`LeaderboardSite.Pages.Preview).str namePrefix).str problemId

scoped syntax "preview_problem_pages%" : term
scoped syntax "lifecycle_problem_pages%" : term

private def problemPageTerms (preview : Bool) (namePrefix : String) : TermElabM Expr := do
  let problems ← validateProblems (← parseProblemsPayload)
  let mut terms : Array (TSyntax `term) := #[]
  for problem in problems do
    let pageName := previewPageName namePrefix problem.id
    let anchors : TSyntaxArray `term := anchorBlockTerms problem
    let part ← `(problemPart
      $(quote preview)
      $(quote problem.title)
      $(quote problem.id)
      $(quote problem.notesText)
      $(quote problem.sourceText)
      $(quote problem.informalSolution)
      #[$anchors,*])
    terms := terms.push (← `(Dir.page $(quote problem.id) $(quote pageName) $part #[]))
  let result : TSyntax `term ← `(#[$[$terms],*])
  let expected ← Lean.Elab.Term.elabTerm (← `(Array Dir)) none
  Lean.Elab.Term.elabTerm result (some expected)

elab_rules : term
  | `(preview_problem_pages%) => problemPageTerms true "PreviewProblem"
  | `(lifecycle_problem_pages%) => problemPageTerms false "LifecycleProblem"

end LeaderboardSite.Pages.Preview
