# Compute reporting on problem pages

Each accepted solution separates **Measured by LeanEval** from **Production
information — self-reported**. Build/export and checker elapsed times are labeled
**very noisy**. Retired instruction counts are shown when available; unavailable
counters have an explanation. Counts are userspace instructions across child
processes and remain dependent on architecture, toolchain, and cache setup.

The two sortable comparison views compare solutions within a problem. Numeric
zero is distinct from a missing value, and missing values sort last in either
direction. Statement revision and measurement setup remain visible. The preferred
measurement is an available acceptance measurement, otherwise the latest
successful replay; the site never selects the fastest attempt. Expandable details
retain other attempts and link the original reference profile. Standings and
leaderboard ranking rules are unchanged.

Production time, total/cached input tokens, output tokens and estimated
API-equivalent cost are per-problem reports including unsuccessful attempts.
Shared-run totals belong in notes. Billing mode describes how the submitter paid,
not the meaning of the cost estimate. Values are labeled as self-reported and
each field shows the date it actually changed. Unchanged fields retain their
original dates; removed and superseded metadata text is not republished. The owner edit link
carries a public result ID and exact Results commit; GitHub authorization happens
at the submission service and no private submission ID appears in the public link.

This consumer requests public State projection **v7**. Merge the production State
producer and staging/production Worker contracts before deploying it. Earlier
public projection schemas remain vendored and unchanged; the compatibility tests
continue to exercise them. The generator consumes redacted public State only. Optional acceptance receipts
that are missing from the Results snapshot, malformed, duplicated or mismatched
are skipped with a diagnostic, so they cannot block accepted-result publication.

Validation covers real-data generation/schema validation, safe DOM rendering,
comparison ordering and measurement preference, metadata provenance, and schema
compatibility. The receipt fixture is shared with the submission recorder and
State producer. The Node behavior tests run alongside the existing Python tests
in Pages CI.
