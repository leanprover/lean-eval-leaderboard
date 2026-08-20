import VersoBlog
import LeaderboardSite.Leaderboard
import LeaderboardSite.Copy

set_option verso.exampleProject "benchmark-snapshot"
set_option maxHeartbeats 1000000
set_option maxRecDepth 65536

open Verso Doc
open Verso.Genre.Blog
open Verso.Output Html

namespace LeaderboardSite.Pages

open LeaderboardSite.Leaderboard

private def textInline (text : String) : Inline Page := .text text

private def textHtml (text : String) : Html := Html.text true text

private def htmlBlob (html : Html) : Block Page :=
  .other (BlockExt.blob html) #[]

private def previewBanner : Block Page :=
  htmlBlob {{
    <aside class="v2-preview-banner" aria-labelledby="v2-preview-title">
      <span class="v2-preview-badge">{{textHtml "Preview"}}</span>
      <div>
        <h1 id="v2-preview-title">{{textHtml "Results schema v2 preview"}}</h1>
        <p>
          {{textHtml "This page is rendered through the strict flat-v2 compatibility path. The current leaderboard remains available at the site root."}}
        </p>
      </div>
      <a href=".">{{textHtml "Return to the current leaderboard"}}</a>
    </aside>
  }}

private def pagePart (title : String) (content : Array (Block Page)) : Part Page :=
  .mk #[textInline title] title none content #[]

def _root_.LeaderboardSite.Pages.Preview : VersoDoc Page :=
  .mk (fun _ => pagePart "Results v2 preview"
    (#[previewBanner] ++ leaderboardPreview%)) "{}"

end LeaderboardSite.Pages
