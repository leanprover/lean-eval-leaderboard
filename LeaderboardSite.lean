import VersoBlog

import SiteTheme
import LeaderboardSite.Pages.Front
import LeaderboardSite.Pages.Problems
import LeaderboardSite.Pages.ProblemDetail
import LeaderboardSite.Pages.Submit

open Verso Doc
open Verso.Genre.Blog

open scoped LeaderboardSite.Pages.ProblemDetail

/-- Site value built by hand rather than via `Site.Syntax`'s `site …` DSL.
The DSL only allows statically-listed children per directory, but the
`"problems"` directory needs a child `Dir.page` per problem entry, expanded
at elaboration time by `problem_detail_pages%`. The `%doc?` / `%docName?`
macros resolve each top-level page constant exactly the way the DSL would. -/
def leaderboardSite : Site :=
  Site.page (%docName? LeaderboardSite.Pages.Front) (%doc? LeaderboardSite.Pages.Front) #[
    Dir.static "static" "static",
    Dir.static "site-data" "site-data",
    Dir.page "problems"
      (%docName? LeaderboardSite.Pages.Problems)
      (%doc? LeaderboardSite.Pages.Problems)
      (problem_detail_pages%),
    Dir.page "submit"
      (%docName? LeaderboardSite.Pages.Submit)
      (%doc? LeaderboardSite.Pages.Submit)
      #[]
  ]

def main (args : List String) : IO UInt32 :=
  blogMain (theme "Leaderboard" "Lean AI formalization leaderboard") leaderboardSite {} args
