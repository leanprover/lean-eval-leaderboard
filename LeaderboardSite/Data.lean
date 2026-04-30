import Lean.Data.Json
import VersoBlog

open Lean
open Lean.Elab Term
open Verso Doc Doc.Elab
open Verso.Genre.Blog
open Verso.Code.External

namespace LeaderboardSite.Data

structure BenchmarkInfo where
  repo : String
  commit : String
deriving FromJson

/-- One `@[eval_problem]`-annotated declaration. Multiple holes may belong
to the same `manifests/problems.toml` entry; they are rendered together as
a stack on the problems page and in home-page popovers. -/
structure Hole where
  /-- Fully-qualified declaration name (e.g. `LeanEval.Foo.bar`). -/
  name : String
  /-- Short basename (e.g. `bar`); unique within one problem. -/
  basename : String
  /-- Kernel-level kind: `theorem` / `def` / `instance` / `opaque`. The
  `body` text below already starts with the right Lean keyword, so the
  renderer keys off the body's leading token rather than this field. -/
  kind : String
  /-- Trimmed source body, with `@[eval_problem]` already stripped. -/
  body : String
deriving Inhabited, Quote, Repr

instance : FromJson Hole where
  fromJson? json := do
    return {
      name := ← json.getObjValAs? String "name"
      basename := ← json.getObjValAs? String "basename"
      kind := ← json.getObjValAs? String "kind"
      body := ← json.getObjValAs? String "body"
    }

structure ProblemEntry where
  id : String
  title : String
  test : Bool
  submitter : String
  moduleName : String
  holes : Array Hole
  notesText : Option String
  sourceText : Option String
  informalSolution : Option String
  challengePath : String
  sortIndex : Nat

instance : FromJson ProblemEntry where
  fromJson? json := do
    return {
      id := ← json.getObjValAs? String "id"
      title := ← json.getObjValAs? String "title"
      test := ← json.getObjValAs? Bool "test"
      submitter := ← json.getObjValAs? String "submitter"
      moduleName := ← json.getObjValAs? String "module"
      holes := ← json.getObjValAs? (Array Hole) "holes"
      notesText := (json.getObjValAs? String "notes").toOption
      sourceText := (json.getObjValAs? String "source").toOption
      informalSolution := (json.getObjValAs? String "informal_solution").toOption
      challengePath := ← json.getObjValAs? String "challenge_path"
      sortIndex := ← json.getObjValAs? Nat "sort_index"
    }

structure ProblemsPayload where
  schemaVersion : Nat
  generatedAt : String
  benchmark : BenchmarkInfo
  problems : Array ProblemEntry

instance : FromJson ProblemsPayload where
  fromJson? json := do
    return {
      schemaVersion := ← json.getObjValAs? Nat "schema_version"
      generatedAt := ← json.getObjValAs? String "generated_at"
      benchmark := ← json.getObjValAs? BenchmarkInfo "benchmark"
      problems := ← json.getObjValAs? (Array ProblemEntry) "problems"
    }

structure LeaderboardSummary where
  models : Nat
  submitters : Nat
  problems : Nat
  mainProblems : Nat
  testProblems : Nat
deriving Inhabited, Quote, Repr

instance : FromJson LeaderboardSummary where
  fromJson? json := do
    return {
      models := ← json.getObjValAs? Nat "models"
      submitters := ← json.getObjValAs? Nat "submitters"
      problems := ← json.getObjValAs? Nat "problems"
      mainProblems := ← json.getObjValAs? Nat "main_problems"
      testProblems := ← json.getObjValAs? Nat "test_problems"
    }

structure LeaderboardScore where
  solvedTotal : Nat
  solvedMain : Nat
  solvedTest : Nat
  display : String
deriving Quote, Inhabited, Repr

instance : FromJson LeaderboardScore where
  fromJson? json := do
    let total ← json.getObjValAs? Nat "solved_total"
    return {
      solvedTotal := total
      solvedMain := ← json.getObjValAs? Nat "solved_main"
      solvedTest := ← json.getObjValAs? Nat "solved_test"
      display := (json.getObjValAs? String "display").toOption.getD (toString total)
    }

structure SubmitterRef where
  user : String
  solvedTotal : Nat
deriving Quote, Inhabited, Repr

instance : FromJson SubmitterRef where
  fromJson? json := do
    return {
      user := ← json.getObjValAs? String "user"
      solvedTotal := ← json.getObjValAs? Nat "solved_total"
    }

structure PublicSolution where
  available : Bool
  url : Option String
deriving Quote, Inhabited, Repr

