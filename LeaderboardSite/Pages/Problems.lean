import Lean.Data.Json
import VersoBlog

open Lean
open Lean.Elab
open Lean.Elab.Term
open Verso
open Verso.Doc
open Verso.Doc.Elab
open Verso.Genre.Blog
open Verso.Code.External

set_option verso.exampleProject "benchmark-snapshot"
set_option maxHeartbeats 1000000

namespace LeaderboardSite.Pages

private structure BenchmarkInfo where
  repo : String
  commit : String
deriving FromJson

private structure ProblemEntry where
  id : String
  title : String
  test : Bool
  submitter : String
  moduleName : String
  theoremName : String
  statementText : String
  notesText : Option String
  sourceText : Option String
  informalSolution : Option String
  challengePath : String
  sortIndex : Nat

private structure ProblemsPayload where
  schemaVersion : Nat
  generatedAt : String
  benchmark : BenchmarkInfo
  problems : Array ProblemEntry

private instance : FromJson ProblemEntry where
  fromJson? json := do
    return {
      id := ← json.getObjValAs? String "id"
      title := ← json.getObjValAs? String "title"
      test := ← json.getObjValAs? Bool "test"
      submitter := ← json.getObjValAs? String "submitter"
      moduleName := ← json.getObjValAs? String "module"
      theoremName := ← json.getObjValAs? String "theorem"
      statementText := ← json.getObjValAs? String "statement"
      notesText := (json.getObjValAs? String "notes").toOption
      sourceText := (json.getObjValAs? String "source").toOption
      informalSolution := (json.getObjValAs? String "informal_solution").toOption
      challengePath := ← json.getObjValAs? String "challenge_path"
      sortIndex := ← json.getObjValAs? Nat "sort_index"
    }

private instance : FromJson ProblemsPayload where
  fromJson? json := do
    return {
      schemaVersion := ← json.getObjValAs? Nat "schema_version"
      generatedAt := ← json.getObjValAs? String "generated_at"
      benchmark := ← json.getObjValAs? BenchmarkInfo "benchmark"
      problems := ← json.getObjValAs? (Array ProblemEntry) "problems"
    }

private def problemsJsonPath : System.FilePath :=
  "site-data/problems.json"

private def snapshotCatalogPath : System.FilePath :=
  "benchmark-snapshot/BenchmarkProblems/Catalog.lean"

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

private def parseProblemsPayload : TermElabM ProblemsPayload := do
  let raw ← IO.FS.readFile problemsJsonPath
  let json ←
    match Json.parse raw with
    | .ok json => pure json
    | .error err => throwError "Failed to parse {problemsJsonPath}: {err}"
  match FromJson.fromJson? json with
  | .ok payload => pure payload
  | .error err => throwError "Failed to decode {problemsJsonPath}: {err}"

private def loadSnapshotCatalog : TermElabM String :=
  IO.FS.readFile snapshotCatalogPath

private def theoremName (problem : ProblemEntry) : String :=
  match problem.theoremName.splitOn "." |>.reverse with
  | name :: _ => name
  | [] => problem.theoremName

private def anchorSourceText (catalog : String) (problem : ProblemEntry) : TermElabM String := do
  let startMarker := s!"-- ANCHOR: {problem.id}"
  let endMarker := s!"-- ANCHOR_END: {problem.id}"
  let parts := catalog.splitOn startMarker
  let some rest := parts[1]?
    | throwError "Anchor '{problem.id}' not found in {snapshotCatalogPath}"
  if parts.length != 2 then
    throwError "Anchor '{problem.id}' appears multiple times in {snapshotCatalogPath}"
  let rest := rest.dropWhile (· == '\n') |>.toString
  let bodyParts := rest.splitOn endMarker
  let some body := bodyParts[0]?
    | throwError "Anchor '{problem.id}' is missing its body in {snapshotCatalogPath}"
  if bodyParts.length < 2 then
    throwError "Anchor '{problem.id}' is missing its closing marker in {snapshotCatalogPath}"
  let body := body.trimAscii.toString
  if !body.contains s!"theorem {theoremName problem}" then
    throwError "Anchor '{problem.id}' does not contain theorem {theoremName problem}"
  pure body

