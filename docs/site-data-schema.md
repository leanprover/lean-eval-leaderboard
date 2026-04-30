# Site Data Schema

This document defines the derived intermediate representation consumed by the
public lean-eval leaderboard website.

The raw `results/<login>.json` files are the public audit log. They are not a
good rendering format for the site because they are:

- per-user rather than per-leaderboard-row
- append-only and sticky
- missing benchmark problem metadata and theorem statements
- awkward for model-level aggregation

The site build should therefore generate presentation-oriented artifacts under
`site-data/`.

## Generated artifacts

The first version should generate exactly two public artifacts:

```text
site-data/
  problems.json
  leaderboard.json
```

## `site-data/problems.json`

This file is the benchmark catalog as consumed by the website.

```json
{
  "schema_version": 2,
  "generated_at": "2026-04-11T12:00:00Z",
  "benchmark": {
    "repo": "leanprover/lean-eval",
    "commit": "8e1b9cf5e1d3c2b1a0f9e8d7c6b5a4938271605f"
  },
  "problems": [
    {
      "id": "finite_graph_ramsey_theorem",
      "title": "Finite Ramsey theorem for graphs",
      "test": false,
      "submitter": "Kim Morrison",
      "module": "FormalMathEval.Combinatorics.Ramsey",
      "theorem": "finite_graph_ramsey_theorem",
      "statement": "(r s : ℕ) : ∃ n, ...",
      "notes": "States finite Ramsey existence for red/blue edge colourings...",
      "source": "Classical theorem in Ramsey theory.",
      "informal_solution": "Show that for every r and s there is an n ...",
      "challenge_path": "generated/finite_graph_ramsey_theorem",
      "sort_index": 6
    }
  ]
}
```

### Field definitions

- `schema_version`: version of this derived file format
- `generated_at`: ISO 8601 UTC timestamp of the site-data build
- `benchmark.repo`: source repository for benchmark metadata
- `benchmark.commit`: exact benchmark commit used for extraction
- `problems`: complete problem catalog

### Per-problem fields

- `id`: stable benchmark problem id
- `title`: display title
- `test`: whether this is a test/starter problem
- `submitter`: benchmark submitter
- `module`: Lean module containing the theorem
- `theorem`: Lean theorem identifier from the manifest
- `statement`: theorem statement text extracted from the benchmark source
- `notes`: optional benchmark notes
- `source`: optional citation or URL
- `informal_solution`: optional informal proof sketch
- `challenge_path`: path or URL fragment for the public challenge workspace
- `sort_index`: stable order for problem listings

## `site-data/leaderboard.json`

This file is the site-facing leaderboard representation. It is already
aggregated, ranked, and enriched with provenance and notability metadata.

```json
{
  "schema_version": 1,
  "generated_at": "2026-04-11T12:00:00Z",
  "results_repo": {
    "repo": "leanprover/lean-eval-leaderboard",
    "commit": "0123456789abcdef0123456789abcdef01234567"
  },
  "benchmark": {
    "repo": "leanprover/lean-eval",
    "commit": "8e1b9cf5e1d3c2b1a0f9e8d7c6b5a4938271605f"
  },
  "summary": {
    "models": 3,
    "submitters": 5,
    "problems": 17,
    "main_problems": 15,
    "test_problems": 2
  },
  "entries": [
    {
      "rank": 1,
      "model_id": "claude-opus-4-6",
      "model_name": "Claude Opus 4.6",
      "score": {
        "solved_total": 9,
        "solved_main": 7,
        "solved_test": 2,
        "display": "9"
      },
      "first_solved_at": "2026-04-11T10:45:00Z",
      "last_solved_at": "2026-04-15T08:10:00Z",
      "submitter_count": 2,
      "submitters": [
        {
          "user": "kim-em",
          "solved_total": 7
        },
        {
          "user": "alice",
          "solved_total": 2
        }
      ],
      "solved_problem_ids": [
        "two_plus_two",
        "list_append_singleton_length"
      ],
      "notable_problem_ids": [
        "finite_graph_ramsey_theorem",
        "rouche_logCounting_zero_eq"
      ],
      "solved_problems": [
        {
          "problem_id": "finite_graph_ramsey_theorem",
          "solved_at": "2026-04-13T12:20:00Z",
          "rarity_rank": 1,
          "rarity_score": 1000,
          "public_solution": {
            "available": true,
            "repo": "kim-em/my-lean-eval-proofs",
            "ref": "deadbeefcafef00dbaadc0de1234567890abcdef",
            "url": "https://github.com/kim-em/my-lean-eval-proofs/tree/deadbeefcafef00dbaadc0de1234567890abcdef/generated/finite_graph_ramsey_theorem"
          },
          "provenance": {
            "user": "kim-em",
            "issue_number": 42,
            "benchmark_commit": "8e1b9cf5e1d3c2b1a0f9e8d7c6b5a4938271605f",
            "submission_repo": "kim-em/my-lean-eval-proofs",
            "submission_ref": "deadbeefcafef00dbaadc0de1234567890abcdef"
          }
        }
      ]
    }
  ]
}
```

