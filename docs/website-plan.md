# Website Plan

This document turns the current design brief into an implementation sequence for
the public leaderboard site.

## Repo split

- `leanprover/lean-eval`
  - benchmark source of truth
  - theorem extraction
  - generated challenge workspaces
  - evaluation pipeline
- `leanprover/lean-eval-leaderboard`
  - public results store
  - derived website data under `site-data/`
  - Verso website

The site should live in `leanprover/lean-eval-leaderboard`.

## Data flow

1. Read raw `results/*.json` from this repo.
2. Import benchmark metadata from `leanprover/lean-eval` at a pinned commit.
3. Extract theorem statements and problem metadata into `site-data/problems.json`.
4. Aggregate raw success records into `site-data/leaderboard.json`.
5. Render the Verso site from `site-data/*.json`.

## First milestone

The first milestone should produce a static site with:

- homepage hero
- compact leaderboard rows
- expandable row details
- theorem-statement popovers
- public-solution links when allowed

The homepage should be the dominant artifact. Secondary pages can follow.

## Verso structure

A reasonable first scaffold is:

```text
lakefile.lean
lean-toolchain
LeaderboardSite.lean
SiteTheme.lean
LeaderboardSite/
  Data.lean
  Pages/
    Front.lean
    Benchmark.lean
    Problems.lean
static/
  style.css
  background.svg
  background.js
```

## Build responsibilities

The site build should be split into two phases:

### Phase 1: data preparation

- validate raw `results/*.json`
- normalize model names
- compute model rows, ranks, and notable-problem ordering
- pull benchmark metadata and theorem statements
- write `site-data/problems.json`
- write `site-data/leaderboard.json`

### Phase 2: site generation

- read `site-data/*.json`
- render the Verso pages
- emit a static site directory

## Design translation

The design brief in the benchmark repo should map into the site as follows:

- dark charcoal base with restrained teal accents
- proof-structure background motif behind content
- monospace used for theorem statements and technical metadata
- thin linework and restrained panel styling
- no startup-style gradients or loud dashboard chrome

The main visual object should be the leaderboard itself, not an oversized hero.

## Open implementation choices

These choices can be deferred until after the schema and first mockup land:

- whether benchmark metadata is fetched live during build or committed as a
  pinned snapshot
- whether the hex-grid background is pure SVG/CSS or lightly animated with JS
- whether theorem popovers are pure CSS/HTML or need a small custom script

## Immediate next coding steps

1. Scaffold the Verso site package in this repo.
2. Add a generator that writes `site-data/problems.json` and
   `site-data/leaderboard.json`.
3. Build the homepage against mock or sample data first.
4. Replace the sample data with the real generated artifacts.
