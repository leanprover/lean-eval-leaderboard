import VersoBlog
import LeaderboardSite.Data

open Lean
open Lean.Elab Term
open Verso Doc Doc.Elab
open Verso.Genre.Blog
open Verso.Code.External

set_option verso.exampleProject "benchmark-snapshot"
set_option maxHeartbeats 1000000

namespace LeaderboardSite.Pages

open LeaderboardSite.Data

private def textInline (text : String) : Inline Page :=
  .text text

private def codeInline (text : String) : Inline Page :=
  .code text

private def linkInline (label url : String) : Inline Page :=
  .link #[textInline label] url

private def paragraph (contents : Array (Inline Page)) : Block Page :=
  .para contents

private def unavailableText : String :=
  "Unavailable."

private def valueOrUnavailable (value : Option String) : String :=
  match value.map (·.trimAscii.toString) with
  | some text => if text.isEmpty then unavailableText else text
  | none => unavailableText

private def pageMeta (htmlId? : Option String := none) : Option Page.Meta :=
  htmlId?.map fun htmlId => { htmlId }

private def pagePart
    (title : String)
    (content : Array (Block Page))
    (subParts : Array (Part Page) := #[])
    (htmlId? : Option String := none) :
    Part Page :=
  .mk #[textInline title] title (pageMeta htmlId?) content subParts

private def isUrl (text : String) : Bool :=
  text.startsWith "http://" || text.startsWith "https://"

private def optionalParagraphTerm
    (label : String)
    (value : Option String) :
    TermElabM (TSyntax `term) :=
  `(paragraph #[textInline $(quote s!"{label}: {valueOrUnavailable value}")])

private def sourceParagraphTerm (problem : ProblemEntry) : TermElabM (TSyntax `term) := do
  match problem.sourceText.map (·.trimAscii.toString) with
  | some source =>
      if isUrl source then
        `(paragraph #[
          textInline "Source: ",
          linkInline $(quote source) $(quote source)
        ])
      else
        `(paragraph #[textInline $(quote s!"Source: {source}")])
  | none =>
      `(paragraph #[textInline $(quote s!"Source: {unavailableText}")])

private def holeWrap (child : Block Page) : Block Page :=
  .other (BlockExt.htmlDiv "hole") #[child]

/-- Assemble one problem's `Part Page` at runtime from the spliced anchor
blocks. Routing per-problem assembly through this function keeps the
elaborator-time syntax tree shallow (one runtime call per problem rather
than a 5-plus-#holes literal), which avoids the code generator's
maximum-recursion-depth limit on problems with many holes. -/
private def assembleProblemPart
    (title id submitterText : String)
    (notes source solution : Block Page)
    (anchors : Array (Block Page)) : Part Page :=
  let prelude : Array (Block Page) := #[
    paragraph #[codeInline id],
    paragraph #[textInline submitterText],
    notes,
    source,
    solution
  ]
  pagePart title (prelude ++ anchors.map holeWrap) #[] (some id)

private def problemPartTerm (catalog : String) (problem : ProblemEntry) : TermElabM (TSyntax `term) := do
  let notesBlock ← optionalParagraphTerm "Notes" problem.notesText
  let sourceBlock ← sourceParagraphTerm problem
  let solutionBlock ← optionalParagraphTerm "Informal solution" problem.informalSolution
  let anchors ← anchorBlockTerms catalog problem
  let anchorsArr : TSyntaxArray `term := anchors
  `(assembleProblemPart
      $(quote problem.title)
      $(quote problem.id)
      $(quote s!"Submitter: {problem.submitter}.")
      $notesBlock
      $sourceBlock
      $solutionBlock
      #[$anchorsArr,*])

private def sectionPartTerm (catalog : String) (title : String) (htmlId : String)
    (problems : Array ProblemEntry) : TermElabM (TSyntax `term) := do
  let subParts ← problems.mapM (problemPartTerm catalog)
  let subParts : TSyntaxArray `term := subParts
  `(pagePart $(quote title) #[] #[$subParts,*] (some $(quote htmlId)))

private def introParagraphTerms : TermElabM (Array (TSyntax `term)) := do
  pure #[
    ← `(paragraph #[textInline "The benchmark catalog consists of carefully curated problems across mathematics, chosen so that their statements are mostly accessible using existing Mathlib definitions, but their solutions are difficult for current publicly available frontier models."]),
    ← `(paragraph #[
      textInline "The problem statements below are automatically extracted from the ",
      linkInline "lean-eval" "https://github.com/leanprover/lean-eval",
      textInline " repository."
    ]),
    ← `(paragraph #[
      textInline "Authors are encouraged to submit new problems via PRs to that repository, for inclusion in future benchmark releases. See ",
      linkInline "Submit" "/submit",
      textInline " for details on submitting solutions."
    ])
  ]

scoped syntax "problems_page%" : term

elab_rules : term
  | `(problems_page%) => do
      let payload ← parseProblemsPayload
      let catalog ← loadSnapshotCatalog
      let problems ← validateProblems payload
      let introBlocks ← introParagraphTerms
      let mainProblems := Array.filter (fun problem => !problem.test) problems
      let starterProblems := Array.filter (·.test) problems
      let mainSection ← sectionPartTerm catalog "Main benchmark problems" "main-problems" mainProblems
      let mut subParts := #[mainSection]
      if !starterProblems.isEmpty then
        subParts := subParts.push (← sectionPartTerm catalog "Starter problems" "starter-problems" starterProblems)
      let introBlocks' : TSyntaxArray `term := introBlocks
      let subParts' : TSyntaxArray `term := subParts
      let pageTerm ← `(pagePart "Problems" #[$introBlocks',*] #[$subParts',*])
      let expectedType ← Lean.Elab.Term.elabTerm (← `(Part Page)) none
      Lean.Elab.Term.elabTerm pageTerm (some expectedType)

/-- Wrapped as a `VersoDoc` so the `site` DSL's lookup of
`Problems.toPart` resolves to `VersoDoc.toPart` rather than the
deprecated `Part.toPart`. -/
def _root_.LeaderboardSite.Pages.Problems : VersoDoc Page :=
  .mk (fun _ => problems_page%) "{}"

end LeaderboardSite.Pages
