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
  "Public results on a benchmark of hard Lean formalization problems, \
   based on solutions submitted by external participants. Expand any row \
   to inspect solved theorems, extracted statements, and links to public \
   proofs when available."
def heroSide   : String :=
  "This is a submission-based leaderboard. All results come from solution \
   artifacts submitted by external participants; the Lean FRO does not run \
   models against these problems itself. Rankings reflect accepted \
   submitted solutions, not an automatic evaluation of every model on \
   every problem."

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
  "Ranked by main benchmark problems solved. Internal test problems do \
   not count toward the score."

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

def howProducedSummary          : String := "How produced"
def theoremStatementUnavailable : String := "Theorem statement unavailable."
def versoTheoremPreviewLabel    : String := "Verso theorem preview"
def leanTheoremStatementLabel   : String := "Lean theorem statement"

/-- ARIA label for the problem-id chip that opens the theorem-statement popover. -/
def theoremDisclosureAria (problemId : String) : String :=
  s!"Show theorem statement for {problemId}"

/-! ## Score line -/

def scoreSolvedSuffix : String := " solved"

/-! ## Per-row entry section labels -/

def submissionHistoryLabel : String := "Submission history"
def firstSubmissionLabel   : String := "First submission"
def lastSubmissionLabel    : String := "Last submission"
def contributorsLabel      : String := "Contributors"
def uniqueSolvesLabel      : String := "Problems uniquely solved by this model"
def otherSolvesLabel       : String := "Other solved problems"
def submittersEmpty        : String := "None"

