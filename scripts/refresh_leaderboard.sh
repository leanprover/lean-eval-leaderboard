#!/usr/bin/env bash
# Compare all published input revisions, including legacy issue Results.
set -euo pipefail

repository="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY must name the leaderboard repository}"
current_state="$(git -C "${1:-lean-eval-state}" rev-parse HEAD)"
current_results="$(gh api repos/leanprover/lean-eval-submissions/commits/main --jq .sha)"
current_benchmark="$(tr -d '\n' < benchmark-snapshot/.benchmark-commit)"
for revision in "$current_state" "$current_results" "$current_benchmark"; do
  if [[ ! "$revision" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Could not establish a full current input revision." >&2
    exit 1
  fi
done

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

fetch_public_json() {
  curl --fail --silent --show-error --location \
    --proto '=https' --max-redirs 2 --max-time 30 \
    --retry 3 --retry-all-errors --retry-max-time 60 --output "$2" "$1"
}
fetch_public_json https://lean-lang.org/eval/site-data/v2/index.json "$scratch/index.json"
fetch_public_json https://lean-lang.org/eval/site-data/leaderboard.json "$scratch/results.json"

# Reject missing or malformed provenance rather than declaring the site current.
published="$(jq --exit-status --null-input \
  --slurpfile indexes "$scratch/index.json" --slurpfile stores "$scratch/results.json" '
  def commit: type == "string" and test("^[0-9a-f]{40}$");
  select(($indexes | length) == 1 and ($stores | length) == 1) |
  $indexes[0] as $index | $stores[0] as $results |
  select($index.schema_version == 2 and $results.schema_version == 1) |
  select($index.state.repo == "leanprover/lean-eval-state" and $index.state.materialized == true) |
  select($index.benchmark.repo == "leanprover/lean-eval" and $results.benchmark.repo == "leanprover/lean-eval") |
  select($results.results_repo.repo == "leanprover/lean-eval-submissions") |
  select($index.state.commit | commit) |
  select($index.benchmark.commit | commit) |
  select($results.benchmark.commit | commit) |
  select($results.results_repo.commit | commit) |
  select($index.generated_at | type == "string" and length > 0) |
  select($results.generated_at | type == "string" and length > 0) |
  {state: $index.state.commit, results: $results.results_repo.commit,
   benchmark: $index.benchmark.commit,
   coherent: ($index.generated_at == $results.generated_at and $index.benchmark == $results.benchmark)}
')" || {
  echo "::error::Published site-data lacks valid provenance in index.json or leaderboard.json." >&2
  exit 1
}
if jq --exit-status --arg state "$current_state" --arg results "$current_results" \
    --arg benchmark "$current_benchmark" \
    '.coherent and .state == $state and .results == $results and .benchmark == $benchmark' \
    <<< "$published" > /dev/null; then
  echo "Leaderboard already publishes current State, Results, and benchmark revisions."
  exit 0
fi

echo "::notice::Leaderboard inputs are stale or its public snapshots are inconsistent."
runs="$(gh api "repos/$repository/actions/workflows/deploy.yml/runs?per_page=100")"
# A fork's PR branch may also be called main; it cannot publish production.
production_runs="$(jq --exit-status '[.workflow_runs[] | select(.head_branch == "main" and .event != "pull_request")]' <<< "$runs")"
active="$(jq '[.[] | select(.status != "completed")] | length' <<< "$production_runs")"
if [ "$active" != 0 ]; then
  echo "A Pages deployment is already active; the next refresh will recheck publication."
  exit 0
fi

last_conclusion="$(jq -r '.[0].conclusion // "none"' <<< "$production_runs")"
last_url="$(jq -r '.[0].html_url // "unknown"' <<< "$production_runs")"
gh workflow run deploy.yml --repo "$repository" --ref main
echo "Dispatched a Pages refresh for current State, Results, and benchmark revisions."
case "$last_conclusion" in
  failure|timed_out|action_required|startup_failure)
    echo "::error::Leaderboard publication is stale after a failed deployment: $last_url. A recovery was dispatched." >&2
    exit 1
    ;;
esac
