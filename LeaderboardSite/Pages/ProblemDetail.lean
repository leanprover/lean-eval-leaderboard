import VersoBlog
import LeaderboardSite.Data
import LeaderboardSite.AnchorRegistry
import LeaderboardSite.Copy

open Lean
open Lean.Elab Term
open Verso Doc Doc.Elab
open Verso.Genre.Blog
open Verso.Code.External
open Verso.Output Html

set_option verso.exampleProject "benchmark-snapshot"
set_option maxHeartbeats 1000000

namespace LeaderboardSite.Pages.ProblemDetail

open LeaderboardSite.Data
open LeaderboardSite.Copy

private def textInline (text : String) : Inline Page :=
  .text text

private def codeInline (text : String) : Inline Page :=
  .code text

private def linkInline (label url : String) : Inline Page :=
  .link #[textInline label] url

private def paragraph (contents : Array (Inline Page)) : Block Page :=
  .para contents

private def divBlock (classes : String) (contents : Array (Block Page)) : Block Page :=
  .other (BlockExt.htmlDiv classes) contents

private def holeWrap (child : Block Page) : Block Page :=
  .other (BlockExt.htmlDiv "hole") #[child]

private def headingBlock (text : String) : Block Page :=
  .other (BlockExt.blob {{ <h2>{{Html.text true text}}</h2> }}) #[]

/-- "2026-04-30T10:05:19Z" → "Apr 30, 2026". Mirrors
`Leaderboard.formatDate`. -/
private def formatDate (iso : String) : String :=
  match iso.splitOn "T" with
  | date :: _ =>
    match date.splitOn "-" with
    | [yyyy, mm, dd] =>
      match mm.toNat? with
      | some m =>
        if 1 ≤ m ∧ m ≤ 12 then
          let name := monthNames[m - 1]!
          let dayNum := dd.toNat?.getD 0
          s!"{name} {dayNum}, {yyyy}"
        else iso
      | none => iso
    | _ => iso
  | [] => iso

/-- One row in the "Solved by" list on a per-problem detail page. The fields
are flattened from `LeaderboardEntry` + `SolvedProblem` so the list can be
sorted independently of the leaderboard's per-model grouping. -/
structure SolverRecord where
  user : String
  modelName : String
  solvedAt : String
  publicSolutionUrl : Option String
deriving Quote, Inhabited, Repr

/-- Collect all solves of `problemId`, one row per (model, submitter), sorted
oldest-first. Mirrors the per-model `solved_problems[]` shape of
`leaderboard.json` flattened to a per-problem view. -/
def solversFor (entries : Array LeaderboardEntry) (problemId : String) : Array SolverRecord :=
  let rows := entries.flatMap fun entry =>
    entry.solvedProblems.filterMap fun sp =>
      if sp.problemId = problemId then
        some {
          user := sp.provenance.user
          modelName := entry.modelName
          solvedAt := sp.solvedAt
          publicSolutionUrl := sp.publicSolution.url
        }
      else none
  rows.qsort (fun a b => a.solvedAt < b.solvedAt)

private def solverParagraph (s : SolverRecord) : Block Page :=
  let baseInlines : Array (Inline Page) := #[
    textInline "• ",
    linkInline s!"@{s.user}" s!"https://github.com/{s.user}",
    textInline (solverWithModelOnDate s.modelName (formatDate s.solvedAt))
  ]
  let inlines := match s.publicSolutionUrl with
    | some url =>
      baseInlines ++ #[textInline " (", linkInline proofWord url, textInline ")"]
    | none => baseInlines
  paragraph inlines

private def solversSection (solvers : Array SolverRecord) : Array (Block Page) :=
  if solvers.isEmpty then
    #[headingBlock solvedByLabel, paragraph #[textInline notYetSolvedText]]
  else
    #[headingBlock solvedByLabel] ++ solvers.map solverParagraph

private def isUrl (text : String) : Bool :=
  text.startsWith "http://" || text.startsWith "https://"

