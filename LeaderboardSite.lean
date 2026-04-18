import VersoBlog

import SiteTheme
import LeaderboardSite.Pages.Front
import LeaderboardSite.Pages.Problems
import LeaderboardSite.Pages.Submit

open Verso.Genre.Blog
open Verso.Genre.Blog.Site.Syntax

def leaderboardSite : Site := site LeaderboardSite.Pages.Front /
  static "static" ← "static"
  static "site-data" ← "site-data"
  "problems" LeaderboardSite.Pages.Problems
  "submit" LeaderboardSite.Pages.Submit

def main (args : List String) : IO UInt32 :=
  blogMain (theme "Leaderboard" "Lean AI formalization leaderboard") leaderboardSite {} args
