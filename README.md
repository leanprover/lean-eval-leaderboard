# lean-eval-leaderboard

**[View the leaderboard →](https://lean-lang.org/eval/)**

The public website for the
[lean-eval](https://github.com/leanprover/lean-eval) benchmark.

This repository builds the leaderboard site. It does **not** store the raw
results: those live in the submissions repository,
[`leanprover/lean-eval-submissions`](https://github.com/leanprover/lean-eval-submissions),
under `results/<login>.json` — its README documents the record schema and
write semantics. The deploy workflow checks that repo out and the site is
regenerated from it.

`site-data/` is the derived, presentation-oriented data consumed by the
public website. **Do not edit generated files here by hand.**

> Submitter-facing instructions live on the Verso website at
> [`LeaderboardSite/Pages/Submit.lean`](LeaderboardSite/Pages/Submit.lean).
> This README is for people building or operating the leaderboard repository,
> not for people trying to submit proofs.

## File layout

```
site-data/
  problems.json
  leaderboard.json
```

The `site-data/` directory is generated from the results store
(`leanprover/lean-eval-submissions/results/`) together with benchmark metadata
imported from the benchmark repository. Its schema is documented in
[docs/site-data-schema.md](docs/site-data-schema.md). Its files are derived
(`.gitignore`d) and produced by `scripts/generate_site_data.py`, which the
deploy workflow runs before every site build, and which local developers
invoke via `lake script run generate` (the `generate` script in
`lakefile.lean` runs the generator and then builds the site).

`generate_site_data.py` takes `--benchmark-repo` (a `leanprover/lean-eval`
checkout) and `--results-repo` (a `leanprover/lean-eval-submissions`
checkout); both default to sibling clones, or set `LEAN_EVAL_BENCHMARK_REPO` /
`LEAN_EVAL_RESULTS_REPO`. The deploy pins the benchmark clone to the commit
recorded in `benchmark-snapshot/.benchmark-commit`, so the regenerated
site-data and the checked-in snapshot's catalog stay in lockstep; the results
clone is always read at `main` HEAD.

## Results

The results store and its record schema live in
[`leanprover/lean-eval-submissions`](https://github.com/leanprover/lean-eval-submissions).
Successes are **sticky**: once a `(user, model, problem)` triple is recorded
it is never modified or removed.

<details>
<summary>Historical record-schema notes (superseded — see lean-eval-submissions)</summary>

The text below is retained for reference; the authoritative schema is the
one in the submissions repo's README.

### Record schema (v2)

```json
{
  "schema_version": 2,
  "user": "kim-em",
  "solved": {
    "Claude Opus 4.6": {
      "two_plus_two": {
        "solved_at": "2026-04-11T10:45:00Z",
        "benchmark_commit": "8e1b9cf5e1d3c2b1a0f9e8d7c6b5a4938271605f",
        "submission_repo": "kim-em/my-lean-eval-proofs",
        "submission_ref": "deadbeefcafef00dbaadc0de1234567890abcdef",
        "submission_public": true,
        "issue_number": 42
      },
      "list_append_singleton_length": {
        "solved_at": "2026-04-12T08:15:30Z",
        "benchmark_commit": "8e1b9cf5e1d3c2b1a0f9e8d7c6b5a4938271605f",
        "submission_repo": "kim-em/my-lean-eval-proofs",
        "submission_ref": "deadbeefcafef00dbaadc0de1234567890abcdef",
        "submission_public": false,
        "issue_number": 43
      }
    },
    "GPT-5.5": {
      "two_plus_two": {
        "solved_at": "2026-04-12T11:00:00Z",
        "benchmark_commit": "8e1b9cf5e1d3c2b1a0f9e8d7c6b5a4938271605f",
        "submission_repo": "kim-em/another-gist",
        "submission_ref": "0123456789abcdef0123456789abcdef01234567",
        "submission_public": true,
        "issue_number": 44
      }
    }
  }
}
```

### Top-level fields

| Field            | Type    | Description                                              |
| ---------------- | ------- | -------------------------------------------------------- |
| `schema_version` | integer | Currently `2`.                                           |
| `user`           | string  | GitHub login with original case preserved.               |
| `solved`         | object  | Map from model name to per-problem solution records. Never empty. |

### Per-model bucket

The keys of `solved` are free-form model identifiers as supplied on the
submission form (e.g. `"Claude Opus 4.7"`, `"GPT-5.5"`, `"Aristotle (Harmonic)"`).
Each value is an object mapping `<problem_id>` to a solution record.

### Per-problem solution record

| Field              | Type    | Description                                                                            |
| ------------------ | ------- | -------------------------------------------------------------------------------------- |
| `solved_at`        | string  | ISO 8601 UTC timestamp of when the record was first written.                           |
| `benchmark_commit` | string  | 40-character SHA of the `leanprover/lean-eval` commit evaluated against.               |
| `submission_repo`  | string  | Identifier of the submission source: `owner/repo` for a GitHub repository, or `user/gist-id` for a gist. |
| `submission_ref`   | string  | 40-character SHA pinning the submission at evaluation time. For repositories this is a commit SHA; for gists this is the gist revision SHA. |
| `submission_public`| boolean | `true` if the submission source was public at evaluation time, `false` otherwise. The leaderboard site uses this to decide whether to link to the solution. |
| `issue_number`     | integer | Issue number in `leanprover/lean-eval` that triggered the evaluation.                  |
| `production_description` | string \| absent | Optional free-form description of how the solution was produced. |

The `model` field has moved out of the per-problem record and become the
key of the surrounding bucket.

## Write semantics

When the lean-eval CI records a successful submission:

1. It reads `results/<login>.json`, or starts from an empty `solved` map.
2. The submission carries one model name (the value of the issue form's
   `Model` field). The CI uses that as the bucket key.
3. For each problem that passed in the submission:
   - If `solved[<model>][<problem_id>]` already exists, **do nothing** (sticky no-op).
   - Otherwise, create the model bucket if needed, and add a new record with
     the fields above.
4. If at least one new record was added, the CI commits and pushes the
   updated file. If no new records were added, it makes no commit.

The map only ever grows: existing buckets keep their problems, and existing
problem records keep their original `solved_at` timestamps and audit trail
(`benchmark_commit`, `submission_ref`, `issue_number`).

A single user can therefore claim the same problem under several model
names — one record per `(user, model, problem)` triple. This is the change
from v1, which keyed sticky records on `(user, problem)` only and so could
record at most one model per problem per user.

## Commit convention

Commits by the lean-eval CI use the message form:

```
record: <login> solved <problem_id>[, <problem_id>...] using <model> @ <benchmark_short_sha>
```

One commit per submission, grouping all newly-recorded problems for a
single model together.

### Schema evolution

Breaking changes bump `schema_version`. Consumers should refuse to parse a
file whose `schema_version` they do not know. Non-breaking additive changes
(new optional fields) keep the version number stable.

</details>

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