/-- One muted line summarising test-problem solves inside an expanded
entry, e.g. `"Test problems: two_plus_two, foo (2 / 5 solved)"`. Test
problems are internal fixtures and are not counted toward the score. -/
def testSolvesLine (ids : String) (solved total : Nat) : String :=
  s!"Test problems: {ids} ({solved} / {total} solved)"

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

  I'd like to acknowledge the use of Aristotle, Claude Code, and Codex in
  the preparation of many of the problems here. In particular I should
  point out that Aristotle has a handicap on the leaderboard: typically,
  if a single query to Aristotle could resolve a problem, I would deem it
  too easy and drop it from consideration for the eval set. I think it's a
  testament to the public service that Aristotle provides that this is
  both possible, and useful!
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
  Production server intake is not enabled yet. Until launch, submit through the
  [current GitHub issue form](https://github.com/leanprover/lean-eval-submissions/issues/new?template=submit.yml).

  At launch, the authenticated submission application will be hosted at
  [lean-eval-submission-server.lean-eval.workers.dev](https://lean-eval-submission-server.lean-eval.workers.dev/).
  This separate origin is intentional: GitHub OAuth callbacks and the
  application session are scoped to the Worker that handles private intake.
  The launch overlap will begin only after server intake launches, will last
  at least four weeks, and will keep the current GitHub issue form available
  as a fallback.
  After submitting, you can
  [return to the leaderboard](https://lean-lang.org/eval/).
  :::

def submitStep1Title  : String :=
  "1. Submit through the current issue-intake path"
def submitStep1HtmlId : String := "step-1"

def submitStep1Body : VersoDoc Page :=
  verso (Page) "submitStep1"
  :::
  Until production server launch, use the
  [current GitHub issue form](https://github.com/leanprover/lean-eval-submissions/issues/new?template=submit.yml)
  and follow the instructions there. It is the working submission path while
  server intake remains disabled.
  :::

def submitStep2Title  : String := "2. Prepare for authenticated intake at launch"
def submitStep2HtmlId : String := "step-2"

def submitStep2Body : VersoDoc Page :=
  verso (Page) "submitStep2"
  :::
  At launch, submissions through the authenticated service will
  require a private GitHub repository in `owner/repository` form and the exact
  40-character source commit to evaluate. Before using it,
  [install the Lean Eval Source Reader GitHub App](https://github.com/apps/lean-eval-source-reader)
  on that repository so that LeanEval can clone it. You will then
  [continue to the secure submission service](https://lean-eval-submission-server.lean-eval.workers.dev/),
  sign in with GitHub, choose the source, and identify the model or system that
  produced the proof. The application will walk the submitted source and
  try every directory containing a
  `lakefile.toml` whose `name` field matches a benchmark problem id, and
  which has a `Submission.lean` next to it. For example:

  - a clone of a single generated workspace from
    [leanprover/lean-eval/generated/](https://github.com/leanprover/lean-eval/tree/main/generated)
  - a fork of leanprover/lean-eval itself with your proofs under the
    relevant `generated/<problem_id>/` directories
  - a custom repository containing several benchmark workspaces side by
    side

  For each matched directory LeanEval overlays only your `Submission.lean`
  and any files under `Submission/**/*.lean` onto a pristine copy of the
  benchmark's workspace for that problem. Every other file in your
  submission is ignored, including `Solution.lean`, `Challenge.lean`, or
  any modified `lakefile.toml`. The CI then runs
  [comparator](https://github.com/leanprover/comparator) to check the
  proof.

  Before evaluation, LeanEval records the exact source revision and digest
  and stores a private encrypted archive bound to that submission. Submission
  source and credentials are not exposed through public workflow artifacts or
  logs.
  :::

def submitStep3Title  : String := "3. Review authenticated-intake release terms"
def submitStep3HtmlId : String := "step-3"

def submitStep3Body : VersoDoc Page :=
  verso (Page) "submitStep3"
  :::
  After server launch, the authenticated submission action will include this
  acknowledgement:

  > By submitting, I confirm that I have authority to provide this source. I authorize Lean Eval to store and run it privately for evaluation and publish evaluation metadata and results. I will not submit secrets or material I am not authorized to disclose. If I choose scheduled release, I also confirm that I have authority to license the accepted source under the Apache License 2.0 and authorize Lean Eval to publish it two UTC calendar months after acceptance.

  For authenticated submissions after launch, scheduled release will be the
  default. A submitter may instead choose to keep accepted source private; the
  public result remains visible with its solution marked as withheld. If the
  initial choice is private, the submitter may later authorize scheduled
  release with the same license confirmation. That change is irreversible: a
  scheduled choice cannot be changed back to private.
  :::

def submitWhatPublicTitle  : String := "What becomes public, and when"
def submitWhatPublicHtmlId : String := "what-becomes-public"

def submitWhatPublicBody : VersoDoc Page :=
  verso (Page) "submitWhatPublic"
  :::
  The following release policy will apply to submissions made through the
  authenticated application after launch. Submissions through the current
  issue-intake path retain their existing policy.

  Submission metadata and evaluation results may become public when the result
  is recorded. Private source remains in the encrypted archive during the
  release delay.

  If you choose scheduled release, LeanEval automatically publishes the exact
  accepted `Submission.lean` and files under `Submission/` under the Apache
  License 2.0 two UTC calendar months after acceptance. Repository metadata,
  credentials, challenge files, modified build files, and unrelated source
  files are not included in that release.

  Only schedule files that you have authority to provide and license. Do not
  include secrets. If you choose to keep accepted source private, the public
  leaderboard keeps the evaluation result but shows that the solution is
  withheld. You may later schedule release; that transition is irreversible,
  and scheduled release cannot later be changed to private.
  :::

/-! ### Submit-page CTA + TL;DR widgets

`Submit.lean` keeps the bespoke HTML wrappers (`<a class="cta-button">`,
`<p class="submit-tldr">`) and reads its labels from here. The TL;DR
paragraph splices a `<code>` and an `<a>` mid-sentence, so its prose is
broken into chunks rather than authored as a single string. -/

def submitCtaUrl    : String :=
  "https://github.com/leanprover/lean-eval-submissions/issues/new?template=submit.yml"
def submitCtaLabel  : String :=
  "Submit using the current GitHub issue form"
def submitCtaArrow  : String := " →"

def submitTldrPart1 : String :=
  "Until production server launch, use the GitHub issue form to submit each matching "
def submitTldrCode1 : String := "Submission.lean"
def submitTldrPart2 : String :=
  ". LeanEval verifies each proof with "
def submitTldrComparatorLabel : String := "comparator"
def submitTldrComparatorUrl   : String :=
  "https://github.com/leanprover/comparator"
def submitTldrPart3 : String :=
  " before recording an accepted result."

end LeaderboardSite.Copy
