import VersoBlog
import LeaderboardSite.Leaderboard

set_option verso.exampleProject "benchmark-snapshot"
set_option maxHeartbeats 1000000

open Lean
open Lean.Elab Term
open Verso Doc
open Verso.Genre.Blog

namespace LeaderboardSite.Pages

open LeaderboardSite.Leaderboard

private def textInline (text : String) : Inline Page := .text text

private def linkInline (label url : String) : Inline Page :=
  .link #[.text label] url

private def codeInline (text : String) : Inline Page := .code text

private def paragraph (contents : Array (Inline Page)) : Block Page :=
  .para contents

private def pagePart
    (title : String)
    (content : Array (Block Page))
    (subParts : Array (Part Page) := #[]) :
    Part Page :=
  .mk #[textInline title] title none content subParts

private def divBlock (classes : String) (contents : Array (Block Page)) : Block Page :=
  .other (BlockExt.htmlDiv classes) contents

/-- Intro prose displayed after the leaderboard widget. Wrapped in
`.wrap.prose.page-copy` so it gets the standard readable column. -/
private def introProse : Block Page :=
  divBlock "wrap prose page-copy" #[
    paragraph #[
      textInline "Welcome to ",
      codeInline "lean-eval",
      textInline ", a Lean formalization benchmark and public leaderboard."
    ],
    paragraph #[
      textInline "You can submit new problems for review, and solutions for existing problems. New problems will be carefully reviewed and added to future benchmark releases if they are accepted. Solutions are automatically verified using ",
      linkInline "comparator" "https://github.com/leanprover/comparator",
      textInline " and added to the public leaderboard."
    ],
    paragraph #[
      textInline "This benchmark intends to capture hard Lean formalization problems, consisting of mathematical problems that are currently stateable mostly using existing ",
      linkInline "Mathlib" "https://github.com/leanprover-community/mathlib4",
      textInline " definitions, perhaps with a page or so of additional setup. They should be hard, but usually not open problems: in fact, it's preferred if the problem has a known informal solution which is publicly available."
    ],
    paragraph #[
      textInline "Our hope is that at launch, the problem set will be mostly, but not entirely, out of reach for current publicly available frontier models, or simple orchestration layers built on top of these. So some genuine mathematical subtlety is required!"
    ],
    paragraph #[
      textInline "It's also important to say what this benchmark is not: we are not trying to capture the ability to write readable or reusable code, or to follow best practices in Lean. In particular, the only requirement for a solution to be accepted is that it is correct and passes the comparator tests."
    ]
  ]

/-- The home page: leaderboard widget (full-width) on top, intro prose
(constrained-width) below. The page does its own wrapping; the theme
does not impose a prose container on this page.

Wrapped as a `VersoDoc` so the `site` DSL's lookup of `Front.toPart`
resolves to `VersoDoc.toPart` rather than the deprecated `Part.toPart`. -/
def _root_.LeaderboardSite.Pages.Front : VersoDoc Page :=
  .mk (fun _ => pagePart "Lean AI formalization leaderboard"
    (leaderboard% ++ #[introProse])) "{}"

end LeaderboardSite.Pages