instance : FromJson PublicSolution where
  fromJson? json := do
    return {
      available := ← json.getObjValAs? Bool "available"
      url := (json.getObjValAs? String "url").toOption
    }

/-- Per-solve provenance. `user` is the GitHub login of the submitter who
solved the problem; multiple submitters can contribute solves to the same
leaderboard row, so per-problem attribution lives here rather than on the
parent `LeaderboardEntry`. -/
structure Provenance where
  user : String
deriving Quote, Inhabited, Repr

instance : FromJson Provenance where
  fromJson? json := do
    return {
      user := ← json.getObjValAs? String "user"
    }

structure SolvedProblem where
  problemId : String
  solvedAt : String
  rarityRank : Nat
  publicSolution : PublicSolution
  provenance : Provenance
  productionDescription : Option String
deriving Quote, Inhabited, Repr

instance : FromJson SolvedProblem where
  fromJson? json := do
    return {
      problemId := ← json.getObjValAs? String "problem_id"
      solvedAt := ← json.getObjValAs? String "solved_at"
      rarityRank := ← json.getObjValAs? Nat "rarity_rank"
      publicSolution := ← json.getObjValAs? PublicSolution "public_solution"
      provenance := ← json.getObjValAs? Provenance "provenance"
      productionDescription := (json.getObjValAs? String "production_description").toOption
    }

structure LeaderboardEntry where
  rank : Nat
  modelName : String
  submitterCount : Nat
  score : LeaderboardScore
  firstSolvedAt : String
  lastSolvedAt : String
  submitters : Array SubmitterRef
  notableProblemIds : Array String
  solvedProblems : Array SolvedProblem
deriving Quote, Inhabited, Repr

instance : FromJson LeaderboardEntry where
  fromJson? json := do
    return {
      rank := ← json.getObjValAs? Nat "rank"
      modelName := ← json.getObjValAs? String "model_name"
      submitterCount := ← json.getObjValAs? Nat "submitter_count"
      score := ← json.getObjValAs? LeaderboardScore "score"
      firstSolvedAt := ← json.getObjValAs? String "first_solved_at"
      lastSolvedAt := ← json.getObjValAs? String "last_solved_at"
      submitters := ← json.getObjValAs? (Array SubmitterRef) "submitters"
      notableProblemIds := ← json.getObjValAs? (Array String) "notable_problem_ids"
      solvedProblems := ← json.getObjValAs? (Array SolvedProblem) "solved_problems"
    }

structure LeaderboardPayload where
  schemaVersion : Nat
  generatedAt : String
  benchmark : BenchmarkInfo
  summary : LeaderboardSummary
  entries : Array LeaderboardEntry

instance : FromJson LeaderboardPayload where
  fromJson? json := do
    return {
      schemaVersion := ← json.getObjValAs? Nat "schema_version"
      generatedAt := ← json.getObjValAs? String "generated_at"
      benchmark := ← json.getObjValAs? BenchmarkInfo "benchmark"
      summary := ← json.getObjValAs? LeaderboardSummary "summary"
      entries := ← json.getObjValAs? (Array LeaderboardEntry) "entries"
    }

def problemsJsonPath : System.FilePath :=
  "site-data/problems.json"

def leaderboardJsonPath : System.FilePath :=
  "site-data/leaderboard.json"

def snapshotCatalogPath : System.FilePath :=
  "benchmark-snapshot/BenchmarkProblems/Catalog.lean"

def parseProblemsPayload : TermElabM ProblemsPayload := do
  let raw ← IO.FS.readFile problemsJsonPath
  let json ←
    match Json.parse raw with
    | .ok json => pure json
    | .error err => throwError "Failed to parse {problemsJsonPath}: {err}"
  match FromJson.fromJson? json with
  | .ok payload => pure payload
  | .error err => throwError "Failed to decode {problemsJsonPath}: {err}"

def parseLeaderboardPayload : TermElabM LeaderboardPayload := do
  let raw ← IO.FS.readFile leaderboardJsonPath
  let json ←
    match Json.parse raw with
    | .ok json => pure json
    | .error err => throwError "Failed to parse {leaderboardJsonPath}: {err}"
  match FromJson.fromJson? json with
  | .ok payload => pure payload
  | .error err => throwError "Failed to decode {leaderboardJsonPath}: {err}"

def loadSnapshotCatalog : TermElabM String :=
  IO.FS.readFile snapshotCatalogPath