private def optionalParagraph (label : String) (value : Option String) : Block Page :=
  let body :=
    match value.map (·.trimAscii.toString) with
    | some s => if s.isEmpty then unavailable else s
    | none => unavailable
  paragraph #[textInline s!"{label}: {body}"]

private def sourceParagraph (value : Option String) : Block Page :=
  match value.map (·.trimAscii.toString) with
  | some s =>
    if s.isEmpty then
      paragraph #[textInline s!"{problemsSourcePrefix}{unavailable}"]
    else if isUrl s then
      paragraph #[textInline problemsSourcePrefix, linkInline s s]
    else
      paragraph #[textInline s!"{problemsSourcePrefix}{s}"]
  | none => paragraph #[textInline s!"{problemsSourcePrefix}{unavailable}"]

private def backLink : Block Page :=
  -- Verso emits a `<base href>` pointing at the site root, so a plain
  -- `problems/` href resolves to `<root>/problems/` rather than back up
  -- past the GitHub Pages base path.
  paragraph #[linkInline backToProblems "problems/"]

/-- Assemble one detail page's `Part Page` at runtime from spliced anchor
blocks plus the (already-flattened) solver list. Routing assembly through a
runtime function keeps the term tree the elaborator emits shallow — the same
pattern used in `Problems.lean`'s `assembleProblemPart`. -/
private def assembleDetailPart
    (title id submitterText : String)
    (notesText sourceText informalSolution : Option String)
    (anchors : Array (Block Page))
    (solvers : Array SolverRecord) : Part Page :=
  let prelude : Array (Block Page) := #[
    backLink,
    paragraph #[codeInline id],
    paragraph #[textInline submitterText],
    optionalParagraph problemsNotesLabel notesText,
    sourceParagraph sourceText,
    optionalParagraph problemsInformalSolutionLabel informalSolution
  ]
  let body :=
    prelude
    ++ anchors.map holeWrap
    ++ solversSection solvers
  Verso.Doc.Part.mk #[textInline title] title none body #[]

/-- Per-detail-page Lean name. Used as the `Dir.page` `id : Lean.Name` so
each generated page has a distinct entry in Verso's `pageIds` map (anything
collapsing to a shared key — e.g. `.anonymous` — would be silently
overwritten as later pages register). -/
private def pageNameFor (problemId : String) : Lean.Name :=
  (`LeaderboardSite.Pages.ProblemDetail).str problemId

/-- Term elaborator producing `Array Dir` of one detail page per
`ProblemEntry`, ready to splice into the `"problems"` directory's children
in `LeaderboardSite.lean`. -/
scoped syntax "problem_detail_pages%" : term

elab_rules : term
  | `(problem_detail_pages%) => do
      let problemsPayload ← parseProblemsPayload
      let leaderboardPayload ← parseLeaderboardPayload
      let problems ← validateProblems problemsPayload
      let mut dirTerms : Array (TSyntax `term) := #[]
      for problem in problems do
        let solvers := solversFor leaderboardPayload.entries problem.id
        let anchors : TSyntaxArray `term := anchorBlockTerms problem
        let pageName := pageNameFor problem.id
        let partTerm ← `(assembleDetailPart
            $(quote problem.title)
            $(quote problem.id)
            $(quote (problemsSubmitterSentence problem.submitter))
            $(quote problem.notesText)
            $(quote problem.sourceText)
            $(quote problem.informalSolution)
            #[$anchors,*]
            $(quote solvers))
        let dirTerm ← `(Dir.page $(quote problem.id) $(quote pageName) $partTerm #[])
        dirTerms := dirTerms.push dirTerm
      let arr : TSyntax `term ← `(#[$[$dirTerms],*])
      let expectedType ← Lean.Elab.Term.elabTerm (← `(Array Dir)) none
      Lean.Elab.Term.elabTerm arr (some expectedType)

end LeaderboardSite.Pages.ProblemDetail
