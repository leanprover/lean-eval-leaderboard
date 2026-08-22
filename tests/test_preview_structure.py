from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


class PreviewStructureTests(unittest.TestCase):
    def test_site_contains_lifecycle_cutover_and_legacy_rollback_routes(self) -> None:
        site = (REPO_ROOT / "LeaderboardSite.lean").read_text()
        page = (REPO_ROOT / "LeaderboardSite/Pages/Preview.lean").read_text()
        self.assertIn("LeaderboardSite.Pages.LifecycleFront", site)
        self.assertIn('Dir.page "legacy"', site)
        self.assertIn('Dir.page "preview"', site)
        self.assertIn('Dir.page "formalization-evaluation"', site)
        self.assertIn('Dir.page "software-verification"', site)
        self.assertIn('Dir.page "open-conjectures"', site)
        self.assertIn('Dir.page "recent"', site)
        self.assertIn("lifecycle_problem_pages%", site)
        self.assertIn("preview_problem_pages%", site)
        theme = (REPO_ROOT / "SiteTheme.lean").read_text()
        self.assertIn("isLegacyFront", theme)
        self.assertIn('"home-page legacy-page"', theme)
        self.assertIn("LeanEval lifecycle-aware leaderboard", page)
        self.assertIn('aria-live="polite"', page)
        self.assertIn("aria-label={{heading}}", page)
        self.assertNotIn('<h1 id="lifecycle-title">', page)
        self.assertIn('href="legacy/"', page)
        self.assertNotIn("Local-only preview", page)

    def test_site_data_uses_stable_cutover_routes(self) -> None:
        generator = (REPO_ROOT / "scripts/lifecycle_site_data.py").read_text()
        self.assertIn('"url": f"problems/', generator)
        self.assertIn('"url": f"{group[\'id\']}/"', generator)
        self.assertIn("base + 'recent/'", generator)
        self.assertNotIn('"url": f"preview/problems/', generator)
        self.assertNotIn("base + 'preview/recent/'", generator)

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

    def test_deploy_checks_cutover_preview_parity_and_links(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/deploy.yml").read_text()
        self.assertIn("_site/legacy/index.html", workflow)
        self.assertIn("_site/formalization-evaluation/index.html", workflow)
        self.assertIn("_site/recent/index.html", workflow)
        self.assertIn("_site/preview/index.html", workflow)
        self.assertIn("leaderboard-preview.json", workflow)
        self.assertIn("del(.preview)", workflow)
        self.assertIn("site-data/v2/index.json", workflow)
        self.assertIn("recent-solutions.xml", workflow)
        self.assertIn("Verify public catalog visibility", workflow)
        self.assertIn("all(.problems[]; .visible == true", workflow)
        self.assertIn("python3 scripts/check_links.py", workflow)
        self.assertIn("PRODUCTION_STATE_READ_KEY", workflow)
        self.assertIn("Checkout private production State for its redacted projection", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("--state-projection", workflow)
        self.assertIn("_site/site-data/public-state.json", workflow)
        self.assertIn("Private State fields leaked", workflow)


if __name__ == "__main__":
    unittest.main()
