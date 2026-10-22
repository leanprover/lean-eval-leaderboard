import json
import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/refresh_leaderboard.sh"


class PublicationRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        (self.root / "benchmark-snapshot").mkdir()
        (self.root / "benchmark-snapshot/.benchmark-commit").write_text("c" * 40 + "\n")
        self.index = {
            "schema_version": 2,
            "generated_at": "2026-10-22T00:00:00Z",
            "state": {"repo": "leanprover/lean-eval-state", "commit": "a" * 40, "materialized": True},
            "benchmark": {"repo": "leanprover/lean-eval", "commit": "c" * 40},
        }
        self.results = {
            "schema_version": 1,
            "generated_at": self.index["generated_at"],
            "benchmark": dict(self.index["benchmark"]),
            "results_repo": {"repo": "leanprover/lean-eval-submissions", "commit": "b" * 40},
        }
        self.runs = [{"head_branch": "main", "event": "repository_dispatch", "status": "completed",
                      "conclusion": "success", "html_url": "https://example.test/run/1"}]
        commands = self.root / "bin"
        commands.mkdir()
        fake = commands / "fake"
        fake.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
root = pathlib.Path(os.environ["FIXTURES"])
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
if name == "git":
    print(os.environ.get("CURRENT_STATE", "a" * 40))
elif name == "curl":
    file = "index.json" if args[-1].endswith("v2/index.json") else "results.json"
    pathlib.Path(args[args.index("--output") + 1]).write_text((root / file).read_text())
elif name == "gh" and args[0] == "api":
    if "commits/main" in args[1]:
        print("b" * 40)
    else:
        print((root / "runs.json").read_text())
elif name == "gh" and args[:3] == ["workflow", "run", "deploy.yml"]:
    (root / "dispatch").write_text(json.dumps(args))
else:
    raise SystemExit("unexpected command: " + str(args))
