from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


class PreviewStructureTests(unittest.TestCase):
    def test_site_contains_visible_preview_page(self) -> None:
        site = (REPO_ROOT / "LeaderboardSite.lean").read_text()
        page = (REPO_ROOT / "LeaderboardSite/Pages/Preview.lean").read_text()
        self.assertIn('Dir.page "preview"', site)
        self.assertIn("Results schema v2 preview", page)
        self.assertIn("leaderboardPreview%", page)
        self.assertIn('href="."', page)

    def test_deploy_checks_preview_parity_and_links(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/deploy.yml").read_text()
        self.assertIn("_site/preview/index.html", workflow)
        self.assertIn("leaderboard-preview.json", workflow)
        self.assertIn("del(.preview)", workflow)
        self.assertIn("Verify public catalog visibility", workflow)
        self.assertIn("all(.problems[]; .visible == true", workflow)
        self.assertIn("python3 scripts/check_links.py", workflow)


if __name__ == "__main__":
    unittest.main()
