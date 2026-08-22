#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

try:
    from scripts.results_schema import (
        ResultsSchemaError,
        parse_schema_version_2_file,
    )
    from scripts.lifecycle_site_data import (
        adapt_results_store,
        adapt_state_domain,
        build_lifecycle_projection,
        load_preview_fixture,
        load_set_definitions,
        merge_solutions,
    )
except ModuleNotFoundError:
    from results_schema import ResultsSchemaError, parse_schema_version_2_file
    from lifecycle_site_data import (
        adapt_results_store,
        adapt_state_domain,
        build_lifecycle_projection,
        load_preview_fixture,
        load_set_definitions,
        merge_solutions,
    )


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE_DATA_ROOT = REPO_ROOT / "site-data"
BENCHMARK_SNAPSHOT_ROOT = REPO_ROOT / "benchmark-snapshot"
DEFAULT_BENCHMARK_REPO = pathlib.Path(
    os.environ.get("LEAN_EVAL_BENCHMARK_REPO", str(REPO_ROOT.parent / "lean-eval"))
)
# The results store (`results/<login>.json`) lives in a sibling repo,
# leanprover/lean-eval-submissions. The deploy workflow checks it out and
# passes --results-repo; locally it defaults to a sibling clone.
DEFAULT_RESULTS_REPO = pathlib.Path(
    os.environ.get("LEAN_EVAL_RESULTS_REPO", str(REPO_ROOT.parent / "lean-eval-submissions"))
)
RESULTS_REPO_SLUG = "leanprover/lean-eval-submissions"
# Path to the SHA pin file the deploy workflow already uses to know
# which lean-eval commit benchmark-snapshot/ was built from. Single
# line, 40 hex chars + trailing newline. Bumping this file is the
# recorded act of advancing the benchmark commit the leaderboard
# reflects. See SECURITY.md (in lean-eval) > "Bumping pinned
# dependencies" for the procedure.
BENCHMARK_COMMIT_FILE = REPO_ROOT / "benchmark-snapshot" / ".benchmark-commit"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PROBLEM_ID_RE = re.compile(r"^[A-Za-z0-9_]+$")
TAG_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ROOT_DECLARATIONS_BY_PROBLEM = {
    "annals_dirichlet_weyl_bound": {"Nat.IsCubeFree"},
}
ANNALS_PROBABILITY_NOTATION_IMPORT = (
    "import LeanEval.Analysis.AnnalsProbabilityNotation"
)


@dataclass(frozen=True)
class Hole:
    name: str
    basename: str
    kind: str
    body: str


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    group: str
    status: str
    visible: bool
    statement_revision: int
    tags: tuple[str, ...]
    submitter: str
    module: str
    notes: str | None
    source: str | None
    informal_solution: str | None
    holes: tuple[Hole, ...]
    challenge_path: str
    sort_index: int


def run(cmd: list[str], cwd: pathlib.Path) -> str:
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
      raise SystemExit(completed.stderr.strip() or completed.stdout.strip() or f"command failed: {' '.join(cmd)}")
    return completed.stdout.strip()


def git_head(repo: pathlib.Path) -> str:
    return run(["git", "rev-parse", "HEAD"], cwd=repo)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_model_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown-model"


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_holes(benchmark_repo: pathlib.Path, problem_id: str) -> tuple[Hole, ...]:
    """Read `generated/<id>/holes.json` and return the per-hole metadata."""
    path = benchmark_repo / "generated" / problem_id / "holes.json"
    if not path.is_file():
        raise SystemExit(
            f"holes.json not found for problem '{problem_id}': {path}. "
            f"Re-run `python scripts/generate_projects.py` in the benchmark repo "
            f"to publish per-hole metadata."
        )
    payload = load_json(path)
    holes = []
    for raw in payload["holes"]:
        holes.append(Hole(
            name=str(raw["name"]),
            basename=str(raw["basename"]),
            kind=str(raw["kind"]),
            body=str(raw["body"]),
        ))
    return tuple(holes)


def load_manifest(manifest_dir: pathlib.Path, benchmark_repo: pathlib.Path) -> list[Problem]:
    """Load every `manifests/problems/<id>.toml` file as a `Problem`.

    Files are walked in sorted filename order, which becomes `sort_index`.
    """
    problems: list[Problem] = []
    for index, path in enumerate(sorted(manifest_dir.glob("*.toml"))):
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        for field in ("id", "title", "group", "status", "module", "submitter"):
            if not isinstance(raw.get(field), str) or not raw[field].strip():
                raise SystemExit(f"{path}: {field} must be a non-empty string")
        if type(raw.get("visible")) is not bool:
            raise SystemExit(f"{path}: visible must be a boolean")
        revision = raw.get("statement_revision")
        if type(revision) is not int or revision <= 0:
            raise SystemExit(f"{path}: statement_revision must be a positive integer")
        raw_tags = raw.get("tags")
        if not isinstance(raw_tags, list) or not all(
            isinstance(tag, str) and tag for tag in raw_tags
        ):
            raise SystemExit(f"{path}: tags must be an array of non-empty strings")
        if len(raw_tags) != len(set(raw_tags)):
            raise SystemExit(f"{path}: tags must not contain duplicates")
        if raw["group"] not in {
            "formalization-evaluation",
            "software-verification",
            "open-conjectures",
        }:
            raise SystemExit(f"{path}: unsupported group {raw['group']!r}")
        if raw["status"] not in {"draft", "active", "archived"}:
            raise SystemExit(f"{path}: unsupported status {raw['status']!r}")
        problem_id = str(raw["id"])
        if not PROBLEM_ID_RE.fullmatch(problem_id):
            raise SystemExit(f"{path}: invalid problem id {problem_id!r}")
        holes = load_holes(benchmark_repo, problem_id)
        problems.append(
            Problem(
                id=problem_id,
                title=str(raw["title"]),
                group=str(raw["group"]),
                status=str(raw["status"]),
                visible=raw["visible"],
                statement_revision=revision,
                tags=tuple(raw_tags),
                submitter=str(raw["submitter"]),
                module=str(raw["module"]),
                notes=str(raw["notes"]).strip() if raw.get("notes") else None,
                source=str(raw["source"]).strip() if raw.get("source") else None,
                informal_solution=str(raw["informal_solution"]).strip() if raw.get("informal_solution") else None,
                holes=holes,
                challenge_path=f"generated/{problem_id}",
                sort_index=index,
            )
        )
    return problems


