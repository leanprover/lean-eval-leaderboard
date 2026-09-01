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

    def test_submit_page_keeps_issue_intake_primary_before_server_launch(self) -> None:
        copy = (REPO_ROOT / "LeaderboardSite/Copy.lean").read_text()
        worker = "https://lean-eval-submission-server.lean-eval.workers.dev/"
        issue_form = (
            "https://github.com/leanprover/lean-eval-submissions/"
            "issues/new?template=submit.yml"
        )
        self.assertIn(worker, copy)
        self.assertIn(issue_form, copy)
        self.assertIn(
            "The launch overlap will begin only after server intake launches",
            copy,
        )
        self.assertIn("will last\n  at least four weeks", copy)
        self.assertNotIn("During the 28-day launch overlap", copy)
        self.assertIn(
            "Production server intake is not enabled yet",
            copy,
        )
        self.assertIn(
            "Until launch, submit through the",
            copy,
        )
        self.assertIn(
            "At launch, the authenticated submission application will be hosted",
            copy,
        )
        self.assertIn("Submit using the current GitHub issue form", copy)
        self.assertIn(
            'def submitCtaUrl    : String :=\n  "' + issue_form + '"',
            copy,
        )
        self.assertNotIn(
            'def submitCtaUrl    : String :=\n  "' + worker + '"',
            copy,
        )
        submit_copy = copy[copy.index("/-! ## Submit page") :]
        normalized_copy = copy.replace("\n  ", " ")
        self.assertNotRegex(submit_copy, r"\b20\d{2}-\d{2}-\d{2}\b")
        self.assertIn("GitHub OAuth callbacks", copy)
        self.assertIn("private encrypted archive", copy)
        self.assertIn("two UTC calendar months after acceptance", copy)
        self.assertIn("automatically publishes", copy)
        self.assertIn("Apache License 2.0", copy)
        self.assertIn("3. Review authenticated-intake release terms", copy)
        self.assertIn(
            "After server launch, the authenticated submission action will include",
            normalized_copy,
        )
        self.assertIn(
            "For authenticated submissions after launch, scheduled release will be the",
            normalized_copy,
        )
        self.assertNotIn("The submission action includes", submit_copy)
        self.assertNotIn("At submission time", submit_copy)
        self.assertIn("keep accepted source private", copy)
        self.assertIn("If the\n  initial choice is private", copy)
        self.assertIn("authorize scheduled release", normalized_copy)
        self.assertIn(
            "a scheduled choice cannot be changed back to private",
            normalized_copy,
        )
        self.assertIn("that transition is irreversible", copy)
        for revocation_offer in (
            "opt out",
            "withdraw authorization",
            "revoke authorization",
            "cancel scheduled release",
        ):
            self.assertNotIn(revocation_offer, copy.lower())
        self.assertIn("current GitHub issue form", copy)
        self.assertIn("return to the leaderboard", copy)
        self.assertIn(
            "[return to the leaderboard](https://lean-lang.org/eval/)",
            copy,
        )
        self.assertIn(
            "https://github.com/apps/lean-eval-source-reader",
            copy,
        )
        self.assertIn("40-character source commit", copy)
        self.assertIn("require a private GitHub repository", copy)
        self.assertNotIn("Public repositories need no extra setup", copy)
        self.assertNotIn("https://github.com/apps/lean-eval-bot", copy)
        self.assertNotIn("Secret (unlisted) gists", copy)

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

    def test_problem_page_shows_the_exact_scheduled_release_time(self) -> None:
        client = (REPO_ROOT / "static/lifecycle-preview.js").read_text()

        self.assertIn('release.status === "scheduled"', client)
        self.assertIn('["Automatic release", release.release_at', client)
        self.assertIn(
            'formattedDate(release.release_at) + " · " + release.release_at',
            client,
        )

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
        self.assertIn("For authenticated submissions after launch", workflow)
        self.assertIn("initial choice is private", workflow)
        self.assertIn(
            "The prelaunch submit page presents future release controls as current",
            workflow,
        )
        self.assertIn("Production server intake is not enabled yet", workflow)
        self.assertIn("Submit using the current GitHub issue form", workflow)
        self.assertIn(
            "The launch overlap will begin only after server intake launches",
            workflow,
        )
        self.assertIn(".historical_replay_series | type == \"array\"", workflow)
        self.assertIn(".historical_replay_unavailability | type == \"array\"", workflow)
        self.assertIn("_site/site-data/public-state.json", workflow)
        self.assertIn("Private State fields leaked", workflow)


if __name__ == "__main__":
    unittest.main()
