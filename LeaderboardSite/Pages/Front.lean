import VersoBlog

open Verso.Genre.Blog

#doc (Page) "Lean AI formalization leaderboard" =>

Welcome to `lean-eval`,
a Lean formalization benchmark and public leaderboard.

You can submit new problems for review, and solutions for existing problems.
New problems will be carefully reviewed
and added to future benchmark releases if they are accepted.
Solutions are automatically verified using [comparator](https://github.com/leanprover/comparator)
and added to the public leaderboard.

This benchmark intends to capture hard Lean formalization problems,
consisting of mathematical problems that are currently stateable
mostly using existing [Mathlib](https://github.com/leanprover-community/mathlib4) definitions,
perhaps with a page or so of additional setup.
They should be *hard*, but usually not *open* problems:
in fact, it's preferred if the problem has a known informal solution which is publicly available.

Our hope is that at launch,
the problem set will be mostly, but not entirely,
out of reach for current publicly available frontier models,
or simple orchestration layers built on top of these.
So some genuine mathematical subtlety is required!
