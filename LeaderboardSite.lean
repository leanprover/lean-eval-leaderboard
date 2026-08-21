import VersoBlog

import SiteTheme
import LeaderboardSite.Copy
import LeaderboardSite.Pages.Front
import LeaderboardSite.Pages.Problems
import LeaderboardSite.Pages.ProblemDetail
import LeaderboardSite.Pages.Submit
import LeaderboardSite.Pages.Preview

set_option maxRecDepth 65536

open Verso Doc
open Verso.Genre.Blog

open scoped LeaderboardSite.Pages.ProblemDetail
open scoped LeaderboardSite.Pages.Preview

/-- Site value built by hand rather than via `Site.Syntax`'s `site …` DSL.
The DSL only allows statically-listed children per directory, but the stable,
legacy, and preview problem directories each need a child `Dir.page` per
problem entry. Their macros expand those children at elaboration time. The
`%doc?` / `%docName?` macros resolve each top-level page constant exactly the
way the DSL would. -/
def leaderboardSite : Site :=
  Site.page (%docName? LeaderboardSite.Pages.V2Front) (%doc? LeaderboardSite.Pages.V2Front) #[
    Dir.static "static" "static",
    Dir.static "site-data" "site-data",
    Dir.page "problems"
      (%docName? LeaderboardSite.Pages.V2Problems)
      (%doc? LeaderboardSite.Pages.V2Problems)
      (v2_problem_pages%),
    Dir.page "formalization-evaluation"
      (%docName? LeaderboardSite.Pages.V2Formalization)
      (%doc? LeaderboardSite.Pages.V2Formalization) #[],
    Dir.page "software-verification"
      (%docName? LeaderboardSite.Pages.V2Software)
      (%doc? LeaderboardSite.Pages.V2Software) #[],
    Dir.page "open-conjectures"
      (%docName? LeaderboardSite.Pages.V2Conjectures)
      (%doc? LeaderboardSite.Pages.V2Conjectures) #[],
    Dir.page "recent"
      (%docName? LeaderboardSite.Pages.V2Recent)
      (%doc? LeaderboardSite.Pages.V2Recent) #[],
    Dir.page "submit"
      (%docName? LeaderboardSite.Pages.Submit)
      (%doc? LeaderboardSite.Pages.Submit)
      #[],
    Dir.page "legacy"
      (%docName? LeaderboardSite.Pages.Front)
      (%doc? LeaderboardSite.Pages.Front)
      #[
        Dir.page "problems"
          (%docName? LeaderboardSite.Pages.Problems)
          (%doc? LeaderboardSite.Pages.Problems)
          (problem_detail_pages%)
      ],
    Dir.page "preview"
      (%docName? LeaderboardSite.Pages.Preview)
      (%doc? LeaderboardSite.Pages.Preview)
      #[
        Dir.page "formalization-evaluation"
          (%docName? LeaderboardSite.Pages.PreviewFormalization)
          (%doc? LeaderboardSite.Pages.PreviewFormalization) #[],
        Dir.page "software-verification"
          (%docName? LeaderboardSite.Pages.PreviewSoftware)
          (%doc? LeaderboardSite.Pages.PreviewSoftware) #[],
        Dir.page "open-conjectures"
          (%docName? LeaderboardSite.Pages.PreviewConjectures)
          (%doc? LeaderboardSite.Pages.PreviewConjectures) #[],
        Dir.page "recent"
          (%docName? LeaderboardSite.Pages.PreviewRecent)
          (%doc? LeaderboardSite.Pages.PreviewRecent) #[],
        Dir.page "problems"
          (%docName? LeaderboardSite.Pages.PreviewProblems)
          (%doc? LeaderboardSite.Pages.PreviewProblems)
          (preview_problem_pages%)
      ]
  ]

def main (args : List String) : IO UInt32 :=
  blogMain (theme LeaderboardSite.Copy.siteThemeName LeaderboardSite.Copy.siteTitle)
    leaderboardSite {} args
