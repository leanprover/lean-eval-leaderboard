import VersoBlog

import SiteTheme
import LeaderboardSite.Pages.Front
import LeaderboardSite.Pages.Problems
import LeaderboardSite.Pages.Submit

open Verso.Genre.Blog
open Verso.Genre.Blog.Site.Syntax

def leaderboardSite : IO Site := do
  let problemsPage ← LeaderboardSite.Pages.Problems.loadPage
  pure <|
    .page (%docName? LeaderboardSite.Pages.Front) (%doc? LeaderboardSite.Pages.Front) #[
      .static "static" "static",
      .static "site-data" "site-data",
      .page "problems" `LeaderboardSite.Pages.Problems problemsPage #[],
      .page "submit" (%docName? LeaderboardSite.Pages.Submit) (%doc? LeaderboardSite.Pages.Submit) #[]
    ]

def main (args : List String) : IO UInt32 := do
  blogMain (theme "Leaderboard" "Lean AI formalization leaderboard") (← leaderboardSite) {} args
