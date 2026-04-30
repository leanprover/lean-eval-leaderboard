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

structure ProblemEntry where
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

instance : FromJson ProblemEntry where
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

structure SolvedProblem where
  problemId : String
  solvedAt : String
  rarityRank : Nat
  publicSolution : PublicSolution
deriving Quote, Inhabited, Repr

instance : FromJson SolvedProblem where
  fromJson? json := do
    return {
      problemId := ← json.getObjValAs? String "problem_id"
      solvedAt := ← json.getObjValAs? String "solved_at"
      rarityRank := ← json.getObjValAs? Nat "rarity_rank"
      publicSolution := ← json.getObjValAs? PublicSolution "public_solution"
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

private def shortTheoremName (problem : ProblemEntry) : String :=
  match problem.theoremName.splitOn "." |>.reverse with
  | name :: _ => name
  | [] => problem.theoremName

def anchorSourceText (catalog : String) (problem : ProblemEntry) : TermElabM String := do
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
  if !body.contains s!"theorem {shortTheoremName problem}" then
    throwError "Anchor '{problem.id}' does not contain theorem {shortTheoremName problem}"
  pure body

def runPageDocElab (act : DocElabM α) : TermElabM α := do
  let ctx ← DocElabContext.fromGenreTerm (← `(Page))
  let initDocState : DocElabM.State := { highlightDeduplicationTable := .some {} }
  let initPartState : PartElabM.State := .init (Syntax.mkStrLit "Page")
  let (result, _) ← DocElabM.run ctx initDocState initPartState act
  pure result

def anchorBlockTerm (catalog : String) (problem : ProblemEntry) : TermElabM (TSyntax `term) := do
  let anchorName := Lean.mkIdent <| Lean.Name.mkSimple problem.id
  let moduleName := Lean.mkIdent `BenchmarkProblems.Catalog
  let args : Array Verso.Doc.Arg := #[
    .anon (.name anchorName),
    .named .missing (Lean.mkIdent `module) (.name moduleName)
  ]
  let expected := Syntax.mkStrLit (← anchorSourceText catalog problem)
  let terms ← runPageDocElab <| Verso.Code.External.anchor args expected
  match terms[0]? with
  | some term => pure term
  | none => throwError "Anchor expander for '{problem.id}' returned no block"

end LeaderboardSite.Data
