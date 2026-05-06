import VersoBlog
import LeaderboardSite.Copy

open Lean
open Verso Doc
open Verso.Genre.Blog
open Verso.Output Html

namespace LeaderboardSite.Pages

open LeaderboardSite.Copy

private def textInline (text : String) : Inline Page := .text text

private def textHtml (s : String) : Verso.Output.Html := Verso.Output.Html.text true s

private def pagePart
    (title : String)
    (content : Array (Block Page))
    (subParts : Array (Part Page) := #[]) :
    Part Page :=
  .mk #[textInline title] title none content subParts

private def htmlBlob (h : Verso.Output.Html) : Block Page :=
  Verso.Doc.Block.other (BlockExt.blob h) #[]

/-- Big "Submit benchmark solution" button at the top of the page. -/
private def ctaBlock : Block Page :=
  htmlBlob {{
    <a class="cta-button" href={{submitCtaUrl}}>
      <span>{{textHtml submitCtaLabel}}</span>
      <span aria-hidden="true">{{textHtml submitCtaArrow}}</span>
    </a>
  }}

/-- Three-step TL;DR paragraph between the CTA and the lead. The HTML
weaves a `<code>` and an `<a>` mid-sentence so its prose is broken
into chunks rather than authored as a single string. -/
private def tldrBlock : Block Page :=
  htmlBlob {{
    <p class="submit-tldr">
      {{textHtml submitTldrPart1}}
      <code>{{textHtml submitTldrCode1}}</code>
      {{textHtml submitTldrPart2}}
      <a href={{submitTldrComparatorUrl}}>{{textHtml submitTldrComparatorLabel}}</a>
      {{textHtml submitTldrPart3}}
    </p>
  }}

/-- Build a step sub-Part: title, explicit `htmlId` (referenced by CSS
and anchors — must not drift), and body blocks pulled from a Verso
markdown body in `Copy`. -/
private def stepPart (title id : String) (body : VersoDoc Page) : Part Page :=
  Verso.Doc.Part.mk #[textInline title] title (some { htmlId := id })
    body.toPart.content #[]

private def step1 : Part Page :=
  stepPart submitStep1Title submitStep1HtmlId submitStep1Body

private def step2 : Part Page :=
  stepPart submitStep2Title submitStep2HtmlId submitStep2Body

private def step3 : Part Page :=
  stepPart submitStep3Title submitStep3HtmlId submitStep3Body

private def whatBecomesPublic : Part Page :=
  stepPart submitWhatPublicTitle submitWhatPublicHtmlId submitWhatPublicBody

def _root_.LeaderboardSite.Pages.Submit : VersoDoc Page :=
  .mk (fun _ => pagePart submitTitle
    (#[ctaBlock, tldrBlock] ++ submitLeadBody.toPart.content)
    #[step1, step2, step3, whatBecomesPublic]) "{}"

end LeaderboardSite.Pages
