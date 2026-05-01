import VersoBlog
import LeaderboardSite.Data
import LeaderboardSite.AnchorRegistry

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

private def codeLinkInline (id url : String) : Inline Page :=
  .link #[codeInline id] url

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

open Verso.Output Html in
/-- Render the live filter box at the top of the Problems page.
The matching is implemented in `static/site.js`: it walks every
`section[id]` under `main` and hides the ones whose text content
doesn't include the query (case-insensitive). -/
private def filterBlock : Block Page :=
  let html : Verso.Output.Html := {{
    <div class="problems-filter" data-problems-filter="true">
      <label class="problems-filter-label" for="problems-filter-input">
        <span class="problems-filter-icon" aria-hidden="true">"⌕"</span>
        <span class="problems-filter-label-text">"Filter problems"</span>
      </label>
      <input id="problems-filter-input" type="search" class="problems-filter-input"
             placeholder="title, id, notes, source, or Lean source"
             aria-describedby="problems-filter-count"
             autocomplete="off" spellcheck="false"/>
      <span id="problems-filter-count"
            class="problems-filter-count"
            aria-live="polite"></span>
    </div>
  }}
  Verso.Doc.Block.other (BlockExt.blob html) #[]

open Verso.Output Html in
/-- Render an in-page table of contents as a collapsible `<details>` block.
Each item links to the per-problem detail page. -/
private def tocBlock (items : Array (String × String)) : Block Page :=
  -- Verso emits a `<base href>` pointing at the site root, so all
  -- relative URLs in the page resolve from there. We want each TOC
  -- entry to point at `<root>/problems/<id>/`, so use the explicit
  -- `problems/<id>/` shape (no leading slash, no `..`).
  let lis : Verso.Output.Html := Verso.Output.Html.fromArray <|
    items.map fun (id, title) =>
      let href := s!"problems/{id}/"
      {{ <li><a href={{href}}>{{Verso.Output.Html.text true title}}</a></li> }}
  let html : Verso.Output.Html := {{
    <details class="problems-toc">
      <summary>"All problems"</summary>
      <ul class="problems-toc-list">{{lis}}</ul>
    </details>
  }}
  Verso.Doc.Block.other (BlockExt.blob html) #[]

open Verso.Output Html in
/-- Hidden marker emitted as the first child of each problem `<section>`.
The element carries a precomputed lower-cased `data-filter-text`
haystack of every field the filter should match against (title, id,
submitter, notes, source, informal solution, Lean source). The JS
filter selects on `[data-problem-section]` rather than guessing
structure from heading levels, and reads the haystack from
`data-filter-text` instead of walking `innerText` of the whole
section, so future visible decorations don't accidentally become
matchable. -/
private def filterHaystack (haystack : String) : Block Page :=
  let html : Verso.Output.Html := {{
    <span class="problem-filter-haystack" data-problem-section="true"
          data-filter-text={{haystack}} hidden="true" aria-hidden="true"></span>
  }}
  Verso.Doc.Block.other (BlockExt.blob html) #[]

/-- Assemble one problem's `Part Page` at runtime from the spliced anchor
blocks. Routing per-problem assembly through this function keeps the
elaborator-time syntax tree shallow (one runtime call per problem rather
than a 5-plus-#holes literal), which avoids the code generator's
maximum-recursion-depth limit on problems with many holes. -/
private def assembleProblemPart
    (title id submitterText haystack : String)
    (notes source solution : Block Page)
    (anchors : Array (Block Page)) : Part Page :=
  let prelude : Array (Block Page) := #[
    filterHaystack haystack,
    -- The id chip is a link to the per-problem detail page.
    paragraph #[codeLinkInline id s!"problems/{id}/"],
    paragraph #[textInline submitterText],
    notes,
    source,
    solution
  ]
  pagePart title (prelude ++ anchors.map holeWrap) #[] (some id)

/-- Build the lower-cased filter haystack for a problem: title, id,
submitter, notes, source, informal solution, and the body of every
hole. This is what the live filter on `/problems/` matches against. -/
private def filterHaystackText (problem : ProblemEntry) : String :=
  let parts : Array String := #[
    problem.title,
    problem.id,
    problem.submitter,
    problem.notesText.getD "",
    problem.sourceText.getD "",
    problem.informalSolution.getD ""
  ] ++ problem.holes.map (·.body)
  (String.intercalate " " parts.toList).toLower

private def problemPartTerm (problem : ProblemEntry) : TermElabM (TSyntax `term) := do
  let notesBlock ← optionalParagraphTerm "Notes" problem.notesText
  let sourceBlock ← sourceParagraphTerm problem
  let solutionBlock ← optionalParagraphTerm "Informal solution" problem.informalSolution
  let anchorsArr : TSyntaxArray `term := anchorBlockTerms problem
  `(assembleProblemPart
      $(quote problem.title)
      $(quote problem.id)
      $(quote s!"Submitter: {problem.submitter}.")
      $(quote (filterHaystackText problem))
      $notesBlock
      $sourceBlock
      $solutionBlock
      #[$anchorsArr,*])

open Verso.Output Html in
/-- Hidden marker emitted as the first child of each group section
("Main benchmark problems" / "Test problems"). The JS filter selects
on `[data-problem-group]` rather than guessing structure from heading
levels or "any section with direct child sections". -/
private def groupHaystack : Block Page :=
  let html : Verso.Output.Html := {{
    <span class="problem-filter-haystack" data-problem-group="true"
          hidden="true" aria-hidden="true"></span>
  }}
  Verso.Doc.Block.other (BlockExt.blob html) #[]

private def sectionPartTerm (title : String) (htmlId : String)
    (problems : Array ProblemEntry) : TermElabM (TSyntax `term) := do
  let subParts ← problems.mapM problemPartTerm
  let subParts : TSyntaxArray `term := subParts
  `(pagePart $(quote title) #[groupHaystack] #[$subParts,*] (some $(quote htmlId)))

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
      linkInline "Submit" "submit/",
      textInline " for details on submitting solutions."
    ])
  ]

scoped syntax "problems_page%" : term

elab_rules : term
  | `(problems_page%) => do
      let payload ← parseProblemsPayload
      let problems ← validateProblems payload
      let introBlocks ← introParagraphTerms
      let mainProblems := Array.filter (fun problem => !problem.test) problems
      let starterProblems := Array.filter (·.test) problems
      let mainSection ← sectionPartTerm "Main benchmark problems" "main-problems" mainProblems
      let mut subParts := #[mainSection]
      if !starterProblems.isEmpty then
        subParts := subParts.push (← sectionPartTerm "Test problems" "test-problems" starterProblems)
      let tocItems : Array (String × String) :=
        (mainProblems ++ starterProblems).map fun p => (p.id, p.title)
      let tocTerm ← `(tocBlock $(quote tocItems))
      let filterTerm ← `(filterBlock)
      let introBlocks' : TSyntaxArray `term :=
        (introBlocks.push filterTerm).push tocTerm
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
