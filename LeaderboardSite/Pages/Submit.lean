import VersoBlog

open Verso.Genre.Blog

#doc (Page) "Submit" =>

Submissions are made by opening a GitHub issue on the
[lean-eval benchmark repository](https://github.com/leanprover/lean-eval).

# 1. Put your proof somewhere the lean-eval CI can fetch it

Accepted submission sources are URLs of one of these shapes:

* a GitHub repository: `https://github.com/<owner>/<repo>`
* a GitHub repository pinned to a branch, tag, or commit:
  `https://github.com/<owner>/<repo>/tree/<ref>` or
  `https://github.com/<owner>/<repo>/commit/<sha>`
* a public gist: `https://gist.github.com/<user>/<gist-id>` (optionally with
  a revision suffix)

Private GitHub repositories are supported. To use one, install the
`lean-eval-bot` GitHub App on the repository first, so that the CI can clone
it. The install link is in the
[lean-eval README](https://github.com/leanprover/lean-eval).

Secret (unlisted) gists are not supported in v1. Make your gist public, or
host the proof in a repository.

# 2. Lay out the proof so CI can find it

The CI walks whatever you submit and tries every directory containing a
`lakefile.toml` whose `name` field matches a benchmark problem id, and which
has a `Submission.lean` next to it. For example:

* a clone of a single generated workspace from
  [leanprover/lean-eval/generated/](https://github.com/leanprover/lean-eval/tree/main/generated)
* a fork of leanprover/lean-eval itself with your proofs under the relevant
  `generated/<problem_id>/` directories
* a custom repository containing several benchmark workspaces side by side
* a gist containing a two-file minimum: a `lakefile.toml` with
  `name = "<problem_id>"` and a `Submission.lean`

For each matched directory the CI overlays only your `Submission.lean` and
any files under `Submission/**/*.lean` onto a pristine copy of the benchmark's
workspace for that problem. Every other file in your submission is ignored,
including `Solution.lean`, `Challenge.lean`, or any modified `lakefile.toml`.
The CI then runs [comparator](https://github.com/leanprover/comparator) to
check the proof.

# 3. Open a submission issue

Click
[Submit benchmark solution](https://github.com/leanprover/lean-eval/issues/new?template=submit.yml)
to open a pre-filled issue. The form asks for two things:

* a submission URL in one of the shapes above
* a free-form model identifier that identifies the model or system that
  produced the proof

When you submit the issue, the lean-eval CI takes over. It clones your
content, scans for benchmark workspaces, runs comparator on every match, and
records any newly-solved problems in the leaderboard repository. The CI
comments on your issue with a per-problem pass/fail summary and closes it
when done. Any problem that passes is added to your
`results/<your-github-login>.json` record.

Submissions are cumulative. Every success is sticky, and there is no limit
on how many times you can submit. Resubmit whenever you have new proofs.

# What becomes public

Only the information you enter on the submission form, plus the list of
problems your submission solved, becomes public. Your proof is never copied
out of the ephemeral workflow runner into any public artifact. The
leaderboard only stores identifiers and timestamps.

If your submission source was a public repository or a public gist, the
leaderboard may link to it so that others can inspect your solution. If the
source was private, no link is published.