### Top-level fields

- `schema_version`: version of the derived leaderboard format
- `generated_at`: ISO 8601 UTC timestamp of artifact generation
- `results_repo`: exact results-repo commit used for the build
- `benchmark`: exact benchmark repo commit used for problem metadata
- `summary`: site-wide totals for quick rendering
- `entries`: leaderboard rows

### Leaderboard row identity

Rows are aggregated by normalized model name.

The site generator should:

1. trim surrounding whitespace
2. collapse internal whitespace runs to a single space
3. preserve original case for display
4. derive `model_id` from the normalized display string using a slug transform

Example:

- raw: `"  Claude   Opus 4.6  "`
- normalized display: `"Claude Opus 4.6"`
- `model_id`: `"claude-opus-4-6"`

The website should show one row per `model_id`, not one row per user.

### Row-level fields

- `rank`: ordinal rank after sorting and tie-breaking
- `model_id`: stable slug key for the row
- `model_name`: display name after normalization
- `score`: precomputed display score object
- `first_solved_at`: earliest solve timestamp contributing to the row
- `last_solved_at`: latest solve timestamp contributing to the row
- `submitter_count`: number of distinct users contributing solves
- `submitters`: provenance summary by user
- `solved_problem_ids`: full solved set for this row
- `notable_problem_ids`: precomputed top-10 display subset
- `solved_problems`: enriched per-problem records for detail views

### Per-solved-problem fields

- `problem_id`: benchmark problem id
- `solved_at`: earliest timestamp by which this model row established the solve
- `rarity_rank`: ordering position among this model's solved problems
- `rarity_score`: score used to compute notability
- `public_solution.available`: whether the site may link to a proof
- `public_solution.repo`: repository containing the linked proof, if public
- `public_solution.ref`: exact git ref for the linked proof, if public
- `public_solution.url`: final website-ready URL, if public
- `provenance`: first-success audit information used for this row/problem pair

## Aggregation rules

These rules resolve the mismatch between the raw append-only user records and
the model-centric site design.

### 1. Problem-level provenance for a model row

For each `(model_id, problem_id)` pair:

- collect all user-level successes whose normalized model name matches
- choose the earliest `solved_at`
- attach the provenance from that earliest success

This keeps the row stable and deterministic.

### 2. Model row solved set

The solved set for a row is the union of problem ids across all matching user
records for that normalized model.

### 3. Ranking

The first implementation should rank rows by:

1. `score.solved_total` descending
2. `score.solved_main` descending
3. `last_solved_at` ascending
4. `model_name` ascending

This can evolve later if the benchmark introduces weighted scoring, but the
derived artifact should keep a structured `score` object so the UI contract does
not need to change.

### 4. Notable problem ordering

The site brief wants expanded rows to show each model's "top 10 solved
problems", ordered by significance.

The generator should compute a `rarity_score` for each solved problem using:

1. fewer solving model rows is more notable
2. more recent first-solve date is more notable when rarity ties
3. main problems outrank test problems when otherwise tied
4. `problem_id` ascending as a final deterministic tie-break

The exact numeric formula is not user-facing. The important contract is that
`notable_problem_ids` and each item's `rarity_rank` are precomputed before the
frontend renders.

## Why the frontend should not aggregate raw results

The frontend should not derive leaderboard rows directly from `results/*.json`.
That would duplicate benchmark logic in client code and make future evolution
harder.

The frontend should treat `site-data/leaderboard.json` as authoritative for:

- ranking
- model normalization
- top-10 notable solved problems
- public-proof linking
- provenance summaries

## Evolution guidance

Additive changes may add optional fields while keeping the current `schema_version`.

Breaking changes should increment the version if they:

- rename or remove required fields
- change leaderboard row identity
- change the meaning of `score`
- change the meaning of `solved_problems` or `notable_problem_ids`

### `problems.json` version history

- `2`: renamed the per-problem `author` field to `submitter`
- `1`: initial format