def validateProblems (payload : ProblemsPayload) : TermElabM (Array ProblemEntry) := do
  if payload.schemaVersion != 3 then
    throwError "Unsupported problems schema version {payload.schemaVersion}; expected 3"
  let mut seen : Std.HashSet String := {}
  for problem in payload.problems do
    if problem.id.trimAscii.isEmpty then
      throwError "Encountered a problem with an empty id"
    if problem.title.trimAscii.isEmpty then
      throwError "Problem '{problem.id}' is missing a title"
    if problem.holes.isEmpty then
      throwError "Problem '{problem.id}' has no holes"
    if seen.contains problem.id then
      throwError "Duplicate problem id '{problem.id}' in {problemsJsonPath}"
    seen := seen.insert problem.id
  pure <| payload.problems.qsort (fun a b => a.sortIndex < b.sortIndex)

def holeAnchorId (problemId : String) (hole : Hole) : String :=
  s!"{problemId}__{hole.basename}"

/-- Look up one hole's anchor body in the snapshot catalog. The anchor name
is `<problem-id>__<basename>`. Returns the trimmed body so callers can use
it for plain-text fallbacks. -/
def anchorSourceText (catalog : String) (problemId : String) (hole : Hole) : TermElabM String := do
  let anchorId := holeAnchorId problemId hole
  -- Trailing newline pins the match to the full anchor line; without it,
  -- a basename like `genus` would prefix-match `genus_eq_zero_iff_homeo`.
  let startMarker := s!"-- ANCHOR: {anchorId}\n"
  let endMarker := s!"-- ANCHOR_END: {anchorId}\n"
  let parts := catalog.splitOn startMarker
  let some rest := parts[1]?
    | throwError "Anchor '{anchorId}' not found in {snapshotCatalogPath}"
  if parts.length != 2 then
    throwError "Anchor '{anchorId}' appears multiple times in {snapshotCatalogPath}"
  let rest := rest.dropWhile (· == '\n') |>.toString
  let bodyParts := rest.splitOn endMarker
  let some body := bodyParts[0]?
    | throwError "Anchor '{anchorId}' is missing its body in {snapshotCatalogPath}"
  if bodyParts.length < 2 then
    throwError "Anchor '{anchorId}' is missing its closing marker in {snapshotCatalogPath}"
  pure body.trimAscii.toString

def runPageDocElab (act : DocElabM α) : TermElabM α := do
  let ctx ← DocElabContext.fromGenreTerm (← `(Page))
  let initDocState : DocElabM.State := { highlightDeduplicationTable := .some {} }
  let initPartState : PartElabM.State := .init (Syntax.mkStrLit "Page")
  let (result, _) ← DocElabM.run ctx initDocState initPartState act
  pure result

/-- Build a `TSyntax \`term` for one hole's Verso anchor. When elaborated,
this expands into a deeply-nested `Block Page` value carrying the
highlighted source. Each call yields a fresh expression tree. -/
def inlineAnchorTerm (catalog : String) (problem : ProblemEntry) (hole : Hole) :
    TermElabM (TSyntax `term) := do
  let moduleName := Lean.mkIdent `BenchmarkProblems.Catalog
  let anchorId := holeAnchorId problem.id hole
  let anchorName := Lean.mkIdent <| Lean.Name.mkSimple anchorId
  let args : Array Verso.Doc.Arg := #[
    .anon (.name anchorName),
    .named .missing (Lean.mkIdent `module) (.name moduleName)
  ]
  let expected := Syntax.mkStrLit (← anchorSourceText catalog problem.id hole)
  let terms ← runPageDocElab <| Verso.Code.External.anchor args expected
  match terms[0]? with
  | some term => pure term
  | none => throwError "Anchor expander for '{anchorId}' returned no block"

/-- Stable top-level constant name carrying one hole's anchor block.
Each anchor lives in its own `def` so the page that uses them stays
tractable for the Lean code generator (otherwise inlining 24+ Verso
anchor expressions into a single problem fragment overflows codegen
recursion). -/
def anchorConstName (problemId : String) (hole : Hole) : Lean.Name :=
  let leaf := s!"_anc_{problemId}__{hole.basename}"
  (((Lean.Name.mkSimple "LeaderboardSite").str "Pages").str "Anchors").str leaf

/-- Identifier referring to the top-level constant declared by
`register_problem_anchors` for this hole. -/
def anchorConstIdent (problemId : String) (hole : Hole) : Lean.Ident :=
  Lean.mkIdent (anchorConstName problemId hole)

/-- One identifier reference per hole, in source order. The identifier
points at the constant declared by `register_problem_anchors`. -/
def anchorBlockTerms (problem : ProblemEntry) : Array (TSyntax `term) :=
  problem.holes.map fun hole => ⟨anchorConstIdent problem.id hole⟩

end LeaderboardSite.Data
