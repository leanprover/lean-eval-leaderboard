import VersoBlog
import LeaderboardSite.Data

open Lean
open Lean.Elab Term Command
open Verso Doc Doc.Elab
open Verso.Genre.Blog
open Verso.Code.External
open LeaderboardSite.Data

set_option verso.exampleProject "benchmark-snapshot"
set_option maxHeartbeats 1000000

/-- Register one top-level constant per `@[eval_problem]`-tagged hole, each
of type `Block Page` and holding the Verso anchor block for that hole.
Pages downstream (catalog and home-page popovers) reference these
constants by name, which keeps each downstream `def`'s body small enough
for the Lean code generator — inlining 24+ Verso anchors into a single
`def`'s expression tree overflows the codegen recursion budget.

Lives in its own module (separate from `Data.lean`) so the `syntax`
declaration is fully registered before the same module needs to parse
the `register_problem_anchors` invocation; defining and using a custom
command keyword in the same compilation unit doesn't reliably take
effect on the very next command position. -/
syntax "register_problem_anchors" : command

elab_rules : command
  | `(register_problem_anchors) => do
      let problems ← Lean.Elab.Command.runTermElabM fun _ => do
        let payload ← parseProblemsPayload
        validateProblems payload
      for problem in problems do
        -- Load this problem's snapshot file once, then synthesize a
        -- `def` per hole. Per-problem files keep each problem's
        -- `import` lines scoped to that file alone, which prevents one
        -- source's `import Mathlib` from turning identifiers like `μ`
        -- in another problem's body into reserved notation tokens.
        let fileText ← Lean.Elab.Command.runTermElabM fun _ =>
          loadSnapshotProblemFile problem.snapshotModule
        for hole in problem.holes do
          let constName := anchorConstName problem.id hole
          if (← Lean.getEnv).contains constName then
            continue
          let anchorTerm ← Lean.Elab.Command.runTermElabM fun _ =>
            inlineAnchorTerm fileText problem hole
          let constIdent := Lean.mkIdent constName
          let cmd ← `(def $constIdent : Block Page := $anchorTerm)
          Lean.Elab.Command.elabCommand cmd

register_problem_anchors
