# Split leaderboard site-data v2

`site-data/v2/` is the lifecycle-aware leaderboard's versioned browser
interface. The compatibility `problems.json`/`leaderboard.json` files remain
available to the preserved `/legacy/` surface and downstream consumers.

The generator reads the public State `materialized/domain.json`, never the
append-only events. It joins submissions, results, replay tasks, and release
tasks into one normalized solution view, then supplements presentation-only
catalog fields from the pinned benchmark checkout. If no State projection is
provided, immutable base results are adapted instead. Every fallback appears
in each payload's `data_limitations`; missing replay and release data is emitted
as an explicit `unavailable` state rather than omitted or guessed.

The split files are:

- `index.json`: small group index, source pins, and feed locations;
- `groups/<group>.json`: policy, scopes, tags, problem summaries, normalized
  credits, and default-scope standings for exactly one group;
- `problems/<id>.json`: lifecycle/status history, statement revisions, named
  sets, all base solutions, metadata provenance, replay measurements, and
  release state;
- `recent-solutions.json` and `recent-solutions.xml`: global chronological
  accepted-solution feeds.

The authoritative structural contract is
[`schemas/site-data-v2.schema.json`](../schemas/site-data-v2.schema.json).

## Credit and ordering

An alias table maps declared labels to canonical credit identities before
aggregation. Multiple base results that collide on `(canonical identity,
problem)` retain their individual problem-page records but contribute one
standings solve. Acceptance order is `(accepted_at, acceptance_event_id,
result_id)`, so tied timestamps have a deterministic first solve. Unique means
that exactly one canonical identity solved the problem in the selected scope;
first means earliest acceptance order; total means distinct solved problems.
The default order is unique, then first, then total.

Standings are built and filtered inside one group payload. There is no
cross-group score or ranking.

## Scope and URLs

The newest published frozen set is the group's flagship/default scope. Before
a group has a frozen set, draft is its explicit fallback. Tag filters and a
non-default scope or ordering persist in the query string.

The lifecycle-aware problem views own the stable `/problems/<id>/` routes,
preserving the public `/eval/problems/<id>/` URLs under the site's mount point.
The previous server-rendered leaderboard remains available under `/legacy/`
for comparison and rollback diagnosis. The v2 client constructs untrusted
content with `textContent`, and RSS text is XML-escaped.

## Local fixture boundary

Production State currently lacks lifecycle histories and model-alias amendment
views. `tests/fixtures/preview-domain-v1.json` exercises the complete adapter
contract locally. It is loaded only via the explicit `--preview-fixture` flag
and can never be inferred by a deploy build.

Example local generation:

```bash
python3 scripts/generate_site_data.py \
  --no-write-snapshot \
  --benchmark-repo ../lean-eval \
  --results-repo ../lean-eval-submissions \
  --state-domain ../lean-eval-state/materialized/domain.json \
  --state-repo ../lean-eval-state
```
