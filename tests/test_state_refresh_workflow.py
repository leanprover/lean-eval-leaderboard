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

    def test_refresh_binds_live_and_private_state_before_dispatch(self) -> None:
        self.assertIn("https://lean-lang.org/eval/site-data/v2/index.json", WORKFLOW)
        self.assertIn('select(.schema_version == 2)', WORKFLOW)
        self.assertIn('select(.state.repo == "leanprover/lean-eval-state")', WORKFLOW)
        self.assertIn('select(.state.materialized == true)', WORKFLOW)
        self.assertIn('git -C lean-eval-state rev-parse HEAD', WORKFLOW)
        self.assertIn('if [ "$deployed_state" = "$current_state" ]', WORKFLOW)

    def test_refresh_does_not_queue_behind_an_active_pages_build(self) -> None:
        self.assertIn("actions/workflows/deploy.yml/runs?per_page=100", WORKFLOW)
        self.assertIn('.head_branch == "main"', WORKFLOW)
        self.assertIn('.status != "completed"', WORKFLOW)
        self.assertIn('if [ "$active" != 0 ]', WORKFLOW)
        self.assertIn('gh workflow run deploy.yml --repo "$REPOSITORY" --ref main', WORKFLOW)

    def test_refresh_permissions_are_minimal_for_same_repo_dispatch(self) -> None:
        self.assertIn("permissions:\n  actions: write\n  contents: read", WORKFLOW)
        self.assertNotIn("pages: write", WORKFLOW)
        self.assertNotIn("id-token: write", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