private def validateProblems (payload : ProblemsPayload) : TermElabM (Array ProblemEntry) := do
  if payload.schemaVersion != 2 then
    throwError "Unsupported problems schema version {payload.schemaVersion}; expected 2"
  let mut seen : Std.HashSet String := {}
  for problem in payload.problems do
    if problem.id.trimAscii.isEmpty then
      throwError "Encountered a problem with an empty id"
    if problem.title.trimAscii.isEmpty then
      throwError "Problem '{problem.id}' is missing a title"
    if problem.statementText.trimAscii.isEmpty then
      throwError "Problem '{problem.id}' is missing a statement"
    if seen.contains problem.id then
      throwError "Duplicate problem id '{problem.id}' in {problemsJsonPath}"
    seen := seen.insert problem.id
  pure <| payload.problems.qsort (fun a b => a.sortIndex < b.sortIndex)

private def runPageDocElab (act : DocElabM α) : TermElabM α := do
  let ctx ← DocElabContext.fromGenreTerm (← `(Page))
  let initDocState : DocElabM.State := { highlightDeduplicationTable := .some {} }
  let initPartState : PartElabM.State := .init (Syntax.mkStrLit "Problems")
  let (result, _) ← DocElabM.run ctx initDocState initPartState act
  pure result

private def anchorBlockTerm (catalog : String) (problem : ProblemEntry) : TermElabM (TSyntax `term) := do
  let anchorName := mkIdent <| Name.mkSimple problem.id
  let moduleName := mkIdent `BenchmarkProblems.Catalog
  let args : Array Verso.Doc.Arg := #[
    .anon (.name anchorName),
    .named .missing (mkIdent `module) (.name moduleName)
  ]
  let expected := Syntax.mkStrLit (← anchorSourceText catalog problem)
  let terms ← runPageDocElab <| Verso.Code.External.anchor args expected
  match terms[0]? with
  | some term => pure term
  | none => throwError "Anchor expander for '{problem.id}' returned no block"

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

private def problemPartTerm (catalog : String) (problem : ProblemEntry) : TermElabM (TSyntax `term) := do
  let notesBlock ← optionalParagraphTerm "Notes" problem.notesText
  let sourceBlock ← sourceParagraphTerm problem
  let solutionBlock ← optionalParagraphTerm "Informal solution" problem.informalSolution
  let anchorBlock ← anchorBlockTerm catalog problem
  `(pagePart $(quote problem.title) #[
      paragraph #[codeInline $(quote problem.id)],
      paragraph #[textInline $(quote s!"Submitter: {problem.submitter}.")],
      $notesBlock,
      $sourceBlock,
      $solutionBlock,
      $anchorBlock
    ] #[] (some $(quote problem.id)))

private def sectionPartTerm (catalog : String) (title : String) (problems : Array ProblemEntry) : TermElabM (TSyntax `term) := do
  let subParts ← problems.mapM (problemPartTerm catalog)
  let subParts : TSyntaxArray `term := subParts
  `(pagePart $(quote title) #[] #[$subParts,*])

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
      let mainSection ← sectionPartTerm catalog "Main benchmark problems" mainProblems
      let mut subParts := #[mainSection]
      if !starterProblems.isEmpty then
        subParts := subParts.push (← sectionPartTerm catalog "Starter problems" starterProblems)
      let introBlocks' : TSyntaxArray `term := introBlocks
      let subParts' : TSyntaxArray `term := subParts
      let pageTerm ← `(pagePart "Problems" #[$introBlocks',*] #[$subParts',*])
      let expectedType ← Lean.Elab.Term.elabTerm (← `(Part Page)) none
      Lean.Elab.Term.elabTerm pageTerm (some expectedType)

def _root_.LeaderboardSite.Pages.Problems : Part Page :=
  problems_page%

end LeaderboardSite.Pages
