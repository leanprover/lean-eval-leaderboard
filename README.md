# lean-eval-leaderboard

Results store and public website data source for the
[lean-eval](https://github.com/leanprover/lean-eval) benchmark.

This repository holds machine-written artifacts produced by the lean-eval CI
and by the leaderboard-site build pipeline.

- `results/` is the append-only public success log written by lean-eval CI.
- `site-data/` is the derived, presentation-oriented data consumed by the
  public website.

**Do not edit generated files here by hand.**

Successes are **sticky**: once a problem is marked solved for a given user,
that record is never modified or removed, even if a later submission from the
same user no longer proves it.

> Submitter-facing instructions live on the Verso website at
> [`LeaderboardSite/Pages/Submit.lean`](LeaderboardSite/Pages/Submit.lean).
> This README is for people building or operating the leaderboard repository,
> not for people trying to submit proofs.

## File layout

```
results/
  <github-login>.json

site-data/
  problems.json
  leaderboard.json
```

One file per submitter. Users without any successful submission have no file.
Filenames use the user's GitHub login, lowercased, since GitHub logins are
case-insensitive.

The `site-data/` directory is generated from the raw `results/` files together
with benchmark metadata imported from the benchmark repository. Its schema is
documented in [docs/site-data-schema.md](docs/site-data-schema.md).

## Record schema (v1)

```json
{
  "schema_version": 1,
  "user": "kim-em",
  "solved": {
    "two_plus_two": {
      "solved_at": "2026-04-11T10:45:00Z",
      "benchmark_commit": "8e1b9cf5e1d3c2b1a0f9e8d7c6b5a4938271605f",
      "submission_repo": "kim-em/my-lean-eval-proofs",
      "submission_ref": "deadbeefcafef00dbaadc0de1234567890abcdef",
      "submission_public": true,
      "model": "Claude Opus 4.6",
      "issue_number": 42
    },
    "list_append_singleton_length": {
      "solved_at": "2026-04-12T08:15:30Z",
      "benchmark_commit": "8e1b9cf5e1d3c2b1a0f9e8d7c6b5a4938271605f",
      "submission_repo": "kim-em/my-lean-eval-proofs",
      "submission_ref": "deadbeefcafef00dbaadc0de1234567890abcdef",
      "submission_public": false,
      "model": "Claude Opus 4.6",
      "issue_number": 43
    }
  }
}
```

### Top-level fields

| Field            | Type    | Description                                              |
| ---------------- | ------- | -------------------------------------------------------- |
| `schema_version` | integer | Currently `1`.                                           |
| `user`           | string  | GitHub login with original case preserved.              |
| `solved`         | object  | Map from problem id to solution record. Never empty.    |

### Per-problem solution record

| Field              | Type    | Description                                                                            |
| ------------------ | ------- | -------------------------------------------------------------------------------------- |
| `solved_at`        | string  | ISO 8601 UTC timestamp of when the record was first written.                           |
| `benchmark_commit` | string  | 40-character SHA of the `leanprover/lean-eval` commit evaluated against.               |
| `submission_repo`  | string  | Identifier of the submission source: `owner/repo` for a GitHub repository, or `user/gist-id` for a gist. |
| `submission_ref`   | string  | 40-character SHA pinning the submission at evaluation time. For repositories this is a commit SHA; for gists this is the gist revision SHA. |
| `submission_public`| boolean | `true` if the submission source was public at evaluation time, `false` otherwise. The leaderboard site uses this to decide whether to link to the solution. |
| `model`            | string  | Free-form model identifier supplied by the submitter on the submission form.           |
| `issue_number`     | integer | Issue number in `leanprover/lean-eval` that triggered the evaluation.                  |

## Write semantics

When the lean-eval CI records a successful submission:

1. It reads `results/<login>.json`, or starts from an empty `solved` map.
2. For each problem that passed in the submission:
   - If `solved[<problem_id>]` already exists, **do nothing** (sticky no-op).
   - Otherwise, add a new record with the fields above.
3. If at least one new record was added, the CI commits and pushes the updated
   file. If no new records were added, it makes no commit.

The `solved` map only ever grows. The original `solved_at` timestamp is
preserved, and the audit trail (`benchmark_commit`, `submission_ref`,
`issue_number`) always refers to the run that first established the success.

## Commit convention

Commits by the lean-eval CI use the message form:

```
record: <login> solved <problem_id>[, <problem_id>...] @ <benchmark_short_sha>
```

One commit per submission, grouping all newly-recorded problems together.

## Schema evolution

Breaking changes bump `schema_version`. Consumers should refuse to parse a
file whose `schema_version` they do not know. Non-breaking additive changes
(new optional fields) keep the version number stable.

## Website build direction

The public website should live in this repository and consume derived artifacts
from `site-data/`, not the raw `results/` tree directly. The site itself will
be implemented in Verso.

- Raw results preserve audit information and sticky solve history.
- Derived site data resolves aggregation rules, ranking, and problem metadata.
- The frontend should render `site-data/leaderboard.json` and
  `site-data/problems.json` without re-implementing benchmark logic in the
  browser.

See:

- [docs/site-data-schema.md](docs/site-data-schema.md)
- [docs/website-plan.md](docs/website-plan.md)
