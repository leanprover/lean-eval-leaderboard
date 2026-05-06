import VersoBlog

/-!
# Site copy

Every reader-facing string on the site lives here. Page-layout files
(Pages/*.lean, Leaderboard.lean, SiteTheme.lean) read these and have no
prose literals of their own.

Two flavours of content:

* Plain `String` defs (and small formatter functions) for short labels
  embedded in hand-rolled HTML — nav, footer, hero, panel headers,
  ARIA labels, button text, fallback strings, glyphs.
* `VersoDoc Page` markdown bodies for substantial prose — the Front-page
  intro, the Problems-page intro, and each Submit-page sub-section.
  Authored as Verso markdown (the `verso (Page) "title"` term form
  defined at `.lake/packages/verso/src/verso/Verso/Doc/Concrete.lean:140`)
  so inline links read as `[label](url)` and code spans use backticks.

Layout files compose markdown bodies into Parts via `VersoDoc.toPart` and
`Part.content` — the same shape `paragraph #[textInline ...]` chains used
to produce, just authored as readable prose.

Verso markdown fence-length notes (parser quirk in v4.30.0-rc2):

* For bodies that contain a `:::name` directive (e.g. `:::htmlDiv`), the
  outer fence must be at least 5 colons. 4-colon outer + 3-colon inner
  directive trips the parser.
* For bodies with no nested directives, plain 3-colon fences are fine.
* The opening fence must be on its own line *after* the title; the
  closing fence on its own line at the end of the body.
-/

namespace LeaderboardSite.Copy

open Verso Doc Verso.Doc.Concrete Verso.Genre.Blog

/-! ## Site title / theme name -/

def siteTitle      : String := "Lean AI formalization leaderboard"
def siteThemeName  : String := "Leaderboard"

/-! ## Cross-page constants -/

def unavailable : String := "Unavailable."
def monthNames  : Array String :=
  #["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

/-! ## Topbar / nav (used by SiteTheme.lean) -/

def wordmarkMark         : String := "⊢"
def wordmarkText         : String := "lean-eval"
def navProblems          : String := "Problems"
def navSubmit            : String := "Submit"
def topbarGithubAria     : String := "View source on GitHub"
def themeToggleAria      : String := "Toggle dark mode"
def themeToggleSunGlyph  : String := "☀"
def themeToggleMoonGlyph : String := "☾"

/-! ## Footer (used by SiteTheme.lean) -/

def footerTagline               : String := "Public results for lean-eval."
def footerBenchmarkRepo         : String := "Benchmark repo"
def footerResultsRepo           : String := "Results repo"
def footerCommunityHeading      : String := "Community"
def footerLinkLean              : String := "Lean"
def footerLinkMathlibInitiative : String := "Mathlib Initiative"
def footerLinkZulip             : String := "Zulip"

/-! ## Page-title separator (SiteTheme.lean) -/

def pageTitleSeparator : String := " | "

/-! ## Hero panel (Leaderboard.lean) -/

def heroKicker : String := "lean-eval"
def heroTitle  : String := siteTitle
def heroCopy   : String :=
  "Public results on a benchmark of hard Lean formalization problems. \
   Expand any row to inspect solved theorems, extracted statements, and \
   links to public proofs when available."
def heroSide   : String :=
  "Problem statements and leaderboard results are generated from public \
   benchmark data and submitted solution artifacts. This is a \
   submission-based leaderboard: rankings reflect accepted submitted \
   solutions, not an automatic evaluation of every model on every \
   problem by the Lean FRO or benchmark organisers."

def heroBenchmarkBreakdownLabel : String := "Benchmark breakdown"
def heroMainProblemsLabel       : String := "Main problems"
def heroTestProblemsLabel       : String := "Test problems"
def heroModelsLabel             : String := "models"
def heroProblemsLabel           : String := "problems"
def heroSubmitterSingular       : String := "submitter"
def heroSubmitterPlural         : String := "submitters"
def heroProblemAuthorSingular   : String := "problem author"
def heroProblemAuthorPlural     : String := "problem authors"

/-! ## Leaderboard panel header -/

def panelKicker  : String := "Leaderboard"
def panelHeading : String := "Model rankings"
def panelNote    : String :=
  "Ranked by solved problems, with main benchmark problems weighted first."

/-! ## Empty-showcase state -/

def emptyShowcaseLabel : String := "No public solves yet"
def emptyShowcaseCopy  : String :=
  "The benchmark catalog is public, and leaderboard rows will appear here \
   as successful submissions are recorded."

/-! ## Coverage matrix -/

def coverageKicker        : String := "Coverage"
def coverageHeading       : String := "Per-problem coverage"
def coverageNote          : String :=
  "Which problems each model has solved. Hidden on narrow screens."
def coverageHeaderProblem : String := "Problem"
def coverageCellSolved    : String := "✓"
def coverageCellUnsolved  : String := "—"
def coverageKindMain      : String := "main"
def coverageKindTest      : String := "test"

/-- ARIA label for a coverage cell, e.g. `"Some title: solved"`. -/
def coverageCellAria (title : String) (solved : Bool) : String :=
  let state := if solved then "solved" else "not solved"
  s!"{title}: {state}"

/-! ## Problem chips / theorem cards -/

def proofWord                   : String := "proof"
def howProducedSummary          : String := "How produced"
def theoremStatementUnavailable : String := "Theorem statement unavailable."
def versoTheoremPreviewLabel    : String := "Verso theorem preview"
def leanTheoremStatementLabel   : String := "Lean theorem statement"

/-- ARIA label for the problem-id chip that opens the theorem-statement popover. -/
def theoremDisclosureAria (problemId : String) : String :=
  s!"Show theorem statement for {problemId}"

/-! ## Score pills -/

def scoreSolvedSuffix : String := " solved"
def scoreMainSuffix   : String := " main"
def scoreTestSuffix   : String := " test"

/-! ## Per-row entry section labels -/

def submissionHistoryLabel : String := "Submission history"
def firstSubmissionLabel   : String := "First submission"
def lastSubmissionLabel    : String := "Last submission"
def contributorsLabel      : String := "Contributors"
def uniqueSolvesLabel      : String := "Problems uniquely solved by this model"
def otherSolvesLabel       : String := "Other solved problems"
def submittersEmpty        : String := "None"

/-! ## Problems page -/

def problemsTitle                 : String := "Problems"
def filterBoxIcon                 : String := "⌕"
def filterBoxLabel                : String := "Filter problems"
def filterBoxPlaceholder          : String := "title, id, notes, source, or Lean source"
def tocAllProblemsLabel           : String := "All problems"
def mainBenchmarkSection          : String := "Main benchmark problems"
def testProblemsSection           : String := "Test problems"
def problemsNotesLabel            : String := "Notes"
def problemsInformalSolutionLabel : String := "Informal solution"
def problemsSourcePrefix          : String := "Source: "

/-- "Submitter: GitHubUser." line shown on Problems and ProblemDetail. -/
def problemsSubmitterSentence (submitter : String) : String :=
  s!"Submitter: {submitter}."

/-- Three-paragraph intro for the Problems page. The third paragraph
links to `submit/` (site-relative — the leaderboard is served under a
GitHub-Pages base path, so absolute `/submit` would 404). -/
def problemsIntro : VersoDoc Page :=
  verso (Page) "problemsIntro"
  :::
  The benchmark catalog consists of carefully curated problems across
  mathematics, chosen so that their statements are mostly accessible
  using existing Mathlib definitions, but their solutions are difficult
  for current publicly available frontier models.

  The problem statements below are automatically extracted from the
  [lean-eval](https://github.com/leanprover/lean-eval) repository.

  Authors are encouraged to submit new problems via PRs to that
  repository, for inclusion in future benchmark releases. See
  [Submit](submit/) for details on submitting solutions.
  :::

/-! ## ProblemDetail page -/

def solvedByLabel    : String := "Solved by"
def notYetSolvedText : String := "Not yet solved."
def backToProblems   : String := "← All problems"

/-- Solver-row sentence fragment: e.g. `" with GPT-5 on Apr 12, 2026"`. -/
def solverWithModelOnDate (modelName formattedDate : String) : String :=
  s!" with {modelName} on {formattedDate}"

/-! ## Front page intro

Wrapped in the existing `wrap prose page-copy` div so the home page's
full-width layout (which bypasses the theme's default prose container)
still gets the readable column. Outer fence is `:::::` because Verso
v4.30.0-rc2's parser doesn't accept a 4-colon outer with a 3-colon
inner directive. -/

def frontIntro : VersoDoc Page :=
  verso (Page) "frontIntro"
  :::::
  :::htmlDiv (class := "wrap prose page-copy")
  Welcome to `lean-eval`, a Lean formalization benchmark and public
  leaderboard.

  You can submit new problems for review, and solutions for existing
  problems. New problems will be carefully reviewed and added to future
  benchmark releases if they are accepted. Solutions are automatically
  verified using
  [comparator](https://github.com/leanprover/comparator)
  and added to the public leaderboard.

  This benchmark intends to capture hard Lean formalization problems,
  consisting of mathematical problems that are currently stateable mostly
  using existing
  [Mathlib](https://github.com/leanprover-community/mathlib4)
  definitions, perhaps with a page or so of additional setup. They should
  be hard, but usually not open problems: in fact, it's preferred if the
  problem has a known informal solution which is publicly available.

  Our hope is that at launch, the problem set will be mostly, but not
  entirely, out of reach for current publicly available frontier models,
  or simple orchestration layers built on top of these. So some genuine
  mathematical subtlety is required!

  It's also important to say what this benchmark is not: we are not
  trying to capture the ability to write readable or reusable code, or to
  follow best practices in Lean. In particular, the only requirement for
  a solution to be accepted is that it is correct and passes the
  comparator tests.
  :::
  :::::

/-! ## Submit page

The Submit page composes a top-level Part with named sub-Parts whose
`htmlId`s (`step-1`, `step-2`, `step-3`, `what-becomes-public`) are
referenced from CSS / anchors. We keep that Part composition in
`Submit.lean` and only export the per-section *bodies* here, so the ids
can't drift from markdown heading-id generation. -/

def submitTitle : String := "Submit"

/-- Lead paragraph above the step sub-sections. -/
def submitLeadBody : VersoDoc Page :=
  verso (Page) "submitLead"
  :::
  Submissions are made by opening a GitHub issue on the
  [lean-eval benchmark repository](https://github.com/leanprover/lean-eval).
  :::

def submitStep1Title  : String :=
  "1. Put your proof somewhere the lean-eval CI can fetch it"
def submitStep1HtmlId : String := "step-1"

def submitStep1Body : VersoDoc Page :=
  verso (Page) "submitStep1"
  :::
  Accepted submission sources are URLs of one of these shapes:

  - a GitHub repository: `https://github.com/<owner>/<repo>`
  - a GitHub repository pinned to a branch, tag, or commit:
    `https://github.com/<owner>/<repo>/tree/<ref>` or
    `https://github.com/<owner>/<repo>/commit/<sha>`
  - a public gist: `https://gist.github.com/<user>/<gist-id>`
    (optionally with a revision suffix)

  Private GitHub repositories are supported. To use one,
  [install the lean-eval-bot GitHub App](https://github.com/apps/lean-eval-bot)
  on the repository first, so that the CI can clone it.

  Secret (unlisted) gists are not supported in v1. Make your gist public,
  or host the proof in a repository.
  :::

def submitStep2Title  : String := "2. Lay out the proof so CI can find it"
def submitStep2HtmlId : String := "step-2"

def submitStep2Body : VersoDoc Page :=
  verso (Page) "submitStep2"
  :::
  The CI walks whatever you submit and tries every directory containing a
  `lakefile.toml` whose `name` field matches a benchmark problem id, and
  which has a `Submission.lean` next to it. For example:

  - a clone of a single generated workspace from
    [leanprover/lean-eval/generated/](https://github.com/leanprover/lean-eval/tree/main/generated)
  - a fork of leanprover/lean-eval itself with your proofs under the
    relevant `generated/<problem_id>/` directories
  - a custom repository containing several benchmark workspaces side by
    side
  - a gist containing a two-file minimum: a `lakefile.toml` with
    `name = "<problem_id>"` and a `Submission.lean`

  For each matched directory the CI overlays only your `Submission.lean`
  and any files under `Submission/**/*.lean` onto a pristine copy of the
  benchmark's workspace for that problem. Every other file in your
  submission is ignored, including `Solution.lean`, `Challenge.lean`, or
  any modified `lakefile.toml`. The CI then runs
  [comparator](https://github.com/leanprover/comparator) to check the
  proof.
  :::

def submitStep3Title  : String := "3. Open a submission issue"
def submitStep3HtmlId : String := "step-3"

def submitStep3Body : VersoDoc Page :=
  verso (Page) "submitStep3"
  :::
  Click [Submit benchmark solution](https://github.com/leanprover/lean-eval/issues/new?template=submit.yml)
  to open a pre-filled issue. The form asks for two things:

  - a submission URL in one of the shapes above
  - a free-form model identifier that identifies the model or system that
    produced the proof

  When you submit the issue, the lean-eval CI takes over. It clones your
  content, scans for benchmark workspaces, runs comparator on every
  match, and records any newly-solved problems in the leaderboard
  repository. The CI comments on your issue with a per-problem pass/fail
  summary and closes it when done. Any problem that passes is added to
  your `results/<your-github-login>.json` record.

  Submissions are cumulative. Every success is sticky, and there is no
  limit on how many times you can submit. Resubmit whenever you have new
  proofs.
  :::

def submitWhatPublicTitle  : String := "What becomes public"
def submitWhatPublicHtmlId : String := "what-becomes-public"

def submitWhatPublicBody : VersoDoc Page :=
  verso (Page) "submitWhatPublic"
  :::
  Only the information you enter on the submission form, plus the list of
  problems your submission solved, becomes public. Your proof is never
  copied out of the ephemeral workflow runner into any public artifact.
  The leaderboard only stores identifiers and timestamps.

  If your submission source was a public repository or a public gist, the
  leaderboard may link to it so that others can inspect your solution. If
  the source was private, no link is published.
  :::

/-! ### Submit-page CTA + TL;DR widgets

`Submit.lean` keeps the bespoke HTML wrappers (`<a class="cta-button">`,
`<p class="submit-tldr">`) and reads its labels from here. The TL;DR
paragraph splices a `<code>` and an `<a>` mid-sentence, so its prose is
broken into chunks rather than authored as a single string. -/

def submitCtaUrl    : String :=
  "https://github.com/leanprover/lean-eval/issues/new?template=submit.yml"
def submitCtaLabel  : String := "Submit benchmark solution"
def submitCtaArrow  : String := " →"

def submitTldrPart1 : String :=
  "Three steps: host your proof on GitHub or in a public gist, lay it \
   out so CI can match each "
def submitTldrCode1 : String := "Submission.lean"
def submitTldrPart2 : String :=
  " to a problem id, and open a pre-filled issue. CI runs the proof \
   through "
def submitTldrComparatorLabel : String := "comparator"
def submitTldrComparatorUrl   : String :=
  "https://github.com/leanprover/comparator"
def submitTldrPart3 : String :=
  " and updates the leaderboard automatically."

end LeaderboardSite.Copy
