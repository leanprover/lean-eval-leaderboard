import Lean.Data.Json
import VersoBlog

open Lean
open Verso
open Verso.Doc
open Verso.Genre.Blog

namespace LeaderboardSite.Pages.Problems

structure BenchmarkInfo where
  repo : String
  commit : String

structure ProblemEntry where
  id : String
  title : String
  test : Bool
  submitter : String
  moduleName : String
  theoremName : String
  statement : String
  notes : Option String := none
  source : Option String := none
  informal_solution : Option String := none
  challenge_path : String
  sort_index : Nat

structure ProblemsPayload where
  schema_version : Nat
  generated_at : String
  benchmark : BenchmarkInfo
  problems : Array ProblemEntry

def optionalStringField (json : Json) (key : String) : Except String (Option String) :=
  match json.getObjVal? key with
  | Except.ok value =>
    match Json.getStr? value with
    | Except.ok str => pure (some str)
    | Except.error err => Except.error err
  | Except.error _ => pure none

instance : FromJson BenchmarkInfo where
  fromJson? json :=
    return {
      repo := ← json.getObjValAs? String "repo",
      commit := ← json.getObjValAs? String "commit"
    }

instance : FromJson ProblemEntry where
  fromJson? json := do
    let notes : Option String ← optionalStringField json "notes"
    let source : Option String ← optionalStringField json "source"
    let informalSolution : Option String ← optionalStringField json "informal_solution"
    return {
      id := ← json.getObjValAs? String "id",
      title := ← json.getObjValAs? String "title",
      test := ← json.getObjValAs? Bool "test",
      submitter := ← json.getObjValAs? String "submitter",
      moduleName := ← json.getObjValAs? String "module",
      theoremName := ← json.getObjValAs? String "theorem",
      statement := ← json.getObjValAs? String "statement",
      notes := notes,
      source := source,
      informal_solution := informalSolution,
      challenge_path := ← json.getObjValAs? String "challenge_path",
      sort_index := ← json.getObjValAs? Nat "sort_index"
    }

instance : FromJson ProblemsPayload where
  fromJson? json :=
    return {
      schema_version := ← json.getObjValAs? Nat "schema_version",
      generated_at := ← json.getObjValAs? String "generated_at",
      benchmark := ← json.getObjValAs? BenchmarkInfo "benchmark",
      problems := ← json.getObjValAs? (Array ProblemEntry) "problems"
    }

def intro : Array (Block Page) :=
  #[
    .para #[
      .text "The benchmark catalog consists of carefully curated problems across mathematics, chosen so that their statements are mostly accessible using existing Mathlib definitions, but their solutions are difficult for current publicly available frontier models."
    ],
    .para #[
      .text "The problem statements below are automatically extracted from the ",
      .link #[(.text "lean-eval")] "https://github.com/kim-em/lean-eval",
      .text " repository. Authors are encouraged to submit new problems via PRs to that repository, for inclusion in future benchmark releases. See ",
      .link #[(.text "Submit")] "/submit",
      .text " for details on submitting solutions."
    ]
  ]

def textOrUnavailable (value : Option String) : String :=
  match value with
  | some text =>
    let trimmed := text.trimAscii.toString
    if trimmed.isEmpty then
      "Unavailable."
    else
      trimmed
  | none => "Unavailable."

def paragraphWithLabel (label value : String) : Block Page :=
  .para #[
    .text s!"{label}: ",
    .text value
  ]

def problemPart (problem : ProblemEntry) : Part Page :=
  .mk
    #[.text problem.title]
    problem.title
    none
    #[
      .para #[.code problem.id],
      paragraphWithLabel "Submitter" problem.submitter,
      paragraphWithLabel "Notes" (textOrUnavailable problem.notes),
      paragraphWithLabel "Source" (textOrUnavailable problem.source),
      paragraphWithLabel "Informal solution" (textOrUnavailable problem.informal_solution),
      .code problem.statement
    ]
    #[]

def problemSection (title : String) (problems : Array ProblemEntry) : Part Page :=
  .mk
    #[.text title]
    title
    none
    #[]
    (problems.qsort (fun a b => a.sort_index < b.sort_index) |>.map problemPart)

def pageFromPayload (payload : ProblemsPayload) : Part Page :=
  let mainProblems := payload.problems.filter (not ·.test)
  let starterProblems := payload.problems.filter (·.test)
  .mk
    #[.text "Problems"]
    "Problems"
    none
    intro
    #[
      problemSection "Main benchmark problems" mainProblems,
      problemSection "Starter problems" starterProblems
    ]

def loadPayload (path : System.FilePath := "site-data/problems.json") : IO ProblemsPayload := do
  let raw ← IO.FS.readFile path
  let json ←
    match Json.parse raw with
    | Except.ok value => pure value
    | Except.error err => throw <| IO.userError s!"Failed to parse {path}: {err}"
  match FromJson.fromJson? json with
  | Except.ok payload => pure payload
  | Except.error err => throw <| IO.userError s!"Failed to decode {path}: {err}"

def loadPage (path : System.FilePath := "site-data/problems.json") : IO (Part Page) :=
  pageFromPayload <$> loadPayload path

end LeaderboardSite.Pages.Problems
