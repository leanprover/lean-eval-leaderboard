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
  Site.page (%docName? LeaderboardSite.Pages.LifecycleFront) (%doc? LeaderboardSite.Pages.LifecycleFront) #[
    Dir.static "static" "static",
    Dir.static "site-data" "site-data",
    Dir.page "problems"
      (%docName? LeaderboardSite.Pages.LifecycleProblems)
      (%doc? LeaderboardSite.Pages.LifecycleProblems)
      (lifecycle_problem_pages%),
    Dir.page "formalization-evaluation"
      (%docName? LeaderboardSite.Pages.LifecycleFormalization)
      (%doc? LeaderboardSite.Pages.LifecycleFormalization) #[],
    Dir.page "software-verification"
      (%docName? LeaderboardSite.Pages.LifecycleSoftware)
      (%doc? LeaderboardSite.Pages.LifecycleSoftware) #[],
    Dir.page "open-problems"
      (%docName? LeaderboardSite.Pages.LifecycleOpenProblems)
      (%doc? LeaderboardSite.Pages.LifecycleOpenProblems) #[],
    -- Keep the former public URL as a neutral compatibility alias. It has no
    -- independent group identity and is intentionally absent from navigation.
    Dir.page "open-conjectures"
      (%docName? LeaderboardSite.Pages.LifecycleOpenProblemsCompatibility)
      (%doc? LeaderboardSite.Pages.LifecycleOpenProblemsCompatibility) #[],
    Dir.page "recent"
      (%docName? LeaderboardSite.Pages.LifecycleRecent)
      (%doc? LeaderboardSite.Pages.LifecycleRecent) #[],
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
        Dir.page "open-problems"
          (%docName? LeaderboardSite.Pages.PreviewOpenProblems)
          (%doc? LeaderboardSite.Pages.PreviewOpenProblems) #[],
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
