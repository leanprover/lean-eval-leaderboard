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
        self.assertIn('Dir.page "open-problems"', site)
        # The retired route is one documented compatibility alias, not a
        # second group or preview surface.
        self.assertIn('Dir.page "open-conjectures"', site)
        self.assertEqual(site.count('Dir.page "open-conjectures"'), 1)
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
        self.assertIn('data-lifecycle-group-tab="open-problems"', page)
        self.assertNotIn('data-lifecycle-group-tab="open-conjectures"', page)
        self.assertNotIn("Open conjectures", page)
        self.assertNotIn("Local-only preview", page)

    def test_lifecycle_problem_pages_retain_the_complete_problem_statement(self) -> None:
        page = (REPO_ROOT / "LeaderboardSite/Pages/Preview.lean").read_text()
        detail = (
            REPO_ROOT / "LeaderboardSite/Pages/ProblemDetail.lean"
        ).read_text()
        self.assertIn("anchorBlockTerms problem", page)
        self.assertIn('headingBlock "Problem statement"', page)
        self.assertIn('"wrap prose lifecycle-problem-statement"', page)
        self.assertIn("problemStatementBlocks", page)
        self.assertIn("def problemStatementBlocks", detail)
        self.assertIn("optionalParagraph problemsNotesLabel notesText", detail)
        self.assertIn("sourceParagraph sourceText", detail)
        self.assertIn("anchors.map holeWrap", detail)

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
        self.assertIn("No open problems are published in this group yet.", client)

    def test_submit_page_marks_server_prelaunch_and_keeps_issue_intake_current(self) -> None:
        copy = (REPO_ROOT / "LeaderboardSite/Copy.lean").read_text()
        worker = "https://lean-eval-submission-server.lean-eval.workers.dev/"
        issue_form = (
            "https://github.com/leanprover/lean-eval-submissions/"
            "issues/new?template=submit.yml"
        )
        self.assertIn(worker, copy)
        self.assertIn(issue_form, copy)
        self.assertIn("Production server intake is not enabled", copy)
        self.assertIn("it is not accepting submissions", copy)
        self.assertIn("current functioning\n  submission path", copy)
        self.assertIn(
            "Server intake prelaunch — not accepting submissions",
            copy,
        )
        self.assertIn(
            "Submit now through the GitHub issue form",
            copy,
        )
        self.assertNotIn("secondary path", copy)
        self.assertNotIn(
            "New submissions\n  should use the authenticated application",
            copy,
        )
        self.assertIn("GitHub OAuth callbacks", copy)
        self.assertIn("private encrypted archive", copy)
        self.assertIn("two UTC calendar months after acceptance", copy)
        self.assertIn("automatically publishes", copy)
        self.assertIn("Apache License 2.0", copy)
        self.assertIn("opt out at any time before release", copy)
        self.assertIn("legacy GitHub issue form", copy)
        self.assertIn("return to the leaderboard", copy)
        self.assertIn(
            "[return to the leaderboard](https://lean-lang.org/eval/)",
            copy,
        )
        self.assertIn(
            "https://github.com/apps/lean-eval-source-reader",
            copy,
        )
        self.assertIn("exact 40-character source commit", copy)
        self.assertIn("will require a private GitHub repository", copy)
        self.assertNotIn("Public repositories need no extra setup", copy)
        self.assertNotIn("https://github.com/apps/lean-eval-bot", copy)
        self.assertNotIn("Secret (unlisted) gists", copy)
        self.assertNotIn(
            'def submitCtaUrl    : String :=\n  "https://github.com/',
            copy,
        )

    def test_client_renders_current_replay_measurement_fields(self) -> None:
        client = (REPO_ROOT / "static/lifecycle-preview.js").read_text()
        for field in (
            "checker_wall_time_ms",
            "checker_retired_instructions",
            "checker_retired_instructions_unavailable_reason",
            "build_wall_time_ms",
            "build_retired_instructions",
            "build_retired_instructions_unavailable_reason",
            "lines_of_code",
            "file_count",
        ):
            with self.subTest(field=field):
                self.assertIn(f"measurement.{field}", client)
        self.assertNotIn("measurement.wall_time_ms", client)
        self.assertNotIn("measurement.retired_instructions", client)

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
        self.assertIn("--schema-version 6", workflow)
        self.assertIn(".schema_version == 6", workflow)
        self.assertIn(".historical_replay_series | type == \"array\"", workflow)
        self.assertIn(".historical_replay_unavailability | type == \"array\"", workflow)
        self.assertIn("_site/site-data/public-state.json", workflow)
        self.assertIn("Private State fields leaked", workflow)


if __name__ == "__main__":
    unittest.main()
