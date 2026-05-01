#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results"
SITE_DATA_ROOT = REPO_ROOT / "site-data"
BENCHMARK_SNAPSHOT_ROOT = REPO_ROOT / "benchmark-snapshot"
DEFAULT_BENCHMARK_REPO = pathlib.Path(
    os.environ.get("LEAN_EVAL_BENCHMARK_REPO", str(REPO_ROOT.parent / "lean-eval"))
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
    test: bool
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


def load_manifest(manifest_path: pathlib.Path, benchmark_repo: pathlib.Path) -> list[Problem]:
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    problems: list[Problem] = []
    for index, raw in enumerate(data["problem"]):
        problem_id = str(raw["id"])
        holes = load_holes(benchmark_repo, problem_id)
        problems.append(
            Problem(
                id=problem_id,
                title=str(raw["title"]),
                test=bool(raw.get("test", False)),
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


def benchmark_snapshot_lakefile(benchmark_repo: pathlib.Path) -> str:
    mathlib_git, mathlib_rev = benchmark_mathlib_require(benchmark_repo)
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
            'rev = "main"',
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


def build_problem_fragment(problem: Problem, benchmark_repo: pathlib.Path) -> tuple[list[str], list[str]]:
    """Build a per-problem catalog fragment.

    Returns `(imports, body_parts)` where `body_parts` are concatenated
    inside the problem's `namespace Problem<CamelId>` block. The fragment
    contains one `-- ANCHOR: <id>__<basename>` block per hole, in source
    order."""
    root = generated_problem_root(benchmark_repo, problem)
    challenge_path = root / "Challenge.lean"
    deps_path = root / "ChallengeDeps.lean"

    challenge_imports, challenge_body = strip_imports(challenge_path.read_text(encoding="utf-8"))
    imports = [line for line in challenge_imports if line.strip() != "import ChallengeDeps"]
    body_parts: list[str] = []

    if is_legacy_single_theorem(problem):
        # Legacy single-theorem path. Preserve the existing
        # ChallengeDeps + qualify-theorem-references machinery so byte
        # equivalence is maintained for problems that previously rendered
        # cleanly.
        local_declarations: dict[str, str] = {}
        if deps_path.is_file():
            deps_imports, deps_body = strip_imports(deps_path.read_text(encoding="utf-8"))
            for line in deps_imports:
                if line not in imports:
                    imports.append(line)
            body_parts.append("\n".join(deps_body).strip())
            local_declarations = collect_local_declarations(deps_body)
        hole = problem.holes[0]
        theorem_text = qualify_theorem_text("\n".join(challenge_body).strip(), hole.basename, local_declarations)
        body_parts.append(inject_legacy_theorem_anchor(problem, hole, theorem_text).strip())
    else:
        # Multi-hole path: the entire source module is reproduced verbatim
        # in Challenge.lean (with `@[eval_problem]` already stripped).
        # Inject one anchor block per hole around its `body` substring.
        text = "\n".join(challenge_body).strip()
        for hole in problem.holes:
            text = inject_multi_hole_anchor(problem, hole, text)
        body_parts.append(text.strip())
    return imports, body_parts


def snapshot_namespace(problem: Problem) -> str:
    return f"Problem{camel_case(problem.id)}"


def write_benchmark_snapshot(benchmark_repo: pathlib.Path, problems: list[Problem]) -> None:
    if BENCHMARK_SNAPSHOT_ROOT.exists():
        shutil.rmtree(BENCHMARK_SNAPSHOT_ROOT)
    BENCHMARK_SNAPSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    write_text(
        BENCHMARK_SNAPSHOT_ROOT / "lakefile.toml",
        benchmark_snapshot_lakefile(benchmark_repo),
    )
    shutil.copy2(benchmark_repo / "lean-toolchain", BENCHMARK_SNAPSHOT_ROOT / "lean-toolchain")
    module_imports: list[str] = []
    module_lines: list[str] = []
    for problem in sorted(problems, key=lambda p: p.sort_index):
        imports, fragments = build_problem_fragment(problem, benchmark_repo)
        for line in imports:
            if line not in module_imports:
                module_imports.append(line)
        # Legacy single-theorem problems get a per-problem `namespace
        # Problem<CamelId>` wrap so their `ChallengeDeps`-derived helpers
        # (often in shared namespaces like `Foo.bar`) don't collide
        # across problems. Multi-hole problems instead reproduce the
        # source module's full namespace structure verbatim, which both
        # gives the bodies the original namespace context they need to
        # type-check (e.g. references to `Spec` inside `namespace
        # AlgebraicGeometry`) and isolates each problem under its
        # original module's logical namespace path.
        if is_legacy_single_theorem(problem):
            namespace = snapshot_namespace(problem)
            module_lines.append(f"namespace {namespace}")
            module_lines.append("")
            for fragment in fragments:
                if fragment:
                    module_lines.append(fragment)
                    module_lines.append("")
            module_lines.append(f"end {namespace}")
            module_lines.append("")
        else:
            for fragment in fragments:
                if fragment:
                    module_lines.append(fragment)
                    module_lines.append("")

    catalog_path = BENCHMARK_SNAPSHOT_ROOT / "BenchmarkProblems" / "Catalog.lean"
    write_text(catalog_path, "\n".join(module_imports + [""] + module_lines).rstrip() + "\n")
    write_text(BENCHMARK_SNAPSHOT_ROOT / "BenchmarkProblems.lean", "import BenchmarkProblems.Catalog\n")
    # Pin file: the deploy workflow checks this out and regenerates site-data
    # against the same benchmark commit the snapshot was built from, so the
    # snapshot's catalog and site-data/problems.json stay in lockstep.
    write_text(BENCHMARK_SNAPSHOT_ROOT / ".benchmark-commit", git_head(benchmark_repo) + "\n")


def public_solution_url(repo: str, ref: str, problem_id: str, public: bool) -> str | None:
    if not public:
        return None
    return f"https://github.com/{repo}/tree/{ref}/generated/{problem_id}"


def timestamp_key(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def build_problem_payload(benchmark_repo: pathlib.Path, problems: list[Problem]) -> dict[str, Any]:
    return {
        "schema_version": 3,
        "generated_at": utc_now(),
        "benchmark": {
            "repo": "leanprover/lean-eval",
            "commit": git_head(benchmark_repo),
        },
        "problems": [
            {
                "id": problem.id,
                "title": problem.title,
                "test": problem.test,
                "submitter": problem.submitter,
                "module": problem.module,
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
        ],
    }


def build_leaderboard_payload(
    results_repo: pathlib.Path,
    benchmark_repo: pathlib.Path,
    problems: list[Problem],
    raw_results: list[dict[str, Any]],
) -> dict[str, Any]:
    problem_map = {problem.id: problem for problem in problems}
    per_model_problem: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    per_model_submitters: dict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    model_display: dict[str, str] = {}

    for user_record in raw_results:
        user = str(user_record["user"])
        schema_version = user_record.get("schema_version")
        if schema_version != 2:
            raise SystemExit(
                f"results file for user {user!r} has schema_version "
                f"{schema_version!r}; this generator only knows version 2. "
                "Run scripts/migrate_v1_to_v2.py if it is still v1."
            )
        solved_per_model = user_record.get("solved", {})
        for raw_model_name, problems_for_model in solved_per_model.items():
            model_name = normalize_model_name(str(raw_model_name))
            model_id = slugify(model_name)
            model_display.setdefault(model_id, model_name)
            for problem_id, record in problems_for_model.items():
                per_model_submitters[model_id][user] += 1
                current = per_model_problem[model_id].get(problem_id)
                production_description_raw = record.get("production_description")
                production_description = (
                    str(production_description_raw).strip()
                    if isinstance(production_description_raw, str) and str(production_description_raw).strip()
                    else None
                )
                candidate = {
                    "problem_id": problem_id,
                    "solved_at": str(record["solved_at"]),
                    "provenance": {
                        "user": user,
                        "issue_number": int(record["issue_number"]),
                        "benchmark_commit": str(record["benchmark_commit"]),
                        "submission_repo": str(record["submission_repo"]),
                        "submission_ref": str(record["submission_ref"]),
                    },
                    "public_solution": {
                        "available": bool(record["submission_public"]),
                        "repo": str(record["submission_repo"]) if record["submission_public"] else None,
                        "ref": str(record["submission_ref"]) if record["submission_public"] else None,
                        "url": public_solution_url(
                            str(record["submission_repo"]),
                            str(record["submission_ref"]),
                            problem_id,
                            bool(record["submission_public"]),
                        ),
                    },
                    "production_description": production_description,
                }
                if current is None or timestamp_key(candidate["solved_at"]) < timestamp_key(current["solved_at"]):
                    per_model_problem[model_id][problem_id] = candidate

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
                1 if problem and problem.test else 0,
                item["problem_id"],
            )

        notable = sorted(solved_items, key=rarity_sort_key)
        for rank, item in enumerate(notable, start=1):
            problem = problem_map.get(item["problem_id"])
            recency_component = int(timestamp_key(item["solved_at"]) // 86400)
            item["rarity_rank"] = rank
            item["rarity_score"] = (total_models - solving_model_counts[item["problem_id"]]) * 1_000_000 + recency_component
            item["problem_test"] = problem.test if problem else False

        solved_total = len(solved_items)
        solved_main = sum(0 if problem_map[item["problem_id"]].test else 1 for item in solved_items if item["problem_id"] in problem_map)
        solved_test = sum(1 if problem_map[item["problem_id"]].test else 0 for item in solved_items if item["problem_id"] in problem_map)
        entries.append(
            {
                "model_id": model_id,
                "model_name": model_display[model_id],
                "score": {
                    "solved_total": solved_total,
                    "solved_main": solved_main,
                    "solved_test": solved_test,
                    "display": str(solved_total),
                },
                "first_solved_at": first_solved_at,
                "last_solved_at": last_solved_at,
                "submitter_count": len(per_model_submitters[model_id]),
                "submitters": [
                    {"user": user, "solved_total": count}
                    for user, count in sorted(
                        per_model_submitters[model_id].items(),
                        key=lambda item: (-item[1], item[0].lower()),
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

    entries.sort(
        key=lambda entry: (
            -entry["score"]["solved_total"],
            -entry["score"]["solved_main"],
            timestamp_key(entry["last_solved_at"]),
            entry["model_name"].lower(),
        )
    )
    for rank, entry in enumerate(entries, start=1):
        entry["rank"] = rank

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "results_repo": {
            "repo": "leanprover/lean-eval-leaderboard",
            "commit": git_head(results_repo),
        },
        "benchmark": {
            "repo": "leanprover/lean-eval",
            "commit": git_head(benchmark_repo),
        },
        "summary": {
            "models": len(entries),
            "submitters": len({str(record["user"]) for record in raw_results}),
            "problems": len(problems),
            "main_problems": sum(0 if problem.test else 1 for problem in problems),
            "test_problems": sum(1 if problem.test else 0 for problem in problems),
        },
        "entries": entries,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-repo", default=str(DEFAULT_BENCHMARK_REPO))
    parser.add_argument("--results-root", default=str(RESULTS_ROOT))
    parser.add_argument("--output-dir", default=str(SITE_DATA_ROOT))
    parser.add_argument(
        "--no-write-snapshot",
        action="store_true",
        help="Regenerate site-data/ only; leave benchmark-snapshot/ untouched. "
             "Used by the deploy workflow, which reads the snapshot's pinned "
             "benchmark commit and never wants to mutate the snapshot itself.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark_repo = pathlib.Path(args.benchmark_repo).resolve()
    results_root = pathlib.Path(args.results_root).resolve()
    output_dir = pathlib.Path(args.output_dir).resolve()

    manifest_path = benchmark_repo / "manifests" / "problems.toml"
    if not manifest_path.is_file():
        raise SystemExit(f"Benchmark manifest not found: {manifest_path}")

    problems = load_manifest(manifest_path, benchmark_repo)
    raw_results = load_results(results_root)

    write_json(output_dir / "problems.json", build_problem_payload(benchmark_repo, problems))
    write_json(
        output_dir / "leaderboard.json",
        build_leaderboard_payload(REPO_ROOT, benchmark_repo, problems, raw_results),
    )
    if not args.no_write_snapshot:
        write_benchmark_snapshot(benchmark_repo, problems)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
