from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


class PreviewStructureTests(unittest.TestCase):
    def test_site_contains_visible_preview_page(self) -> None:
        site = (REPO_ROOT / "LeaderboardSite.lean").read_text()
        page = (REPO_ROOT / "LeaderboardSite/Pages/Preview.lean").read_text()
        self.assertIn('Dir.page "preview"', site)
        self.assertIn('Dir.page "formalization-evaluation"', site)
        self.assertIn('Dir.page "software-verification"', site)
        self.assertIn('Dir.page "open-conjectures"', site)
        self.assertIn('Dir.page "recent"', site)
        self.assertIn("preview_problem_pages%", site)
        self.assertIn("LeanEval lifecycle-aware leaderboard", page)
        self.assertIn('aria-live="polite"', page)
        self.assertIn('href="."', page)

    def test_client_uses_safe_dom_and_url_persistent_filters(self) -> None:
        client = (REPO_ROOT / "static/lifecycle-preview.js").read_text()
        self.assertNotIn("innerHTML", client)
        self.assertIn("textContent", client)
        self.assertIn("history.replaceState", client)
        self.assertIn('tags:', client)
        self.assertIn('["unique", "first", "total"]', client)
        self.assertIn("recent-solutions.xml", client)

    def test_product_ui_uses_lifecycle_not_schema_terminology(self) -> None:
        sources = [
            REPO_ROOT / "LeaderboardSite/Pages/Preview.lean",
            REPO_ROOT / "SiteTheme.lean",
            REPO_ROOT / "static/lifecycle-preview.js",
            REPO_ROOT / "static/style.css",
        ]
        for source in sources:
            with self.subTest(source=source.relative_to(REPO_ROOT)):
                self.assertNotIn("v2-", source.read_text())
        self.assertFalse((REPO_ROOT / "static/v2-preview.js").exists())

    def test_deploy_checks_preview_parity_and_links(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/deploy.yml").read_text()
        self.assertIn("_site/preview/index.html", workflow)
        self.assertIn("leaderboard-preview.json", workflow)
        self.assertIn("del(.preview)", workflow)
        self.assertIn("site-data/v2/index.json", workflow)
        self.assertIn("recent-solutions.xml", workflow)
        self.assertIn("Verify public catalog visibility", workflow)
        self.assertIn("all(.problems[]; .visible == true", workflow)
        self.assertIn("python3 scripts/check_links.py", workflow)


if __name__ == "__main__":
    unittest.main()
