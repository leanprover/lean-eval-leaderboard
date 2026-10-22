import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/refresh-state.yml").read_text(encoding="utf-8")


class StateRefreshWorkflowTests(unittest.TestCase):
    def test_refresh_is_bounded_and_uses_existing_read_only_state_key(self) -> None:
        self.assertIn('cron: "7,22,37,52 * * * *"', WORKFLOW)
        self.assertIn("timeout-minutes: 5", WORKFLOW)
        self.assertIn("cancel-in-progress: false", WORKFLOW)
        self.assertIn("PRODUCTION_STATE_READ_KEY", WORKFLOW)
        self.assertIn("ref: main", WORKFLOW)
        self.assertIn("persist-credentials: false", WORKFLOW)
        self.assertIn("fetch-depth: 1", WORKFLOW)

    def test_refresh_checks_out_and_runs_the_publication_monitor(self) -> None:
        self.assertIn("Checkout publication monitor", WORKFLOW)
        self.assertIn("run: bash scripts/refresh_leaderboard.sh", WORKFLOW)
        self.assertIn("GH_TOKEN: ${{ github.token }}", WORKFLOW)

    def test_dependency_fetches_prune_stale_cached_refs(self) -> None:
        workflow = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
        self.assertLess(workflow.index("git config --global fetch.prune true"),
                        workflow.index("run: lake update"))

    def test_refresh_permissions_are_minimal_for_same_repo_dispatch(self) -> None:
        self.assertIn("permissions:\n  actions: write\n  contents: read", WORKFLOW)
        self.assertNotIn("pages: write", WORKFLOW)
        self.assertNotIn("id-token: write", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
