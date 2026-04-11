import Lake
open Lake DSL

require std from git "https://github.com/leanprover/std4" @ "v4.30.0-rc1"
require verso from git "https://github.com/leanprover/verso" @ "v4.30.0-rc1"

package «lean-eval-leaderboard» where

lean_lib SiteTheme where

lean_lib LeaderboardSite where

@[default_target]
lean_exe «lean-eval-leaderboard» where
  root := `LeaderboardSite
  supportInterpreter := true

script generate (args) do
  if !args.isEmpty then
    IO.eprintln "No args expected"
    return 1
  let dataCode ← IO.Process.Child.wait <| ← IO.Process.spawn {
    cmd := "python3"
    args := #["scripts/generate_site_data.py"]
  }
  if dataCode != 0 then
    return dataCode
  let siteCode ← IO.Process.Child.wait <| ← IO.Process.spawn {
    cmd := "lake"
    args := #["exe", "lean-eval-leaderboard", "--output", "_site"]
  }
  if siteCode != 0 then
    return siteCode
  return 0