def write_json(path: pathlib.Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_tag_registry(path: pathlib.Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    registry: dict[str, dict[str, str]] = {}
    for tag, definition in raw.get("tags", {}).items():
        if not TAG_ID_RE.fullmatch(str(tag)):
            raise SystemExit(f"{path}: invalid tag id {tag!r}")
        label = definition.get("label")
        description = definition.get("description")
        if not isinstance(label, str) or not label or not isinstance(description, str):
            raise SystemExit(f"{path}: tag {tag!r} has invalid display metadata")
        registry[str(tag)] = {"label": label, "description": description}
    return registry


def benchmark_mathlib_require(benchmark_repo: pathlib.Path) -> tuple[str, str]:
    lakefile = benchmark_repo / "lakefile.toml"
    data = tomllib.loads(lakefile.read_text(encoding="utf-8"))
    for req in data.get("require", []):
        if str(req.get("name")) == "mathlib":
            git = str(req.get("git", "")).strip()
            rev = str(req.get("rev", "")).strip()
            if git and rev:
                return git, rev
    raise SystemExit(f"Could not find mathlib requirement in {lakefile}")


# `require verso from git "<url>" @ "<rev>"` in the site lakefile. The site
# decodes the snapshot's highlighted JSON with the SubVerso that this Verso
# pulls in, so the Verso revision is the source of truth for the snapshot pin.
VERSO_REQUIRE_RE = re.compile(
    r'require\s+verso\s+from\s+git\s+"(?P<git>[^"]+)"\s*@\s*"(?P<rev>[^"]+)"'
)


def site_verso_require() -> tuple[str, str]:
    lakefile = REPO_ROOT / "lakefile.lean"
    match = VERSO_REQUIRE_RE.search(lakefile.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"Could not find a `require verso` line in {lakefile}")
    return match.group("git"), match.group("rev")


def fetch_json_url(
    url: str,
    *,
    attempts: int = 5,
    retry_delay_seconds: float = 5,
) -> Any:
    """Fetch JSON with bounded retries for transient hosting failures."""
    headers = {"User-Agent": "lean-eval-leaderboard-snapshot-generator"}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            if attempt == attempts:
                raise
            time.sleep(retry_delay_seconds * attempt)
    raise AssertionError("unreachable")


def consumer_subverso_rev() -> str:
    """The SubVerso revision LeaderboardSite decodes highlighted JSON with.

    It is whatever Verso (pinned in the site lakefile) pins SubVerso to in its
    own lake-manifest, fetched straight from GitHub so this works without a
    resolved Lake workspace — the bump workflow regenerates the snapshot
    without ever running the site's `lake update`.
    """
    verso_git, verso_rev = site_verso_require()
    slug = re.sub(r"\.git$", "", verso_git).rstrip("/").removeprefix("https://github.com/")
    url = f"https://raw.githubusercontent.com/{slug}/{verso_rev}/lake-manifest.json"
    try:
        manifest = fetch_json_url(url)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SystemExit(f"Could not fetch Verso's lake-manifest from {url}: {exc}")
    for pkg in manifest.get("packages", []):
        if pkg.get("name") == "subverso":
            rev = str(pkg.get("rev", "")).strip()
            if SHA_RE.fullmatch(rev):
                return rev
            raise SystemExit(f"Verso manifest at {url} has a non-SHA subverso rev: {rev!r}")
    raise SystemExit(f"No subverso package in Verso's lake-manifest at {url}")


def benchmark_snapshot_lakefile(benchmark_repo: pathlib.Path) -> str:
    mathlib_git, mathlib_rev = benchmark_mathlib_require(benchmark_repo)
    subverso_rev = consumer_subverso_rev()
    return "\n".join(
        [
            'name = "benchmark-snapshot"',
            'defaultTargets = ["BenchmarkProblems"]',
            "",
            "[[require]]",
            'name = "mathlib"',
            f'git = "{mathlib_git}"',
            f'rev = "{mathlib_rev}"',
            "",
            "[[require]]",
            'name = "subverso"',
            'git = "https://github.com/leanprover/subverso"',
            "# Pinned to the SubVerso revision Verso pulls into LeaderboardSite, so the",
            "# highlighted JSON this snapshot emits stays decodable by the site. Derived",
            "# from the site lakefile's Verso pin by scripts/generate_site_data.py.",
            f'rev = "{subverso_rev}"',
            "",
            "[[lean_lib]]",
            'name = "BenchmarkProblems"',
            "",
        ]
    )


def load_results(results_root: pathlib.Path) -> list[dict[str, Any]]:
    if not results_root.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for path in sorted(results_root.glob("*.json")):
        results.append(load_json(path))
    return results


def normalized_result_records(
    user_record: dict[str, Any],
    *,
    context: str,
) -> tuple[str, list[dict[str, Any]]]:
    """Return the normalized internal view of a schema-version-1/2 user file.

    The schema-version-1 branch intentionally retains the original reader's
    permissive behavior. The schema-version-2 branch validates the complete
    flat envelope and stable identifiers before any value reaches aggregation.
    """

    version = user_record.get("schema_version")
    if version == 1:
        user = str(user_record["user"])
        normalized: list[dict[str, Any]] = []
        solved_per_model = user_record.get("solved", {})
        for raw_model_name, problems_for_model in solved_per_model.items():
            for problem_id, record in problems_for_model.items():
                production_metadata = {
                    key: record[key]
                    for key in (
                        "production_description",
                        "solution_publication_status",
                        "solution_publication_date",
                    )
                    if key in record
                }
                normalized.append(
                    {
                        "result_id": None,
                        "problem_id": str(problem_id),
                        "statement_revision": 1,
                        "declared_model": str(raw_model_name),
                        "accepted_at": str(record["solved_at"]),
                        "benchmark_commit": str(record["benchmark_commit"]),
                        "intake": {
                            "kind": "issue",
                            "issue_number": int(record["issue_number"]),
                        },
                        "submission": {
                            "kind": str(record["submission_kind"]),
                            "repo": str(record["submission_repo"]),
                            "ref": str(record["submission_ref"]),
                            "public": bool(record["submission_public"]),
                        },
                        "production_metadata": production_metadata,
                    }
                )
        return user, normalized
    if version == 2:
        try:
            records = parse_schema_version_2_file(user_record, context=context)
        except ResultsSchemaError as exc:
            raise SystemExit(str(exc)) from exc
        return user_record["user"], records
    raise SystemExit(
        f"results file for user {user_record.get('user')!r} has "
        f"schema_version {version!r}; "
        "this generator supports versions 1 and 2."
    )


def camel_case(value: str) -> str:
    pieces = re.split(r"[^A-Za-z0-9]+", value)
    out = "".join(piece[:1].upper() + piece[1:] for piece in pieces if piece)
    return out or "Problem"


def generated_problem_root(benchmark_repo: pathlib.Path, problem: Problem) -> pathlib.Path:
    return benchmark_repo / problem.challenge_path


def strip_imports(text: str) -> tuple[list[str], list[str]]:
    """Pull every `import ...` line out of `text`, regardless of position.

    The multi-hole `Challenge.lean` may contain `import` lines interleaved
    with the source module's copyright comment block, so we cannot rely on
    a contiguous header run. Lean only accepts imports at the top of a
    file anyway, so removing them globally and re-emitting them at the
    catalog's top is safe."""
    imports: list[str] = []
    body: list[str] = []
    for line in text.splitlines():
        if line.startswith("import "):
            imports.append(line)
        else:
            body.append(line)
    return imports, body


DECL_PATTERN = re.compile(
    r"^(?:@[A-Za-z0-9_.]+(?:\s*\[[^\]]+\])?\s+)*"
    r"(?:(?:protected|private)\s+)?"
    r"(?P<kind>abbrev|class|def|inductive|opaque|structure|theorem)\s+"
    r"(?P<name>[A-Za-z0-9_']+)\b"
)


def collect_local_declarations(lines: list[str]) -> dict[str, str]:
    namespace_stack: list[str] = []
    declarations: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("/-") or stripped.startswith("--"):
            continue
        if stripped.startswith("namespace "):
            parts = stripped.split()
            if len(parts) >= 2:
                namespace_stack.append(parts[1])
            continue
        if stripped.startswith("end "):
            parts = stripped.split()
            if len(parts) >= 2 and namespace_stack and namespace_stack[-1] == parts[1]:
                namespace_stack.pop()
            continue
        match = DECL_PATTERN.match(stripped)
        if match is None:
            continue
        name = match.group("name")
        declarations[name] = ".".join(namespace_stack + [name]) if namespace_stack else name
    return declarations


def qualify_theorem_text(theorem_text: str, theorem_basename: str, local_declarations: dict[str, str]) -> str:
    """Rewrite short references in a theorem body to fully-qualified forms.

    Used only on the legacy single-theorem path, where the theorem body
    references same-module helpers via short names but the helpers will
    live inside our per-problem `Problem<CamelId>` namespace at the
    catalog level."""
    qualified = theorem_text
    for short_name, full_name in sorted(local_declarations.items(), key=lambda item: len(item[0]), reverse=True):
        if short_name == theorem_basename:
            continue
        qualified = re.sub(
            rf"(?<![A-Za-z0-9_.']){re.escape(short_name)}\b",
            full_name,
            qualified,
        )
    return qualified


def anchor_id(problem_id: str, hole: Hole) -> str:
    return f"{problem_id}__{hole.basename}"


def inject_legacy_theorem_anchor(problem: Problem, hole: Hole, theorem_text: str) -> str:
    pattern = re.compile(
        rf"(?ms)^theorem\s+{re.escape(hole.basename)}\b.*?^\s*sorry\s*$"
    )
    match = pattern.search(theorem_text)
    if not match:
        raise SystemExit(f"Could not find theorem block for {problem.id}::{hole.basename}")
    aid = anchor_id(problem.id, hole)
    return (
        theorem_text[:match.start()]
        + f"-- ANCHOR: {aid}\n"
        + match.group(0)
        + f"\n-- ANCHOR_END: {aid}"
        + theorem_text[match.end():]
    )


def inject_multi_hole_anchor(problem: Problem, hole: Hole, source_text: str) -> str:
    """Wrap a hole's body inline with `-- ANCHOR: <id>__<basename>` markers.

    For multi-hole problems the per-hole `body` string is a verbatim
    substring of the generated `Challenge.lean`, so plain string search
    suffices and we don't need to keyword-match across kinds. Extend the
    captured span to end-of-line so any trailing same-line `-- ...`
    inline comments end up inside the anchor wrap rather than on the
    closing marker line (which subverso parses as part of the anchor
    name)."""
    aid = anchor_id(problem.id, hole)
    idx = source_text.find(hole.body)
    if idx < 0:
        raise SystemExit(
            f"Could not locate hole body for {problem.id}::{hole.basename} "
            f"in Challenge.lean — `body` field in holes.json must be a substring of the generated Challenge.lean."
        )
    end_idx = idx + len(hole.body)
    nl = source_text.find("\n", end_idx)
    if nl != -1:
        end_idx = nl
    return (
        source_text[:idx]
        + f"-- ANCHOR: {aid}\n"
        + source_text[idx:end_idx]
        + f"\n-- ANCHOR_END: {aid}"
        + source_text[end_idx:]
    )


def is_legacy_single_theorem(problem: Problem) -> bool:
    return len(problem.holes) == 1 and problem.holes[0].kind == "theorem"


def module_to_source_path(module: str) -> pathlib.PurePath:
    """Map a `LeanEval.X.Y` module name to its source-file path."""
    return pathlib.PurePath(*module.split(".")).with_suffix(".lean")


def source_file_imports(
    benchmark_repo: pathlib.Path,
    module: str,
    _visited: set[str] | None = None,
) -> list[str]:
    """Return the original source file's imports, filtered to be safe to
    re-emit at the top of the per-problem snapshot file.

    The benchmark repo's `generate_projects.py` rewrites every emitted
    `Challenge.lean` (and `ChallengeDeps.lean`) to start with
    `import Mathlib`. We instead read from the source so the snapshot
    file uses whatever the author actually wrote — typically specific
    Mathlib submodules, occasionally bare `import Mathlib`. Either is
    fine because each problem now lives in its own snapshot file.

    Filters:
    - drop `import EvalTools.*` — the snapshot strips `@[eval_problem]`
      from bodies, so the marker module is unused;
    - replace each `import LeanEval.X` with the *transitive* set of
      non-LeanEval imports from `LeanEval/X.lean`'s source. The
      LeanEval helper module's body is already inlined elsewhere
      (`ChallengeDeps.lean` for legacy, verbatim in the source for
      multi-hole), but its Mathlib dependencies are not — without this
      expansion, identifiers like `EuclideanSpace` that originate in the
      helper's imports are unbound."""
    visited = _visited if _visited is not None else set()
    if module in visited:
        return []
    visited.add(module)
    src = benchmark_repo / module_to_source_path(module)
    if not src.is_file():
        return []
    imports, _ = strip_imports(src.read_text(encoding="utf-8"))
    result: list[str] = []
    for line in imports:
        target = line.removeprefix("import ").strip()
        if target.startswith("EvalTools"):
            continue
        if target.startswith("LeanEval."):
            for inner in source_file_imports(benchmark_repo, target, visited):
                if inner not in result:
                    result.append(inner)
            continue
        if line not in result:
            result.append(line)
    return result


def build_problem_fragment(problem: Problem, benchmark_repo: pathlib.Path) -> tuple[list[str], list[str]]:
    """Build a per-problem catalog fragment.

    Returns `(imports, body_parts)` where `body_parts` are concatenated
    inside the problem's `namespace Problem<CamelId>` block. The fragment
    contains one `-- ANCHOR: <id>__<basename>` block per hole, in source
    order."""
    root = generated_problem_root(benchmark_repo, problem)
    challenge_path = root / "Challenge.lean"
    deps_path = root / "ChallengeDeps.lean"

    _, challenge_body = strip_imports(challenge_path.read_text(encoding="utf-8"))
    # Imports come from the original source file (specific submodules),
    # not from the blanket `import Mathlib` that Challenge.lean uses.
    # Falls back to the empty list if the source isn't accessible (the
    # generator then emits no imports for that problem, and any required
    # ones get pulled in by other problems' source imports).
    imports = list(source_file_imports(benchmark_repo, problem.module))
    body_parts: list[str] = []

    if is_legacy_single_theorem(problem):
        # Legacy single-theorem path. Preserve the existing
        # ChallengeDeps + qualify-theorem-references machinery so byte
        # equivalence is maintained for problems that previously rendered
        # cleanly.
        local_declarations: dict[str, str] = {}
        if deps_path.is_file():
            # Drop ChallengeDeps's `import Mathlib` header — its imports
            # are also rewritten by generate_projects.py and would
            # reintroduce the blanket import we just avoided. The deps
            # body (helper definitions extracted from the source) is what
            # we actually need.
            _, deps_body = strip_imports(deps_path.read_text(encoding="utf-8"))
            body_parts.append("\n".join(deps_body).strip())
            local_declarations = collect_local_declarations(deps_body)
        hole = problem.holes[0]
        theorem_text = qualify_theorem_text("\n".join(challenge_body).strip(), hole.basename, local_declarations)
        body_parts.append(inject_legacy_theorem_anchor(problem, hole, theorem_text).strip())
    else:
        # Multi-hole path: helper definitions are extracted into
        # `ChallengeDeps.lean`, while `Challenge.lean` holds only the
        # `@[eval_problem]` theorems. Inline the deps body first — both files
        # reproduce the source module's namespace structure, so the helper
        # defs and the theorems land in the same namespace and the theorems'
        # references resolve. Without this the helper names are unbound
        # (autobound to implicits) and the snapshot fails to compile. Then
        # inject one anchor block per hole around its `body` substring in the
        # challenge text.
        if deps_path.is_file():
            _, deps_body = strip_imports(deps_path.read_text(encoding="utf-8"))
            body_parts.append("\n".join(deps_body).strip())
        text = "\n".join(challenge_body).strip()
        for hole in problem.holes:
            text = inject_multi_hole_anchor(problem, hole, text)
        body_parts.append(text.strip())
    return imports, body_parts


def snapshot_namespace(problem: Problem) -> str:
    return f"Problem{camel_case(problem.id)}"


def snapshot_module_name(problem: Problem) -> str:
    return f"BenchmarkProblems.{snapshot_namespace(problem)}"


def dedupe_universe_declarations(fragments: list[str]) -> list[str]:
    """Remove repeated universe names when generated modules are inlined.

    `ChallengeDeps.lean` and `Challenge.lean` are separate Lean modules and may
    legitimately repeat `universe u`. A snapshot file concatenates their bodies,
    where redeclaring the same universe name is an error. Preserve declaration
    order while emitting each name only once.
    """
    seen: set[str] = set()
    result: list[str] = []
    for fragment in fragments:
        lines: list[str] = []
        for line in fragment.splitlines():
            code, separator, comment = line.partition("--")
            stripped = code.strip()
            if not stripped.startswith("universe "):
                lines.append(line)
                continue
            names = stripped.removeprefix("universe ").split()
            fresh = [name for name in names if name not in seen]
            seen.update(names)
            if fresh:
                indent = code[:len(code) - len(code.lstrip())]
                rebuilt = indent + "universe " + " ".join(fresh)
                if separator:
                    rebuilt += " " + separator + comment
                lines.append(rebuilt)
            elif separator and comment.strip():
                indent = code[:len(code) - len(code.lstrip())]
                lines.append(indent + separator + comment)
        result.append("\n".join(lines))
    return result


def preserve_root_declarations(fragment: str, names: set[str]) -> str:
    """Keep selected dotted declaration names rooted inside a wrapper.

    A declaration such as `def Nat.IsCubeFree` intentionally extends an existing
    root namespace. Snapshot packaging adds a per-problem namespace for isolation;
    without `_root_.`, Lean instead creates `Problem<Id>.Nat.IsCubeFree`. The
    allowlist is explicit because other dotted declarations intentionally refer
    to namespaces created inside the per-problem wrapper.
    """
    declaration = re.compile(
        r"(?m)^(?P<prefix>\s*(?:(?:noncomputable|protected|private)\s+)*"
        r"(?:abbrev|class|def|inductive|lemma|structure|theorem)\s+)"
        r"(?P<name>(?!_root_\.)[^\s({\[]+\.[^\s({\[]+)"
    )

    def replace(match: re.Match[str]) -> str:
        name = match.group("name")
        if name not in names:
            return match.group(0)
        return match.group("prefix") + "_root_." + name

    return declaration.sub(replace, fragment)


def qualify_probability_root_opens(fragment: str) -> str:
    """Disambiguate Mathlib's root probability namespace under isolation.

    Annals' shared probability-notation helper introduces a sibling
    `ProbabilityTheory` namespace inside the per-problem wrapper. The problem
    source also opens Mathlib's root namespace for definitions such as
    `bernoulliMeasure`; make that open explicit while leaving the isolated
    notation namespace in place.
    """
    lines: list[str] = []
    for line in fragment.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("open ") and not stripped.startswith("open scoped "):
            code, separator, comment = line.partition("--")
            code = re.sub(
                r"(?<![\w.])ProbabilityTheory(?![\w.])",
                "_root_.ProbabilityTheory",
                code,
            )
            line = code + separator + comment
        lines.append(line)
    return "\n".join(lines)


def write_benchmark_snapshot(benchmark_repo: pathlib.Path, problems: list[Problem]) -> None:
    if BENCHMARK_SNAPSHOT_ROOT.exists():
        shutil.rmtree(BENCHMARK_SNAPSHOT_ROOT)
    BENCHMARK_SNAPSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    write_text(
        BENCHMARK_SNAPSHOT_ROOT / "lakefile.toml",
        benchmark_snapshot_lakefile(benchmark_repo),
    )
    shutil.copy2(benchmark_repo / "lean-toolchain", BENCHMARK_SNAPSHOT_ROOT / "lean-toolchain")

    # One file per problem, with the source author's exact imports at
    # the top of each file. Lean's `import` directives are file-scoped,
    # so giving each problem its own file means a source that uses
    # blanket `import Mathlib` (and the all-Mathlib notation table that
    # comes with it) cannot pollute another problem whose body uses
    # identifiers like `μ` that Mathlib reserves as notation tokens.
    sorted_problems = sorted(
        (problem for problem in problems if problem.visible),
        key=lambda p: p.sort_index,
    )
    umbrella_imports: list[str] = []
    for problem in sorted_problems:
        imports, fragments = build_problem_fragment(problem, benchmark_repo)
        fragments = dedupe_universe_declarations(fragments)
        namespace = snapshot_namespace(problem)
        body_lines: list[str] = []
        if is_legacy_single_theorem(problem):
            root_declarations = ROOT_DECLARATIONS_BY_PROBLEM.get(problem.id, set())
            fragments = [
                preserve_root_declarations(fragment, root_declarations)
                for fragment in fragments
            ]
            source_imports, _ = strip_imports(
                (benchmark_repo / module_to_source_path(problem.module)).read_text(
                    encoding="utf-8"
                )
            )
            if ANNALS_PROBABILITY_NOTATION_IMPORT in source_imports:
                fragments = [qualify_probability_root_opens(fragment) for fragment in fragments]
            # Legacy single-theorem problems wrap their helpers and
            # theorem in a per-problem `Problem<CamelId>` namespace so
            # any short helper names from `ChallengeDeps` don't collide
            # with the same name in another problem.
            body_lines.append(f"namespace {namespace}")
            body_lines.append("")
            for fragment in fragments:
                if fragment:
                    body_lines.append(fragment)
                    body_lines.append("")
            body_lines.append(f"end {namespace}")
        else:
            # Multi-hole problems reproduce the source module's full
            # namespace structure verbatim, which gives the body the
            # original namespace context it needs to type-check.
            for fragment in fragments:
                if fragment:
                    body_lines.append(fragment)
                    body_lines.append("")

        problem_path = BENCHMARK_SNAPSHOT_ROOT / "BenchmarkProblems" / f"{namespace}.lean"
        write_text(
            problem_path,
            "\n".join(imports + [""] + body_lines).rstrip() + "\n",
        )
        umbrella_imports.append(f"import {snapshot_module_name(problem)}")

    write_text(
        BENCHMARK_SNAPSHOT_ROOT / "BenchmarkProblems.lean",
        "\n".join(umbrella_imports) + "\n",
    )
    # Pin file: the deploy workflow checks this out and regenerates site-data
    # against the same benchmark commit the snapshot was built from, so the
    # snapshot's per-problem files and site-data/problems.json stay in lockstep.
    write_text(BENCHMARK_SNAPSHOT_ROOT / ".benchmark-commit", git_head(benchmark_repo) + "\n")


def public_solution_url(
    kind: str, repo: str, ref: str, problem_id: str, public: bool
) -> str | None:
    if not public:
        return None
    if kind == "gist":
        return f"https://gist.github.com/{repo}/{ref}"
    return f"https://github.com/{repo}/tree/{ref}/generated/{problem_id}"


def timestamp_key(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def build_problem_payload(benchmark_repo: pathlib.Path, problems: list[Problem]) -> dict[str, Any]:
    """Build the public catalog from the complete visible/hidden manifest."""

    return {
        "schema_version": 4,
        "generated_at": utc_now(),
        "benchmark": {
            "repo": "leanprover/lean-eval",
            "commit": git_head(benchmark_repo),
        },
        "problems": [
            {
                "id": problem.id,
                "title": problem.title,
                # Kept in the derived payload during the UI transition. Hidden
                # catalog fixtures are omitted entirely rather than exposed as
                # a public "test" section.
                "test": False,
                "group": problem.group,
                "status": problem.status,
                "visible": problem.visible,
                "statement_revision": problem.statement_revision,
                "tags": list(problem.tags),
                "submitter": problem.submitter,
                "module": problem.module,
                "snapshot_module": snapshot_module_name(problem),
                "holes": [
                    {
                        "name": hole.name,
                        "basename": hole.basename,
                        "kind": hole.kind,
                        "body": hole.body,
                    }
                    for hole in problem.holes
                ],
                "notes": problem.notes,
                "source": problem.source,
                "informal_solution": problem.informal_solution,
                "challenge_path": problem.challenge_path,
                "sort_index": problem.sort_index,
            }
            for problem in problems
            if problem.visible
        ],
    }


def build_leaderboard_payload(
    results_repo: pathlib.Path,
    benchmark_repo: pathlib.Path,
    problems: list[Problem],
    raw_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate results against the complete visible/hidden catalog."""

    catalog_problem_map = {problem.id: problem for problem in problems}
    problem_map = {
        problem.id: problem for problem in problems if problem.visible
    }
    per_model_problem: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    per_model_submitter_problems: dict[str, defaultdict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    model_display: dict[str, str] = {}
    public_submitters: set[str] = set()

    for file_index, user_record in enumerate(raw_results):
        user, records = normalized_result_records(
            user_record,
            context=f"results file {file_index} for {user_record.get('user')!r}",
        )
        for record in records:
            problem_id = record["problem_id"]
            catalog_problem = catalog_problem_map.get(problem_id)
            if catalog_problem is not None and not catalog_problem.visible:
                # Hidden catalog entries are internal fixtures. They must not
                # create a row, affect a score, or leak into public provenance.
                continue
            public_submitters.add(user)
            model_name = normalize_model_name(record["declared_model"])
            model_id = slugify(model_name)
            model_display.setdefault(model_id, model_name)
            per_model_submitter_problems[model_id][user].add(problem_id)
            current = per_model_problem[model_id].get(problem_id)
            production_description_raw = record["production_metadata"].get(
                "production_description"
            )
            production_description = (
                production_description_raw.strip()
                if isinstance(production_description_raw, str)
                and production_description_raw.strip()
                else None
            )
            submission = record["submission"]
            intake = record["intake"]
            submission_kind = submission["kind"]
            provenance = {
                "user": user,
                "benchmark_commit": record["benchmark_commit"],
                "submission_kind": submission_kind,
                "submission_repo": submission["repo"],
                "submission_ref": submission["ref"],
                "intake": intake,
                "statement_revision": record["statement_revision"],
            }
            if record["result_id"] is not None:
                provenance["result_id"] = record["result_id"]
            if intake["kind"] == "issue":
                provenance["issue_number"] = intake["issue_number"]
            candidate = {
                "problem_id": problem_id,
                "solved_at": record["accepted_at"],
                "provenance": provenance,
                "public_solution": {
                    "available": submission["public"],
                    "kind": submission_kind if submission["public"] else None,
                    "repo": submission["repo"] if submission["public"] else None,
                    "ref": submission["ref"] if submission["public"] else None,
                    "url": public_solution_url(
                        submission_kind,
                        submission["repo"],
                        submission["ref"],
                        problem_id,
                        submission["public"],
                    ),
                },
                "production_description": production_description,
            }
            if current is None or timestamp_key(candidate["solved_at"]) < timestamp_key(
                current["solved_at"]
            ):
                per_model_problem[model_id][problem_id] = candidate

    # Snapshot-race tolerance: a result can be recorded against a
    # leanprover/lean-eval commit slightly newer than the leaderboard's
    # benchmark-snapshot, naming a problem the snapshot's catalog does
    # not yet contain. Such records are kept in the leaderboard payload
    # but counted only in solved_total (not solved_main/solved_test);
    # warn so the gap is visible until the snapshot catches up.
    unknown_problem_ids = sorted(
        {
            problem_id
            for problems_for_model in per_model_problem.values()
            for problem_id in problems_for_model
            if problem_id not in problem_map
        }
    )
    if unknown_problem_ids:
        print(
            "warning: results reference problem ids absent from the benchmark "
            f"snapshot catalog: {', '.join(unknown_problem_ids)}",
            file=sys.stderr,
        )

    solving_model_counts: dict[str, int] = defaultdict(int)
    for problems_for_model in per_model_problem.values():
        for problem_id in problems_for_model:
            solving_model_counts[problem_id] += 1

    entries: list[dict[str, Any]] = []
    total_models = len(per_model_problem)
    for model_id, problems_for_model in per_model_problem.items():
        solved_items = list(problems_for_model.values())
        solved_items.sort(key=lambda item: item["problem_id"])
        first_solved_at = min(item["solved_at"] for item in solved_items)
        last_solved_at = max(item["solved_at"] for item in solved_items)

        def rarity_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
            problem = problem_map.get(item["problem_id"])
            return (
                solving_model_counts[item["problem_id"]],
                -timestamp_key(item["solved_at"]),
                1 if problem is None else 0,
                item["problem_id"],
            )

        notable = sorted(solved_items, key=rarity_sort_key)
        for rank, item in enumerate(notable, start=1):
            problem = problem_map.get(item["problem_id"])
            recency_component = int(timestamp_key(item["solved_at"]) // 86400)
            item["rarity_rank"] = rank
            item["rarity_score"] = (total_models - solving_model_counts[item["problem_id"]]) * 1_000_000 + recency_component
            item["problem_test"] = False

        solved_total = len(solved_items)
        solved_main = sum(
            1 for item in solved_items if item["problem_id"] in problem_map
        )
        solved_test = 0
        entries.append(
            {
                "model_id": model_id,
                "model_name": model_display[model_id],
                "score": {
                    "solved_total": solved_total,
                    "solved_main": solved_main,
                    "solved_test": solved_test,
                    # Headline number is main-only: test problems are
                    # internal fixtures and must not inflate the score.
                    "display": str(solved_main),
                },
                "first_solved_at": first_solved_at,
                "last_solved_at": last_solved_at,
                "submitter_count": len(per_model_submitter_problems[model_id]),
                "submitters": [
                    {"user": user, "solved_total": len(problem_ids)}
                    for user, problem_ids in sorted(
                        per_model_submitter_problems[model_id].items(),
                        key=lambda item: (-len(item[1]), item[0].lower()),
                    )
                ],
                "solved_problem_ids": [item["problem_id"] for item in solved_items],
                "notable_problem_ids": [item["problem_id"] for item in notable[:10]],
                # Problems where this entry is the only solver across the
                # whole leaderboard. Used by the home page to highlight
                # genuinely-unique solves.
                "unique_problem_ids": [
                    item["problem_id"]
                    for item in notable
                    if solving_model_counts[item["problem_id"]] == 1
                ],
                "solved_problems": [
                    {
                        "problem_id": item["problem_id"],
                        "solved_at": item["solved_at"],
                        "rarity_rank": item["rarity_rank"],
                        "rarity_score": item["rarity_score"],
                        "public_solution": item["public_solution"],
                        "provenance": item["provenance"],
                        "production_description": item.get("production_description"),
                    }
                    for item in notable
                ],
            }
        )

    # Rank by main benchmark solves only; test-problem solves never move a
    # model up the board.
    entries.sort(
        key=lambda entry: (
            -entry["score"]["solved_main"],
            timestamp_key(entry["last_solved_at"]),
            entry["model_name"].lower(),
        )
    )
    for rank, entry in enumerate(entries, start=1):
        entry["rank"] = rank

    return {
        "schema_version": 1,
        "raw_results_schema_versions": sorted(
            {int(record.get("schema_version", -1)) for record in raw_results}
        ),
        "generated_at": utc_now(),
        "results_repo": {
            "repo": RESULTS_REPO_SLUG,
            "commit": git_head(results_repo),
        },
        "benchmark": {
            "repo": "leanprover/lean-eval",
            "commit": git_head(benchmark_repo),
        },
        "summary": {
            "models": len(entries),
            "submitters": len(public_submitters),
            "problem_authors": len(
                {problem.submitter for problem in problems if problem.visible}
            ),
            "problems": len(problem_map),
            "main_problems": len(problem_map),
            "test_problems": 0,
        },
        "entries": entries,
    }


def _read_pinned_sha() -> str:
    if not BENCHMARK_COMMIT_FILE.is_file():
        raise SystemExit(
            f"{BENCHMARK_COMMIT_FILE} is missing. The leaderboard build "
            "requires a pinned benchmark commit so it cannot drift to an "
            "unverified leanprover/lean-eval state. Create the file with a "
            "single 40-char hex SHA + newline. Bump procedure: SECURITY.md "
            "> 'Bumping pinned dependencies'."
        )
    raw = BENCHMARK_COMMIT_FILE.read_text(encoding="utf-8").strip()
    if not SHA_RE.fullmatch(raw):
        raise SystemExit(
            f"{BENCHMARK_COMMIT_FILE} must contain exactly a 40-char hex SHA. "
            f"Found: {raw!r}."
        )
    return raw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-repo", default=str(DEFAULT_BENCHMARK_REPO))
    parser.add_argument(
        "--results-repo",
        default=str(DEFAULT_RESULTS_REPO),
        help="Checkout of leanprover/lean-eval-submissions (the results store).",
    )
    parser.add_argument(
        "--results-root",
        default=None,
        help="Directory of <login>.json result files. "
        "Defaults to <results-repo>/results.",
    )
    parser.add_argument("--output-dir", default=str(SITE_DATA_ROOT))
    parser.add_argument(
        "--state-domain",
        default=None,
        help="Optional lean-eval-state materialized/domain.json projection. "
        "The preview never reads State events directly.",
    )
    parser.add_argument(
        "--state-repo",
        default=None,
        help="State checkout whose HEAD produced --state-domain; recorded as provenance.",
    )
    parser.add_argument(
        "--preview-fixture",
        default=None,
        help="Optional schema-version-1 lifecycle/alias fixture for local "
        "preview development. Never inferred or enabled implicitly.",
    )
    parser.add_argument(
        "--site-base-url",
        default="https://lean-lang.org/eval/",
        help="Absolute public base URL used only for RSS links.",
    )
    parser.add_argument(
        "--no-write-snapshot",
        action="store_true",
        help="Regenerate site-data/ only; leave benchmark-snapshot/ untouched. "
             "Used by the deploy workflow, which reads the snapshot's pinned "
             "benchmark commit and never wants to mutate the snapshot itself.",
    )
    parser.add_argument(
        "--lean-eval-expected-sha",
        default=None,
        help="Assert the lean-eval clone at --benchmark-repo is at this SHA. "
        "In --no-write-snapshot mode, defaults to the contents of "
        "`.benchmark-commit` (the deploy invariant: snapshot files and "
        "lean-eval revision must agree). In write-snapshot mode there is "
        "no default — this script will overwrite `.benchmark-commit` to "
        "the input HEAD anyway. Pass explicitly when you want a sanity "
        "assertion, or when running locally against an unmerged branch.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark_repo = pathlib.Path(args.benchmark_repo).resolve()
    results_repo = pathlib.Path(args.results_repo).resolve()
    results_root = (
        pathlib.Path(args.results_root).resolve()
        if args.results_root
        else results_repo / "results"
    )
    output_dir = pathlib.Path(args.output_dir).resolve()

    # Pin-check: assert that the lean-eval clone we're about to read from
    # matches the SHA we expected. The *source* of the expected SHA depends
    # on what we're doing:
    #   * --no-write-snapshot (deploy): default to the recorded pin in
    #     .benchmark-commit. The deploy path reads the snapshot off disk
    #     and the lean-eval clone *must* equal that pin or the generated
    #     site-data describes problems that don't match the snapshot.
    #   * write-snapshot (default; bump): no default, because the script's
    #     last act is to overwrite .benchmark-commit to git_head, so
    #     defaulting the expected SHA to the *old* pin is incoherent (it
    #     would refuse the very operation we're performing). Callers can
    #     still pass --lean-eval-expected-sha as a sanity assertion that
    #     the clone they handed us is the SHA they meant to snapshot.
    expected_sha = args.lean_eval_expected_sha
    if expected_sha is None and args.no_write_snapshot:
        expected_sha = _read_pinned_sha()
    if expected_sha is not None:
        if not SHA_RE.fullmatch(expected_sha):
            raise SystemExit(
                f"--lean-eval-expected-sha must be a 40-char hex SHA, got {expected_sha!r}"
            )
        actual_sha = git_head(benchmark_repo)
        if actual_sha != expected_sha:
            from_flag = args.lean_eval_expected_sha is not None
            source = "--lean-eval-expected-sha" if from_flag else str(BENCHMARK_COMMIT_FILE)
            hint = (
                "The SHA you asserted via --lean-eval-expected-sha does not match "
                "the lean-eval checkout. Re-resolve the target SHA and re-run."
                if from_flag
                else "If you intend to advance the pin, drop --no-write-snapshot so "
                     "the snapshot (and .benchmark-commit) are regenerated together. "
                     "See SECURITY.md > 'Bumping pinned dependencies'."
            )
            raise SystemExit(
                "Benchmark commit mismatch — refusing to build the leaderboard "
                "against an unexpected leanprover/lean-eval revision.\n"
                f"  expected: {expected_sha} (from {source})\n"
                f"  actual:   {actual_sha} (HEAD of {benchmark_repo})\n"
                f"{hint}"
            )

    manifest_dir = benchmark_repo / "manifests" / "problems"
    if not manifest_dir.is_dir():
        raise SystemExit(f"Benchmark manifest directory not found: {manifest_dir}")

    problems = load_manifest(manifest_dir, benchmark_repo)
    raw_results = load_results(results_root)

    normalized_files = [
        normalized_result_records(
            user_record,
            context=f"results file {index} for {user_record.get('user')!r}",
        )
        for index, user_record in enumerate(raw_results)
    ]

    write_json(output_dir / "problems.json", build_problem_payload(benchmark_repo, problems))
    leaderboard_payload = build_leaderboard_payload(
        results_repo, benchmark_repo, problems, raw_results
    )
    write_json(output_dir / "leaderboard.json", leaderboard_payload)
    preview_payload = {
        **leaderboard_payload,
        "preview": {
            "kind": "results-v2-compatibility",
            "source": "strict-v2-normalized-results",
        },
    }
    write_json(output_dir / "leaderboard-preview.json", preview_payload)
    fixture_path = (
        pathlib.Path(args.preview_fixture).resolve() if args.preview_fixture else None
    )
    fixture = load_preview_fixture(fixture_path)
    aliases = {
        item["declared_label"]: {
            "canonical_id": item["canonical_id"],
            "label": item["label"],
        }
        for item in fixture.get("model_aliases", [])
    }
    state_domain_path = (
        pathlib.Path(args.state_domain).resolve() if args.state_domain else None
    )
    state_domain = load_json(state_domain_path) if state_domain_path else None
    state_repo = pathlib.Path(args.state_repo).resolve() if args.state_repo else None
    if state_domain_path is not None and state_repo is None:
        raise SystemExit("--state-domain requires --state-repo for immutable provenance")
    fallback_solutions = adapt_results_store(normalized_files, aliases)
    state_solutions = adapt_state_domain(state_domain, aliases)
    lifecycle_files = build_lifecycle_projection(
        problems=problems,
        solutions=merge_solutions(state_solutions, fallback_solutions),
        set_definitions=load_set_definitions(benchmark_repo / "manifests" / "sets"),
        tag_registry=load_tag_registry(benchmark_repo / "manifests" / "tags.toml"),
        fixture=fixture,
        generated_at=leaderboard_payload["generated_at"],
        benchmark_commit=git_head(benchmark_repo),
        state_commit=git_head(state_repo) if state_repo else None,
        state_metadata=state_domain,
        site_base_url=args.site_base_url,
    )
    for relative_path, payload in lifecycle_files.items():
        destination = output_dir / relative_path
        if isinstance(payload, str):
            write_text(destination, payload)
        else:
            write_json(destination, payload)
    if not args.no_write_snapshot:
        write_benchmark_snapshot(benchmark_repo, problems)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
