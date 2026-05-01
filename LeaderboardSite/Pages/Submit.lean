import VersoBlog

open Lean
open Verso Doc
open Verso.Genre.Blog
open Verso.Output Html

namespace LeaderboardSite.Pages

private def textInline (text : String) : Inline Page := .text text
private def codeInline (text : String) : Inline Page := .code text
private def linkInline (label url : String) : Inline Page :=
  .link #[.text label] url
private def emInline (text : String) : Inline Page := .emph #[.text text]

private def paragraph (contents : Array (Inline Page)) : Block Page :=
  .para contents

private def heading (text : String) (htmlId : String) (children : Array (Block Page)) : Part Page :=
  Verso.Doc.Part.mk #[.text text] text (some { htmlId }) children #[]

private def pagePart
    (title : String)
    (content : Array (Block Page))
    (subParts : Array (Part Page) := #[]) :
    Part Page :=
  .mk #[textInline title] title none content subParts

private def bullets (items : Array (Array (Inline Page))) : Block Page :=
  .ul (items.map fun is => ⟨#[.para is]⟩)

private def htmlBlob (h : Verso.Output.Html) : Block Page :=
  Verso.Doc.Block.other (BlockExt.blob h) #[]

private def ctaBlock : Block Page :=
  htmlBlob {{
    <a class="cta-button"
       href="https://github.com/leanprover/lean-eval/issues/new?template=submit.yml">
      <span>"Submit benchmark solution"</span>
      <span aria-hidden="true">" →"</span>
    </a>
  }}

private def tldrBlock : Block Page :=
  htmlBlob {{
    <p class="submit-tldr">
      "Three steps: host your proof on GitHub or in a public gist, lay it out so CI can match each "
      <code>"Submission.lean"</code>
      " to a problem id, and open a pre-filled issue. CI runs the proof through "
      <a href="https://github.com/leanprover/comparator">"comparator"</a>
      " and updates the leaderboard automatically."
    </p>
  }}

private def step1 : Part Page :=
  heading "1. Put your proof somewhere the lean-eval CI can fetch it" "step-1" #[
    paragraph #[textInline "Accepted submission sources are URLs of one of these shapes:"],
    bullets #[
      #[textInline "a GitHub repository: ",
        codeInline "https://github.com/<owner>/<repo>"],
      #[textInline "a GitHub repository pinned to a branch, tag, or commit: ",
        codeInline "https://github.com/<owner>/<repo>/tree/<ref>",
        textInline " or ",
        codeInline "https://github.com/<owner>/<repo>/commit/<sha>"],
      #[textInline "a public gist: ",
        codeInline "https://gist.github.com/<user>/<gist-id>",
        textInline " (optionally with a revision suffix)"]
    ],
    paragraph #[
      textInline "Private GitHub repositories are supported. To use one, ",
      linkInline "install the lean-eval-bot GitHub App" "https://github.com/apps/lean-eval-bot",
      textInline " on the repository first, so that the CI can clone it."
    ],
    paragraph #[
      textInline "Secret (unlisted) gists are not supported in v1. Make your gist public, or host the proof in a repository."
    ]
  ]

private def step2 : Part Page :=
  heading "2. Lay out the proof so CI can find it" "step-2" #[
    paragraph #[
      textInline "The CI walks whatever you submit and tries every directory containing a ",
      codeInline "lakefile.toml",
      textInline " whose ",
      codeInline "name",
      textInline " field matches a benchmark problem id, and which has a ",
      codeInline "Submission.lean",
      textInline " next to it. For example:"
    ],
    bullets #[
      #[textInline "a clone of a single generated workspace from ",
        linkInline "leanprover/lean-eval/generated/" "https://github.com/leanprover/lean-eval/tree/main/generated"],
      #[textInline "a fork of leanprover/lean-eval itself with your proofs under the relevant ",
        codeInline "generated/<problem_id>/", textInline " directories"],
      #[textInline "a custom repository containing several benchmark workspaces side by side"],
      #[textInline "a gist containing a two-file minimum: a ",
        codeInline "lakefile.toml", textInline " with ",
        codeInline "name = \"<problem_id>\"", textInline " and a ",
        codeInline "Submission.lean"]
    ],
    paragraph #[
      textInline "For each matched directory the CI overlays only your ",
      codeInline "Submission.lean",
      textInline " and any files under ",
      codeInline "Submission/**/*.lean",
      textInline " onto a pristine copy of the benchmark's workspace for that problem. Every other file in your submission is ignored, including ",
      codeInline "Solution.lean", textInline ", ",
      codeInline "Challenge.lean", textInline ", or any modified ",
      codeInline "lakefile.toml", textInline ". The CI then runs ",
      linkInline "comparator" "https://github.com/leanprover/comparator",
      textInline " to check the proof."
    ]
  ]

private def step3 : Part Page :=
  heading "3. Open a submission issue" "step-3" #[
    paragraph #[
      textInline "Click ",
      linkInline "Submit benchmark solution" "https://github.com/leanprover/lean-eval/issues/new?template=submit.yml",
      textInline " to open a pre-filled issue. The form asks for two things:"
    ],
    bullets #[
      #[textInline "a submission URL in one of the shapes above"],
      #[textInline "a free-form model identifier that identifies the model or system that produced the proof"]
    ],
    paragraph #[
      textInline "When you submit the issue, the lean-eval CI takes over. It clones your content, scans for benchmark workspaces, runs comparator on every match, and records any newly-solved problems in the leaderboard repository. The CI comments on your issue with a per-problem pass/fail summary and closes it when done. Any problem that passes is added to your ",
      codeInline "results/<your-github-login>.json",
      textInline " record."
    ],
    paragraph #[
      textInline "Submissions are cumulative. Every success is sticky, and there is no limit on how many times you can submit. Resubmit whenever you have new proofs."
    ]
  ]

private def whatBecomesPublic : Part Page :=
  heading "What becomes public" "what-becomes-public" #[
    paragraph #[
      textInline "Only the information you enter on the submission form, plus the list of problems your submission solved, becomes public. Your proof is never copied out of the ephemeral workflow runner into any public artifact. The leaderboard only stores identifiers and timestamps."
    ],
    paragraph #[
      textInline "If your submission source was a public repository or a public gist, the leaderboard may link to it so that others can inspect your solution. If the source was private, no link is published."
    ]
  ]

def _root_.LeaderboardSite.Pages.Submit : VersoDoc Page :=
  .mk (fun _ => pagePart "Submit"
    #[ctaBlock, tldrBlock,
      paragraph #[
        textInline "Submissions are made by opening a GitHub issue on the ",
        linkInline "lean-eval benchmark repository" "https://github.com/leanprover/lean-eval",
        textInline "."
      ]]
    #[step1, step2, step3, whatBecomesPublic]) "{}"

end LeaderboardSite.Pages
