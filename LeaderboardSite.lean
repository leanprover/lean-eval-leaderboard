import VersoBlog

import SiteTheme
import LeaderboardSite.Pages.Front
import LeaderboardSite.Pages.Benchmark
import LeaderboardSite.Pages.Problems

open Verso.Genre.Blog
open Verso.Genre.Blog.Site.Syntax

def leaderboardSite : Site := site LeaderboardSite.Pages.Front /
  static "static" ← "static"
  static "site-data" ← "site-data"
  "benchmark" LeaderboardSite.Pages.Benchmark
  "problems" LeaderboardSite.Pages.Problems

def main (args : List String) : IO UInt32 :=
  blogMain (theme "Leaderboard" "Lean AI formalization leaderboard") leaderboardSite {} args