''')
        fake.chmod(0o755)
        for name in ["git", "curl", "gh"]:
            (commands / name).symlink_to(fake)
        self.env = {**os.environ, "FIXTURES": str(self.root),
                    "PATH": str(commands) + os.pathsep + os.environ["PATH"],
                    "GITHUB_REPOSITORY": "leanprover/lean-eval-leaderboard"}

    def run_monitor(self):
        for filename, data in [("index.json", self.index), ("results.json", self.results),
                               ("runs.json", {"workflow_runs": self.runs})]:
            (self.root / filename).write_text(json.dumps(data))
        return subprocess.run(["bash", str(SCRIPT)], cwd=self.root, env=self.env,
                              text=True, capture_output=True)

    def assert_dispatched(self, result, code=0):
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        args = json.loads((self.root / "dispatch").read_text())
        self.assertEqual(args, ["workflow", "run", "deploy.yml", "--repo",
                                "leanprover/lean-eval-leaderboard", "--ref", "main"])

    def test_current_inputs_do_not_dispatch(self):
        result = self.run_monitor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "dispatch").exists())
        self.assertIn("already publishes current", result.stdout)

    def test_results_only_advance_dispatches_even_when_state_matches(self):
        self.results["results_repo"]["commit"] = "d" * 40
        self.assert_dispatched(self.run_monitor())

    def test_realistic_large_results_payload_is_read_from_file(self):
        self.results["entries"] = [{"description": "x" * 200_000}]
        result = self.run_monitor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already publishes current", result.stdout)

    def test_state_only_advance_dispatches(self):
        self.index["state"]["commit"] = "d" * 40
        self.assert_dispatched(self.run_monitor())

    def test_benchmark_only_advance_dispatches(self):
        for data in [self.index, self.results]:
            data["benchmark"]["commit"] = "d" * 40
        self.assert_dispatched(self.run_monitor())

    def test_mixed_public_snapshots_are_not_reported_current(self):
        self.results["generated_at"] = "2026-10-21T00:00:00Z"
        self.assert_dispatched(self.run_monitor())

    def test_active_production_build_prevents_duplicate_dispatch(self):
        self.results["results_repo"]["commit"] = "d" * 40
        self.runs[0].update(status="in_progress", conclusion=None)
        result = self.run_monitor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "dispatch").exists())
        self.assertIn("already active", result.stdout)

    def test_fork_pr_named_main_does_not_block_production(self):
        self.results["results_repo"]["commit"] = "d" * 40
        self.runs.insert(0, {**self.runs[0], "event": "pull_request", "status": "in_progress"})
        self.assert_dispatched(self.run_monitor())

    def test_failed_publication_is_red_and_still_dispatches_recovery(self):
        self.results["results_repo"]["commit"] = "d" * 40
        self.runs[0]["conclusion"] = "failure"
        result = self.run_monitor()
        self.assert_dispatched(result, code=1)
        self.assertIn("::error::", result.stderr)
        self.assertIn(self.runs[0]["html_url"], result.stderr)

    def test_malformed_provenance_fails_without_dispatch(self):
        self.results["results_repo"]["commit"] = "not-a-commit"
        result = self.run_monitor()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "dispatch").exists())

    def test_disagreeing_benchmark_snapshots_trigger_refresh(self):
        self.results["benchmark"]["commit"] = "d" * 40
        self.assert_dispatched(self.run_monitor())

    def test_unmaterialized_state_reports_invalid_public_provenance(self):
        self.index["state"]["materialized"] = False
        result = self.run_monitor()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("::error::Published site-data lacks valid provenance", result.stderr)
        self.assertFalse((self.root / "dispatch").exists())

    def test_old_failure_after_newer_success_does_not_report_failure(self):
        self.results["results_repo"]["commit"] = "d" * 40
        self.runs.append({**self.runs[0], "conclusion": "failure"})
        self.assert_dispatched(self.run_monitor())

    def test_missing_results_provenance_fails_without_dispatch(self):
        del self.results["results_repo"]
        result = self.run_monitor()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "dispatch").exists())

    def test_malformed_current_revision_fails_without_dispatch(self):
        self.env["CURRENT_STATE"] = "invalid"
        result = self.run_monitor()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "dispatch").exists())


class DependencyRefPruningTests(unittest.TestCase):
    def test_lake_style_fetch_recovers_deleted_branch_prefix_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            env = {**os.environ, "GIT_CONFIG_GLOBAL": str(root / "gitconfig"), "GIT_CONFIG_NOSYSTEM": "1"}

            def git(*args, check=True):
                return subprocess.run(["git", *args], cwd=root, env=env, check=check,
                                      text=True, capture_output=True)

            git("init", "--bare", "remote.git")
            git("clone", "remote.git", "writer")
            git("-C", "writer", "-c", "user.name=Test", "-c", "user.email=test@example.test",
                "commit", "--allow-empty", "-m", "initial")
            git("-C", "writer", "push", "origin", "HEAD:refs/heads/bump/v4.37.0/old")
            git("clone", "remote.git", "cached")
            git("-C", "writer", "push", "origin", ":refs/heads/bump/v4.37.0/old")
            git("-C", "writer", "push", "origin", "HEAD:refs/heads/bump/v4.37.0")
            git("-C", "cached", "show-ref", "--verify", "refs/remotes/origin/bump/v4.37.0/old")
            # Some Git versions may resolve this automatically; do not bind
            # production publication to a particular error message or version.
            git("-C", "cached", "fetch", "origin", check=False)
            git("config", "--global", "fetch.prune", "true")
            git("-C", "cached", "fetch", "origin")
            git("-C", "cached", "show-ref", "--verify", "refs/remotes/origin/bump/v4.37.0")
            old = git("-C", "cached", "show-ref", "--verify",
                      "refs/remotes/origin/bump/v4.37.0/old", check=False)
            self.assertNotEqual(old.returncode, 0)


if __name__ == "__main__":
    unittest.main()
