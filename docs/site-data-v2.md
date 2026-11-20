# Lifecycle-aware leaderboard site-data

`site-data/v2/` is the lifecycle-aware leaderboard's browser interface, using
wire schema version 2. The compatibility `problems.json`/`leaderboard.json`
files remain available to the preserved `/legacy/` surface and downstream
consumers.

The production generator reads State's redacted
v7 or v8 public projection, never the private append-only events or
internal `materialized/domain.json`. The public artifact contains recorded
results, public lifecycle evidence, result amendments, model-identity review
history, and locator-free historical replay series or reviewed-unavailable
dispositions only. It excludes pending/rejected submissions, submission IDs,
source and archive locators, profile locators, credentials, and authentication
nonces. Its source State commit, canonical event digest, and event count make
the bytes reproducible by an authorized auditor. Presentation-only catalog
fields come from the pinned benchmark checkout. If no State projection is
provided, immutable base results are adapted instead. Every fallback appears
in each payload's `data_limitations`; missing replay and release data is emitted
as an explicit `unavailable` state rather than omitted or guessed.

Historical entries join to immutable base Results by `result_id`. The adapter
rejects unknown Results, source-visibility mismatches, duplicate series,
cross-lane series, and any replay/disposition overlap. It displays the newest
series status and retains every versioned measurement series with its exact
measurement-configuration and execution-profile digests. Reviewed
unavailability supplies a public reason and no fabricated measurement.

Projection v8 distinguishes `fetch_method` (`git` or `archive`) from the original
`source_visibility`. Recovering an originally public source from its archive
therefore retains public visibility and uses the archive replay profile link.
It does not introduce an archive locator or publish a solution. Reviewed
`archive_permanently_unrecoverable` dispositions require the archive method and
the exact reviewed rationale; earlier projection formats retain their existing
field sets and behavior.
An originally private v8 archive measurement retains its exact profile digest
without a profile URL: the redacted format cannot distinguish legacy private
profiles from newer archive profiles. Older projection formats retain their
existing private profile links.

Before running State's projector, deployment verifies the complete, clean
production checkout against exactly two code contracts: legacy
`e2dd6314f04df175966ff105709b855053949d97` (v7), or archive-capable
`351b1c409290516bfa379fc857908908e1d08932` (v8). The closed map in
`scripts/state_contracts.py` binds complete scripts/schema trees and critical
file modes, blobs and SHA-256s, including the new archive runtime dependency.
Data-only descendants are allowed; mixed or unknown code is rejected before
it can execute. No new State credential or publication authority is added.

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

State aliases map the exact `(lowercase owner, verbatim declared label)` pair to
an approved identity, then follow same-owner consolidation links to its current
canonical identity. Renames change only the displayed canonical label. Multiple
base results that resolve to the same `(canonical identity, problem)` retain
their individual problem-page records but contribute one standings solve.
Results without a reviewed State alias retain the legacy normalized-label
fallback. Acceptance order is `(accepted_at, acceptance_event_id, result_id)`,
so tied timestamps have a deterministic first solve. Unique means that exactly
one canonical identity solved the problem in the selected scope; first means
earliest acceptance order; total means distinct solved problems. The default
order is unique, then first, then total.

Standings are built and filtered inside one group payload. There is no
cross-group score or ranking.

## Catalog history

Problem lifecycle history comes from the pinned benchmark manifest's
append-only `status_history` and `revision_history` tables. The projection
preserves each calendar date, reason category, and statement digest exactly.
Revision rows are labeled `superseded` except for the terminal revision, which
must equal the manifest's current `statement_revision` and is labeled
`current`. The terminal status row must likewise equal `current_status`.

The initial catalog migration intentionally has no synthetic history rows. If
a problem manifest has no recorded history, its history arrays remain empty;
the separately projected current status and statement revision remain visible,
and the problem payload records the limitation. Presentation-only test fixtures
are used only when the canonical manifest has no history.

## Scope and URLs

The newest published frozen set is the group's flagship/default scope. Before
a group has a frozen set, draft is its explicit fallback. Tag filters and a
non-default scope or ordering persist in the query string.

The lifecycle-aware problem views own the stable `/problems/<id>/` routes,
preserving the public `/eval/problems/<id>/` URLs under the site's mount point.
The previous server-rendered leaderboard remains available under `/legacy/`
for comparison and rollback diagnosis. The lifecycle-aware client constructs
untrusted content with `textContent`, and RSS text is XML-escaped.

## Publication monitoring

The scheduled refresh compares the live State revision in `v2/index.json`, the
Results revision in `leaderboard.json`, and the repository's pinned benchmark
revision. It also requires both public snapshots to have matching generation
timestamps and benchmark pins. An active production Pages run suppresses duplicate
dispatches. A stale publication following a failed deployment dispatches a recovery
and fails the monitor so that the outage is visible in Actions.

Before generating any public data, the generator requires the statement revisions
in `generated/index.json` to match the authored manifests. Source changes can notify
the snapshot workflow before regeneration finishes; this guard prevents publishing
an old generated statement under a new revision number.

The deploy job enables Git's `fetch.prune` before either Lake dependency update.
This removes deleted remote branches from cached dependency checkouts before they
can conflict with new branch names.

## Local fixture boundary

State owns model-identity review and alias policy; it does not own catalog
lifecycle histories. The fixture's aliases exercise fallback presentation when
no State projection is supplied.
`tests/fixtures/preview-domain-schema-version-1.json` exercises those
presentation-only fixtures locally. It is loaded only via the explicit
`--preview-fixture` flag
and can never be inferred by a deploy build.

Example local generation:

```bash
python3 scripts/generate_site_data.py \
  --no-write-snapshot \
  --benchmark-repo ../lean-eval \
  --results-repo ../lean-eval-submissions \
  --state-projection /tmp/lean-eval-public-state.json \
  --state-repo ../lean-eval-state
```
