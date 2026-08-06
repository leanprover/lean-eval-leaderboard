import VersoBlog
import LeaderboardSite.Leaderboard
import LeaderboardSite.Copy

set_option verso.exampleProject "benchmark-snapshot"
set_option maxHeartbeats 1000000

-- `leaderboard%` expands to one binding per notable problem, so elaboration
-- depth grows with the catalog. Flattening the anchor map (#59) cut the cost
-- per binding by about 4x, but the growth is still linear and the default
-- budget of 512 was already exhausted once, at 118 notable problems, which
-- broke the published site for two days. Raise the ceiling so the next
-- threshold is far beyond any plausible catalog size.
set_option maxRecDepth 4000

open Lean
open Verso Doc
open Verso.Genre.Blog

namespace LeaderboardSite.Pages

open LeaderboardSite.Leaderboard
open LeaderboardSite.Copy

private def textInline (text : String) : Inline Page := .text text

private def pagePart
    (title : String)
    (content : Array (Block Page))
    (subParts : Array (Part Page) := #[]) :
    Part Page :=
  .mk #[textInline title] title none content subParts

/-- The home page: leaderboard widget (full-width) on top, intro prose
(constrained-width) below. The prose lives in `Copy.frontIntro`,
authored as Verso markdown wrapped in the existing `wrap prose
page-copy` div so the home page's full-width layout (which bypasses the
theme's default prose container) still gets the readable column.

Wrapped as a `VersoDoc` so the `site` DSL's lookup of `Front.toPart`
resolves to `VersoDoc.toPart` rather than the deprecated `Part.toPart`. -/
def _root_.LeaderboardSite.Pages.Front : VersoDoc Page :=
  .mk (fun _ => pagePart siteTitle
    (leaderboard% ++ frontIntro.toPart.content)) "{}"

end LeaderboardSite.Pages
